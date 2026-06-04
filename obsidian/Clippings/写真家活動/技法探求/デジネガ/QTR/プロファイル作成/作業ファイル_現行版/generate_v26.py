#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v26 QTRカーブ生成
v22ベース（0-248） + 紙白補正（248-255均等割、255=33500）

重要なフィードバック:
- v25: 紙白効果は良いが、Input 248の濃度が濃すぎる
- v22: v20より全体的にバランスが良い（特にハイライト領域）
- 提案: v22の0-248 + 紙白補正（255=33500、v25の35000より控えめ）

設計コンセプト:
- Input 0-248: v22の値を使用（全体バランス改善）
- Input 255: 33500（紙白到達、v25より控えめ）
- Input 248-255: 均等8分割（スムーズな移行）
- 露光時間: 6分45秒

Generated: 2026-04-03
"""
import numpy as np

print("=" * 80)
print("v26 K単色カーブ生成開始")
print("v22ベース（0-248） + 紙白補正（248-255均等割、255=33500）")
print("=" * 80)

# ===== v22のK値を読み込み =====
print("\n[Step 1] v22のK値を読み込み")

v22_k_path = '/tmp/v22_k_values.txt'
with open(v22_k_path, 'r') as f:
    v22_k_values = [int(line.strip()) for line in f.readlines()]

print(f"✓ v22 K値読み込み完了: {len(v22_k_values)} values")
print(f"  v22 K[0] = {v22_k_values[0]}")
print(f"  v22 K[248] = {v22_k_values[248]}")
print(f"  v22 K[255] = {v22_k_values[255]}")

# v20との比較
v20_k_path = '/tmp/v20_k_values.txt'
with open(v20_k_path, 'r') as f:
    v20_k_values = [int(line.strip()) for line in f.readlines()]

print(f"\n【v22とv20の比較（248）】")
print(f"  v20 K[248] = {v20_k_values[248]}")
print(f"  v22 K[248] = {v22_k_values[248]} (差: {v22_k_values[248] - v20_k_values[248]:+d})")

# ===== v26のK値を計算 =====
print("\n[Step 2] v26のK値を計算")

# Input 0-248: v22の値をそのまま使用
v26_k_values = v22_k_values[:249].copy()  # 0-248の249個

# Input 248-255を均等8分割
k_248 = v22_k_values[248]  # 30020
k_255_new = 33500

# 248から255まで8ステップ（249, 250, 251, 252, 253, 254, 255）
step = (k_255_new - k_248) / 7  # 7ステップで8ポイント

print(f"\n248-255の計算:")
print(f"  K[248] = {k_248} (v22のまま)")
print(f"  K[255] = {k_255_new} (新設定)")
print(f"  ステップ幅 = {step:.1f}")

# 249-255を計算
for i in range(1, 8):  # 1-7 (249-255に対応)
    k_value = round(k_248 + step * i)
    v26_k_values.append(k_value)
    print(f"  K[{248 + i}] = {k_value}")

print(f"\n✓ v26 K値計算完了: {len(v26_k_values)} values")

# ===== 単調増加を確認 =====
print("\n[Step 3] 単調増加を確認")

violations = 0
for i in range(1, 256):
    if v26_k_values[i] <= v26_k_values[i-1]:
        violations += 1
        print(f"  警告: K[{i}] = {v26_k_values[i]} <= K[{i-1}] = {v26_k_values[i-1]}")
        # 修正
        v26_k_values[i] = v26_k_values[i-1] + 1

if violations == 0:
    print("✓ 単調増加: 完璧")
else:
    print(f"✓ 単調増加: {violations}箇所を修正")

# ===== .quadファイル生成 =====
print("\n[Step 4] Quadファイルを生成中...")

quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v26
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - v22 base (0-248) for better overall balance
# - Input 248-255 recalculated: even 8-step division
# - K[255] = 33500 (paper white, moderate vs v25's 35000)
# - v25 feedback: paper white good, but Input 248 too dark
# - v22 has better balance in highlight region than v20
# - Exposure: 6:45
# Generated: 2026-04-03 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# v22 (0-248) + paper white correction (248-255)
#
# K curve
"""

for k in v26_k_values:
    quad_content += f"{k}\n"

quad_content += "#\n"

# 残り9チャンネル（全て0）
for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# 保存
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v26.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v26カーブ生成完了: {output_path}")

# ===== ファイル整合性確認 =====
print(f"\n[Step 5] ファイル整合性確認")
import os
file_size = os.path.getsize(output_path)
with open(output_path, 'r') as f:
    line_count = len(f.readlines())

print(f"ファイルサイズ: {file_size} bytes")
print(f"総行数: {line_count} 行")

# ===== v25との比較 =====
print(f"\n[Step 6] v25とv26の比較（245-255）")

# v25のK値（v24ベース + 255=35000）
v25_k_values = v20_k_values[:249].copy()  # 0-248はv20
k_248_v24 = 29028
k_255_v24 = 32820
step_v24 = (k_255_v24 - k_248_v24) / 7
for i in range(1, 7):
    v25_k_values.append(round(k_248_v24 + step_v24 * i))
v25_k_values.append(35000)  # 255

print("\nInput | v25_K | v26_K | 差分 | 備考")
print("------|-------|-------|------|------------------")
for i in range(245, 256):
    v25_k = v25_k_values[i]
    v26_k = v26_k_values[i]
    diff = v26_k - v25_k
    if i == 248:
        note = f"v22ベース (v20比{v26_k - v20_k_values[i]:+d})"
    elif i == 255:
        note = "33500 vs 35000"
    else:
        note = f"差{diff:+d}"
    print(f"{i:5} | {v25_k:5} | {v26_k:5} | {diff:+4} | {note}")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v26 K単色カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ Input 0-248: v22の値を使用（バランス改善）")
print(f"  ✓ Input 248-255: 均等8分割（紙白補正）")
print(f"  ✓ K[248] = {v26_k_values[248]} (v22、v20の{v20_k_values[248]}より+{v26_k_values[248] - v20_k_values[248]})")
print(f"  ✓ K[255] = {v26_k_values[255]} (v25の35000より控えめ)")
print(f"  ✓ 248-255ステップ幅 = {step:.1f} (均等)")
print(f"  ✓ 露光時間: 6分45秒")
print(f"\n【v25からの改善点】")
print(f"  1. v22ベース → Input 248の濃度が適切に")
print(f"  2. K[255] = 33500 → 紙白到達（v25より控えめ）")
print(f"  3. v22は全体的にバランスが良い（特にハイライト）")
print(f"\n【期待される効果】")
print(f"  1. Input 248の濃度が適切 → ハイライト階調改善")
print(f"  2. 紙白到達 → ハイライト判別可能")
print(f"  3. 全体バランス改善 → より自然な階調")
print(f"\n【次のステップ】")
print(f"1. v26をQTRにインストール")
print(f"2. 6分45秒露光でテストプリント")
print(f"3. Input 248の濃度と紙白表現を確認")
print(f"{'=' * 80}")
