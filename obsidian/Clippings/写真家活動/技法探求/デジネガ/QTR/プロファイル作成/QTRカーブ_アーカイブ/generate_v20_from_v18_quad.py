#!/usr/bin/env python3
"""
PX1V-PtPd-v20: v18の.quadファイルベース、ハイライト域のみ置き換え
v18のQuad値（Input 0-199）をそのまま使用
Input 200-255のみを新しい目標値で計算
"""

import numpy as np

# ========== v18の.quadファイルを読み込み ==========
v18_quad_file = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/QTRカーブ情報（V18使用）/backup_v18_FINAL_20260314/PX1V-PtPd-Linear-v18.quad'

print("=" * 80)
print("PX1V-PtPd-v20: v18ベース、ハイライト域のみ置き換え")
print("=" * 80)

with open(v18_quad_file, 'r') as f:
    v18_lines = f.readlines()

# Kチャンネルの開始行を見つける
k_curve_start = None
for i, line in enumerate(v18_lines):
    if '# K curve' in line:
        k_curve_start = i + 1
        break

if k_curve_start is None:
    print("エラー: v18のKチャンネルが見つかりません")
    exit(1)

# v18のQuad値を読み込み（256個）
v18_quad_values = []
for i in range(k_curve_start, k_curve_start + 256):
    val = int(v18_lines[i].strip())
    v18_quad_values.append(val)

print(f"\n✓ v18の.quadファイルを読み込みました")
print(f"  - Quad値の総数: {len(v18_quad_values)}")
print(f"  - 範囲: {v18_quad_values[0]} - {v18_quad_values[-1]}")

# ========== v18と同じベースライン補正式 ==========
SLOPE = 0.007387
INTERCEPT = 0.0935

def density_to_baseline(density):
    """濃度からベースライン値を計算（v18と同じ）"""
    baseline = (density - INTERCEPT) / SLOPE
    return np.clip(baseline, 0, 255)

def baseline_to_quad(baseline):
    """ベースライン値をQuad値に変換（v18と同じ）"""
    return int(round(baseline * 257))

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

# v18の実測値（Input 192まで）
v18_measured = {
    0: 0.07, 8: 0.08, 16: 0.13, 24: 0.16, 32: 0.18, 40: 0.20,
    48: 0.24, 56: 0.27, 64: 0.31, 72: 0.33, 80: 0.37, 88: 0.39,
    96: 0.43, 104: 0.48, 112: 0.53, 120: 0.58, 128: 0.63, 136: 0.67,
    144: 0.71, 152: 0.75, 160: 0.79, 168: 0.83, 176: 0.87, 184: 0.90,
    192: 0.94,
}

print("\n=== ハイライト域の目標値 ===")
print(f"{'Input':>5} {'目標濃度':>10} {'v18からの変化':>15}")
print("=" * 35)
for inp in sorted(v20_highlight_targets.keys()):
    target = v20_highlight_targets[inp]
    v18_val = v18_measured.get(inp, None)
    if v18_val is not None:
        change = target - v18_val
        print(f"{inp:>5} {target:>10.2f} {change:>+15.2f}")
    else:
        print(f"{inp:>5} {target:>10.2f} {'新規':>15}")

# ========== Input 193-255のハイライト域を計算 ==========
# アンカーポイント: v18の192 + v20の200-255
anchor_inputs = [192] + sorted(v20_highlight_targets.keys())
anchor_densities = [v18_measured[192]] + [v20_highlight_targets[i] for i in sorted(v20_highlight_targets.keys())]

print(f"\n線形補間でInput 193-255を生成...")
print(f"アンカーポイント: {anchor_inputs}")

# Input 193-255を線形補間
highlight_densities = np.interp(range(193, 256), anchor_inputs, anchor_densities)

# Quad値を計算
highlight_quads = []
for density in highlight_densities:
    baseline = density_to_baseline(density)
    quad = baseline_to_quad(baseline)
    highlight_quads.append(quad)

# ========== v20のQuad値配列を構築 ==========
# Input 0-192: v18のQuad値をそのまま使用
# Input 193-255: 新しく計算したQuad値
v20_quad_values = v18_quad_values[:193] + highlight_quads

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

# 境界線リスク（Quad差分 > 200）
risk_threshold = 200
risk_points = np.where(quad_diffs > risk_threshold)[0]

