//
// QTR StepWedge Tool.jsx
//
// Copyright © 2009-2010, Roy Harrington.  All rights reserved.

/*
@@@BUILDINFO@@@ QTR StepWedge Tool.jsx 1.0.0.1
*/

/*

// BEGIN__HARVEST_EXCEPTION_ZSTRING

<javascriptresource>
<name>$$$/JavaScripts/QTRStepWedge/Menu=QTR StepWedge Tool...</name>
<about>$$$/JavaScripts/QTRStepWedge/About=QTR StepWedge Tool^r^rCopyright (c) 2009-2010, Roy Harrington. All rights reserved.^r^rProcesses Scanned Stepwedges for Profile Creation^rPass One for Calibration - Pass Two for Reading Target Data.</about>
<category>aabThisPutsMeAtTheTopOfTheMenu</category>
</javascriptresource>

// END__HARVEST_EXCEPTION_ZSTRING

*/
// enable double clicking from the Macintosh Finder or the Windows Explorer
#target photoshop

var logging = false;
var logFile;

var numSteps = 20;
var numCalSteps = 20;
var numReadSteps = 21;

var stepReadings = Array();
var stepLines;

var wedgeBounds, wedgeOrigin, wedgeSize;
var stepHeight, stepWidth;

var levelsBlack, levelsWhite, levelsGamma, levelsOutBlack, levelsOutWhite;

var origBlack, origGray, origWhite;
var convBlack, convGray, convWhite;
var targBlack, targGray, targWhite;
var stepBlack=19, stepGray=7, stepWhite=0;
var labBlack=11,  labGray=50,  labWhite=95;

var White = new SolidColor();
White.gray.gray = 0;
var Black = new SolidColor();
Black.gray.gray = 100;

var layerName = "QTR Stepwedge Sample Data";
var QTRstepwedgeOptionsKey = "QTR Stepwedge Options Key";
var optCalSteps  = 101;
var optReadSteps = 102;
var optStepBlack = 103;
var optStepGray  = 104;
var optStepWhite = 105;
var optLabBlack  = 106;
var optLabGray   = 107;
var optLabWhite  = 108;

var doc, layer, sampler;
var calibMode = false;

// Execute startup stub.

var saveRulerUnits = app.preferences.rulerUnits;
app.preferences.rulerUnits = Units.PIXELS; // selections are always in pixels

try { main(); }
catch (e) { alert('Error: (' + e + ') on line ' + e.line); }

app.preferences.rulerUnits = saveRulerUnits;


function main()
{
    	// Basic error checking.  
    	if (app.documents.length == 0)
    	{
    		alert("No step wedge image currently loaded") ;
    		return;
    	}

	doc = app.activeDocument;

    	if (doc.bitsPerChannel != BitsPerChannelType.SIXTEEN)
    	    doc.bitsPerChannel =  BitsPerChannelType.SIXTEEN;

    	if (doc.mode != DocumentMode.GRAYSCALE &&
	    doc.mode != DocumentMode.RGB)
	    {
	    alert("File must be either Grayscale or RGB")
	    return;
	    }

	try
	{
		wedgeBounds = doc.selection.bounds;
		wedgeOrigin = Array(wedgeBounds[0].value, wedgeBounds[1].value);
		wedgeSize   = Array(wedgeBounds[2].value-wedgeBounds[0].value, 
			      	    wedgeBounds[3].value-wedgeBounds[1].value);
	}
	catch(e)
	{
		wedgeOrigin = [0, 0];
		wedgeSize   = Array(doc.width, doc.height);
		doc.selection.selectAll();
		wedgeBounds = doc.selection.bounds;
	}

	getOptions();

	try
		{
		layer = doc.artLayers.getByName(layerName);
		doc.activeLayer = layer;
		}
	catch(e)
		{
	    	if (doc.artLayers.length != 1)
		    {
		    alert("File cannot have multiple layers, flatten image.")
		    return;
		    }
		calibMode = true;
		}
	logOpen();


	// Run the main body of the script

	if (calibMode == true)
		{
		if (dialogCalibrate() == 2)
			return;

		layer = doc.activeLayer.duplicate();
		layer.name = layerName;
		doc.activeLayer = layer;

		numSteps = numCalSteps;
	        doc.suspendHistory("QTR Stepwedge Setup", "setupWedge()");
	        doc.suspendHistory("QTR Stepwedge Calibrate", "calibrateWedge()");
		dialogCalDone();
		}
	else 
		{
 		if (dialogReadData() == 2)
			return;

		numSteps = numReadSteps;
	        doc.suspendHistory("QTR Stepwedge Setup", "setupWedge()");
      		doc.suspendHistory("QTR Stepwedge Read Data", "readWedge()");
		displayData();
		}

	saveOptions();
	// restore selection of wedge
	doc.selection.select(  Array(	Array(wedgeBounds[0].value, wedgeBounds[1].value),
					Array(wedgeBounds[2].value, wedgeBounds[1].value),
					Array(wedgeBounds[2].value, wedgeBounds[3].value),
					Array(wedgeBounds[0].value, wedgeBounds[3].value)));

	logClose();
}

