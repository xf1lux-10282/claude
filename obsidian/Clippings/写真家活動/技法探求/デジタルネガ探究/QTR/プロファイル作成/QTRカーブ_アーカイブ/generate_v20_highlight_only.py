#!/usr/bin/env python3
"""
PX1V-PtPd-v20: v18ベースのハイライト強化版
v18の方法（256ポイント、正しいベースライン式）を使用
ハイライト域（Input 200-255）のみを調整
"""

import numpy as np
import pandas as pd

# ========== v18と同じベースライン補正式 ==========
# v11のBaseline関係式（v14/v18と同じ）
SLOPE = 0.007387
INTERCEPT = 0.0935

def density_to_baseline(density):
    """濃度からベースライン値を計算（v18と同じ）"""
    baseline = (density - INTERCEPT) / SLOPE
    return np.clip(baseline, 0, 255)

def baseline_to_quad(baseline):
    """ベースライン値をQuad値に変換（v18と同じ）"""
    return int(round(baseline * 257))

# ========== v18実測値 ==========
v18_measured = {
    0: 0.07, 8: 0.08, 16: 0.13, 24: 0.16, 32: 0.18, 40: 0.20,
    48: 0.24, 56: 0.27, 64: 0.31, 72: 0.33, 80: 0.37, 88: 0.39,
    96: 0.43, 104: 0.48, 112: 0.53, 120: 0.58, 128: 0.63, 136: 0.67,
    144: 0.71, 152: 0.75, 160: 0.79, 168: 0.83, 176: 0.87, 184: 0.90,
    192: 0.94,
}

# ========== v20のハイライト域目標値（ユーザー提案） ==========
v20_highlight_adjustments = {
    200: 0.95,
    208: 1.00,
    216: 1.02,
    224: 1.06,
    232: 1.12,
    240: 1.19,
    248: 1.24,
    255: 1.26,
}

# ========== v20アンカーポイント ==========
v20_anchors = v18_measured.copy()
v20_anchors.update(v20_highlight_adjustments)

anchor_inputs = np.array(sorted(v20_anchors.keys()))
anchor_densities = np.array([v20_anchors[i] for i in anchor_inputs])

print("=" * 80)
print("PX1V-PtPd-v20: v18ベースのハイライト強化版")
print("=" * 80)
print(f"\nアンカーポイント: {len(anchor_inputs)}点")
print(f"  - Input 0-192: v18実測値そのまま")
print(f"  - Input 200-255: ハイライト強化")

print("\n=== ハイライト域の調整 ===")
print(f"{'Input':>5} {'v18実測':>8} {'v20目標':>8} {'調整':>8}")
print("=" * 40)
for inp in [200, 208, 216, 224, 232, 240, 248, 255]:
    v18_val = v18_measured.get(inp, None)
    v20_val = v20_anchors[inp]
    if v18_val is not None:
        adj = v20_val - v18_val
        print(f"{inp:>5} {v18_val:>8.2f} {v20_val:>8.2f} {adj:>+8.2f}")
    else:
        print(f"{inp:>5} {'---':>8} {v20_val:>8.2f} {'新規':>8}")

# ========== 256ポイント生成（v18と同じ方法） ==========
print("\n線形補間で256ポイント生成...")
input_indices = np.arange(256)  # 0, 1, 2, ..., 255（256ポイント）
target_densities = np.interp(input_indices, anchor_inputs, anchor_densities)

# Baseline値とQuad値を計算
baselines = np.array([density_to_baseline(d) for d in target_densities])
quad_values = np.array([baseline_to_quad(b) for b in baselines])

# 単調性チェック
quad_values_checked = [quad_values[0]]
for i in range(1, len(quad_values)):
    quad_values_checked.append(max(quad_values[i], quad_values_checked[i-1]))
quad_values_checked = np.array(quad_values_checked)

corrections = np.sum(quad_values != quad_values_checked)
if corrections > 0:
    print(f"⚠️  単調性補正: {corrections}ポイント")
else:
    print(f"✓ 単調性チェック: OK")

# ========== Quad値の勾配チェック（境界線検出） ==========
quad_diffs = np.diff(quad_values_checked)
max_diff = np.max(quad_diffs)
max_diff_input = np.argmax(quad_diffs)

