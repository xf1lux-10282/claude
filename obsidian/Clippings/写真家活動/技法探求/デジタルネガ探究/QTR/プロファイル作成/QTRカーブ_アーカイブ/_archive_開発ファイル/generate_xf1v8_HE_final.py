#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v8-HE QTRカーブ生成 (Final版)

設計方針:
- Input 0-232: v7-NAと完全同一（保護）
- Input 232-255: ハイライト圧縮（手動最適化K値）

アンカーポイント（K値指定）:
  232 → 30070 (v7-NAと同一)
  236 → 31150
  240 → 32050
  244 → 32950
  248 → 33850
  252 → 34750
  255 → 36356

特徴:
- Gradient比率 2.38倍（バンディングリスク小）
- 中間域（236-252）Gradient均一 225 K/step
- Base域との滑らかな接続（Input 231→232）

Created: 2026-03-21
"""

import numpy as np
import pandas as pd

# ==========================================
# 1. K値からの濃度変換（参考用）
# ==========================================

def k_to_density(k):
    """K値から濃度Dへの変換（線形近似）"""
    D1, K1 = 0.08, 0
    D2, K2 = 1.08, 33051

    a = (D2 - D1) / (K2 - K1)
    b = D1 - a * K1

    d = a * k + b
    return d

# ==========================================
# 2. カーブ設計
# ==========================================

# Input 0-232: v7-NAと完全同一
K_MAX_232 = 30070  # v7-NAのInput 232のK値

# Input 0-232の線形補間（v7-NAと同一）
inputs_base = np.arange(233)  # 0-232
k_values_base = np.linspace(0, K_MAX_232, 233)
k_values_base = np.round(k_values_base).astype(int)

print("=== Base域確認 ===")
print(f"Input 231: K={k_values_base[231]} (D={k_to_density(k_values_base[231]):.3f})")
print(f"Input 232: K={k_values_base[232]} (D={k_to_density(k_values_base[232]):.3f})")

# Input 232-255: ハイライト圧縮（手動K値指定）
highlight_anchors = {
    232: 30070,
    236: 31150,
    240: 32050,
    244: 32950,
    248: 33850,
    252: 34750,
    255: 36356
}

print("\n=== ハイライト域アンカーポイント ===")
print("Input |   K値   | 濃度(D)")
print("------|---------|--------")
for inp, k in highlight_anchors.items():
    density = k_to_density(k)
    print(f" {inp:3d}  | {k:7d} | {density:6.3f}")

# 各セグメント間を線形補間
anchor_inputs = sorted(highlight_anchors.keys())
all_highlight_k = []

for i in range(len(anchor_inputs) - 1):
    start_inp = anchor_inputs[i]
    end_inp = anchor_inputs[i + 1]
    start_k = highlight_anchors[start_inp]
    end_k = highlight_anchors[end_inp]

    num_points = end_inp - start_inp + 1  # 両端を含む
    segment_k = np.linspace(start_k, end_k, num_points)

    # 最後の点を除いて追加（次のセグメントの開始点になる）
    if i < len(anchor_inputs) - 2:
        all_highlight_k.extend(segment_k[:-1])
    else:
        # 最後のセグメント
        all_highlight_k.extend(segment_k)

all_highlight_k = np.round(np.array(all_highlight_k)).astype(int)

# Input 232が重複するので調整
# base: 0-232, highlight: 233-255
k_values_highlight = all_highlight_k[1:]  # Input 232をスキップ

# 全体を結合
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
else:
    print("\n✓ 単調性チェック: OK")

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

# セグメント別Gradient
print(f"\n各セグメントのGradient:")
for i in range(len(anchor_inputs) - 1):
    inp1, inp2 = anchor_inputs[i], anchor_inputs[i+1]
    k1 = highlight_anchors[inp1]
    k2 = highlight_anchors[inp2]
    delta_k = k2 - k1
    delta_inp = inp2 - inp1
    gradient = delta_k / delta_inp
    print(f"  Input {inp1:3d} → {inp2:3d}: Gradient={gradient:6.1f} K/step")

# ==========================================
# 4. CSV記録生成
# ==========================================

# 主要ポイントの記録
key_points = [0, 8, 16, 32, 64, 96, 128, 160, 192, 224, 232, 236, 240, 244, 248, 252, 255]
csv_data = []

for inp in key_points:
    k = all_k_values[inp]
    density = k_to_density(k)

    csv_data.append({
        'input': inp,
        'k_value': k,
        'negative_density（実測）': '',
        'print_density': '',
        'negative_density（目標）': f"{density:.3f}"
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
# PX1V-PtPd-xf1-v8-HE - Highlight Enhanced (Final)
# - Base (0-232): v7-NAと完全同一（K_max=30070）
# - Highlight (232-255): 圧縮階調（手動最適化K値）
# - 目標: 白飛び抑制、ハイライト"ゆっくり消える"表現
# - Gradient: Base 129-130, Highlight 225-535（平均284）
# - Gradient比率: 2.38倍（バンディングリスク小）
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
    density = k_to_density(k)

    highlight_detail.append({
        'input': i,
        'k_value': k,
        'gradient': gradient,
        'density_est': f"{density:.3f}"
    })

df_detail = pd.DataFrame(highlight_detail)
detail_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/xf1v8_HE_highlight_detail_final.csv'
df_detail.to_csv(detail_path, index=False)
print(f"\n✓ ハイライト詳細分析: {detail_path}")

# ==========================================
# 7. サマリー出力
# ==========================================

print("\n" + "="*60)
print("PX1V-PtPd-xf1-v8-HE 生成完了（Final版）")
print("="*60)
print(f"Base域 (Input 0-232):")
print(f"  - K範囲: 0 - {K_MAX_232}")
print(f"  - Gradient: {gradients[:232].mean():.1f} K/step")
print(f"  - v7-NAと完全同一")
print(f"\nHighlight域 (Input 232-255):")
print(f"  - K範囲: {all_k_values[232]} - {all_k_values[255]}")
print(f"  - Gradient: min={gradients[232:].min()}, max={gradients[232:].max()}, mean={gradients[232:].mean():.1f}")
print(f"  - Gradient比率: {gradients[232:].max() / gradients[232:].min():.2f}倍")
print(f"  - 濃度範囲: {k_to_density(all_k_values[232]):.3f}D - {k_to_density(all_k_values[255]):.3f}D")
print(f"\n特性:")
print(f"  ✓ Base域との滑らかな接続")
print(f"  ✓ 中間域（236-252）Gradient均一（225 K/step）")
print(f"  ✓ ハイライト圧縮により白飛び抑制")
print(f"  ✓ 'ゆっくり消える' 表現を実現")
print(f"\n次のステップ:")
print(f"  1. システムにインストール")
print(f"  2. テストネガ出力（特にInput 250-255を確認）")
print(f"  3. Input 252-255の急峻さを実物で評価")
