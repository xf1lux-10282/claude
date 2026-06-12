#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v21 QTRカーブ生成
K単色カーブ（理想濃度差から計算されたK値、33ポイント）

設計コンセプト:
- K値: 理想濃度差（0.02-0.05）から逆算
- 0.01の濃度差 = K値差約220
- Input 8 (K=2520) を基準に計算
- 均等な濃度差: シャドウ/ハイライト 0.02-0.03、中間調 0.05
- 露光時間: 6分45秒（v16/v18/v20と同じ条件で検証）
- GY/LGY: 使用しない（K単色）
- cubic補間で256ポイントに拡張

期待される効果:
- 予測可能で均一な階調変化
- v18/v20の実測データに基づく信頼性の高い設計
- 濃度差が理想通りに制御される

Generated: 2026-04-03
"""
import numpy as np
from scipy import interpolate
import csv

print("=" * 80)
print("v21 K単色カーブ生成開始")
print("理想濃度差から計算されたK値（6分45秒露光対応）")
print("=" * 80)

# ===== v21のK値（33ポイント） =====
print("\n[Step 1] 理想濃度差から計算されたK値を読み込み")

# K値（理想濃度差から計算）- 33個（Input 0, 8-240を8ステップ, 248, 255）
# 0.01の濃度差 = K値差約220
# Input 8 (K=2520) を基準に計算
specified_k_values = [
    0, 2520, 2960, 3400, 4060, 4500, 5160, 6040, 7140, 8240, 9340,
    10440, 11540, 12640, 13740, 14840, 15940, 17040, 18140, 19240, 20340, 21440,
    22540, 23640, 24740, 25840, 26940, 27820, 28480, 29140, 29800, 30460, 31120
]

# Input値: 0, 8-240を8ステップ, 248, 255（33ポイント）
specified_inputs = [0] + list(range(8, 241, 8)) + [248, 255]

print(f"✓ 指定ポイント数: {len(specified_inputs)} points")
print(f"  Input範囲: {specified_inputs[0]}-{specified_inputs[-1]}")
print(f"  K値範囲: {specified_k_values[0]}-{specified_k_values[-1]}")

# v18/v20との主要差分を表示
v18_k_values = [
    0, 2400, 3372, 4864, 5264, 6197, 7531, 9031, 9864, 10864, 11364,
    11864, 12489, 13364, 14293, 15007, 15721, 16435, 17086, 17642, 18614, 19664,
    20531, 21364, 22531, 23364, 23864, 24864, 25499, 26264, 27128, 28304, 29752
]

v20_k_values = [
    0, 2400, 3048, 4118, 5131, 6197, 7086, 7864, 8698, 9864, 10697,
    11364, 12333, 13364, 13945, 15096, 15542, 16149, 16923, 17885, 18847, 19431,
    20531, 21531, 22198, 23364, 24614, 25287, 26264, 27128, 28304, 29028, 29752
]

print(f"\n【v18/v20からの主要変更】")
print("Input | v18_K | v20_K | v21_K | v21-v18 | v21-v20")
print("------|-------|-------|-------|---------|--------")
for i in [0, 8, 16, 48, 72, 96, 128, 160, 192, 216, 240, 248, 255]:
    idx = int(i / 8) if i <= 240 else (31 if i == 248 else 32)
    inp = specified_inputs[idx]
    v18_k = v18_k_values[idx]
    v20_k = v20_k_values[idx]
    v21_k = specified_k_values[idx]
    print(f"{inp:5} | {v18_k:5} | {v20_k:5} | {v21_k:5} | {v21_k-v18_k:+7} | {v21_k-v20_k:+7}")

# ===== 256ポイントに補間 =====
print("\n[Step 2] 256ポイントに補間（cubic）")

f_interp = interpolate.interp1d(
    specified_inputs,
    specified_k_values,
    kind='cubic',
    fill_value='extrapolate'
)

all_inputs = np.arange(256)
k_values_float = f_interp(all_inputs)
k_values = [round(float(k)) for k in k_values_float]

print(f"✓ 補間完了: {len(k_values)} values")
print(f"  K[0] = {k_values[0]}")
print(f"  K[128] = {k_values[128]}")
print(f"  K[255] = {k_values[255]}")

# ===== 単調増加を保証 =====
print("\n[Step 3] 単調増加を保証")

violations = 0
for i in range(1, 256):
    if k_values[i] <= k_values[i-1]:
        violations += 1
        k_values[i] = k_values[i-1] + 1

if violations == 0:
    print("✓ 単調増加保証: 完璧（修正不要）")
else:
    print(f"✓ 単調増加保証: {violations}箇所を修正")

# ===== .quadファイル生成 =====
print("\n[Step 4] Quadファイルを生成中...")

quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v21
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Calculated from ideal density steps (0.02-0.05)
# - K only (no GY/LGY)
# - 0.01 density step = ~220 K value increment
# - Based on Input 8 (K=2520) as reference
# - Target: uniform, predictable gradation
# - Exposure: 6:45 (same as v16/v18/v20 for validation)
# Generated: 2026-04-03 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# Ideal density step implementation
#
# K curve
"""

