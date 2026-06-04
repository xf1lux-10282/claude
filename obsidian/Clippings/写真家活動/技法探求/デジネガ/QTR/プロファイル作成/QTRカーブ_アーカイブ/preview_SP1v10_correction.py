#!/usr/bin/env python3
"""
SP1v10修正案プレビュースクリプト

修正内容:
1. Input 104: V7の112の値を使用（0.47D）
2. Input 112: V7の120の値を使用（0.53D）
3. Input 120: そのまま
4. Input 128以降: V9の136以降を1ステップ前にシフト
5. Input 248: V20の255の値を使用（1.29D）
6. Input 255: そのまま

実行日: 2026-03-18
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_measurement_data():
    """測定データを読み込み"""

    # V9測定データ
    v9_file = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/v2-補正/measurement_QTR-SP-9.csv"
    df_v9 = pd.read_csv(v9_file)
    df_v9.columns = ['input', 'v9_density', 'empty', 'v7_density']

    # V7測定データ
    v7_file = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/v2-補正/measurement_QTR-SP-7.csv"
    df_v7 = pd.read_csv(v7_file)

    return df_v9, df_v7

def get_v20_value():
    """V20のInput 255の値を取得"""
    # 過去のV20データから取得（仮定値として1.29D）
    # 実際のファイルがあればそこから読み込む
    return 1.29

def create_v10_proposal(df_v9, df_v7):
    """V10の修正案を作成"""

    v10_data = []

    for _, row in df_v9.iterrows():
        inp = row['input']
        v9_d = row['v9_density']
        v7_d = row['v7_density']

        # デフォルトはV9の値
        v10_d = v9_d
        modification = "No change"

        # 修正ルール適用
        if inp == 104:
            # V7のInput 112の値を使用
            v7_112 = df_v7[df_v7['input'] == 112]['negative_density'].values
            if len(v7_112) > 0:
                v10_d = v7_112[0]
                modification = "V7[112] → 0.47D"

        elif inp == 112:
            # V7のInput 120の値を使用
            v7_120 = df_v7[df_v7['input'] == 120]['negative_density'].values
            if len(v7_120) > 0:
                v10_d = v7_120[0]
                modification = "V7[120] → 0.53D"

        elif inp == 120:
            # そのまま
            v10_d = v9_d
            modification = "Keep V9"

        elif 128 <= inp <= 240:
            # V9の1ステップ後（+8）の値を使用
            next_inp = inp + 8
            v9_next = df_v9[df_v9['input'] == next_inp]['v9_density'].values
            if len(v9_next) > 0:
                v10_d = v9_next[0]
                modification = f"V9[{next_inp}] shift"
            else:
                v10_d = v9_d
                modification = "Keep V9 (no shift)"

        elif inp == 248:
            # V20のInput 255の値を使用
            v10_d = get_v20_value()
            modification = "V20[255] → 1.29D"

        elif inp == 255:
            # そのまま
            v10_d = v9_d
            modification = "Keep V9"

        v10_data.append({
            'input': inp,
            'v7_density': v7_d,
            'v9_density': v9_d,
            'v10_density': v10_d,
            'modification': modification,
            'change_from_v9': v10_d - v9_d
        })

    return pd.DataFrame(v10_data)

def analyze_v10_proposal(df):
    """V10修正案を解析"""

    print("=" * 100)
    print("SP1v10修正案プレビュー")
    print("=" * 100)

    print("\n【修正内容詳細】")
    print(f"{'Input':<8} {'V7(D)':<10} {'V9(D)':<10} {'V10(D)':<10} {'変化(V10-V9)':<15} {'修正内容':<30}")
    print("-" * 100)

    for _, row in df.iterrows():
        if row['change_from_v9'] != 0 or row['input'] in [104, 112, 120, 128, 136, 144, 152, 248, 255]:
            print(f"{row['input']:<8} "
                  f"{row['v7_density']:<10.2f} "
                  f"{row['v9_density']:<10.2f} "
                  f"{row['v10_density']:<10.2f} "
                  f"{row['change_from_v9']:+15.2f} "
                  f"{row['modification']:<30}")

    # 勾配チェック（急激な変化がないか）
    print("\n【勾配チェック（境界線リスク）】")
    print(f"{'区間':<20} {'V9勾配(D)':<15} {'V10勾配(D)':<15} {'改善':<10}")
    print("-" * 60)

    critical_pairs = [
        (96, 104),
        (104, 112),
        (112, 120),
        (120, 128),
        (128, 136),
        (240, 248),
        (248, 255)
    ]

    for inp1, inp2 in critical_pairs:
        row1 = df[df['input'] == inp1].iloc[0]
        row2 = df[df['input'] == inp2].iloc[0]

        v9_grad = row2['v9_density'] - row1['v9_density']
        v10_grad = row2['v10_density'] - row1['v10_density']

        improvement = "✓" if abs(v10_grad) < abs(v9_grad) or abs(v10_grad) < 0.10 else "⚠"

        print(f"Input {inp1}→{inp2:<8} "
              f"{v9_grad:+15.3f} "
              f"{v10_grad:+15.3f} "
              f"{improvement:<10}")

    # 領域別統計
    print("\n【領域別統計】")
    print(f"{'領域':<30} {'V9平均(D)':<15} {'V10平均(D)':<15} {'変化(D)':<15}")
    print("-" * 75)

    regions = [
        ("Input 0-96 (ブースト前半)", df[df['input'] <= 96]),
        ("Input 104-120 (修正領域)", df[(df['input'] >= 104) & (df['input'] <= 120)]),
        ("Input 128-240 (シフト領域)", df[(df['input'] >= 128) & (df['input'] <= 240)]),
        ("Input 248-255 (ハイライト)", df[df['input'] >= 248])
    ]

    for region_name, region_df in regions:
        if len(region_df) > 0:
            v9_mean = region_df['v9_density'].mean()
            v10_mean = region_df['v10_density'].mean()
            change = v10_mean - v9_mean
            print(f"{region_name:<30} {v9_mean:<15.3f} {v10_mean:<15.3f} {change:+15.3f}")

    return df

def plot_v10_preview(df):
    """V10プレビューグラフを生成"""

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    inputs = df['input']

    # グラフ1: V7, V9, V10比較
    ax = axes[0, 0]
    ax.plot(inputs, df['v7_density'], 'o-', label='V7 Measured', linewidth=2, markersize=6, alpha=0.7)
    ax.plot(inputs, df['v9_density'], 's-', label='V9 Measured', linewidth=2, markersize=6, alpha=0.7)
    ax.plot(inputs, df['v10_density'], '^-', label='V10 Proposed', linewidth=2, markersize=6)

    # 修正箇所をハイライト
    modified = df[df['change_from_v9'] != 0]
    ax.scatter(modified['input'], modified['v10_density'],
               s=150, c='red', marker='o', edgecolors='black', linewidth=2,
               label='Modified Points', zorder=5, alpha=0.7)

    ax.set_xlabel('Input Value (0-255)', fontsize=12)
    ax.set_ylabel('Negative Density (D)', fontsize=12)
    ax.set_title('V7 vs V9 vs V10 (Proposed)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # グラフ2: V9→V10の変化量
    ax = axes[0, 1]
    ax.plot(inputs, df['change_from_v9'], 'o-', linewidth=2, markersize=6, color='red')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.axvline(x=104, color='orange', linestyle='--', alpha=0.5, label='Correction Start (104)')
    ax.axvline(x=128, color='purple', linestyle='--', alpha=0.5, label='Shift Start (128)')
    ax.axvline(x=248, color='red', linestyle='--', alpha=0.5, label='V20 Value (248)')
    ax.set_xlabel('Input Value (0-255)', fontsize=12)
    ax.set_ylabel('Density Change (V10 - V9) (D)', fontsize=12)
    ax.set_title('Modification Amount (V10 - V9)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # グラフ3: 勾配比較（V9 vs V10）
    ax = axes[1, 0]

    v9_gradients = []
    v10_gradients = []
    gradient_inputs = []

    for i in range(len(df) - 1):
        v9_grad = df.iloc[i+1]['v9_density'] - df.iloc[i]['v9_density']
        v10_grad = df.iloc[i+1]['v10_density'] - df.iloc[i]['v10_density']
        v9_gradients.append(v9_grad)
        v10_gradients.append(v10_grad)
        gradient_inputs.append(df.iloc[i+1]['input'])

    ax.plot(gradient_inputs, v9_gradients, 'o-', label='V9 Gradient', linewidth=2, markersize=4, alpha=0.7)
    ax.plot(gradient_inputs, v10_gradients, 's-', label='V10 Gradient', linewidth=2, markersize=4)
    ax.axhline(y=0.10, color='red', linestyle='--', alpha=0.5, label='Banding Risk (>0.10D)')
    ax.set_xlabel('Input Value', fontsize=12)
    ax.set_ylabel('Gradient (ΔDensity per step)', fontsize=12)
    ax.set_title('Gradient Comparison (Banding Risk)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-0.05, 0.15)

    # グラフ4: 問題領域の拡大図（Input 96-160）
    ax = axes[1, 1]
    problem_region = df[(df['input'] >= 96) & (df['input'] <= 160)]

    ax.plot(problem_region['input'], problem_region['v7_density'], 'o-',
            label='V7', linewidth=2, markersize=8, alpha=0.7)
    ax.plot(problem_region['input'], problem_region['v9_density'], 's-',
            label='V9 (Unnatural)', linewidth=2, markersize=8, alpha=0.7)
    ax.plot(problem_region['input'], problem_region['v10_density'], '^-',
            label='V10 (Corrected)', linewidth=2, markersize=8)

    # 不自然な箇所をマーク
    unnatural = problem_region[problem_region['input'].isin([104, 112, 128])]
    ax.scatter(unnatural['input'], unnatural['v9_density'],
               s=200, c='yellow', marker='o', edgecolors='red', linewidth=3,
               label='Unnatural Points', zorder=5, alpha=0.5)

    ax.set_xlabel('Input Value', fontsize=12)
    ax.set_ylabel('Negative Density (D)', fontsize=12)
    ax.set_title('Problem Region Detail (Input 96-160)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/SP1v10_preview.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ グラフ保存: SP1v10_preview.png")

def main():
    print("\n" + "=" * 100)
    print("SP1v10修正案プレビュースクリプト実行開始")
    print("=" * 100)

    # データ読み込み
    df_v9, df_v7 = load_measurement_data()

    # V10修正案作成
    df_v10 = create_v10_proposal(df_v9, df_v7)

    # 解析
    analyze_v10_proposal(df_v10)

    # グラフ生成
    plot_v10_preview(df_v10)

    # CSV出力
    output_csv = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/SP1v10_preview.csv"
    df_v10.to_csv(output_csv, index=False)
    print(f"\n✓ CSV保存: SP1v10_preview.csv")

    print("\n" + "=" * 100)
    print("【結論】")
    print("=" * 100)

    # 修正箇所の数
    modified_count = len(df_v10[df_v10['change_from_v9'] != 0])
    print(f"\n修正箇所: {modified_count}地点")

    # 最大変化
    max_change = df_v10['change_from_v9'].abs().max()
    max_change_input = df_v10[df_v10['change_from_v9'].abs() == max_change]['input'].values[0]
    print(f"最大変化: Input {max_change_input}で{max_change:.3f}D")

    # 問題領域の改善確認
    problem_region = df_v10[(df_v10['input'] >= 104) & (df_v10['input'] <= 136)]

    # V9の問題：Input 128で下がる
    v9_128_drop = problem_region[problem_region['input'] == 128]['v9_density'].values[0] - \
                   problem_region[problem_region['input'] == 120]['v9_density'].values[0]

    v10_128_drop = problem_region[problem_region['input'] == 128]['v10_density'].values[0] - \
                    problem_region[problem_region['input'] == 120]['v10_density'].values[0]

    print(f"\nInput 120→128の変化:")
    print(f"  V9: {v9_128_drop:+.3f}D（不自然な下降）")
    print(f"  V10: {v10_128_drop:+.3f}D（修正後）")

    if v10_128_drop > 0:
        print(f"  ✓ 修正により正常な上昇傾向に回復")

    print("\nこのプレビューで問題なければ、SP1v10のQuadファイル生成に進めます。")
    print("=" * 100)

if __name__ == "__main__":
    main()
