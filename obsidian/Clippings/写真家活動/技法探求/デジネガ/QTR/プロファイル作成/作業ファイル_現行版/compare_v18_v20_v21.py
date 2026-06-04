#!/usr/bin/env python3
"""
v18、v20、v21の詳細比較CSV生成

各カーブのK値、プリント濃度、濃度差を一覧で比較

Generated: 2026-04-03
"""
import pandas as pd
import numpy as np
from scipy import interpolate
import csv

print("=" * 80)
print("v18、v20、v21の詳細比較CSV生成")
print("=" * 80)

# ===== データ読み込み =====
print("\n[Step 1] データを読み込み")

v18_remeasured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v18_remeasured_density.csv')
v20_measured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v20_measured_density.csv')
v21_predicted = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v21_predicted_values.csv')

print(f"✓ v18再測定データ: {len(v18_remeasured)} points")
print(f"✓ v20実測データ: {len(v20_measured)} points")
print(f"✓ v21予測データ: {len(v21_predicted)} points")

# ===== K→濃度補間モデルを作成（v21の予測濃度計算用） =====
print("\n[Step 2] v18+v20からK→濃度補間モデルを作成")

combined_k = np.concatenate([v18_remeasured['K'].values, v20_measured['K'].values])
combined_density = np.concatenate([v18_remeasured['Density_measured'].values, v20_measured['Density_measured'].values])

combined_df = pd.DataFrame({'K': combined_k, 'Density': combined_density})
combined_df = combined_df.sort_values('K')
combined_df = combined_df.drop_duplicates(subset='K', keep='first')

f_k_to_density = interpolate.interp1d(
    combined_df['K'],
    combined_df['Density'],
    kind='linear',
    fill_value='extrapolate'
)

print(f"✓ K→濃度補間関数作成完了: {len(combined_df)} unique K values")

# ===== v21の予測濃度を計算 =====
print("\n[Step 3] v21の予測濃度を計算")

v21_predicted_density = []
for k in v21_predicted['V21_K']:
    if k == 0:
        # Input 0は実測値を使用（v20の1.41）
        density = 1.41
    else:
        density = float(f_k_to_density(k))
    v21_predicted_density.append(density)

v21_predicted['V21_Predicted_Density'] = v21_predicted_density

print(f"✓ v21予測濃度計算完了")

# ===== 濃度差を計算 =====
print("\n[Step 4] 各カーブの濃度差を計算")

# v18の濃度差（前のポイントとの差）
v18_density_diff = [0]  # Input 0は差分なし
for i in range(1, len(v18_remeasured)):
    diff = v18_remeasured.iloc[i-1]['Density_measured'] - v18_remeasured.iloc[i]['Density_measured']
    v18_density_diff.append(diff)

# v20の濃度差
v20_density_diff = [0]
for i in range(1, len(v20_measured)):
    diff = v20_measured.iloc[i-1]['Density_measured'] - v20_measured.iloc[i]['Density_measured']
    v20_density_diff.append(diff)

# v21の予測濃度差
v21_density_diff = [0]
for i in range(1, len(v21_predicted)):
    diff = v21_predicted_density[i-1] - v21_predicted_density[i]
    v21_density_diff.append(diff)

print(f"✓ 濃度差計算完了")

# ===== 比較CSVを生成 =====
print("\n[Step 5] 比較CSVを生成")

csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/compare_v18_v20_v21.csv'

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)

    # ヘッダー行
    writer.writerow([
        'Input',
        'V18_K', 'V18_Density', 'V18_Density_Diff',
        'V20_K', 'V20_Density', 'V20_Density_Diff',
        'V21_K', 'V21_Predicted_Density', 'V21_Density_Diff',
        'Target_Density_v3'
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
            int(v21_predicted.iloc[i]['V21_K']),
            f"{v21_predicted_density[i]:.2f}",
            f"{v21_density_diff[i]:.3f}",
            f"{v21_predicted.iloc[i]['Target_Density']:.2f}"
        ])

print(f"✓ CSV生成完了: {csv_path}")

# ===== サマリー表示 =====
print("\n" + "=" * 80)
print("比較サマリー（主要ポイント）")
print("=" * 80)

print("\nInput | V18_K | V18_D | V18_Δ | V20_K | V20_D | V20_Δ | V21_K | V21_D(予) | V21_Δ(予) | 理想v3")
print("------|-------|-------|-------|-------|-------|-------|-------|-----------|-----------|-------")

for i in [0, 8, 24, 48, 72, 96, 128, 160, 192, 216, 232, 240, 248, 255]:
    idx = int(i / 8) if i <= 240 else (31 if i == 248 else 32)

    print(f"{i:5} | {v18_remeasured.iloc[idx]['K']:5} | "
          f"{v18_remeasured.iloc[idx]['Density_measured']:5.2f} | "
          f"{v18_density_diff[idx]:5.3f} | "
          f"{v20_measured.iloc[idx]['K']:5} | "
          f"{v20_measured.iloc[idx]['Density_measured']:5.2f} | "
          f"{v20_density_diff[idx]:5.3f} | "
          f"{v21_predicted.iloc[idx]['V21_K']:5} | "
          f"{v21_predicted_density[idx]:9.2f} | "
          f"{v21_density_diff[idx]:9.3f} | "
          f"{v21_predicted.iloc[idx]['Target_Density']:6.2f}")

print("\n" + "=" * 80)
print("完了")
print("=" * 80)
print(f"\n生成されたCSVファイル:")
print(f"  {csv_path}")
print(f"\nこのファイルには以下が含まれます:")
print(f"  - v18のK値、プリント濃度、濃度差")
print(f"  - v20のK値、プリント濃度、濃度差")
print(f"  - v21のK値、予測プリント濃度、予測濃度差")
print(f"  - 理想濃度v3（目標値）")
print("=" * 80)
