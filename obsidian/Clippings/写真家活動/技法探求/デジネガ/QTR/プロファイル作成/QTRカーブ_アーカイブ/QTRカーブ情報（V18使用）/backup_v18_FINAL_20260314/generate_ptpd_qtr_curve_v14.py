#!/usr/bin/env python3
"""
PX1V-PtPd-Linear v14 Curve Generator
Based on v12 with smoothed Input 48-104 using spline interpolation
Target: Remove both boundaries in 0.27-0.47 range
"""

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d, CubicSpline

# Read v12 actual measurements
v12_data = pd.read_csv("/Users/daisukekinoshita/Desktop/measurement_QTR2-12.csv")
v12_data = v12_data[['input', 'negative_density']].dropna()

print("=== v14 Generation: Smoothing Input 48-104 ===")
print()
print("v12 Measurements (problematic range):")
print(v12_data[(v12_data['input'] >= 40) & (v12_data['input'] <= 112)])
print()

# Create smooth curve for Input 48-104
# Use cubic spline on control points: 40, 48, 104, 112
control_points_input = np.array([40, 48, 104, 112])
control_points_density = v12_data[v12_data['input'].isin(control_points_input)]['negative_density'].values

print("Control points for spline:")
for inp, dens in zip(control_points_input, control_points_density):
    print(f"  Input {inp} -> Density {dens}")
print()

# Create cubic spline
spline = CubicSpline(control_points_input, control_points_density)

# Generate smoothed values for Input 48-104
smooth_inputs = np.array([48, 56, 64, 72, 80, 88, 96, 104])
smooth_densities = spline(smooth_inputs)

print("Smoothed values (spline interpolation):")
print("Input | Original | Smoothed | Diff")
print("------|----------|----------|-------")
for inp, dens in zip(smooth_inputs, smooth_densities):
    original = v12_data[v12_data['input'] == inp]['negative_density'].values[0] if inp in v12_data['input'].values else None
    diff = dens - original if original is not None else 0
    orig_str = f"{original}" if original is not None else "N/A"
    print(f"{inp:5.0f} | {orig_str:8s} | {dens:.4f}  | {diff:+.4f}")
print()

# Create v14 target curve (replace 48-104 with smoothed values)
v14_target = v12_data.copy()
for inp, dens in zip(smooth_inputs, smooth_densities):
    v14_target.loc[v14_target['input'] == inp, 'negative_density'] = dens

# Verify smoothness
print("=== Gradient Analysis (v12 vs v14) ===")
print()
focus = v14_target[(v14_target['input'] >= 40) & (v14_target['input'] <= 112)].copy()
focus['gradient_v14'] = focus['negative_density'].diff() / focus['input'].diff()

v12_focus = v12_data[(v12_data['input'] >= 40) & (v12_data['input'] <= 112)].copy()
v12_focus['gradient_v12'] = v12_focus['negative_density'].diff() / v12_focus['input'].diff()

print("Input | v12 Grad | v14 Grad | Improvement")
print("------|----------|----------|------------")
for idx in focus.index:
    inp = focus.loc[idx, 'input']
    v14_grad = focus.loc[idx, 'gradient_v14']

    v12_grad = v12_focus[v12_focus['input'] == inp]['gradient_v12'].values[0] if inp in v12_focus[v12_focus['gradient_v12'].notna()]['input'].values else np.nan

    if not np.isnan(v12_grad) and not np.isnan(v14_grad):
        improvement = abs(v12_grad - v14_grad)
        print(f"{inp:5.0f} | {v12_grad:8.4f} | {v14_grad:8.4f} | {improvement:8.4f}")
    else:
        print(f"{inp:5.0f} |      nan |      nan |      nan")

print()
print("Max gradient reduction:")
max_v12_grad = v12_focus['gradient_v12'].max()
max_v14_grad = focus['gradient_v14'].max()
print(f"  v12: {max_v12_grad:.4f}")
print(f"  v14: {max_v14_grad:.4f}")
print(f"  Reduction: {(max_v12_grad - max_v14_grad):.4f} ({(1-max_v14_grad/max_v12_grad)*100:.1f}%)")

# Use v11 baseline->density relationship (same as v12/v13)
v11_data = {
    'input': [160, 255],
    'baseline': [155.2, 210.7],
    'density': [1.24, 1.65]
}

slope = (v11_data['density'][1] - v11_data['density'][0]) / (v11_data['baseline'][1] - v11_data['baseline'][0])
intercept = v11_data['density'][0] - slope * v11_data['baseline'][0]

print()
print("=== Baseline Calculation (same as v12/v13) ===")
print(f"Density = {slope:.6f} * Baseline + {intercept:.4f}")

# Generate v14 curve
remapped_curve_8bit = []
remapped_curve_16bit = []

# Create interpolation function from v14 target
v14_interp = interp1d(
    v14_target['input'].values,
    v14_target['negative_density'].values,
    kind='cubic',
    fill_value='extrapolate'
)

