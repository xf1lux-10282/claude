#!/usr/bin/perl
#
#	Copyright (c) 2017 - Roy V Harrington -- Harrington Photography
#

use strict;

# VERSION: 2.7.8.0

my $version = "QTR-Create-ICC version 2.7.8.0";
my $header;
my $taghdr;

my @tagtable;

my $totalsize;

my $bpcflag = 0;
my $RGBflag = 0;
my $ACVflag = 0;

my @D50 = (0.96421, 1.00000, 0.82491);

my @datafile;
my @sortdata;
my $numrows = 0;
my $numcols = 0;
my %colname;
my $iccname;
my $outname;

my @rgbvalid;
my @rgbcurve;
my @rgbinvert;

my $clut_Lab2Gray = [0, 0,         0, 0,   
					 65535, 65535, 65535, 65535];
my $clut_Lab2RGB  = [0, 0, 0,              0, 0, 0,
					 0, 0, 0,              0, 0, 0, 
					 65535, 65535, 65535,  65535, 65535, 65535, 
					 65535, 65535, 65535,  65535, 65535, 65535];
my $clut_Gray2Lab = [0, 0, 0,
					 65535, 65535, 65535];
my $clut_RGB2Lab  = [];

my $linear_Gray   = [0, 65535];
my $linear_RGB    = [0, 65535, 0, 65535, 0, 65535];
my $linear_Lab    = [0, 65535, 0, 65535, 0, 65535];
my $gamut_yes     = [0, 0];

my $filename;
my $fileraw;

	foreach my $arg (@ARGV) {
		$filename = $arg if ($arg =~ m/(txt|csv)$/);
		$fileraw  = $arg if ($arg =~ m/\.raw$/);
	}

	if ($fileraw) {
		read_rgb_raw($fileraw);
		$ACVflag = 1;
	}

	readdata($filename);
	
	$filename =~ s/\.\w\w\w$//i;
	my $name = $filename;

	$name =~ s/^.*\///g;
	$name =~ s/^.*\\//g;
	
	$iccname = $filename . ".icc";
	$outname = $filename . "-out.txt";
	
#	open (OUTFILE, "> $outname")
#		or die "cannot create output file: $outname error:$!\n";
		
	prtoutfile();
