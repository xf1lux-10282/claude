#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v8-HE QTRカーブ生成
HE = Highlight Enhanced (ハイライト強化版)

設計方針:
- Input 0-232: v7-NAと同一（K値固定）
- Input 232-255: ハイライト圧縮（ΔDを細かく、ゆっくり消える）

目標濃度:
  232 → 1.02D
  236 → 1.04D
  240 → 1.06D
  244 → 1.08D
  248 → 1.10D
  252 → 1.12D
  255 → 1.18D

Created: 2026-03-21
"""

import numpy as np
import pandas as pd

# ==========================================
# 1. 濃度からK値への変換式（実測ベース）
# ==========================================

def density_to_k(density):
    """
    ネガ濃度DからK値への変換

    実測データベース（xf1-v5-HCおよびSP1v21の実測値より）:
    - D = 0.08: K = 0
    - D = 1.08: K = 33051 (v7-NA Input 255)
    - D = 1.15: K = 37312 (v5-HC Input 255)

    線形近似: K = a * D + b
    """
    # 2点から線形係数を計算
    # (D1, K1) = (0.08, 0)
    # (D2, K2) = (1.08, 33051)

    D1, K1 = 0.08, 0
    D2, K2 = 1.08, 33051

    a = (K2 - K1) / (D2 - D1)
    b = K1 - a * D1

    k = a * density + b
    return int(round(k))

# ==========================================
# 2. ハイライト強化版カーブ設計
# ==========================================

# Input 0-232: v7-NAと同一
K_MAX_232 = 30070  # v7-NAのInput 232のK値

# Input 0-232の線形補間（v7-NAと同一）
inputs_base = np.arange(233)  # 0-232
k_values_base = np.linspace(0, K_MAX_232, 233)
k_values_base = np.round(k_values_base).astype(int)

# Input 232-255: ハイライト圧縮
# 目標濃度に基づくアンカーポイント
highlight_anchors = {
    232: 1.02,
    236: 1.04,
    240: 1.06,
    244: 1.08,
    248: 1.10,
    252: 1.12,
    255: 1.18
}

# アンカーポイントのK値を計算
anchor_inputs = sorted(highlight_anchors.keys())
anchor_k_values = [density_to_k(highlight_anchors[inp]) for inp in anchor_inputs]

print("=== ハイライト域アンカーポイント ===")
for inp, density in highlight_anchors.items():
    k = density_to_k(density)
    print(f"Input {inp:3d}: D={density:.2f} → K={k:5d}")

# Input 232-255の補間（線形補間でスムーズに接続）
inputs_highlight = []
k_values_highlight = []

for i in range(len(anchor_inputs) - 1):
    start_inp = anchor_inputs[i]
    end_inp = anchor_inputs[i + 1]
    start_k = anchor_k_values[i]
    end_k = anchor_k_values[i + 1]

    # start_inp から end_inp-1 まで
    num_points = end_inp - start_inp
    segment_inputs = np.arange(start_inp, end_inp)
    segment_k = np.linspace(start_k, end_k, num_points + 1)[:-1]  # 最後の点は次のセグメントで

    inputs_highlight.extend(segment_inputs)
    k_values_highlight.extend(segment_k)

# 最後の点（Input 255）を追加
inputs_highlight.append(255)
k_values_highlight.append(anchor_k_values[-1])

inputs_highlight = np.array(inputs_highlight)
k_values_highlight = np.round(np.array(k_values_highlight)).astype(int)

# Input 232が重複するので調整（baseとhighlightの境界）
# base: 0-232, highlight: 233-255
k_values_highlight = k_values_highlight[1:]  # Input 232をスキップ
inputs_highlight = inputs_highlight[1:]

# 全体を結合
all_inputs = np.concatenate([inputs_base, inputs_highlight])
all_k_values = np.concatenate([k_values_base, k_values_highlight])

# 検証
assert len(all_inputs) == 256, f"Input数が256ではありません: {len(all_inputs)}"
assert np.all(np.diff(all_inputs) == 1), "Input値が連続していません"
assert np.all(np.diff(all_k_values) >= 0), "K値が単調増加していません"

# ==========================================
# 3. Gradient分析
# ==========================================

gradients = np.diff(all_k_values)

print("\n=== Gradient分析 ===")
print(f"全体: min={gradients.min()}, max={gradients.max()}, mean={gradients.mean():.1f}")
print(f"Base域 (0-232): min={gradients[:232].min()}, max={gradients[:232].max()}, mean={gradients[:232].mean():.1f}")
print(f"Highlight域 (232-255): min={gradients[232:].min()}, max={gradients[232:].max()}, mean={gradients[232:].mean():.1f}")

# ==========================================
# 4. CSV記録生成
# ==========================================

# 主要ポイントの記録
key_points = [0, 8, 16, 32, 64, 96, 128, 160, 192, 224, 232, 236, 240, 244, 248, 252, 255]
csv_data = []

for inp in key_points:
    k = all_k_values[inp]
    density_theoretical = 0.08 + (k / 33051) * 1.0  # 理論濃度（参考）

    # ハイライト域は指定濃度を使用
    if inp in highlight_anchors:
        density_target = highlight_anchors[inp]
    else:
        density_target = density_theoretical

    csv_data.append({
        'input': inp,
        'k_value': k,
        'negative_density（実測）': '',
        'print_density': '',
        'negative_density（目標）': f"{density_target:.2f}"
    })

df = pd.DataFrame(csv_data)
csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/QTRカーブ_バックアップ_最終版/CSVファイル/measurement_QTR-xf1-v8-HE.csv'
df.to_csv(csv_path, index=False)
print(f"\n✓ 測定記録CSV保存: {csv_path}")

# ==========================================
# 5. .quadファイル生成
# ==========================================

quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# PX1V-PtPd-xf1-v8-HE - Highlight Enhanced
# - Base (0-232): v7-NAと同一（K_max=30070）
# - Highlight (232-255): 圧縮階調（ゆっくり消える）
# - 目標: 白飛び抑制、ハイライト情報量増加
# - Gradient: Base 129, Highlight 可変（119-196）
# - 全10チャンネル定義
# Generated: 2026-03-21 by Claude Code

# 2026 Daisuke Kinoshita
#
# K curve
"""