if len(risk_points) > 0:
    print(f"\n⚠️  境界線リスク（Quad差分 > {risk_threshold}）: {len(risk_points)}箇所")
    
    # 境界が見える範囲（濃度0.25-0.40D、Input 48-96付近）でのリスク
    boundary_risk = [p for p in risk_points if 48 <= p <= 96]
    if boundary_risk:
        print(f"  - 境界が見える範囲（Input 48-96）: {len(boundary_risk)}箇所")
        for inp in boundary_risk[:10]:
            print(f"    Input {inp}→{inp+1}: Quad差分={quad_diffs[inp]:.0f}")
    else:
        print(f"  ✓ 境界が見える範囲（Input 48-96）: リスクなし")
    
    # ハイライト域でのリスク
    highlight_risk = [p for p in risk_points if p >= 193]
    if highlight_risk:
        print(f"  - ハイライト域（Input 193-255）: {len(highlight_risk)}箇所")
        for inp in highlight_risk[:10]:
            print(f"    Input {inp}→{inp+1}: Quad差分={quad_diffs[inp]:.0f}")
    else:
        print(f"  ✓ ハイライト域（Input 193-255）: リスクなし")
else:
    print(f"✓ 境界線リスクなし（全てのQuad差分 < {risk_threshold}）")

# ========== ハイライト域の詳細表示 ==========
print("\n=== ハイライト域の詳細（Input 192-255）===")
print(f"{'Input':>5} {'濃度':>8} {'Quad値':>10} {'Quad差分':>10} {'状態':>8}")
print("=" * 50)

for i in range(192, 256):
    density_val = highlight_densities[i - 193] if i >= 193 else v18_measured.get(192, 0)
    if i == 192:
        # v18の値
        baseline_192 = v18_quad_values[192] / 257
        density_192 = baseline_192 * SLOPE + INTERCEPT
        density_val = density_192
    
    quad_val = v20_quad_values[i]
    diff = quad_val - v20_quad_values[i-1] if i > 0 else 0
    status = "⚠️" if diff > 200 else "✓"
    
    marker = ""
    if i in v20_highlight_targets:
        marker = " <<<"
    
    if i % 4 == 0 or i >= 248 or i == 192:  # 4刻みとハイライト末尾を表示
        print(f"{i:>5} {density_val:>8.3f} {quad_val:>10} {diff:>10.0f} {status:>8}{marker}")

# ========== .quadファイル生成 ==========
output_quad = 'PX1V-PtPd-v20.quad'

# v18のヘッダーとフッターを維持
header_lines = v18_lines[:k_curve_start]
footer_start = k_curve_start + 256

# ヘッダーを修正
header_text = ''.join(header_lines)
header_text = header_text.replace('v18', 'v20')
header_text = header_text.replace('Best of v14 + v17', 'v18 base with highlight enhancement')

# 新しいコメント行を追加
new_header = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# PX1V-PtPd-v20 - v18 base with highlight enhancement (Input 193-255)
# Input 0-192: v18 quad values (proven smooth gradient)
# Input 193-255: Enhanced highlight (200:0.95, 208:1.00, 216:1.02, 224:1.06, 232:1.12, 240:1.19, 248:1.24, 255:1.26)
# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# K curve
"""

with open(output_quad, 'wb') as f:
    # ヘッダー
    f.write(new_header.encode('ascii'))
    
    # Kチャンネル（v20のQuad値）
    for quad_val in v20_quad_values:
        f.write(f'{int(quad_val)}\n'.encode('ascii'))
    
    # 残り9チャンネル（v18のフッターをそのまま使用）
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

# v18とv20の比較
print(f"\n=== v18とv20の比較 ===")
print(f"{'範囲':>15} {'変更':>40}")
print("=" * 60)
print(f"{'Input 0-192':>15} {'v18のQuad値をそのまま使用（境界線なし）':>40}")
print(f"{'Input 193-199':>15} {'線形補間（v18の192→v20の200へ接続）':>40}")
print(f"{'Input 200-255':>15} {'ハイライト強化（目標濃度に基づく）':>40}")

# Input 255の検証
print(f"\n=== Input 255検証 ===")
print(f"目標濃度: {v20_highlight_targets[255]:.4f}")
print(f"Quad値: {v20_quad_values[255]}")
print(f"v18からの変化: {v20_quad_values[255] - v18_quad_values[255]:+d} (v18: {v18_quad_values[255]})")

print("\n次のステップ:")
print(f"  1. sudo cp {output_quad} /Library/Printers/QTR/quadtone/QuadP700/")
print(f"  2. /Library/Printers/QTR/bin/quadcurves QuadP700")
print(f"  3. defaults delete com.quadtonerip.QTR-Print-Tool")
print(f"  4. QTR Print-Toolで v20 を選択してテストプリント")
print(f"  5. 濃度測定（特にハイライト域 Input 200-255）")

