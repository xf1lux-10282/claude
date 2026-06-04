#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-3ink QTRカーブ生成
K + GY + LGY トリプルインク構成

設計:
- GY channel (LK, 階調担当):
  - Zone 1 (0-24): 175 K/step
  - Zone 2 (25-240): 115 K/step
  - Zone 3 (241-254): 300 K/step
  - Input 255: 0

- K channel (濃度ベース):
  - Input 0-254: 30 K/step
  - Input 255: 40000 (紙白確実到達)

- LGY channel (LLK, 微細階調補完):
  - Input 0-254: 10 K/step
  - Input 255: 0

狙い:
- GYで豊かな階調を確保
- Kで濃度ベース + ディザリングパターン解消
- LGYで微細階調の補完 + さらなるディザリング低減

Generated: 2026-04-05
"""
import numpy as np
import os

print("=" * 80)
print("PX1V-PtPd-xf1-3ink カーブ生成開始")
print("=" * 80)

# ===== GY値生成（ゾーン勾配）=====
print("\n[Step 1] GY値を計算（ゾーン勾配）")

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

# ===== K値生成（0-254は30 K/step）=====
print("\n[Step 2] K値を計算（0-254は30 K/step）")

k_values_3ink = []

# Input 0-254: 30 K/step
for i in range(255):
    k_values_3ink.append(i * 30)

# Input 255: 40000 (紙白確実到達)
k_values_3ink.append(40000)

print(f"✓ K値計算完了: {len(k_values_3ink)} values")
print(f"  K[0] = {k_values_3ink[0]}")
print(f"  K[24] = {k_values_3ink[24]}")
print(f"  K[240] = {k_values_3ink[240]}")
print(f"  K[254] = {k_values_3ink[254]}")
print(f"  K[255] = {k_values_3ink[255]}")

# ===== LGY値生成（0-254は10 K/step）=====
print("\n[Step 3] LGY値を計算（0-254は10 K/step）")

lgy_values = []

# Input 0-254: 10 K/step
for i in range(255):
    lgy_values.append(i * 10)

# Input 255: 0
lgy_values.append(0)

print(f"✓ LGY値計算完了: {len(lgy_values)} values")
print(f"  LGY[0] = {lgy_values[0]}")
print(f"  LGY[24] = {lgy_values[24]}")
print(f"  LGY[240] = {lgy_values[240]}")
print(f"  LGY[254] = {lgy_values[254]}")
print(f"  LGY[255] = {lgy_values[255]}")

# ===== 主要ポイントの確認 =====
print("\n[Step 4] 主要ポイントの確認")
print(f"Input |     K | GY (LK) | LGY (LLK) | 合計 | K% | LGY% | 備考")
print(f"------|-------|---------|-----------|------|-----|------|-----")
for i in [0, 8, 24, 25, 48, 128, 240, 241, 254, 255]:
    total = k_values_3ink[i] + gy_values[i] + lgy_values[i]
    k_pct = (k_values_3ink[i] / total * 100) if total > 0 else 0
    lgy_pct = (lgy_values[i] / total * 100) if total > 0 else 0
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
    print(f"{i:5} | {k_values_3ink[i]:5} | {gy_values[i]:7} | {lgy_values[i]:9} | {total:5} | {k_pct:4.1f} | {lgy_pct:5.1f} | {note}")

# ===== 露光時間の計算 =====
print("\n[Step 5] 露光時間の計算")

# 2inkの5分27秒（327秒）からLGY追加分を減算
# LGY追加により総K値が増加するため、約8%短縮と推定
ink2_exposure_sec = 5 * 60 + 27  # 327秒
exposure_reduction_pct = 8
ink3_exposure_sec = ink2_exposure_sec * (1 - exposure_reduction_pct / 100)
exposure_min = int(ink3_exposure_sec // 60)
exposure_sec = int(ink3_exposure_sec % 60)

print(f"  2ink: 5分27秒")
print(f"  3ink: {exposure_min}分{exposure_sec:02d}秒 (-{exposure_reduction_pct}%)")

# ===== .quadファイル生成 =====
print("\n[Step 6] Quadファイルを生成中...")

quad_content = f"""## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-3ink
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Triple ink configuration: K + GY(LK) + LGY(LLK)
# - GY channel (LK, gradation):
#   - Zone 1 (0-24): 175 K/step
#   - Zone 2 (25-240): 115 K/step
#   - Zone 3 (241-254): 300 K/step
#   - Input 255: 0
# - K channel (density base):
#   - Input 0-254: 30 K/step
#   - Input 255: 40000 (paper white)
# - LGY channel (LLK, fine gradation):
#   - Input 0-254: 10 K/step
#   - Input 255: 0
# - Exposure: {exposure_min}:{exposure_sec:02d} (2ink's 5:27 reduced by {exposure_reduction_pct}%)
# - Target: Paper white (D=0.09) at Input 255
# - Benefit: Rich gradation (GY) + density base (K) + fine detail (LGY) + maximum dithering reduction
# Generated: 2026-04-05 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# 3ink: K (density base) + GY (gradation) + LGY (fine gradation)
#
# K curve
"""

for k in k_values_3ink:
    quad_content += f"{k}\n"
quad_content += "#\n"

# C, M, Y, LC, LM (全て0)
for channel in ['C', 'M', 'Y', 'LC', 'LM']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# LK (GY): ゾーン勾配
quad_content += "# LK curve\n"
for gy in gy_values:
    quad_content += f"{gy}\n"
quad_content += "#\n"

# LLK (LGY): 10 K/step
quad_content += "# LLK curve\n"
for lgy in lgy_values:
    quad_content += f"{lgy}\n"
quad_content += "#\n"

# V, MK (全て0)
for channel in ['V', 'MK']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# 保存
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-3ink.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ 3inkカーブ生成完了: {output_path}")

# ===== ファイル整合性確認 =====
print(f"\n[Step 7] ファイル整合性確認")
file_size = os.path.getsize(output_path)
with open(output_path, 'r') as f:
    line_count = len(f.readlines())

print(f"ファイルサイズ: {file_size} bytes")
print(f"総行数: {line_count} 行")

# ===== CSV出力 =====
print(f"\n[Step 8] CSV出力")

csv_path = output_path.replace('.quad', '_values.csv')
with open(csv_path, 'w', encoding='utf-8') as f:
    f.write("Input,K,GY,LGY,Total,K_percent,GY_percent,LGY_percent\n")
    for i in range(256):
        total = k_values_3ink[i] + gy_values[i] + lgy_values[i]
        k_pct = (k_values_3ink[i] / total * 100) if total > 0 else 0
        gy_pct = (gy_values[i] / total * 100) if total > 0 else 0
        lgy_pct = (lgy_values[i] / total * 100) if total > 0 else 0
        f.write(f"{i},{k_values_3ink[i]},{gy_values[i]},{lgy_values[i]},{total},{k_pct:.2f},{gy_pct:.2f},{lgy_pct:.2f}\n")

print(f"✓ CSV出力完了: {csv_path}")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"PX1V-PtPd-xf1-3ink カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ GY channel (LK, 階調担当):")
print(f"    - Zone 1 (0-24): 175 K/step")
print(f"    - Zone 2 (25-240): 115 K/step")
print(f"    - Zone 3 (241-254): 300 K/step")
print(f"    - Input 255: 0")
print(f"  ✓ K channel (濃度ベース):")
print(f"    - Input 0-254: 30 K/step")
print(f"    - Input 255: 40000 (紙白確実到達)")
print(f"  ✓ LGY channel (LLK, 微細階調):")
print(f"    - Input 0-254: 10 K/step")
print(f"    - Input 255: 0")
print(f"  ✓ 露光時間: {exposure_min}分{exposure_sec:02d}秒 (2inkから-{exposure_reduction_pct}%)")
print(f"\n【効果】")
print(f"  1. 豊かな階調（GYで表現）")
print(f"  2. 濃度ベース確保（K=30/step）")
print(f"  3. 微細階調補完（LGY=10/step）")
print(f"  4. 紙白確実到達（K[255]=40000）")
print(f"  5. 最大限のディザリングパターン解消（K+GY+LGY混合）")
print(f"\n【インク配分（主要ポイント）】")
for i in [0, 24, 128, 240, 254, 255]:
    k = k_values_3ink[i]
    gy = gy_values[i]
    lgy = lgy_values[i]
    total = k + gy + lgy
    k_pct = (k / total * 100) if total > 0 else 0
    lgy_pct = (lgy / total * 100) if total > 0 else 0
    print(f"  Input {i:3}: K={k:5}, GY={gy:5}, LGY={lgy:4}, Total={total:5} (K={k_pct:4.1f}%, LGY={lgy_pct:4.1f}%)")
print(f"\n【2inkとの比較】")
print(f"  2ink: K + GY (2インク)")
print(f"  3ink: K + GY + LGY (3インク、LGY追加で微細階調強化)")
print(f"\n【次のステップ】")
print(f"1. 3inkをQTRにインストール")
print(f"2. {exposure_min}分{exposure_sec:02d}秒露光でテストプリント")
print(f"3. 2inkと階調・ディザリングを比較")
print(f"{'=' * 80}")
