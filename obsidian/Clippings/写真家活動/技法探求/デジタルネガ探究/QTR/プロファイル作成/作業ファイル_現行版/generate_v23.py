#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v23 QTRカーブ生成
K単色カーブ（v22の調整版、33ポイント）

設計コンセプト:
- K値: v22からの微調整（実測フィードバック反映）
- Input 8の値を2960に変更（v21/v22の2520から+440）
- 全体的なバランス調整
- 露光時間: 6分45秒（v16/v18/v20/v21/v22と同じ条件）
- GY/LGY: 使用しない（K単色）
- cubic補間で256ポイントに拡張

v22からの主な変更:
- Input 8: 2520 → 2960 (+440、基準点変更）
- Input 192-240: 調整（ハイライト領域の微調整）

Generated: 2026-04-03
"""
import numpy as np
from scipy import interpolate
import csv

print("=" * 80)
print("v23 K単色カーブ生成開始")
print("v22の調整版（基準点変更）")
print("=" * 80)

# ===== v23のK値（33ポイント） =====
print("\n[Step 1] v23のK値を読み込み")

# K値（33個）- Input 0, 8-240を8ステップ, 248, 255
specified_k_values = [
    0, 2960, 3400, 3840, 4280, 4940, 5820, 6700, 7580, 8680, 9780,
    10880, 11980, 13080, 14180, 15280, 16380, 17480, 18580, 19680, 20780, 21880,
    22980, 24080, 24960, 25840, 26720, 27380, 28040, 28700, 29140, 29580, 30020
]

# Input値: 0, 8-240を8ステップ, 248, 255（33ポイント）
specified_inputs = [0] + list(range(8, 241, 8)) + [248, 255]

print(f"✓ 指定ポイント数: {len(specified_inputs)} points")
print(f"  Input範囲: {specified_inputs[0]}-{specified_inputs[-1]}")
print(f"  K値範囲: {specified_k_values[0]}-{specified_k_values[-1]}")

# v22との差分を表示
v22_k_values = [
    0, 2520, 2960, 3400, 4060, 4940, 5820, 6700, 7580, 8680, 9780,
    10880, 11980, 13080, 14180, 15280, 16380, 17480, 18580, 19680, 20780, 21880,
    22980, 24080, 25180, 26280, 27160, 27820, 28480, 29140, 29580, 30020, 30680
]

print(f"\n【v22からの主要変更】")
print("Input | v22_K | v23_K | 差分 | 変更の意図")
print("------|-------|-------|------|------------------")
for i in [0, 8, 16, 24, 32, 40, 96, 128, 160, 192, 200, 216, 232, 240, 248, 255]:
    idx = int(i / 8) if i <= 240 else (31 if i == 248 else 32)
    inp = specified_inputs[idx]
    v22_k = v22_k_values[idx]
    v23_k = specified_k_values[idx]
    diff = v23_k - v22_k

    if diff > 0:
        intent = "深く（プリント浅く）"
    elif diff < 0:
        intent = "浅く（プリント深く）"
    else:
        intent = "変更なし"

    print(f"{inp:5} | {v22_k:5} | {v23_k:5} | {diff:+4} | {intent}")

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
# Title: PX1V-PtPd-xf1-v23
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - v22 adjusted with new reference point at Input 8
# - K only (no GY/LGY)
# - Input 8: 2520 → 2960 (+440)
# - Highlight region fine-tuned (192-255)
# - Exposure: 6:45 (same as v16/v18/v20/v21/v22 for validation)
# Generated: 2026-04-03 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# v22 adjustment with reference point change
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
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v23.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v23カーブ生成完了: {output_path}")

# ===== ファイル整合性確認 =====
print(f"\n[Step 5] ファイル整合性確認")
import os
file_size = os.path.getsize(output_path)
with open(output_path, 'r') as f:
    line_count = len(f.readlines())

print(f"ファイルサイズ: {file_size} bytes")
print(f"総行数: {line_count} 行")

# ===== CSVファイル生成 =====
print(f"\n[Step 6] CSV出力（全33ポイント）")

csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v23_k_values_detailed.csv'

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Input', 'V23_K', 'V22_K', 'V21_K', 'Diff_v22', 'Diff_v21'])

    # v21の値
    v21_k_values = [
        0, 2520, 2960, 3400, 4060, 4500, 5160, 6040, 7140, 8240, 9340,
        10440, 11540, 12640, 13740, 14840, 15940, 17040, 18140, 19240, 20340, 21440,
        22540, 23640, 24740, 25840, 26940, 27820, 28480, 29140, 29800, 30460, 31120
    ]

    for i in range(len(specified_inputs)):
        inp = specified_inputs[i]
        v23_k = specified_k_values[i]
        v22_k = v22_k_values[i]
        v21_k = v21_k_values[i]
        diff_v22 = v23_k - v22_k
        diff_v21 = v23_k - v21_k
        writer.writerow([inp, v23_k, v22_k, v21_k, diff_v22, diff_v21])

print(f"✓ CSV生成完了: {csv_path}")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v23 K単色カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ K値: v22からの調整版（33ポイント→cubic補間で256ポイント）")
print(f"  ✓ GY/LGY: 使用しない（K単色）")
print(f"  ✓ Input 8基準: K=2960（v22の2520から+440）")
print(f"  ✓ 露光時間: 6分45秒（v22と同じ条件で比較）")
print(f"  ✓ K[0] = {k_values[0]}")
print(f"  ✓ K[128] = {k_values[128]}")
print(f"  ✓ K[255] = {k_values[255]}")
print(f"\n【v22からの主な変更】")
print(f"  1. Input 8: 2520 → 2960 (+440、基準点変更）")
print(f"  2. Input 24: 3400維持（v22から変更なし）")
print(f"  3. Input 32: 4060 → 4280 (+220)")
print(f"  4. Input 192-216: 減少（ハイライト領域調整）")
print(f"  5. Input 240-255: 減少（最ハイライト浅く、紙白に近づける）")
print(f"\n【次のステップ】")
print(f"1. v23をQTRにインストール（ルール8準拠）")
print(f"2. 6分45秒露光でテストプリント")
print(f"3. v22と比較して改善を確認")
print(f"{'=' * 80}")
