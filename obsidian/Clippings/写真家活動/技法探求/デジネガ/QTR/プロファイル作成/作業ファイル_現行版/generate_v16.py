#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v16 QTRカーブ生成
K単色カーブ（ユーザー指定33ポイント値）

設計コンセプト:
- K値: ユーザー指定の33ポイント値（Input 0, 8-240を8ステップ, 248, 255）
- GY/LGY: 使用しない（K単色）
- cubic補間で256ポイントに拡張

Generated: 2026-04-02
"""
import numpy as np
from scipy import interpolate
import csv

print("=" * 80)
print("v16 K単色カーブ生成開始")
print("=" * 80)

# ===== ユーザー指定のK値（33ポイント） =====
print("\n[Step 1] ユーザー指定のK値を読み込み")

# K値（ユーザー指定）- 33個（Input 0, 8-240を8ステップ, 248, 255）
specified_k_values = [
    0, 960, 1920, 2880, 3864, 4864, 5864, 6864, 7864, 8864, 9864,
    10864, 11864, 12864, 13864, 14864, 15864, 16864, 17864, 18864, 19864,
    20864, 21864, 22864, 23864, 24864, 25816, 26712, 27544, 28304, 29064, 29752, 30440
]

# Input値: 0, 8-240を8ステップ, 248, 255（33ポイント）
specified_inputs = [0] + list(range(8, 241, 8)) + [248, 255]

print(f"✓ 指定ポイント数: {len(specified_inputs)} points")
print(f"  Input範囲: {specified_inputs[0]}-{specified_inputs[-1]}")
print(f"  K値範囲: {specified_k_values[0]}-{specified_k_values[-1]}")

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
# Title: PX1V-PtPd-xf1-v16
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - User-specified K values (32 points, cubic interpolation)
# - K only (no GY/LGY)
# - Exposure: TBD
# Generated: 2026-04-02 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
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
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v16.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v16カーブ生成完了: {output_path}")

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

csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v16_values.csv'

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Input', 'K'])

    for i in range(0, 256, 8):
        k = k_values[i]
        writer.writerow([i, k])

print(f"✓ CSV生成完了: {csv_path}")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v16 K単色カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ K値: ユーザー指定33ポイント（cubic補間で256ポイント化）")
print(f"  ✓ GY/LGY: 使用しない（K単色）")
print(f"  ✓ K[0] = {k_values[0]}")
print(f"  ✓ K[128] = {k_values[128]}")
print(f"  ✓ K[255] = {k_values[255]}")
print(f"\n【次のステップ】")
print(f"1. v16-multiinkカーブを生成")
print(f"2. 両カーブをQTRにインストール（ルール8準拠）")
print(f"3. テストプリントで比較")
print(f"{'=' * 80}")
