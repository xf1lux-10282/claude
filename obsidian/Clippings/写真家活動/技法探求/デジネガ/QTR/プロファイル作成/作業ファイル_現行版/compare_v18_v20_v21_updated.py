#!/usr/bin/env python3
"""
v18、v20、v21（最適化版）の詳細比較CSV生成

v21は実測データベースで最適化されたバージョン

Generated: 2026-04-03
"""
import pandas as pd
import numpy as np
from scipy import interpolate
import csv

print("=" * 80)
print("v18、v20、v21（最適化版）の詳細比較CSV生成")
print("=" * 80)

# ===== データ読み込み =====
print("\n[Step 1] データを読み込み")

v18_remeasured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v18_remeasured_density.csv')
v20_measured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v20_measured_density.csv')
v21_optimized = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v21_optimized_values.csv')

print(f"✓ v18再測定データ: {len(v18_remeasured)} points")
print(f"✓ v20実測データ: {len(v20_measured)} points")
print(f"✓ v21最適化データ: {len(v21_optimized)} points")

# ===== v18とv20の濃度差を計算 =====
print("\n[Step 2] v18とv20の濃度差を計算")

v18_density_diff = [0]
for i in range(1, len(v18_remeasured)):
    diff = v18_remeasured.iloc[i-1]['Density_measured'] - v18_remeasured.iloc[i]['Density_measured']
    v18_density_diff.append(diff)

v20_density_diff = [0]
for i in range(1, len(v20_measured)):
    diff = v20_measured.iloc[i-1]['Density_measured'] - v20_measured.iloc[i]['Density_measured']
    v20_density_diff.append(diff)

print("✓ 濃度差計算完了")

# ===== 比較CSVを生成 =====
print("\n[Step 3] 比較CSVを生成")

csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/compare_v18_v20_v21.csv'

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)

    # ヘッダー行
    writer.writerow([
        'Input',
        'V18_K', 'V18_Density', 'V18_Density_Diff',
        'V20_K', 'V20_Density', 'V20_Density_Diff',
        'V21_K', 'V21_Predicted_Density', 'V21_Density_Diff',
        'Target_Density_v3', 'Target_Density_Diff',
        'V21_Selection_Method'
    ])

    # データ行
    for i in range(len(v18_remeasured)):
        writer.writerow([
            int(v18_remeasured.iloc[i]['Input']),
            int(v18_remeasured.iloc[i]['K']),
            f"{v18_remeasured.iloc[i]['Density_measured']:.2f}",
            f"{v18_density_diff[i]:.3f}",
            int(v20_measured.iloc[i]['K']),
            f"{v20_measured.iloc[i]['Density_measured']:.2f}",
            f"{v20_density_diff[i]:.3f}",
            int(v21_optimized.iloc[i]['V21_K']),
            v21_optimized.iloc[i]['V21_Predicted_Density'],
            v21_optimized.iloc[i]['V21_Density_Diff'],
            v21_optimized.iloc[i]['Target_Density_v3'],
            v21_optimized.iloc[i]['Target_Density_Diff'],
            v21_optimized.iloc[i]['Selection_Method']
        ])

print(f"✓ CSV生成完了: {csv_path}")

# ===== サマリー表示 =====
print("\n" + "=" * 80)
print("比較サマリー（全ポイント）")
print("=" * 80)

print("\nInput | V18_K | V18_D | V18_Δ | V20_K | V20_D | V20_Δ | V21_K | V21_D(予) | V21_Δ(予) | 理想v3 | 理想Δ | 選択方法")
print("------|-------|-------|-------|-------|-------|-------|-------|-----------|-----------|--------|-------|-------------")

for i in range(len(v18_remeasured)):
    inp = int(v18_remeasured.iloc[i]['Input'])
    print(f"{inp:5} | "
          f"{v18_remeasured.iloc[i]['K']:5} | "
          f"{v18_remeasured.iloc[i]['Density_measured']:5.2f} | "
          f"{v18_density_diff[i]:5.3f} | "
          f"{v20_measured.iloc[i]['K']:5} | "
          f"{v20_measured.iloc[i]['Density_measured']:5.2f} | "
          f"{v20_density_diff[i]:5.3f} | "
          f"{v21_optimized.iloc[i]['V21_K']:5} | "
          f"{v21_optimized.iloc[i]['V21_Predicted_Density']:9} | "
          f"{v21_optimized.iloc[i]['V21_Density_Diff']:9} | "
          f"{v21_optimized.iloc[i]['Target_Density_v3']:6} | "
          f"{v21_optimized.iloc[i]['Target_Density_Diff']:5} | "
          f"{v21_optimized.iloc[i]['Selection_Method']}")

# ===== 濃度差の統計 =====
print("\n" + "=" * 80)
print("濃度差の統計分析")
print("=" * 80)

# v21の予測濃度差と理想濃度差の誤差
diff_errors = []
for i in range(1, len(v21_optimized)):
    predicted_diff = float(v21_optimized.iloc[i]['V21_Density_Diff'])
    target_diff = float(v21_optimized.iloc[i]['Target_Density_Diff'])
    error = abs(predicted_diff - target_diff)
    diff_errors.append(error)

print(f"\n平均濃度差誤差: {np.mean(diff_errors):.3f}")
print(f"最大濃度差誤差: {max(diff_errors):.3f}")
print(f"濃度差誤差 < 0.01: {sum(1 for e in diff_errors if e < 0.01)}/{len(diff_errors)} points")
print(f"濃度差誤差 < 0.02: {sum(1 for e in diff_errors if e < 0.02)}/{len(diff_errors)} points")
print(f"濃度差誤差 < 0.03: {sum(1 for e in diff_errors if e < 0.03)}/{len(diff_errors)} points")

print("\n" + "=" * 80)
print("完了")
print("=" * 80)
print(f"\n生成されたCSVファイル:")
print(f"  {csv_path}")
print(f"\nこのファイルには以下が含まれます:")
print(f"  - v18のK値、プリント濃度、濃度差")
print(f"  - v20のK値、プリント濃度、濃度差")
print(f"  - v21のK値、予測プリント濃度、予測濃度差（最適化版）")
print(f"  - 理想濃度v3、理想濃度差（目標値）")
print(f"  - v21のK値選択方法")
print("=" * 80)
