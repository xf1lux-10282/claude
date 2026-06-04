#!/usr/bin/env python3
"""
PX1V-PtPd-v21: v20実測値を基にした微調整版
v20実測値から、240-255の階調を最適化
"""

import numpy as np
from scipy.interpolate import CubicSpline

# ========== v18の.quadファイルを読み込み ==========
v18_quad_file = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/QTRカーブ情報（V18使用）/backup_v18_FINAL_20260314/PX1V-PtPd-Linear-v18.quad'

print("=" * 80)
print("PX1V-PtPd-v21: v20実測値ベースの微調整版")
print("=" * 80)

with open(v18_quad_file, 'r') as f:
    v18_lines = f.readlines()

# Kチャンネルの開始行を見つける
k_curve_start = None
for i, line in enumerate(v18_lines):
    if '# K curve' in line:
        k_curve_start = i + 1
        break

# v18のQuad値を読み込み
v18_quad_values = []
for i in range(k_curve_start, k_curve_start + 256):
    val = int(v18_lines[i].strip())
    v18_quad_values.append(val)

print(f"\n✓ v18の.quadファイルを読み込みました")

# ========== v18と同じベースライン補正式 ==========
SLOPE = 0.007387
INTERCEPT = 0.0935

def density_to_baseline(density):
    baseline = (density - INTERCEPT) / SLOPE
    return np.clip(baseline, 0, 255)

def baseline_to_quad(baseline):
    return int(round(baseline * 257))

def quad_to_density(quad):
    baseline = quad / 257
    density = baseline * SLOPE + INTERCEPT
    return density

# ========== v21の目標値（v20実測をベース） ==========
# v20実測値をそのまま使用するポイント
v20_measured = {
    200: 0.98,
    208: 1.03,
    216: 1.05,
    224: 1.08,
    232: 1.13,
}

# v21で微調整するポイント
v21_adjusted = {
    240: 1.20,  # v20実測1.23 → 1.20に下げる
    248: 1.26,  # v20実測1.27 → 1.26に下げる
    255: 1.29,  # v20実測1.29 → そのまま
}

# v21の全目標値
v21_targets = {**v20_measured, **v21_adjusted}

print(f"\n=== v21の目標値設定 ===")
print(f"{'Input':>5} {'濃度':>8} {'ソース':>20}")
print("=" * 40)
for inp in sorted(v21_targets.keys()):
    dens = v21_targets[inp]
    source = "v20実測（そのまま）" if inp in v20_measured else "v21微調整"
    print(f"{inp:>5} {dens:>8.2f} {source:>20}")

# ========== スプライン補間用の制御点を設定 ==========
# v18のInput 176, 184 + v21の目標値
v18_176_quad = v18_quad_values[176]
v18_184_quad = v18_quad_values[184]
v18_176_density = quad_to_density(v18_176_quad)
v18_184_density = quad_to_density(v18_184_quad)

control_points_input = [176, 184] + sorted(v21_targets.keys())
control_points_density = [v18_176_density, v18_184_density] + [v21_targets[i] for i in sorted(v21_targets.keys())]

control_points_input = np.array(control_points_input)
control_points_density = np.array(control_points_density)

print(f"\n=== スプライン補間の制御点 ===")
print(f"{'Input':>5} {'濃度':>10} {'ソース':>15}")
print("=" * 35)
for i, inp in enumerate(control_points_input):
    dens = control_points_density[i]
    source = "v18実測" if inp < 200 else ("v20実測" if inp <= 232 else "v21調整")
    print(f"{inp:>5} {dens:>10.4f} {source:>15}")

# ========== スプライン補間を実行 ==========
print(f"\nスプライン補間を実行（Input 177-255）...")
spline = CubicSpline(control_points_input, control_points_density)

highlight_range = range(177, 256)
highlight_densities_spline = spline(highlight_range)

# Quad値を計算
highlight_quads = []
for density in highlight_densities_spline:
    baseline = density_to_baseline(density)
    quad = baseline_to_quad(baseline)
    highlight_quads.append(quad)

# ========== v21のQuad値配列を構築 ==========
v21_quad_values = v18_quad_values[:177] + highlight_quads

# 単調性チェック
v21_quad_checked = [v21_quad_values[0]]
for i in range(1, len(v21_quad_values)):
    v21_quad_checked.append(max(v21_quad_values[i], v21_quad_checked[i-1]))

corrections = sum(1 for i in range(len(v21_quad_values)) if v21_quad_values[i] != v21_quad_checked[i])
if corrections > 0:
    print(f"⚠️  単調性補正: {corrections}ポイント")
    v21_quad_values = v21_quad_checked
else:
    print(f"✓ 単調性チェック: OK")

# ========== Quad値の勾配チェック ==========
quad_diffs = np.diff(v21_quad_values)
max_diff = np.max(quad_diffs)
max_diff_input = np.argmax(quad_diffs)

print(f"\n=== Quad値勾配解析 ===")
print(f"最大Quad差分: {max_diff:.0f} (Input {max_diff_input}→{max_diff_input+1})")
print(f"平均Quad差分: {np.mean(quad_diffs):.2f}")
print(f"標準偏差: {np.std(quad_diffs):.2f}")

# 境界線リスク
risk_threshold = 200
risk_points = np.where(quad_diffs > risk_threshold)[0]

