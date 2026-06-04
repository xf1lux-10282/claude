#!/usr/bin/env python3
"""
PX1V-PtPd-v22: 紙白1.25D目標版

Input 255を1.25Dに設定してハイライト範囲を確保
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
    """v18の.quadファイルからQuad値を読み込み"""
    with open(quad_path, 'r') as f:
        lines = f.readlines()

    # K curveセクションを探す
    k_curve_start = None
    for i, line in enumerate(lines):
        if '# K curve' in line:
            k_curve_start = i + 1
            break

    if k_curve_start is None:
        raise ValueError("K curve not found")

    # Quad値を抽出
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

def generate_v22_final_1_25():
    """v22カーブを生成 - Input 255を1.25D目標"""
    print("=" * 80)
    print("PX1V-PtPd-v22: Input 255=1.25D目標版")
    print("=" * 80)

    # v18の.quadファイルを読み込み
    v18_quad_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/QTRカーブ情報（V18使用）/backup_v18_FINAL_20260314/PX1V-PtPd-Linear-v18.quad'

    v18_quad_values = read_quad_file(v18_quad_path)
    print(f"\n✓ v18のQuad値を読み込み: {len(v18_quad_values)}ポイント")

    # v18実測値を読み込み
    v18_measured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/QTRカーブ情報（V18使用）/backup_v18_FINAL_20260314/measurement_QTR2-18.csv')

    # v21実測値（比較用）
    v21_measured = pd.read_csv('/Users/daisukekinoshita/Desktop/measurement_QTR2-21.csv')

    print("\n制約条件:")
    print("  ✓ Input 0-216: v18のQuad値をそのまま使用")
    print("  ✓ Input 224, 232, 240, 248, 255: v22目標濃度から計算")
    print("  ✓ 各アンカーポイント間: 線形補間で滑らかに接続")

    # v22の目標濃度（ハイライト域のアンカーポイント）
    v22_targets = {
        224: 1.06,  # v21: 1.11D → -0.05D
        232: 1.10,  # v21: 1.15D → -0.05D
        240: 1.15,  # v21: 1.25D → -0.10D
        248: 1.20,  # v21: 1.32D → -0.12D
        255: 1.25,  # 紙白1.25D目標（v21: 1.34D → -0.09D）
    }

    print("\nv22目標値（ハイライト域）:")
    for inp in [224, 232, 240, 248, 255]:
        v21_val = v21_measured[v21_measured['input'] == inp]['negative_density'].values[0]
        v22_target = v22_targets[inp]
        diff = v22_target - v21_val
        print(f"  Input {inp}: {v22_target:.2f}D (v21: {v21_val:.2f}D, {diff:+.2f}D)")

    print("\nハイライト範囲:")
    highlight_range = v22_targets[255] - v22_targets[240]
    print(f"  240-255: {highlight_range:.2f}D")
    print(f"  v18比較: v18は0.07D、v22は{highlight_range:.2f}D（{highlight_range/0.07:.2f}x）")

    # 予想実測値
    print("\nv22予想実測値 (+0.05Dオフセット想定):")
    for inp in [224, 232, 240, 248, 255]:
        target = v22_targets[inp]
        expected = target + 0.05
        if inp == 255:
            status = "⚠️" if expected > 1.25 else "✓"
            print(f"  {status} Input {inp}: {target:.2f}D → 実測{expected:.2f}D想定（紙白1.25D {'超過' if expected > 1.25 else '以内'}）")
        else:
            print(f"  Input {inp}: {target:.2f}D → 実測{expected:.2f}D想定")

    # v22のQuad値を構築
    v22_quad_values = np.copy(v18_quad_values)

    # アンカーポイント（216 + v22ハイライト）
    anchor_inputs = [216, 224, 232, 240, 248, 255]
    anchor_quads = []

    # Input 216: v18のQuad値
    anchor_quads.append(v18_quad_values[216])

    # Input 224-255: v22目標濃度から計算
    for inp in [224, 232, 240, 248, 255]:
        density = v22_targets[inp]
        baseline = density_to_baseline(density)
        quad = baseline_to_quad(baseline)
        anchor_quads.append(quad)
        v22_quad_values[inp] = quad

    print("\nv22ハイライトアンカーポイント:")
    for i, inp in enumerate(anchor_inputs):
        quad = anchor_quads[i]
        if inp == 216:
            v18_dens = v18_measured[v18_measured['input'] == inp]['negative_density'].values[0]
            print(f"  Input {inp}: Quad={quad} (v18実測: {v18_dens:.2f}D)")
        else:
            print(f"  Input {inp}: Quad={quad} (目標: {v22_targets[inp]:.2f}D)")

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
        status = "⚠️" if avg_diff > 200 else "✓"
        print(f"  {status} Input {start_input}→{end_input}: {num_points}点補間（平均勾配: {avg_diff:.1f}）")

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

        # v18自体の問題箇所を確認
        v18_quad_diffs = np.diff(v18_quad_values)
        v18_problem_count = np.sum(v18_quad_diffs > 200)
        print(f"  参考: v18自体の問題箇所: {v18_problem_count}箇所")

        # ハイライト域の問題箇所
        highlight_problems = [i for i in range(len(quad_diffs)) if quad_diffs[i] > 200 and i >= 216]
        v18_highlight_problems = [i for i in range(len(v18_quad_diffs)) if v18_quad_diffs[i] > 200 and i >= 216]

        print(f"  ハイライト域（216-255）: {len(highlight_problems)}箇所（v18: {len(v18_highlight_problems)}箇所）")

        # v22で新規発生した問題
        new_problems = []
        for i in range(len(quad_diffs)):
            if quad_diffs[i] > 200 and (i >= len(v18_quad_diffs) or v18_quad_diffs[i] <= 200):
                if i >= 216:
                    new_problems.append(i)

        if new_problems:
            print(f"  ⚠️  v22でハイライト域に新規発生: {len(new_problems)}箇所")
        else:
            print(f"  ✓ v22で新規発生: なし（v18由来の問題のみ）")
    else:
        print(f"  ✓ 境界線リスク: なし（全範囲で差分 < 200）")

    # ハイライト域のQuad差分確認
    print("\nハイライト域のQuad差分 (主要ポイント):")
    for i in [216, 223, 224, 231, 232, 239, 240, 247, 248, 254]:
        if i < 255:
            diff = quad_diffs[i]
            status = "✓" if diff < 200 else "⚠️"
            print(f"  {status} Input {i:3d}→{i+1:3d}: {diff:.1f}")

    # 濃度の逆算（確認用）
    baselines = v22_quad_values / 257.0
    densities = baselines * SLOPE + INTERCEPT

    print("\nv22予想濃度（逆算）:")
    for inp in [216, 224, 232, 240, 248, 255]:
        predicted_density = densities[inp]
        if inp in v22_targets:
            target = v22_targets[inp]
            diff = predicted_density - target
            print(f"  Input {inp}: {predicted_density:.4f}D (目標: {target:.2f}D, 差: {diff:+.4f}D)")
        else:
            v18_val = v18_measured[v18_measured['input'] == inp]['negative_density'].values[0]
            print(f"  Input {inp}: {predicted_density:.4f}D (v18: {v18_val:.2f}D)")

    # .quadファイル書き出し
    output_quad = 'PX1V-PtPd-v22.quad'
    with open(output_quad, 'w') as f:
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        f.write('# QuadProfile Version 2.8.0\n')
        f.write('# PX1V-PtPd-v22 - Target 255 at 1.25D (Paper White)\n')
        f.write('# Based on v18 Quad values (Input 0-216 unchanged)\n')
        f.write('# Input 217-255: Linear interpolation between anchor points\n')
        f.write('# Anchors: 224: 1.06, 232: 1.10, 240: 1.15, 248: 1.20, 255: 1.25\n')
        f.write('# Highlight range 240-255: 0.10D\n')
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
    v22_anchor_inputs = [224, 232, 240, 248, 255]
    v22_anchor_densities = [v22_targets[i] for i in v22_anchor_inputs]
    axes[0, 0].scatter(v22_anchor_inputs, v22_anchor_densities,
                       c='red', s=100, zorder=6, marker='o', label='v22 anchors')

    axes[0, 0].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White (1.25D)')
    axes[0, 0].set_xlabel('Input Value', fontsize=12)
    axes[0, 0].set_ylabel('Negative Density', fontsize=12)
    axes[0, 0].set_title('v22: Input 255 = 1.25D Target',
                         fontsize=14, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 2. ハイライト域拡大
    highlight_mask = input_values >= 200
    axes[0, 1].plot(input_values[highlight_mask], densities[highlight_mask],
                    'b-', linewidth=3, label='v22 (predicted)')

    # v18実測値
    v18_highlight_mask = v18_inputs >= 200
    axes[0, 1].scatter(v18_inputs[v18_highlight_mask],
                       v18_densities[v18_highlight_mask],
                       c='green', s=80, zorder=5, marker='s',
                       label='v18 measured', alpha=0.7)

    # v21実測値
    v21_highlight_mask = v21_inputs >= 200
    axes[0, 1].plot(v21_inputs[v21_highlight_mask],
                    v21_densities[v21_highlight_mask],
                    'g--', linewidth=2, marker='s', markersize=6,
                    label='v21 measured', alpha=0.5)

    # v22アンカーポイント
    axes[0, 1].scatter(v22_anchor_inputs, v22_anchor_densities,
                       c='red', s=150, zorder=6, marker='o', label='v22 anchors')

    axes[0, 1].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White')
    axes[0, 1].set_xlabel('Input Value', fontsize=12)
    axes[0, 1].set_ylabel('Negative Density', fontsize=12)
    axes[0, 1].set_title('v22: Highlight Range = 0.10D (240-255)',
                         fontsize=14, fontweight='bold')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_xlim(200, 256)
    axes[0, 1].set_ylim(0.90, 1.40)

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
    highlight_diff_mask = input_values[:-1] >= 200
    axes[1, 1].plot(input_values[:-1][highlight_diff_mask],
                    quad_diffs[highlight_diff_mask],
                    'g-', linewidth=3, marker='o', markersize=4)
    axes[1, 1].axhline(y=200, color='red', linestyle='--', linewidth=2,
                       label='Threshold')
    axes[1, 1].set_xlabel('Input Value', fontsize=12)
    axes[1, 1].set_ylabel('Quad Difference', fontsize=12)
    axes[1, 1].set_title('v22: Highlight Quad Differences (200-255)',
                         fontsize=14, fontweight='bold')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_xlim(200, 256)
    axes[1, 1].set_ylim(-10, 250)

    plt.tight_layout()
    plt.savefig('v22_1.25D_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✓ グラフ保存: v22_1.25D_analysis.png")

    print("\n次のステップ:")
    print(f"  1. sudo cp {output_quad} /Library/Printers/QTR/quadtone/QuadP700/")
    print(f"  2. /Library/Printers/QTR/bin/quadcurves QuadP700")
    print(f"  3. defaults delete com.quadtonerip.QTR-Print-Tool")
    print(f"  4. QTR Print-Toolで v22 を選択してテストプリント")
    print(f"  5. 濃度測定で実測値を確認")

    return v22_quad_values, densities

if __name__ == '__main__':
    quad_values, densities = generate_v22_final_1_25()

    print("\n" + "=" * 80)
    print("v22 カーブ生成完了 - Input 255 = 1.25D目標")
    print("ハイライト範囲（240-255）: 0.10D")
    print("=" * 80)
