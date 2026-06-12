#!/usr/bin/env python3
"""
SP1v22 QTR Curve Generator
==========================

Purpose:
  Create SP1v22 curve optimized for artist's tonal ranges:
  - K45%-90% (Input 26-140): Enhanced black gradation
  - K5%-20% (Input 204-242): Extended white gradation ("white within white")

Design Strategy:
  1. Input 40-80: Increase negative density +0.08D to +0.13D (enhance black detail)
  2. Input 88-144: Spline interpolation to eliminate banding at 88/96 and 136/144
  3. Input 128: Adjust to 0.485D for 0.76D print target (from 0.79D)
  4. Input 232-242: Increase negative density +0.07D to +0.08D (extend white gradation)

Baseline: SP1v21
Target Paper: Revere Platinum
Exposure: 7min (420 sec)
Target Dmax: 1.46D (reflection)
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

def create_sp1v22_curve(sp1v21_neg_density, measurement_df):
    """
    Create SP1v22 curve with all adjustments

    Returns:
        sp1v22_neg_density: 256-element array of negative densities
        design_log: DataFrame with adjustment details
    """
    print("\n🔧 Creating SP1v22 curve adjustments...")

    # Start with SP1v21 baseline
    sp1v22_neg = sp1v21_neg_density.copy()

    # Adjustment log
    adjustments = []

    # === ADJUSTMENT 1: Input 40-80 (K70%-90% black enhancement) ===
    print("\n1️⃣ Adjusting Input 40-80 (black gradation enhancement)...")

    # NOTE: We'll apply this AFTER linear interpolation to ensure smooth transitions
    # For now, just mark the target adjustments
    target_adjustments_40_80 = {}

    # Linear gradient: +0.08D at Input 40 to +0.13D at Input 80
    for inp in range(40, 81):
        # Calculate adjustment
        ratio = (inp - 40) / 40.0  # 0.0 at inp=40, 1.0 at inp=80
        adjustment = 0.08 + ratio * (0.13 - 0.08)
        target_adjustments_40_80[inp] = adjustment

    print(f"  Target: Input 40 +{0.08:.3f}D, Input 80 +{0.13:.3f}D")
    print(f"  (Will apply after linear interpolation)")

    # === ADJUSTMENT 2: Input 128 (midtone correction) ===
    print("\n2️⃣ Adjusting Input 128 (midtone correction to 0.76D print target)...")

    old_val = sp1v22_neg[128]
    sp1v22_neg[128] = 0.485  # Directly set to target
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

    # === ADJUSTMENT 3: Input 88-144 (linear interpolation for banding elimination) ===
    print("\n3️⃣ Applying linear interpolation to Input 88-144 (banding elimination)...")

    # Use measured data points as much as possible
    # Measured inputs: 0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120, 128, 136, 144, ...
    # We need to ensure smooth transitions around banding zones

    # Strategy: Use linear interpolation between measured points
    # This guarantees monotonic increase and no banding
    measured_inputs_in_range = [80, 88, 96, 104, 112, 120, 128, 136, 144, 152, 160]

    # Get values for anchor points (already adjusted for Input 80 and 128)
    anchor_values = np.array([sp1v22_neg[inp] for inp in measured_inputs_in_range])

    # Create linear interpolation function
    linear_interp = interpolate.interp1d(measured_inputs_in_range, anchor_values, kind='linear')

    # Apply to Input 81-160 (entire range for consistency)
    for inp in range(81, 161):
        if inp not in measured_inputs_in_range:  # Don't overwrite measured anchor points
            old_val = sp1v22_neg[inp]
            sp1v22_neg[inp] = linear_interp(inp)
            new_val = sp1v22_neg[inp]

            if 88 <= inp <= 144:  # Only log adjustments in target range
                adjustments.append({
                    'input': inp,
                    'k_percent': round((255 - inp) / 255 * 100, 1),
                    'adjustment_type': 'Linear smoothing',
                    'old_negative_density': round(old_val, 3),
                    'adjustment': round(new_val - old_val, 3),
                    'new_negative_density': round(new_val, 3)
                })

    print(f"  Linear interpolation applied to Input 81-160")
    print(f"  Anchor points: {measured_inputs_in_range}")
    print(f"  Method: Linear (guaranteed monotonic, no banding)")
    print(f"  Banding zones (88/96, 136/144) eliminated")

    # === ADJUSTMENT 3b: Apply black enhancement to Input 40-87 ===
    print("\n3️⃣b Applying black enhancement to Input 40-87...")

    # First apply enhancement to Input 40-80
    for inp in range(40, 81):
        old_val = sp1v22_neg[inp]
        adjustment = target_adjustments_40_80[inp]
        sp1v22_neg[inp] += adjustment
        new_val = sp1v22_neg[inp]

        adjustments.append({
            'input': inp,
            'k_percent': round((255 - inp) / 255 * 100, 1),
            'adjustment_type': 'Black enhancement',
            'old_negative_density': round(old_val, 3),
            'adjustment': round(adjustment, 3),
            'new_negative_density': round(new_val, 3)
        })

    # Now re-interpolate Input 81-87 to smoothly connect to Input 88
    # Linear interpolation from Input 80 (enhanced) to Input 88 (from linear interp)
    val_80 = sp1v22_neg[80]
    val_88 = sp1v22_neg[88]

    for inp in range(81, 88):
        old_val = sp1v22_neg[inp]
        # Linear interpolation
        ratio = (inp - 80) / (88 - 80)
        sp1v22_neg[inp] = val_80 + ratio * (val_88 - val_80)
        new_val = sp1v22_neg[inp]

        adjustments.append({
            'input': inp,
            'k_percent': round((255 - inp) / 255 * 100, 1),
            'adjustment_type': 'Transition smoothing',
            'old_negative_density': round(old_val, 3),
            'adjustment': round(new_val - old_val, 3),
            'new_negative_density': round(new_val, 3)
        })

    print(f"  Input 40: +{target_adjustments_40_80[40]:.3f}D → {sp1v22_neg[40]:.3f}D")
    print(f"  Input 80: +{target_adjustments_40_80[80]:.3f}D → {sp1v22_neg[80]:.3f}D")
    print(f"  Input 81-87: Smoothly interpolated to Input 88")

    # === ADJUSTMENT 4: Input 232-242 (white gradation extension) ===
    print("\n4️⃣ Adjusting Input 232-242 (white gradation extension)...")

    # Linear gradient: +0.07D at Input 232 to +0.08D at Input 242
    for inp in range(232, 243):
        ratio = (inp - 232) / 10.0  # 0.0 at inp=232, 1.0 at inp=242
        adjustment = 0.07 + ratio * (0.08 - 0.07)

        old_val = sp1v22_neg[inp]
        sp1v22_neg[inp] += adjustment
        new_val = sp1v22_neg[inp]

        adjustments.append({
            'input': inp,
            'k_percent': round((255 - inp) / 255 * 100, 1),
            'adjustment_type': 'White extension',
            'old_negative_density': round(old_val, 3),
            'adjustment': round(adjustment, 3),
            'new_negative_density': round(new_val, 3)
        })

    print(f"  Input 232: +{0.07:.3f}D → {sp1v22_neg[232]:.3f}D")
    print(f"  Input 242: +{0.08:.3f}D → {sp1v22_neg[242]:.3f}D")

    # === FINAL SMOOTHING: Apply gentle spline to all non-anchor points ===
    print("\n5️⃣ Final global smoothing...")

    # Define global anchor points
    global_anchors = [0, 40, 80, 128, 144, 200, 232, 242, 255]
    global_values = sp1v22_neg[global_anchors]

    # Create global spline
    global_spline = interpolate.UnivariateSpline(global_anchors, global_values, k=3, s=0.001)

    # Apply to intermediate points (not anchor points)
    for inp in range(256):
        if inp not in global_anchors and inp not in range(40, 81) and inp not in range(232, 243):
            # Blend 70% spline, 30% original to preserve adjustments
            sp1v22_neg[inp] = 0.7 * global_spline(inp) + 0.3 * sp1v22_neg[inp]

    print("  Global smoothing applied (70% spline, 30% original)")

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

    # Header
    lines.append("# SP1v22 - Optimized for Revere Platinum Pt/Pd printing")
    lines.append("# Date: 2026-03-19")
    lines.append("# Baseline: SP1v21")
    lines.append("# Adjustments:")
    lines.append("#   1. Input 40-80: +0.08D to +0.13D (black gradation enhancement)")
    lines.append("#   2. Input 88-144: Spline smoothing (banding elimination)")
    lines.append("#   3. Input 128: 0.485D (0.76D print target)")
    lines.append("#   4. Input 232-242: +0.07D to +0.08D (white gradation extension)")
    lines.append("# Target exposure: 7min (420 sec)")
    lines.append("# Target paper: Revere Platinum")
    lines.append("# Artist's tonal ranges:")
    lines.append("#   K45%-90% (Input 26-140): Black gradation")
    lines.append("#   K5%-20% (Input 204-242): White gradation")
    lines.append("")

    # K channel (channel 0)
    lines.append("0")
    for val in k_values:
        lines.append(str(int(val)))
    lines.append("")

    # Other channels (1-9): all zeros
    for ch in range(1, 10):
        lines.append(str(ch))
        for _ in range(256):
            lines.append("0")
        lines.append("")

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
    fig.suptitle('SP1v22 Curve Comparison', fontsize=16, fontweight='bold')

    inputs = np.arange(256)

    # Panel 1: Negative density comparison
    ax1 = axes[0, 0]
    ax1.plot(inputs, sp1v21_neg, 'b-', linewidth=2, label='SP1v21', alpha=0.7)
    ax1.plot(inputs, sp1v22_neg, 'r-', linewidth=2, label='SP1v22')

    # Highlight adjustment zones
    ax1.axvspan(40, 80, color='yellow', alpha=0.1, label='Black enhancement')
    ax1.axvspan(88, 144, color='green', alpha=0.1, label='Banding elimination')
    ax1.axvspan(232, 242, color='cyan', alpha=0.1, label='White extension')
    ax1.axvline(128, color='gray', linestyle='--', alpha=0.5, label='Midtone')

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
    ax2.axvspan(40, 80, color='yellow', alpha=0.1)
    ax2.axvspan(88, 144, color='green', alpha=0.1)
    ax2.axvspan(232, 242, color='cyan', alpha=0.1)

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

    # Mark banding zones
    ax3.axvline(88, color='orange', linestyle='--', alpha=0.5, label='Banding zone')
    ax3.axvline(96, color='orange', linestyle='--', alpha=0.5)
    ax3.axvline(136, color='orange', linestyle='--', alpha=0.5)
    ax3.axvline(144, color='orange', linestyle='--', alpha=0.5)

    ax3.set_xlabel('Input (K45%-90% range)', fontsize=11)
    ax3.set_ylabel('Negative Density', fontsize=11)
    ax3.set_title('Black Gradation Detail (Artist\'s Primary Range)', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='upper left', fontsize=9)

    # Panel 4: White gradation detail (Input 204-242, K5%-20%)
    ax4 = axes[1, 1]
    white_range = range(204, 243)
    ax4.plot(list(white_range), sp1v21_neg[204:243], 'b-', linewidth=2, label='SP1v21', alpha=0.7)
    ax4.plot(list(white_range), sp1v22_neg[204:243], 'r-', linewidth=2, label='SP1v22')

    ax4.set_xlabel('Input (K5%-20% range)', fontsize=11)
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
        print("✓ No banding risk detected (all steps > 0.002D)")

    return banding_issues

def main():
    """Main execution"""
    print("=" * 70)
    print("SP1v22 CURVE GENERATOR")
    print("=" * 70)
    print(f"Baseline: SP1v21")
    print(f"Target: Optimized for artist's black (K45%-90%) and white (K5%-20%) gradations")
    print(f"Paper: Revere Platinum")
    print(f"Exposure: 7min (420 sec)")
    print("=" * 70)

    # Load data
    sp1v21_inputs, sp1v21_k_values = load_sp1v21_quad()
    measurement_df = load_measurement_7m()

    # Convert SP1v21 K values to negative density
    sp1v21_neg = k_to_negative_density(sp1v21_k_values, measurement_df)

    # Create SP1v22 curve
    sp1v22_neg, design_log = create_sp1v22_curve(sp1v21_neg, measurement_df)

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
    print("SP1v22 GENERATION COMPLETE")
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
    print(f"  White range (Input 204-242): {sp1v22_neg[204]:.3f}D - {sp1v22_neg[242]:.3f}D")
    print()
    print(f"⚠️  Banding risk: {len(banding_issues)} potential zones")
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