print(f"\n=== Quad値勾配解析（境界線リスク） ===")
print(f"最大Quad差分: {max_diff:.0f} (Input {max_diff_input}→{max_diff_input+1})")

# 境界線リスクの高い箇所（Quad差分 > 200）
risk_threshold = 200
risk_points = np.where(quad_diffs > risk_threshold)[0]
if len(risk_points) > 0:
    print(f"\n⚠️  境界線リスク（Quad差分 > {risk_threshold}）: {len(risk_points)}箇所")
    for inp in risk_points[:20]:  # 最初の20箇所のみ表示
        diff = quad_diffs[inp]
        dens = target_densities[inp]
        print(f"  Input {inp:3d}→{inp+1:3d}: Quad差分={diff:4.0f}, 濃度={dens:.3f}")
else:
    print(f"✓ 境界線リスクなし（全てのQuad差分 < {risk_threshold}）")

# ハイライト域の勾配確認
print("\n=== ハイライト域のQuad差分（Input 200-255）===")
print(f"{'Input':>8} {'濃度':>8} {'Quad値':>10} {'Quad差分':>10} {'リスク':>8}")
print("=" * 55)
for i in range(200, 256):
    diff = quad_values_checked[i] - quad_values_checked[i-1] if i > 0 else 0
    risk = "⚠️" if diff > 200 else "✓"
    if i % 8 == 0 or i >= 248:  # 8刻みとハイライト末尾を表示
        print(f"{i:>8} {target_densities[i]:>8.3f} {quad_values_checked[i]:>10} {diff:>10.0f} {risk:>8}")

# ========== .quadファイル生成 ==========
output_quad = 'PX1V-PtPd-v20.quad'
with open(output_quad, 'wb') as f:
    content = '## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n'
    content += '# QuadProfile Version 2.8.0\n'
    content += '# PX1V-PtPd-v20 - Highlight Enhanced based on v18\n'
    content += '# Input 0-192: v18 measured values\n'
    content += '# Input 200-255: Highlight enhancement (200: 0.95, 208: 1.00, 216: 1.02, 224: 1.06, 232: 1.12, 240: 1.19, 248: 1.24, 255: 1.26)\n'
    content += '# 2026 Daisuke Kinoshita\n'
    content += '# BOOST_K=0 - NO BOOST\n'
    content += '# K curve\n'
    
    for qv in quad_values_checked:
        content += f'{int(qv)}\n'
    
    # 残り9チャンネル（全て0）
    for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
        content += f'# {channel} curve\n'
        for _ in range(256):
            content += '0\n'
    
    f.write(content.encode('ascii'))

print(f"\n✓ .quadファイル生成: {output_quad}")

# ========== .txtファイル生成 ==========
output_txt = 'PX1V-PtPd-v20.txt'
df = pd.DataFrame({
    'Input': input_indices,
    'Target_Density': target_densities,
    'Baseline': baselines,
    'Quad_Value': quad_values_checked
})
df.to_csv(output_txt, index=False, float_format='%.6f')
print(f"✓ 詳細データ: {output_txt}")

# ========== ファイル検証 ==========
import subprocess
file_check = subprocess.run(['file', output_quad], capture_output=True, text=True)
line_count = subprocess.run(['wc', '-l', output_quad], capture_output=True, text=True)

print(f"\n=== ファイル検証 ===")
print(f"エンコーディング: {file_check.stdout.strip()}")
print(f"行数: {line_count.stdout.strip()}")

# Input 255の値確認
print(f"\n=== 重要ポイント検証 ===")
print(f"Input 255の目標濃度: {target_densities[255]:.4f}")
print(f"Input 255のQuad値: {quad_values_checked[255]}")

print("\n次のステップ:")
print(f"  1. sudo cp {output_quad} /Library/Printers/QTR/quadtone/QuadP700/")
print(f"  2. /Library/Printers/QTR/bin/quadcurves QuadP700")
print(f"  3. defaults delete com.quadtonerip.QTR-Print-Tool")
print(f"  4. QTR Print-Toolで v20 を選択してテストプリント")
print(f"  5. 濃度測定とv19との比較")

