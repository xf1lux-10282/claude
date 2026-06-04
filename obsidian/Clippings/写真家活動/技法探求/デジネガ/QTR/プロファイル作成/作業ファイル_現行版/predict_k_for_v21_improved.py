#!/usr/bin/env python3
"""
v21用K値の改善された予測
v18とv20の2つの実測データを使用して、より正確なK→濃度関係を確立

重要な発見:
1. 240-255は機能している（階調分離あり）
2. 255でも紙白に届いていない（全体的にまだ浅い）
3. 必要なのは「階段を壊さずに、ネガ濃度を上げる」

新しい理想濃度v3の特徴:
- シャドウ/ハイライト: 濃度差0.02-0.03（小さい）
- 中間調: 濃度差0.05（均一）
- 全体的に滑らかで自然な階調変化

Generated: 2026-04-03
"""
import pandas as pd
import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt
import csv

print("=" * 80)
print("v21用K値の改善された予測")
print("v18+v20の2実測データから高精度K→濃度モデルを構築")
print("=" * 80)

# ===== v18とv20の実測データを読み込み =====
print("\n[Step 1] v18とv20の実測データを読み込み")

v18_remeasured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v18_remeasured_density.csv')
v20_measured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v20_measured_density.csv')

print(f"✓ v18再測定データ: {len(v18_remeasured)} points")
print(f"  K範囲: {v18_remeasured['K'].min()} - {v18_remeasured['K'].max()}")
print(f"  濃度範囲: {v18_remeasured['Density_measured'].min():.2f} - {v18_remeasured['Density_measured'].max():.2f}")

print(f"\n✓ v20実測データ: {len(v20_measured)} points")
print(f"  K範囲: {v20_measured['K'].min()} - {v20_measured['K'].max()}")
print(f"  濃度範囲: {v20_measured['Density_measured'].min():.2f} - {v20_measured['Density_measured'].max():.2f}")

# ===== 2つのデータを統合してK→濃度モデルを作成 =====
print("\n[Step 2] v18とv20を統合してK→濃度の補間モデルを作成")

# 両方のデータを結合
combined_k = np.concatenate([v18_remeasured['K'].values, v20_measured['K'].values])
combined_density = np.concatenate([v18_remeasured['Density_measured'].values, v20_measured['Density_measured'].values])

# DataFrameにして重複を除去
combined_df = pd.DataFrame({'K': combined_k, 'Density': combined_density})
combined_df = combined_df.sort_values('K')
combined_df = combined_df.drop_duplicates(subset='K', keep='first')

print(f"✓ 統合データ: {len(combined_df)} unique K values")
print(f"  K範囲: {combined_df['K'].min()} - {combined_df['K'].max()}")

# K→濃度の補間関数
f_k_to_density = interpolate.interp1d(
    combined_df['K'],
    combined_df['Density'],
    kind='linear',
    fill_value='extrapolate'
)

print("✓ K→濃度補間関数作成完了")

# ===== 濃度→Kの逆補間関数を作成 =====
print("\n[Step 3] 濃度→Kの逆補間関数を作成")

# 濃度は単調減少なので、降順でソート
density_sorted = combined_df.sort_values('Density', ascending=False)
density_unique = density_sorted.drop_duplicates(subset='Density', keep='first')

print(f"  重複濃度を除去: {len(density_sorted)} → {len(density_unique)} points")

f_density_to_k = interpolate.interp1d(
    density_unique['Density'],
    density_unique['K'],
    kind='linear',
    fill_value='extrapolate'
)

print("✓ 濃度→K逆補間関数作成完了")

# ===== 新しい理想濃度v3を読み込み =====
print("\n[Step 4] 新しい理想濃度ターゲットv3を読み込み")

target_v3 = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/ideal_density_target_v3.csv')

print(f"✓ 理想濃度ターゲットv3: {len(target_v3)} points")
print(f"  濃度範囲: {target_v3['Target_Density'].min():.2f} - {target_v3['Target_Density'].max():.2f}")

print("\n【v3の特徴】均等な濃度差")
print("シャドウ/ハイライト: 0.02-0.03ステップ")
print("中間調: 0.05ステップ（均一）")

# ===== 理想濃度v3からK値を逆算 =====
print("\n[Step 5] 理想濃度v3から必要K値を計算")

v21_k_values = []
for idx, density in enumerate(target_v3['Target_Density']):
    if target_v3.iloc[idx]['Input'] == 0:
        # Input 0は常にK=0（ネガ完全透明）
        k = 0
    else:
        k = f_density_to_k(density)
    v21_k_values.append(round(float(k)))

target_v3['V21_K'] = v21_k_values

print("✓ v21 K値逆算完了（Input 0は強制的にK=0）")

print("✓ v21 K値逆算完了")
print(f"  K範囲: {min(v21_k_values)} - {max(v21_k_values)}")

# ===== v18, v20との比較 =====
print("\n[Step 6] v18, v20, v21の比較")

