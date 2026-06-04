#!/usr/bin/env python3
"""
SP1v20カーブ生成スクリプト

設計方針:
- Input 0-223: V18のまま（コントラスト削減-0.05D維持）
- Input 224-239: V19と同じ（既に良好）
- Input 240-255: V19から-0.04D下げる（実測値補正）

ターゲット濃度:
- 224 → 0.9916D (V18[224])
- 232 → 1.05D
- 240 → 1.08D (V19: 1.12D → 1.08D)
- 248 → 1.15D (V19: 1.19D → 1.15D)
- 255 → 1.21D (V19: 1.25D → 1.21D)

根拠: SP1v19実測でInput 240/248/255が設計値より+0.04〜0.05D高かった
期待: SP1v20実測で設計値に近づく（±0.02D以内）

作成日: 2026-03-19
作成者: Claude Code
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Arial Unicode MS'

def load_v18_curve():
    """V18カーブを読み込む"""
    v18_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-SP1v18.quad"

    with open(v18_path, 'r') as f:
        lines = f.readlines()

    # Kチャンネルのデータを抽出
    k_data = []
    in_k_channel = False

    for line in lines:
        if line.strip() == "# K curve":
            in_k_channel = True
            continue
        elif line.strip().startswith("# C curve"):
            break

        if in_k_channel and not line.startswith('#'):
            # 各行に1つの数値のみ
            try:
                quad = int(line.strip())
                k_data.append(quad)
            except ValueError:
                continue

    return np.array(k_data, dtype=int)

def quad_to_density(quad):
    """Quad値を濃度に変換"""
    return quad * 1.73 / 55891

def density_to_quad(density):
    """濃度をQuad値に変換"""
    return int(round(density * 55891 / 1.73))

def generate_sp1v20():
    """SP1v20カーブを生成"""

    print("=" * 80)
    print("SP1v20カーブ生成")
    print("=" * 80)

    # V18を読み込み
    print("\n[Step 1] V18カーブを読み込み中...")
    v18_quads = load_v18_curve()
    print(f"✓ V18カーブ読み込み完了: {len(v18_quads)}点")

    # V20 = V18をベースにコピー
    v20_quads = v18_quads.copy().astype(int)

    # Input 224-255: ハイライト諧調拡張（V19から-0.04D調整）
    print("\n[Step 2] ハイライト諧調拡張（Input 224-255）")
    print("V19実測で+0.04〜0.05D高かったため、設計値を-0.04D下げる")

    # アンカーポイント定義
    anchor_inputs = [224, 232, 240, 248, 255]
    anchor_densities = [
        quad_to_density(v18_quads[224]),  # 224 → V18[224] (0.9916D)
        1.05,   # 232 → 1.05D (V19と同じ)
        1.08,   # 240 → 1.08D (V19: 1.12D → -0.04D)
        1.15,   # 248 → 1.15D (V19: 1.19D → -0.04D)
        1.21    # 255 → 1.21D (V19: 1.25D → -0.04D)
    ]

    print("\n【アンカーポイント】")
    print(f"{'Input':<8} {'V19設計':<10} {'V19実測':<10} {'V20ターゲット':<15} {'期待実測':<10}")
    print("-" * 65)

    v19_design = [0.9916, 1.05, 1.12, 1.19, 1.25]
    v19_measured = [1.05, 1.08, 1.17, 1.24, 1.29]

    for i, inp in enumerate(anchor_inputs):
        expected = anchor_densities[i] + (v19_measured[i] - v19_design[i])
        print(f"{inp:<8} {v19_design[i]:<10.4f} {v19_measured[i]:<10.2f} {anchor_densities[i]:<15.4f} {expected:<10.2f}")

    # アンカーポイント間を線形補間
    print("\n[Step 3] Input 224-255を線形補間中...")

    for i in range(len(anchor_inputs) - 1):
        start_input = anchor_inputs[i]
        end_input = anchor_inputs[i + 1]
        start_density = anchor_densities[i]
        end_density = anchor_densities[i + 1]

        for inp in range(start_input, end_input + 1):
            # 線形補間
            t = (inp - start_input) / (end_input - start_input)
            target_density = start_density + t * (end_density - start_density)
            v20_quads[inp] = density_to_quad(target_density)

    print(f"✓ Input 224-255の補間完了")

    # 単調増加の確認
    print("\n[Step 4] 単調増加の確認...")
    violations = []
    for i in range(1, 256):
        if v20_quads[i] <= v20_quads[i-1]:
            violations.append((i, v20_quads[i] - v20_quads[i-1]))

    if violations:
        print(f"⚠️ 単調増加違反: {len(violations)}箇所")
        for inp, delta in violations[:10]:
            print(f"   Input {inp-1}→{inp}: Δ={delta} Quad")

        # 修正
        print("\n単調増加違反を修正中...")
        for inp, _ in violations:
            v20_quads[inp] = v20_quads[inp-1] + 1
        print("✓ 修正完了")
    else:
        print("✓ 単調増加違反なし")

    # Input 220-255の詳細表示
    print("\n[Step 5] Input 220-255の詳細")
    print(f"{'Input':<8} {'V18 Quad':<10} {'V20 Quad':<10} {'Δ Quad':<10} {'V20 Density':<12}")
    print("-" * 60)

    for inp in range(220, 256):
        v18_quad = v18_quads[inp]
        v20_quad = v20_quads[inp]
        delta = v20_quad - v18_quad
        v20_density = quad_to_density(v20_quad)

        marker = "←" if inp in anchor_inputs else ""
        print(f"{inp:<8} {v18_quad:<10} {v20_quad:<10} {delta:+<10} {v20_density:<12.4f} {marker}")

    return v18_quads, v20_quads

def check_banding_risk(v18_quads, v20_quads):
    """バンディングリスクを分析"""

    print("\n" + "=" * 80)
    print("バンディングリスク解析")
    print("=" * 80)

    def analyze_risks(quads, name):
        risks = []
        for i in range(1, 256):
            delta = quads[i] - quads[i-1]
            if delta < 50:  # 50 Quad未満はリスク
                risks.append((i, delta))
        return risks

    v18_risks = analyze_risks(v18_quads, "V18")
    v20_risks = analyze_risks(v20_quads, "V20")

    print(f"\nV18リスク箇所: {len(v18_risks)}箇所")
    print(f"V20リスク箇所: {len(v20_risks)}箇所")

    # V20で新たに追加されたリスク箇所
    v18_risk_inputs = set([r[0] for r in v18_risks])
    v20_risk_inputs = set([r[0] for r in v20_risks])
    new_risks = v20_risk_inputs - v18_risk_inputs

    if new_risks:
        print(f"\n⚠️ V20で新たに追加されたリスク箇所: {len(new_risks)}箇所")
        for inp in sorted(new_risks)[:10]:
            for r in v20_risks:
                if r[0] == inp:
                    print(f"   Input {r[0]-1}→{r[0]}: Δ={r[1]} Quad")
                    break
    else:
        print(f"✓ 新たなリスク箇所なし")

def plot_comparison(v18_quads, v20_quads):
    """比較グラフを生成"""

    inputs = np.arange(256)
    v18_density = np.array([quad_to_density(q) for q in v18_quads])
    v20_density = np.array([quad_to_density(q) for q in v20_quads])

    fig, axes = plt.subplots(3, 1, figsize=(14, 12))

    # グラフ1: Quad値比較
    ax1 = axes[0]
    ax1.plot(inputs, v18_quads, 'g-', label='V18 (Baseline)', linewidth=2, alpha=0.7)
    ax1.plot(inputs, v20_quads, 'r-', label='V20 (Highlight -0.04D)', linewidth=2)
    ax1.axvline(x=224, color='orange', linestyle='--', alpha=0.5, label='Highlight Adjustment Start')
    ax1.axvspan(240, 255, color='red', alpha=0.1, label='Adjusted Zone (-0.04D)')
    ax1.set_xlabel('Input Value', fontsize=12)
    ax1.set_ylabel('Quad Value', fontsize=12)
    ax1.set_title('SP1v20 Quad Comparison (V18 → V20)', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # グラフ2: 濃度比較（全体）
    ax2 = axes[1]
    ax2.plot(inputs, v18_density, 'g-', label='V18', linewidth=2, alpha=0.7)
    ax2.plot(inputs, v20_density, 'r-', label='V20', linewidth=2)
    ax2.axvline(x=224, color='orange', linestyle='--', alpha=0.5)
    ax2.axvspan(240, 255, color='red', alpha=0.1)
    ax2.set_xlabel('Input Value', fontsize=12)
    ax2.set_ylabel('Negative Density (D)', fontsize=12)
    ax2.set_title('Density Comparison - Full Range', fontsize=14)
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)

    # グラフ3: ハイライト詳細（Input 200-255）
    ax3 = axes[2]
    highlight_range = inputs >= 200
    ax3.plot(inputs[highlight_range], v18_density[highlight_range], 'g-o', label='V18', linewidth=2, markersize=4, alpha=0.7)
    ax3.plot(inputs[highlight_range], v20_density[highlight_range], 'r-^', label='V20', linewidth=2, markersize=4)

    # V19設計値と期待値を表示
    v19_targets = [240, 248, 255]
    v19_design_d = [1.12, 1.19, 1.25]
    v20_target_d = [1.08, 1.15, 1.21]

    ax3.scatter(v19_targets, v19_design_d, color='blue', s=100, marker='x', label='V19 Design', zorder=5)
    ax3.scatter(v19_targets, v20_target_d, color='red', s=100, marker='*', label='V20 Target', zorder=5)

    ax3.axvline(x=240, color='orange', linestyle='--', alpha=0.5)
    ax3.set_xlabel('Input Value', fontsize=12)
    ax3.set_ylabel('Negative Density (D)', fontsize=12)
    ax3.set_title('Highlight Detail (Input 200-255) - V20 Adjustment', fontsize=14)
    ax3.set_xlim(200, 255)
    ax3.legend(loc='upper left')
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/SP1v20_preview.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ グラフ保存: SP1v20_preview.png")

    plt.close()

def save_quad_file(v20_quads):
    """V20カーブを.quadファイルとして保存"""

    # V7をテンプレートとして読み込み
    v7_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-SP1v7.quad"

    with open(v7_path, 'r') as f:
        v7_lines = f.readlines()

    # 新しいファイルの内容を構築
    output_lines = []

    # ヘッダー（1-14行目）をV20用に変更
    output_lines.append("## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n")
    output_lines.append("# QuadProfile Version 2.8.0\n")
    output_lines.append("# PX1V-PtPd-SP1v20 - Highlight adjustment (-0.04D for Input 240-255)\n")
    output_lines.append("# Input 0-223: V18 baseline (contrast reduction -0.05D)\n")
    output_lines.append("# Input 224-239: V19 baseline (highlight extension)\n")
    output_lines.append("# Input 240-255: V19 - 0.04D (correction based on V19 measurement)\n")
    output_lines.append("#   240 → 1.08D (V19: 1.12D, measured: 1.17D)\n")
    output_lines.append("#   248 → 1.15D (V19: 1.19D, measured: 1.24D)\n")
    output_lines.append("#   255 → 1.21D (V19: 1.25D, measured: 1.29D)\n")
    output_lines.append("# Expected: Measured density will be closer to original design targets\n")
    output_lines.append("# Generated: 2026-03-19 by Claude Code\n")
    output_lines.append("#\n")
    output_lines.append("# ink limits: K=100% C=100% M=100% Y=100% LC=100% LM=100% LK=100% LLK=100% V=100% MK=100%\n")
    output_lines.append("#\n")

    # Kチャンネル
    output_lines.append("# K curve\n")
    for quad in v20_quads:
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
    output_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-SP1v20.quad"

    with open(output_path, 'w') as f:
        f.writelines(output_lines)

    print(f"\n✓ ファイル保存: PX1V-PtPd-SP1v20.quad")

    # ファイル検証
    with open(output_path, 'r') as f:
        line_count = len(f.readlines())

    print(f"✓ ファイル行数: {line_count}行")

    if line_count < 2500:
        print("⚠️ 警告: ファイル行数が少ない可能性があります")

    return output_path

def main():
    # カーブ生成
    v18_quads, v20_quads = generate_sp1v20()

    # バンディングリスク解析
    check_banding_risk(v18_quads, v20_quads)

    # グラフ生成
    print("\n" + "=" * 80)
    print("比較グラフ生成")
    print("=" * 80)
    plot_comparison(v18_quads, v20_quads)

    # .quadファイル保存
    print("\n" + "=" * 80)
    print(".quadファイル保存")
    print("=" * 80)
    output_path = save_quad_file(v20_quads)

    # サマリー
    print("\n" + "=" * 80)
    print("SP1v20生成完了")
    print("=" * 80)

    print("\n【生成ファイル】")
    print("- PX1V-PtPd-SP1v20.quad")
    print("- SP1v20_preview.png")

    print("\n【設計サマリー】")
    print("- Input 0-223: V18と同じ（コントラスト削減-0.05D維持）")
    print("- Input 224-239: V19と同じ（良好な範囲）")
    print("- Input 240-255: V19から-0.04D下げる（実測補正）")

    print("\n【期待される効果】")
    print("- Input 240-255の実測値が設計値に近づく（±0.02D以内）")
    print("- ハイライト諧調は依然として拡張されている（V18より細かい）")
    print("- コントラスト削減効果を維持（Input 121-220）")

    print("\n【次のステップ】")
    print("1. SP1v20_preview.pngでグラフを確認")
    print("2. QTRにインストール")
    print("3. ネガ濃度を測定")
    print("4. Input 240/248/255が目標濃度（1.12D/1.19D/1.25D付近）になっているか確認")

if __name__ == "__main__":
    main()
