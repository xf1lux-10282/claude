#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v19 QTRカーブ生成
K単色カーブ（v18実測結果からの微調整版、33ポイント値）

設計コンセプト:
- K値: v18実測結果に基づき、急な勾配部分を圧縮
- 調整箇所:
  1. Input 48, 56: 暗部上部の急な落ち込みを緩和
  2. Input 112, 128: 中間部のムラを均一化
  3. Input 168, 192: ハイライト寄りの段差を圧縮
  4. Input 255: 最終端の抜けすぎを修正
- 露光時間: 6分45秒（v16/v18と同じ）
- GY/LGY: 使用しない（K単色）
- cubic補間で256ポイントに拡張

Generated: 2026-04-03
"""
import numpy as np
from scipy import interpolate
import csv

print("=" * 80)
print("v19 K単色カーブ生成開始")
print("v18実測結果からの微調整版（6分45秒露光対応）")
print("=" * 80)

# ===== v18のK値（33ポイント） =====
v18_k_values = [
    0, 2400, 3372, 4864, 5264, 6197, 7531, 9031, 9864, 10864, 11364,
    11864, 12489, 13364, 14293, 15007, 15721, 16435, 17086, 17642, 18614, 19664,
    20531, 21364, 22531, 23364, 23864, 24864, 25499, 26264, 27128, 28304, 29752
]

# ===== v19のK値（調整版） =====
print("\n[Step 1] v18からの調整を適用")

# v18をベースに、問題箇所のみ調整
v19_k_values = v18_k_values.copy()

# 調整内容
adjustments = {
    6: -200,   # Input 48: 急な落ち込みを緩和 (7531 → 7331)
    7: -400,   # Input 56: 急な落ち込みを緩和 (9031 → 8631)
    14: +200,  # Input 112: ムラを均一化 (14293 → 14493)
    16: +150,  # Input 128: ムラを均一化 (15721 → 15871)
    21: -300,  # Input 168: 段差を圧縮 (19664 → 19364)
    24: -400,  # Input 192: 段差を圧縮 (22531 → 22131)
    32: -500   # Input 255: 紙白への到達を改善 (29752 → 29252)
}

print("\n調整内容:")
input_indices = [0] + list(range(8, 241, 8)) + [248, 255]
for idx, delta in adjustments.items():
    inp = input_indices[idx]
    old_k = v18_k_values[idx]
    new_k = old_k + delta
    v19_k_values[idx] = new_k
    print(f"  Input {inp:3}: {old_k:5} → {new_k:5} ({delta:+5})")

specified_k_values = v19_k_values
specified_inputs = input_indices

print(f"\n✓ v19 K値決定: {len(specified_k_values)} points")
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
# Title: PX1V-PtPd-xf1-v19
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - v18 measured results fine-tuning
# - K only (no GY/LGY)
# - Gradient compression in problem areas
# - Exposure: 6:45 (same as v16/v18)
# Generated: 2026-04-03 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# v18 gradient refinement
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
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v19.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v19カーブ生成完了: {output_path}")

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

csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v19_values.csv'

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Input', 'K_v19', 'K_v18', 'Diff'])

    for i in range(0, 256, 8):
        k_v19 = k_values[i]
        # v18の値（参考用）
        v18_interp = interpolate.interp1d(specified_inputs, v18_k_values, kind='cubic', fill_value='extrapolate')
        k_v18 = round(float(v18_interp(i)))
        diff = k_v19 - k_v18
        writer.writerow([i, k_v19, k_v18, diff])

    # 255も追加
    k_v19_255 = k_values[255]
    k_v18_255 = round(float(v18_interp(255)))
    diff_255 = k_v19_255 - k_v18_255
    writer.writerow([255, k_v19_255, k_v18_255, diff_255])

print(f"✓ CSV生成完了: {csv_path}")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v19 K単色カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ K値: v18実測結果から7箇所を微調整")
print(f"  ✓ GY/LGY: 使用しない（K単色）")
print(f"  ✓ 露光時間: 6分45秒（v16/v18と同じ）")
print(f"  ✓ K[0] = {k_values[0]}")
print(f"  ✓ K[128] = {k_values[128]}")
print(f"  ✓ K[255] = {k_values[255]}")
print(f"\n【調整内容】")
print(f"  1. Input 48-56: 急な勾配を緩和 (-200, -400)")
print(f"  2. Input 112-128: ムラを均一化 (+200, +150)")
print(f"  3. Input 168-192: ハイライト段差を圧縮 (-300, -400)")
print(f"  4. Input 255: 紙白到達を改善 (-500)")
print(f"\n【次のステップ】")
print(f"1. v19をQTRにインストール（ルール8準拠）")
print(f"2. 6分45秒露光でテストプリント")
print(f"3. 濃度測定して理想値との比較")
print(f"4. 理想濃度に到達していれば完成")
print(f"{'=' * 80}")
