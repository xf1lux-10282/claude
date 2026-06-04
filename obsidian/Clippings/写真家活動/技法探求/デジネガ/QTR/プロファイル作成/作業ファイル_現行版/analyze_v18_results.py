#!/usr/bin/env python3
"""
v18実測結果の分析と問題箇所の特定

ユーザーの分析:
1. Input 40-56 (1.24 → 1.18 → 1.09): 急すぎる
2. Input 104-128 (0.86 → 0.78 → 0.77 → 0.69): ムラがある
3. Input 160-192 (0.53 → 0.44, 0.37 → 0.30): 段差が大きい
4. Input 248-255 (0.13 → 0.09): 抜けすぎ

Generated: 2026-04-03
"""
import pandas as pd
import numpy as np

print("=" * 80)
print("v18実測結果分析")
print("=" * 80)

# ===== データ読み込み =====
df = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v18_measured_density.csv')

print("\n[全体サマリー]")
print(f"  平均誤差: {df['Density_diff'].mean():.4f}")
print(f"  最大プラス誤差: {df['Density_diff'].max():.4f} (Input {df.loc[df['Density_diff'].idxmax(), 'Input']:.0f})")
print(f"  最大マイナス誤差: {df['Density_diff'].min():.4f} (Input {df.loc[df['Density_diff'].idxmin(), 'Input']:.0f})")

# ===== 濃度変化率の分析 =====
print("\n[濃度変化率の分析]")
print("各区間での濃度差（急な変化を検出）\n")

df['Density_change'] = df['Density_measured'].diff().abs()

print("Input区間 | 実測濃度変化 | 理想変化 | 変化率比")
print("----------|--------------|----------|----------")

for i in range(1, len(df)):
    input_prev = df.iloc[i-1]['Input']
    input_curr = df.iloc[i]['Input']
    measured_change = df.iloc[i]['Density_change']

    # 理想的な変化量（等間隔想定）
    ideal_change = abs(df.iloc[i]['Target_Density'] - df.iloc[i-1]['Target_Density'])

    # 変化率比（1.0が理想、大きいほど急）
    if ideal_change > 0:
        ratio = measured_change / ideal_change
    else:
        ratio = 1.0

    # 問題箇所をハイライト
    marker = ""
    if ratio > 1.5:
        marker = " ← 急すぎ"
    elif ratio < 0.5:
        marker = " ← 緩すぎ"

    print(f"{input_prev:3.0f}-{input_curr:3.0f} | {measured_change:12.3f} | {ideal_change:8.3f} | {ratio:8.2f}{marker}")

# ===== 問題箇所の詳細分析 =====
print("\n" + "=" * 80)
print("問題箇所の詳細分析")
print("=" * 80)

# 問題1: Input 40-56
print("\n【問題1】Input 40-56 (暗部上部〜中間入口)")
zone1 = df[(df['Input'] >= 40) & (df['Input'] <= 64)]
print(zone1[['Input', 'K', 'Density_measured', 'Target_Density', 'Density_diff']].to_string(index=False))
print(f"\n  → Input 40-48: 濃度差 {zone1.iloc[0]['Density_measured'] - zone1.iloc[1]['Density_measured']:.3f} (理想: 0.04)")
print(f"  → Input 48-56: 濃度差 {zone1.iloc[1]['Density_measured'] - zone1.iloc[2]['Density_measured']:.3f} (理想: 0.05)")
print(f"  対策: Input 48, 56のK値増加を抑制")

# 問題2: Input 104-128
print("\n【問題2】Input 104-128 (中間の下側)")
zone2 = df[(df['Input'] >= 104) & (df['Input'] <= 136)]
print(zone2[['Input', 'K', 'Density_measured', 'Target_Density', 'Density_diff']].to_string(index=False))
print(f"\n  → Input 104-112: 濃度差 {zone2.iloc[0]['Density_measured'] - zone2.iloc[1]['Density_measured']:.3f} (理想: 0.05)")
print(f"  → Input 112-120: 濃度差 {zone2.iloc[1]['Density_measured'] - zone2.iloc[2]['Density_measured']:.3f} (理想: 0.05)")
print(f"  → Input 120-128: 濃度差 {zone2.iloc[2]['Density_measured'] - zone2.iloc[3]['Density_measured']:.3f} (理想: 0.05)")
print(f"  対策: Input 112のK値を調整して勾配を均一化")

# 問題3: Input 160-192
print("\n【問題3】Input 160-192 (ハイライト寄り)")
zone3 = df[(df['Input'] >= 160) & (df['Input'] <= 192)]
print(zone3[['Input', 'K', 'Density_measured', 'Target_Density', 'Density_diff']].to_string(index=False))
print(f"\n  → Input 160-168: 濃度差 {zone3.iloc[0]['Density_measured'] - zone3.iloc[1]['Density_measured']:.3f} (理想: 0.05)")
print(f"  → Input 184-192: 濃度差 {zone3.iloc[3]['Density_measured'] - zone3.iloc[4]['Density_measured']:.3f} (理想: 0.05)")
print(f"  対策: Input 168, 192のK値差を詰める")

# 問題4: Input 248-255
print("\n【問題4】Input 248-255 (最終端)")
zone4 = df[(df['Input'] >= 240)]
print(zone4[['Input', 'K', 'Density_measured', 'Target_Density', 'Density_diff']].to_string(index=False))
print(f"\n  → Input 248-255: 濃度差 {zone4.iloc[1]['Density_measured'] - zone4.iloc[2]['Density_measured']:.3f} (理想: 0.02)")
print(f"  対策: Input 255のK値を減らして紙白に近づける")

# ===== v19への推奨調整 =====
print("\n" + "=" * 80)
print("v19への推奨K値調整")
print("=" * 80)

print("\nInput | v18 K値 | 推奨調整 | v19 K値候補")
print("------|---------|----------|-------------")

# 調整が必要なポイント
adjustments = {
    48: ("減少", -200, "急な落ち込みを緩和"),
    56: ("減少", -400, "急な落ち込みを緩和"),
    112: ("調整", +200, "ムラを均一化"),
    128: ("調整", +150, "ムラを均一化"),
    168: ("減少", -300, "段差を圧縮"),
    192: ("減少", -400, "段差を圧縮"),
    255: ("減少", -500, "紙白への到達を改善")
}

for idx, row in df.iterrows():
    inp = int(row['Input'])
    k_v18 = int(row['K'])

    if inp in adjustments:
        action, delta, reason = adjustments[inp]
        k_v19 = k_v18 + delta
        print(f"{inp:5} | {k_v18:7} | {delta:+8} | {k_v19:11} ← {reason}")
    else:
        print(f"{inp:5} | {k_v18:7} | (維持) | {k_v18:11}")

print("\n" + "=" * 80)
print("次のステップ")
print("=" * 80)
print("1. 上記調整をgenerate_v19.pyに反映")
print("2. v19カーブを生成・インストール")
print("3. 6分45秒露光でテストプリント")
print("4. 濃度測定して最終確認")
print("=" * 80)
