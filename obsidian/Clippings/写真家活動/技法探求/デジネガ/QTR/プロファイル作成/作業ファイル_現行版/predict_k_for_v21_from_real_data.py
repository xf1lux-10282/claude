#!/usr/bin/env python3
"""
v21用K値の最適化された予測
v18とv20の実測データから、理想濃度に最も近いK値を選択し、必要に応じて線形補間で微調整

アプローチ:
1. 各Inputで、v18とv20のどちらが理想濃度v3に近いかを判定
2. 近い方のK値をベースとして採用
3. 必要に応じてv18とv20の間で線形補間して理想濃度に合わせる

Generated: 2026-04-03
"""
import pandas as pd
import numpy as np
from scipy import interpolate
import csv

print("=" * 80)
print("v21用K値の最適化された予測")
print("v18+v20実測データから理想濃度に最も近いK値を選択")
print("=" * 80)

# ===== データ読み込み =====
print("\n[Step 1] データを読み込み")

v18_remeasured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v18_remeasured_density.csv')
v20_measured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v20_measured_density.csv')
target_v3 = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/ideal_density_target_v3.csv')

print(f"✓ v18再測定データ: {len(v18_remeasured)} points")
print(f"✓ v20実測データ: {len(v20_measured)} points")
print(f"✓ 理想濃度v3: {len(target_v3)} points")

# ===== v21のK値を選択・補間 =====
print("\n[Step 2] v18/v20から理想濃度に最も近いK値を選択")

v21_k_values = []
selection_log = []

for i in range(len(target_v3)):
    inp = int(target_v3.iloc[i]['Input'])
    target_density = target_v3.iloc[i]['Target_Density']

    if inp == 0:
        # Input 0は常にK=0
        k_v21 = 0
        selection_log.append((inp, 0, 0, 0, 0.0, "Fixed(K=0)"))
    else:
        v18_k = int(v18_remeasured.iloc[i]['K'])
        v18_density = v18_remeasured.iloc[i]['Density_measured']
        v20_k = int(v20_measured.iloc[i]['K'])
        v20_density = v20_measured.iloc[i]['Density_measured']

        # v18とv20のどちらが理想濃度に近いか
        diff_v18 = abs(v18_density - target_density)
        diff_v20 = abs(v20_density - target_density)

        if diff_v18 <= diff_v20:
            # v18の方が近い
            if diff_v18 < 0.01:
                # 十分近いのでv18のK値をそのまま使用
                k_v21 = v18_k
                selection_log.append((inp, v18_k, v18_density, target_density, diff_v18, "v18(exact)"))
            else:
                # v18とv20の間で線形補間
                # 濃度の比率からK値を補間
                if v18_density != v20_density:
                    ratio = (target_density - v20_density) / (v18_density - v20_density)
                    ratio = np.clip(ratio, 0, 1)
                    k_v21 = round(v20_k + ratio * (v18_k - v20_k))
                else:
                    k_v21 = v18_k
                selection_log.append((inp, k_v21, v18_density, target_density, diff_v18, "v18→v20 interp"))
        else:
            # v20の方が近い
            if diff_v20 < 0.01:
                # 十分近いのでv20のK値をそのまま使用
                k_v21 = v20_k
                selection_log.append((inp, v20_k, v20_density, target_density, diff_v20, "v20(exact)"))
            else:
                # v18とv20の間で線形補間
                if v18_density != v20_density:
                    ratio = (target_density - v20_density) / (v18_density - v20_density)
                    ratio = np.clip(ratio, 0, 1)
                    k_v21 = round(v20_k + ratio * (v18_k - v20_k))
                else:
                    k_v21 = v20_k
                selection_log.append((inp, k_v21, v20_density, target_density, diff_v20, "v20→v18 interp"))

    v21_k_values.append(k_v21)

print("✓ v21 K値選択完了")
print(f"  K範囲: {min(v21_k_values)} - {max(v21_k_values)}")

# ===== 選択ログを表示 =====
print("\n[Step 3] K値選択の詳細ログ（主要ポイント）")
print("\nInput | 選択K | 実測濃度 | 理想濃度 | 誤差 | 選択方法")
print("------|-------|----------|----------|------|-------------")
for i in [0, 8, 24, 48, 72, 96, 128, 160, 192, 216, 232, 240, 248, 255]:
    idx = int(i / 8) if i <= 240 else (31 if i == 248 else 32)
    inp, k, measured_d, target_d, diff, method = selection_log[idx]
    print(f"{inp:5} | {k:5} | {measured_d:8.2f} | {target_d:8.2f} | {diff:4.3f} | {method}")

