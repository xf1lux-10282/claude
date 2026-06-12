#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v18 QTRカーブ生成
K単色カーブ（理想濃度から逆算、33ポイント値）

設計コンセプト:
- K値: v16実測データから理想濃度カーブを逆算した33ポイント値
- 理想濃度: 等間隔的な階調変化を目指す（1.38→0.13）
- 露光時間: 6分45秒（v16と同じ条件で検証）
- GY/LGY: 使用しない（K単色）
- cubic補間で256ポイントに拡張

期待される効果:
- シャドウ分離の改善（Input 0-8）
- ハイライト階調の拡張（Input 240-255）
- より線形に近い階調変化

Generated: 2026-04-03
"""
import numpy as np
from scipy import interpolate
import csv

print("=" * 80)
print("v18 K単色カーブ生成開始")
print("理想濃度から逆算（6分45秒露光対応）")
print("=" * 80)

# ===== ユーザー指定のK値（33ポイント） =====
print("\n[Step 1] 理想濃度から逆算したK値を読み込み")

# K値（理想濃度から逆算）- 33個（Input 0, 8-240を8ステップ, 248, 255）
# v16実測データから理想濃度カーブを実現するために必要なK値
specified_k_values = [
    0, 2400, 3372, 4864, 5264, 6197, 7531, 9031, 9864, 10864, 11364,
    11864, 12489, 13364, 14293, 15007, 15721, 16435, 17086, 17642, 18614, 19664,
    20531, 21364, 22531, 23364, 23864, 24864, 25499, 26264, 27128, 28304, 29752
]

# Input値: 0, 8-240を8ステップ, 248, 255（33ポイント）
specified_inputs = [0] + list(range(8, 241, 8)) + [248, 255]

print(f"✓ 指定ポイント数: {len(specified_inputs)} points")
print(f"  Input範囲: {specified_inputs[0]}-{specified_inputs[-1]}")
print(f"  K値範囲: {specified_k_values[0]}-{specified_k_values[-1]}")

# v16との主要差分を表示
print(f"\n【v16からの主要変更】")
print(f"  Input 8:  960 → {specified_k_values[1]} (+{specified_k_values[1]-960})")
print(f"  Input 128: 15864 → {specified_k_values[16]} ({specified_k_values[16]-15864:+d})")
print(f"  Input 240: 29064 → {specified_k_values[29]} ({specified_k_values[29]-29064:+d})")

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
# Title: PX1V-PtPd-xf1-v18
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Ideal density curve (reverse-calculated from v16 measurements)
# - K only (no GY/LGY)
# - Target: linear-like gradation (1.38→0.13)
# - Exposure: 6:45 (same as v16 for validation)
# Generated: 2026-04-03 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# Ideal density target implementation
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
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v18.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v18カーブ生成完了: {output_path}")

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

csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v18_values.csv'

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
print(f"v18 K単色カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ K値: 理想濃度から逆算した33ポイント（cubic補間で256ポイント化）")
print(f"  ✓ GY/LGY: 使用しない（K単色）")
print(f"  ✓ 理想濃度: 等間隔的な階調変化（1.38→0.13）")
print(f"  ✓ 露光時間: 6分45秒（v16と同じ条件で検証）")
print(f"  ✓ K[0] = {k_values[0]}")
print(f"  ✓ K[128] = {k_values[128]}")
print(f"  ✓ K[255] = {k_values[255]}")
print(f"\n【次のステップ】")
print(f"1. v18をQTRにインストール（ルール8準拠）")
print(f"2. 6分45秒露光でテストプリント")
print(f"3. 濃度測定と理想値との比較")
print(f"4. 理想濃度に近づいていれば成功")
print(f"5. 必要に応じてv19で微調整")
print(f"{'=' * 80}")
