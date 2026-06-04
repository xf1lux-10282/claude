#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v15 QTRカーブ生成
バンディング対策版: K単色にLG/GYを少量追加

設計コンセプト:
- K値: v14のK値を100%維持（UV透過量の基準を維持）
- LGY値（ライトグレー）: v14のK値の3%を全階調で追加 → LLKチャンネル
- GY値（グレー）: v14のK値の3%を全階調で追加 → LKチャンネル
- 目的: Kインク単色使用によるディザリングパターンの穴を埋め、バンディングを軽減
- UV透過量: 若干増加（約106%）するが、露光時間で調整可能

期待される効果:
- 横線（バンディング）の軽減
- より滑らかなグラデーション
- K単色の露光特性をほぼ維持

Generated: 2026-04-02
"""
import numpy as np

print("=" * 80)
print("v15 Multi-ink カーブ生成開始")
print("バンディング対策: K 100% + LG 3% + GY 3%")
print("=" * 80)

# ===== v14のK-valuesを再生成 =====
print("\n[Step 1] v14 K-valuesを再生成")

# Zone 1: Shadow (0-24) - v12と同じ
zone1_k_values = []
for i in range(0, 25):
    k = round(4148 * i / 24)
    zone1_k_values.append(k)

# Zone 2: Midtone (24-239) - v12より少し緩やか（115.0 K/step）
zone2_k_start = 4148
target_zone2_grad = 115.0
zone2_steps = 239 - 24  # 215 steps
zone2_k_end = round(zone2_k_start + target_zone2_grad * zone2_steps)

zone2_k_values = []
for i in range(1, zone2_steps + 1):
    k = round(zone2_k_start + target_zone2_grad * i)
    zone2_k_values.append(k)

# Input 240: 指定値
k_240 = 29400

# Input 241-247: 240→248を線形補間
k_248 = 31900

transition_k_values = []
steps_240_to_248 = 8
for i in range(1, steps_240_to_248):  # 241-247
    k = round(k_240 + (k_248 - k_240) * i / steps_240_to_248)
    transition_k_values.append(k)

# Zone 3: Highlight (248-255)
zone3_k_start = k_248
zone3_k_end = 33800
zone3_steps = 7

zone3_k_values = []
for i in range(1, zone3_steps + 1):
    k = round(zone3_k_start + (zone3_k_end - zone3_k_start) * i / zone3_steps)
    zone3_k_values.append(k)

# 全K-values結合
k_values = zone1_k_values + zone2_k_values + [k_240] + transition_k_values + [k_248] + zone3_k_values

print(f"✓ v14 K-values再生成完了: {len(k_values)} values")
print(f"  K[0] = {k_values[0]}")
print(f"  K[128] = {k_values[128]}")
print(f"  K[255] = {k_values[255]}")

# ===== LGY/GY値を計算（K値の3%） =====
print("\n[Step 2] LGY/GY値を計算（K値の3%）")

lgy_values = []  # ライトグレー（LLKチャンネル）
gy_values = []   # グレー（LKチャンネル）

for k in k_values:
    lgy = round(k * 0.03)  # K値の3%
    gy = round(k * 0.03)   # K値の3%
    lgy_values.append(lgy)
    gy_values.append(gy)

print(f"✓ LGY/GY値計算完了")
print(f"  LGY[0] = {lgy_values[0]} (K[0]の3%, LLKチャンネル)")
print(f"  LGY[128] = {lgy_values[128]} (K[128]の3%, LLKチャンネル)")
print(f"  LGY[255] = {lgy_values[255]} (K[255]の3%, LLKチャンネル)")
print(f"  GY[0] = {gy_values[0]} (K[0]の3%, LKチャンネル)")
print(f"  GY[128] = {gy_values[128]} (K[128]の3%, LKチャンネル)")
print(f"  GY[255] = {gy_values[255]} (K[255]の3%, LKチャンネル)")

# ===== 合計インク量の確認 =====
print("\n[Step 3] 合計インク量の確認")

total_values = []
for i in range(256):
    total = k_values[i] + lgy_values[i] + gy_values[i]
    total_values.append(total)

# サンプルポイントで確認
sample_points = [0, 64, 128, 192, 240, 255]
print(f"\nInput | K      | LGY   | GY    | 合計   | 対v14比")
print(f"------|--------|-------|-------|--------|--------")
for inp in sample_points:
    k = k_values[inp]
    lgy = lgy_values[inp]
    gy = gy_values[inp]
    total = total_values[inp]
    ratio = (total / k * 100) if k > 0 else 100.0
    print(f"{inp:5} | {k:6} | {lgy:5} | {gy:5} | {total:6} | {ratio:6.2f}%")

print(f"\n✓ 全階調で約106%のインク量（K 100% + LGY 3% + GY 3%）")
print(f"  → UV透過量が若干減少（ネガが少し濃くなる）")
print(f"  → 露光時間を若干短縮することで調整可能")

# ===== .quadファイル生成 =====
print("\n[Step 4] Quadファイルを生成中...")

quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v15-multiink
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Base curve: v14 (K values unchanged)
# - Multi-ink banding reduction: K 100% + LG 3% + GY 3%
# - Purpose: Fill dithering pattern gaps to reduce horizontal banding
# - Total ink: ~106% (slightly denser negative)
# - UV transmission: Slightly reduced, adjust exposure time if needed
# - Exposure: 6.3-6.5min推奨 (v14より若干短縮)
# Generated: 2026-04-02 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# Multi-ink anti-banding configuration
#
# K curve
"""

