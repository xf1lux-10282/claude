#!/usr/bin/env python3
"""
SP1v9予測値の精度検証スクリプト

目的:
1. SP1v7の予測濃度と実測値（measurement_QTR-SP-7.csv）を比較
2. 予測誤差を定量化
3. SP1v9の予測値の信頼性を評価

実行日: 2026-03-18
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_sp1v9_predictions():
    """SP1v9の予測データを読み込み"""
    file_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-SP1v9.txt"
    df = pd.read_csv(file_path)
    return df

def load_sp7_measured():
    """SP1v7の実測データを読み込み（measurement_QTR-SP-7.csv）"""
    file_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/v2-補正/measurement_QTR-SP-7.csv"
    df = pd.read_csv(file_path)
    return df

def compare_predictions():
    """予測値と実測値を比較"""

    # データ読み込み
    sp1v9_pred = load_sp1v9_predictions()
    sp7_measured = load_sp7_measured()

    # SP1v7予測値を抽出（SP1v9.txtのSP1v7_Density列）
    # 実測値と一致するInputのみ
    comparison_data = []

    for _, row in sp7_measured.iterrows():
        inp = row['input']
        measured_d = row['negative_density']

        # SP1v9予測データからSP1v7予測値を取得
        pred_row = sp1v9_pred[sp1v9_pred['Input'] == inp]
        if not pred_row.empty:
            sp1v7_pred_d = pred_row['SP1v7_Density'].values[0]
            sp1v9_pred_d = pred_row['SP1v9_Density'].values[0]

            # 誤差計算
            sp1v7_error = measured_d - sp1v7_pred_d

            comparison_data.append({
                'Input': inp,
                'SP1v7_Predicted': sp1v7_pred_d,
                'SP1v7_Measured': measured_d,
                'SP1v7_Error': sp1v7_error,
                'SP1v9_Predicted': sp1v9_pred_d,
                'SP1v9_Change': sp1v9_pred_d - sp1v7_pred_d
            })

    df_comparison = pd.DataFrame(comparison_data)
    return df_comparison

def analyze_prediction_accuracy(df):
    """予測精度を解析"""

    print("=" * 80)
    print("SP1v7予測値と実測値の比較解析")
    print("=" * 80)

    # 統計量
    mean_error = df['SP1v7_Error'].mean()
    std_error = df['SP1v7_Error'].std()
    max_error = df['SP1v7_Error'].abs().max()
    rmse = np.sqrt((df['SP1v7_Error'] ** 2).mean())

    print(f"\n【予測誤差統計】")
    print(f"平均誤差:        {mean_error:+.4f}D")
    print(f"標準偏差:        {std_error:.4f}D")
    print(f"最大絶対誤差:    {max_error:.4f}D")
    print(f"RMSE:            {rmse:.4f}D")

    # 最大誤差の場所
    max_error_idx = df['SP1v7_Error'].abs().idxmax()
    max_error_row = df.loc[max_error_idx]
    print(f"\n【最大誤差発生地点】")
    print(f"Input: {max_error_row['Input']}")
    print(f"予測値: {max_error_row['SP1v7_Predicted']:.4f}D")
    print(f"実測値: {max_error_row['SP1v7_Measured']:.4f}D")
    print(f"誤差:   {max_error_row['SP1v7_Error']:+.4f}D")

    # 詳細テーブル
    print(f"\n{'Input':<8} {'Pred(D)':<10} {'Meas(D)':<10} {'Error(D)':<12} {'SP1v9(D)':<10} {'Change(D)':<12}")
    print("-" * 80)

    for _, row in df.iterrows():
        print(f"{row['Input']:<8} "
              f"{row['SP1v7_Predicted']:<10.4f} "
              f"{row['SP1v7_Measured']:<10.4f} "
              f"{row['SP1v7_Error']:+12.4f} "
              f"{row['SP1v9_Predicted']:<10.4f} "
              f"{row['SP1v9_Change']:+12.4f}")

    return df

def plot_comparison(df):
    """比較グラフを生成"""

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    inputs = df['Input']

    # グラフ1: 予測値 vs 実測値
    ax = axes[0, 0]
    ax.plot(inputs, df['SP1v7_Predicted'], 'o-', label='SP1v7 Predicted', linewidth=2, markersize=6)
    ax.plot(inputs, df['SP1v7_Measured'], 's-', label='SP1v7 Measured', linewidth=2, markersize=6)
    ax.plot(inputs, df['SP1v9_Predicted'], '^-', label='SP1v9 Predicted', linewidth=2, markersize=6, alpha=0.7)
    ax.set_xlabel('Input Value (0-255)', fontsize=12)
    ax.set_ylabel('Negative Density (D)', fontsize=12)
    ax.set_title('Predicted vs Measured Density', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # グラフ2: 予測誤差
    ax = axes[0, 1]
    ax.plot(inputs, df['SP1v7_Error'], 'o-', linewidth=2, markersize=6, color='red')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.axhline(y=df['SP1v7_Error'].mean(), color='blue', linestyle='--',
               label=f'Mean Error: {df["SP1v7_Error"].mean():+.4f}D', linewidth=2)
    ax.fill_between(inputs,
                      df['SP1v7_Error'].mean() - df['SP1v7_Error'].std(),
                      df['SP1v7_Error'].mean() + df['SP1v7_Error'].std(),
                      alpha=0.2, color='blue', label=f'±1σ: {df["SP1v7_Error"].std():.4f}D')
    ax.set_xlabel('Input Value (0-255)', fontsize=12)
    ax.set_ylabel('Prediction Error (Measured - Predicted) (D)', fontsize=12)
    ax.set_title('SP1v7 Prediction Error', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # グラフ3: SP1v9の変化量
    ax = axes[1, 0]
    ax.plot(inputs, df['SP1v9_Change'], 'o-', linewidth=2, markersize=6, color='green')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.axvline(x=16, color='orange', linestyle='--', label='Boost Start (Input 16)', linewidth=2)
    ax.axvline(x=128, color='purple', linestyle='--', label='Transition (Input 128)', linewidth=2)
    ax.axvline(x=244, color='red', linestyle='--', label='Adjustment End (Input 244)', linewidth=2)
    ax.set_xlabel('Input Value (0-255)', fontsize=12)
    ax.set_ylabel('Density Change (SP1v9 - SP1v7) (D)', fontsize=12)
    ax.set_title('SP1v9 Density Adjustment', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # グラフ4: 誤差分布（ヒストグラム）
    ax = axes[1, 1]
    ax.hist(df['SP1v7_Error'], bins=15, alpha=0.7, color='red', edgecolor='black')
    ax.axvline(x=0, color='black', linestyle='-', linewidth=2)
    ax.axvline(x=df['SP1v7_Error'].mean(), color='blue', linestyle='--',
               label=f'Mean: {df["SP1v7_Error"].mean():+.4f}D', linewidth=2)
    ax.set_xlabel('Prediction Error (D)', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Error Distribution', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    output_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/SP1v9_accuracy_verification.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ グラフ保存: SP1v9_accuracy_verification.png")

def main():
    print("\n" + "=" * 80)
    print("SP1v9予測精度検証スクリプト実行開始")
    print("=" * 80)

    # 比較実行
    df = compare_predictions()

    # 精度解析
    analyze_prediction_accuracy(df)

    # グラフ生成
    plot_comparison(df)

    # CSV出力
    output_csv = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/SP1v9_accuracy_verification.csv"
    df.to_csv(output_csv, index=False)
    print(f"✓ CSV保存: SP1v9_accuracy_verification.csv")

    print("\n" + "=" * 80)
    print("【結論】")
    print("=" * 80)

    rmse = np.sqrt((df['SP1v7_Error'] ** 2).mean())

    if rmse < 0.05:
        print("✓ 予測精度: 非常に良好（RMSE < 0.05D）")
        print("✓ SP1v9の予測値は信頼できます")
    elif rmse < 0.10:
        print("✓ 予測精度: 良好（RMSE < 0.10D）")
        print("✓ SP1v9の予測値はおおむね信頼できます")
        print("  注意: 一部の領域で誤差が大きい可能性があります")
    else:
        print("⚠ 予測精度: 要注意（RMSE ≥ 0.10D）")
        print("⚠ SP1v9の予測値に大きな誤差が含まれる可能性があります")
        print("  推奨: 実測テストで慎重に確認してください")

    print("\n【次のステップ】")
    print("1. 上記の予測誤差を考慮して、SP1v9をテストプリント")
    print("2. 実測濃度を測定し、予測値との比較")
    print("3. 必要に応じてSP1v10で補正")

if __name__ == "__main__":
    main()
