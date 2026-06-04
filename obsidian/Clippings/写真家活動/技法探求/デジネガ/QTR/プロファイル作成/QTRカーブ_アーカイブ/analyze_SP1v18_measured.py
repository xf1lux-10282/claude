#!/usr/bin/env python3
"""
SP1v18実測データの分析スクリプト

目的:
- V18とV7の実測濃度を比較
- 意図通りの軟調化が実現できたか検証
- Input 80-220での濃度削減量を確認
- ハイライト部分（240-255）の濃度を確認

実行日: 2026-03-19
作成者: Claude Code
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_measurement_data():
    """測定データを読み込む"""
    file_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/v2-補正/measurement_QTR-SP-18.csv"

    df = pd.read_csv(file_path)

    # 列名を整理
    df.columns = ['input', 'v18_density', 'empty', 'v7_density']
    df = df.drop('empty', axis=1)

    return df

def analyze_density_reduction(df):
    """濃度削減量を分析"""

    print("=" * 80)
    print("SP1v18実測データ分析")
    print("=" * 80)

    # 濃度差を計算
    df['density_diff'] = df['v18_density'] - df['v7_density']

    print("\n【1. 全体サマリー】")
    print(f"測定ポイント数: {len(df)}点")
    print(f"V18濃度範囲: {df['v18_density'].min():.2f}D - {df['v18_density'].max():.2f}D")
    print(f"V7濃度範囲: {df['v7_density'].min():.2f}D - {df['v7_density'].max():.2f}D")

    print("\n【2. 濃度差の統計】")
    print(f"平均濃度差: {df['density_diff'].mean():.4f}D")
    print(f"最大削減: {df['density_diff'].min():.4f}D (Input {df.loc[df['density_diff'].idxmin(), 'input']:.0f})")
    print(f"最大増加: {df['density_diff'].max():.4f}D (Input {df.loc[df['density_diff'].idxmax(), 'input']:.0f})")

    # Input範囲別の分析
    print("\n【3. Input範囲別の濃度削減】")

    ranges = [
        ("Input 0-79 (V7ベースライン)", 0, 79),
        ("Input 80-120 (段階的削減)", 80, 120),
        ("Input 121-220 (一律削減)", 121, 220),
        ("Input 221-248 (線形補間)", 221, 248),
        ("Input 249-255 (V7ベースライン)", 249, 255)
    ]

    for label, start, end in ranges:
        mask = (df['input'] >= start) & (df['input'] <= end)
        subset = df[mask]

        if len(subset) > 0:
            avg_diff = subset['density_diff'].mean()
            min_diff = subset['density_diff'].min()
            max_diff = subset['density_diff'].max()

            print(f"\n{label}")
            print(f"  平均濃度差: {avg_diff:+.4f}D")
            print(f"  範囲: {min_diff:+.4f}D 〜 {max_diff:+.4f}D")
            print(f"  測定点数: {len(subset)}点")

    # 理論値との比較
    print("\n【4. 理論値との比較】")
    print("設計値: Input 121-220で一律-1500 Quad (-0.0464D ≈ -0.05D)")

    # Input 121-220の実測値
    target_range = df[(df['input'] >= 121) & (df['input'] <= 220)]
    if len(target_range) > 0:
        actual_avg = target_range['density_diff'].mean()
        print(f"実測平均: {actual_avg:+.4f}D")
        print(f"差分: {actual_avg - (-0.0464):.4f}D")

        if abs(actual_avg - (-0.05)) < 0.01:
            print("✓ 理論値とほぼ一致（±0.01D以内）")
        else:
            print("⚠️ 理論値から乖離")

    # Input 255の確認
    print("\n【5. Input 255（最大濃度）の確認】")
    v18_max = df[df['input'] == 255]['v18_density'].values[0]
    v7_max = df[df['input'] == 255]['v7_density'].values[0]

    print(f"V18: {v18_max:.2f}D")
    print(f"V7: {v7_max:.2f}D")
    print(f"差分: {v18_max - v7_max:+.2f}D")

    if v18_max > v7_max:
        print("✓ V18がV7より濃い（意図通り）")
    else:
        print("⚠️ V18がV7より薄い（要確認）")

    return df

def plot_comparison(df):
    """比較グラフを生成"""

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    # グラフ1: 濃度カーブの比較
    ax1 = axes[0]
    ax1.plot(df['input'], df['v7_density'], 'b-o', label='V7 (Baseline)', linewidth=2, markersize=4)
    ax1.plot(df['input'], df['v18_density'], 'r-s', label='V18 (Reduced)', linewidth=2, markersize=4)

    # 範囲マーカー
    ax1.axvline(x=80, color='orange', linestyle='--', alpha=0.5, label='Start Reduction (80)')
    ax1.axvline(x=120, color='purple', linestyle='--', alpha=0.5, label='Max Reduction (120)')
    ax1.axvline(x=220, color='green', linestyle='--', alpha=0.5, label='End Reduction (220)')
    ax1.axvline(x=248, color='red', linestyle='--', alpha=0.5, label='Return to V7 (248)')

    ax1.set_xlabel('Input Value', fontsize=12)
    ax1.set_ylabel('Negative Density (D)', fontsize=12)
    ax1.set_title('SP1v18 vs V7 - Measured Density Comparison', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # グラフ2: 濃度差
    ax2 = axes[1]
    ax2.plot(df['input'], df['density_diff'], 'g-o', linewidth=2, markersize=4)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.axhline(y=-0.05, color='red', linestyle='--', alpha=0.5, label='Target: -0.05D')

    # 範囲マーカー
    ax2.axvline(x=80, color='orange', linestyle='--', alpha=0.5)
    ax2.axvline(x=120, color='purple', linestyle='--', alpha=0.5)
    ax2.axvline(x=220, color='green', linestyle='--', alpha=0.5)
    ax2.axvline(x=248, color='red', linestyle='--', alpha=0.5)

    ax2.set_xlabel('Input Value', fontsize=12)
    ax2.set_ylabel('Density Difference (V18 - V7)', fontsize=12)
    ax2.set_title('Density Reduction by SP1v18', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/SP1v18_measured_analysis.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')

    print(f"\n✓ グラフ保存: SP1v18_measured_analysis.png")

    plt.close()

def export_analysis_csv(df):
    """詳細分析データをCSV出力"""

    output_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/SP1v18_measured_analysis.csv"

    # パーセンテージ変化を追加
    df['percent_change'] = ((df['v18_density'] - df['v7_density']) / df['v7_density'] * 100).round(2)

    df.to_csv(output_path, index=False)

    print(f"✓ 詳細分析CSV保存: SP1v18_measured_analysis.csv")

def main():
    print("SP1v18実測データ分析開始\n")

    # データ読み込み
    df = load_measurement_data()

    # 濃度削減分析
    df = analyze_density_reduction(df)

    # グラフ生成
    print("\n[グラフ生成中...]")
    plot_comparison(df)

    # CSV出力
    print("\n[詳細分析CSV出力中...]")
    export_analysis_csv(df)

    print("\n" + "=" * 80)
    print("分析完了")
    print("=" * 80)

    print("\n【評価サマリー】")

    # Input 121-220の実測平均を確認
    target_range = df[(df['input'] >= 121) & (df['input'] <= 220)]
    actual_avg = target_range['density_diff'].mean()

    print(f"\n1. ミッドトーン削減（Input 121-220）")
    print(f"   目標: -0.05D")
    print(f"   実測: {actual_avg:.4f}D")

    if abs(actual_avg - (-0.05)) < 0.01:
        print("   判定: ✓ 目標達成（±0.01D以内）")
    elif abs(actual_avg - (-0.05)) < 0.02:
        print("   判定: △ ほぼ達成（±0.02D以内）")
    else:
        print("   判定: ✗ 目標未達")

    # Input 255の確認
    v18_max = df[df['input'] == 255]['v18_density'].values[0]
    v7_max = df[df['input'] == 255]['v7_density'].values[0]

    print(f"\n2. 最大濃度（Input 255）")
    print(f"   V18: {v18_max:.2f}D")
    print(f"   V7: {v7_max:.2f}D")

    if v18_max >= v7_max:
        print("   判定: ✓ V18がV7以上（露光レンジ維持）")
    else:
        print("   判定: ⚠️ V18がV7より低い（要確認）")

    # 全体評価
    print(f"\n3. 全体の軟調化効果")
    overall_avg = df['density_diff'].mean()
    print(f"   平均濃度差: {overall_avg:.4f}D")

    if overall_avg < -0.02:
        print("   判定: ✓ 明確な軟調化効果あり")
    elif overall_avg < 0:
        print("   判定: △ 軽微な軟調化効果")
    else:
        print("   判定: ✗ 軟調化効果なし")

    print("\n【次のステップ】")
    print("1. グラフを確認して実測結果を視覚的に評価")
    print("2. プラチナ/パラジウムプリントで実際の効果を確認")
    print("3. 必要に応じてSP1v19で削減量を調整")

if __name__ == "__main__":
    main()