function showAbout()
{
    var dataRes = 	
	"dialog { properties:{ resizeable:false, orientation:'column' }, \
		text: 'QTR Scanned StepWedge Tool', frameLocation:[300,300], \
		st1:StaticText { text:'QuadToneRIP Stepwedge Tool' }, \
		st2:StaticText { text:'Version 1.0' }, \
		st3:StaticText { text:'Copyright © 2010, Roy Harrington' }, \
		btn:Button { text:'Continue', properties:{name:'ok'} } \
	}";
	var win = new Window(dataRes);
	win.show();
}

function dialogCalibrate()
{
    var dataRes = 	
	"dialog { properties:{ resizeable:false }, \
		text: 'QTR Scanned StepWedge Tool', frameLocation:[200,200], \
		st1:StaticText { text:'QuadToneRIP Stepwedge Tool -- Calibration Mode' }, \
		gr1:Group { orientation:'row', \
			st2:StaticText { text:'Number of Steps in Wedge:' } , \
			numCalSteps:EditText { characters:6 }, \
		}, \
		pn1: Panel { orientation:'row', alignChildren:'top',\
			text: 'Calibrated Patch Values', \
			gr1: Group { orientation:'column', alignment:'left', \
				st1: StaticText { text:'Patch' }, \
				st2: StaticText { text:'White (dMin)' }, \
				st3: StaticText { text:'Middle Gray' }, \
				st4: StaticText { text:'Black (dMax)' }, \
			}, \
			gr2: Group { orientation:'column', alignment:'left', \
				st1: StaticText { text:'Step Number' }, \
				stepWhite: EditText { characters:6 }, \
				stepGray:  EditText { characters:6 }, \
				stepBlack: EditText { characters:6 }, \
			}, \
			gr3: Group { orientation:'column', alignment:'left', \
				st1: StaticText { text:'Lab Value' }, \
				labWhite: EditText { characters:6 }, \
				labGray:  EditText { characters:6 }, \
				labBlack: EditText { characters:6 }, \
			}, \
		}, \
		bt1: Group { orientation:'row', alignment:'right', \
			aboutBtn: Button { text:'About' }, \
			st1: StaticText { characters:4 }, \
			cancelBtn: Button { text:'Cancel', properties:{name:'cancel'} }, \
			buildBtn: Button { text:'Calibrate', properties:{name:'ok'} }, \
		}, \
	}";


    while (true)
	{
	var win = new Window(dataRes);
	
	win.bt1.aboutBtn.onClick = showAbout;
	win.gr1.numCalSteps.text = numCalSteps;

	win.pn1.gr2.stepWhite.text = stepWhite;
	win.pn1.gr2.stepGray.text  = stepGray;
	win.pn1.gr2.stepBlack.text = stepBlack;

	win.pn1.gr3.labWhite.text = labWhite;
	win.pn1.gr3.labGray.text  = labGray;
	win.pn1.gr3.labBlack.text = labBlack;

	if (win.show() == 2) return 2;	// cancel

	numCalSteps = Number(win.gr1.numCalSteps.text);

	stepWhite = Number(win.pn1.gr2.stepWhite.text);
	stepGray  = Number(win.pn1.gr2.stepGray.text);
	stepBlack = Number(win.pn1.gr2.stepBlack.text);

	labWhite = Number(win.pn1.gr3.labWhite.text);
	labGray  = Number(win.pn1.gr3.labGray.text);
	labBlack = Number(win.pn1.gr3.labBlack.text);

	if (numCalSteps < 3 || numCalSteps > 255)
		{ alert("Illegal number of steps"); continue; }
	if (stepWhite < 0 || stepWhite >= numCalSteps)
		{ alert("Illegal White Step Number"); continue; }
	if (stepGray < 0 || stepGray >= numCalSteps)
		{ alert("Illegal Gray Step Number"); continue; }
	if (stepBlack < 0 || stepBlack >= numCalSteps)
		{ alert("Illegal Black Step Number"); continue; }
	if (labWhite < 90 || labWhite > 100)
		{ alert("Illegal White Lab Number"); continue; }
	if (labGray < 40 || labGray > 60)
		{ alert("Illegal Gray Lab Number"); continue; }
	if (labBlack < 0 || labBlack > 30)
		{ alert("Illegal Black Lab Number"); continue; }
	break;
	}

    return 1;
}


