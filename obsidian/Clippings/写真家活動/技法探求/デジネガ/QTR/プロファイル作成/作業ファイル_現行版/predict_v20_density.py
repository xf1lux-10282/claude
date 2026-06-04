#!/usr/bin/env python3
"""
v20予測プリント濃度の計算

v18実測データから確立されたK→濃度の関係を使用して、
v20のK値から予測プリント濃度を計算し、理想濃度v2と比較する。

Generated: 2026-04-03
"""
import pandas as pd
import numpy as np
from scipy import interpolate
import csv

print("=" * 80)
print("v20 予測プリント濃度計算")
print("=" * 80)

# ===== v18実測データの読み込み =====
print("\n[Step 1] v18実測データを読み込み（K→濃度の関係）")

v18_measured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v18_measured_density.csv')

print(f"✓ v18実測データ: {len(v18_measured)} points")
print(f"  K値範囲: {v18_measured['K'].min()} - {v18_measured['K'].max()}")
print(f"  濃度範囲: {v18_measured['Density_measured'].min():.2f} - {v18_measured['Density_measured'].max():.2f}")

# ===== K→濃度の補間関数を作成 =====
print("\n[Step 2] K→濃度の補間関数を作成（v18実測ベース）")

v18_sorted = v18_measured.sort_values('K')
v18_unique = v18_sorted.drop_duplicates(subset='K', keep='first')

f_k_to_density = interpolate.interp1d(
    v18_unique['K'],
    v18_unique['Density_measured'],
    kind='linear',
    fill_value='extrapolate'
)

print(f"✓ 補間関数作成完了: {len(v18_unique)} unique K values")

# ===== v20のK値を読み込み =====
print("\n[Step 3] v20のK値を読み込み")

v20_predicted = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v20_predicted_values.csv')

v20_k_values = v20_predicted['V20_K'].tolist()
specified_inputs = v20_predicted['Input'].tolist()

print(f"✓ v20 K値: {len(v20_k_values)} points")
print(f"  K値範囲: {v20_k_values[0]} - {v20_k_values[-1]}")

# ===== v20の256ポイントに補間 =====
print("\n[Step 4] v20を256ポイントに補間")

f_v20_interp = interpolate.interp1d(
    specified_inputs,
    v20_k_values,
    kind='cubic',
    fill_value='extrapolate'
)

all_inputs = np.arange(256)
v20_k_256 = [round(float(f_v20_interp(i))) for i in all_inputs]

# 単調増加を保証
for i in range(1, 256):
    if v20_k_256[i] <= v20_k_256[i-1]:
        v20_k_256[i] = v20_k_256[i-1] + 1

print(f"✓ 256ポイント補間完了")

# ===== v20予測濃度を計算 =====
print("\n[Step 5] v20予測プリント濃度を計算")

v20_predicted_density = [float(f_k_to_density(k)) for k in v20_k_256]

print(f"✓ 予測濃度計算完了")
print(f"  予測濃度範囲: {min(v20_predicted_density):.3f} - {max(v20_predicted_density):.3f}")

# ===== 理想濃度v2を読み込み =====
print("\n[Step 6] 理想濃度ターゲットv2を読み込み")

target_v2 = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/ideal_density_target_v2.csv')

# 256ポイントに補間
f_target = interpolate.interp1d(
    target_v2['Input'],
    target_v2['Target_Density'],
    kind='linear',
    fill_value='extrapolate'
)

target_density_256 = [float(f_target(i)) for i in all_inputs]

print(f"✓ 理想濃度v2: {len(target_density_256)} points")

# ===== 33ポイントでの詳細比較 =====
print("\n" + "=" * 80)
print("v20 予測プリント濃度 vs 理想濃度v2（33ポイント）")
print("=" * 80)

print("\nInput | K_v20 | 予測濃度 | 理想濃度v2 | 予測誤差")
print("------|-------|----------|------------|----------")

