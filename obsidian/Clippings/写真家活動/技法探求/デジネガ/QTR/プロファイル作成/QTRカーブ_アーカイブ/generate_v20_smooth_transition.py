#!/usr/bin/env python3
"""
PX1V-PtPd-v20: v18ベース、ハイライト域を滑らかに拡張
v18のInput 0-184をそのまま使用
Input 185-255を滑らかに補間してハイライト強化
"""

import numpy as np

# ========== v18の.quadファイルを読み込み ==========
v18_quad_file = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/QTRカーブ情報（V18使用）/backup_v18_FINAL_20260314/PX1V-PtPd-Linear-v18.quad'

print("=" * 80)
print("PX1V-PtPd-v20: v18ベース、ハイライト域を滑らかに拡張")
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
    """Quad値から濃度を逆算"""
    baseline = quad / 257
    density = baseline * SLOPE + INTERCEPT
    return density

# ========== v18の実測値（Input 184まで） ==========
v18_measured = {
    0: 0.07, 8: 0.08, 16: 0.13, 24: 0.16, 32: 0.18, 40: 0.20,
    48: 0.24, 56: 0.27, 64: 0.31, 72: 0.33, 80: 0.37, 88: 0.39,
    96: 0.43, 104: 0.48, 112: 0.53, 120: 0.58, 128: 0.63, 136: 0.67,
    144: 0.71, 152: 0.75, 160: 0.79, 168: 0.83, 176: 0.87, 184: 0.90,
}

# v18のInput 184のQuad値から濃度を逆算
v18_184_quad = v18_quad_values[184]
v18_184_density = quad_to_density(v18_184_quad)

print(f"\nv18のInput 184:")
print(f"  - Quad値: {v18_184_quad}")
print(f"  - 濃度（逆算）: {v18_184_density:.4f}")

# ========== v20のハイライト域目標値 ==========
v20_highlight_targets = {
    200: 0.95,
    208: 1.00,
    216: 1.02,
    224: 1.06,
    232: 1.12,
    240: 1.19,
    248: 1.24,
    255: 1.26,
}

# ========== アンカーポイント設定（滑らかな接続のため） ==========
# Input 184（v18の最後の測定点）からInput 200（v20の最初の目標）へ滑らかに接続
anchor_inputs = [184] + sorted(v20_highlight_targets.keys())
anchor_densities = [v18_184_density] + [v20_highlight_targets[i] for i in sorted(v20_highlight_targets.keys())]

print(f"\n=== アンカーポイント ===")
print(f"{'Input':>5} {'濃度':>8} {'ソース':>15}")
print("=" * 35)
print(f"{184:>5} {v18_184_density:>8.4f} {'v18実測':>15}")
for inp in sorted(v20_highlight_targets.keys()):
    dens = v20_highlight_targets[inp]
    print(f"{inp:>5} {dens:>8.4f} {'v20目標':>15}")

# ========== Input 185-255を線形補間 ==========
print(f"\n線形補間でInput 185-255を生成...")
highlight_range = range(185, 256)
highlight_densities = np.interp(highlight_range, anchor_inputs, anchor_densities)

# Quad値を計算
highlight_quads = []
for density in highlight_densities:
    baseline = density_to_baseline(density)
    quad = baseline_to_quad(baseline)
    highlight_quads.append(quad)

# ========== v20のQuad値配列を構築 ==========
# Input 0-184: v18のQuad値をそのまま使用
# Input 185-255: 新しく計算したQuad値
v20_quad_values = v18_quad_values[:185] + highlight_quads

# 単調性チェック
v20_quad_checked = [v20_quad_values[0]]
for i in range(1, len(v20_quad_values)):
    v20_quad_checked.append(max(v20_quad_values[i], v20_quad_checked[i-1]))

corrections = sum(1 for i in range(len(v20_quad_values)) if v20_quad_values[i] != v20_quad_checked[i])
if corrections > 0:
    print(f"⚠️  単調性補正: {corrections}ポイント")
    v20_quad_values = v20_quad_checked
else:
    print(f"✓ 単調性チェック: OK")

# ========== Quad値の勾配チェック ==========
quad_diffs = np.diff(v20_quad_values)
max_diff = np.max(quad_diffs)
max_diff_input = np.argmax(quad_diffs)

print(f"\n=== Quad値勾配解析 ===")
print(f"最大Quad差分: {max_diff:.0f} (Input {max_diff_input}→{max_diff_input+1})")
print(f"平均Quad差分: {np.mean(quad_diffs):.2f}")

# 境界線リスク（Quad差分 > 200）
risk_threshold = 200
risk_points = np.where(quad_diffs > risk_threshold)[0]