function dialogCalDone()
{
	var dataRes = 	
	"dialog { properties:{ resizeable:false }, \
		text: 'QTR Scanned StepWedge Tool', frameLocation:[200,200], \
		st1:StaticText { text:'QuadToneRIP Stepwedge Tool -- Calibration Complete' }, \
		pn1: Panel { orientation:'row', alignChildren:'top',\
			text: 'Levels Correction Values', \
			gr1: Group { orientation:'column', alignment:'center', \
				st0: StaticText { text:'Field' }, \
				st1: StaticText { text:'InBlack' }, \
				st2: StaticText { text:'InWhite' }, \
				st3: StaticText { text:'OutBlack' }, \
				st4: StaticText { text:'OutWhite' }, \
				st5: StaticText { text:'Gamma' }, \
			}, \
			gr2: Group { orientation:'column', alignment:'center', \
				st1: StaticText { text:'Value' }, \
				levelsBlack: StaticText { text:'' }, \
				levelsWhite: StaticText { text:'' }, \
				levelsOutBlack: StaticText { text:'' }, \
				levelsOutWhite: StaticText { text:'' }, \
				levelsGamma: StaticText { text:'' }, \
			}, \
		}, \
		btnPnl: Group { orientation:'row', alignment:'right', \
			buildBtn: Button { text:'Continue', properties:{name:'ok'} }, \
		}, \
	}";


	var win = new Window(dataRes);
	
	win.pn1.gr2.levelsBlack.text = Math.round(levelsBlack);
	win.pn1.gr2.levelsWhite.text = Math.round(levelsWhite);
	win.pn1.gr2.levelsOutBlack.text = Math.round(levelsOutBlack);
	win.pn1.gr2.levelsOutWhite.text = Math.round(levelsOutWhite);
	win.pn1.gr2.levelsGamma.text = levelsGamma;

	win.show();
}

function dialogReadData()
{
    var dataRes = 	
	"dialog { properties:{ resizeable:false }, \
		text: 'QTR Scanned StepWedge Tool', frameLocation:[200,200], \
		st1:StaticText { text:'QuadToneRIP Stepwedge Tool -- Read Data Mode' }, \
		gr1:Group { orientation:'row', \
			st2:StaticText { text:'Number of Steps in Wedge:' } , \
			numReadSteps:EditText { characters:6 }, \
		}, \
		bt1: Group { orientation:'row', alignment:'right', \
			aboutBtn: Button { text:'About' }, \
			st1: StaticText { characters:4 }, \
			cancelBtn: Button { text:'Cancel', properties:{name:'cancel'} }, \
			buildBtn:  Button { text:'Read Steps', properties:{name:'ok'} }, \
		}, \
	}";


    while (true)
	{
	var win = new Window(dataRes);		
	
	win.bt1.aboutBtn.onClick = showAbout;
	win.gr1.numReadSteps.text = numReadSteps;

	if (win.show() == 2) return 2;	//cancel
	numReadSteps = Number(win.gr1.numReadSteps.text);
	if (numReadSteps < 1 || numReadSteps > 255)
		{ alert("Illegal number of steps"); continue; }
	break;
	}
	return 1;
}

