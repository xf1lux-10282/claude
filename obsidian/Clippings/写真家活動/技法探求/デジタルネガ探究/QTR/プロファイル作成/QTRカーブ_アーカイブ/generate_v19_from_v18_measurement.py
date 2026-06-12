#!/usr/bin/env python3
"""
PX1V-PtPd-v19: v18実測値ベースのハイライト強化版

measurement_QTR2-18.csvの実測値を使用し、
ハイライト域(232-255)のみを微調整
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ========== 基本定数 ==========
BASELINE_SLOPE = 0.007387
BASELINE_INTERCEPT = 0.0935

def density_to_baseline(density):
    """濃度からベースライン値を計算"""
    baseline = (density - BASELINE_INTERCEPT) / BASELINE_SLOPE
    return max(0.0, min(65535.0, baseline))

def baseline_to_quad(baseline):
    """ベースライン値をQuad値に変換"""
    quad = baseline * 257
    return int(round(min(65535, max(0, quad))))

def generate_v19_curve():
    """v19カーブを生成"""
    print("=" * 80)
    print("PX1V-PtPd-v19: v18実測値ベースのハイライト強化版")
    print("=" * 80)

    # v18実測値を読み込み
    v18_data = {
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
        224: 1.06,  # ここから微調整
        232: 1.10,  # v18実測
        240: 1.15,  # v18実測
        248: 1.20,  # v18実測
        255: 1.23,  # v18実測
    }

    # v19の調整（ハイライト域全体）
    v19_adjustments = {
        200: 0.95,  # v18: 0.96 → -0.01D（滑らかな接続）
        208: 1.00,  # v18: 1.01 → -0.01D（滑らかな接続）
        232: 1.12,  # v18: 1.10 → +0.02D
        240: 1.19,  # v18: 1.15 → +0.04D
        248: 1.24,  # v18: 1.20 → +0.04D
        255: 1.26,  # v18: 1.23 → +0.03D
    }

    # v19アンカーポイント作成
    v19_anchors = v18_data.copy()
    v19_anchors.update(v19_adjustments)

    anchor_inputs = np.array(sorted(v19_anchors.keys()))
    anchor_densities = np.array([v19_anchors[i] for i in anchor_inputs])

    print(f"\n設計アンカーポイント: {len(anchor_inputs)}点")
    print(f"  - v18実測値そのまま: 0-192")
    print(f"  - v19微調整: 200-255")

    print("\nハイライト域の変更:")
    for inp in [200, 208, 216, 224, 232, 240, 248, 255]:
        v18_val = v18_data[inp]
        v19_val = v19_anchors[inp]
        diff = v19_val - v18_val
        status = "調整" if inp in v19_adjustments else "維持"
        print(f"  Input {inp}: {v18_val:.2f}D → {v19_val:.2f}D ({diff:+.2f}D) [{status}]")

    print("\nv19ハイライト階調差:")
    highlight_inputs = [224, 232, 240, 248, 255]
    for i in range(1, len(highlight_inputs)):
        curr_inp = highlight_inputs[i]
        prev_inp = highlight_inputs[i-1]
        curr_dens = v19_anchors[curr_inp]
        prev_dens = v19_anchors[prev_inp]
        diff = curr_dens - prev_dens
        print(f"  {prev_inp}→{curr_inp}: {diff:.4f}D")

    # 線形補間で257ポイント生成
    print("\n線形補間を実行...")
    input_values = np.arange(257)
    input_255_scale = input_values * (255 / 256)

    target_densities = np.interp(input_255_scale, anchor_inputs, anchor_densities)
    baselines = np.array([density_to_baseline(d) for d in target_densities])
    quad_values = np.array([baseline_to_quad(b) for b in baselines])

    # 単調性チェック
    quad_values_checked = [quad_values[0]]
    for i in range(1, len(quad_values)):
        quad_values_checked.append(max(quad_values[i], quad_values_checked[i-1]))
    quad_values_checked = np.array(quad_values_checked)

    corrections = np.sum(quad_values != quad_values_checked)
    if corrections > 0:
        print(f"⚠️  単調性補正: {corrections}ポイント")
    else:
        print(f"✓ 単調性チェック: OK")

    # 勾配解析
    gradients = np.diff(quad_values_checked)
    max_gradient = np.max(gradients)
    max_gradient_input = np.argmax(gradients)

    print(f"\n勾配解析:")
    print(f"  最大勾配: {max_gradient:.4f} (Input {max_gradient_input})")

    if max_gradient < 6:
        print("  ✓ 全範囲で勾配 < 6.0 (境界線なし)")
    else:
        print(f"  ⚠️  勾配が閾値を超えています")

        # 問題箇所を表示
        problem_count = np.sum(gradients > 6)
        print(f"  勾配 > 6.0 の箇所: {problem_count}箇所")

    # ハイライト域の勾配
    print("\nハイライト域の勾配 (Input 216-255):")
    for i in range(216, 256):
        gradient = abs(quad_values_checked[i+1] - quad_values_checked[i])
        if i in [224, 232, 240, 248, 255]:
            status = "✓" if gradient < 6 else "⚠️"
            print(f"  {status} Input {i:3d}→{i+1:3d}: 勾配 {gradient:.4f}")

    # .quadファイル書き出し
    output_quad = 'PX1V-PtPd-v19.quad'
    with open(output_quad, 'w') as f:
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        f.write('# QuadProfile Version 2.8.0\n')
        f.write('# PX1V-PtPd-v19 - Highlight Enhanced based on v18 measurements\n')
        f.write('# 200: 0.96→0.95, 208: 1.01→1.00 (smooth connection)\n')
        f.write('# 232: 1.10→1.12, 240: 1.15→1.19, 248: 1.20→1.24, 255: 1.23→1.26\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')

        # Kチャンネル（Photo Black）
        f.write('# K curve\n')
        for qv in quad_values_checked:
            f.write(f'{int(qv)}\n')

        # 残り9チャンネル（全て0 = 使用しない）
        # C, M, Y, LC, LM, LK, LLK, V, MK
        for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
            f.write(f'# {channel} curve\n')
            for _ in range(257):
                f.write('0\n')

    print(f"\n✓ .quadファイル生成: {output_quad}")

    # .txtファイル
    output_txt = 'PX1V-PtPd-v19.txt'
    df = pd.DataFrame({
        'Input': input_values,
        'Input_255': input_255_scale,
        'Target_Density': target_densities,
        'Baseline': baselines,
        'Quad_Value': quad_values_checked
    })
    df.to_csv(output_txt, index=False, float_format='%.6f')
    print(f"✓ 詳細データ: {output_txt}")

    # グラフ作成
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1. 全範囲濃度カーブ
    axes[0, 0].plot(input_255_scale, target_densities, 'b-', linewidth=2, label='v19')
    axes[0, 0].scatter(anchor_inputs, anchor_densities, c='red', s=30, zorder=5)
    axes[0, 0].set_xlabel('Input Value', fontsize=12)
    axes[0, 0].set_ylabel('Negative Density', fontsize=12)
    axes[0, 0].set_title('v19: Full Range Density Curve', fontsize=14, fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3)

    # 2. ハイライト域拡大
    highlight_mask = input_255_scale >= 200
    axes[0, 1].plot(input_255_scale[highlight_mask], target_densities[highlight_mask],
                    'b-', linewidth=3, label='v19')

    # v18実測値をプロット
    v18_highlight_inputs = [200, 208, 216, 224, 232, 240, 248, 255]
    v18_highlight_densities = [v18_data[i] for i in v18_highlight_inputs]
    axes[0, 1].plot(v18_highlight_inputs, v18_highlight_densities,
                    'g--', linewidth=2, marker='s', markersize=6, label='v18 measured', alpha=0.7)

    # v19調整ポイント
    v19_highlight_inputs = [232, 240, 248, 255]
    v19_highlight_densities = [v19_anchors[i] for i in v19_highlight_inputs]
    axes[0, 1].scatter(v19_highlight_inputs, v19_highlight_densities,
                       c='red', s=100, zorder=5, marker='o', label='v19 adjusted')

    axes[0, 1].set_xlabel('Input Value', fontsize=12)
    axes[0, 1].set_ylabel('Negative Density', fontsize=12)
    axes[0, 1].set_title('v19 vs v18: Highlight Comparison', fontsize=14, fontweight='bold')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_xlim(200, 256)

    # 3. 全範囲勾配
    axes[1, 0].plot(input_values[:-1], gradients, 'g-', linewidth=1.5)
    axes[1, 0].axhline(y=6, color='red', linestyle='--', linewidth=2, label='Threshold (6.0)')
    axes[1, 0].set_xlabel('Input Value', fontsize=12)
    axes[1, 0].set_ylabel('Gradient', fontsize=12)
    axes[1, 0].set_title('v19: Full Range Gradient', fontsize=14, fontweight='bold')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_ylim(-1, max(10, min(max_gradient + 1, 20)))

    # 4. ハイライト勾配
    highlight_grad_mask = input_values[:-1] >= 200
    axes[1, 1].plot(input_values[:-1][highlight_grad_mask], gradients[highlight_grad_mask],
                    'g-', linewidth=3, marker='o', markersize=4)
    axes[1, 1].axhline(y=6, color='red', linestyle='--', linewidth=2, label='Threshold')
    axes[1, 1].set_xlabel('Input Value', fontsize=12)
    axes[1, 1].set_ylabel('Gradient', fontsize=12)
    axes[1, 1].set_title('v19: Highlight Gradient (200-255)', fontsize=14, fontweight='bold')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_xlim(200, 256)
    axes[1, 1].set_ylim(-1, 10)

    plt.tight_layout()
    plt.savefig('v19_from_v18_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✓ グラフ保存: v19_from_v18_analysis.png")

    print("\n次のステップ:")
    print(f"  1. sudo cp {output_quad} /Library/Printers/QTR/quadtone/QuadP700/")
    print(f"  2. /Library/Printers/QTR/bin/quadcurves QuadP700")
    print(f"  3. defaults delete com.quadtonerip.QTR-Print-Tool")
    print(f"  4. QTR Print-Toolで v19 を選択してテストプリント")

    return quad_values_checked, target_densities

if __name__ == '__main__':
    quad_values, densities = generate_v19_curve()

    print("\n" + "=" * 80)
    print("v19 カーブ生成完了")
    print("=" * 80)
