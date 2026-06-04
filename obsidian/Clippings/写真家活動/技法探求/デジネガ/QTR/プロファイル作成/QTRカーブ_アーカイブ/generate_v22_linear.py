#!/usr/bin/env python3
"""
PX1V-PtPd-v22: 紙白制約版 (上限1.25D) - 線形補間

v22_paper_white.pyでスプライン補間により境界線リスクが発生したため、
v18の成功例に従って線形補間を使用
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

def generate_v22_linear():
    """v22カーブを生成 - 線形補間版"""
    print("=" * 80)
    print("PX1V-PtPd-v22: 紙白制約版 (上限1.25D) - 線形補間")
    print("=" * 80)

    # v20実測値を読み込み
    v20_measured = pd.read_csv('/Users/daisukekinoshita/Desktop/measurement_QTR2-20.csv')

    # v21実測値（比較用）
    v21_measured = pd.read_csv('/Users/daisukekinoshita/Desktop/measurement_QTR2-21.csv')

    print("\nv21測定結果（ハイライト域）:")
    for inp in [224, 232, 240, 248, 255]:
        v21_val = v21_measured[v21_measured['input'] == inp]['negative_density'].values[0]
        print(f"  Input {inp}: {v21_val:.2f}D")

    # v22の目標値設定（紙白1.25D制約）
    # v21の+0.05-0.06Dオフセットを考慮
    v22_targets = {
        0: 0.07,
        8: 0.08,
        16: 0.13,
        24: 0.16,
        32: 0.18,
        40: 0.20,
        48: 0.24,
        56: 0.27,
        64: 0.31,
        72: 0.33,
        80: 0.37,
        88: 0.39,
        96: 0.43,
        104: 0.48,
        112: 0.53,
        120: 0.58,
        128: 0.63,
        136: 0.67,
        144: 0.71,
        152: 0.75,
        160: 0.79,
        168: 0.83,
        176: 0.87,
        184: 0.90,
        192: 0.94,
        200: 0.96,
        208: 1.01,
        216: 1.02,
        224: 1.06,  # v21: 1.11D → -0.05D
        232: 1.10,  # v21: 1.15D → -0.05D
        240: 1.15,  # v21: 1.25D → -0.10D
        248: 1.20,  # v21: 1.32D → -0.12D
        255: 1.22,  # v21: 1.34D → -0.12D（1.25D制約）
    }

    print("\nv22目標値 (紙白1.25D制約):")
    highlight_inputs = [224, 232, 240, 248, 255]
    for inp in highlight_inputs:
        v21_val = v21_measured[v21_measured['input'] == inp]['negative_density'].values[0]
        v22_target = v22_targets[inp]
        diff = v22_target - v21_val
        print(f"  Input {inp}: {v22_target:.2f}D (v21: {v21_val:.2f}D, {diff:+.2f}D)")

    # 予想実測値
    print("\nv22予想実測値 (+0.05Dオフセット想定):")
    for inp in highlight_inputs:
        target = v22_targets[inp]
        expected = target + 0.05
        print(f"  Input {inp}: {target:.2f}D → 実測{expected:.2f}D想定")

    print(f"\n  Input 255最大想定: 1.22 + 0.06 = 1.28D")
    print(f"  ✓ 紙白1.25D制約を若干超過の可能性あり")
    print(f"  → さらに安全にするならInput 255を1.20Dに設定")

    # アンカーポイント
    anchor_inputs = np.array(sorted(v22_targets.keys()))
    anchor_densities = np.array([v22_targets[i] for i in anchor_inputs])

    print(f"\nアンカーポイント: {len(anchor_inputs)}点（8刻み）")

    # 線形補間で256点生成
    input_values = np.arange(256)
    target_densities = np.interp(input_values, anchor_inputs, anchor_densities)

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

        # 問題箇所を表示（最初の10箇所のみ）
        problem_indices = np.where(quad_diffs > 200)[0]
        for idx in problem_indices[:10]:
            print(f"    Input {idx:3d}→{idx+1:3d}: Quad差分 {quad_diffs[idx]:.1f}")
        if len(problem_indices) > 10:
            print(f"    ... 他 {len(problem_indices)-10}箇所")
    else:
        print(f"  ✓ 境界線リスク: なし（全範囲で差分 < 200）")

    # ハイライト域の詳細
    print("\nv22ハイライト域の設計:")
    for i in range(1, len(highlight_inputs)):
        curr_inp = highlight_inputs[i]
        prev_inp = highlight_inputs[i-1]
        curr_dens = target_densities[curr_inp]
        prev_dens = target_densities[prev_inp]
        diff = curr_dens - prev_dens
        print(f"  {prev_inp}→{curr_inp}: {diff:.4f}D")

    total_highlight_range = target_densities[255] - target_densities[240]
    print(f"\nハイライト範囲（240-255）: {total_highlight_range:.4f}D")

    # ハイライト域のQuad差分確認
    print("\nハイライト域のQuad差分 (Input 224-255):")
    for i in range(224, 255):
        diff = quad_diffs[i]
        status = "✓" if diff < 200 else "⚠️"
        if i in [224, 232, 240, 248]:
            print(f"  {status} Input {i:3d}→{i+1:3d}: {diff:.1f}")

    # .quadファイル書き出し
    output_quad = 'PX1V-PtPd-v22.quad'
    with open(output_quad, 'w') as f:
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        f.write('# QuadProfile Version 2.8.0\n')
        f.write('# PX1V-PtPd-v22 - Paper White Constraint (Max 1.25D) - Linear\n')
        f.write('# Based on v21 measurements with offset correction\n')
        f.write('# 224: 1.06, 232: 1.10, 240: 1.15, 248: 1.20, 255: 1.22\n')
        f.write('# Expected: 240-255 = 0.07D\n')
        f.write('# Linear interpolation for smooth gradient\n')
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

    # v21実測値
    v21_inputs = v21_measured['input'].values
    v21_densities = v21_measured['negative_density'].values
    axes[0, 0].plot(v21_inputs, v21_densities, 'g--', linewidth=1.5,
                    marker='s', markersize=4, label='v21 measured', alpha=0.7)

    axes[0, 0].scatter(anchor_inputs, anchor_densities, c='red', s=30,
                       zorder=5, label='v22 anchors')
    axes[0, 0].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White (1.25D)')
    axes[0, 0].set_xlabel('Input Value', fontsize=12)
    axes[0, 0].set_ylabel('Negative Density', fontsize=12)
    axes[0, 0].set_title('v22: Full Range with Paper White Constraint (Linear)',
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

    # v22アンカー
    highlight_anchor_mask = anchor_inputs >= 200
    axes[0, 1].scatter(anchor_inputs[highlight_anchor_mask],
                       anchor_densities[highlight_anchor_mask],
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
    axes[1, 0].set_title('v22: Boundary Line Risk Analysis (Linear)',
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
    plt.savefig('v22_linear_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✓ グラフ保存: v22_linear_analysis.png")

    print("\n次のステップ:")
    print(f"  1. sudo cp {output_quad} /Library/Printers/QTR/quadtone/QuadP700/")
    print(f"  2. /Library/Printers/QTR/bin/quadcurves QuadP700")
    print(f"  3. defaults delete com.quadtonerip.QTR-Print-Tool")
    print(f"  4. QTR Print-Toolで v22 を選択してテストプリント")
    print(f"  5. 濃度測定で1.25D以内に収まっているか確認")

    return quad_values_checked, target_densities

if __name__ == '__main__':
    quad_values, densities = generate_v22_linear()

    print("\n" + "=" * 80)
    print("v22 カーブ生成完了 - 線形補間版")
    print("=" * 80)