exit;
#
# check for data values in order
#
	for my $i (1..$#sortdata) {
		if ($sortdata[$i][$colname{'lab_l'}] >= $sortdata[$i-1][$colname{'lab_l'}]) {
			print OUTFILE "\nThe Lab values are not in order.\nCannot make a profile.\n";
			goto errexit;
		}
	}
	
	open (ICCFILE, "> $iccname")
		or die "cannot create output file: $iccname error:$!\n";
	binmode (ICCFILE);
	
	tagtext ('cprt', "Copyright (c) 2017 - Roy V Harrington\r\n\r\n$version\r\n");
	
	tagdesc ('desc', "QTR_$name");
	
	my @indata = ("GRAY\tLAB_L\tLAB_A\tLAB_B\r\n");
	
	foreach my $line (@sortdata) {
	    push @indata, sprintf("%.2f\t%.2f\t%.2f\t%.2f\r\n", 
					$$line[$colname{'gray'}], $$line[$colname{'lab_l'}], 
					$$line[$colname{'lab_a'}], $$line[$colname{'lab_b'}]);
		
	}
	
	tagtext ('Data', join('', @indata));
	
	my @curve;
	my $in_chan;
	my $out_chan;
	my $in_table;
	my $out_table;
	my $clut_table;

	my @lablvals;
	my @labavals;
	my @labbvals;
	my @lablvalsbpc;
	my @labavalsbpc;
	my @labbvalsbpc;
	
	my $max  = $sortdata[0];
	my $maxL = $$max[$colname{'lab_l'}];
	my $maxY = L_to_Y($maxL);
	my $min  = $sortdata[$#sortdata];
	my $minL = $$min[$colname{'lab_l'}];
	my $minY = L_to_Y($minL);
	my $ytmp;
	my $prev = 0;
	my $curr = 0;
	my @wtpt = LAB_to_XYZ($$max[$colname{'lab_l'}], $$max[$colname{'lab_a'}], $$max[$colname{'lab_b'}]);
	my @bkpt = LAB_to_XYZ($$min[$colname{'lab_l'}], $$min[$colname{'lab_a'}], $$min[$colname{'lab_b'}]);

	tagxyz  ('wtpt', @wtpt);
	tagxyz  ('bkpt', @bkpt);

	$prev = 0;
	$curr = 0;
#
# do 51 steps for the soft proof direction
#
    for (my $i=0; $i<=255; $i+=5) {
		my $istep = 100.0*$i/255.0;
		
		while ($istep >= $sortdata[$curr][$colname{'gray'}] && $curr < $#sortdata) {
			$prev = $curr;
			$curr++ if ($curr < $#sortdata);
		}
		
		my @labtmp; my @labtmpbpc; my @xyztmp; my @xyztmpbpc;
		
		$labtmp[0] = interpolate($istep, 
							   $sortdata[$prev][$colname{'gray'}],
							   $sortdata[$curr][$colname{'gray'}],
							   $sortdata[$prev][$colname{'lab_l'}],
							   $sortdata[$curr][$colname{'lab_l'}]);
							   
		$labtmp[1] = interpolate($istep, 
							   $sortdata[$prev][$colname{'gray'}],
							   $sortdata[$curr][$colname{'gray'}],
							   $sortdata[$prev][$colname{'lab_a'}],
							   $sortdata[$curr][$colname{'lab_a'}]);
							   
		$labtmp[2] = interpolate($istep, 
							   $sortdata[$prev][$colname{'gray'}],
							   $sortdata[$curr][$colname{'gray'}],
							   $sortdata[$prev][$colname{'lab_b'}],
							   $sortdata[$curr][$colname{'lab_b'}]);
							   
#		print "istep = ", $istep, " prev = ", $prev, " curr = ", $curr, "\n";
#		print "lab in = ", join(' ', @labtmp), "\n";						
		@xyztmp = @xyztmpbpc = LAB_to_XYZ(@labtmp);
#		print "xyz in = ", join(' ', @xyztmp), "\n";						

		
#		if ($bpcflag) {
			$xyztmpbpc[0] = interpolate($xyztmpbpc[0], $wtpt[0], $bkpt[0], 1.0, 0.0);
			$xyztmpbpc[1] = interpolate($xyztmpbpc[1], $wtpt[1], $bkpt[1], 1.0, 0.0);
			$xyztmpbpc[2] = interpolate($xyztmpbpc[2], $wtpt[2], $bkpt[2], 1.0, 0.0);
#		}
#		else {
			@xyztmp = divdxyz(@xyztmp, @wtpt);
#		}
		
#		print "xyz out = ", join(' ', @xyztmp), "\n";							
		@labtmp = XYZ_to_LAB(multxyz(@xyztmp, @D50));
		@labtmpbpc = XYZ_to_LAB(multxyz(@xyztmpbpc, @D50));
#		print "lab out = ", join(' ', @labtmp), "\n\n";						

		unshift @lablvals, int( $labtmp[0]*652.80 + 0.5);
		unshift @labavals, int(($labtmp[1]+128)*256.0 + 0.5);
		unshift @labbvals, int(($labtmp[2]+128)*256.0 + 0.5);

		unshift @lablvalsbpc, int( $labtmpbpc[0]*652.80 + 0.5);
		unshift @labavalsbpc, int(($labtmpbpc[1]+128)*256.0 + 0.5);
		unshift @labbvalsbpc, int(($labtmpbpc[2]+128)*256.0 + 0.5);
	}
	
#
#  output A2B0 tab: device to PCS (i.e. Gray/RGB to Lab, or Soft-Proof) curve
#	

	if ($ACVflag) {
		$in_chan  = 3;
		$in_table = \@rgbinvert;
		$clut_table = clut_RGB2Lab(@rgbvalid);
	} elsif ($RGBflag) {
		$in_chan  = 3;
		$in_table = $linear_RGB;
		$clut_table = clut_RGB2Lab(1,1,1);
	} else {
		$in_chan  = 1;
		$in_table = $linear_Gray;
		$clut_table = $clut_Gray2Lab;
	}
	
	tagcurv ( 'kTRC', [@lablvalsbpc]);

	$out_table = [@lablvalsbpc, @labavalsbpc, @labbvalsbpc];
	taglut16 ('A2B0', $in_chan, 3, 2, $in_table, $out_table, $clut_table);
	addtag ('A2B2', '');

	$out_table = [@lablvals, @labavals, @labbvals];
	taglut16 ('A2B1', $in_chan, 3, 2, $in_table, $out_table, $clut_table);
	
	
	@curve = ();
	$prev = 0;
	$curr = 0;

#	foreach my $a ( @sortdata) { print join("\t", @$a), "\n";	}

  	@curve = (65535);  # need a dummy entry at end because of legacy L encodings in ICC file
  	
	for my $i (0..255) {
		my $istep = 100.0 - 100.0*$i/255.0;
#		print "istep = ", $istep;
		my $ytmp   = L_to_Y($istep);
		my $yytmp = interpolate($ytmp, 1.0, 0.0, $maxY, $minY);
		$istep = Y_to_L($yytmp);
#		print " ", $istep;
		
		while ($istep <= $sortdata[$curr][$colname{'lab_l'}] && $curr < $#sortdata) {
			$prev = $curr;
			$curr++ if ($curr < $#sortdata);
		}
		$ytmp = interpolate($istep, 
							   $sortdata[$prev][$colname{'lab_l'}],
							   $sortdata[$curr][$colname{'lab_l'}],
							   $sortdata[$prev][$colname{'gray'}],
							   $sortdata[$curr][$colname{'gray'}]
							   );

		$ytmp = (100.0 - $ytmp) / 100.0;
		
#		print " ", $ytmp,"\n";
		unshift @curve, int($ytmp * 65535 + 0.5);
		
	}

#	print join("\n", @curve), "\n";

#
#  output B2A0 tab: PCS to device (i.e. Lab to Gray/RGB) curve
#	
	$in_table = $linear_Lab;
	 
	if ($ACVflag) {
		for my $i (1..514) { push @curve, 128*256; }  # push 0's for a & b
		$in_table = [@curve];
		$out_chan = 3;
		$out_table = \@rgbcurve;
		$clut_table = $clut_Lab2RGB;
	} elsif ($RGBflag) {
		$out_chan = 3;
		$out_table = [@curve, @curve, @curve];
		$clut_table = $clut_Lab2RGB;
	} else {
		$out_chan = 1;
		$out_table = [@curve];
		$clut_table = $clut_Lab2Gray;
	}
	
	taglut16 ('B2A0', 3, $out_chan, 2, $in_table, $out_table, $clut_table);
	addtag ('B2A2', '');

	$prev = 0;
	$curr = 0;

#	foreach my $a ( @sortdata) { print join("\t", @$a), "\n";	}

  	@curve = (65535);  # need a dummy entry at end because of legacy L encodings in ICC file
  	
	for my $i (0..255) {
		my $istep = 100.0 - 100.0*$i/255.0;
		my $ytmp   = L_to_Y($istep);
		my $yytmp = interpolate($ytmp, 1.0, 0.0, $maxY, 0.0);
		$istep = Y_to_L($yytmp);
		
#		print "istep = ", $istep;
		
		if ($istep > $maxL) {
			$ytmp = 1.0;
		} elsif ($istep < $minL) {
			$ytmp = 0.0;
		} else {
		
		while ($istep <= $sortdata[$curr][$colname{'lab_l'}] && $curr < $#sortdata) {
			$prev = $curr;
			$curr++ if ($curr < $#sortdata);
		}
		$ytmp = interpolate($istep, 
							   $sortdata[$prev][$colname{'lab_l'}],
							   $sortdata[$curr][$colname{'lab_l'}],
							   $sortdata[$prev][$colname{'gray'}],
							   $sortdata[$curr][$colname{'gray'}]
							   );

		$ytmp = (100.0 - $ytmp) / 100.0;
		}
		
#		print " ", $ytmp,"\n";
		unshift @curve, int($ytmp * 65535 + 0.5);
		
	}

#	print join("\n", @curve), "\n";

#
#  output B2A0 tab: PCS to device (i.e. Lab to Gray/RGB) curve
#	
	$in_table = $linear_Lab;
	 
	if ($ACVflag) {
		for my $i (1..514) { push @curve, 128*256; }  # push 0's for a & b
		$in_table = [@curve];
		$out_chan = 3;
		$out_table = \@rgbcurve;
		$clut_table = $clut_Lab2RGB;
	} elsif ($RGBflag) {
		$out_chan = 3;
		$out_table = [@curve, @curve, @curve];
		$clut_table = $clut_Lab2RGB;
	} else {
		$out_chan = 1;
		$out_table = [@curve];
		$clut_table = $clut_Lab2Gray;
	}
	
	taglut16 ('B2A1', 3, $out_chan, 2, $in_table, $out_table, $clut_table);
	
	taglut8 ('gamt', 3, 1, 2, $linear_Lab, $gamut_yes, $clut_Lab2Gray);
	
	packtags();
	packheader();
	
#	print ICCFILE $header;
#	print ICCFILE $taghdr;
	
#	foreach my $tagref (@tagtable)
#		{ print ICCFILE $tagref->{'value'}; }

#	close (ICCFILE);

	print OUTFILE "\nCreated ICC file $iccname\n";
	
errexit:
	close (OUTFILE);
	
#	if ($^O eq "darwin") {
#		system ("open -e \"$outname\"");
#		}
#	else {
#		system ("notepad \"$outname\"");
#	}

	exit;

sub packheader
{
	$header = pack ( "N3 A4 A4 A4 n6 A4 N10 A4 N", (
	
		$totalsize,		# size
		0,				# CMM type
		0x02100000,		# version 2.1
		"prtr",			# class
		$RGBflag ? "RGB" : "GRAY",			# space
		"Lab", 			# PCS
		gettime(),		# datetime
		"acsp",			# signature
		0,				# platform
		0,0,0,0,0,0,	# fill
		getxyz(@D50),	# D50 Illuminant
		"QTR",			# creator
		0				# profile ID
	));
	# pad out to 128 bytes
	while (length ($header) < 128) {
		 $header .= pack ( "x" );
	}

}

sub tagtext
{
	my $type = shift;
	my $str = shift;
	
	my $tag = pack ("A4 x4 a*", ( "text", $str));
	
	addtag($type, $tag);
}

sub tagdesc
{
	my $type = shift;
	my $str = shift;
	
	my $tag = pack ("A4 x4 N a*", (
		"desc",
		length($str)+1,
		$str
	));
	
	while (length($tag) < length($str)+0x5a) {
		 $tag .= pack ( "x" );
	}
	
	addtag($type, $tag);
}

sub tagxyz
{
	my $type = shift;
	my $x    = shift;
	my $y    = shift;
	my $z    = shift;
	
	my $tag = pack ("A4 x4 NNN", (
		"XYZ",
		getxyz($x,$y,$z)
	));
	
	addtag($type, $tag);
}

sub tagcurv
{
	my $type = shift;
	my $curv = shift;
	
	my $tag = pack ("A4 x4 N", (
		"curv",
		scalar (@{$curv})
	));
	
	foreach my $val (@{$curv}) {
		$tag .= pack ("n", $val);
	}
	
	addtag($type, $tag);
}

#
# taglut16 (type, ichan, ochan, ngrid, itab, otab, clut)
#
sub taglut16
{
	my $type = shift;
	my $ichan = shift;
	my $ochan = shift;
	my $ngrid = shift;
	my $itab = shift;
	my $otab = shift;
	my $clut = shift;
	
	my $tag = pack ("A4 x4 CCCx N9 nn", (
		"mft2",
		$ichan, $ochan, $ngrid,
		65536, 0, 0,
		0, 65536, 0,
		0, 0, 65536,
		scalar(@$itab)/$ichan, scalar(@$otab)/$ochan
	));
	
	foreach my $val (@{$itab}) {
		$tag .= pack ("n", $val);
	}
	
	foreach my $val (@{$clut}) {
		$tag .= pack ("n", $val);
	}
	
	foreach my $val (@{$otab}) {
		$tag .= pack ("n", $val);
	}
	
	addtag($type, $tag);
}

#
# taglut8 (type, ichan, ochan, ngrid, itab, otab, clut)
#
sub taglut8
{
	my $type = shift;
	my $ichan = shift;
	my $ochan = shift;
	my $ngrid = shift;
	my $itab = shift;
	my $otab = shift;
	my $clut = shift;
	
	my $tag = pack ("A4 x4 CCCx N9", (
		"mft1",
		$ichan, $ochan, $ngrid,
		65536, 0, 0,
		0, 65536, 0,
		0, 0, 65536,
	));
	
#	foreach my $val (@{$itab}) {
	for my $val (0..255) {
		$tag .= pack ("C", $val);
	}
	for my $val (0..255) {
		$tag .= pack ("C", $val);
	}
	for my $val (0..255) {
		$tag .= pack ("C", $val);
	}
	
	foreach my $val (@{$clut}) {
		$tag .= pack ("C", int($val/257));
	}
	
#	foreach my $val (@{$otab}) {
	for my $val (0..255) {
		$tag .= pack ("C", 0);
	}
	
	addtag($type, $tag);
}

sub addtag
{
	my $type = shift;
	my $tag = shift;
	
	while (length($tag) & 3) {
		 $tag .= pack ( "x" );
	}
	
	my $tagref = {};
	$tagref->{'type'}  = $type;
	$tagref->{'value'} = $tag;
	push (@tagtable, $tagref);
}

sub packtags
{
	my $numtags = scalar(@tagtable);
	my $tagtype;
	my $tagsize;
	my $prevoffset;
	my $prevsize;
	
	$totalsize = 128 + 4 + (12 * $numtags);
	
	$taghdr = pack ("N", $numtags);
	
	foreach my $tagref (@tagtable) {
		
		$tagsize = length( $tagref->{'value'} );
		
		if ($tagsize) {
			$taghdr .= pack ("A4 N N", ( $tagref->{'type'}, $totalsize, $tagsize ));
			$prevsize = $tagsize;
			$prevoffset = $totalsize;
		}
		else {
			$taghdr .= pack ("A4 N N", ( $tagref->{'type'}, $prevoffset, $prevsize ));
		}
		
		$totalsize += $tagsize;
	};
	
}

sub gettime
{
	my ($sec, $min, $hour, $mday, $mon, $year) = localtime();
	return ($year, $mon, $mday, $hour, $min, $sec);
}

sub getxyz
{
	my $x = shift;
	my $y = shift;
	my $z = shift;
	return map { int ($_ * 65536 + 0.5) } ($x, $y, $z);
}

sub multxyz
{
	my $x1 = shift;
	my $y1 = shift;
	my $z1 = shift;
	my $x2 = shift;
	my $y2 = shift;
	my $z2 = shift;
	
	return ($x1*$x2, $y1*$y2, $z1*$z2);
}

sub divdxyz
{
	my $x1 = shift;
	my $y1 = shift;
	my $z1 = shift;
	my $x2 = shift;
	my $y2 = shift;
	my $z2 = shift;
	
	return ($x1/$x2, $y1/$y2, $z1/$z2);
}

sub LAB_to_XYZ
{
	my $lab_l = shift;
	my $lab_a = shift;
	my $lab_b = shift;

	my $var_y = ($lab_l + 16.0)/116.0;
	my $var_x = ($lab_a / 500.0) + $var_y;
	my $var_z =  $var_y - ($lab_b / 200.0);

	my $var_y3 = $var_y * $var_y * $var_y;
	my $var_x3 = $var_x * $var_x * $var_x;
	my $var_z3 = $var_z * $var_z * $var_z;

	$var_y = ($var_y3 > 0.008856451679) ? $var_y3 : ($var_y - (16.0 / 116.0)) / 7.7870370370371;
	$var_x = ($var_x3 > 0.008856451679) ? $var_x3 : ($var_x - (16.0 / 116.0)) / 7.7870370370371;
	$var_z = ($var_z3 > 0.008856451679) ? $var_z3 : ($var_z - (16.0 / 116.0)) / 7.7870370370371;

	($var_x, $var_y, $var_z) = multxyz($var_x, $var_y, $var_z, @D50);
	return ($var_x, $var_y, $var_z);
}

sub XYZ_to_LAB
{
	my $var_x = shift;
	my $var_y = shift;
	my $var_z = shift;
	
	($var_x, $var_y, $var_z) = divdxyz($var_x, $var_y, $var_z, @D50);
	
	my $var_y3 = $var_y ** (1.0/3.0);
	my $var_x3 = $var_x ** (1.0/3.0);
	my $var_z3 = $var_z ** (1.0/3.0);
	
	$var_y = ($var_y > 0.008856451679) ? $var_y3 : (903.2962962963 * $var_y + 16.0) / 116.0;
	$var_x = ($var_x > 0.008856451679) ? $var_x3 : (903.2962962963 * $var_x + 16.0) / 116.0;
	$var_z = ($var_z > 0.008856451679) ? $var_z3 : (903.2962962963 * $var_z + 16.0) / 116.0;
	
	my $lab_l = (116.0 * $var_y) - 16.0;
	my $lab_a =  500.0 * ($var_x - $var_y);
	my $lab_b =  200.0 * ($var_y - $var_z);
	
	return ($lab_l, $lab_a, $lab_b);
	
}

sub L_to_Y
{
	my $val = shift;
	
	 return $val / 903.2962962963
	 	 if ($val < 8.0);

	$val = ($val + 16.0)/116.0;
	return $val * $val * $val;
}

sub Y_to_L
{
	my $val = shift;
	
	return $val * 903.2962962963
		if ($val < 0.008856451679);
		
	$val = $val ** (1.0/3.0);
	return ($val * 116) - 16.0;
}

sub Y_to_d
{
	my $val = shift;
	
	return 4.0 if ($val <= 0.0001);
	return - (log($val) / log(10));
}

sub d_to_Y
{
	my $val = shift;

	return (10 ** (-$val));
}

sub interpolate
{
	my $inval = shift;
	my $inmax = shift;
	my $inmin = shift;
	my $outmax = shift;
	my $outmin = shift;
	
	if ($inval == $inmin)
		{ return $outmin; }
	if ($inval == $inmax)
		{ return $outmax; }
	return $outmin + (($outmax - $outmin) * ($inval - $inmin) / ($inmax - $inmin));
}

sub readdata
{
	my $fname = shift;
	
	my $inputfile;
	my @inputarr;
	my $comma_flag = ($fname =~ m/csv$/i);
    my $cgats_flag = 0;
	
	@datafile = ();
	@sortdata = ();
	$numrows = 0;
	$numcols = 0;
	%colname = ();

#	open (INFILE,  $fname)
#		or die "file not found: $fname error:$!\n";

	{
		local $/;
		$inputfile = <STDIN>;
		$inputfile =~ tr/\r/\n/;
		@inputarr = split ( /\n/, $inputfile );
	}
	
#	close (INFILE);
		
	foreach my $dline (@inputarr) {
	
		chomp($dline);
		$dline = uc($dline);
		$dline =~ s/,/./g if !$comma_flag;	# convert commas and ignore leading/trailing spaces
        # clean out info header in CGATS files
        if ($dline =~ m/^CGATS/) { $cgats_flag = 1; }
        $dline =~ s/^(CGATS|ORIGIN|INSTR|DESCR|MEASU|ILLUM|OBSER|FILTE|WEIGH|KEYWO|DEVCA|CREAT).*//;
        $dline =~ s/LINEARIZE=//;
        $dline =~ s/"//g;
		$dline =~ s/^\s*//;
		$dline =~ s/\s*$//;
		$dline =~ s/[#;].*//;		# ignore comments
		next unless $dline;

		my @arr;
		if ($comma_flag)
			{ @arr = split (/,/ , $dline); }
		else
			{ @arr = split (/\s+/ , $dline); }

		next if (scalar(@arr) < $numcols);
		if (scalar(@arr) > $numcols) {
			@datafile = ();
			$numrows = 0;
			$numcols = scalar(@arr);
		}
		$datafile[$numrows] = \@arr;
		$numrows++;
	}
#
# handle single line like a list
#	
	if ($numrows == 1) {
		my $data = $datafile[0];
		$numrows = 0;
		$numcols = 1;
		foreach my $val (@$data) {
			my @arr = ($val);
			$datafile[$numrows] = \@arr;
			$numrows++;
		}
	}
	
#	foreach my $a ( @datafile) { print $a, "\t", join("\t", @$a), "\n";	}
	
	my $hdrnames = @datafile[0];
	for (my $i=0; $i < $numcols; $i++) {
		#
		# find which column has which data
		#
		my $hdr = $$hdrnames[$i];
		if (namein($hdr, ['GRAY','GREY','STEP']))			{ $colname{'gray'} = $i; }
		
		elsif (namein($hdr, ['LAB_L','LAB','L*','L']))		{ $colname{'lab_l'} = $i; }
		elsif (namein($hdr, ['LAB_A','A*','A']))		{ $colname{'lab_a'} = $i; }
		elsif (namein($hdr, ['LAB_B','B*','B']))		{ $colname{'lab_b'} = $i; }
	
		elsif (namein($hdr, ['XYZ_X','X']))					{ $colname{'xyz_x'} = $i; }
		elsif (namein($hdr, ['XYZ_Y','Y']))					{ $colname{'xyz_y'} = $i; }
		elsif (namein($hdr, ['XYZ_Z','Z']))					{ $colname{'xyz_z'} = $i; }
	
		elsif (namein($hdr, ['RGB_R','RGB']))				{ $colname{'rgb'}   = $i; }
	
		elsif (namein($hdr, ['DENSITY','DENS','D','VISUAL','V']))
															{ $colname{'dens'}  = $i; }
	}
	
	if (scalar(%colname)) {
		shift (@datafile);
		$numrows--;
	}
	else {
#
# without headers try to decipher what column is what
#
		my @maxdata;
		my @mindata;
	
		for my $i (0..$#datafile) {
			#
			# get maximum and minimum values for each column
			#
			my $data = $datafile[$i];

			for my $j (0..$#$data) {
				$maxdata[$j] = $$data[$j]
					if ($i == 0 || $maxdata[$j] < $$data[$j]);
				$mindata[$j] = $$data[$j]
					if ($i == 0 || $mindata[$j] > $$data[$j]);
			}
		}
		
#		print "min =\t", join("\t", @mindata), "\n";
#		print "max =\t", join("\t", @maxdata), "\n";

		for my $i (0..$#maxdata) {
			if ($mindata[$i] == 0 && $maxdata[$i] == 100)
					{ $colname{'gray'}  = $i if (!exists($colname{'gray'}));  }
			elsif ($mindata[$i] == 0 && $maxdata[$i] == 255)
					{ $colname{'rgb'}   = $i if (!exists($colname{'rgb'}));  }
			elsif ($mindata[$i] > -20 && $maxdata[$i] < 20) {
				if (!exists($colname{'lab_a'}) && exists($colname{'lab_l'}) &&
							$colname{'lab_l'} == $i-1)
					 { $colname{'lab_a'} = $i; next; }
				if (!exists($colname{'lab_b'}) && exists($colname{'lab_a'}) &&
							$colname{'lab_a'} == $i-1)
					 { $colname{'lab_b'} = $i; next; }
			}

			if ($mindata[$i] >= 0) {
				if ($maxdata[$i] < 1)
					{ $colname{'xyz_y'} = $i if (!exists($colname{'xyz_y'})); }
				elsif ($maxdata[$i] < 3)
					{ $colname{'dens'}  = $i if (!exists($colname{'dens'}));  }
				elsif ($maxdata[$i] >= 80 && $maxdata[$i] < 100)
					{ $colname{'lab_l'} = $i if (!exists($colname{'lab_l'})); }
			}
		}
	}

	if (!exists($colname{'gray'}) && exists($colname{'rgb'})) {
		#
		# create a gray entry from rgb values
		#
		$colname{'gray'} = $numcols;
		foreach my $line (@datafile) {
			$$line[$numcols] = sprintf("%.2f", 100.0 - (100.0 * $$line[$colname{'rgb'}] / 255.0));
		}
		$numcols++;
	}

	if (exists($colname{'dens'}) && !exists($colname{'lab_l'})) {
		#
		# create a lab_l entry from density
		#
		$colname{'lab_l'} = $numcols;
		foreach my $line (@datafile) {
			$$line[$numcols] = sprintf("%.2f", Y_to_L(d_to_Y($$line[$colname{'dens'}])));
		}
		$numcols++;
	}
	
	if (!exists($colname{'lab_a'})) {
		#
		# create a lab_a entry = 0
		#
		$colname{'lab_a'} = $numcols;
		foreach my $line (@datafile) {
			$$line[$numcols] = 0;
		}
		$numcols++;
	}
	
	if (!exists($colname{'lab_b'})) {
		#
		# create a lab_b entry = 0
		#
		$colname{'lab_b'} = $numcols;
		foreach my $line (@datafile) {
			$$line[$numcols] = 0;
		}
		$numcols++;
	}
	
	if (exists($colname{'lab_l'}) && !exists($colname{'dens'})) {
		#
		# create a density entry from lab_l
		#
		$colname{'dens'} = $numcols;
		foreach my $line (@datafile) {
			$$line[$numcols] = sprintf("%.3f", Y_to_d(L_to_Y($$line[$colname{'lab_l'}])));
		}
		$numcols++;
	}
	
	@sortdata = sort datacompare @datafile;
	
	if (!exists($colname{'gray'})) {
		#
		# create a gray/step entry
		#
		my $nsteps;
		
		$colname{'gray'} = $numcols;
		$numcols++;
		foreach my $ns (21, 11, 6, 26, 51, 16, $numrows) {
		    $nsteps = $ns;
			last if ($numrows / $nsteps == int($numrows / $nsteps));
		}

		my $gray = 0.0;
		my $n = 0;
		my $ndups = $numrows / $nsteps; 
		my $step = 100.0 / ($nsteps - 1);
		foreach my $line (@sortdata) {
			$$line[$colname{'gray'}] = sprintf("%.2f", $gray);
			$n += 1;
			if ($n == $ndups) {
				$gray += $step;
				$n = 0;
			}
		}
	}

	{
		my @tmpdata;
		my $numvals = 0;
		my $avgval;
		my @avgarr;
		
		foreach my $line (@sortdata) {
			if ($numvals == 0) {
				@avgarr = @{$line};
				$numvals = 1;
			}
			else {
				if ($$line[$colname{'gray'}] == $avgarr[$colname{'gray'}]) {
						$avgarr[$colname{'lab_l'}] += $$line[$colname{'lab_l'}];
						$avgarr[$colname{'lab_a'}] += $$line[$colname{'lab_a'}];
						$avgarr[$colname{'lab_b'}] += $$line[$colname{'lab_b'}];
						$avgarr[$colname{'dens'}]  += $$line[$colname{'dens'}];
						$numvals += 1;
				} else {
						my @tmparr = @avgarr;
						$tmparr[$colname{'lab_l'}] /= $numvals;
						$tmparr[$colname{'lab_a'}] /= $numvals;
						$tmparr[$colname{'lab_b'}] /= $numvals;
						$tmparr[$colname{'dens'}]  /= $numvals;
						push @tmpdata, \@tmparr;
						@avgarr = @{$line};
						$numvals = 1;
				}
			}
		}
		$avgarr[$colname{'lab_l'}] /= $numvals;
		$avgarr[$colname{'lab_a'}] /= $numvals;
		$avgarr[$colname{'lab_b'}] /= $numvals;
		$avgarr[$colname{'dens'}]  /= $numvals;
		push @tmpdata, \@avgarr;
		@sortdata = @tmpdata;
	}
	

	
#	foreach my $a ( @datafile) { print join("\t", @$a), "\n";	}
#	print "\n";
#	foreach my $a ( @sortdata) { print join("\t", @$a), "\n";	}
#	print "\n";
	
#	print "# cols found = ", scalar(%colname), "\n";
#	print join (' ', %colname), "\n";
#	exit;
}


sub read_rgb_raw
{
	my $fname = shift;
	
	my $inputfile;
	my @inputarr;
	my (@rlist, @glist, @blist);
	my ($rvalid, $gvalid, $bvalid);

	open (INFILE,  $fname)
		or die "file not found: $fname error:$!\n";

	{
		local $/;
		$inputfile = <INFILE>;
	}
	
	length ($inputfile) == 256*3*2
		or die "file $name incorrect size\n";

#
# try both formats Mac & PC but try the natural one first
#
	my @frmtlist = ($^O eq "darwin") ? ("n1536","v1536","n1536") : ("v1536","n1536","v1536");

	foreach my $frmt (@frmtlist) {
	
		@inputarr = unpack ($frmt, $inputfile);
		
		(@rlist, @glist, @blist) = ();
		for my $i (0..255) {
			push @rlist, shift @inputarr;
			push @glist, shift @inputarr;
			push @blist, shift @inputarr;
		}
		
		$rvalid = isvalid_curve( \@rlist );
		$gvalid = isvalid_curve( \@glist );
		$bvalid = isvalid_curve( \@blist );
		
		last if ($rvalid + $gvalid + $bvalid > 0);
	}
	
	@rgbvalid = ($rvalid, $gvalid, $bvalid);
	$rlist[255] = 65535;
	$glist[255] = 65535;
	$blist[255] = 65535;
	@rgbcurve = (@rlist, @glist, @blist);
	
	@rlist = invertcurve( \@rlist );
	@glist = invertcurve( \@glist );
	@blist = invertcurve( \@blist );
	
	@rgbinvert = (@rlist, @glist, @blist);
}

#
# invert a 256 x 16bit curve
#
sub invertcurve
{
	my $in = shift;
	my @out;
	my $j = 0;
	
	for my $i (0..255) {
		while ($j < 255 && $i*257 >= $$in[$j+1]) { $j++; }
		
		my $val = $j * 257;
		$val += 257 * ($i*257 - $$in[$j]) / ($$in[$j+1] - $$in[$j])
			if ($j < 255 && $$in[$j+1] != $$in[$j]);
		push @out, $val; 
	}

	return @out;
}

#
# is valid curve ?
#
sub isvalid_curve
{
	my $in = shift;

	for my $i (1..255) {
		if ($$in[$i] <= $$in[$i-1]) {
			return 0;
		}
	}

	return 1;
}

#
# create a special clut depending on R,G,B curves
#   only map the curves wanted
#
sub clut_RGB2Lab
{
	my $rflag = shift;
	my $gflag = shift;
	my $bflag = shift;
	my $tot = $rflag + $gflag + $bflag;
	
	my @clut = ();
	if ($tot == 0) {
		$tot = 1;
		print OUTFILE "\nWARNING: None of the RGB curves are in ascending order.\n",
					  "Cannot make the Soft Proofing side of profile.\n";
	}
	
	for my $r (0..1) {
		for my $g (0..1) {
			for my $b (0..1) {
				my $val = ($r*$rflag + $g*$gflag + $b*$bflag) * 65535 / $tot;
				push @clut, ($val, $val, $val);
			}
		}
	}
	return \@clut;
}

#
# search for equivalent name
#
sub namein
{
	my $name = shift;
	my $list = shift;
	
	foreach my $entry (@$list) {
		return 1 if ($name eq $entry);
	}
	return 0;
}

sub datacompare
{
	if (exists($colname{'gray'}))
		{ return ($$a[$colname{'gray'}] <=> $$b[$colname{'gray'}]); }
	if (exists($colname{'lab_l'}))
		{ return ($$b[$colname{'lab_l'}] <=> $$a[$colname{'lab_l'}]); }
	return 0;
}

sub prtoutfile
{
	my @linear;
	
#	print OUTFILE "$version\n";
#	print OUTFILE "\nFile: $outname\n";
#	print OUTFILE "Step\tDens\tLab\tA\tB\t\n";
	foreach my $line (@sortdata) {
		
		my $step  = $$line[$colname{'gray'}];
		my $lab_l = $$line[$colname{'lab_l'}];
		my $lab_a = $$line[$colname{'lab_a'}];
		my $lab_b = $$line[$colname{'lab_b'}];
		my $dens  = $$line[$colname{'dens'}];

		my $str;
		my $x;
		for (0..60) { $str .= " "; }
		substr ($str, 0, 1) = "-";
		substr ($str, 60, 1) = "+";
		substr ($str, 30, 1) = "|";
		substr ($str, $lab_l*.6, 1) = "L" if ($lab_l >= 0 && $lab_l <= 100);
		
		$x = $lab_a*4+30; $x = 0 if ($x < 0); $x = 60 if ($x > 60);
		substr ($str, $x, 1) = "a";
		
		$x = $lab_b*4+30; $x = 0 if ($x < 0); $x = 60 if ($x > 60);
		substr ($str, $x, 1) = "b";
				
#		printf OUTFILE "%.2f\t%.3f\t%.2f\t%.2f\t%.2f\t%s\n", 
		#	$step, $dens, $lab_l, $lab_a, $lab_b, $str;
		printf  "%.2f\t%.2f\t%.2f\t%.2f\n", $step, $lab_l, $lab_a, $lab_b;

		push (@linear, $lab_l);
	}
	
}