if len(risk_points) > 0:
    print(f"\n⚠️  境界線リスク（Quad差分 > {risk_threshold}）: {len(risk_points)}箇所")
    
    boundary_risk = [p for p in risk_points if 48 <= p <= 96]
    if boundary_risk:
        print(f"  ⚠️  境界が見える範囲（Input 48-96）: {len(boundary_risk)}箇所")
    else:
        print(f"  ✓ 境界が見える範囲（Input 48-96）: リスクなし")
    
    highlight_risk = [p for p in risk_points if p >= 177]
    if highlight_risk:
        print(f"  ⚠️  ハイライト域（Input 177-255）: {len(highlight_risk)}箇所")
        print(f"      最大Quad差分のある箇所（上位5）:")
        highlight_diffs = [(p, quad_diffs[p]) for p in highlight_risk]
        highlight_diffs.sort(key=lambda x: x[1], reverse=True)
        for inp, diff in highlight_diffs[:5]:
            dens = quad_to_density(v21_quad_values[inp])
            print(f"      Input {inp:3d}→{inp+1:3d}: Quad差分={diff:3.0f}, 濃度={dens:.3f}")
    else:
        print(f"  ✓ ハイライト域（Input 177-255）: リスクなし")
else:
    print(f"✓ 境界線リスクなし")

# ========== ハイライト域の詳細 ==========
print("\n=== ハイライト域の詳細（Input 200-255、目標値ポイント）===")
print(f"{'Input':>5} {'濃度':>10} {'Quad値':>10} {'Quad差分':>10} {'状態':>6}")
print("=" * 50)

for inp in sorted(v21_targets.keys()):
    if inp >= 200:
        quad_val = v21_quad_values[inp]
        density_val = highlight_densities_spline[inp - 177]
        diff = quad_val - v21_quad_values[inp-1] if inp > 0 else 0
        status = "⚠️" if diff > 200 else "✓"
        
        print(f"{inp:>5} {density_val:>10.4f} {quad_val:>10} {diff:>10.0f} {status:>6}")

# ========== .quadファイル生成 ==========
output_quad = 'PX1V-PtPd-v21.quad'

new_header = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# PX1V-PtPd-v21 - Fine-tuned based on v20 measurements
# Input 0-176: v18 quad values (proven smooth gradient)
# Input 177-255: Cubic spline with v20 measurements + v21 adjustments
# Control points: 176, 184 (v18), 200-232 (v20 measured), 240-255 (v21 adjusted)
# Adjustments: 240:1.20 (down0.03), 248:1.26 (down0.01), 255:1.29 (maintained)
# Purpose: Optimize 240-255 density range for print visibility
# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# K curve
"""

with open(output_quad, 'wb') as f:
    f.write(new_header.encode('ascii'))
    
    for quad_val in v21_quad_values:
        f.write(f'{int(quad_val)}\n'.encode('ascii'))
    
    footer_start = k_curve_start + 256
    footer_text = ''.join(v18_lines[footer_start:])
    f.write(footer_text.encode('ascii'))

print(f"\n✓ .quadファイル生成: {output_quad}")

# ========== ファイル検証 ==========
import subprocess
file_check = subprocess.run(['file', output_quad], capture_output=True, text=True)
line_count = subprocess.run(['wc', '-l', output_quad], capture_output=True, text=True)

print(f"\n=== ファイル検証 ===")
print(f"エンコーディング: {file_check.stdout.strip()}")
print(f"行数: {line_count.stdout.strip()}")

# ========== v20実測とv21目標の比較 ==========
print(f"\n=== v20実測 vs v21目標（ハイライト域）===")
print(f"{'Input':>5} {'v20実測':>10} {'v21目標':>10} {'差分':>10}")
print("=" * 45)

v20_measured_full = {200: 0.98, 208: 1.03, 216: 1.05, 224: 1.08, 232: 1.13, 240: 1.23, 248: 1.27, 255: 1.29}

for inp in sorted(v21_targets.keys()):
    v20_val = v20_measured_full.get(inp, 0)
    v21_val = v21_targets[inp]
    diff = v21_val - v20_val
    print(f"{inp:>5} {v20_val:>10.2f} {v21_val:>10.2f} {diff:>+10.3f}")

# ========== 詳細データCSV ==========
output_csv = 'PX1V-PtPd-v21_detail.csv'
with open(output_csv, 'w') as f:
    f.write('Input,Quad_Value,Baseline,Density,Quad_Diff,Source\n')
    for i in range(256):
        quad = v21_quad_values[i]
        baseline = quad / 257
        density = quad_to_density(quad)
        diff = quad - v21_quad_values[i-1] if i > 0 else 0
        source = 'v18' if i < 177 else 'v21_spline'
        f.write(f'{i},{quad},{baseline:.6f},{density:.6f},{diff},{source}\n')

print(f"✓ 詳細データ: {output_csv}")

print(f"\n=== v21の特徴 ===")
print("1. v20実測値を制御点として使用（実現可能性が高い）")
print("2. Input 240を1.23D→1.20Dに下げることで、240-255の階調を改善")
print("3. Input 240-255の濃度レンジ: 0.09D（v20の0.06Dから1.5倍に拡大）")
print("4. v18の0.08Dより1.12倍に拡張")

print("\n次のステップ:")
print(f"  1. sudo cp {output_quad} /Library/Printers/QTR/quadtone/QuadP700/")
print(f"  2. /Library/Printers/QTR/bin/quadcurves QuadP700")
print(f"  3. QTR Print-Toolで v21 を選択してテストプリント")
print(f"  4. 確認ポイント:")
print(f"     - 境界線（Input 232-240付近）")
print(f"     - ハイライト階調（240, 248, 255が分離するか）")

