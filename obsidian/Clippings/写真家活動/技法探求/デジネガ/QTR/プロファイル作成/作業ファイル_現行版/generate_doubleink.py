#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-doubleink QTRカーブ生成
K + GY ダブルインク構成（v29-doubleink-3の正式版）

設計:
- GY channel (LK, 階調担当):
  - Zone 1 (0-24): 175 K/step
  - Zone 2 (25-240): 115 K/step
  - Zone 3 (241-254): 300 K/step
  - Input 255: 0

- K channel (濃度ベース):
  - Input 0-254: 50 K/step
  - Input 255: 40000 (紙白確実到達)

狙い:
- GYで豊かな階調を確保
- Kで濃度ベース + ディザリングパターン解消
- v29-doubleink-3の実績を正式版として採用

Generated: 2026-04-04
"""
import numpy as np
import os

print("=" * 80)
print("PX1V-PtPd-xf1-doubleink カーブ生成開始")
print("=" * 80)

# ===== GY値生成（v29と同じゾーン勾配）=====
print("\n[Step 1] GY値を計算（v29と同じゾーン勾配）")

gy_values = []

# Zone 1: Input 0-24 (175 K/step)
k = 0
gy_values.append(k)  # Input 0
for i in range(1, 25):  # Input 1-24
    k += 175
    gy_values.append(k)

print(f"✓ Zone 1完了: Input 0-24")
print(f"  GY[0] = {gy_values[0]}")
print(f"  GY[24] = {gy_values[24]}")

# Zone 2: Input 25-240 (115 K/step)
for i in range(25, 241):  # Input 25-240
    k += 115
    gy_values.append(k)

print(f"✓ Zone 2完了: Input 25-240")
print(f"  GY[25] = {gy_values[25]}")
print(f"  GY[240] = {gy_values[240]}")

# Zone 3: Input 241-254 (300 K/step)
for i in range(241, 255):  # Input 241-254
    k += 300
    gy_values.append(k)

print(f"✓ Zone 3完了: Input 241-254")
print(f"  GY[241] = {gy_values[241]}")
print(f"  GY[254] = {gy_values[254]}")

# Input 255: 0
gy_values.append(0)

print(f"✓ Input 255: GY = {gy_values[255]}")

# ===== K値生成（0-254は50 K/step）=====
print("\n[Step 2] K値を計算（0-254は50 K/step）")

k_values_doubleink = []

# Input 0-254: 50 K/step
for i in range(255):
    k_values_doubleink.append(i * 50)

# Input 255: 40000 (紙白確実到達)
k_values_doubleink.append(40000)

print(f"✓ K値計算完了: {len(k_values_doubleink)} values")
print(f"  K[0] = {k_values_doubleink[0]}")
print(f"  K[24] = {k_values_doubleink[24]}")
print(f"  K[240] = {k_values_doubleink[240]}")
print(f"  K[254] = {k_values_doubleink[254]}")
print(f"  K[255] = {k_values_doubleink[255]}")

# ===== 主要ポイントの確認 =====
print("\n[Step 3] 主要ポイントの確認")
print(f"Input |     K | GY (LK) | 合計 | K% | 備考")
print(f"------|-------|---------|------|-----|-----")
for i in [0, 8, 24, 25, 48, 128, 240, 241, 254, 255]:
    total = k_values_doubleink[i] + gy_values[i]
    k_pct = (k_values_doubleink[i] / total * 100) if total > 0 else 0
    if i == 0:
        note = "シャドウ開始"
    elif i <= 24:
        note = "Zone 1"
    elif i == 25:
        note = "Zone 2開始"
    elif i <= 240:
        note = "Zone 2"
    elif i == 241:
        note = "Zone 3開始"
    elif i <= 254:
        note = "Zone 3"
    else:
        note = "紙白"
    print(f"{i:5} | {k_values_doubleink[i]:5} | {gy_values[i]:7} | {total:5} | {k_pct:4.1f} | {note}")

# ===== 露光時間の設定 =====
print("\n[Step 4] 露光時間の設定")
exposure_min = 5
exposure_sec = 9

print(f"  露光時間: {exposure_min}分{exposure_sec:02d}秒")

# ===== .quadファイル生成 =====
print("\n[Step 5] Quadファイルを生成中...")

quad_content = f"""## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-doubleink
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Double ink configuration: K + GY(LK)
# - GY channel (LK, gradation):
#   - Zone 1 (0-24): 175 K/step
#   - Zone 2 (25-240): 115 K/step
#   - Zone 3 (241-254): 300 K/step
#   - Input 255: 0
# - K channel (density base):
#   - Input 0-254: 50 K/step
#   - Input 255: 40000 (paper white)
# - Exposure: {exposure_min}:{exposure_sec:02d}
# - Target: Paper white (D=0.09) at Input 255
# - Benefit: Rich gradation (GY) + dithering elimination (K+GY mix)
# Generated: 2026-04-04 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# Double ink: GY (gradation) + K (density base)
#
# K curve
"""

for k in k_values_doubleink:
    quad_content += f"{k}\n"
quad_content += "#\n"

# C, M, Y, LC, LM (全て0)
for channel in ['C', 'M', 'Y', 'LC', 'LM']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# LK (GY): v29と同じゾーン勾配
quad_content += "# LK curve\n"
for gy in gy_values:
    quad_content += f"{gy}\n"
quad_content += "#\n"

# LLK, V, MK (全て0)
for channel in ['LLK', 'V', 'MK']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# 保存
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-doubleink.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ doubleinkカーブ生成完了: {output_path}")

# ===== ファイル整合性確認 =====
print(f"\n[Step 6] ファイル整合性確認")
file_size = os.path.getsize(output_path)
with open(output_path, 'r') as f:
    line_count = len(f.readlines())

print(f"ファイルサイズ: {file_size} bytes")
print(f"総行数: {line_count} 行")

# ===== CSV出力 =====
print(f"\n[Step 7] CSV出力")

csv_path = output_path.replace('.quad', '_values.csv')
with open(csv_path, 'w', encoding='utf-8') as f:
    f.write("Input,K,GY,Total,K_percent,GY_percent\n")
    for i in range(256):
        total = k_values_doubleink[i] + gy_values[i]
        k_pct = (k_values_doubleink[i] / total * 100) if total > 0 else 0
        gy_pct = (gy_values[i] / total * 100) if total > 0 else 0
        f.write(f"{i},{k_values_doubleink[i]},{gy_values[i]},{total},{k_pct:.2f},{gy_pct:.2f}\n")

print(f"✓ CSV出力完了: {csv_path}")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"PX1V-PtPd-xf1-doubleink カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ GY channel (LK, 階調担当):")
print(f"    - Zone 1 (0-24): 175 K/step")
print(f"    - Zone 2 (25-240): 115 K/step")
print(f"    - Zone 3 (241-254): 300 K/step")
print(f"    - Input 255: 0")
print(f"  ✓ K channel (濃度ベース):")
print(f"    - Input 0-254: 50 K/step")
print(f"    - Input 255: 40000 (紙白確実到達)")
print(f"  ✓ 露光時間: {exposure_min}分{exposure_sec:02d}秒")
print(f"\n【効果】")
print(f"  1. 豊かな階調（GYで表現）")
print(f"  2. 濃度ベース確保（K=50/step）")
print(f"  3. 紙白確実到達（K[255]=40000）")
print(f"  4. ディザリングパターン解消（K+GY混合、K配分22-29%）")
print(f"\n【インク配分（主要ポイント）】")
for i in [0, 24, 128, 240, 254, 255]:
    k = k_values_doubleink[i]
    gy = gy_values[i]
    total = k + gy
    k_pct = (k / total * 100) if total > 0 else 0
    print(f"  Input {i:3}: K={k:5}, GY={gy:5}, Total={total:5} (K={k_pct:4.1f}%)")
print(f"\n【次のステップ】")
print(f"1. doubleinkをQTRにインストール")
print(f"2. {exposure_min}分{exposure_sec:02d}秒露光でテストプリント")
print(f"{'=' * 80}")
