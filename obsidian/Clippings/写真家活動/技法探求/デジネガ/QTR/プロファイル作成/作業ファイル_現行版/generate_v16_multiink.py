#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v16-multiink QTRカーブ生成
バンディング対策版: 指定K値 + GY/LGY各2%

設計コンセプト:
- K値: ユーザー指定の33ポイント値を使用（Input 0, 8-240を8ステップ, 248, 255）
- GY値（グレー）: K値の2%を全階調で追加 → LKチャンネル
- LGY値（ライトグレー）: K値の2%を全階調で追加 → LLKチャンネル
- 目的: Kインク単色使用によるディザリングパターンの穴を埋め、バンディングを軽減
- UV透過量: 若干増加（約104%）するが、露光時間で調整可能

期待される効果:
- 横線（バンディング）の軽減
- より滑らかなグラデーション
- K単色の露光特性をほぼ維持
- v16（3%）より控えめな追加量

Generated: 2026-04-02
"""
import numpy as np
from scipy import interpolate

print("=" * 80)
print("v16-multiink Multi-ink カーブ生成開始")
print("バンディング対策: 指定K値 + GY 2% + LGY 2%")
print("=" * 80)

# ===== ユーザー指定のK値（33ポイント） =====
print("\n[Step 1] ユーザー指定のK値を読み込み")

# K値（ユーザー指定）- 33個
# Input 0, 8-240を8ステップ, 248, 255（33ポイント）: 0, 8, 16,...,232, 240, 248, 255
specified_k_values = [
    0, 960, 1920, 2880, 3864, 4864, 5864, 6864, 7864, 8864, 9864,
    10864, 11864, 12864, 13864, 14864, 15864, 16864, 17864, 18864, 19864,
    20864, 21864, 22864, 23864, 24864, 25816, 26712, 27544, 28304, 29064, 29752, 30440
]

# Input値: 0, 8-240を8ステップ, 248, 255（33ポイント）
specified_inputs = [0] + list(range(8, 241, 8)) + [248, 255]  # 0, 8, 16,...,232, 240, 248, 255 (33ポイント)

print(f"✓ 指定ポイント数: {len(specified_inputs)} points")
print(f"  Input範囲: {specified_inputs[0]}-{specified_inputs[-1]}")
print(f"  K値範囲: {specified_k_values[0]}-{specified_k_values[-1]}")

# ===== 256ポイントに補間 =====
print("\n[Step 2] 256ポイントに補間（cubic）")

# 補間関数を作成
f_interp = interpolate.interp1d(
    specified_inputs,
    specified_k_values,
    kind='cubic',
    fill_value='extrapolate'
)

# 全256ポイントのK値を生成
all_inputs = np.arange(256)
k_values_float = f_interp(all_inputs)
k_values = [round(float(k)) for k in k_values_float]

print(f"✓ 補間完了: {len(k_values)} values")
print(f"  K[0] = {k_values[0]}")
print(f"  K[128] = {k_values[128]}")
print(f"  K[255] = {k_values[255]}")

# ===== 単調増加を保証 =====
print("\n[Step 3] 単調増加を保証")

violations = 0
for i in range(1, 256):
    if k_values[i] <= k_values[i-1]:
        violations += 1
        k_values[i] = k_values[i-1] + 1

if violations == 0:
    print("✓ 単調増加保証: 完璧（修正不要）")
else:
    print(f"✓ 単調増加保証: {violations}箇所を修正")

# ===== GY/LGY値を計算（K値の2%） =====
print("\n[Step 4] GY/LGY値を計算（K値の2%）")

gy_values = []   # グレー（LKチャンネル）
lgy_values = []  # ライトグレー（LLKチャンネル）

for k in k_values:
    gy = round(k * 0.02)   # K値の2%
    lgy = round(k * 0.02)  # K値の2%
    gy_values.append(gy)
    lgy_values.append(lgy)

print(f"✓ GY/LGY値計算完了")
print(f"  GY[0] = {gy_values[0]} (K[0]の2%, LKチャンネル)")
print(f"  GY[128] = {gy_values[128]} (K[128]の2%, LKチャンネル)")
print(f"  GY[255] = {gy_values[255]} (K[255]の2%, LKチャンネル)")
print(f"  LGY[0] = {lgy_values[0]} (K[0]の2%, LLKチャンネル)")
print(f"  LGY[128] = {lgy_values[128]} (K[128]の2%, LLKチャンネル)")
print(f"  LGY[255] = {lgy_values[255]} (K[255]の2%, LLKチャンネル)")

# ===== 合計インク量の確認 =====
print("\n[Step 5] 合計インク量の確認")

total_values = []
for i in range(256):
    total = k_values[i] + gy_values[i] + lgy_values[i]
    total_values.append(total)

# サンプルポイントで確認
sample_points = [0, 64, 128, 192, 240, 248, 255]
print(f"\nInput | K      | GY    | LGY   | 合計   | 対v14比")
print(f"------|--------|-------|-------|--------|--------")
for inp in sample_points:
    k = k_values[inp]
    gy = gy_values[inp]
    lgy = lgy_values[inp]
    total = total_values[inp]
    ratio = (total / k * 100) if k > 0 else 100.0
    print(f"{inp:5} | {k:6} | {gy:5} | {lgy:5} | {total:6} | {ratio:6.2f}%")

print(f"\n✓ 全階調で約104%のインク量（K 100% + GY 2% + LGY 2%）")
print(f"  → UV透過量が若干減少（ネガが少し濃くなる）")
print(f"  → v16（106%）より控えめな設定")

# ===== .quadファイル生成 =====
print("\n[Step 6] Quadファイルを生成中...")

quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v16-multiink-multiink
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Base curve: User-specified K values (31 points, cubic interpolation)
# - Multi-ink banding reduction: K 100% + GY 2% + LGY 2%
# - Purpose: Fill dithering pattern gaps to reduce horizontal banding
# - Total ink: ~104% (slightly denser negative, less than v16)
# - UV transmission: Slightly reduced, adjust exposure time if needed
# - Exposure: 6.4-6.5min推奨 (v14より若干短縮)
# Generated: 2026-04-02 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
# Multi-ink anti-banding configuration (2% GY/LGY)
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
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v16-multiink-multiink.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v16-multiink-multiinkカーブ生成完了: {output_path}")

# ===== ファイル整合性確認 =====
print(f"\n[Step 7] ファイル整合性確認")
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
channel_count = len([l for l in channel_lines if 'curve' in l.lower() and not 'base' in l.lower()])
print(f"チャンネル数: {channel_count}（期待値: 10）")
if channel_count == 10:
    print("✓ 10チャンネル構造: OK")
else:
    print(f"❌ チャンネル数エラー")

# ===== CSVファイル生成 =====
print(f"\n[Step 8] CSV出力（8ステップ単位）")

import csv
csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v16-multiink-multiink_values.csv'

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Input', 'K', 'GY (2%)', 'LGY (2%)', 'Total', 'Total %'])

    for i in range(0, 256, 8):
        k = k_values[i]
        gy = gy_values[i]
        lgy = lgy_values[i]
        total = k + gy + lgy
        total_pct = (total / k * 100) if k > 0 else 100.0
        writer.writerow([i, k, gy, lgy, total, f'{total_pct:.2f}'])

print(f"✓ CSV生成完了: {csv_path}")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v16-multiink-multiink 設計コンセプト")
print(f"{'=' * 80}")
print(f"\n【問題】")
print(f"  K単色印刷でミッドトーン〜ハイライトに等間隔の横線（バンディング）が発生")
print(f"  → 単一ノズルラインの負担集中")
print(f"  → ディザリングパターンの穴が可視化")
print(f"\n【解決策】")
print(f"  K値: ユーザー指定の31ポイント値を使用（cubic補間で256ポイント化）")
print(f"  GY値（グレー）: K値の2%を全階調で追加 → LKチャンネル")
print(f"  LGY値（ライトグレー）: K値の2%を全階調で追加 → LLKチャンネル")
print(f"\n【特徴】")
print(f"  ✓ 階調バランス: 指定K値ベースで維持（全階調で一貫した比率）")
print(f"  ✓ ディザリングパターン: 3つのインクで穴を埋める")
print(f"  ✓ UV透過量: 約104%（v16の106%より控えめ）")
print(f"  ✓ バンディング: 軽減が期待される")
print(f"\n【v16との比較】")
print(f"  v16: K 100% + GY 3% + LGY 3% = 106%")
print(f"  v16-multiink: K 100% + GY 2% + LGY 2% = 104%")
print(f"  → より控えめなインク追加量")
print(f"\n【推奨露光時間】")
print(f"  v14: 6.5分 → v16-multiink-multiink: 6.4-6.5分")
print(f"  （ネガが若干濃くなるため、短縮が必要な場合あり）")
print(f"\n【インクチャンネル配置】")
print(f"  ✓ Kチャンネル → K（ブラック）インク")
print(f"  ✓ LKチャンネル → GY（グレー）インク")
print(f"  ✓ LLKチャンネル → LGY（ライトグレー）インク")
print(f"  ✓ PX-1Vの実装に合わせて設定済み")
print(f"\n【次のステップ】")
print(f"1. QTRプリンタにインストール（ルール8準拠）")
print(f"2. テストプリント（横線が出ていたのと同じファイルで確認）")
print(f"3. フィルムを目視で横線が軽減されているか確認")
print(f"4. v16と比較して効果を評価")
print(f"{'=' * 80}")
