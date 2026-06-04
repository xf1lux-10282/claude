#!/usr/bin/env python3
"""
SP1v19実測データ分析スクリプト

目的:
- SP1v19カーブのネガ濃度測定データを分析
- V18, V7との比較
- ハイライト諧調拡張（Input 224-255）の効果を検証

実行日: 2026-03-19
作成者: Claude Code
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Arial Unicode MS'

def load_measurement_data():
    """測定データを読み込む"""
    csv_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/v2-補正/measurement_QTR-SP-19.csv"

    df = pd.read_csv(csv_path)

    # 列名を整理
    df.columns = ['input', 'v19_density', 'v18_density', 'v7_density']

    print("=== 測定データ読み込み ===")
    print(f"データ点数: {len(df)}")
    print(f"Input範囲: {df['input'].min()} - {df['input'].max()}")
    print(f"\nデータサンプル:")
    print(df.head(10))

    return df

def analyze_highlight_extension(df):
    """ハイライト諧調拡張（Input 224-255）の効果を分析"""

    print("\n" + "=" * 80)
    print("ハイライト諧調拡張の効果分析（Input 224-255）")
    print("=" * 80)

    # Input 224-255のデータを抽出
    highlight_df = df[df['input'] >= 224].copy()

    print(f"\n測定点数: {len(highlight_df)}点")
    print(f"Input範囲: {highlight_df['input'].min()} - {highlight_df['input'].max()}")

    # V19とV18の比較
    print("\n【V19 vs V18】")
    print(f"{'Input':<8} {'V19':<10} {'V18':<10} {'Δ(V19-V18)':<15} {'V7':<10}")
    print("-" * 60)

    for _, row in highlight_df.iterrows():
        inp = int(row['input'])
        v19 = row['v19_density']
        v18 = row['v18_density']
        v7 = row['v7_density']

        if pd.notna(v18):
            delta = v19 - v18
            print(f"{inp:<8} {v19:<10.2f} {v18:<10.2f} {delta:+.4f}D{'':<8} {v7:<10.2f}")
        else:
            print(f"{inp:<8} {v19:<10.2f} {'N/A':<10} {'N/A':<15} {v7:<10.2f}")

    # 濃度範囲の確認
    v19_min = highlight_df['v19_density'].min()
    v19_max = highlight_df['v19_density'].max()
    v19_range = v19_max - v19_min

    print(f"\n【V19ハイライト範囲】")
    print(f"最小濃度 (Input {highlight_df.loc[highlight_df['v19_density'].idxmin(), 'input']:.0f}): {v19_min:.2f}D")
    print(f"最大濃度 (Input {highlight_df.loc[highlight_df['v19_density'].idxmax(), 'input']:.0f}): {v19_max:.2f}D")
    print(f"濃度範囲: {v19_range:.2f}D")
    print(f"測定点数: {len(highlight_df)}点")
    print(f"平均ステップ: {v19_range / (len(highlight_df) - 1):.4f}D")

    # 設計値との比較
    print(f"\n【設計値との比較】")
    design_targets = {
        224: 0.9916,
        232: 1.05,
        240: 1.12,
        248: 1.19,
        255: 1.25
    }

    print(f"{'Input':<8} {'設計値':<10} {'実測値':<10} {'誤差':<10} {'判定':<10}")
    print("-" * 60)

    for inp, target in design_targets.items():
        measured_row = highlight_df[highlight_df['input'] == inp]
        if not measured_row.empty:
            measured = measured_row['v19_density'].values[0]
            error = measured - target
            judgment = "✓" if abs(error) < 0.05 else "⚠️"
            print(f"{inp:<8} {target:<10.4f} {measured:<10.2f} {error:+.4f}D{'':<4} {judgment:<10}")

def analyze_contrast_reduction(df):
    """コントラスト削減効果の維持確認（Input 121-220）"""

    print("\n" + "=" * 80)
    print("コントラスト削減効果の維持確認（Input 121-220）")
    print("=" * 80)

    # Input 121-220のデータを抽出
    midtone_df = df[(df['input'] >= 121) & (df['input'] <= 220)].copy()
    midtone_df['v19_v7_diff'] = midtone_df['v19_density'] - midtone_df['v7_density']
    midtone_df['v18_v7_diff'] = midtone_df['v18_density'] - midtone_df['v7_density']

    print(f"\n測定点数: {len(midtone_df)}点")

    # V19とV18の削減効果を比較
    v19_avg_reduction = midtone_df['v19_v7_diff'].mean()
    v18_avg_reduction = midtone_df['v18_v7_diff'].mean()

    print(f"\n【平均削減効果】")
    print(f"V19: {v19_avg_reduction:.4f}D")
    print(f"V18: {v18_avg_reduction:.4f}D")
    print(f"差分: {v19_avg_reduction - v18_avg_reduction:+.4f}D")

    if abs(v19_avg_reduction - v18_avg_reduction) < 0.01:
        print(f"判定: ✓ V19はV18のコントラスト削減効果を維持")
    else:
        print(f"判定: ⚠️ V19とV18で削減効果に差異あり")

def plot_comparison(df):
    """比較グラフを生成"""

    fig, axes = plt.subplots(3, 1, figsize=(14, 12))

    # グラフ1: 全体の濃度比較
    ax1 = axes[0]
    ax1.plot(df['input'], df['v7_density'], 'b-o', label='V7 (Original)', linewidth=2, markersize=4, alpha=0.5)
    ax1.plot(df['input'], df['v18_density'], 'g-s', label='V18 (Contrast reduced)', linewidth=2, markersize=4, alpha=0.7)
    ax1.plot(df['input'], df['v19_density'], 'r-^', label='V19 (Highlight extended)', linewidth=2, markersize=4)

    ax1.axvline(x=224, color='orange', linestyle='--', alpha=0.5, label='Highlight Extension Start')
    ax1.axvspan(224, 255, color='orange', alpha=0.1)

    ax1.set_xlabel('Input Value', fontsize=12)
    ax1.set_ylabel('Negative Density (D)', fontsize=12)
    ax1.set_title('SP1v19 Measured Density - Full Range Comparison', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # グラフ2: ハイライト部分の拡大（Input 200-255）
    ax2 = axes[1]
    highlight_df = df[df['input'] >= 200].copy()

    ax2.plot(highlight_df['input'], highlight_df['v7_density'], 'b-o', label='V7', linewidth=2, markersize=5, alpha=0.5)
    ax2.plot(highlight_df['input'], highlight_df['v18_density'], 'g-s', label='V18', linewidth=2, markersize=5, alpha=0.7)
    ax2.plot(highlight_df['input'], highlight_df['v19_density'], 'r-^', label='V19', linewidth=2, markersize=5)

    ax2.axvline(x=224, color='orange', linestyle='--', alpha=0.5)
    ax2.axhline(y=1.05, color='red', linestyle=':', alpha=0.3, label='Target 1.05D')
    ax2.axhline(y=1.25, color='red', linestyle=':', alpha=0.3, label='Target 1.25D')

    ax2.set_xlabel('Input Value', fontsize=12)
    ax2.set_ylabel('Negative Density (D)', fontsize=12)
    ax2.set_title('Highlight Detail (Input 200-255)', fontsize=14)
    ax2.set_xlim(200, 255)
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)

    # グラフ3: V7との濃度差分（コントラスト削減効果）
    ax3 = axes[2]

    # V19-V7とV18-V7の差分を計算
    df_valid = df.dropna(subset=['v18_density']).copy()
    df_valid['v19_v7_diff'] = df_valid['v19_density'] - df_valid['v7_density']
    df_valid['v18_v7_diff'] = df_valid['v18_density'] - df_valid['v7_density']

    ax3.plot(df_valid['input'], df_valid['v18_v7_diff'], 'g-s', label='V18 - V7', linewidth=2, markersize=4, alpha=0.7)
    ax3.plot(df_valid['input'], df_valid['v19_v7_diff'], 'r-^', label='V19 - V7', linewidth=2, markersize=4)

    ax3.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    ax3.axhline(y=-0.05, color='red', linestyle='--', alpha=0.3, label='Target -0.05D')
    ax3.axvline(x=224, color='orange', linestyle='--', alpha=0.5)
    ax3.axvspan(121, 220, color='blue', alpha=0.1, label='Contrast Reduction Zone')
    ax3.axvspan(224, 255, color='orange', alpha=0.1, label='Highlight Extension Zone')

    ax3.set_xlabel('Input Value', fontsize=12)
    ax3.set_ylabel('Density Difference (D)', fontsize=12)
    ax3.set_title('Contrast Reduction Effect (Density Difference from V7)', fontsize=14)
    ax3.legend(loc='lower left')
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/SP1v19_measured_analysis.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ グラフ保存: SP1v19_measured_analysis.png")

    plt.close()

def save_analysis_csv(df):
    """分析結果をCSVに保存"""

    # 差分を計算
    df_export = df.copy()
    df_export['v19_v7_diff'] = df_export['v19_density'] - df_export['v7_density']
    df_export['v19_v18_diff'] = df_export['v19_density'] - df_export['v18_density']
    df_export['v18_v7_diff'] = df_export['v18_density'] - df_export['v7_density']

    output_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/SP1v19_measured_analysis.csv"
    df_export.to_csv(output_path, index=False, float_format='%.4f')
    print(f"✓ CSV保存: SP1v19_measured_analysis.csv")

def main():
    print("=" * 80)
    print("SP1v19実測データ分析")
    print("=" * 80)

    # データ読み込み
    df = load_measurement_data()

    # ハイライト諧調拡張の効果分析
    analyze_highlight_extension(df)

    # コントラスト削減効果の維持確認
    analyze_contrast_reduction(df)

    # グラフ生成
    print("\n" + "=" * 80)
    print("比較グラフ生成")
    print("=" * 80)
    plot_comparison(df)

    # CSV保存
    print("\n" + "=" * 80)
    print("分析結果保存")
    print("=" * 80)
    save_analysis_csv(df)

    # サマリー
    print("\n" + "=" * 80)
    print("分析完了")
    print("=" * 80)

    print("\n【生成ファイル】")
    print("- SP1v19_measured_analysis.png")
    print("- SP1v19_measured_analysis.csv")

    print("\n【次のステップ】")
    print("1. グラフを確認してハイライト諧調拡張の効果を評価")
    print("2. Input 224-255の濃度範囲が期待通りか確認")
    print("3. V18のコントラスト削減効果が維持されているか確認")
    print("4. 実際のPt/Pdプリントで目視確認")

if __name__ == "__main__":
    main()