for i in specified_inputs:
    k_v20 = v20_k_256[i]
    pred_density = v20_predicted_density[i]
    target_density = target_density_256[i]
    pred_error = pred_density - target_density

    print(f"{i:5} | {k_v20:5} | {pred_density:8.3f} | {target_density:10.2f} | {pred_error:+8.3f}")

# ===== 統計サマリー =====
print("\n" + "=" * 80)
print("予測誤差の統計（33ポイント）")
print("=" * 80)

pred_errors_33 = [v20_predicted_density[int(i)] - target_density_256[int(i)] for i in specified_inputs]

print(f"\n平均誤差: {np.mean(pred_errors_33):+.4f}")
print(f"最大プラス誤差: {max(pred_errors_33):+.4f} (Input {specified_inputs[pred_errors_33.index(max(pred_errors_33))]})")
print(f"最大マイナス誤差: {min(pred_errors_33):+.4f} (Input {specified_inputs[pred_errors_33.index(min(pred_errors_33))]})")
print(f"標準偏差: {np.std(pred_errors_33):.4f}")

# 誤差が±0.01以内のポイント数
within_001 = sum(1 for e in pred_errors_33 if abs(e) <= 0.01)
within_002 = sum(1 for e in pred_errors_33 if abs(e) <= 0.02)
within_003 = sum(1 for e in pred_errors_33 if abs(e) <= 0.03)

print(f"\n誤差±0.01以内: {within_001}/{len(pred_errors_33)} points ({100*within_001/len(pred_errors_33):.1f}%)")
print(f"誤差±0.02以内: {within_002}/{len(pred_errors_33)} points ({100*within_002/len(pred_errors_33):.1f}%)")
print(f"誤差±0.03以内: {within_003}/{len(pred_errors_33)} points ({100*within_003/len(pred_errors_33):.1f}%)")

# ===== CSV出力 =====
print("\n[Step 7] CSV出力（8ステップ単位 + 255）")

csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v20_predicted_density.csv'

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Input', 'K_v20', 'Predicted_Density', 'Target_Density_v2', 'Predicted_Error'])

    for i in range(0, 256, 8):
        k_v20 = v20_k_256[i]
        pred_density = v20_predicted_density[i]
        target_density = target_density_256[i]
        pred_error = pred_density - target_density

        writer.writerow([i, k_v20, f"{pred_density:.3f}", f"{target_density:.2f}", f"{pred_error:+.3f}"])

    # 255も追加
    i = 255
    k_v20 = v20_k_256[255]
    pred_density = v20_predicted_density[255]
    target_density = target_density_256[255]
    pred_error = pred_density - target_density

    writer.writerow([255, k_v20, f"{pred_density:.3f}", f"{target_density:.2f}", f"{pred_error:+.3f}"])

print(f"✓ CSV生成完了: {csv_path}")

# ===== まとめ =====
print("\n" + "=" * 80)
print("まとめ")
print("=" * 80)
print("\n【v20予測濃度の特徴】")
print("1. v18実測データのK→濃度関係を使用")
print("2. 新しい理想濃度v2（より滑らか）との比較")
print("3. 逆算K値から予測される実際のプリント濃度を算出")

print("\n【判定】")
if abs(np.mean(pred_errors_33)) < 0.01 and within_002/len(pred_errors_33) > 0.9:
    print("✓ 予測プリント濃度は理想濃度v2とほぼ一致しています")
    print("  → v20は理想的なカーブになる可能性が高い")
elif abs(np.mean(pred_errors_33)) < 0.02 and within_003/len(pred_errors_33) > 0.8:
    print("△ 予測プリント濃度は理想濃度v2に近いですが、若干の誤差があります")
    print("  → v20は実用的なカーブになる可能性が高い")
else:
    print("✗ 予測プリント濃度と理想濃度v2に乖離があります")
    print("  → v20実測後に微調整が必要な可能性があります")

print("\n【次のステップ】")
print("1. 予測誤差が許容範囲なら、v20カーブを生成")
print("2. QTRにインストール")
print("3. 6分45秒露光でテストプリント")
print("4. 実測濃度と予測濃度・理想濃度を3者比較")
print("=" * 80)