for k in k_values:
    quad_content += f"{k}\n"

quad_content += "#\n"

# 残り9チャンネル（全て0）
for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# 保存
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v21.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v21カーブ生成完了: {output_path}")

# ===== ファイル整合性確認 =====
print(f"\n[Step 5] ファイル整合性確認")
import os
file_size = os.path.getsize(output_path)
with open(output_path, 'r') as f:
    line_count = len(f.readlines())

print(f"ファイルサイズ: {file_size} bytes")
print(f"総行数: {line_count} 行")

# ===== CSVファイル生成 =====
print(f"\n[Step 6] CSV出力（8ステップ単位）")

csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v21_values.csv'

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Input', 'K_v21', 'K_v18', 'K_v20', 'Diff_v18', 'Diff_v20'])

    for i in range(0, 256, 8):
        k_v21 = k_values[i]
        # v18/v20の値（参考用）
        v18_interp = interpolate.interp1d(specified_inputs, v18_k_values, kind='cubic', fill_value='extrapolate')
        v20_interp = interpolate.interp1d(specified_inputs, v20_k_values, kind='cubic', fill_value='extrapolate')
        k_v18 = round(float(v18_interp(i)))
        k_v20 = round(float(v20_interp(i)))
        diff_v18 = k_v21 - k_v18
        diff_v20 = k_v21 - k_v20
        writer.writerow([i, k_v21, k_v18, k_v20, diff_v18, diff_v20])

    # 255も追加
    k_v21_255 = k_values[255]
    k_v18_255 = round(float(v18_interp(255)))
    k_v20_255 = round(float(v20_interp(255)))
    diff_v18_255 = k_v21_255 - k_v18_255
    diff_v20_255 = k_v21_255 - k_v20_255
    writer.writerow([255, k_v21_255, k_v18_255, k_v20_255, diff_v18_255, diff_v20_255])

print(f"✓ CSV生成完了: {csv_path}")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v21 K単色カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ K値: 理想濃度差から計算した33ポイント（cubic補間で256ポイント化）")
print(f"  ✓ GY/LGY: 使用しない（K単色）")
print(f"  ✓ 濃度差基準: 0.01 = K値差約220")
print(f"  ✓ 基準点: Input 8 (K=2520)")
print(f"  ✓ 理想濃度差: シャドウ/ハイライト 0.02-0.03、中間調 0.05（均一）")
print(f"  ✓ 露光時間: 6分45秒（v16/v18/v20と同じ条件で検証）")
print(f"  ✓ K[0] = {k_values[0]}")
print(f"  ✓ K[128] = {k_values[128]}")
print(f"  ✓ K[255] = {k_values[255]}")
print(f"\n【設計方針】")
print(f"  1. v18/v20の実測データから0.01濃度差=220K差を算出")
print(f"  2. 理想濃度差に基づいて均等な階調変化を実現")
print(f"  3. Input 8を基準に全体を計算")
print(f"  4. 予測可能で制御された濃度差")
print(f"\n【次のステップ】")
print(f"1. v21をQTRにインストール（ルール8準拠）")
print(f"2. 6分45秒露光でテストプリント")
print(f"3. 濃度測定して理想値v3との比較")
print(f"4. 均等な濃度差が実現できているか確認")
print(f"{'=' * 80}")
