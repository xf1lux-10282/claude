#!/usr/bin/env python3
"""
理想濃度からK値を予測計算

アプローチ:
1. v16実測データ（K→濃度）から補間関数を作成
2. 理想濃度→K値を逆算（逆補間）
3. 6:45→6:00の露光時間補正を適用

Generated: 2026-04-03
"""
import numpy as np
import pandas as pd
from scipy import interpolate
import csv

print("=" * 80)
print("理想濃度からK値を予測計算")
print("=" * 80)

# ===== Step 1: v16実測データを読み込み =====
print("\n[Step 1] v16実測データ（K→濃度）を読み込み")

measured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v16_measured_density.csv')
print(f"✓ 実測データ読み込み完了: {len(measured)} points")
print(f"  K範囲: {measured['K'].min()} - {measured['K'].max()}")
print(f"  濃度範囲: {measured['Density_6m45s'].min()} - {measured['Density_6m45s'].max()}")

# ===== Step 2: 理想濃度を読み込み =====
print("\n[Step 2] 理想濃度ターゲットを読み込み")

target = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/ideal_density_target.csv')
print(f"✓ 理想濃度読み込み完了: {len(target)} points")
print(f"  濃度範囲: {target['Target_Density'].min()} - {target['Target_Density'].max()}")

# ===== Step 3: K→濃度の補間関数を作成 =====
print("\n[Step 3] K→濃度の補間関数を作成（cubic spline）")

# K値が大きいほど濃度が小さい（逆相関）ことを確認
f_k_to_density = interpolate.interp1d(
    measured['K'],
    measured['Density_6m45s'],
    kind='cubic',
    fill_value='extrapolate'
)

print("✓ K→濃度補間関数作成完了")
print(f"  テスト: K=15864 → 濃度={f_k_to_density(15864):.3f} (実測: 0.71)")

# ===== Step 4: 濃度→Kの逆補間関数を作成 =====
print("\n[Step 4] 濃度→Kの逆補間関数を作成")

# 濃度は単調減少なので、逆順でソートして補間
measured_sorted = measured.sort_values('Density_6m45s', ascending=False)

# 重複濃度を除去（最初のK値を採用）
measured_unique = measured_sorted.drop_duplicates(subset='Density_6m45s', keep='first')

print(f"  重複濃度を除去: {len(measured_sorted)} → {len(measured_unique)} points")

# 濃度が同じ点が複数ある場合はlinear補間を使用（より安定）
f_density_to_k = interpolate.interp1d(
    measured_unique['Density_6m45s'],
    measured_unique['K'],
    kind='linear',
    fill_value='extrapolate'
)

print("✓ 濃度→K逆補間関数作成完了")
print(f"  テスト: 濃度=0.71 → K={f_density_to_k(0.71):.0f}")

# ===== Step 5: 理想濃度から必要K値を計算 =====
print("\n[Step 5] 理想濃度から必要K値を計算")

predicted_k = []
for density in target['Target_Density']:
    k = f_density_to_k(density)
    predicted_k.append(round(float(k)))

target['Predicted_K_6m45s'] = predicted_k

print("✓ K値予測完了（6:45露光ベース）")
print(f"  予測K範囲: {min(predicted_k)} - {max(predicted_k)}")

# ===== Step 6: v18用K値として採用（6:45ベース） =====
print("\n[Step 6] v18用K値を決定（6:45露光ベース）")

# まずは6:45で理想濃度を実現するK値を使用
# 実測確認後、必要に応じて露光時間を調整
target['V18_K'] = target['Predicted_K_6m45s']

print("✓ v18用K値決定")
print(f"  K範囲: {target['V18_K'].min()} - {target['V18_K'].max()}")
print(f"  露光時間: 6分45秒（v16と同じ）")

# ===== Step 7: v16実測との比較 =====
print("\n[Step 7] v16実測K値との比較")

comparison = pd.merge(target, measured[['Input', 'K', 'Density_6m45s']], on='Input')
comparison['K_diff'] = comparison['V18_K'] - comparison['K']
comparison['Density_diff'] = comparison['Target_Density'] - comparison['Density_6m45s']

print("\nInput | v16実測K | v16濃度 | 理想濃度 | v18予測K | K差分")
print("------|----------|---------|----------|----------|-------")
for idx, row in comparison.iterrows():
    if idx % 3 == 0:  # 3行ごとに表示
        print(f"{row['Input']:5} | {row['K']:8} | {row['Density_6m45s']:7.2f} | "
              f"{row['Target_Density']:8.2f} | {row['V18_K']:8} | {row['K_diff']:+6}")

# ===== Step 8: v18カーブ値として出力 =====
print("\n[Step 8] v18推奨K値を出力")

v18_k_values = target['V18_K'].tolist()

print("\n=== v18推奨K値（33ポイント） ===")
print("# 理想濃度カーブから逆算、6分45秒露光対応")
print("specified_k_values = [")
for i in range(0, len(v18_k_values), 11):
    chunk = v18_k_values[i:i+11]
    print("    " + ", ".join(f"{k}" for k in chunk) + ("," if i + 11 < len(v18_k_values) else ""))
print("]")

# ===== Step 9: CSVとして保存 =====
print("\n[Step 9] 予測結果をCSVに保存")

csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v18_predicted_values.csv'

comparison[['Input', 'Target_Density', 'V18_K', 'K', 'K_diff', 'Density_6m45s', 'Density_diff']].to_csv(
    csv_path, index=False
)

print(f"✓ CSV保存完了: {csv_path}")

# ===== Step 10: まとめ =====
print("\n" + "=" * 80)
print("予測計算完了")
print("=" * 80)
print("\n【重要な注意点】")
print("1. この予測はv16実測データに基づく外挿を含むため、精度に限界があります")
print("2. 特にシャドウ部（Input 0-8）とハイライト部（240-255）は実測で検証が必要")
print("3. cubic spline補間の特性上、端点付近で振動する可能性があります")
print("4. 実際のプリントで検証し、必要に応じて微調整してください")
print("\n【推奨ワークフロー】")
print("1. v18カーブを生成・インストール")
print("2. 6分45秒露光でテストプリント（v16と同じ条件）")
print("3. 濃度測定と理想値との比較")
print("4. 理想濃度に近づいていれば、露光時間を短縮（6分等）")
print("5. 必要に応じてv19で微調整")
print("=" * 80)
