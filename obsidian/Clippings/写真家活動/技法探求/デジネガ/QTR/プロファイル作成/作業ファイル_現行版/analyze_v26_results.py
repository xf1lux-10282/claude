#!/usr/bin/env python3
"""
v26測定結果の分析
6分45秒露光、v22ベース + 紙白補正（248-255）
"""
import pandas as pd
import numpy as np

print("=" * 80)
print("v26測定結果分析")
print("=" * 80)

# データ読み込み
df = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v26_measured_density.csv')

print(f"\n測定ポイント数: {len(df)}")

# 濃度差を計算
density_diffs = [0]
for i in range(1, len(df)):
    diff = df.iloc[i-1]['Density_measured'] - df.iloc[i]['Density_measured']
    density_diffs.append(diff)

df['Density_step'] = density_diffs

# 理想濃度との差
df['Deviation_from_target'] = df['Density_measured'] - df['Target_Density_v3']

print("\n【測定結果サマリー】")
print(f"濃度範囲: {df['Density_measured'].max():.2f} → {df['Density_measured'].min():.2f}")
print(f"目標範囲: {df['Target_Density_v3'].max():.2f} → {df['Target_Density_v3'].min():.2f}")

# 紙白到達確認
print(f"\n【紙白到達確認】")
print(f"Input 255 測定値: {df.iloc[-1]['Density_measured']:.2f}")
print(f"Input 255 目標値: {df.iloc[-1]['Target_Density_v3']:.2f}")
print(f"差: {df.iloc[-1]['Deviation_from_target']:+.2f}")

if df.iloc[-1]['Density_measured'] <= 0.12:
    print("✓ 紙白到達成功（0.12以下）")
elif df.iloc[-1]['Density_measured'] <= 0.15:
    print("△ 紙白ほぼ到達（0.15以下）")
else:
    print("✗ 紙白未到達（0.15超）")

# 全体の傾向
print("\n【全体傾向】")
print(f"平均偏差: {df['Deviation_from_target'].mean():+.3f}")
print(f"最大偏差: {df['Deviation_from_target'].max():+.3f} (Input {df.iloc[df['Deviation_from_target'].idxmax()]['Input']:.0f})")
print(f"最小偏差: {df['Deviation_from_target'].min():+.3f} (Input {df.iloc[df['Deviation_from_target'].idxmin()]['Input']:.0f})")

# 濃度差の分析
print("\n【濃度差の分析】")
print("Input | 測定濃度 | 濃度差 | 理想差 | 差の誤差")
print("------|----------|--------|--------|----------")
for i in [0, 8, 16, 32, 48, 72, 96, 128, 160, 192, 216, 232, 240, 248, 255]:
    row = df[df['Input'] == i].iloc[0]
    measured_d = row['Density_measured']
    step = row['Density_step']
    # 理想濃度差（次のポイントとの差）
    if i < 248:
        target_diff = row['Density_diff_measured']  # CSVから
    else:
        target_diff = 0.02

    if i == 0:
        error = 0
    else:
        error = abs(step - target_diff) if not pd.isna(target_diff) else 0

    print(f"{i:5} | {measured_d:8.2f} | {step:6.3f} | {target_diff:6.2f} | {error:8.3f}")

# 問題点の抽出
print("\n【問題点】")
problems = []

# 濃度差が逆転している箇所
for i in range(1, len(df)):
    if df.iloc[i]['Density_step'] < 0:
        problems.append(f"Input {df.iloc[i]['Input']:.0f}: 濃度逆転（{df.iloc[i]['Density_step']:+.3f}）")

# 理想濃度との大きな乖離
for i in range(len(df)):
    if abs(df.iloc[i]['Deviation_from_target']) > 0.05:
        problems.append(f"Input {df.iloc[i]['Input']:.0f}: 目標から大きく乖離（{df.iloc[i]['Deviation_from_target']:+.3f}）")

if problems:
    for p in problems:
        print(f"  - {p}")
else:
    print("  問題なし")

# 良好な点
print("\n【良好な点】")
goods = []

# 紙白到達
if df.iloc[-1]['Density_measured'] <= 0.12:
    goods.append("紙白到達成功（Input 255 = 0.11）")

# 240-248の分離
if df.iloc[-2]['Density_step'] > 0:
    goods.append(f"240-248の分離確認（差 {df.iloc[-2]['Density_step']:.3f}）")

# 全体的なバランス
if abs(df['Deviation_from_target'].mean()) < 0.03:
    goods.append(f"全体的な偏差が小さい（平均 {df['Deviation_from_target'].mean():+.3f}）")

for g in goods:
    print(f"  ✓ {g}")

print("\n" + "=" * 80)
print("分析完了")
print("=" * 80)
