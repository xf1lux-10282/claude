#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v8-HE QTRカーブ生成 (v3 - 完全線形補間版)

設計方針:
- Input 0-231: v7-NAと同一（完全保護）
- Input 232-255: ハイライト圧縮（指定濃度で線形補間）

目標濃度（アンカーポイント）:
  232 → 1.02D
  236 → 1.04D
  240 → 1.06D
  244 → 1.08D
  248 → 1.10D
  252 → 1.12D
  255 → 1.18D

改善点:
- 各セグメント間を完全線形補間
- Gradientの均一性を最優先

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
    線形近似: K = a * D + b
    """
    D1, K1 = 0.08, 0
    D2, K2 = 1.08, 33051

    a = (K2 - K1) / (D2 - D1)
    b = K1 - a * D1

    k = a * density + b
    return k

# ==========================================
# 2. ハイライト強化版カーブ設計
# ==========================================

# Input 0-231: v7-NAと同一
K_MAX_231 = 29941  # v7-NAのInput 231のK値（計算）

# Input 0-231の線形補間（v7-NAと同一）
inputs_base = np.arange(232)  # 0-231
k_values_base = np.linspace(0, K_MAX_231, 232)
k_values_base = np.round(k_values_base).astype(int)

print("=== Base域確認 ===")
print(f"Input 231: K={k_values_base[231]}")

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

print("\n=== ハイライト域アンカーポイント ===")
for inp, density in highlight_anchors.items():
    k = density_to_k(density)
    print(f"Input {inp:3d}: D={density:.2f} → K={k:7.1f}")

# 各セグメント間を線形補間
all_highlight_k = []

for i in range(len(anchor_inputs) - 1):
    start_inp = anchor_inputs[i]
    end_inp = anchor_inputs[i + 1]
    start_k = anchor_k_values[i]
    end_k = anchor_k_values[i + 1]

    num_points = end_inp - start_inp + 1  # 両端を含む
    segment_k = np.linspace(start_k, end_k, num_points)

    # 最後の点を除いて追加（次のセグメントの開始点になる）
    if i < len(anchor_inputs) - 2:
        all_highlight_k.extend(segment_k[:-1])
    else:
        # 最後のセグメント
        all_highlight_k.extend(segment_k)

all_highlight_k = np.round(np.array(all_highlight_k)).astype(int)

# Input 232からの相対位置を確認
print(f"\nHighlight K値の数: {len(all_highlight_k)} (期待値: 24 = 255-232+1)")

# 全体を結合
all_k_values = np.concatenate([k_values_base, all_highlight_k])

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
print(f"Base域 (0-231): min={gradients[:231].min()}, max={gradients[:231].max()}, mean={gradients[:231].mean():.1f}")
print(f"Highlight域 (231-255): min={gradients[231:].min()}, max={gradients[231:].max()}, mean={gradients[231:].mean():.1f}")

# Gradient分布の確認
print(f"\nHighlight域のGradient分布:")
unique_gradients, counts = np.unique(gradients[231:], return_counts=True)
for g, c in zip(unique_gradients, counts):
    print(f"  Gradient {g:3d}: {c:2d}回")

# Input 231-233の接続を確認
print(f"\n=== 接続点の確認 ===")
for i in range(230, 234):
    if i < 255:
        print(f"Input {i} → {i+1}: K {all_k_values[i]:5d} → {all_k_values[i+1]:5d} (Δ={gradients[i]:4d})")

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
# - Base (0-231): v7-NAと同一（K_max=29941）
# - Highlight (232-255): 圧縮階調（完全線形補間）
# - 目標: 白飛び抑制、ハイライト情報量増加
# - Gradient: Base 129-130, Highlight 各セグメント均一
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
for i in range(231, 256):
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
print("PX1V-PtPd-xf1-v8-HE 生成完了（v3 - 完全線形補間版）")
print("="*50)
print(f"Base域 (Input 0-231):")
print(f"  - K範囲: 0 - {K_MAX_231}")
print(f"  - Gradient: {gradients[:231].mean():.1f} K/step")
print(f"\nHighlight域 (Input 232-255):")
print(f"  - K範囲: {all_k_values[232]} - {all_k_values[255]}")
print(f"  - Gradient: min={gradients[231:].min()}, max={gradients[231:].max()}, mean={gradients[231:].mean():.1f}")
print(f"  - 濃度範囲: 1.02D - 1.18D")
print(f"\n特性:")
print(f"  - 完全線形補間で各セグメント均一Gradient")
print(f"  - ハイライト圧縮により白飛び抑制")
print(f"  - 'ゆっくり消える' 表現を実現")
print(f"  - Base域(0-231)はv7-NAと完全同一")
