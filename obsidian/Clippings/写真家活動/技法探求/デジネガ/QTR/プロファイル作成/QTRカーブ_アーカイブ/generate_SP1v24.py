#!/usr/bin/env python3
"""
SP1v24 QTRカーブ生成スクリプト

目的:
- Input 128: 0.80Dを維持（階調優先）
- 白階調の大幅拡張（Input 136-232）
- なだらかな階調表現

設計方針:
- SP1v23のプリント濃度実測値をベースラインとして使用
- ユーザー指定の目標プリント濃度に向けて調整
- プリント濃度 → ネガ濃度の逆算にSP1v23の変換特性を利用
- ネガ濃度 → K値の変換にSP1v21のマッピングを使用
"""

import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import subprocess

# QTR constants
QTR_MAX_VALUE = 65535  # 16-bit maximum

print("=" * 100)
print("SP1v24 QTRカーブ生成")
print("=" * 100)
print()

# ============================================================================
# Step 1: Load SP1v23 measurement data
# ============================================================================
print("1️⃣ SP1v23測定データ読み込み...")

import pandas as pd

sp1v23_file = "/Users/daisukekinoshita/Desktop/measurement_QTR-SP-23.csv"
sp1v23_data = pd.read_csv(sp1v23_file)

print(f"  ✓ SP1v23測定データ: {len(sp1v23_data)}ポイント")
print()

# ============================================================================
# Step 2: Load SP1v24 target print density
# ============================================================================
print("2️⃣ SP1v24目標プリント濃度読み込み...")

sp1v24_target_file = "/tmp/sp1v24_target_print_density.csv"
sp1v24_target = pd.read_csv(sp1v24_target_file)

print(f"  ✓ SP1v24目標値: {len(sp1v24_target)}ポイント")
print()

# Merge
data = pd.merge(sp1v23_data, sp1v24_target, on='input')

# ============================================================================
# Step 3: Calculate target negative density from target print density
# ============================================================================
print("3️⃣ プリント濃度 → ネガ濃度の逆算...")
print()

# Build print → negative conversion function from SP1v23 data
# Use SP1v23's measured relationship: print_density = f(negative_density)
# We need inverse: negative_density = f_inv(print_density)

# Sort by print density for interpolation
sp1v23_sorted = sp1v23_data.sort_values('v23_print_density')

# Remove duplicate print density values (keep first occurrence)
sp1v23_unique = sp1v23_sorted.drop_duplicates(subset='v23_print_density', keep='first')

print(f"  SP1v23データポイント: {len(sp1v23_data)} → 重複削除後: {len(sp1v23_unique)}")
print()

# Create print → negative mapping
print_to_neg = interpolate.interp1d(
    sp1v23_unique['v23_print_density'],
    sp1v23_unique['v23_negative_density'],
    kind='linear',
    fill_value='extrapolate'
)

# Calculate target negative density for each input
sp1v24_neg_density = []

for _, row in data.iterrows():
    target_print = row['target_print_density']

    # Use SP1v23's print→neg conversion
    target_neg = float(print_to_neg(target_print))

    # Clip to reasonable range
    target_neg = np.clip(target_neg, 0.05, 1.50)

    sp1v24_neg_density.append(target_neg)

sp1v24_neg_density = np.array(sp1v24_neg_density)

print("目標ネガ濃度の計算結果:")
print()
print("Input   v23ネガ   v24目標ネガ   差分       v23プリント  v24目標プリント")
print("-" * 100)

for i, inp in enumerate(data['input']):
    v23_neg = data.iloc[i]['v23_negative_density']
    v24_neg = sp1v24_neg_density[i]
    neg_diff = v24_neg - v23_neg
    v23_print = data.iloc[i]['v23_print_density']
    v24_print = data.iloc[i]['target_print_density']

    print(f"{int(inp):3d}     {v23_neg:.3f}D    {v24_neg:.3f}D      {neg_diff:+.3f}D    {v23_print:.2f}D        {v24_print:.2f}D")

print()

# ============================================================================
# Step 4: Interpolate to 256 input values
# ============================================================================
print("4️⃣ 256段階へ補間...")

# We have 33 measured points, need 256 for full curve
measured_inputs = data['input'].values
measured_neg_density = sp1v24_neg_density

# Create interpolation function
interp_func = interpolate.interp1d(
    measured_inputs,
    measured_neg_density,
    kind='cubic',
    fill_value='extrapolate'
)

# Generate full 256-point curve
inputs_256 = np.arange(256)
sp1v24_neg_full = interp_func(inputs_256)

# Ensure monotonic increase
for i in range(1, 256):
    if sp1v24_neg_full[i] < sp1v24_neg_full[i-1]:
        sp1v24_neg_full[i] = sp1v24_neg_full[i-1] + 0.001

