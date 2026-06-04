#!/usr/bin/env python3
"""
v19予測プリント濃度の計算

v18実測データから確立されたK→濃度の関係を使用して、
v19のK値から予測プリント濃度を計算する。

Generated: 2026-04-03
"""
import pandas as pd
import numpy as np
from scipy import interpolate
import csv

print("=" * 80)
print("v19 予測プリント濃度計算")
print("=" * 80)

# ===== v18実測データの読み込み =====
print("\n[Step 1] v18実測データを読み込み")

v18_measured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v18_measured_density.csv')

print(f"✓ v18実測データ: {len(v18_measured)} points")
print(f"  K値範囲: {v18_measured['K'].min()} - {v18_measured['K'].max()}")
print(f"  濃度範囲: {v18_measured['Density_measured'].min():.2f} - {v18_measured['Density_measured'].max():.2f}")

# ===== K→濃度の補間関数を作成 =====
print("\n[Step 2] K→濃度の補間関数を作成（v18実測ベース）")

# K値でソートして重複を除去
v18_sorted = v18_measured.sort_values('K')
v18_unique = v18_sorted.drop_duplicates(subset='K', keep='first')

# K→濃度の補間関数（linear補間で安定性を確保）
f_k_to_density = interpolate.interp1d(
    v18_unique['K'],
    v18_unique['Density_measured'],
    kind='linear',
    fill_value='extrapolate'
)

print(f"✓ 補間関数作成完了: {len(v18_unique)} unique K values")

# ===== v19のK値を読み込み =====
print("\n[Step 3] v19のK値を読み込み")

# v19の33ポイント値（generate_v19.pyから）
v18_k_values = [
    0, 2400, 3372, 4864, 5264, 6197, 7531, 9031, 9864, 10864, 11364,
    11864, 12489, 13364, 14293, 15007, 15721, 16435, 17086, 17642, 18614, 19664,
    20531, 21364, 22531, 23364, 23864, 24864, 25499, 26264, 27128, 28304, 29752
]

v19_k_values = v18_k_values.copy()

# 調整を適用
adjustments = {
    6: -200,   # Input 48
    7: -400,   # Input 56
    14: +200,  # Input 112
    16: +150,  # Input 128
    21: -300,  # Input 168
    24: -400,  # Input 192
    32: -500   # Input 255
}

for idx, delta in adjustments.items():
    v19_k_values[idx] = v18_k_values[idx] + delta

specified_inputs = [0] + list(range(8, 241, 8)) + [248, 255]

print(f"✓ v19 K値: {len(v19_k_values)} points")
print(f"  K値範囲: {v19_k_values[0]} - {v19_k_values[-1]}")

# ===== v19の256ポイントに補間 =====
print("\n[Step 4] v19を256ポイントに補間")

f_v19_interp = interpolate.interp1d(
    specified_inputs,
    v19_k_values,
    kind='cubic',
    fill_value='extrapolate'
)

all_inputs = np.arange(256)
v19_k_256 = [round(float(f_v19_interp(i))) for i in all_inputs]

# 単調増加を保証
for i in range(1, 256):
    if v19_k_256[i] <= v19_k_256[i-1]:
        v19_k_256[i] = v19_k_256[i-1] + 1

print(f"✓ 256ポイント補間完了")

# ===== v19予測濃度を計算 =====
print("\n[Step 5] v19予測プリント濃度を計算")

v19_predicted_density = [float(f_k_to_density(k)) for k in v19_k_256]

print(f"✓ 予測濃度計算完了")
print(f"  予測濃度範囲: {min(v19_predicted_density):.3f} - {max(v19_predicted_density):.3f}")

# ===== 理想濃度を読み込み =====
print("\n[Step 6] 理想濃度ターゲットを読み込み")

target_df = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/ideal_density_target.csv')

# 256ポイントに補間
f_target = interpolate.interp1d(
    target_df['Input'],
    target_df['Target_Density'],
    kind='linear',
    fill_value='extrapolate'
)

target_density_256 = [float(f_target(i)) for i in all_inputs]

print(f"✓ 理想濃度: {len(target_density_256)} points")

# ===== CSV出力（8ステップ単位） =====
print("\n[Step 7] CSV出力（8ステップ単位 + 255）")

csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v19_predicted_density.csv'

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Input', 'K_v19', 'K_v18', 'K_diff', 'Predicted_Density', 'Target_Density', 'Predicted_Error'])

    for i in range(0, 256, 8):
        k_v19 = v19_k_256[i]
        k_v18 = int(f_v19_interp.x[np.searchsorted(f_v19_interp.x, i, side='right')-1]) if i in specified_inputs else v19_k_256[i]

        # v18の補間値を取得
        f_v18_interp = interpolate.interp1d(specified_inputs, v18_k_values, kind='cubic', fill_value='extrapolate')
        k_v18_actual = round(float(f_v18_interp(i)))

        k_diff = k_v19 - k_v18_actual
        pred_density = v19_predicted_density[i]
        target_density = target_density_256[i]
        pred_error = pred_density - target_density

        writer.writerow([i, k_v19, k_v18_actual, k_diff, f"{pred_density:.3f}", f"{target_density:.2f}", f"{pred_error:+.3f}"])

    # 255も追加
    i = 255
    k_v19 = v19_k_256[255]
    k_v18_actual = round(float(f_v18_interp(255)))
    k_diff = k_v19 - k_v18_actual
    pred_density = v19_predicted_density[255]
    target_density = target_density_256[255]
    pred_error = pred_density - target_density

    writer.writerow([255, k_v19, k_v18_actual, k_diff, f"{pred_density:.3f}", f"{target_density:.2f}", f"{pred_error:+.3f}"])

print(f"✓ CSV生成完了: {csv_path}")

# ===== 主要ポイントの予測を表示 =====
print("\n" + "=" * 80)
print("v19 予測プリント濃度（主要ポイント）")
print("=" * 80)

print("\nInput | K_v19 | K_v18 | K差分 | 予測濃度 | 理想濃度 | 予測誤差")
print("------|-------|-------|-------|----------|----------|----------")

key_points = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 168, 176, 184, 192, 208, 224, 240, 248, 255]

for i in key_points:
    k_v19 = v19_k_256[i]
    k_v18_actual = round(float(f_v18_interp(i)))
    k_diff = k_v19 - k_v18_actual
    pred_density = v19_predicted_density[i]
    target_density = target_density_256[i]
    pred_error = pred_density - target_density

    # 調整箇所をマーク
    marker = ""
    if i in [specified_inputs[idx] for idx in adjustments.keys()]:
        marker = " ←調整"

    print(f"{i:5} | {k_v19:5} | {k_v18_actual:5} | {k_diff:+5} | {pred_density:8.3f} | {target_density:8.2f} | {pred_error:+8.3f}{marker}")

# ===== 統計サマリー =====
print("\n" + "=" * 80)
print("予測誤差の統計")
print("=" * 80)

pred_errors = [v19_predicted_density[i] - target_density_256[i] for i in range(256)]

print(f"\n平均誤差: {np.mean(pred_errors):+.4f}")
print(f"最大プラス誤差: {max(pred_errors):+.4f} (Input {pred_errors.index(max(pred_errors))})")
print(f"最大マイナス誤差: {min(pred_errors):+.4f} (Input {pred_errors.index(min(pred_errors))})")
print(f"標準偏差: {np.std(pred_errors):.4f}")

# v18との比較
v18_errors = v18_measured['Density_diff'].values
print(f"\n【v18実測との比較】")
print(f"v18平均誤差: {np.mean(v18_errors):+.4f}")
print(f"v19予測平均誤差: {np.mean(pred_errors):+.4f}")

# ===== まとめ =====
print("\n" + "=" * 80)
print("まとめ")
print("=" * 80)
print("\n【v19予測濃度の特徴】")
print("1. v18実測データのK→濃度関係を使用")
print("2. v19の7箇所の調整が濃度カーブに与える影響を予測")
print("3. 理想濃度との予測誤差を事前に把握")

print("\n【次のステップ】")
print("1. 予測誤差が許容範囲内か確認")
print("2. v19をインストール済み（/Library/Printers/QTR/quadtone/QuadP700/）")
print("3. 6分45秒露光でテストプリント")
print("4. 実測濃度と予測濃度を比較")
print("=" * 80)