//
function calibrateWedge()
{
	origBlack = getSampleValue(stepBlack);
	origGray  = getSampleValue(stepGray);
	origWhite = getSampleValue(stepWhite);

	targBlack = convertFromLab(labBlack);
	targGray  = convertFromLab(labGray);
	targWhite = convertFromLab(labWhite);

	logMsg("step  = "+stepBlack+","+stepGray+","+stepWhite);
	logMsg("orig  = "+origBlack+","+origGray+","+origWhite);
	logMsg("targ  = "+targBlack+","+targGray+","+targWhite);
	logMsg("lab   = "+labBlack+" ,"+labGray+" ,"+labWhite);

	calculateLevels();
	var a=levelsBlack, b=levelsWhite, c=levelsGamma, d=levelsOutBlack, e=levelsOutWhite;

//	layer.adjustLevels(a, b, 1, d, e);
	layer.adjustLevels(Math.round(a), Math.round(b), 1, Math.round(d), Math.round(e));
	layer.adjustLevels(0, 255, c, 0, 255);

	sampler.remove();
	waitForRedraw();
}
	
// setup and read the patches for stepwedge
function setupWedge() 
{
	sampler = doc.colorSamplers.add(Array(0,0));
	stepHeight = wedgeSize[1];
	stepWidth  = wedgeSize[0]/numSteps;

	for (step = 0; step < numSteps; step++)
		{
		doc.selection.select(getBounds(step));
		layer.applyAverage();
		val = getSampleValue(step) ;
		doc.selection.stroke((val>127?Black:White),1,StrokeLocation.OUTSIDE);
		}
	doc.selection.deselect();
}

function st6(s)
{
	s = s+'';
	switch(s.length)
	{
	case 1: s += '     '; break;
	case 2: s += '    '; break;
	case 3: s += '   '; break;
	case 4: s += '  '; break;
	case 5: s += ' '; break;
	case 6: s += ''; break;
	}
	return s;
}

// setup and read the patches for stepwedge
function readWedge() 
{
	stepReadings = Array();
	stepLines = "Patch \tGray  \tLab   \tA   \tB\n";

	for (step = 0; step < numSteps; step++)
		{
     		sampler.move(getPosition(step));
		labL = sampler.color.lab.l;
		labA = sampler.color.lab.a + 0.5;
		labB = sampler.color.lab.b + 0.5;
		stepReadings[step] = labL;
		labL = labL.toFixed(2);
		labA = labA.toFixed(2);
		labB = labB.toFixed(2);
		gray = 100*step/(numSteps-1);
		gray = gray.toFixed(2);
		stepLines += st6(step)+"\t"+st6(gray)+"\t"+st6(labL)+"\t"+st6(labA)+"\t"+st6(labB)+"\n";
		}
	sampler.remove();
}

var g;

