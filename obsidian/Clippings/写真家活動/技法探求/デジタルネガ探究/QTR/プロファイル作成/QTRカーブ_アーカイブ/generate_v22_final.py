#!/usr/bin/env python3
"""
PX1V-PtPd-v22: 紙白制約版 (上限1.25D)

重要な制約:
- Input 0-216: v18実測値を絶対に変更しない
- Input 224-255: v22目標値（紙白1.25D制約考慮）
- 線形補間で滑らかに接続
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

def generate_v22_final():
    """v22カーブを生成 - Input 0-216は絶対変更なし"""
    print("=" * 80)
    print("PX1V-PtPd-v22: 紙白制約版 (上限1.25D)")
    print("=" * 80)

    # v18実測値を読み込み（Input 0-216は絶対変更しない）
    v18_measured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/QTRカーブ情報（V18使用）/backup_v18_FINAL_20260314/measurement_QTR2-18.csv')

    # v21実測値（比較用）
    v21_measured = pd.read_csv('/Users/daisukekinoshita/Desktop/measurement_QTR2-21.csv')

    print("\n制約条件:")
    print("  ✓ Input 0-216: v18実測値を絶対に変更しない")
    print("  ✓ Input 224-255: v22目標値（紙白1.25D制約）")

    print("\nv18実測値（Input 0-216）:")
    for inp in [0, 40, 80, 120, 160, 200, 216]:
        v18_val = v18_measured[v18_measured['input'] == inp]['negative_density'].values[0]
        print(f"  Input {inp}: {v18_val:.2f}D")

    print("\nv21測定結果（ハイライト域）:")
    for inp in [224, 232, 240, 248, 255]:
        v21_val = v21_measured[v21_measured['input'] == inp]['negative_density'].values[0]
        print(f"  Input {inp}: {v21_val:.2f}D")

    # v22の目標値設定
    # Input 0-216: v18実測値そのまま
    v22_targets = {}
    for inp in [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120, 128, 136, 144, 152, 160, 168, 176, 184, 192, 200, 208, 216]:
        v18_row = v18_measured[v18_measured['input'] == inp]
        if len(v18_row) > 0:
            v22_targets[inp] = v18_row['negative_density'].values[0]

    # Input 224-255: v22目標値（紙白1.25D制約）
    v22_targets[224] = 1.06  # v21: 1.11D → -0.05D
    v22_targets[232] = 1.10  # v21: 1.15D → -0.05D
    v22_targets[240] = 1.15  # v21: 1.25D → -0.10D
    v22_targets[248] = 1.20  # v21: 1.32D → -0.12D
    v22_targets[255] = 1.22  # v21: 1.34D → -0.12D（1.25D制約）

    print("\nv22目標値（ハイライト域のみ調整）:")
    for inp in [224, 232, 240, 248, 255]:
        v21_val = v21_measured[v21_measured['input'] == inp]['negative_density'].values[0]
        v22_target = v22_targets[inp]
        diff = v22_target - v21_val
        print(f"  Input {inp}: {v22_target:.2f}D (v21: {v21_val:.2f}D, {diff:+.2f}D)")

    # 予想実測値
    print("\nv22予想実測値 (+0.05Dオフセット想定):")
    for inp in [224, 232, 240, 248, 255]:
        target = v22_targets[inp]
        expected = target + 0.05
        status = "✓" if expected <= 1.28 else "⚠️"
        print(f"  {status} Input {inp}: {target:.2f}D → 実測{expected:.2f}D想定")

    print(f"\n  Input 255最大想定: 1.22 + 0.06 = 1.28D")
    print(f"  注: 紙白1.25Dを若干超過の可能性")

    # アンカーポイント
    anchor_inputs = np.array(sorted(v22_targets.keys()))
    anchor_densities = np.array([v22_targets[i] for i in anchor_inputs])

    print(f"\nアンカーポイント: {len(anchor_inputs)}点")
    print(f"  - Input 0-216: v18実測値（{len([i for i in anchor_inputs if i <= 216])}点）")
    print(f"  - Input 224-255: v22目標値（5点）")

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

        # 問題箇所を表示
        problem_indices = np.where(quad_diffs > 200)[0]
        for idx in problem_indices[:10]:
            print(f"    Input {idx:3d}→{idx+1:3d}: Quad差分 {quad_diffs[idx]:.1f}")
        if len(problem_indices) > 10:
            print(f"    ... 他 {len(problem_indices)-10}箇所")
    else:
        print(f"  ✓ 境界線リスク: なし（全範囲で差分 < 200）")

    # ハイライト域のQuad差分確認
    print("\nハイライト域のQuad差分 (Input 216-255):")
    for i in range(216, 255):
        diff = quad_diffs[i]
        if i in [216, 224, 232, 240, 248]:
            status = "✓" if diff < 200 else "⚠️"
            print(f"  {status} Input {i:3d}→{i+1:3d}: {diff:.1f}")

    # ハイライト範囲
    print("\nv22ハイライト域の設計:")
    highlight_inputs = [216, 224, 232, 240, 248, 255]
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
        f.write('# Input 0-216: v18 measured values (unchanged)\n')
        f.write('# Input 224-255: v22 targets (paper white constraint)\n')
        f.write('# 224: 1.06, 232: 1.10, 240: 1.15, 248: 1.20, 255: 1.22\n')
        f.write('# Linear interpolation between anchor points\n')
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

    # v18実測値（Input 0-216）
    v18_inputs = v18_measured['input'].values
    v18_densities = v18_measured['negative_density'].values
    v18_mask = v18_inputs <= 216
    axes[0, 0].scatter(v18_inputs[v18_mask], v18_densities[v18_mask],
                       c='green', s=20, zorder=5, label='v18 (unchanged)', alpha=0.7)

    # v21実測値
    v21_inputs = v21_measured['input'].values
    v21_densities = v21_measured['negative_density'].values
    axes[0, 0].plot(v21_inputs, v21_densities, 'g--', linewidth=1.5,
                    marker='s', markersize=4, label='v21 measured', alpha=0.5)

    # v22ハイライト目標値
    v22_highlight_inputs = [224, 232, 240, 248, 255]
    v22_highlight_densities = [v22_targets[i] for i in v22_highlight_inputs]
    axes[0, 0].scatter(v22_highlight_inputs, v22_highlight_densities,
                       c='red', s=100, zorder=6, marker='o', label='v22 targets')

    axes[0, 0].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White (1.25D)')
    axes[0, 0].set_xlabel('Input Value', fontsize=12)
    axes[0, 0].set_ylabel('Negative Density', fontsize=12)
    axes[0, 0].set_title('v22: v18 Base (0-216) + v22 Highlight (224-255)',
                         fontsize=14, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 2. ハイライト域拡大
    highlight_mask = input_values >= 200
    axes[0, 1].plot(input_values[highlight_mask], target_densities[highlight_mask],
                    'b-', linewidth=3, label='v22')

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

    # v22ハイライト目標値
    axes[0, 1].scatter(v22_highlight_inputs, v22_highlight_densities,
                       c='red', s=150, zorder=6, marker='o', label='v22 targets')

    axes[0, 1].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White')
    axes[0, 1].set_xlabel('Input Value', fontsize=12)
    axes[0, 1].set_ylabel('Negative Density', fontsize=12)
    axes[0, 1].set_title('v22 Highlight: v18→v22 Transition',
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
    plt.savefig('v22_final_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✓ グラフ保存: v22_final_analysis.png")

    print("\n次のステップ:")
    print(f"  1. sudo cp {output_quad} /Library/Printers/QTR/quadtone/QuadP700/")
    print(f"  2. /Library/Printers/QTR/bin/quadcurves QuadP700")
    print(f"  3. defaults delete com.quadtonerip.QTR-Print-Tool")
    print(f"  4. QTR Print-Toolで v22 を選択してテストプリント")
    print(f"  5. 濃度測定で1.25D以内に収まっているか確認")

    return quad_values_checked, target_densities

if __name__ == '__main__':
    quad_values, densities = generate_v22_final()

    print("\n" + "=" * 80)
    print("v22 カーブ生成完了")
    print("Input 0-216: v18実測値（変更なし）")
    print("Input 224-255: v22目標値（紙白1.25D制約）")
    print("=" * 80)