for target_input in range(256):
    # Get target density from v14
    target_density = float(v14_interp(target_input))

    # Calculate required baseline input
    baseline_input = (target_density - intercept) / slope
    baseline_input = np.clip(baseline_input, 0, 255)

    remapped_curve_8bit.append(baseline_input)
    remapped_curve_16bit.append(int(round(baseline_input * 257)))

print()
print("=== v14 Curve Values (critical points) ===")
print(f"Input 0   -> Baseline: {remapped_curve_8bit[0]:.1f}")
print(f"Input 48  -> Baseline: {remapped_curve_8bit[48]:.1f}")
print(f"Input 56  -> Baseline: {remapped_curve_8bit[56]:.1f}")
print(f"Input 64  -> Baseline: {remapped_curve_8bit[64]:.1f}")
print(f"Input 72  -> Baseline: {remapped_curve_8bit[72]:.1f}")
print(f"Input 80  -> Baseline: {remapped_curve_8bit[80]:.1f}")
print(f"Input 88  -> Baseline: {remapped_curve_8bit[88]:.1f}")
print(f"Input 96  -> Baseline: {remapped_curve_8bit[96]:.1f}")
print(f"Input 104 -> Baseline: {remapped_curve_8bit[104]:.1f}")
print(f"Input 255 -> Baseline: {remapped_curve_8bit[255]:.1f}")

# Generate .quad file
quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# PX1V-PtPd-Linear v14 - Fully smoothed Input 48-104 (spline interpolation)
# Target: Remove all boundaries in 0.27-0.47 range
# BOOST_K=0 - NO BOOST
# K curve
"""

for val in remapped_curve_16bit:
    quad_content += f"{val}\n"

# Add other ink curves (all zeros)
for ink_name in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
    quad_content += f"# {ink_name} curve\n"
    for _ in range(256):
        quad_content += "0\n"

quad_file = "/Users/daisukekinoshita/Desktop/PX1V-PtPd-Linear-v14.quad"
with open(quad_file, 'w') as f:
    f.write(quad_content)

print(f"\n✓ Created: {quad_file}")

# Generate .txt file
txt_content = """#  QuadToneRIP curve descriptor file
#
#  PX1V-PtPd-Linear-v14
#  Platinum/Palladium Print Optimized Curve
#  Based on v12 with smoothed Input 48-104 (spline interpolation)
#  Target: Remove all boundaries in 0.27-0.47 range
#  BOOST_K=0 (NO ink boost)
#  Ink Limits: 100% (fixed)
#  Created: 2026-03-14

N_OF_INKS=8
DEFAULT_INK_LIMIT=100

LIMIT_K=100
BOOST_K=0
LIMIT_C=0
LIMIT_M=0
LIMIT_Y=0
LIMIT_LC=0
LIMIT_LM=0
LIMIT_LK=100
LIMIT_LLK=100

#
#  Describe usage of each ink
#  All inks must be listed
#

# Gray Partitioning Information

N_OF_GRAY_PARTS=3
GRAY_INK_1=K
GRAY_VAL_1=100

GRAY_INK_2=LK
GRAY_VAL_2=55

GRAY_INK_3=LLK
GRAY_VAL_3=16

GRAY_HIGHLIGHT=1
GRAY_SHADOW=1

GRAY_GAMMA=1
GRAY_CURVE=

# Toner Partition Information

TONER_INK_1=M
TONER_VAL_1=100
TONER_INK_2=LM
TONER_VAL_2=40

TONER_HIGHLIGHT=1
TONER_SHADOW=1
TONER_GAMMA=1
TONER_CURVE=

TONER_2_INK_1=C
TONER_2_VAL_1=100
TONER_2_INK_2=LC
TONER_2_VAL_2=40

TONER_2_HIGHLIGHT=1
TONER_2_SHADOW=1
TONER_2_GAMMA=1

# Smoothed Input 48-104 using cubic spline interpolation
# Target density 1.22 at Input 255 maintained
# Always use Ink Limits 100% in Print-Tool
# No color inks, gray only
#LINEARIZE=""
"""

txt_file = "/Users/daisukekinoshita/Desktop/PX1V-PtPd-Linear-v14.txt"
with open(txt_file, 'w') as f:
    f.write(txt_content)

print(f"✓ Created: {txt_file}")

# Save v14 target curve for comparison
v14_target.to_csv("/Users/daisukekinoshita/Desktop/measurement_QTR2-14_target.csv", index=False)
print(f"✓ Created: /Users/daisukekinoshita/Desktop/measurement_QTR2-14_target.csv")

print("\n=== Installation Instructions ===")
print("1. Backup current v13 (optional)")
print("2. Install v14 by overwriting v9")
print("3. Print same test image")
print("4. Check if both boundaries are eliminated")