// display data that was read
function displayData()
{
	waitForRedraw();

	var dataRes = 	
	"dialog { properties:{ resizeable:false }, \
		text: 'QTR Scanned StepWedge Tool', frameLocation:[200,200], \
		st1:StaticText { text:'QuadToneRIP Stepwedge Tool -- StepWedge Data' }, \
		msgPnl: Panel { orientation:'column', alignChildren:'left',\
			st2: StaticText { text:'StepWedge Data:' }, \
			et:  EditText   { properties:{multiline:true}, \
					  text:'data table', characters:36 } \
		}, \
		btnPnl: Group { orientation:'row', alignment:'right', \
			cancelBtn: Button { text:'Don\\'t Save', properties:{name:'cancel'} }, \
			buildBtn: Button { text:'Save Data File', properties:{name:'ok'} }, \
		}, \
	}";

//		gfxPnl: Panel { orientation:'column', alignChildren:'left',\
//			gfx: Button { type:'customView', preferredSize:[340,240] }, \
//		}, \
//			graphBtn: Button { text:'Show Graph' }, \
//			st1: StaticText { characters:4 }, \

	var win = new Window(dataRes);		

	win.msgPnl.et.text = stepLines+" ";
//	win.btnPnl.graphBtn.onClick = showGraph;

//	showGraph(win.gfxPnl.graphics);
//	g.onDraw = drawGraph;

	if (win.show() == 1)
		{
		var name = doc.fullName.fullName;
		var file = new File( name.replace(/\....$/, ".txt") );

		file = file.saveDlg();
		if (file != null)
			{
			file.open("w:");
			file.write(stepLines);
			file.close();
			}
		}
}

function showGraph(g)
{
	var white = g.newBrush(g.BrushType.SOLID_COLOR, [1, 1, 1, 1]);
	g.backgroundColor = white;
//	var gray  = g.newBrush(g.BrushType.SOLID_COLOR, [0.3, 0.3, 0.3, 1]);
	var pen = g.newPen(g.PenType.SOLID_COLOR, [0, 0, 0, 1], 1);
//	var red   = g.newBrush(g.BrushType.SOLID_COLOR, [1, 0, 0, 1]);
//	var blue  = g.newBrush(g.BrushType.SOLID_COLOR, [0, 0, 1, 1]);
	g.currentPath  = g.newPath();
	g.moveTo(10,10);
	g.lineTo(20,20);
	g.strokePath(pen);

	for (step = 0; step < numSteps; step++)
		{
		x = (step/numSteps) * 300;
		y = stepReadings[step] * 2;
		if (step == 0)
			g.moveTo(x,y);
		else
			g.lineTo(x,y);
		}
	g.strokePath(pen, g.currentPath);
}

function waitForRedraw() 
{
	var state  = charIDToTypeID("Stte");
	var redraw = charIDToTypeID("RdCm");
	var wait   = charIDToTypeID("Wait");
	var desc   = new ActionDescriptor();
	desc.putEnumerated(state, state, redraw);
	executeAction(wait, desc, DialogModes.NO);
}

function logOpen()
{
	if (logging == false) return;
	var name = doc.fullName.fullName;
	logFile = new File( name.replace(/\....$/, ".log") );
	logFile.open("w:");
}

function logClose()
{
	if (logging == false) return;
	logFile.close();
}

function logMsg(text)
{
	if (logging == false) return;
	logFile.writeln(text);
}

function getPosition(step)
{
	return Array(	Math.round(wedgeOrigin[0] + stepWidth/2 + stepWidth*step), 
			Math.round(wedgeOrigin[1] + stepHeight/2));
}

function getBounds(step)
{
	var pos = getPosition(step);
	var wid = Math.round(stepWidth/4);
	var hgt = Math.round(stepHeight/4);

	return Array( 	Array(pos[0]-wid, pos[1]-hgt),	Array(pos[0]+wid, pos[1]-hgt),
			Array(pos[0]+wid, pos[1]+hgt),	Array(pos[0]-wid, pos[1]+hgt));
}

function getSampleValue(step)
{
	var temp;
        sampler.move(getPosition(step));
    	if (doc.mode == DocumentMode.GRAYSCALE)
		temp = (100-sampler.color.gray.gray)*2.55;
	else if (doc.mode == DocumentMode.RGB)
		temp = (sampler.color.rgb.red*0.3 + sampler.color.rgb.green*0.59 + sampler.color.rgb.blue*0.11);
	else temp = 0;
	return temp;
}

