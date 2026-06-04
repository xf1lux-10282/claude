#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v29-doubleink-3 QTRカーブ生成
K + GY ダブルインク構成（K値さらに強化版）

設計:
- GY channel (LK, 階調担当):
  - v29のK値と完全に同じ
  - Zone 1 (0-24): 175 K/step
  - Zone 2 (25-240): 115 K/step
  - Zone 3 (241-254): 300 K/step
  - Input 255: 0

- K channel (濃度ベース):
  - Input 0-254: 50 K/step (v29-doubleink-2の30 K/stepから1.67倍)
  - Input 255: 40000 (紙白確実到達)

狙い:
- GYでv29と同じ豊かな階調を確保
- Kをさらに強化（50 K/step）して濃度ベースをより増強
- ディザリングパターン解消

Generated: 2026-04-04
"""
import numpy as np

print("=" * 80)
print("v29-doubleink-3 カーブ生成開始")
print("=" * 80)

# ===== v29のK値を読み込み =====
print("\n[Step 1] v29のK値を読み込み")

v29_quad_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v29.quad'

v29_k_values = []
with open(v29_quad_path, 'r') as f:
    in_k_section = False
    for line in f:
        line = line.strip()
        if line == '# K curve':
            in_k_section = True
            continue
        if in_k_section:
            if line.startswith('#'):
                break
            if line and not line.startswith('#'):
                v29_k_values.append(int(line))

print(f"✓ v29 K値読み込み完了: {len(v29_k_values)} values")

# ===== GY値生成（v29のK値と完全に同じ）=====
print("\n[Step 2] GY値を設定（v29のK値と同じ）")

gy_values = []

# Input 0-254: v29のK値と同じ
for i in range(255):
    gy_values.append(v29_k_values[i])

# Input 255: 0
gy_values.append(0)

print(f"✓ GY値設定完了: {len(gy_values)} values")
print(f"  GY[0] = {gy_values[0]}")
print(f"  GY[24] = {gy_values[24]}")
print(f"  GY[254] = {gy_values[254]}")
print(f"  GY[255] = {gy_values[255]}")

# ===== K値生成（0-254は50 K/step）=====
print("\n[Step 3] K値を計算（0-254は50 K/step）")

k_values_doubleink3 = []

# Input 0-254: 50 K/step
for i in range(255):
    k_values_doubleink3.append(i * 50)

# Input 255: 40000 (紙白確実到達)
k_values_doubleink3.append(40000)

print(f"✓ K値計算完了: {len(k_values_doubleink3)} values")
print(f"  K[0] = {k_values_doubleink3[0]}")
print(f"  K[24] = {k_values_doubleink3[24]}")
print(f"  K[240] = {k_values_doubleink3[240]}")
print(f"  K[254] = {k_values_doubleink3[254]}")
print(f"  K[255] = {k_values_doubleink3[255]}")

# ===== 主要ポイントの確認 =====
print("\n[Step 4] 主要ポイントの確認")
print(f"Input |     K | GY (LK) | 合計 | K% | 備考")
print(f"------|-------|---------|------|-----|-----")
for i in [0, 8, 24, 25, 48, 128, 240, 241, 254, 255]:
    total = k_values_doubleink3[i] + gy_values[i]
    k_pct = (k_values_doubleink3[i] / total * 100) if total > 0 else 0
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
    print(f"{i:5} | {k_values_doubleink3[i]:5} | {gy_values[i]:7} | {total:5} | {k_pct:4.1f} | {note}")

# ===== 露光時間の計算 =====
print("\n[Step 5] 露光時間の計算")

# v29と同じGY、Kが50/stepなので、露光時間はさらに短縮
# 概算: v29の6分04秒から約15%短縮
v29_exposure_sec = 6 * 60 + 4  # 364秒
exposure_reduction_pct = 15
doubleink3_exposure_sec = v29_exposure_sec * (1 - exposure_reduction_pct / 100)
exposure_min = int(doubleink3_exposure_sec // 60)
exposure_sec = int(doubleink3_exposure_sec % 60)

print(f"  v29: 6分04秒")
print(f"  v29-doubleink-3: {exposure_min}分{exposure_sec:02d}秒 (-{exposure_reduction_pct}%)")

# ===== .quadファイル生成 =====
print("\n[Step 6] Quadファイルを生成中...")

quad_content = f"""## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v29-doubleink-3
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Double ink configuration: K + GY(LK), K further enhanced
# - GY channel (LK, gradation):
#   - Input 0-254: Same as v29's K values
#   - Zone 1 (0-24): 175 K/step
#   - Zone 2 (25-240): 115 K/step
#   - Zone 3 (241-254): 300 K/step
#   - Input 255: 0
# - K channel (density base):
#   - Input 0-254: 50 K/step (5x of v29-doubleink's 10 K/step)
#   - Input 255: 40000 (paper white)
# - Exposure: {exposure_min}:{exposure_sec:02d} (v29's 6:04 reduced by {exposure_reduction_pct}%)
# - Target: Paper white (D=0.09) at Input 255
# - Benefit: Rich gradation (GY=v29) + strongest density base (K=50/step)
# Generated: 2026-04-04 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# Double ink K max enhanced: GY (v29 gradation) + K (50/step density)
#
# K curve
"""

for k in k_values_doubleink3:
    quad_content += f"{k}\n"
quad_content += "#\n"

# C, M, Y, LC, LM (全て0)
for channel in ['C', 'M', 'Y', 'LC', 'LM']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# LK (GY): v29のK値と同じ
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
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v29-doubleink-3.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v29-doubleink-3カーブ生成完了: {output_path}")

# ===== ファイル整合性確認 =====
print(f"\n[Step 7] ファイル整合性確認")
import os
file_size = os.path.getsize(output_path)
with open(output_path, 'r') as f:
    line_count = len(f.readlines())

print(f"ファイルサイズ: {file_size} bytes")
print(f"総行数: {line_count} 行")

# ===== CSV出力 =====
print(f"\n[Step 8] CSV出力")

csv_path = output_path.replace('.quad', '_values.csv')
with open(csv_path, 'w', encoding='utf-8') as f:
    f.write("Input,K,GY,Total,K_percent,GY_percent,K_step_size\n")
    for i in range(256):
        total = k_values_doubleink3[i] + gy_values[i]
        k_pct = (k_values_doubleink3[i] / total * 100) if total > 0 else 0
        gy_pct = (gy_values[i] / total * 100) if total > 0 else 0
        k_step = "50/step" if i <= 254 else "40000"
        f.write(f"{i},{k_values_doubleink3[i]},{gy_values[i]},{total},{k_pct:.2f},{gy_pct:.2f},{k_step}\n")

print(f"✓ CSV出力完了: {csv_path}")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v29-doubleink-3 カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ GY channel (LK, 階調担当):")
print(f"    - Input 0-254: v29のK値と同じ")
print(f"    - Zone 1 (0-24): 175 K/step")
print(f"    - Zone 2 (25-240): 115 K/step")
print(f"    - Zone 3 (241-254): 300 K/step")
print(f"    - Input 255: 0")
print(f"  ✓ K channel (濃度ベース):")
print(f"    - Input 0-254: 50 K/step (v29-doubleinkの5倍)")
print(f"    - Input 255: 40000 (紙白確実到達)")
print(f"  ✓ 露光時間: {exposure_min}分{exposure_sec:02d}秒 (v29から-{exposure_reduction_pct}%)")
print(f"\n【効果】")
print(f"  1. v29と同じ豊かな階調（GYで表現）")
print(f"  2. 濃度ベース最強化（K=50/step、v29-doubleinkの5倍）")
print(f"  3. 紙白確実到達（K[255]=40000）")
print(f"  4. ディザリングパターン解消（K+GY混合）")
print(f"\n【doubleinkシリーズ比較】")
print(f"  v29-doubleink:   GY=v29, K=10/step")
print(f"  v29-doubleink-2: GY=v29, K=30/step (3倍)")
print(f"  v29-doubleink-3: GY=v29, K=50/step (5倍)")
print(f"\n【インク配分（主要ポイント）】")
for i in [0, 24, 128, 240, 254, 255]:
    k = k_values_doubleink3[i]
    gy = gy_values[i]
    total = k + gy
    k_pct = (k / total * 100) if total > 0 else 0
    print(f"  Input {i:3}: K={k:5}, GY={gy:5}, Total={total:5} (K={k_pct:4.1f}%)")
print(f"\n【次のステップ】")
print(f"1. v29-doubleink-3をQTRにインストール")
print(f"2. {exposure_min}分{exposure_sec:02d}秒露光でテストプリント")
print(f"3. v29-doubleink, v29-doubleink-2と濃度を比較")
print(f"{'=' * 80}")
