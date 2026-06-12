#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v28 QTRカーブ生成
v26ベース + K[255]=40000

v27の失敗分析:
- Input 8を下げる(2520→2080)とプリントが逆に濃くなった
- 物理: K値↓ → ネガ薄↑ → 光透過↑ → プリント濃↑
- シャドウ域(24-80)がv26より濃くなり、改悪だった

v28の設計:
1. v26のK値をそのまま使用（0-254）
2. Input 255のみ40000に増加（v26: 33500）
3. 露光時間を6分30秒に減少（v26: 6分45秒）

理由:
- v26は24-80のバランスが良かった
- 紙白到達のみが課題（Input 255 = 0.11）
- K[255]増加 → 露光時間減少で補正

Generated: 2026-04-03
"""
import numpy as np

print("=" * 80)
print("v28 K単色カーブ生成開始")
print("v26ベース + K[255]=40000")
print("=" * 80)

# ===== v26のK値を読み込み =====
print("\n[Step 1] v26のK値を読み込み")

v22_k_path = '/tmp/v22_k_values.txt'
with open(v22_k_path, 'r') as f:
    v22_k_values = [int(line.strip()) for line in f.readlines()]

# v26のK値を再構成（0-248はv22、248-255は補正済み）
v26_k_values = v22_k_values[:249].copy()  # 0-248

# v26の248-255（K[248]=30020, K[255]=33500）
k_248 = 30020
k_255_v26 = 33500
step_v26 = (k_255_v26 - k_248) / 7

for i in range(1, 8):
    k_value = round(k_248 + step_v26 * i)
    v26_k_values.append(k_value)

print(f"✓ v26 K値読み込み完了: {len(v26_k_values)} values")
print(f"  v26 K[0] = {v26_k_values[0]}")
print(f"  v26 K[8] = {v26_k_values[8]}")
print(f"  v26 K[248] = {v26_k_values[248]}")
print(f"  v26 K[255] = {v26_k_values[255]}")

# ===== v28のK値を計算 =====
print("\n[Step 2] v28のK値を計算")

# Input 0-254: v26そのまま
v28_k_values = v26_k_values[:255].copy()

# Input 255のみ変更
k_255_new = 40000
v28_k_values.append(k_255_new)

print(f"\nInput 255の変更:")
print(f"  v26 K[255] = {v26_k_values[255]}")
print(f"  v28 K[255] = {k_255_new}")
print(f"  差: {k_255_new - v26_k_values[255]} (+{(k_255_new / v26_k_values[255] - 1) * 100:.1f}%)")

print(f"\n✓ v28 K値計算完了: {len(v28_k_values)} values")

# ===== 単調増加を確認 =====
print("\n[Step 3] 単調増加を確認")

violations = 0
for i in range(1, 256):
    if v28_k_values[i] <= v28_k_values[i-1]:
        violations += 1
        print(f"  警告: K[{i}] = {v28_k_values[i]} <= K[{i-1}] = {v28_k_values[i-1]}")
        # 修正
        v28_k_values[i] = v28_k_values[i-1] + 1

if violations == 0:
    print("✓ 単調増加: 完璧")
else:
    print(f"✓ 単調増加: {violations}箇所を修正")

# ===== .quadファイル生成 =====
print("\n[Step 4] Quadファイルを生成中...")

quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v28
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - v26 base (0-254) + K[255]=40000
# - v27 failure: Input 8 reduction backfired (darker prints)
# - v28 strategy: Only adjust K[255], keep v26 shadow balance
# - Exposure: 6:05 (reduced 40s from v26's 6:45, -10%) (reduced from 6:45 to compensate K[255] increase)
# - Target: Paper white (D=0.09) at Input 255
# Generated: 2026-04-03 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# v26 base + K[255]=40000
#
# K curve
"""

for k in v28_k_values:
    quad_content += f"{k}\n"

quad_content += "#\n"

# 残り9チャンネル（全て0）
for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# 保存
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v28.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v28カーブ生成完了: {output_path}")

# ===== ファイル整合性確認 =====
print(f"\n[Step 5] ファイル整合性確認")
import os
file_size = os.path.getsize(output_path)
with open(output_path, 'r') as f:
    line_count = len(f.readlines())

print(f"ファイルサイズ: {file_size} bytes")
print(f"総行数: {line_count} 行")

# ===== v26とv28の比較 =====
print(f"\n[Step 6] v26とv28の比較（主要ポイント）")

print("\nInput | v26_K | v28_K | 差分 | 備考")
print("------|-------|-------|------|------------------")
for i in [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 128, 160, 192, 216, 232, 240, 248, 254, 255]:
    v26_k = v26_k_values[i]
    v28_k = v28_k_values[i]
    diff = v28_k - v26_k

    if i == 255:
        note = "増（紙白到達）"
    elif diff == 0:
        note = "同一"
    else:
        note = f"{diff:+d}"

    print(f"{i:5} | {v26_k:5} | {v28_k:5} | {diff:+5} | {note}")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v28 K単色カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ Input 0-254: v26と同一")
print(f"  ✓ Input 255: 40000（v26の33500から+6500、+19.4%）")
print(f"  ✓ 露光時間: 6分05秒（v26の6分45秒から-40秒、-10%）")
print(f"\n【v27の失敗から学んだこと】")
print(f"  1. Input 8を下げる → プリントが濃くなる（逆効果）")
print(f"  2. K値↓ → ネガ薄↑ → 光透過↑ → プリント濃↑")
print(f"  3. v26のシャドウバランスが実は良かった")
print(f"  4. ハンドコーティングによる±0.01-0.02の変動は誤差範囲")
print(f"\n【v28の設計思想】")
print(f"  1. v26のシャドウバランスを保持")
print(f"  2. 紙白到達のみを改善（K[255]増加）")
print(f"  3. K[255]増加分を露光時間減少で補正")
print(f"\n【期待される効果】")
print(f"  1. シャドウ域（24-80）はv26と同じ良好なバランス")
print(f"  2. ハイライト域（128-200）もv26と同じ")
print(f"  3. Input 255で紙白確実到達（0.09以下）")
print(f"  4. 全体的な濃度バランスが理想的")
print(f"\n【次のステップ】")
print(f"1. v28をQTRにインストール")
print(f"2. 6分05秒露光でテストプリント（K値+19.4%に対し露光-10%）")
print(f"3. v26とv28の比較（特に紙白到達確認）")
print(f"4. 紙白が0.09以下なら、v28でシャドウ微調整検討")
print(f"{'=' * 80}")
