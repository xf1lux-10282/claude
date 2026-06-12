#!/usr/bin/env python3
"""
v27測定結果の分析
6分45秒露光、v26ベース + Input 8下げ + スケーリング + K[255]=36000
"""
import pandas as pd
import numpy as np

print("=" * 80)
print("v27測定結果分析")
print("=" * 80)

# データ読み込み
df = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v27_measured_density.csv', encoding='utf-8')

print(f"\n測定ポイント数: {len(df)}")

# 濃度差を計算（実測値ベース）
density_diffs = [0]
for i in range(1, len(df)):
    diff = df.iloc[i-1]['Density_measured'] - df.iloc[i]['Density_measured']
    density_diffs.append(diff)

df['Density_step_actual'] = density_diffs

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

if df.iloc[-1]['Density_measured'] <= 0.09:
    print("✓ 紙白到達成功（0.09以下）")
elif df.iloc[-1]['Density_measured'] <= 0.12:
    print("△ 紙白ほぼ到達（0.12以下）")
else:
    print("✗ 紙白未到達（0.12超）")

# 全体の傾向
print("\n【全体傾向】")
print(f"平均偏差: {df['Deviation_from_target'].mean():+.3f}")
print(f"最大偏差: {df['Deviation_from_target'].max():+.3f} (Input {df.iloc[df['Deviation_from_target'].idxmax()]['Input']:.0f})")
print(f"最小偏差: {df['Deviation_from_target'].min():+.3f} (Input {df.iloc[df['Deviation_from_target'].idxmin()]['Input']:.0f})")

# 濃度差の分析
print("\n【濃度差の分析（主要ポイント）】")
print("Input | 測定濃度 | 濃度差 | 目標差 | 差の誤差 | 備考")
print("------|----------|--------|--------|----------|-----")
for i in [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 128, 160, 192, 216, 232, 240, 248, 255]:
    row = df[df['Input'] == i].iloc[0]
    measured_d = row['Density_measured']
    step = row['Density_step_actual']
    target_diff = 0.05  # 理想は0.05ステップ

    if i == 0:
        error = 0
        note = "最暗"
    else:
        error = abs(step - target_diff)
        if step < 0:
            note = "逆転!"
        elif error < 0.01:
            note = "良好"
        elif error < 0.03:
            note = "許容範囲"
        else:
            note = "改善必要"

    print(f"{i:5} | {measured_d:8.2f} | {step:6.3f} | {target_diff:6.2f} | {error:8.3f} | {note}")

# 問題点の抽出
print("\n【問題点】")
problems = []

# 濃度差が逆転している箇所
for i in range(1, len(df)):
    if df.iloc[i]['Density_step_actual'] < 0:
        problems.append(f"Input {df.iloc[i]['Input']:.0f}: 濃度逆転（{df.iloc[i]['Density_step_actual']:+.3f}）")

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
    goods.append(f"紙白到達成功（Input 255 = {df.iloc[-1]['Density_measured']:.2f}）")

# Input 48逆転解消確認
idx_40 = df[df['Input'] == 40].index[0]
idx_48 = df[df['Input'] == 48].index[0]
step_48 = df.iloc[idx_48]['Density_step_actual']
if step_48 > 0:
    goods.append(f"Input 48の逆転解消（差 {step_48:.3f}）")

# シャドウ域の改善確認
shadow_deviation = df[(df['Input'] >= 24) & (df['Input'] <= 80)]['Deviation_from_target'].mean()
if abs(shadow_deviation) < 0.10:
    goods.append(f"シャドウ域の偏差改善（平均 {shadow_deviation:+.3f}）")

# 全体的なバランス
if abs(df['Deviation_from_target'].mean()) < 0.03:
    goods.append(f"全体的な偏差が小さい（平均 {df['Deviation_from_target'].mean():+.3f}）")

for g in goods:
    print(f"  ✓ {g}")

# v26との比較
print("\n【v26との比較（主要ポイント）】")

# v26データ読み込み
df_v26 = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v26_measured_density.csv', encoding='utf-8')

print("\nInput | v26測定 | v27測定 | 差分 | 改善")
print("------|---------|---------|------|-----")
for i in [0, 8, 24, 48, 72, 128, 192, 240, 248, 255]:
    v26_d = df_v26[df_v26['Input'] == i].iloc[0]['Density_measured']
    v27_d = df[df['Input'] == i].iloc[0]['Density_measured']
    diff = v27_d - v26_d

    if i in [24, 48, 72]:  # シャドウ域
        target_d = df[df['Input'] == i].iloc[0]['Target_Density_v3']
        v26_dev = v26_d - target_d
        v27_dev = v27_d - target_d
        if abs(v27_dev) < abs(v26_dev):
            improvement = "改善"
        else:
            improvement = "悪化"
    elif i == 255:  # 紙白
        if v27_d <= 0.09:
            improvement = "到達!"
        elif v27_d < v26_d:
            improvement = "改善"
        else:
            improvement = "変化なし"
    else:
        improvement = "-"

    print(f"{i:5} | {v26_d:7.2f} | {v27_d:7.2f} | {diff:+.2f} | {improvement}")

print("\n" + "=" * 80)
print("分析完了")
print("=" * 80)