function convertToLab(value)
{
	value = Math.pow(value/255, 2.2);
	if (value >= 0.008856451679)
		return (116 * Math.pow(value, 1/3) - 16);
	else
		return (value * 903.2962962963);
}

function convertFromLab(value)
{
	if (value >= 8)
		value = Math.pow((value+16)/116, 3);
	else
		value = value / 903.2962962963;
	return (Math.pow(value, 1/2.2) * 255);
}

/*
 * calculate levels values to adjust sample layer
 *    do this by iteration of adjustments
 */

function calculateLevels()
{
	levelsBlack = 0;
	levelsWhite = 255;
	levelsOutBlack = 0;
	levelsOutWhite = 255;
	levelsGamma = 1;
	convertSamples();
	var tol = 0.5, inc1 = 1, inc2 = 0.01;

    for (iter=0; iter<6; iter++)
	{
	if (iter == 3) { tol = 0.1, inc1 = 0.1, inc2 = 0.001; }
	while (convWhite > targWhite+tol)
	    {
		if (levelsWhite < 255) levelsWhite += inc1; else levelsOutWhite -= inc1;
		convertSamples();
	    }
	while (convWhite < targWhite-tol)
	    {
		if (levelsOutWhite < 255) levelsOutWhite += inc1; else levelsWhite -= inc1;
		convertSamples();
	    }
	while (convBlack < targBlack-tol)
	    {
		if (levelsBlack > 0) levelsBlack -= inc1; else levelsOutBlack += inc1;
		convertSamples();
	    }
	while (convBlack > targBlack+tol)
	    {
		if (levelsOutBlack > 0) levelsOutBlack -= inc1; else levelsBlack += inc1;
		convertSamples();
	    }
	while (levelsGamma < 2.0 && convGray  < targGray-tol)
		{ levelsGamma += inc2; convertSamples(); }
	while (levelsGamma > 0.5 && convGray  > targGray+tol)
		{ levelsGamma -= inc2; convertSamples(); }
	}
}

/*
 * convert the 3 samples based on levels command
 */

function convertSamples()
{
	convBlack = doLevels(origBlack);
	convGray  = doLevels(origGray);
	convWhite = doLevels(origWhite);
}


/*
 * convert a value [0..255] based on simulation of photoshop levels command
 */

function doLevels(value)
{
	value = (value - levelsBlack)/(levelsWhite - levelsBlack);
	value = (value * (levelsOutWhite - levelsOutBlack)) + levelsOutBlack;
	value = value / 255;
	if (value < 0) value = 0;
	if (value > 1) value = 1;
	return (Math.pow(value, 1/levelsGamma) * 255);
}


/*
 * handle custom options
 */

function getOptions()
{
    try
    {
	optionsDesc = app.getCustomOptions(QTRstepwedgeOptionsKey);
	numCalSteps = optionsDesc.getInteger(optCalSteps);
	numReadSteps = optionsDesc.getInteger(optReadSteps);
	stepBlack = optionsDesc.getInteger(optStepBlack);
	stepGray  = optionsDesc.getInteger(optStepGray);
	stepWhite = optionsDesc.getInteger(optStepWhite);
	labBlack  = optionsDesc.getDouble(optLabBlack);
	labGray   = optionsDesc.getDouble(optLabGray);
	labWhite  = optionsDesc.getDouble(optLabWhite);
    }
    catch(e)
    {
	optionsDesc = new ActionDescriptor();
	saveOptions();
    }
}

function saveOptions()
{
	optionsDesc.putInteger(optCalSteps, numCalSteps);
	optionsDesc.putInteger(optReadSteps, numReadSteps);
	optionsDesc.putInteger(optStepBlack, stepBlack);
	optionsDesc.putInteger(optStepGray, stepGray);
	optionsDesc.putInteger(optStepWhite, stepWhite);
	optionsDesc.putDouble(optLabBlack, labBlack);
	optionsDesc.putDouble(optLabGray, labGray);
	optionsDesc.putDouble(optLabWhite, labWhite);
	app.putCustomOptions(QTRstepwedgeOptionsKey, optionsDesc, true);
}