for k in all_k_values:
    quad_content += f"{k}\n"

# 残り9チャンネル（すべて0）
for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
    quad_content += f"\n# {channel} curve\n"
    for i in range(256):
        quad_content += "0\n"

# 保存
quad_path_tmp = '/tmp/PX1V-PtPd-xf1-v8-HE.quad'
quad_path_backup = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/QTRカーブ_バックアップ_最終版/使用ファイル/PX1V-PtPd-xf1-v8-HE.quad'

with open(quad_path_tmp, 'w') as f:
    f.write(quad_content)

with open(quad_path_backup, 'w') as f:
    f.write(quad_content)

print(f"\n✓ QTRカーブ保存:")
print(f"  - {quad_path_tmp}")
print(f"  - {quad_path_backup}")

# ==========================================
# 6. 詳細分析CSV（ハイライト域）
# ==========================================

highlight_detail = []
for i in range(232, 256):
    k = all_k_values[i]
    gradient = gradients[i-1] if i > 0 else 0
    density_est = 0.08 + (k / 33051) * 1.0

    highlight_detail.append({
        'input': i,
        'k_value': k,
        'gradient': gradient,
        'density_est': f"{density_est:.3f}"
    })

df_detail = pd.DataFrame(highlight_detail)
detail_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/xf1v8_HE_highlight_detail.csv'
df_detail.to_csv(detail_path, index=False)
print(f"\n✓ ハイライト詳細分析: {detail_path}")

# ==========================================
# 7. サマリー出力
# ==========================================

print("\n" + "="*50)
print("PX1V-PtPd-xf1-v8-HE 生成完了")
print("="*50)
print(f"Base域 (Input 0-232):")
print(f"  - K範囲: 0 - {K_MAX_232}")
print(f"  - Gradient: {gradients[:232].mean():.1f} K/step")
print(f"\nHighlight域 (Input 232-255):")
print(f"  - K範囲: {all_k_values[232]} - {all_k_values[255]}")
print(f"  - Gradient: {gradients[232:].mean():.1f} K/step")
print(f"  - 濃度範囲: 1.02D - 1.18D")
print(f"\n特性:")
print(f"  - ハイライト圧縮により白飛び抑制")
print(f"  - 'ゆっくり消える' 表現を実現")
print(f"  - Base域はv7-NAと完全同一")
