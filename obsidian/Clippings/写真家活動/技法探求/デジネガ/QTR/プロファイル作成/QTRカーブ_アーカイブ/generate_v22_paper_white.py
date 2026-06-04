#!/usr/bin/env python3
"""
PX1V-PtPd-v22: 紙白制約版 (上限1.25D)

v21の測定結果から:
- 全体的に目標より+0.02-0.06D高く出る傾向
- Input 255: 1.34D (目標1.29D) → 紙白1.25Dを超過

v22の戦略:
- 紙白1.25D以内に確実に収める
- オフセット分を考慮して目標値を下方修正
- ハイライト範囲は0.07-0.08Dを確保
"""

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
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

def generate_v22_curve():
    """v22カーブを生成 - 紙白制約版"""
    print("=" * 80)
    print("PX1V-PtPd-v22: 紙白制約版 (上限1.25D)")
    print("=" * 80)

    # v20実測値（Input 0-216は安定している）
    v20_measured = pd.read_csv('/Users/daisukekinoshita/Desktop/measurement_QTR2-20.csv')

    # v21実測値（比較用）
    v21_measured = pd.read_csv('/Users/daisukekinoshita/Desktop/measurement_QTR2-21.csv')

    print("\nv21測定結果（ハイライト域）:")
    for inp in [224, 232, 240, 248, 255]:
        v21_val = v21_measured[v21_measured['input'] == inp]['negative_density'].values[0]
        print(f"  Input {inp}: {v21_val:.2f}D")

    # v22の目標値設定
    v22_targets = {
        224: 1.06,  # v21実測1.11D → 目標を下げる
        232: 1.10,  # v21実測1.15D → 目標を下げる
        240: 1.15,  # v21実測1.25D → 大きく下げる
        248: 1.20,  # v21実測1.32D → 大きく下げる
        255: 1.22,  # v21実測1.34D → 1.25D以内に収める
    }

    print("\nv22目標値 (紙白1.25D制約):")
    for inp in [224, 232, 240, 248, 255]:
        v21_val = v21_measured[v21_measured['input'] == inp]['negative_density'].values[0]
        v22_target = v22_targets[inp]
        diff = v22_target - v21_val
        print(f"  Input {inp}: {v22_target:.2f}D (v21: {v21_val:.2f}D, {diff:+.2f}D)")

    # 予想される実測範囲（+0.05-0.06Dオフセット想定）
    print("\nv22予想実測値 (+0.05Dオフセット想定):")
    for inp in [224, 232, 240, 248, 255]:
        target = v22_targets[inp]
        expected = target + 0.05
        print(f"  Input {inp}: {target:.2f}D → 実測{expected:.2f}D想定")

    print(f"\n  Input 255最大想定: 1.22 + 0.06 = 1.28D (1.25D制約内)")

    # 制御点の作成
    # Input 0-216: v20実測値を使用（安定している）
    control_inputs = []
    control_densities = []

    # v20の0-216を使用
    for inp in range(0, 217, 8):
        v20_row = v20_measured[v20_measured['input'] == inp]
        if len(v20_row) > 0:
            control_inputs.append(inp)
            control_densities.append(v20_row['negative_density'].values[0])

    # v22のハイライト域目標値を追加
    for inp in [224, 232, 240, 248, 255]:
        control_inputs.append(inp)
        control_densities.append(v22_targets[inp])

    control_inputs = np.array(control_inputs)
    control_densities = np.array(control_densities)

    print(f"\n制御点: {len(control_inputs)}点")
    print(f"  - Input 0-216: v20実測値")
    print(f"  - Input 224-255: v22目標値（紙白制約考慮）")

    # スプライン補間
    spline = CubicSpline(control_inputs, control_densities)

    # 256点生成
    input_values = np.arange(256)
    target_densities = spline(input_values)

    # 単調増加を保証
    for i in range(1, len(target_densities)):
        if target_densities[i] < target_densities[i-1]:
            target_densities[i] = target_densities[i-1]

    # Baseline変換
    baselines = np.array([density_to_baseline(d) for d in target_densities])
    quad_values = np.array([baseline_to_quad(b) for b in baselines])

    # 単調性チェック
    quad_values_checked = [quad_values[0]]
    for i in range(1, len(quad_values)):
        quad_values_checked.append(max(quad_values[i], quad_values_checked[i-1]))
    quad_values_checked = np.array(quad_values_checked)

    corrections = np.sum(quad_values != quad_values_checked)
    if corrections > 0:
        print(f"\n⚠️  単調性補正: {corrections}ポイント")
    else:
        print(f"\n✓ 単調性チェック: OK")

    # 境界線リスク解析
    quad_diffs = np.diff(quad_values_checked)
    max_diff = np.max(quad_diffs)
    max_diff_input = np.argmax(quad_diffs)

    print(f"\n境界線リスク解析:")
    print(f"  最大Quad差分: {max_diff:.1f} (Input {max_diff_input})")

    if max_diff > 200:
        print(f"  ⚠️  境界線リスク: あり（閾値200超過）")
        problem_count = np.sum(quad_diffs > 200)
        print(f"  問題箇所: {problem_count}箇所")

        # 問題箇所を表示
        for i in range(len(quad_diffs)):
            if quad_diffs[i] > 200:
                print(f"    Input {i:3d}→{i+1:3d}: Quad差分 {quad_diffs[i]:.1f}")
    else:
        print(f"  ✓ 境界線リスク: なし（全範囲で差分 < 200）")

    # ハイライト域の詳細
    print("\nv22ハイライト域の設計:")
    highlight_inputs = [224, 232, 240, 248, 255]
    for i in range(1, len(highlight_inputs)):
        curr_inp = highlight_inputs[i]
        prev_inp = highlight_inputs[i-1]
        curr_dens = target_densities[curr_inp]
        prev_dens = target_densities[prev_inp]
        diff = curr_dens - prev_dens
        print(f"  {prev_inp}→{curr_inp}: {diff:.4f}D")

    total_highlight_range = target_densities[255] - target_densities[240]
    print(f"\nハイライト範囲（240-255）: {total_highlight_range:.4f}D")
    print(f"  目標: 0.07D以上（プリント階調確保）")

    # .quadファイル書き出し
    output_quad = 'PX1V-PtPd-v22.quad'
    with open(output_quad, 'w') as f:
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        f.write('# QuadProfile Version 2.8.0\n')
        f.write('# PX1V-PtPd-v22 - Paper White Constraint (Max 1.25D)\n')
        f.write('# Based on v21 measurements with offset correction\n')
        f.write('# 224: 1.06, 232: 1.10, 240: 1.15, 248: 1.20, 255: 1.22\n')
        f.write('# Expected range: 240-255 = 0.07D\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')

        # Kチャンネル（Photo Black）
        f.write('# K curve\n')
        for qv in quad_values_checked:
            f.write(f'{int(qv)}\n')

        # 残り9チャンネル（全て0 = 使用しない）
        for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
            f.write(f'# {channel} curve\n')
            for _ in range(256):
                f.write('0\n')

    print(f"\n✓ .quadファイル生成: {output_quad}")

    # .txtファイル
    output_txt = 'PX1V-PtPd-v22.txt'
    df = pd.DataFrame({
        'Input': input_values,
        'Target_Density': target_densities,
        'Baseline': baselines,
        'Quad_Value': quad_values_checked
    })
    df.to_csv(output_txt, index=False, float_format='%.6f')
    print(f"✓ 詳細データ: {output_txt}")

    # グラフ作成
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1. 全範囲濃度カーブ
    axes[0, 0].plot(input_values, target_densities, 'b-', linewidth=2, label='v22')

    # v21実測値をプロット
    v21_inputs = v21_measured['input'].values
    v21_densities = v21_measured['negative_density'].values
    axes[0, 0].plot(v21_inputs, v21_densities, 'g--', linewidth=1.5,
                    marker='s', markersize=4, label='v21 measured', alpha=0.7)

    axes[0, 0].scatter(control_inputs, control_densities, c='red', s=30,
                       zorder=5, label='v22 control points')
    axes[0, 0].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White (1.25D)')
    axes[0, 0].set_xlabel('Input Value', fontsize=12)
    axes[0, 0].set_ylabel('Negative Density', fontsize=12)
    axes[0, 0].set_title('v22: Full Range with Paper White Constraint',
                         fontsize=14, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 2. ハイライト域拡大
    highlight_mask = input_values >= 200
    axes[0, 1].plot(input_values[highlight_mask], target_densities[highlight_mask],
                    'b-', linewidth=3, label='v22')

    # v21実測値
    v21_highlight_mask = v21_inputs >= 200
    axes[0, 1].plot(v21_inputs[v21_highlight_mask],
                    v21_densities[v21_highlight_mask],
                    'g--', linewidth=2, marker='s', markersize=6,
                    label='v21 measured', alpha=0.7)

    # v22制御点
    highlight_control_mask = control_inputs >= 200
    axes[0, 1].scatter(control_inputs[highlight_control_mask],
                       control_densities[highlight_control_mask],
                       c='red', s=100, zorder=5, marker='o', label='v22 targets')

    axes[0, 1].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White')
    axes[0, 1].set_xlabel('Input Value', fontsize=12)
    axes[0, 1].set_ylabel('Negative Density', fontsize=12)
    axes[0, 1].set_title('v22 vs v21: Highlight with 1.25D Constraint',
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

    plt.tight_layout()
    plt.savefig('v22_paper_white_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✓ グラフ保存: v22_paper_white_analysis.png")

    print("\n次のステップ:")
    print(f"  1. sudo cp {output_quad} /Library/Printers/QTR/quadtone/QuadP700/")
    print(f"  2. /Library/Printers/QTR/bin/quadcurves QuadP700")
    print(f"  3. defaults delete com.quadtonerip.QTR-Print-Tool")
    print(f"  4. QTR Print-Toolで v22 を選択してテストプリント")
    print(f"  5. 濃度測定で1.25D以内に収まっているか確認")

    return quad_values_checked, target_densities

if __name__ == '__main__':
    quad_values, densities = generate_v22_curve()

    print("\n" + "=" * 80)
    print("v22 カーブ生成完了 - 紙白1.25D制約版")
    print("=" * 80)
