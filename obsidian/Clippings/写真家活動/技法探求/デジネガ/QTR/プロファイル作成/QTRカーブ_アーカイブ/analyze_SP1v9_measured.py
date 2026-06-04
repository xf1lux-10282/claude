#!/usr/bin/env python3
"""
SP1v9実測値解析スクリプト

目的:
1. SP1v9とSP1v7の実測ネガ濃度を比較
2. 調整が意図通りに機能したか検証
3. 次のステップ（SP1v10）の必要性を判断

実行日: 2026-03-18
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_measurement_data():
    """測定データを読み込み"""
    file_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/v2-補正/measurement_QTR-SP-9.csv"
    df = pd.read_csv(file_path)

    # カラム名を整理
    df.columns = ['input', 'v9_density', 'empty', 'v7_density']
    df = df[['input', 'v9_density', 'v7_density']].copy()

    # 紙白を引いて実際のインク濃度増加分を計算
    paper_base = 0.07
    df['v9_ink'] = df['v9_density'] - paper_base
    df['v7_ink'] = df['v7_density'] - paper_base

    # 変化量
    df['density_change'] = df['v9_density'] - df['v7_density']
    df['ink_change'] = df['v9_ink'] - df['v7_ink']

    return df

def analyze_changes(df):
    """変化を解析"""

    print("=" * 90)
    print("SP1v9実測値解析 - SP1v7との比較")
    print("=" * 90)

    # 領域ごとの解析
    regions = [
        ("Input 0-15 (変更なし)", df[df['input'] <= 15]),
        ("Input 16-127 (ブースト領域)", df[(df['input'] >= 16) & (df['input'] <= 127)]),
        ("Input 128-243 (削減領域)", df[(df['input'] >= 128) & (df['input'] <= 243)]),
        ("Input 244-255 (変更なし)", df[df['input'] >= 244])
    ]

    print("\n【領域別解析】")
    print(f"{'領域':<30} {'平均変化(D)':<15} {'最大変化(D)':<15} {'最小変化(D)':<15}")
    print("-" * 90)

    for region_name, region_df in regions:
        if len(region_df) > 0:
            mean_change = region_df['density_change'].mean()
            max_change = region_df['density_change'].max()
            min_change = region_df['density_change'].min()
            print(f"{region_name:<30} {mean_change:+15.4f} {max_change:+15.4f} {min_change:+15.4f}")

    # 詳細テーブル
    print("\n【詳細比較テーブル】")
    print(f"{'Input':<8} {'V7(D)':<10} {'V9(D)':<10} {'変化(D)':<12} {'V7_ink':<10} {'V9_ink':<10} {'Ink変化':<12}")
    print("-" * 90)

    for _, row in df.iterrows():
        print(f"{row['input']:<8} "
              f"{row['v7_density']:<10.2f} "
              f"{row['v9_density']:<10.2f} "
              f"{row['density_change']:+12.2f} "
              f"{row['v7_ink']:<10.2f} "
              f"{row['v9_ink']:<10.2f} "
              f"{row['ink_change']:+12.2f}")

    return df

def evaluate_effectiveness(df):
    """調整の効果を評価"""

    print("\n" + "=" * 90)
    print("【調整効果の評価】")
    print("=" * 90)

    # Input 16-127のブースト効果
    boost_region = df[(df['input'] >= 16) & (df['input'] <= 127)]
    boost_mean = boost_region['density_change'].mean()
    boost_target = 0.05  # 目標: +0.05-0.10D

    print(f"\n1. Input 16-127 (シャドウ軟調化)")
    print(f"   目標: +0.05〜+0.10D")
    print(f"   実測平均: {boost_mean:+.4f}D")

    if 0.03 <= boost_mean <= 0.12:
        print(f"   ✓ 効果あり（目標範囲内）")
    elif boost_mean > 0:
        print(f"   △ 効果は見られるが、目標より{'大きい' if boost_mean > 0.12 else '小さい'}")
    else:
        print(f"   ✗ 効果なし（逆効果）")

    # Input 128-243の削減効果
    reduction_region = df[(df['input'] >= 128) & (df['input'] <= 243)]
    reduction_mean = reduction_region['density_change'].mean()
    reduction_target = -0.04  # 目標: -0.05〜-0.03D

    print(f"\n2. Input 128-243 (コントラスト圧縮)")
    print(f"   目標: -0.05〜-0.03D")
    print(f"   実測平均: {reduction_mean:+.4f}D")

    if -0.06 <= reduction_mean <= -0.02:
        print(f"   ✓ 効果あり（目標範囲内）")
    elif reduction_mean < 0:
        print(f"   △ 効果は見られるが、目標より{'大きい' if reduction_mean < -0.06 else '小さい'}")
    else:
        print(f"   ✗ 効果なし（逆効果）")

    # Input 244-255の維持確認
    maintain_region = df[df['input'] >= 244]
    maintain_mean = maintain_region['density_change'].mean()

    print(f"\n3. Input 244-255 (露光レンジ維持)")
    print(f"   目標: 変更なし（0.00D）")
    print(f"   実測平均: {maintain_mean:+.4f}D")

    if abs(maintain_mean) <= 0.02:
        print(f"   ✓ 正常に維持")
    else:
        print(f"   ⚠ 予期しない変化あり")

    # 境界線リスクの確認
    print(f"\n4. 境界線リスク確認")
    input_15_16 = df[df['input'].isin([8, 16])].copy()
    if len(input_15_16) == 2:
        diff = input_15_16.iloc[1]['v9_density'] - input_15_16.iloc[0]['v9_density']
        print(f"   Input 8→16: {diff:.2f}D差")
        if diff > 0.10:
            print(f"   ⚠ 急激な濃度変化（バンディングリスク）")
        else:
            print(f"   ✓ 問題なし")

    return boost_mean, reduction_mean, maintain_mean

def plot_comparison(df):
    """比較グラフを生成"""

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    inputs = df['input']

    # グラフ1: ネガ濃度比較
    ax = axes[0, 0]
    ax.plot(inputs, df['v7_density'], 'o-', label='SP1v7 Measured', linewidth=2, markersize=6)
    ax.plot(inputs, df['v9_density'], 's-', label='SP1v9 Measured', linewidth=2, markersize=6)
    ax.axvline(x=16, color='orange', linestyle='--', alpha=0.5, label='Boost Start (16)')
    ax.axvline(x=128, color='purple', linestyle='--', alpha=0.5, label='Transition (128)')
    ax.axvline(x=244, color='red', linestyle='--', alpha=0.5, label='Adjust End (244)')
    ax.set_xlabel('Input Value (0-255)', fontsize=12)
    ax.set_ylabel('Negative Density (D)', fontsize=12)
    ax.set_title('SP1v7 vs SP1v9 Measured Density', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # グラフ2: 濃度変化量
    ax = axes[0, 1]
    ax.plot(inputs, df['density_change'], 'o-', linewidth=2, markersize=6, color='green')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.axhline(y=0.05, color='blue', linestyle='--', alpha=0.5, label='Target Boost (+0.05D)')
    ax.axhline(y=-0.04, color='red', linestyle='--', alpha=0.5, label='Target Reduction (-0.04D)')
    ax.axvline(x=16, color='orange', linestyle='--', alpha=0.3)
    ax.axvline(x=128, color='purple', linestyle='--', alpha=0.3)
    ax.axvline(x=244, color='red', linestyle='--', alpha=0.3)
    ax.set_xlabel('Input Value (0-255)', fontsize=12)
    ax.set_ylabel('Density Change (V9 - V7) (D)', fontsize=12)
    ax.set_title('Density Change (SP1v9 - SP1v7)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # グラフ3: インク濃度増加分（紙白補正後）
    ax = axes[1, 0]
    ax.plot(inputs, df['v7_ink'], 'o-', label='SP1v7 Ink', linewidth=2, markersize=6, alpha=0.7)
    ax.plot(inputs, df['v9_ink'], 's-', label='SP1v9 Ink', linewidth=2, markersize=6, alpha=0.7)
    ax.set_xlabel('Input Value (0-255)', fontsize=12)
    ax.set_ylabel('Ink Density (Paper-corrected) (D)', fontsize=12)
    ax.set_title('Ink Density Increase (Paper Base 0.07D removed)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # グラフ4: 領域別の変化分布
    ax = axes[1, 1]

    regions_data = [
        df[df['input'] <= 15]['density_change'].values,
        df[(df['input'] >= 16) & (df['input'] <= 127)]['density_change'].values,
        df[(df['input'] >= 128) & (df['input'] <= 243)]['density_change'].values,
        df[df['input'] >= 244]['density_change'].values
    ]

    positions = [1, 2, 3, 4]
    labels = ['0-15\n(No change)', '16-127\n(Boost)', '128-243\n(Reduction)', '244-255\n(No change)']

    bp = ax.boxplot(regions_data, positions=positions, labels=labels, patch_artist=True)

    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')

    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_ylabel('Density Change (D)', fontsize=12)
    ax.set_title('Density Change Distribution by Region', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    output_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/SP1v9_measured_analysis.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ グラフ保存: SP1v9_measured_analysis.png")

def recommend_next_steps(boost_mean, reduction_mean, maintain_mean):
    """次のステップを推奨"""

    print("\n" + "=" * 90)
    print("【次のステップの推奨】")
    print("=" * 90)

    # 判定ロジック
    boost_ok = 0.03 <= boost_mean <= 0.12
    reduction_ok = -0.06 <= reduction_mean <= -0.02
    maintain_ok = abs(maintain_mean) <= 0.02

    if boost_ok and reduction_ok and maintain_ok:
        print("\n✓ SP1v9は意図通りに機能しています")
        print("\n推奨アクション:")
        print("1. SP1v9でテストプリント実行")
        print("2. コントラストが適切か確認")
        print("3. 必要に応じて微調整（SP1v10）")

    elif boost_ok and not reduction_ok:
        print("\n△ シャドウのブーストは成功、ハイライト削減は不十分")
        print("\n推奨アクション:")
        print("1. Input 128-243の削減量を増やす（-0.05→-0.08D程度）")
        print("2. SP1v10で再調整")

    elif not boost_ok and reduction_ok:
        print("\n△ ハイライト削減は成功、シャドウブーストは不十分")
        print("\n推奨アクション:")
        print("1. Input 16-127のブースト量を増やす（+0.05→+0.08D程度）")
        print("2. SP1v10で再調整")

    else:
        print("\n⚠ 調整が期待通りに機能していません")
        print("\n推奨アクション:")
        print("1. Quadカーブ生成ロジックを見直し")
        print("2. 実測値ベースで完全再計算（SP1v10）")

def main():
    print("\n" + "=" * 90)
    print("SP1v9実測値解析スクリプト実行開始")
    print("=" * 90)

    # データ読み込み
    df = load_measurement_data()

    # 変化解析
    analyze_changes(df)

    # 効果評価
    boost_mean, reduction_mean, maintain_mean = evaluate_effectiveness(df)

    # グラフ生成
    plot_comparison(df)

    # 次のステップ推奨
    recommend_next_steps(boost_mean, reduction_mean, maintain_mean)

    # CSV出力
    output_csv = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/SP1v9_measured_analysis.csv"
    df.to_csv(output_csv, index=False)
    print(f"\n✓ CSV保存: SP1v9_measured_analysis.csv")

    print("\n" + "=" * 90)
    print("解析完了")
    print("=" * 90)

if __name__ == "__main__":
    main()
