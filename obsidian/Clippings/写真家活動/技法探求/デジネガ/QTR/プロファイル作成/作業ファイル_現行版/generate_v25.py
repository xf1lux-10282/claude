#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v25 QTRカーブ生成
v24ベース（0-254） + Input 255を35000に設定

重要な発見:
- v24（7:30露光）で紙白効果が確認できた
- ハイライト階調の判別が可能になった
- 露光時間を6:45に戻し、Input 255のみさらに増加

設計コンセプト:
- Input 0-254: v24と完全同一（v20ベース + 248-254の紙白補正）
- Input 255: 35000に設定（極端な紙白強調）
- 露光時間: 6分45秒（v20/v24の7:30から短縮）
- 254-255のステップは大きいが、紙白表現のため許容

Generated: 2026-04-03
"""
import numpy as np

print("=" * 80)
print("v25 K単色カーブ生成開始")
print("v24ベース + Input 255を35000に設定")
print("=" * 80)

# ===== v24のK値を読み込み =====
print("\n[Step 1] v24のK値を読み込み")

# v20のK値（0-248）
v20_k_path = '/tmp/v20_k_values.txt'
with open(v20_k_path, 'r') as f:
    v20_k_values = [int(line.strip()) for line in f.readlines()]

# v24のK値を再構成（0-248はv20、248-255は補正済み）
v24_k_values = v20_k_values[:249].copy()  # 0-248

# v24の248-255（v24で計算済み）
k_248 = 29028
k_255_v24 = 32820
step_v24 = (k_255_v24 - k_248) / 7

for i in range(1, 8):
    k_value = round(k_248 + step_v24 * i)
    v24_k_values.append(k_value)

print(f"✓ v24 K値読み込み完了: {len(v24_k_values)} values")
print(f"  v24 K[0] = {v24_k_values[0]}")
print(f"  v24 K[254] = {v24_k_values[254]}")
print(f"  v24 K[255] = {v24_k_values[255]}")

# ===== v25のK値を計算 =====
print("\n[Step 2] v25のK値を計算")

# Input 0-254: v24の値をそのまま使用
v25_k_values = v24_k_values[:255].copy()  # 0-254の255個

# Input 255のみ35000に設定
k_255_new = 35000
v25_k_values.append(k_255_new)

print(f"\n✓ v25 K値計算完了: {len(v25_k_values)} values")
print(f"  v25 K[0] = {v25_k_values[0]}")
print(f"  v25 K[254] = {v25_k_values[254]}")
print(f"  v25 K[255] = {v25_k_values[255]} (新設定)")

# 254-255のステップ幅
step_254_255 = v25_k_values[255] - v25_k_values[254]
print(f"\n254-255のステップ幅: {step_254_255}")

# ===== 単調増加を確認 =====
print("\n[Step 3] 単調増加を確認")

violations = 0
for i in range(1, 256):
    if v25_k_values[i] <= v25_k_values[i-1]:
        violations += 1
        print(f"  警告: K[{i}] = {v25_k_values[i]} <= K[{i-1}] = {v25_k_values[i-1]}")

if violations == 0:
    print("✓ 単調増加: 完璧")
else:
    print(f"✗ 単調増加違反: {violations}箇所")

# ===== .quadファイル生成 =====
print("\n[Step 4] Quadファイルを生成中...")

quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v25
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - v24 base (0-254 unchanged)
# - Input 255 = 35000 (extreme paper white emphasis)
# - v24 confirmed paper white effect and highlight visibility
# - Return to 6:45 exposure (from 7:30)
# - Large step 254-255 acceptable for paper white expression
# Generated: 2026-04-03 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# v24 + Input 255 extreme boost (6:45 exposure)
#
# K curve
"""

for k in v25_k_values:
    quad_content += f"{k}\n"

quad_content += "#\n"

# 残り9チャンネル（全て0）
for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# 保存
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v25.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v25カーブ生成完了: {output_path}")

# ===== ファイル整合性確認 =====
print(f"\n[Step 5] ファイル整合性確認")
import os
file_size = os.path.getsize(output_path)
with open(output_path, 'r') as f:
    line_count = len(f.readlines())

print(f"ファイルサイズ: {file_size} bytes")
print(f"総行数: {line_count} 行")

# ===== 比較表示 =====
print(f"\n[Step 6] v24とv25の比較（252-255）")

print("\nInput | v24_K | v25_K | 差分 | v25増加率")
print("------|-------|-------|------|----------")
for i in range(252, 256):
    v24_k = v24_k_values[i]
    v25_k = v25_k_values[i]
    diff = v25_k - v24_k
    increase_pct = (diff / v24_k * 100) if v24_k > 0 else 0
    print(f"{i:5} | {v24_k:5} | {v25_k:5} | {diff:+4} | {increase_pct:+5.1f}%")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v25 K単色カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ Input 0-254: v24と同一（v20ベース + 248-254紙白補正）")
print(f"  ✓ Input 255: 35000（v24の{v24_k_values[255]}から+{35000-v24_k_values[255]}、+{(35000-v24_k_values[255])/v24_k_values[255]*100:.1f}%）")
print(f"  ✓ 254-255ステップ: {step_254_255}（極端だが紙白表現のため）")
print(f"  ✓ 露光時間: 6分45秒（v24の7:30から短縮）")
print(f"\n【v24での発見】")
print(f"  1. 紙白に近づくとハイライトが判別できるようになった")
print(f"  2. 紙白効果が確認できた")
print(f"  3. 露光時間を短くして、Input 255をさらに強調")
print(f"\n【設計意図】")
print(f"  1. 露光時間6:45に戻す → 全体的に濃度を維持")
print(f"  2. Input 255のみ極端に増加 → 紙白を確実に表現")
print(f"  3. 254-255の大きなステップは紙白到達のための技術的処理")
print(f"\n【次のステップ】")
print(f"1. v25をQTRにインストール")
print(f"2. 6分45秒露光でテストプリント")
print(f"3. 紙白表現とハイライト階調の両立を確認")
print(f"{'=' * 80}")
