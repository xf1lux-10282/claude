#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v29 QTRカーブ生成
ユーザー指定の精密なゾーン勾配設計

設計:
- Zone 1 (Shadow, Input 0-24): 175 K/step
- Zone 2 (Midtone, Input 25-240): 115 K/step
- Zone 3 (Highlight, Input 241-254): 300 K/step
- Input 255: 40000 (紙白確実到達)

Generated: 2026-04-04
"""
import numpy as np

print("=" * 80)
print("v29カーブ生成開始（ユーザー指定勾配）")
print("=" * 80)

# ===== Zone設計 =====
print("\n[Step 1] Zone設計の確認")
print("""
Zone 1 (Shadow):    Input 0-24   (25点) → 175 K/step
Zone 2 (Midtone):   Input 25-240 (216点) → 115 K/step
Zone 3 (Highlight): Input 241-254 (14点) → 300 K/step
Special:            Input 255 = 40000
""")

# ===== K値計算 =====
print("\n[Step 2] K値を計算中...")

k_values = []

# Zone 1: Input 0-24 (175 K/step)
k = 0
k_values.append(k)  # Input 0
for i in range(1, 25):  # Input 1-24
    k += 175
    k_values.append(k)

print(f"✓ Zone 1完了: Input 0-24")
print(f"  Input 0: K = {k_values[0]}")
print(f"  Input 24: K = {k_values[24]}")

# Zone 2: Input 25-240 (115 K/step)
for i in range(25, 241):  # Input 25-240
    k += 115
    k_values.append(k)

print(f"✓ Zone 2完了: Input 25-240")
print(f"  Input 25: K = {k_values[25]}")
print(f"  Input 240: K = {k_values[240]}")

# Zone 3: Input 241-254 (300 K/step)
for i in range(241, 255):  # Input 241-254
    k += 300
    k_values.append(k)

print(f"✓ Zone 3完了: Input 241-254")
print(f"  Input 241: K = {k_values[241]}")
print(f"  Input 254: K = {k_values[254]}")

# Input 255: 40000
k_values.append(40000)

print(f"✓ Input 255: K = {k_values[255]}")

# ===== 計算結果の確認 =====
print("\n[Step 3] 計算結果の確認")
print(f"総K値数: {len(k_values)} (期待値: 256)")

# 主要ポイントの確認
print(f"\n主要ポイント:")
print(f"Input |     K | Zone")
print(f"------|-------|--------------")
for i in [0, 8, 24, 25, 48, 128, 240, 241, 254, 255]:
    zone = "Shadow" if i <= 24 else "Midtone" if i <= 240 else "Highlight" if i <= 254 else "Paper white"
    print(f"{i:5} | {k_values[i]:5} | {zone}")

# ステップ差の確認
print(f"\n各ゾーンの実際のステップ差:")
print(f"  Zone 1 (Input 0→24): {k_values[24] - k_values[0]} / 24 = {(k_values[24] - k_values[0]) / 24:.1f} K/step")
print(f"  Zone 2 (Input 25→240): {k_values[240] - k_values[25]} / 215 = {(k_values[240] - k_values[25]) / 215:.1f} K/step")
print(f"  Zone 3 (Input 241→254): {k_values[254] - k_values[241]} / 13 = {(k_values[254] - k_values[241]) / 13:.1f} K/step")
print(f"  Input 254→255: {k_values[255] - k_values[254]} K")

# ===== 露光時間の計算 =====
print("\n[Step 4] 露光時間の計算")

# v14のK[255]=33800, 露光時間6分45秒を基準
v14_k255 = 33800
v14_exposure_sec = 6 * 60 + 45  # 405秒

v29_k255 = k_values[255]
k_increase_pct = ((v29_k255 - v14_k255) / v14_k255) * 100

# K値増加に対する露光時間減少（約10%）
exposure_reduction_pct = 10
v29_exposure_sec = v14_exposure_sec * (1 - exposure_reduction_pct / 100)
v29_exposure_min = int(v29_exposure_sec // 60)
v29_exposure_sec_remainder = int(v29_exposure_sec % 60)

print(f"  v14: K[255] = {v14_k255}, 露光 6分45秒")
print(f"  v29: K[255] = {v29_k255} (+{k_increase_pct:.1f}%)")
print(f"  → 露光時間: {v29_exposure_min}分{v29_exposure_sec_remainder:02d}秒 (-{exposure_reduction_pct}%)")

# ===== .quadファイル生成 =====
print("\n[Step 5] Quadファイルを生成中...")

quad_content = f"""## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v29
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Custom zone gradients by user specification
# - Zone 1 (Shadow, 0-24): 175 K/step
# - Zone 2 (Midtone, 25-240): 115 K/step
# - Zone 3 (Highlight, 241-254): 300 K/step
# - Input 255: 40000 (paper white target)
# - Exposure: {v29_exposure_min}:{v29_exposure_sec_remainder:02d} (v14's 6:45 reduced by {exposure_reduction_pct}%)
# - Target: Paper white (D=0.09) at Input 255
# Generated: 2026-04-04 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# User-specified zone gradients
#
# K curve
"""

for k in k_values:
    quad_content += f"{k}\n"
quad_content += "#\n"

# C, M, Y, LC, LM, LK, LLK, V, MK (全て0)
for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# 保存
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v29.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v29カーブ生成完了: {output_path}")

# ===== ファイル整合性確認 =====
print(f"\n[Step 6] ファイル整合性確認")
import os
file_size = os.path.getsize(output_path)
with open(output_path, 'r') as f:
    line_count = len(f.readlines())

print(f"ファイルサイズ: {file_size} bytes")
print(f"総行数: {line_count} 行")

# ===== CSV出力 =====
print(f"\n[Step 7] CSV出力")

csv_path = output_path.replace('.quad', '_values.csv')
with open(csv_path, 'w', encoding='utf-8') as f:
    f.write("Input,K_value,Diff_from_prev,Zone\n")
    for i in range(len(k_values)):
        k = k_values[i]
        if i > 0:
            diff = k - k_values[i-1]
        else:
            diff = 0

        # Zone classification
        if i <= 24:
            zone = 'Shadow (Zone 1)'
        elif i <= 240:
            zone = 'Midtone (Zone 2)'
        elif i <= 254:
            zone = 'Highlight (Zone 3)'
        else:
            zone = 'Paper white'

        f.write(f"{i},{k},{diff},{zone}\n")

print(f"✓ CSV出力完了: {csv_path}")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v29カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ Zone 1 (Shadow, 0-24): 175 K/step")
print(f"  ✓ Zone 2 (Midtone, 25-240): 115 K/step")
print(f"  ✓ Zone 3 (Highlight, 241-254): 300 K/step")
print(f"  ✓ Input 255: 40000 (紙白確実到達)")
print(f"  ✓ 露光時間: {v29_exposure_min}分{v29_exposure_sec_remainder:02d}秒")
print(f"\n【K値範囲】")
print(f"  Input   0: K =     {k_values[0]}")
print(f"  Input  24: K =  {k_values[24]:5} (Zone 1終端)")
print(f"  Input  25: K =  {k_values[25]:5} (Zone 2開始)")
print(f"  Input 240: K = {k_values[240]:5} (Zone 2終端)")
print(f"  Input 241: K = {k_values[241]:5} (Zone 3開始)")
print(f"  Input 254: K = {k_values[254]:5} (Zone 3終端)")
print(f"  Input 255: K = {k_values[255]:5} (紙白)")
print(f"\n【次のステップ】")
print(f"1. v29をQTRにインストール")
print(f"2. {v29_exposure_min}分{v29_exposure_sec_remainder:02d}秒露光でテストプリント")
print(f"3. 紙白到達を確認（Input 255の濃度 < 0.09）")
print(f"4. 各ゾーンの階調の滑らかさを評価")
print(f"{'=' * 80}")
