#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v24 QTRカーブ生成
v20ベース + 248-255を紙白到達のために再計算

重要な発見:
- Input 255 (K=29752) は白飛び（インク過少）であり、純粋な紙白ではない
- 純粋な紙白（インク無し）はもっと濃度が低い（明るい）
- Input 255のK値を32820に大幅増加して紙白に到達させる

設計コンセプト:
- Input 0-248: v20の値を完全に固定（階調保持）
- Input 255: 32820に設定（紙白到達）
- Input 248-255: 均等8分割（紙白への移行階調）
- この階調は「表現」ではなく「紙白到達」のための技術的処理
- 紙白が表現できれば、ハイライト階調が相対的に見えやすくなる

Generated: 2026-04-03
"""
import numpy as np

print("=" * 80)
print("v24 K単色カーブ生成開始")
print("v20ベース + 248-255を紙白到達のために再計算")
print("=" * 80)

# ===== v20のK値を読み込み =====
print("\n[Step 1] v20のK値を読み込み")

v20_k_path = '/tmp/v20_k_values.txt'
with open(v20_k_path, 'r') as f:
    v20_k_values = [int(line.strip()) for line in f.readlines()]

print(f"✓ v20 K値読み込み完了: {len(v20_k_values)} values")
print(f"  v20 K[0] = {v20_k_values[0]}")
print(f"  v20 K[248] = {v20_k_values[248]}")
print(f"  v20 K[255] = {v20_k_values[255]}")

# ===== v24のK値を計算 =====
print("\n[Step 2] v24のK値を計算")

# Input 0-248: v20の値をそのまま使用
v24_k_values = v20_k_values[:249].copy()  # 0-248の249個

# Input 248-255を均等8分割
k_248 = v20_k_values[248]  # 29028
k_255_new = 32820

# 248から255まで8ステップ（249, 250, 251, 252, 253, 254, 255）
step = (k_255_new - k_248) / 7  # 7ステップで8ポイント

print(f"\n248-255の再計算:")
print(f"  K[248] = {k_248} (v20のまま)")
print(f"  K[255] = {k_255_new} (新設定)")
print(f"  ステップ幅 = {step:.1f}")

# 249-255を計算
for i in range(1, 8):  # 1-7 (249-255に対応)
    k_value = round(k_248 + step * i)
    v24_k_values.append(k_value)
    print(f"  K[{248 + i}] = {k_value}")

print(f"\n✓ v24 K値計算完了: {len(v24_k_values)} values")

# ===== 単調増加を確認 =====
print("\n[Step 3] 単調増加を確認")

violations = 0
for i in range(1, 256):
    if v24_k_values[i] <= v24_k_values[i-1]:
        violations += 1
        print(f"  警告: K[{i}] = {v24_k_values[i]} <= K[{i-1}] = {v24_k_values[i-1]}")
        # 修正
        v24_k_values[i] = v24_k_values[i-1] + 1

if violations == 0:
    print("✓ 単調増加: 完璧")
else:
    print(f"✓ 単調増加: {violations}箇所を修正")

# ===== .quadファイル生成 =====
print("\n[Step 4] Quadファイルを生成中...")

quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v24
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - v20 base (0-248 unchanged)
# - Input 248-255 recalculated for paper white
# - K[255] = 32820 (significant increase to reach paper white)
# - Important discovery: Input 255 was underexposed (not paper white)
# - Pure paper white has lower density (brighter)
# - 248-255 gradation is technical (for paper white), not artistic
# - Exposure: 7:30 (adjusted from 6:45)
# Generated: 2026-04-03 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# v20 + paper white correction (248-255)
#
# K curve
"""

for k in v24_k_values:
    quad_content += f"{k}\n"

quad_content += "#\n"

# 残り9チャンネル（全て0）
for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# 保存
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v24.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v24カーブ生成完了: {output_path}")

# ===== ファイル整合性確認 =====
print(f"\n[Step 5] ファイル整合性確認")
import os
file_size = os.path.getsize(output_path)
with open(output_path, 'r') as f:
    line_count = len(f.readlines())

print(f"ファイルサイズ: {file_size} bytes")
print(f"総行数: {line_count} 行")

# ===== 比較表示 =====
print(f"\n[Step 6] v20とv24の比較（248-255）")

print("\nInput | v20_K | v24_K | 差分 | v24増加率")
print("------|-------|-------|------|----------")
for i in range(248, 256):
    v20_k = v20_k_values[i]
    v24_k = v24_k_values[i]
    diff = v24_k - v20_k
    increase_pct = (diff / v20_k * 100) if v20_k > 0 else 0
    print(f"{i:5} | {v20_k:5} | {v24_k:5} | {diff:+4} | {increase_pct:+5.1f}%")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v24 K単色カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ Input 0-248: v20のまま（階調保持）")
print(f"  ✓ Input 248-255: 紙白到達のために再計算")
print(f"  ✓ K[248] = {v24_k_values[248]} (v20と同じ)")
print(f"  ✓ K[255] = {v24_k_values[255]} (v20の{v20_k_values[255]}から+{v24_k_values[255]-v20_k_values[255]})")
print(f"  ✓ 露光時間: 7分30秒（v20の6分45秒から調整）")
print(f"\n【設計意図】")
print(f"  1. Input 255は白飛び（インク過少）であり、純粋な紙白ではなかった")
print(f"  2. K値を大幅増加してネガを濃く → プリントを浅く → 紙白到達")
print(f"  3. 248-255の階調は表現ではなく紙白到達のための技術的処理")
print(f"  4. 紙白が表現できれば、ハイライト階調が相対的に見えやすくなる")
print(f"\n【次のステップ】")
print(f"1. v24をQTRにインストール")
print(f"2. 7分30秒露光でテストプリント")
print(f"3. 純粋な紙白が表現できているか確認")
print(f"4. ハイライト階調の可視性向上を確認")
print(f"{'=' * 80}")
