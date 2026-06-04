#!/usr/bin/env python3
"""
SP1v21生成スクリプト（修正版 - V19実測値ベース）

設計方針:
- **V19実測値を基準として使用**（重要：V19設計値ではない）
- Input 232: 1.08D（実測値、変更なし）
- Input 240: 1.17D（実測） → 1.15D（目標）[-0.02D調整]
- Input 248: 1.24D（実測） → 1.20D（目標）[-0.04D調整]
- Input 255: 1.29D（実測） → 1.25D（目標）[-0.04D調整]
- 中間値は比例配分で補間（急激な変化を避ける）

根拠:
- V19実測データ: measurement_QTR-SP-19.csv
- V19設計値（1.12D/1.19D/1.25D）からではなく、実測値から調整する

日付: 2026-03-19
作成者: Claude Code
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Arial Unicode MS'

def density_to_quad(density):
    """濃度値をQuad値に変換"""
    return round(density * 55891 / 1.73)

def quad_to_density(quad):
    """Quad値を濃度値に変換"""
    return quad * 1.73 / 55891

def load_v19_curve():
    """V19カーブを読み込む"""
    v19_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-SP1v19.quad"

    with open(v19_path, 'r') as f:
        lines = f.readlines()

    # Quad値を抽出（コメント行をスキップ）
    v19_quads = []
    for line in lines:
        line = line.strip()
        # コメント行と空行をスキップ
        if not line or line.startswith('#'):
            continue

        # 数値のみの行を抽出
        try:
            quad = int(line)
            v19_quads.append(quad)
        except ValueError:
            # 数値に変換できない場合はスキップ
            continue

        # Input 0-255の256点を取得したら終了
        if len(v19_quads) == 256:
            break

    return np.array(v19_quads)

def proportional_interpolation(start_input, end_input, start_quad, end_quad):
    """
    比例配分による補間

    Parameters:
    - start_input: 開始Input値
    - end_input: 終了Input値
    - start_quad: 開始Quad値
    - end_quad: 終了Quad値

    Returns:
    - 中間値のQuad配列（start_inputとend_inputを含む）
    """
    num_points = end_input - start_input + 1
    quads = np.linspace(start_quad, end_quad, num_points)
    return np.round(quads).astype(int)

def generate_v21_curve():
    """V21カーブを生成"""

    print("=" * 80)
    print("SP1v21カーブ生成（V19ベース、-0.04D調整）")
    print("=" * 80)

    # V19カーブを読み込み
    print("\n【ステップ1】V19カーブ読み込み")
    v19_quads = load_v19_curve()
    print(f"✓ V19カーブ読み込み完了: {len(v19_quads)}点")

    # V21カーブを初期化（V19のコピー）
    v21_quads = v19_quads.copy()

    # アンカーポイントの調整値を計算
    print("\n【ステップ2】アンカーポイント調整")
    delta_quad_02 = density_to_quad(0.02)  # -0.02D (for Input 240)
    delta_quad_04 = density_to_quad(0.04)  # -0.04D (for Input 248, 255)
    print(f"調整量: -0.02D = -{delta_quad_02} Quad (Input 240)")
    print(f"調整量: -0.04D = -{delta_quad_04} Quad (Input 248, 255)")

    # V19実測値（measurement_QTR-SP-19.csv）とV21ターゲット
    # V19実測: 232=1.08D, 240=1.17D, 248=1.24D, 255=1.29D
    # V21目標: 232=1.08D, 240=1.15D, 248=1.20D, 255=1.25D

    # 重要: V19のQuad値から差分を引く（濃度値を直接Quad変換するのではない）
    v19_measured_densities = {
        232: 1.08,  # 実測値（変更なし）
        240: 1.17,  # 実測値
        248: 1.24,  # 実測値
        255: 1.29   # 実測値
    }

    v21_target_densities = {
        232: 1.08,  # 変更なし
        240: 1.15,  # 1.17 - 0.02
        248: 1.20,  # 1.24 - 0.04
        255: 1.25   # 1.29 - 0.04
    }

    # V21のQuad値を計算（V19 Quadから差分を引く）
    anchor_points = {
        232: (v19_quads[232], v19_measured_densities[232], v19_quads[232], "unchanged"),
        240: (v19_quads[240], v19_measured_densities[240], v19_quads[240] - delta_quad_02, f"-{delta_quad_02}"),
        248: (v19_quads[248], v19_measured_densities[248], v19_quads[248] - delta_quad_04, f"-{delta_quad_04}"),
        255: (v19_quads[255], v19_measured_densities[255], v19_quads[255] - delta_quad_04, f"-{delta_quad_04}")
    }

    print(f"\n{'Input':<8} {'V19 Quad':<12} {'V19実測D':<12} {'V21 Quad':<12} {'V21目標D':<12} {'調整':<12}")
    print("-" * 80)
    for inp, (v19_q, v19_d, v21_q, adj) in anchor_points.items():
        v21_d = quad_to_density(v21_q)
        print(f"{inp:<8} {v19_q:<12} {v19_d:<12.4f} {v21_q:<12} {v21_d:<12.4f} {adj:<12}")

    # 比例配分による中間値の補間
    print("\n【ステップ3】比例配分による補間")

    # 範囲1: Input 233-239（232と240の間）
    print("\n範囲1: Input 233-239（232と240の間）")
    range1 = proportional_interpolation(232, 240, anchor_points[232][2], anchor_points[240][2])
    v21_quads[232:241] = range1
    print(f"  232: {range1[0]} Quad ({quad_to_density(range1[0]):.4f}D)")
    print(f"  236: {range1[4]} Quad ({quad_to_density(range1[4]):.4f}D)")
    print(f"  240: {range1[8]} Quad ({quad_to_density(range1[8]):.4f}D)")

    # 範囲2: Input 241-247（240と248の間）
    print("\n範囲2: Input 241-247（240と248の間）")
    range2 = proportional_interpolation(240, 248, anchor_points[240][2], anchor_points[248][2])
    v21_quads[240:249] = range2
    print(f"  240: {range2[0]} Quad ({quad_to_density(range2[0]):.4f}D)")
    print(f"  244: {range2[4]} Quad ({quad_to_density(range2[4]):.4f}D)")
    print(f"  248: {range2[8]} Quad ({quad_to_density(range2[8]):.4f}D)")

    # 範囲3: Input 249-254（248と255の間）
    print("\n範囲3: Input 249-254（248と255の間）")
    range3 = proportional_interpolation(248, 255, anchor_points[248][2], anchor_points[255][2])
    v21_quads[248:256] = range3
    print(f"  248: {range3[0]} Quad ({quad_to_density(range3[0]):.4f}D)")
    print(f"  251: {range3[3]} Quad ({quad_to_density(range3[3]):.4f}D)")
    print(f"  255: {range3[7]} Quad ({quad_to_density(range3[7]):.4f}D)")

    return v19_quads, v21_quads, anchor_points

def verify_monotonic_and_banding(v21_quads):
    """単調増加とバンディングリスクを検証"""

    print("\n" + "=" * 80)
    print("検証: 単調増加とバンディングリスク")
    print("=" * 80)

    # 単調増加の検証
    violations = []
    for i in range(1, len(v21_quads)):
        if v21_quads[i] <= v21_quads[i-1]:
            violations.append((i, v21_quads[i-1], v21_quads[i]))

    if violations:
        print(f"\n⚠️ 単調増加違反: {len(violations)}箇所")
        for inp, prev_q, curr_q in violations[:5]:
            print(f"  Input {inp}: {prev_q} → {curr_q} (差分: {curr_q - prev_q})")
    else:
        print("\n✓ 単調増加: 問題なし")

    # バンディングリスク（差分<50）の検証
    banding_risks = []
    for i in range(1, len(v21_quads)):
        diff = v21_quads[i] - v21_quads[i-1]
        if 0 < diff < 50:
            banding_risks.append((i, diff))

    if banding_risks:
        print(f"\n⚠️ バンディングリスク: {len(banding_risks)}箇所（差分<50）")
        for inp, diff in banding_risks[:10]:
            print(f"  Input {inp}: 差分={diff} Quad")
    else:
        print("\n✓ バンディングリスク: なし")

    return len(violations) == 0, len(banding_risks)

def plot_comparison(v19_quads, v21_quads, anchor_points):
    """V19とV21の比較グラフを生成"""

    fig, axes = plt.subplots(3, 1, figsize=(14, 12))

    # 濃度変換
    v19_densities = np.array([quad_to_density(q) for q in v19_quads])
    v21_densities = np.array([quad_to_density(q) for q in v21_quads])
    inputs = np.arange(256)

    # グラフ1: 全体の濃度比較
    ax1 = axes[0]
    ax1.plot(inputs, v19_densities, 'b-o', label='V19 (Base)', linewidth=2, markersize=3, alpha=0.7)
    ax1.plot(inputs, v21_densities, 'r-^', label='V21 (Adjusted -0.04D)', linewidth=2, markersize=3)

    # アンカーポイントをマーク
    for inp in [232, 240, 248, 255]:
        ax1.axvline(x=inp, color='gray', linestyle='--', alpha=0.3)
        ax1.plot(inp, quad_to_density(anchor_points[inp][2]), 'go', markersize=8, label=f'Input {inp}' if inp == 232 else '')

    ax1.axvspan(232, 255, color='orange', alpha=0.1, label='Adjustment Zone')
    ax1.set_xlabel('Input Value', fontsize=12)
    ax1.set_ylabel('Negative Density (D)', fontsize=12)
    ax1.set_title('SP1v21 vs V19 - Full Range Comparison', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # グラフ2: ハイライト部分の拡大（Input 220-255）
    ax2 = axes[1]
    highlight_range = inputs >= 220
    ax2.plot(inputs[highlight_range], v19_densities[highlight_range], 'b-o', label='V19', linewidth=2, markersize=5, alpha=0.7)
    ax2.plot(inputs[highlight_range], v21_densities[highlight_range], 'r-^', label='V21', linewidth=2, markersize=5)

    # アンカーポイント
    for inp in [232, 240, 248, 255]:
        ax2.axvline(x=inp, color='gray', linestyle='--', alpha=0.5)
        ax2.plot(inp, quad_to_density(anchor_points[inp][0]), 'bo', markersize=8, alpha=0.5)
        ax2.plot(inp, quad_to_density(anchor_points[inp][2]), 'ro', markersize=8)

        # 調整量を注釈
        if inp == 240:
            ax2.annotate(f'-0.02D', xy=(inp, quad_to_density(anchor_points[inp][2])),
                        xytext=(5, -10), textcoords='offset points', fontsize=9, color='red')
        elif inp in [248, 255]:
            ax2.annotate(f'-0.04D', xy=(inp, quad_to_density(anchor_points[inp][2])),
                        xytext=(5, -10), textcoords='offset points', fontsize=9, color='red')

    ax2.set_xlabel('Input Value', fontsize=12)
    ax2.set_ylabel('Negative Density (D)', fontsize=12)
    ax2.set_title('Highlight Detail (Input 220-255)', fontsize=14)
    ax2.set_xlim(220, 255)
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)

    # グラフ3: 濃度差分（V21 - V19）
    ax3 = axes[2]
    density_diff = v21_densities - v19_densities
    ax3.plot(inputs, density_diff, 'g-', linewidth=2)
    ax3.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    ax3.axhline(y=-0.04, color='red', linestyle='--', alpha=0.5, label='Target -0.04D')

    # アンカーポイント
    for inp in [232, 240, 248, 255]:
        ax3.axvline(x=inp, color='gray', linestyle='--', alpha=0.3)
        ax3.plot(inp, density_diff[inp], 'ro', markersize=8)

    ax3.axvspan(232, 255, color='orange', alpha=0.1)
    ax3.set_xlabel('Input Value', fontsize=12)
    ax3.set_ylabel('Density Difference (V21 - V19)', fontsize=12)
    ax3.set_title('Adjustment Amount by Input', fontsize=14)
    ax3.legend(loc='lower left')
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/SP1v21_comparison.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ グラフ保存: SP1v21_comparison.png")

    plt.close()

def save_quad_file(v21_quads):
    """V21 .quadファイルを保存（V7テンプレート使用 - ルール4）"""

    print("\n" + "=" * 80)
    print(".quadファイル生成（V7テンプレート準拠）")
    print("=" * 80)

    # V7をテンプレートとして読み込み（ルール4）
    v7_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-SP1v7.quad"

    with open(v7_path, 'r') as f:
        v7_lines = f.readlines()

    # 新しいファイルの内容を構築
    output_lines = []

    # ヘッダー（1-14行目）をV21用に変更
    output_lines.append("## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n")
    output_lines.append("# QuadProfile Version 2.8.0\n")
    output_lines.append("# PX1V-PtPd-SP1v21 - Highlight adjustment from V19 measurement\n")
    output_lines.append("# Input 0-231: V19 baseline\n")
    output_lines.append("# Input 232-255: V19 with differentiated adjustment\n")
    output_lines.append("#   Input 240: -0.02D (V19 measured: 1.17D → Target: 1.15D)\n")
    output_lines.append("#   Input 248: -0.04D (V19 measured: 1.24D → Target: 1.20D)\n")
    output_lines.append("#   Input 255: -0.04D (V19 measured: 1.29D → Target: 1.25D)\n")
    output_lines.append("# Intermediate values: proportional interpolation\n")
    output_lines.append("# Expected: Measured density closer to design targets\n")
    output_lines.append("# Generated: 2026-03-19 by Claude Code\n")
    output_lines.append("#\n")
    output_lines.append("# ink limits: K=100% C=100% M=100% Y=100% LC=100% LM=100% LK=100% LLK=100% V=100% MK=100%\n")
    output_lines.append("#\n")

    # Kチャンネル
    output_lines.append("# K curve\n")
    for quad in v21_quads:
        output_lines.append(f"{quad}\n")

    # 残りのチャンネル（C, M, Y, LC, LM, LK, LLK, V, MK）はV7から
    in_k_channel = False
    skip_until_next_channel = False

    for line in v7_lines:
        if line.strip() == "# K curve":
            in_k_channel = True
            skip_until_next_channel = True
            continue
        elif line.strip() == "# C curve":
            skip_until_next_channel = False

        if not skip_until_next_channel:
            output_lines.append(line)

    # ファイル保存
    output_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-SP1v21.quad"

    with open(output_path, 'w') as f:
        f.writelines(output_lines)

    print(f"\n✓ .quadファイル保存: PX1V-PtPd-SP1v21.quad")
    print(f"✓ 行数: {len(output_lines)}行")

    # ファイル検証
    if len(output_lines) < 2500:
        print("⚠️ 警告: ファイル行数が少ない可能性があります")
    else:
        print("✓ V7テンプレート形式（2500+行）で生成されました")

    # サンプル表示（Kチャンネルの重要なポイント）
    print(f"\n【Kチャンネルサンプル】")
    print(f"Input 232: {v21_quads[232]} Quad ({quad_to_density(v21_quads[232]):.4f}D)")
    print(f"Input 240: {v21_quads[240]} Quad ({quad_to_density(v21_quads[240]):.4f}D)")
    print(f"Input 248: {v21_quads[248]} Quad ({quad_to_density(v21_quads[248]):.4f}D)")
    print(f"Input 255: {v21_quads[255]} Quad ({quad_to_density(v21_quads[255]):.4f}D)")

    return output_path

def save_design_csv(v19_quads, v21_quads, anchor_points):
    """設計データをCSVに保存"""

    # データフレーム作成
    data = {
        'input': range(256),
        'v19_quad': v19_quads,
        'v19_density': [quad_to_density(q) for q in v19_quads],
        'v21_quad': v21_quads,
        'v21_density': [quad_to_density(q) for q in v21_quads],
        'quad_diff': v21_quads - v19_quads,
        'density_diff': [quad_to_density(v21_quads[i]) - quad_to_density(v19_quads[i]) for i in range(256)]
    }

    df = pd.DataFrame(data)

    output_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/SP1v21_design.csv"
    df.to_csv(output_path, index=False, float_format='%.4f')
    print(f"✓ CSV保存: SP1v21_design.csv")

def main():
    print("=" * 80)
    print("SP1v21カーブ生成（V19実測値ベース、比例配分補間）")
    print("=" * 80)
    print("\n設計方針:")
    print("- V19実測値を基準として使用（重要：設計値ではなく実測値）")
    print("- Input 232: 1.08D（変更なし）")
    print("- Input 240: 1.17D（実測） → 1.15D（目標）[-0.02D]")
    print("- Input 248: 1.24D（実測） → 1.20D（目標）[-0.04D]")
    print("- Input 255: 1.29D（実測） → 1.25D（目標）[-0.04D]")
    print("- 中間値は比例配分で補間")

    # V21カーブ生成
    v19_quads, v21_quads, anchor_points = generate_v21_curve()

    # 検証
    is_monotonic, banding_count = verify_monotonic_and_banding(v21_quads)

    # グラフ生成
    print("\n" + "=" * 80)
    print("比較グラフ生成")
    print("=" * 80)
    plot_comparison(v19_quads, v21_quads, anchor_points)

    # .quadファイル保存
    quad_path = save_quad_file(v21_quads)

    # CSV保存
    print("\n" + "=" * 80)
    print("設計データ保存")
    print("=" * 80)
    save_design_csv(v19_quads, v21_quads, anchor_points)

    # サマリー
    print("\n" + "=" * 80)
    print("生成完了")
    print("=" * 80)

    print("\n【生成ファイル】")
    print("- PX1V-PtPd-SP1v21.quad")
    print("- SP1v21_comparison.png")
    print("- SP1v21_design.csv")

    print("\n【検証結果】")
    print(f"- 単調増加: {'✓ OK' if is_monotonic else '⚠️ 違反あり'}")
    print(f"- バンディングリスク: {banding_count}箇所")

    print("\n【次のステップ（ルール3）】")
    print("1. SP1v21_comparison.png を確認")
    print("2. ハイライト部分の調整が適切か評価")
    print("3. 問題なければルール6でQTRにインストール")

if __name__ == "__main__":
    main()
