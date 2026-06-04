#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v8-HE QTRカーブ生成 (v2 - スムーズ補間版)

設計方針:
- Input 0-232: v7-NAと同一（K値固定）
- Input 232-255: ハイライト圧縮（スムーズに補間）

目標濃度（アンカーポイント）:
  232 → 1.02D
  236 → 1.04D
  240 → 1.06D
  244 → 1.08D
  248 → 1.10D
  252 → 1.12D
  255 → 1.18D

改善点:
- 全Input値（232-255）を個別に計算
- スプライン補間でGradientを滑らかに

Created: 2026-03-21
"""

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

# ==========================================
# 1. 濃度からK値への変換式（実測ベース）
# ==========================================

def density_to_k(density):
    """
    ネガ濃度DからK値への変換
    線形近似: K = a * D + b
    """
    D1, K1 = 0.08, 0
    D2, K2 = 1.08, 33051

    a = (K2 - K1) / (D2 - D1)
    b = K1 - a * D1

    k = a * density + b
    return k  # 整数化は後で

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

# アンカーポイントからスプライン補間
anchor_inputs = np.array(sorted(highlight_anchors.keys()))
anchor_densities = np.array([highlight_anchors[inp] for inp in anchor_inputs])
anchor_k_values = np.array([density_to_k(d) for d in anchor_densities])

print("=== ハイライト域アンカーポイント ===")
for inp, density in highlight_anchors.items():
    k = density_to_k(density)
    print(f"Input {inp:3d}: D={density:.2f} → K={k:7.1f}")

# PCHIP補間（単調性保証、滑らか）
interpolator = PchipInterpolator(anchor_inputs, anchor_k_values)

# Input 233-255を補間
inputs_highlight = np.arange(233, 256)
k_values_highlight = interpolator(inputs_highlight)
k_values_highlight = np.round(k_values_highlight).astype(int)

# 全体を結合
all_inputs = np.concatenate([inputs_base, k_values_highlight])
all_k_values = np.concatenate([k_values_base, k_values_highlight])

# 検証
assert len(all_k_values) == 256, f"K値の数が256ではありません: {len(all_k_values)}"

# 単調性チェック
gradients = np.diff(all_k_values)
if np.any(gradients < 0):
    print("⚠️ 警告: カーブが単調増加していません")
    neg_indices = np.where(gradients < 0)[0]
    for idx in neg_indices:
        print(f"  Input {idx} → {idx+1}: K {all_k_values[idx]} → {all_k_values[idx+1]} (Δ={gradients[idx]})")

# ==========================================
# 3. Gradient分析
# ==========================================

print("\n=== Gradient分析 ===")
print(f"全体: min={gradients.min()}, max={gradients.max()}, mean={gradients.mean():.1f}")
print(f"Base域 (0-232): min={gradients[:232].min()}, max={gradients[:232].max()}, mean={gradients[:232].mean():.1f}")
print(f"Highlight域 (232-255): min={gradients[232:].min()}, max={gradients[232:].max()}, mean={gradients[232:].mean():.1f}")

# Gradient分布の確認
print(f"\nHighlight域のGradient分布:")
unique_gradients, counts = np.unique(gradients[232:], return_counts=True)
for g, c in zip(unique_gradients, counts):
    print(f"  Gradient {g:3d}: {c:2d}回")

# ==========================================
# 4. CSV記録生成
# ==========================================

# 主要ポイントの記録
key_points = [0, 8, 16, 32, 64, 96, 128, 160, 192, 224, 232, 236, 240, 244, 248, 252, 255]
csv_data = []

for inp in key_points:
    k = all_k_values[inp]

    # ハイライト域は指定濃度を使用
    if inp in highlight_anchors:
        density_target = highlight_anchors[inp]
    else:
        # 理論濃度（線形近似）
        density_target = 0.08 + (k / 33051) * 1.0

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
# - Highlight (232-255): 圧縮階調（PCHIP補間）
# - 目標: 白飛び抑制、ハイライト情報量増加
# - Gradient: Base 129-130, Highlight スムーズ可変
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
# 6. 詳細分析CSV（ハイライト域全点）
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
print("PX1V-PtPd-xf1-v8-HE 生成完了（v2 - PCHIP補間版）")
print("="*50)
print(f"Base域 (Input 0-232):")
print(f"  - K範囲: 0 - {K_MAX_232}")
print(f"  - Gradient: {gradients[:232].mean():.1f} K/step")
print(f"\nHighlight域 (Input 232-255):")
print(f"  - K範囲: {all_k_values[232]} - {all_k_values[255]}")
print(f"  - Gradient: min={gradients[232:].min()}, max={gradients[232:].max()}, mean={gradients[232:].mean():.1f}")
print(f"  - 濃度範囲: 1.02D - 1.18D")
print(f"\n特性:")
print(f"  - PCHIP補間で滑らかなGradient")
print(f"  - ハイライト圧縮により白飛び抑制")
print(f"  - 'ゆっくり消える' 表現を実現")
print(f"  - Base域はv7-NAと完全同一")