# ===== K→濃度モデルで予測濃度を計算 =====
print("\n[Step 4] v21の予測濃度を計算")

# v18+v20のK→濃度補間モデル
combined_k = np.concatenate([v18_remeasured['K'].values, v20_measured['K'].values])
combined_density = np.concatenate([v18_remeasured['Density_measured'].values, v20_measured['Density_measured'].values])
combined_df = pd.DataFrame({'K': combined_k, 'Density': combined_density})
combined_df = combined_df.sort_values('K').drop_duplicates(subset='K', keep='first')

f_k_to_density = interpolate.interp1d(
    combined_df['K'],
    combined_df['Density'],
    kind='linear',
    fill_value='extrapolate'
)

v21_predicted_density = []
for k in v21_k_values:
    if k == 0:
        density = 1.41
    else:
        density = float(f_k_to_density(k))
    v21_predicted_density.append(density)

print("✓ v21予測濃度計算完了")

# ===== 予測濃度差を計算 =====
print("\n[Step 5] v21の予測濃度差を計算")

v21_density_diff = [0]
for i in range(1, len(v21_predicted_density)):
    diff = v21_predicted_density[i-1] - v21_predicted_density[i]
    v21_density_diff.append(diff)

print("✓ 予測濃度差計算完了")

# ===== 結果をCSVに保存 =====
print("\n[Step 6] 結果をCSVに保存")

csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v21_optimized_values.csv'

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Input', 'V21_K', 'V21_Predicted_Density', 'V21_Density_Diff', 'Target_Density_v3', 'Target_Density_Diff', 'Selection_Method'])

    for i in range(len(v21_k_values)):
        inp, k_sel, _, _, _, method = selection_log[i]
        writer.writerow([
            int(target_v3.iloc[i]['Input']),
            v21_k_values[i],
            f"{v21_predicted_density[i]:.2f}",
            f"{v21_density_diff[i]:.3f}",
            f"{target_v3.iloc[i]['Target_Density']:.2f}",
            f"{target_v3.iloc[i]['Density_Step']:.2f}",
            method
        ])

print(f"✓ CSV保存完了: {csv_path}")

# ===== 予測濃度差と理想濃度差の比較 =====
print("\n[Step 7] 予測濃度差と理想濃度差の比較")
print("\nInput | 予測差 | 理想差 | 差の誤差")
print("------|--------|--------|----------")

max_diff_error = 0
for i in range(1, len(v21_density_diff)):
    predicted_diff = v21_density_diff[i]
    target_diff = target_v3.iloc[i]['Density_Step']
    diff_error = abs(predicted_diff - target_diff)
    max_diff_error = max(max_diff_error, diff_error)

    if i % 4 == 0 or i >= 29:  # 一部のみ表示
        print(f"{target_v3.iloc[i]['Input']:5} | {predicted_diff:6.3f} | {target_diff:6.2f} | {diff_error:8.3f}")

print(f"\n最大濃度差誤差: {max_diff_error:.3f}")

# ===== v21推奨K値を出力 =====
print("\n[Step 8] v21推奨K値を出力")

print("\n=== v21推奨K値（33ポイント） ===")
print("# v18+v20実測データから理想濃度に最も近いK値を選択")
print("# 線形補間で微調整")
print("# 6分45秒露光対応")
print("v21_k_values = [")
for i in range(0, len(v21_k_values), 11):
    chunk = v21_k_values[i:i+11]
    print("    " + ", ".join(f"{k}" for k in chunk) + ("," if i + 11 < len(v21_k_values) else ""))
print("]")

# ===== まとめ =====
print("\n" + "=" * 80)
print("v21 K値最適化完了")
print("=" * 80)
print("\n【アプローチ】")
print("1. v18とv20の実測データから、各Inputで理想濃度に最も近い方を選択")
print("2. 十分近い場合はそのままK値を採用")
print("3. そうでない場合はv18とv20の間で線形補間して微調整")

print("\n【期待される効果】")
print("1. 実測データに基づくため予測精度が高い")
print("2. v18/v20で実際に機能したK値を使うため信頼性が高い")
print("3. 補間による誤差を最小化")

print("\n【次のステップ】")
print("1. 予測濃度差と理想濃度差を確認")
print("2. 許容範囲内ならv21カーブを生成")
print("3. QTRにインストール")
print("4. 6分45秒露光でテストプリント")
print("=" * 80)