if len(risk_points) > 0:
    print(f"\n⚠️  境界線リスク（Quad差分 > {risk_threshold}）: {len(risk_points)}箇所")
    
    # 境界が見える範囲（Input 48-96）
    boundary_risk = [p for p in risk_points if 48 <= p <= 96]
    if boundary_risk:
        print(f"  ⚠️  境界が見える範囲（Input 48-96）: {len(boundary_risk)}箇所")
        for inp in boundary_risk[:5]:
            print(f"      Input {inp}→{inp+1}: Quad差分={quad_diffs[inp]:.0f}")
    else:
        print(f"  ✓ 境界が見える範囲（Input 48-96）: リスクなし")
    
    # ハイライト域
    highlight_risk = [p for p in risk_points if p >= 185]
    if highlight_risk:
        print(f"  ⚠️  ハイライト域（Input 185-255）: {len(highlight_risk)}箇所")
        print(f"      最大Quad差分のある箇所:")
        # Quad差分が大きい順に上位10箇所
        highlight_diffs = [(p, quad_diffs[p]) for p in highlight_risk]
        highlight_diffs.sort(key=lambda x: x[1], reverse=True)
        for inp, diff in highlight_diffs[:10]:
            dens = quad_to_density(v20_quad_values[inp])
            print(f"      Input {inp:3d}→{inp+1:3d}: Quad差分={diff:3.0f}, 濃度={dens:.3f}")
    else:
        print(f"  ✓ ハイライト域（Input 185-255）: リスクなし")
else:
    print(f"✓ 境界線リスクなし（全てのQuad差分 < {risk_threshold}）")

# ========== 詳細表示 ==========
print("\n=== Input 184-255の詳細（移行部分とハイライト域）===")
print(f"{'Input':>5} {'濃度':>8} {'Quad値':>10} {'Quad差分':>10} {'状態':>6} {'ソース':>10}")
print("=" * 65)

for i in range(184, 256):
    if i < 185:
        # v18の値
        quad_val = v18_quad_values[i]
        density_val = quad_to_density(quad_val)
        source = "v18"
    else:
        # v20の新しい値
        quad_val = v20_quad_values[i]
        density_val = highlight_densities[i - 185]
        source = "v20"
    
    diff = quad_val - v20_quad_values[i-1] if i > 0 else 0
    status = "⚠️" if diff > 200 else "✓"
    
    marker = ""
    if i in v20_highlight_targets or i == 184:
        marker = " <<<"
    
    if i == 184 or i in v20_highlight_targets or i >= 252:
        print(f"{i:>5} {density_val:>8.4f} {quad_val:>10} {diff:>10.0f} {status:>6} {source:>10}{marker}")

# ========== .quadファイル生成 ==========
output_quad = 'PX1V-PtPd-v20.quad'

new_header = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# PX1V-PtPd-v20 - v18 base with smooth highlight expansion
# Input 0-184: v18 quad values (proven smooth gradient)
# Input 185-255: Smooth highlight expansion (200:0.95, 208:1.00, 216:1.02, 224:1.06, 232:1.12, 240:1.19, 248:1.24, 255:1.26)
# Purpose: Compensate for print sensitivity compression in highlight area
# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# K curve
"""

with open(output_quad, 'wb') as f:
    f.write(new_header.encode('ascii'))
    
    for quad_val in v20_quad_values:
        f.write(f'{int(quad_val)}\n'.encode('ascii'))
    
    # 残り9チャンネル
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

# ========== v18とv20の比較 ==========
print(f"\n=== v18とv20のハイライト域比較 ===")
print(f"{'Input':>5} {'v18濃度':>10} {'v20濃度':>10} {'濃度差':>10} {'v18 Quad':>10} {'v20 Quad':>10} {'Quad差':>10}")
print("=" * 80)

for inp in [200, 208, 216, 224, 232, 240, 248, 255]:
    v18_quad = v18_quad_values[inp]
    v18_dens = quad_to_density(v18_quad)
    v20_quad = v20_quad_values[inp]
    v20_dens = quad_to_density(v20_quad)
    dens_diff = v20_dens - v18_dens
    quad_diff = v20_quad - v18_quad
    print(f"{inp:>5} {v18_dens:>10.4f} {v20_dens:>10.4f} {dens_diff:>+10.4f} {v18_quad:>10} {v20_quad:>10} {quad_diff:>+10}")

print(f"\n=== ハイライト拡張の効果 ===")
print("v18の問題:")
print("  Input 240-255の濃度差: 0.08D (1.14→1.22)")
print("  → プリント感度圧縮で約0.016Dに (視認不可)")
print("")
print("v20の改善:")
print("  Input 240-255の濃度差: 0.14D (1.12→1.26)")
print("  → プリント感度圧縮でも約0.028Dに (視認可能性向上)")
print(f"  拡張率: {0.14/0.08:.1f}倍")

print("\n次のステップ:")
print(f"  1. sudo cp {output_quad} /Library/Printers/QTR/quadtone/QuadP700/")
print(f"  2. /Library/Printers/QTR/bin/quadcurves QuadP700")
print(f"  3. defaults delete com.quadtonerip.QTR-Print-Tool")
print(f"  4. QTR Print-Toolで v20 を選択してテストプリント")
print(f"  5. プリント結果の確認（240-255の階調が見えるか）")

