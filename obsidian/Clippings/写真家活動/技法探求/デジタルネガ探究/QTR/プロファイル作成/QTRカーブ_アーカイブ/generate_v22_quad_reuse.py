#!/usr/bin/env python3
"""
PX1V-PtPd-v22: 実測Quad値再利用版

戦略:
- Input 232: v18のInput 240のQuad値（実測1.16D）
- Input 255: v21のInput 240のQuad値（実測1.25D）
- 実証済みのQuad値を使用して確実な結果を得る
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ========== 基本定数 ==========
SLOPE = 0.007387
INTERCEPT = 0.0935

def density_to_baseline(density):
    """濃度からベースライン値を計算"""
    baseline = (density - INTERCEPT) / SLOPE
    return max(0.0, min(255.0, baseline))

def baseline_to_quad(baseline):
    """ベースライン値をQuad値に変換"""
    quad = baseline * 257
    return int(round(min(65535, max(0, quad))))

def read_quad_file(quad_path):
    """quadファイルからQuad値を読み込み"""
    with open(quad_path, 'r') as f:
        lines = f.readlines()

    k_curve_start = None
    for i, line in enumerate(lines):
        if '# K curve' in line:
            k_curve_start = i + 1
            break

    if k_curve_start is None:
        raise ValueError("K curve not found")

    quad_values = []
    for line in lines[k_curve_start:]:
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        if not line.isdigit():
            break
        quad_values.append(int(line))
        if len(quad_values) >= 256:
            break

    return np.array(quad_values[:256])

def generate_v22_quad_reuse():
    """v22カーブを生成 - 実測Quad値再利用版"""
    print("=" * 80)
    print("PX1V-PtPd-v22: 実測Quad値再利用版")
    print("=" * 80)

    # v18の.quadファイルを読み込み
    v18_quad_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/QTRカーブ情報（V18使用）/backup_v18_FINAL_20260314/PX1V-PtPd-Linear-v18.quad'
    v18_quad_values = read_quad_file(v18_quad_path)
    print(f"\n✓ v18のQuad値を読み込み: {len(v18_quad_values)}ポイント")

    # v21の.quadファイルを読み込み
    v21_quad_path = '/Users/daisukekinoshita/Desktop/PX1V-PtPd-v21.quad'
    v21_quad_values = read_quad_file(v21_quad_path)
    print(f"✓ v21のQuad値を読み込み: {len(v21_quad_values)}ポイント")

    # v18実測値を読み込み
    v18_measured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/QTRカーブ情報（V18使用）/backup_v18_FINAL_20260314/measurement_QTR2-18.csv')

    # v21実測値を読み込み
    v21_measured = pd.read_csv('/Users/daisukekinoshita/Desktop/measurement_QTR2-21.csv')

    print("\n戦略:")
    print("  ✓ Input 0-184: v18のQuad値をそのまま使用")
    print("  ✓ Input 232: v18のInput 240のQuad値を使用（実測1.16D）")
    print("  ✓ Input 255: v21のInput 240のQuad値を使用（実測1.25D）")
    print("  ✓ Input 192-224: 濃度目標から計算")
    print("  ✓ 各区間: 線形補間で滑らかに接続")

    # Quad値を直接使用する箇所
    v18_240_quad = v18_quad_values[240]
    v21_240_quad = v21_quad_values[240]

    v18_240_measured = v18_measured[v18_measured['input'] == 240]['negative_density'].values[0]
    v21_240_measured = v21_measured[v21_measured['input'] == 240]['negative_density'].values[0]

    print("\n実測Quad値の活用:")
    print(f"  v18 Input 240: Quad={v18_240_quad} → 実測{v18_240_measured:.2f}D")
    print(f"  → v22 Input 232に割り当て")
    print(f"  v21 Input 240: Quad={v21_240_quad} → 実測{v21_240_measured:.2f}D")
    print(f"  → v22 Input 255に割り当て")

    # v22の目標濃度（Input 192-224）
    v22_targets = {
        192: 0.94,  # v18/v21と同じ
        200: 0.99,  # v18: 0.97 → +0.02D
        208: 1.04,  # v18: 1.01 → +0.03D
        216: 1.07,  # v18: 1.02 → +0.05D
        224: 1.11,  # v21と同じ
    }

    print("\nv22目標値（Input 192-224）:")
    for inp in [192, 200, 208, 216, 224]:
        v22_target = v22_targets[inp]
        v18_val = v18_measured[v18_measured['input'] == inp]['negative_density'].values[0]
        v21_val = v21_measured[v21_measured['input'] == inp]['negative_density'].values[0]
        print(f"  Input {inp}: {v22_target:.2f}D (v18: {v18_val:.2f}D, v21: {v21_val:.2f}D)")

    # v22のQuad値を構築
    v22_quad_values = np.copy(v18_quad_values)

    # アンカーポイント
    anchor_inputs = [184, 192, 200, 208, 216, 224, 232, 255]
    anchor_quads = []

    # Input 184: v18のQuad値
    anchor_quads.append(v18_quad_values[184])

    # Input 192-224: v22目標濃度から計算
    for inp in [192, 200, 208, 216, 224]:
        density = v22_targets[inp]
        baseline = density_to_baseline(density)
        quad = baseline_to_quad(baseline)
        anchor_quads.append(quad)
        v22_quad_values[inp] = quad

    # Input 232: v18のInput 240のQuad値
    anchor_quads.append(v18_240_quad)
    v22_quad_values[232] = v18_240_quad

    # Input 255: v21のInput 240のQuad値
    anchor_quads.append(v21_240_quad)
    v22_quad_values[255] = v21_240_quad

    print(f"\nアンカーポイント: {len(anchor_inputs)}点")
    for i, inp in enumerate(anchor_inputs):
        quad = anchor_quads[i]
        if inp == 184:
            v18_dens = v18_measured[v18_measured['input'] == inp]['negative_density'].values[0]
            print(f"  Input {inp}: Quad={quad} (v18: {v18_dens:.2f}D)")
        elif inp in v22_targets:
            print(f"  Input {inp}: Quad={quad} (目標: {v22_targets[inp]:.2f}D)")
        elif inp == 232:
            print(f"  Input {inp}: Quad={quad} (v18 Input240実測: {v18_240_measured:.2f}D)")
        elif inp == 255:
            print(f"  Input {inp}: Quad={quad} (v21 Input240実測: {v21_240_measured:.2f}D)")

    # 各アンカーポイント間を線形補間
    print("\n線形補間:")
    for i in range(len(anchor_inputs) - 1):
        start_input = anchor_inputs[i]
        end_input = anchor_inputs[i + 1]
        start_quad = anchor_quads[i]
        end_quad = anchor_quads[i + 1]

        # 間のポイントを補間
        for inp in range(start_input + 1, end_input):
            ratio = (inp - start_input) / (end_input - start_input)
            interpolated_quad = int(round(start_quad + ratio * (end_quad - start_quad)))
            v22_quad_values[inp] = interpolated_quad

        num_points = end_input - start_input - 1
        avg_diff = (end_quad - start_quad) / (end_input - start_input)
        status = "✓" if avg_diff < 200 else "⚠️"
        print(f"  {status} Input {start_input}→{end_input}: {num_points}点補間（平均Quad勾配: {avg_diff:.1f}）")

    # 単調性チェック
    corrections = 0
    for i in range(1, len(v22_quad_values)):
        if v22_quad_values[i] < v22_quad_values[i-1]:
            v22_quad_values[i] = v22_quad_values[i-1]
            corrections += 1

    if corrections > 0:
        print(f"\n⚠️  単調性補正: {corrections}ポイント")
    else:
        print(f"\n✓ 単調性チェック: OK")

    # 境界線リスク解析
    quad_diffs = np.diff(v22_quad_values)
    max_diff = np.max(quad_diffs)
    max_diff_input = np.argmax(quad_diffs)

    print(f"\n境界線リスク解析:")
    print(f"  最大Quad差分: {max_diff:.1f} (Input {max_diff_input})")

    if max_diff > 200:
        print(f"  ⚠️  境界線リスク: あり（閾値200超過）")
        problem_count = np.sum(quad_diffs > 200)
        print(f"  問題箇所: {problem_count}箇所")

        # v18との比較
        v18_quad_diffs = np.diff(v18_quad_values)
        v18_problem_count = np.sum(v18_quad_diffs > 200)
        print(f"  参考: v18自体の問題箇所: {v18_problem_count}箇所")

        # ハイライト域（232-255）の問題
        highlight_problems = [i for i in range(len(quad_diffs)) if quad_diffs[i] > 200 and i >= 232]
        v18_highlight_problems = [i for i in range(len(v18_quad_diffs)) if v18_quad_diffs[i] > 200 and i >= 232]

        print(f"  ハイライト域（232-255）: {len(highlight_problems)}箇所（v18: {len(v18_highlight_problems)}箇所）")

        if len(highlight_problems) == 0:
            print(f"  ✓ ハイライト域で新規発生: なし")
    else:
        print(f"  ✓ 境界線リスク: なし（全範囲で差分 < 200）")

    # ハイライト域のQuad差分詳細
    print("\nハイライト域のQuad差分（Input 224-255）:")
    for i in range(224, 255):
        diff = quad_diffs[i]
        status = "✓" if diff < 200 else "⚠️"
        if i in [224, 231, 232, 239, 247, 254]:
            print(f"  {status} Input {i:3d}→{i+1:3d}: {diff:.1f}")

    # 濃度の逆算（確認用）
    baselines = v22_quad_values / 257.0
    densities = baselines * SLOPE + INTERCEPT

    print("\nv22予想濃度（逆算）:")
    key_inputs = [184, 192, 200, 208, 216, 224, 232, 240, 248, 255]
    for inp in key_inputs:
        predicted_density = densities[inp]
        if inp in v22_targets:
            target = v22_targets[inp]
            print(f"  Input {inp}: {predicted_density:.4f}D (目標: {target:.2f}D)")
        elif inp == 232:
            print(f"  Input {inp}: {predicted_density:.4f}D (v18実測: {v18_240_measured:.2f}D想定)")
        elif inp == 255:
            print(f"  Input {inp}: {predicted_density:.4f}D (v21実測: {v21_240_measured:.2f}D想定)")
        else:
            print(f"  Input {inp}: {predicted_density:.4f}D")

    # ハイライト範囲
    highlight_range_232_255 = densities[255] - densities[232]
    highlight_range_240_255 = densities[255] - densities[240]
    print(f"\nハイライト範囲:")
    print(f"  232-255: {highlight_range_232_255:.4f}D")
    print(f"  240-255: {highlight_range_240_255:.4f}D")

    # .quadファイル書き出し
    output_quad = 'PX1V-PtPd-v22.quad'
    with open(output_quad, 'w') as f:
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        f.write('# QuadProfile Version 2.8.0\n')
        f.write('# PX1V-PtPd-v22 - Reusing Proven Quad Values\n')
        f.write('# Based on v18 Quad values (Input 0-184 unchanged)\n')
        f.write('# Input 232: v18 Input 240 Quad (measured 1.16D)\n')
        f.write('# Input 255: v21 Input 240 Quad (measured 1.25D)\n')
        f.write('# Linear interpolation between anchor points\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')

        # Kチャンネル（Photo Black）
        f.write('# K curve\n')
        for qv in v22_quad_values:
            f.write(f'{int(qv)}\n')

        # 残り9チャンネル（全て0 = 使用しない）
        for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
            f.write(f'# {channel} curve\n')
            for _ in range(256):
                f.write('0\n')

    print(f"\n✓ .quadファイル生成: {output_quad}")

    # .txtファイル
    output_txt = 'PX1V-PtPd-v22.txt'
    input_values = np.arange(256)
    df = pd.DataFrame({
        'Input': input_values,
        'Quad_Value': v22_quad_values,
        'Baseline': baselines,
        'Predicted_Density': densities
    })
    df.to_csv(output_txt, index=False, float_format='%.6f')
    print(f"✓ 詳細データ: {output_txt}")

    # グラフ作成
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1. 全範囲濃度カーブ
    axes[0, 0].plot(input_values, densities, 'b-', linewidth=2, label='v22 (predicted)')

    # v18実測値
    v18_inputs = v18_measured['input'].values
    v18_densities = v18_measured['negative_density'].values
    axes[0, 0].scatter(v18_inputs, v18_densities, c='green', s=30,
                       zorder=5, label='v18 measured', alpha=0.7)

    # v21実測値
    v21_inputs = v21_measured['input'].values
    v21_densities = v21_measured['negative_density'].values
    axes[0, 0].plot(v21_inputs, v21_densities, 'g--', linewidth=1.5,
                    marker='s', markersize=4, label='v21 measured', alpha=0.5)

    # v22アンカーポイント
    v22_anchor_inputs = [192, 200, 208, 216, 224, 232, 255]
    v22_anchor_densities = [densities[i] for i in v22_anchor_inputs]
    axes[0, 0].scatter(v22_anchor_inputs, v22_anchor_densities,
                       c='red', s=100, zorder=6, marker='o', label='v22 anchors')

    axes[0, 0].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White (1.25D)')
    axes[0, 0].set_xlabel('Input Value', fontsize=12)
    axes[0, 0].set_ylabel('Negative Density', fontsize=12)
    axes[0, 0].set_title('v22: Reusing Proven Quad Values (v18 & v21)',
                         fontsize=14, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 2. ハイライト域拡大
    highlight_mask = input_values >= 176
    axes[0, 1].plot(input_values[highlight_mask], densities[highlight_mask],
                    'b-', linewidth=3, label='v22 (predicted)')

    # v18実測値
    v18_highlight_mask = v18_inputs >= 176
    axes[0, 1].scatter(v18_inputs[v18_highlight_mask],
                       v18_densities[v18_highlight_mask],
                       c='green', s=80, zorder=5, marker='s',
                       label='v18 measured', alpha=0.7)

    # v21実測値
    v21_highlight_mask = v21_inputs >= 176
    axes[0, 1].plot(v21_inputs[v21_highlight_mask],
                    v21_densities[v21_highlight_mask],
                    'g--', linewidth=2, marker='s', markersize=6,
                    label='v21 measured', alpha=0.5)

    # v22特別ポイント
    axes[0, 1].scatter([232, 255], [densities[232], densities[255]],
                       c='red', s=200, zorder=6, marker='*',
                       label='v22 reused quads', edgecolors='black', linewidths=2)

    axes[0, 1].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White')
    axes[0, 1].set_xlabel('Input Value', fontsize=12)
    axes[0, 1].set_ylabel('Negative Density', fontsize=12)
    axes[0, 1].set_title('v22: Input 232=v18(240), Input 255=v21(240)',
                         fontsize=14, fontweight='bold')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_xlim(176, 256)
    axes[0, 1].set_ylim(0.80, 1.40)

    # 3. 全範囲Quad差分
    axes[1, 0].plot(input_values[:-1], quad_diffs, 'g-', linewidth=1.5)
    axes[1, 0].axhline(y=200, color='red', linestyle='--', linewidth=2,
                       label='Boundary Risk (200)')
    axes[1, 0].set_xlabel('Input Value', fontsize=12)
    axes[1, 0].set_ylabel('Quad Difference', fontsize=12)
    axes[1, 0].set_title('v22: Boundary Line Risk Analysis',
                         fontsize=14, fontweight='bold')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_ylim(-10, min(max_diff + 20, 250))

    # 4. ハイライトQuad差分
    highlight_diff_mask = input_values[:-1] >= 176
    axes[1, 1].plot(input_values[:-1][highlight_diff_mask],
                    quad_diffs[highlight_diff_mask],
                    'g-', linewidth=3, marker='o', markersize=4)
    axes[1, 1].axhline(y=200, color='red', linestyle='--', linewidth=2,
                       label='Threshold')
    axes[1, 1].set_xlabel('Input Value', fontsize=12)
    axes[1, 1].set_ylabel('Quad Difference', fontsize=12)
    axes[1, 1].set_title('v22: Highlight Quad Differences (176-255)',
                         fontsize=14, fontweight='bold')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_xlim(176, 256)
    axes[1, 1].set_ylim(-10, 200)

    plt.tight_layout()
    plt.savefig('v22_quad_reuse_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✓ グラフ保存: v22_quad_reuse_analysis.png")

    print("\n次のステップ:")
    print(f"  1. cp {output_quad} /tmp/ && osascript -e 'do shell script \"cp /tmp/{output_quad} /Library/Printers/QTR/quadtone/QuadP700/\" with administrator privileges'")
    print(f"  2. /Library/Printers/QTR/bin/quadcurves QuadP700")
    print(f"  3. defaults delete com.quadtonerip.QTR-Print-Tool")
    print(f"  4. QTR Print-Toolで v22 を選択してテストプリント")
    print(f"  5. 濃度測定で実測値を確認")

    return v22_quad_values, densities

if __name__ == '__main__':
    quad_values, densities = generate_v22_quad_reuse()

    print("\n" + "=" * 80)
    print("v22 カーブ生成完了 - 実測Quad値再利用版")
    print("Input 232: v18のInput 240（実測1.16D）")
    print("Input 255: v21のInput 240（実測1.25D）")
    print("=" * 80)