# Apply linear re-interpolation to prevent banding around Input 104-112
# Re-interpolate between Input 96 and 120 using linear interpolation
anchor_start = 96
anchor_end = 120
anchor_val_start = sp1v24_neg_full[anchor_start]
anchor_val_end = sp1v24_neg_full[anchor_end]

# Linear interpolation between anchors
for i in range(anchor_start + 1, anchor_end):
    ratio = (i - anchor_start) / (anchor_end - anchor_start)
    sp1v24_neg_full[i] = anchor_val_start + ratio * (anchor_val_end - anchor_val_start)

print(f"  平滑化適用: Input {anchor_start}-{anchor_end} (線形補間)")
print()

# Re-ensure monotonic increase after smoothing
for i in range(1, 256):
    if sp1v24_neg_full[i] < sp1v24_neg_full[i-1]:
        sp1v24_neg_full[i] = sp1v24_neg_full[i-1] + 0.001

# Clip to reasonable range
sp1v24_neg_full = np.clip(sp1v24_neg_full, 0.05, 1.50)

print(f"  ✓ 256ポイントに補間完了")
print(f"  ネガ濃度範囲: {sp1v24_neg_full.min():.3f}D ～ {sp1v24_neg_full.max():.3f}D")
print()

# ============================================================================
# Step 5: Convert negative density to K values using SP1v21 mapping
# ============================================================================
print("5️⃣ ネガ濃度 → K値変換（SP1v21マッピング使用）...")

# Load SP1v21 K values and negative density
sp1v21_file = "/Users/daisukekinoshita/Desktop/measurement_QTR-SP-21.csv"
sp1v21_data = pd.read_csv(sp1v21_file)
sp1v21_data.columns = ['input', 'v21_neg_density', 'v21_print_density']

# Extract SP1v21 K values from quad file (line 16-271 = 256 K values)
result = subprocess.run(
    ["sed", "-n", "16,271p", "/Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-SP1v21.quad"],
    capture_output=True,
    text=True
)
sp1v21_k_values = np.array([int(line.strip()) for line in result.stdout.strip().split('\n')])

# Map SP1v21 K values to measured inputs
sp1v21_k_measured = []
for inp in sp1v21_data['input']:
    sp1v21_k_measured.append(sp1v21_k_values[int(inp)])

sp1v21_k_measured = np.array(sp1v21_k_measured)
sp1v21_neg_measured = sp1v21_data['v21_neg_density'].values

# Build negative_density → K value mapping from SP1v21
sort_idx = np.argsort(sp1v21_neg_measured)
sorted_neg = sp1v21_neg_measured[sort_idx]
sorted_k = sp1v21_k_measured[sort_idx]

neg_to_k = interpolate.interp1d(
    sorted_neg,
    sorted_k,
    kind='cubic',
    fill_value='extrapolate'
)

# Convert SP1v24 negative density to K values
sp1v24_k_values = neg_to_k(sp1v24_neg_full)
sp1v24_k_values = np.clip(sp1v24_k_values, 0, QTR_MAX_VALUE).astype(int)

print(f"  ✓ K値変換完了")
print(f"  K値範囲: {sp1v24_k_values.min()} ～ {sp1v24_k_values.max()}")
print()

# Verify key points
print("主要ポイントのK値:")
for inp in [0, 32, 88, 96, 128, 136, 144, 232, 240, 255]:
    print(f"  Input {inp:3d}: K={sp1v24_k_values[inp]:5d}, Neg={sp1v24_neg_full[inp]:.3f}D")
print()

# ============================================================================
# Step 6: Analyze banding risk
# ============================================================================
print("6️⃣ バンディングリスク解析...")

banding_issues = []
for i in range(255):
    diff = sp1v24_neg_full[i+1] - sp1v24_neg_full[i]
    if abs(diff) < 0.001 or diff < 0:
        banding_issues.append({
            'input_pair': f"{i}-{i+1}",
            'density_diff': diff,
            'risk': 'HIGH' if (diff < 0 or abs(diff) < 0.0005) else 'MEDIUM'
        })

if banding_issues:
    print(f"  ⚠️  {len(banding_issues)}箇所でバンディングリスクあり")
    for issue in banding_issues[:5]:
        print(f"    Input {issue['input_pair']}: ΔD={issue['density_diff']:.4f} ({issue['risk']})")
else:
    print(f"  ✓ バンディングリスクなし")
print()

# ============================================================================
# Step 7: Write .quad file
# ============================================================================
print("7️⃣ .quadファイル生成...")

# Use V7 as template
v7_template = "/Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-SP1v7.quad"

with open(v7_template, 'r') as f:
    v7_lines = f.readlines()

# Write SP1v24
output_file = "/tmp/PX1V-PtPd-SP1v24.quad"