for k in k_values:
    quad_content += f"{k}\n"

quad_content += "#\n"

# C, M, Y, LC, LM channels - 全て0
for channel in ['C', 'M', 'Y', 'LC', 'LM']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# LK channel - GY（グレー）として使用
quad_content += "# LK curve\n"
for gy in gy_values:
    quad_content += f"{gy}\n"
quad_content += "#\n"

# LLK channel - LGY（ライトグレー）として使用
quad_content += "# LLK curve\n"
for lgy in lgy_values:
    quad_content += f"{lgy}\n"
quad_content += "#\n"

# V, MK channels - 全て0
for channel in ['V', 'MK']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# 保存
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v15-multiink.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v15-multiinkカーブ生成完了: {output_path}")

# ===== ファイル整合性確認 =====
print(f"\n[Step 5] ファイル整合性確認")
import os
file_size = os.path.getsize(output_path)
with open(output_path, 'r') as f:
    line_count = len(f.readlines())

print(f"ファイルサイズ: {file_size} bytes")
print(f"総行数: {line_count} 行")

# チャンネル確認
import subprocess
result = subprocess.run(['grep', '# .* curve', output_path], capture_output=True, text=True)
channel_lines = result.stdout.strip().split('\n')
print(f"チャンネル数: {len(channel_lines)}（期待値: 10）")
if len(channel_lines) == 10:
    print("✓ 10チャンネル構造: OK")
else:
    print(f"❌ チャンネル数エラー")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v15-multiink 設計コンセプト")
print(f"{'=' * 80}")
print(f"\n【問題】")
print(f"  K単色印刷でミッドトーン〜ハイライトに等間隔の横線（バンディング）が発生")
print(f"  → 単一ノズルラインの負担集中")
print(f"  → ディザリングパターンの穴が可視化")
print(f"\n【解決策】")
print(f"  K値: v14のまま100%維持（露光特性の基準を保持）")
print(f"  LGY値（ライトグレー）: K値の3%を全階調で追加 → LLKチャンネル")
print(f"  GY値（グレー）: K値の3%を全階調で追加 → LKチャンネル")
print(f"\n【特徴】")
print(f"  ✓ 階調バランス: v14と同じ（全階調で一貫した比率）")
print(f"  ✓ ディザリングパターン: 3つのインクで穴を埋める")
print(f"  ✓ UV透過量: 約106%（v14比、露光時間で調整可能）")
print(f"  ✓ バンディング: 大幅に軽減される見込み")
print(f"\n【推奨露光時間】")
print(f"  v14: 6.5分 → v15-multiink: 6.3-6.5分")
print(f"  （ネガが若干濃くなるため、短縮が必要な場合あり）")
print(f"\n【インクチャンネル配置】")
print(f"  ✓ Kチャンネル → K（ブラック）インク")
print(f"  ✓ LKチャンネル → GY（グレー）インク")
print(f"  ✓ LLKチャンネル → LGY（ライトグレー）インク")
print(f"  ✓ PX-1Vの実装に合わせて設定済み")
print(f"\n【次のステップ】")
print(f"1. QTRプリンタにインストール")
print(f"2. テストプリント（横線が出ていたのと同じファイルで確認）")
print(f"3. フィルムを目視で横線が軽減されているか確認")
print(f"4. Pt/Pdプリントで濃度変化を確認（必要に応じて露光時間調整）")
print(f"{'=' * 80}")
