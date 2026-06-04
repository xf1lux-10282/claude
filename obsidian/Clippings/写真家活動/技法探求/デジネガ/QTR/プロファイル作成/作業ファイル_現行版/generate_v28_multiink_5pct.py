#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v28-multiink-5pct QTRカーブ生成
v28ベース + GY/LGY 5%混合

設計:
- K値: v28と同じ（v26の0-254 + K[255]=40000）
- GY: K値の5%
- LGY: K値の5%
- 狙い: ディザリングパターン解消強化（3%で不十分だった場合）

Generated: 2026-04-04
"""
import numpy as np

print("=" * 80)
print("v28 マルチインク（GY+LGY 5%混合）カーブ生成開始")
print("=" * 80)

# ===== v28のK値を読み込み =====
print("\n[Step 1] v28のK値を読み込み")

# v28.quadから読み込み
v28_quad_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v28.quad'

k_values = []
with open(v28_quad_path, 'r') as f:
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
                k_values.append(int(line))

print(f"✓ v28 K値読み込み完了: {len(k_values)} values")
print(f"  K[0] = {k_values[0]}")
print(f"  K[8] = {k_values[8]}")
print(f"  K[255] = {k_values[255]}")

# ===== GY/LGYカーブ生成 =====
print("\n[Step 2] GY/LGYカーブを計算（K値の5%）")

gy_values = []
lgy_values = []

for k in k_values:
    # K値の5%をGYとLGYに配分
    gy = round(k * 0.05)
    lgy = round(k * 0.05)
    gy_values.append(gy)
    lgy_values.append(lgy)

print(f"✓ GY/LGY計算完了: {len(gy_values)} values")
print(f"\n主要ポイントの確認:")
print(f"Input |    K | GY (5%) | LGY (5%)")
print(f"------|------|---------|----------")
for i in [0, 8, 24, 48, 128, 192, 240, 255]:
    print(f"{i:5} | {k_values[i]:4} | {gy_values[i]:7} | {lgy_values[i]:8}")

# ===== .quadファイル生成 =====
print("\n[Step 3] Quadファイルを生成中...")

quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v28-multiink-5pct
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - v28 base (v26's 0-254 + K[255]=40000)
# - Multi-ink: GY + LGY each 5% of K (increased from 3%)
# - Dithering pattern reduction (stronger)
# - Exposure: 6:05 (reduced 40s from v26's 6:45, -10%)
# - Target: Paper white (D=0.09) at Input 255
# Generated: 2026-04-04 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# v28 base + GY/LGY 5% each
#
# K curve
"""

for k in k_values:
    quad_content += f"{k}\n"
quad_content += "#\n"

# C, M, Y, LC, LM (全て0)
for channel in ['C', 'M', 'Y', 'LC', 'LM']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# LK (GY): K値の5%
quad_content += "# LK curve\n"
for gy in gy_values:
    quad_content += f"{gy}\n"
quad_content += "#\n"

# LLK (LGY): K値の5%
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
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v28-multiink-5pct.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v28-multiink-5pctカーブ生成完了: {output_path}")

# ===== ファイル整合性確認 =====
print(f"\n[Step 4] ファイル整合性確認")
import os
file_size = os.path.getsize(output_path)
with open(output_path, 'r') as f:
    line_count = len(f.readlines())

print(f"ファイルサイズ: {file_size} bytes")
print(f"総行数: {line_count} 行")

# ===== CSV出力 =====
print(f"\n[Step 5] CSV出力")

csv_path = output_path.replace('.quad', '_values.csv')
with open(csv_path, 'w', encoding='utf-8') as f:
    f.write("Input,K,GY,LGY,GY_percent,LGY_percent\n")
    for i in range(256):
        gy_pct = (gy_values[i] / k_values[i] * 100) if k_values[i] > 0 else 0
        lgy_pct = (lgy_values[i] / k_values[i] * 100) if k_values[i] > 0 else 0
        f.write(f"{i},{k_values[i]},{gy_values[i]},{lgy_values[i]},{gy_pct:.2f},{lgy_pct:.2f}\n")

print(f"✓ CSV出力完了: {csv_path}")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v28-multiink-5pct カーブ完成")
print(f"{'=' * 80}")
print(f"\n【仕様】")
print(f"  ✓ K値: v28と同一（v26の0-254 + K[255]=40000）")
print(f"  ✓ GY: K値の5%（LK チャンネル）← 3%から増量")
print(f"  ✓ LGY: K値の5%（LLK チャンネル）← 3%から増量")
print(f"  ✓ 露光時間: 6分05秒（v26の6分45秒から-40秒、-10%）")
print(f"\n【効果】")
print(f"  1. v28と同じ濃度バランス（紙白到達）")
print(f"  2. ディザリングパターン解消強化（3%→5%）")
print(f"  3. 暖色傾向やや強まる")
print(f"\n【インク配分（主要ポイント）】")
print(f"  Input   0: K=    0, GY=   0, LGY=   0")
print(f"  Input   8: K= 2520, GY= 126, LGY= 126 (3%時: 76)")
print(f"  Input 128: K=16380, GY= 819, LGY= 819 (3%時: 491)")
print(f"  Input 255: K=40000, GY=2000, LGY=2000 (3%時: 1200)")
print(f"\n【次のステップ】")
print(f"1. v28-multiink-5pctをQTRにインストール")
print(f"2. 6分05秒露光でテストプリント")
print(f"3. 3%版と比較してディザリング改善を評価")
print(f"{'=' * 80}")