with open(output_file, 'w') as f:
    # Write header (first 11 lines from V7, lines 0-10, index 0-10)
    # This is everything BEFORE "# K curve"
    for i in range(11):
        f.write(v7_lines[i])

    # Write K curve comment and values
    f.write("# K curve\n")
    for k_val in sp1v24_k_values:
        f.write(f"{k_val}\n")

    # Write remaining channels from V7 (lines 269 onwards = line index 268+)
    # V7: line 1-11 (index 0-10) = header
    # V7: line 12 (index 11) = "# K curve"
    # V7: lines 13-268 (index 12-267) = 256 K values
    # V7: line 269 (index 268) = "# C curve"
    for i in range(268, len(v7_lines)):
        f.write(v7_lines[i])

print(f"  ✓ .quadファイル生成: {output_file}")
print()

# Verify file
result = subprocess.run(["wc", "-l", output_file], capture_output=True, text=True)
line_count = int(result.stdout.split()[0])
print(f"  行数: {line_count} (期待値: 2570-2582)")
print()

# ============================================================================
# Step 8: Generate graphs
# ============================================================================
print("8️⃣ グラフ生成...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Graph 1: Negative Density Curve
ax1 = axes[0, 0]
ax1.plot(inputs_256, sp1v24_neg_full, 'g-', linewidth=2, label='SP1v24')
ax1.plot(sp1v23_data['input'], sp1v23_data['v23_negative_density'], 'b--o',
         markersize=4, label='SP1v23 (measured)', alpha=0.7)
ax1.axvline(x=128, color='gray', linestyle='--', alpha=0.5)
ax1.set_xlabel('Input (0=Black, 255=White)', fontsize=10)
ax1.set_ylabel('Negative Density', fontsize=10)
ax1.set_title('SP1v24: Negative Density Curve', fontsize=11, fontweight='bold')
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

# Graph 2: K Value Curve
ax2 = axes[0, 1]
ax2.plot(inputs_256, sp1v24_k_values, 'g-', linewidth=2, label='SP1v24')
ax2.plot(sp1v23_data['input'], sp1v23_data['v23_k_value'], 'b--o',
         markersize=4, label='SP1v23', alpha=0.7)
ax2.axvline(x=128, color='gray', linestyle='--', alpha=0.5)
ax2.set_xlabel('Input (0=Black, 255=White)', fontsize=10)
ax2.set_ylabel('K Value (0-65535)', fontsize=10)
ax2.set_title('SP1v24: K Value Curve', fontsize=11, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)

# Graph 3: Target Print Density Comparison
ax3 = axes[1, 0]
ax3.plot(data['input'], data['target_print_density'], 'g-o', markersize=4, label='SP1v24 Target')
ax3.plot(sp1v23_data['input'], sp1v23_data['v23_print_density'], 'b--s',
         markersize=4, label='SP1v23 Measured', alpha=0.7)
ax3.axvline(x=128, color='gray', linestyle='--', alpha=0.5)
ax3.axhline(y=0.80, color='red', linestyle=':', label='Input 128: 0.80D', alpha=0.7)
ax3.set_xlabel('Input (0=Black, 255=White)', fontsize=10)
ax3.set_ylabel('Print Density', fontsize=10)
ax3.set_title('SP1v24: Target Print Density', fontsize=11, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3)

# Graph 4: Negative Density Differences
ax4 = axes[1, 1]
neg_diff_at_measured = []
for inp in data['input']:
    idx = int(inp)
    v23_neg = sp1v23_data[sp1v23_data['input'] == inp]['v23_negative_density'].values[0]
    v24_neg = sp1v24_neg_full[idx]
    neg_diff_at_measured.append(v24_neg - v23_neg)

colors = ['green' if x > 0 else 'red' if x < 0 else 'gray' for x in neg_diff_at_measured]
ax4.bar(data['input'], neg_diff_at_measured, color=colors, alpha=0.6)
ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax4.axvline(x=128, color='gray', linestyle='--', alpha=0.5)
ax4.set_xlabel('Input (0=Black, 255=White)', fontsize=10)
ax4.set_ylabel('Negative Density Change (v24 - v23)', fontsize=10)
ax4.set_title('SP1v24: Negative Density Adjustments', fontsize=11, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
graph_output = '/tmp/sp1v24_curves.png'
plt.savefig(graph_output, dpi=150, bbox_inches='tight')
print(f"  ✓ グラフ保存: {graph_output}")
print()

# ============================================================================
# Summary
# ============================================================================
print("=" * 100)
print("📊 SP1v24 生成完了")
print("=" * 100)
print()

print("生成ファイル:")
print(f"  1. QTRカーブ: {output_file}")
print(f"  2. グラフ: {graph_output}")
print()

print("次のステップ:")
print("  1. グラフを確認してカーブの形状を承認")
print("  2. /Library/Printers/QTR/quadtone/QuadP700/ にインストール")
print("  3. 拡張属性を削除: xattr -c PX1V-PtPd-SP1v24.quad")
print("  4. テスト印刷・測定")
print()

print("=" * 100)
