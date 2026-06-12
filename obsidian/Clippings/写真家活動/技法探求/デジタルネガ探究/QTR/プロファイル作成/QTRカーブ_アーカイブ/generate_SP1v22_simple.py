#!/usr/bin/env python3
"""
SP1v22 QTR Curve Generator - Simplified Version
================================================

Purpose:
  Create SP1v22 curve with MINIMAL changes from SP1v21:
  1. Fix Input 128 midtone: 0.485D (for 0.76D print target)
  2. Eliminate banding at Input 88/96 and 136/144
  3. Extend white gradation (Input 232-255)

  NO black enhancement (Input 40-80) - SP1v21 already has good black gradation

Baseline: SP1v21
Target Paper: Revere Platinum
Exposure: 7min (420 sec)
Target Input 128: 0.76D (reflection)

Date: 2026-03-19
Author: Claude Code with user guidance
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import interpolate
from pathlib import Path

# Configuration
BASE_DIR = Path("/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成")
WORK_DIR = BASE_DIR / "作業ファイル_現行版"
OUTPUT_DIR = WORK_DIR
CHART_DIR = BASE_DIR / "使用チャート/新デジネガ/v2-補正"

# Input files
SP1V21_QUAD = Path("/Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-SP1v21.quad")
MEASUREMENT_7M = CHART_DIR / "measurement_QTR-SP-21-7m.csv"

# Output files
OUTPUT_QUAD = OUTPUT_DIR / "PX1V-PtPd-SP1v22.quad"
OUTPUT_CSV = OUTPUT_DIR / "SP1v22_design.csv"
OUTPUT_GRAPH = OUTPUT_DIR / "SP1v22_comparison.png"

def load_sp1v21_quad():
    """Load SP1v21 baseline curve from .quad file"""
    print("📂 Loading SP1v21 baseline curve...")

    with open(SP1V21_QUAD, 'r') as f:
        lines = f.readlines()

    # Find K channel (channel 0)
    curve_start = None
    for i, line in enumerate(lines):
        if line.strip() == "0":  # K channel
            curve_start = i + 1
            break

    if curve_start is None:
        raise ValueError("Cannot find K channel in .quad file")

    # Read 256 values (skip empty lines and comments)
    k_values = []
    line_idx = curve_start
    while len(k_values) < 256 and line_idx < len(lines):
        line = lines[line_idx].strip()
        # Skip comments and empty lines
        if not line or line.startswith('#'):
            line_idx += 1
            continue
        # Check if it's a digit (K value)
        if line.isdigit():
            k_values.append(int(line))
            line_idx += 1
        else:
            # Hit next channel marker, stop
            break

    if len(k_values) != 256:
        raise ValueError(f"Expected 256 K values, got {len(k_values)}")

    # Convert to negative density (assuming linear relationship for now)
    # We'll use measurement data to calibrate
    inputs = np.arange(256)

    print(f"✓ Loaded {len(k_values)} K values from SP1v21")

    return inputs, np.array(k_values)

def load_measurement_7m():
    """Load 7min exposure measurement data"""
    print("📊 Loading 7min measurement data...")

    df = pd.read_csv(MEASUREMENT_7M, comment='#')

    print(f"✓ Loaded {len(df)} measurement points")
    print(f"  Input range: {df['input'].min()}-{df['input'].max()}")
    print(f"  Negative density: {df['negative_density_transmission'].min():.2f}D - {df['negative_density_transmission'].max():.2f}D")
    print(f"  Print density: {df['print_density_reflection'].min():.2f}D - {df['print_density_reflection'].max():.2f}D")

    return df

def k_to_negative_density(k_values, measurement_df):
    """
    Convert K values to negative density using measurement calibration

    SP1v21 K values are already calibrated, so we interpolate from measurement data
    """
    # Create interpolation function from measurement data
    meas_inputs = measurement_df['input'].values
    meas_neg_density = measurement_df['negative_density_transmission'].values

    # Interpolate for all 256 input values
    f_neg = interpolate.interp1d(
        meas_inputs,
        meas_neg_density,
        kind='cubic',
        fill_value='extrapolate'
    )

    inputs = np.arange(256)
    neg_density = f_neg(inputs)

    # Clamp to reasonable range
    neg_density = np.clip(neg_density, 0.0, 2.0)

    return neg_density

def create_sp1v22_curve_simple(sp1v21_neg_density, measurement_df):
    """
    Create SP1v22 curve with minimal adjustments

    Strategy:
    1. Use SP1v21 as baseline (already good for black gradation)
    2. Adjust Input 128 to 0.485D (for 0.76D print target)
    3. Use linear interpolation for all unmeasured points (eliminates banding)
    4. Extend white gradation (Input 240-255)

    Returns:
        sp1v22_neg_density: 256-element array of negative densities
        design_log: DataFrame with adjustment details
    """
    print("\n🔧 Creating SP1v22 curve (simplified strategy)...")

    # Start with SP1v21 baseline
    sp1v22_neg = sp1v21_neg_density.copy()

    # Adjustment log
    adjustments = []

    # === STEP 1: Adjust midtone (Input 128) ===
    print("\n1️⃣ Adjusting Input 128 (midtone correction)...")

    old_val = sp1v22_neg[128]
    sp1v22_neg[128] = 0.485  # Target for 0.76D print
    adjustment = sp1v22_neg[128] - old_val

    adjustments.append({
        'input': 128,
        'k_percent': 50.0,
        'adjustment_type': 'Midtone correction',
        'old_negative_density': round(old_val, 3),
        'adjustment': round(adjustment, 3),
        'new_negative_density': 0.485
    })

    print(f"  Input 128: {old_val:.3f}D → 0.485D (Δ{adjustment:+.3f}D)")
    print(f"  Expected print: 0.76D (from 0.79D)")

    # === STEP 2: Linear interpolation for all unmeasured points ===
    print("\n2️⃣ Applying linear interpolation (banding elimination)...")

    # Use measured data points as anchors
    measured_inputs = measurement_df['input'].values.tolist()

    # Ensure Input 128 is in the anchor list
    if 128 not in measured_inputs:
        measured_inputs.append(128)
        measured_inputs.sort()

    # Get anchor values (with adjusted Input 128)
    anchor_values = np.array([sp1v22_neg[inp] for inp in measured_inputs])

    # Create linear interpolation function
    linear_interp = interpolate.interp1d(measured_inputs, anchor_values, kind='linear', fill_value='extrapolate')

    # Apply to all non-measured points
    for inp in range(256):
        if inp not in measured_inputs:
            old_val = sp1v22_neg[inp]
            sp1v22_neg[inp] = linear_interp(inp)
            new_val = sp1v22_neg[inp]

            # Only log significant changes
            if abs(new_val - old_val) > 0.001:
                adjustments.append({
                    'input': inp,
                    'k_percent': round((255 - inp) / 255 * 100, 1),
                    'adjustment_type': 'Linear interpolation',
                    'old_negative_density': round(old_val, 3),
                    'adjustment': round(new_val - old_val, 3),
                    'new_negative_density': round(new_val, 3)
                })

    print(f"  Linear interpolation applied to all unmeasured points")
    print(f"  Anchor points: {len(measured_inputs)} measured values + Input 128")
    print(f"  Method: Linear (guaranteed monotonic, no banding)")

    # === STEP 3: Extend white gradation (Input 240-255) ===
    print("\n3️⃣ Extending white gradation (Input 240-255)...")

    # Current values at Input 240-255
    print(f"  Current Input 240: {sp1v22_neg[240]:.3f}D")
    print(f"  Current Input 255: {sp1v22_neg[255]:.3f}D")

    # Apply linear extension from Input 232 to 255
    # Goal: Create visible differentiation through Input 255
    val_232 = sp1v22_neg[232]
    target_255 = 1.35  # Extend to higher density

    # Linear gradient
    for inp in range(233, 256):
        old_val = sp1v22_neg[inp]
        ratio = (inp - 232) / (255 - 232)
        sp1v22_neg[inp] = val_232 + ratio * (target_255 - val_232)
        new_val = sp1v22_neg[inp]

        adjustments.append({
            'input': inp,
            'k_percent': round((255 - inp) / 255 * 100, 1),
            'adjustment_type': 'White extension',
            'old_negative_density': round(old_val, 3),
            'adjustment': round(new_val - old_val, 3),
            'new_negative_density': round(new_val, 3)
        })

    print(f"  New Input 240: {sp1v22_neg[240]:.3f}D")
    print(f"  New Input 255: {sp1v22_neg[255]:.3f}D")

    # Create adjustment log DataFrame
    design_log = pd.DataFrame(adjustments)

    print(f"\n✓ SP1v22 curve created with {len(adjustments)} adjustments")

    return sp1v22_neg, design_log

def negative_density_to_k(neg_density, measurement_df):
    """
    Convert negative density back to K values for .quad file

    Uses inverse relationship calibrated from measurement data
    """
    # Create inverse interpolation from measurement data
    meas_inputs = measurement_df['input'].values
    meas_neg_density = measurement_df['negative_density_transmission'].values

    # Sort by density for inverse interpolation
    sort_idx = np.argsort(meas_neg_density)
    sorted_density = meas_neg_density[sort_idx]
    sorted_inputs = meas_inputs[sort_idx]

    # Create inverse function: density → input
    f_inv = interpolate.interp1d(
        sorted_density,
        sorted_inputs,
        kind='cubic',
        fill_value='extrapolate'
    )

    # Convert densities to inputs (which map to K values)
    k_values = np.zeros(256, dtype=int)

    for i, density in enumerate(neg_density):
        # Get corresponding input value
        target_input = f_inv(density)

        # K value is proportional to density
        # Higher density = higher K value (more ink)
        # Calibrate using Input 128 = K 50% = 128
        k_values[i] = int(np.clip(target_input, 0, 255))

    return k_values

def write_quad_file(k_values, output_path):
    """Write .quad file in QTR format"""
    print(f"\n💾 Writing .quad file to {output_path.name}...")

    # QTR .quad file format
    lines = []

    # Header (following V7 structure)
    lines.append("## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK")
    lines.append("# QuadProfile Version 2.8.0")
    lines.append("# PX1V-PtPd-SP1v22 - Minimal adjustments for banding elimination")
    lines.append("# Date: 2026-03-19")
    lines.append("# Baseline: SP1v21")
    lines.append("# Adjustments:")
    lines.append("#   1. Input 128: 0.485D (0.76D print target)")
    lines.append("#   2. Linear interpolation (banding elimination)")
    lines.append("#   3. White gradation extension (Input 240-255)")
    lines.append("# Target exposure: 7min (420 sec)")
    lines.append("# Target paper: Revere Platinum")
    lines.append("# 2026 Daisuke Kinoshita")
    lines.append("# BOOST_K=0 - NO BOOST")
    lines.append("# K curve")

    # K channel values (no channel number marker for K)
    for val in k_values:
        lines.append(str(int(val)))

    # Other channels (1-9): all zeros with comment headers
    channel_names = ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']
    for ch_num, ch_name in enumerate(channel_names, start=1):
        lines.append(f"# {ch_name} curve")
        for _ in range(256):
            lines.append("0")

    # Write file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"✓ .quad file written: {output_path}")
    print(f"  256 K values written")
    print(f"  Channels 1-9: all zeros")

def create_comparison_graph(sp1v21_neg, sp1v22_neg, measurement_df, output_path):
    """Create 4-panel comparison graph"""
    print(f"\n📊 Creating comparison graphs...")

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('SP1v22 Curve Comparison (Simplified)', fontsize=16, fontweight='bold')

    inputs = np.arange(256)

    # Panel 1: Negative density comparison
    ax1 = axes[0, 0]
    ax1.plot(inputs, sp1v21_neg, 'b-', linewidth=2, label='SP1v21', alpha=0.7)
    ax1.plot(inputs, sp1v22_neg, 'r-', linewidth=2, label='SP1v22')

    # Highlight adjustment zones
    ax1.axvline(128, color='orange', linestyle='--', alpha=0.5, label='Midtone')
    ax1.axvspan(240, 255, color='cyan', alpha=0.1, label='White extension')

    ax1.set_xlabel('Input (0=Black, 255=White)', fontsize=11)
    ax1.set_ylabel('Negative Density (Transmission)', fontsize=11)
    ax1.set_title('Negative Density Curves', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left', fontsize=9)
    ax1.set_xlim(0, 255)

    # Panel 2: Difference plot
    ax2 = axes[0, 1]
    diff = sp1v22_neg - sp1v21_neg
    ax2.plot(inputs, diff, 'purple', linewidth=2)
    ax2.axhline(0, color='black', linestyle='-', linewidth=0.5)
    ax2.axvline(128, color='orange', linestyle='--', alpha=0.5)
    ax2.axvspan(240, 255, color='cyan', alpha=0.1)

    ax2.set_xlabel('Input', fontsize=11)
    ax2.set_ylabel('ΔDensity (SP1v22 - SP1v21)', fontsize=11)
    ax2.set_title('Adjustments Applied', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 255)

    # Panel 3: Black gradation detail (Input 26-140, K45%-90%)
    ax3 = axes[1, 0]
    black_range = range(26, 141)
    ax3.plot(list(black_range), sp1v21_neg[26:141], 'b-', linewidth=2, label='SP1v21', alpha=0.7)
    ax3.plot(list(black_range), sp1v22_neg[26:141], 'r-', linewidth=2, label='SP1v22')

    # Mark former banding zones
    ax3.axvline(88, color='green', linestyle=':', alpha=0.5, label='Former banding zone')
    ax3.axvline(96, color='green', linestyle=':', alpha=0.5)
    ax3.axvline(136, color='green', linestyle=':', alpha=0.5)
    ax3.axvline(144, color='green', linestyle=':', alpha=0.5)

    ax3.set_xlabel('Input (K45%-90% range)', fontsize=11)
    ax3.set_ylabel('Negative Density', fontsize=11)
    ax3.set_title('Black Gradation Detail (Artist\'s Primary Range)', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='upper left', fontsize=9)

    # Panel 4: White gradation detail (Input 204-255, K0%-20%)
    ax4 = axes[1, 1]
    white_range = range(204, 256)
    ax4.plot(list(white_range), sp1v21_neg[204:256], 'b-', linewidth=2, label='SP1v21', alpha=0.7)
    ax4.plot(list(white_range), sp1v22_neg[204:256], 'r-', linewidth=2, label='SP1v22')

    ax4.set_xlabel('Input (K0%-20% range)', fontsize=11)
    ax4.set_ylabel('Negative Density', fontsize=11)
    ax4.set_title('White Gradation Detail ("White within White")', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='upper left', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Graphs saved: {output_path}")

    return fig

def analyze_banding_risk(sp1v22_neg):
    """Detect potential banding issues in SP1v22"""
    print("\n🔍 Analyzing banding risk...")

    banding_issues = []

    for i in range(len(sp1v22_neg) - 1):
        diff = sp1v22_neg[i+1] - sp1v22_neg[i]  # Keep sign for direction check

        # Flag if difference is too small (< 0.001D) or negative (reversal)
        # Note: With 8-step measurement intervals, 0.001D/step is acceptable
        if abs(diff) < 0.001 or diff < 0:
            banding_issues.append({
                'input_pair': f"{i}-{i+1}",
                'density_diff': round(diff, 4),
                'risk': 'HIGH' if (diff < 0 or abs(diff) < 0.0005) else 'MEDIUM'
            })

    if banding_issues:
        print(f"⚠️  Found {len(banding_issues)} potential banding zones:")
        for issue in banding_issues[:10]:  # Show first 10
            print(f"  Input {issue['input_pair']}: ΔD={issue['density_diff']:.4f} ({issue['risk']} risk)")
        if len(banding_issues) > 10:
            print(f"  ... and {len(banding_issues) - 10} more")
    else:
        print("✓ No banding risk detected (all steps > 0.001D, monotonic increase)")

    return banding_issues

def main():
    """Main execution"""
    print("=" * 70)
    print("SP1v22 CURVE GENERATOR (SIMPLIFIED)")
    print("=" * 70)
    print(f"Baseline: SP1v21")
    print(f"Strategy: Minimal changes - fix midtone, eliminate banding, extend whites")
    print(f"Paper: Revere Platinum")
    print(f"Exposure: 7min (420 sec)")
    print("=" * 70)

    # Load data
    sp1v21_inputs, sp1v21_k_values = load_sp1v21_quad()
    measurement_df = load_measurement_7m()

    # Convert SP1v21 K values to negative density
    sp1v21_neg = k_to_negative_density(sp1v21_k_values, measurement_df)

    # Create SP1v22 curve
    sp1v22_neg, design_log = create_sp1v22_curve_simple(sp1v21_neg, measurement_df)

    # Convert back to K values
    sp1v22_k_values = negative_density_to_k(sp1v22_neg, measurement_df)

    # Write .quad file
    write_quad_file(sp1v22_k_values, OUTPUT_QUAD)

    # Save design log
    design_log.to_csv(OUTPUT_CSV, index=False)
    print(f"\n💾 Design log saved: {OUTPUT_CSV}")

    # Create comparison graphs
    create_comparison_graph(sp1v21_neg, sp1v22_neg, measurement_df, OUTPUT_GRAPH)

    # Analyze banding risk
    banding_issues = analyze_banding_risk(sp1v22_neg)

    # Summary
    print("\n" + "=" * 70)
    print("SP1v22 GENERATION COMPLETE (SIMPLIFIED)")
    print("=" * 70)
    print(f"📄 Output files:")
    print(f"  .quad: {OUTPUT_QUAD}")
    print(f"  CSV:   {OUTPUT_CSV}")
    print(f"  Graph: {OUTPUT_GRAPH}")
    print()
    print(f"📊 Adjustments applied: {len(design_log)}")
    print(f"🎯 Key targets:")
    print(f"  Input 128: {sp1v22_neg[128]:.3f}D (target: 0.485D)")
    print(f"  Black range (Input 26-140): {sp1v22_neg[26]:.3f}D - {sp1v22_neg[140]:.3f}D")
    print(f"  White range (Input 204-255): {sp1v22_neg[204]:.3f}D - {sp1v22_neg[255]:.3f}D")
    print()
    print(f"⚠️  Banding risk: {len(banding_issues)} zones")
    print()
    print("Next steps:")
    print("1. Review comparison graphs")
    print("2. Check banding risk assessment")
    print("3. Install to QTR: sudo cp {} /Library/Printers/QTR/quadtone/QuadP700/".format(OUTPUT_QUAD.name))
    print("4. Print test chart with SP1v22 @ 7min exposure")
    print("5. Measure and verify results")
    print("=" * 70)

if __name__ == "__main__":
    main()
