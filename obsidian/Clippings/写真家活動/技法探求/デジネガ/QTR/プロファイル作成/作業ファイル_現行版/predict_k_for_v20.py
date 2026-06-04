#!/usr/bin/env python3
"""
v20用K値の逆算
新しい理想濃度ターゲット（より滑らかな階調）からK値を計算

新しい理想濃度の特徴:
- シャドウ部（0-40）: 1.36→1.24（差0.12、4ステップ）
- 暗部上部（40-80）: 1.24→1.01（差0.23、5ステップ）
- 中間部（80-128）: 1.01→0.71（差0.30、6ステップ）
- ハイライト寄り（128-192）: 0.71→0.32（差0.39、8ステップ）
- ハイライト（192-255）: 0.32→0.09（差0.23、8ステップ）

Generated: 2026-04-03
"""
import pandas as pd
import numpy as np
from scipy import interpolate
import csv

print("=" * 80)
print("v20用K値の逆算")
print("新しい理想濃度ターゲット（より滑らかな階調）")
print("=" * 80)

# ===== v18実測データを読み込み =====
print("\n[Step 1] v18実測データを読み込み（K→濃度の関係）")

v18_measured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v18_measured_density.csv')

print(f"✓ v18実測データ: {len(v18_measured)} points")
print(f"  K範囲: {v18_measured['K'].min()} - {v18_measured['K'].max()}")
print(f"  濃度範囲: {v18_measured['Density_measured'].min():.2f} - {v18_measured['Density_measured'].max():.2f}")

# ===== K→濃度の補間関数を作成 =====
print("\n[Step 2] K→濃度の補間関数を作成")

v18_sorted = v18_measured.sort_values('K')
v18_unique = v18_sorted.drop_duplicates(subset='K', keep='first')

f_k_to_density = interpolate.interp1d(
    v18_unique['K'],
    v18_unique['Density_measured'],
    kind='linear',
    fill_value='extrapolate'
)

print(f"✓ K→濃度補間関数作成完了")
print(f"  テスト: K=15721 → 濃度={f_k_to_density(15721):.3f} (実測: 0.69)")

# ===== 濃度→Kの逆補間関数を作成 =====
print("\n[Step 3] 濃度→Kの逆補間関数を作成")

# 濃度は単調減少なので、降順でソート
measured_sorted = v18_measured.sort_values('Density_measured', ascending=False)
measured_unique = measured_sorted.drop_duplicates(subset='Density_measured', keep='first')

print(f"  重複濃度を除去: {len(measured_sorted)} → {len(measured_unique)} points")

f_density_to_k = interpolate.interp1d(
    measured_unique['Density_measured'],
    measured_unique['K'],
    kind='linear',
    fill_value='extrapolate'
)

print("✓ 濃度→K逆補間関数作成完了")
print(f"  テスト: 濃度=0.69 → K={f_density_to_k(0.69):.0f}")

# ===== 新しい理想濃度を読み込み =====
print("\n[Step 4] 新しい理想濃度ターゲットを読み込み")

target_v2 = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/ideal_density_target_v2.csv')

print(f"✓ 理想濃度ターゲットv2: {len(target_v2)} points")
print(f"  濃度範囲: {target_v2['Target_Density'].min():.2f} - {target_v2['Target_Density'].max():.2f}")

# 旧理想濃度との比較
target_v1 = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/ideal_density_target.csv')

print("\n【v1との主要差分】")
print("Input | v1理想 | v2理想 | 差分")
print("------|--------|--------|------")
for i in [0, 32, 48, 56, 80, 128, 192, 240, 255]:
    idx = target_v2[target_v2['Input'] == i].index[0]
    v1_d = target_v1.loc[idx, 'Target_Density']
    v2_d = target_v2.loc[idx, 'Target_Density']
    diff = v2_d - v1_d
    print(f"{i:5} | {v1_d:6.2f} | {v2_d:6.2f} | {diff:+6.2f}")

# ===== 理想濃度からK値を逆算 =====
print("\n[Step 5] 理想濃度v2から必要K値を計算")

v20_k_values = []
for density in target_v2['Target_Density']:
    k = f_density_to_k(density)
    v20_k_values.append(round(float(k)))

target_v2['V20_K'] = v20_k_values

print("✓ v20 K値逆算完了")
print(f"  K範囲: {min(v20_k_values)} - {max(v20_k_values)}")

# ===== v18, v19との比較 =====
print("\n[Step 6] v18, v19との比較")

# v18の33ポイント値
v18_k_33 = [
    0, 2400, 3372, 4864, 5264, 6197, 7531, 9031, 9864, 10864, 11364,
    11864, 12489, 13364, 14293, 15007, 15721, 16435, 17086, 17642, 18614, 19664,
    20531, 21364, 22531, 23364, 23864, 24864, 25499, 26264, 27128, 28304, 29752
]

# v19の33ポイント値
v19_k_33 = v18_k_33.copy()
adjustments = {
    6: -200, 7: -400, 14: +200, 16: +150, 21: -300, 24: -400, 32: -500
}
for idx, delta in adjustments.items():
    v19_k_33[idx] = v18_k_33[idx] + delta

target_v2['V18_K'] = v18_k_33
target_v2['V19_K'] = v19_k_33
target_v2['K_diff_v18'] = target_v2['V20_K'] - target_v2['V18_K']
target_v2['K_diff_v19'] = target_v2['V20_K'] - target_v2['V19_K']

print("\nInput | v18_K | v19_K | v20_K | v20-v18 | v20-v19")
print("------|-------|-------|-------|---------|--------")
for idx, row in target_v2.iterrows():
    if idx % 3 == 0:  # 3行ごと
        print(f"{int(row['Input']):5} | {int(row['V18_K']):5} | {int(row['V19_K']):5} | "
              f"{int(row['V20_K']):5} | {int(row['K_diff_v18']):+7} | {int(row['K_diff_v19']):+7}")

# ===== v20カーブ値として出力 =====
print("\n[Step 7] v20推奨K値を出力")

print("\n=== v20推奨K値（33ポイント） ===")
print("# 新しい理想濃度カーブ（より滑らか）から逆算")
print("# 6分45秒露光対応")
print("v20_k_values = [")
for i in range(0, len(v20_k_values), 11):
    chunk = v20_k_values[i:i+11]
    print("    " + ", ".join(f"{k}" for k in chunk) + ("," if i + 11 < len(v20_k_values) else ""))
print("]")

# ===== CSVとして保存 =====
print("\n[Step 8] 予測結果をCSVに保存")

csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v20_predicted_values.csv'

target_v2[['Input', 'Target_Density', 'V20_K', 'V18_K', 'V19_K', 'K_diff_v18', 'K_diff_v19']].to_csv(
    csv_path, index=False
)

print(f"✓ CSV保存完了: {csv_path}")

# ===== まとめ =====
print("\n" + "=" * 80)
print("v20 K値逆算完了")
print("=" * 80)
print("\n【新しい理想濃度の特徴】")
print("1. より自然で滑らかな階調変化")
print("2. v1で問題だった急な勾配を全体的に改善")
print("3. シャドウ端（Input 0）: 1.38→1.36に引き下げ")
print("4. ハイライト端（Input 255）: 0.13→0.09に引き下げ")
print("5. 中間部の勾配をより均一化")

print("\n【次のステップ】")
print("1. v20カーブ生成スクリプト（generate_v20.py）を作成")
print("2. v20.quadファイルを生成")
print("3. QTRにインストール")
print("4. 6分45秒露光でテストプリント")
print("5. 濃度測定と理想値v2との比較")
print("=" * 80)
