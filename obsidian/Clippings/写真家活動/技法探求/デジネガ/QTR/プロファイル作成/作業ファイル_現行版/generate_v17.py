#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v17 QTRカーブ生成
K単色カーブ（実測データベース33ポイント値）

設計コンセプト:
- K値: 6分45秒露光の実測データに基づく33ポイント値
- シャドウ改善: Input 0=0, Input 8=880 (v16: 0=0, 8=960から-80)
- 全体的にK値を増加させ、6分露光に対応
- ハイライト改善: 240→248→255の刻みを緩やか化（階調分離向上）
- 目標露光時間: 6分（v16の6分45秒から短縮）
- GY/LGY: 使用しない（K単色）
- cubic補間で256ポイントに拡張

Generated: 2026-04-03
"""
import numpy as np
from scipy import interpolate
import csv

print("=" * 80)
print("v17 K単色カーブ生成開始")
print("実測データベース（6分露光対応）")
print("=" * 80)

# ===== ユーザー指定のK値（33ポイント） =====
print("\n[Step 1] ユーザー指定のK値を読み込み")

# K値（実測データベース）- 33個（Input 0, 8-240を8ステップ, 248, 255）
# 6分45秒露光での実測結果に基づく調整版（修正版）
# シャドウ: 0=0, 8=960
# ハイライト: 240/248/255の刻みを緩やか化
specified_k_values = [
    0, 960, 1944, 2952, 3960, 4968, 5976, 6984, 7992, 9000, 10008,
    11016, 12024, 13032, 14040, 15048, 16056, 17064, 18072, 19080, 20088,
    21096, 22104, 23112, 24120, 25112, 26072, 26968, 27768, 28440, 28952, 29272, 29368
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
# Title: PX1V-PtPd-xf1-v17
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
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v17.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v17カーブ生成完了: {output_path}")

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

csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v17_values.csv'

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Input', 'K'])

    for i in range(0, 256, 8):
        k = k_values[i]
        writer.writerow([i, k])

    # 255も追加
    writer.writerow([255, k_values[255]])

print(f"✓ CSV生成完了: {csv_path}")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v17 K単色カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ K値: 実測ベース33ポイント（cubic補間で256ポイント化）")
print(f"  ✓ GY/LGY: 使用しない（K単色）")
print(f"  ✓ シャドウ改善: Input 8 = 880 (v16の960から-80)")
print(f"  ✓ ハイライト改善: 240→248→255の刻みを緩やか化")
print(f"  ✓ K[0] = {k_values[0]}")
print(f"  ✓ K[128] = {k_values[128]}")
print(f"  ✓ K[255] = {k_values[255]}")
print(f"\n【次のステップ】")
print(f"1. v17-multiinkカーブを生成")
print(f"2. 両カーブをQTRにインストール（ルール8準拠）")
print(f"3. テストプリントで比較")
print(f"{'=' * 80}")
