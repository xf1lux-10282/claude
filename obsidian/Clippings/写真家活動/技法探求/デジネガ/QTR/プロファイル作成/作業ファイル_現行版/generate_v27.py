#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v27 QTRカーブ生成
v26の改良版

v26の問題点:
1. Input 255 = 0.11（紙白0.09に未到達）
2. Input 48で濃度逆転（-0.010）
3. 72-128の濃度差が不均一
4. シャドウ域（24-80）が濃すぎる

v27の改善:
1. Input 8: 2520 → 2080（シャドウに余裕）
2. Input 9-254: v26から比例調整
3. Input 255: 36000（紙白確実到達）

Generated: 2026-04-03
"""
import numpy as np

print("=" * 80)
print("v27 K単色カーブ生成開始")
print("v26改良版（Input 8下げ + Input 255上げ）")
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
print(f"  v26 K[255] = {v26_k_values[255]}")

# ===== v27のK値を計算 =====
print("\n[Step 2] v27のK値を計算")

# Input 0は固定
v27_k_values = [0]

# Input 8の新しい値
k_8_old = v26_k_values[8]  # 2520
k_8_new = 2080

print(f"\nInput 8の変更:")
print(f"  v26 K[8] = {k_8_old}")
print(f"  v27 K[8] = {k_8_new}")
print(f"  差: {k_8_new - k_8_old}")

# Input 1-7: 0からInput 8へ線形補間
for i in range(1, 9):
    k = round(k_8_new * i / 8)
    v27_k_values.append(k)

# Input 9-254: v26から比例調整
# Input 8の減少分を全体に反映（線形スケーリング）
scale_factor = (v26_k_values[254] - k_8_new) / (v26_k_values[254] - k_8_old)

print(f"\nInput 9-254のスケーリング:")
print(f"  スケール係数: {scale_factor:.4f}")

for i in range(9, 255):
    # v26のK値からInput 8以降の部分をスケーリング
    k_offset = v26_k_values[i] - k_8_old
    k_new = k_8_new + round(k_offset * scale_factor)
    v27_k_values.append(k_new)

# Input 255: 36000に設定
k_255_new = 36000
v27_k_values.append(k_255_new)

print(f"\nInput 255の変更:")
print(f"  v26 K[255] = {v26_k_values[255]}")
print(f"  v27 K[255] = {k_255_new}")
print(f"  差: {k_255_new - v26_k_values[255]}")

print(f"\n✓ v27 K値計算完了: {len(v27_k_values)} values")

# ===== 単調増加を確認 =====
print("\n[Step 3] 単調増加を確認")

violations = 0
for i in range(1, 256):
    if v27_k_values[i] <= v27_k_values[i-1]:
        violations += 1
        print(f"  警告: K[{i}] = {v27_k_values[i]} <= K[{i-1}] = {v27_k_values[i-1]}")
        # 修正
        v27_k_values[i] = v27_k_values[i-1] + 1

if violations == 0:
    print("✓ 単調増加: 完璧")
else:
    print(f"✓ 単調増加: {violations}箇所を修正")

# ===== .quadファイル生成 =====
print("\n[Step 4] Quadファイルを生成中...")

quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v27
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - v26 improved version
# - Input 8: 2520 → 2080 (shadow headroom)
# - Input 9-254: scaled from v26
# - Input 255: 36000 (paper white guaranteed)
# - v26 issues: Input 48 density reversal, 72-128 uneven steps
# - v26 issues: Shadow too dark (24-80), highlight too light (128-200)
# - v26 issues: Input 255 = 0.11 (target 0.09 not reached)
# - Exposure: 6:45
# Generated: 2026-04-03 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# v26 improved (Input 8 lowered, 255 raised)
#
# K curve
"""

for k in v27_k_values:
    quad_content += f"{k}\n"

quad_content += "#\n"

# 残り9チャンネル（全て0）
for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# 保存
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v27.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v27カーブ生成完了: {output_path}")

# ===== ファイル整合性確認 =====
print(f"\n[Step 5] ファイル整合性確認")
import os
file_size = os.path.getsize(output_path)
with open(output_path, 'r') as f:
    line_count = len(f.readlines())

print(f"ファイルサイズ: {file_size} bytes")
print(f"総行数: {line_count} 行")

# ===== v26との比較 =====
print(f"\n[Step 6] v26とv27の比較（主要ポイント）")

print("\nInput | v26_K | v27_K | 差分 | 備考")
print("------|-------|-------|------|------------------")
for i in [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 128, 160, 192, 216, 232, 240, 248, 254, 255]:
    v26_k = v26_k_values[i]
    v27_k = v27_k_values[i]
    diff = v27_k - v26_k

    if i == 0:
        note = "固定"
    elif i == 8:
        note = "下げ（シャドウ余裕）"
    elif i == 255:
        note = "上げ（紙白到達）"
    elif diff < -100:
        note = "大幅減"
    elif diff < 0:
        note = "減"
    elif diff > 100:
        note = "大幅増"
    elif diff > 0:
        note = "増"
    else:
        note = "同じ"

    print(f"{i:5} | {v26_k:5} | {v27_k:5} | {diff:+4} | {note}")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v27 K単色カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ Input 0: 0（固定）")
print(f"  ✓ Input 8: 2080（v26の2520から-440）")
print(f"  ✓ Input 9-254: v26から比例調整")
print(f"  ✓ Input 255: 36000（v26の33500から+2500）")
print(f"  ✓ 露光時間: 6分45秒")
print(f"\n【v26からの改善点】")
print(f"  1. Input 8下げ → シャドウに余裕、24-80の濃度改善期待")
print(f"  2. Input 255上げ → 紙白確実到達（0.09目標）")
print(f"  3. スケーリング → 全体バランス維持、Input 48逆転解消期待")
print(f"  4. スケーリング → 72-128の濃度差均一化期待")
print(f"\n【期待される効果】")
print(f"  1. シャドウ域（24-80）の濃度が適切に")
print(f"  2. Input 48の濃度逆転解消")
print(f"  3. 72-128の濃度差が均一に")
print(f"  4. Input 255で紙白確実到達")
print(f"\n【次のステップ】")
print(f"1. v27をQTRにインストール")
print(f"2. 6分45秒露光でテストプリント")
print(f"3. v26との比較（特にシャドウと紙白）")
print(f"{'=' * 80}")