# v18の33ポイント値
v18_k_33 = [
    0, 2400, 3372, 4864, 5264, 6197, 7531, 9031, 9864, 10864, 11364,
    11864, 12489, 13364, 14293, 15007, 15721, 16435, 17086, 17642, 18614, 19664,
    20531, 21364, 22531, 23364, 23864, 24864, 25499, 26264, 27128, 28304, 29752
]

# v20の33ポイント値
v20_k_33 = [
    0, 2400, 3048, 4118, 5131, 6197, 7086, 7864, 8698, 9864, 10697,
    11364, 12333, 13364, 13945, 15096, 15542, 16149, 16923, 17885, 18847, 19431,
    20531, 21531, 22198, 23364, 24614, 25287, 26264, 27128, 28304, 29028, 29752
]

target_v3['V18_K'] = v18_k_33
target_v3['V20_K'] = v20_k_33
target_v3['K_diff_v18'] = target_v3['V21_K'] - target_v3['V18_K']
target_v3['K_diff_v20'] = target_v3['V21_K'] - target_v3['V20_K']

print("\nInput | v18_K | v20_K | v21_K | v21-v18 | v21-v20")
print("------|-------|-------|-------|---------|--------")
for idx, row in target_v3.iterrows():
    if idx % 3 == 0:  # 3行ごと
        print(f"{int(row['Input']):5} | {int(row['V18_K']):5} | {int(row['V20_K']):5} | "
              f"{int(row['V21_K']):5} | {int(row['K_diff_v18']):+7} | {int(row['K_diff_v20']):+7}")

# ===== 重要な領域の分析 =====
print("\n[Step 7] ハイライト域（240-255）の詳細分析")

highlight_indices = [29, 30, 31, 32]  # 232, 240, 248, 255
print("\nInput | v18_K | v20_K | v21_K | v18濃度 | v20濃度 | v3理想")
print("------|-------|-------|-------|---------|---------|-------")
for idx in highlight_indices:
    inp = int(target_v3.iloc[idx]['Input'])
    v18_k = int(target_v3.iloc[idx]['V18_K'])
    v20_k = int(target_v3.iloc[idx]['V20_K'])
    v21_k = int(target_v3.iloc[idx]['V21_K'])
    v18_d = v18_remeasured.iloc[idx]['Density_measured']
    v20_d = v20_measured.iloc[idx]['Density_measured']
    v3_target = target_v3.iloc[idx]['Target_Density']
    print(f"{inp:5} | {v18_k:5} | {v20_k:5} | {v21_k:5} | {v18_d:7.2f} | {v20_d:7.2f} | {v3_target:6.2f}")

print("\n【観察】")
print("- v18とv20の240-255は両方とも階調分離している")
print("- しかし255でも紙白（0.09目標）に届いていない（実測0.15）")
print("- v21では全体的にK値を上げ、255を紙白に到達させる")

# ===== v21カーブ値として出力 =====
print("\n[Step 8] v21推奨K値を出力")

print("\n=== v21推奨K値（33ポイント） ===")
print("# 新しい理想濃度v3（均等な濃度差）から逆算")
print("# v18+v20の2実測データから高精度モデル構築")
print("# 6分45秒露光対応")
print("v21_k_values = [")
for i in range(0, len(v21_k_values), 11):
    chunk = v21_k_values[i:i+11]
    print("    " + ", ".join(f"{k}" for k in chunk) + ("," if i + 11 < len(v21_k_values) else ""))
print("]")

# ===== CSVとして保存 =====
print("\n[Step 9] 予測結果をCSVに保存")

csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v21_predicted_values.csv'

target_v3[['Input', 'Target_Density', 'Density_Step', 'V21_K', 'V18_K', 'V20_K', 'K_diff_v18', 'K_diff_v20']].to_csv(
    csv_path, index=False
)

print(f"✓ CSV保存完了: {csv_path}")

# ===== まとめ =====
print("\n" + "=" * 80)
print("v21 K値逆算完了")
print("=" * 80)
print("\n【新しい理想濃度v3の特徴】")
print("1. 均等な濃度差: シャドウ/ハイライト 0.02-0.03、中間調 0.05")
print("2. v2より自然で予測可能な階調変化")
print("3. 255で紙白（0.09）に到達することを目指す")

print("\n【v18+v20から得られた知見】")
print("1. 240-255の階調分離は両方で確認（階段構造は機能している）")
print("2. 255でも紙白に届いていない（0.15実測 vs 0.09目標）")
print("3. 必要なのは「階段を壊さずにネガ濃度を上げる」")

print("\n【v21の設計方針】")
print("1. 240-255の勾配構造は保つ")
print("2. 全体的にK値を上げて255を紙白に到達させる")
print("3. 均等な濃度差で予測可能な階調を実現")

print("\n【次のステップ】")
print("1. v21カーブ生成スクリプト（generate_v21.py）を作成")
print("2. v21.quadファイルを生成")
print("3. QTRにインストール")
print("4. 6分45秒露光でテストプリント")
print("5. 濃度測定して理想値v3との比較")
print("=" * 80)
