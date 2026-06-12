#!/usr/bin/env python3
"""
PX1V-PtPd-v19: ハイライト強調版カーブ生成（線形補間版）

CubicSplineではなく線形補間を使用して、滑らかなカーブを生成
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ========== 基本定数 ==========
BASELINE_SLOPE = 0.007387
BASELINE_INTERCEPT = 0.0935

# ========== v19設計（v18実測値ベース） ==========
ANCHOR_POINTS = {
    0: 0.0931,
    8: 0.1155,
    16: 0.1429,
    24: 0.1628,
    32: 0.1890,
    40: 0.2410,
    48: 0.2592,
    56: 0.2994,
    64: 0.3331,
    72: 0.3783,
    80: 0.4192,
    88: 0.4771,
    96: 0.5203,
    104: 0.5502,
    112: 0.6188,
    120: 0.6690,
    128: 0.7060,
    136: 0.7386,
    144: 0.8182,
    152: 0.8680,
    160: 0.9315,
    168: 0.83,   # v18実測値
    176: 0.87,   # v18実測値
    184: 0.90,   # v18実測値
    192: 0.94,   # v18実測値
    200: 0.96,   # v18実測値
    208: 1.01,   # v18実測値
    216: 1.02,   # v18実測値
    224: 1.06,   # v18実測値
    232: 1.12,   # v19: +0.02D
    240: 1.19,   # v19: +0.04D
    248: 1.24,   # v19: +0.04D
    255: 1.26,   # v19: +0.03D
}

def density_to_baseline(density):
    """濃度からベースライン値を計算"""
    baseline = (density - BASELINE_INTERCEPT) / BASELINE_SLOPE
    return max(0.0, min(65535.0, baseline))

def baseline_to_quad(baseline):
    """ベースライン値をQuad値に変換"""
    quad = baseline * 257
    return int(round(min(65535, max(0, quad))))

def generate_v19_curve():
    """v19カーブを生成（線形補間）"""
    print("=" * 80)
    print("PX1V-PtPd-v19: ハイライト強調版カーブ生成（線形補間）")
    print("=" * 80)

    # アンカーポイントを配列に変換
    anchor_inputs = np.array(sorted(ANCHOR_POINTS.keys()))
    anchor_densities = np.array([ANCHOR_POINTS[i] for i in anchor_inputs])

    print(f"\n設計アンカーポイント: {len(anchor_inputs)}点")
    print("\nハイライト域の濃度設計:")
    highlight_inputs = [224, 232, 240, 248, 255]
    for i in range(len(highlight_inputs)):
        inp = highlight_inputs[i]
        density = ANCHOR_POINTS[inp]
        if i > 0:
            prev_inp = highlight_inputs[i-1]
            prev_density = ANCHOR_POINTS[prev_inp]
            diff = density - prev_density
            print(f"  Input {inp:3d} → {density:.4f}D  (差: {diff:+.4f}D)")
        else:
            print(f"  Input {inp:3d} → {density:.4f}D")

    # 線形補間で257ポイント生成
    print("\n線形補間を実行...")
    input_values = np.arange(257)
    input_255_scale = input_values * (255 / 256)

    # 線形補間（np.interp）
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

    # 勾配解析（全範囲）
    gradients = np.diff(quad_values_checked)
    max_gradient = np.max(gradients)
    max_gradient_input = np.argmax(gradients)

    print(f"\n全範囲の勾配解析:")
    print(f"  最大勾配: {max_gradient:.4f} (Input {max_gradient_input})")

    if max_gradient < 6:
        print("  ✓ 全範囲で勾配 < 6.0 (境界線なし)")
    else:
        print(f"  ⚠️  勾配が閾値を超えています")

        # 勾配 > 6 の箇所を表示
        problem_inputs = np.where(gradients > 6)[0]
        if len(problem_inputs) > 0:
            print(f"  問題のある箇所: {len(problem_inputs)}箇所")
            for inp in problem_inputs[:10]:  # 最初の10箇所のみ表示
                print(f"    Input {inp}→{inp+1}: 勾配 {gradients[inp]:.4f}")

    # ハイライト域の勾配解析
    print("\nハイライト域の勾配解析 (Input 216-255):")
    highlight_range = range(216, 256)

    for i in highlight_range:
        if i < 256:
            gradient = abs(quad_values_checked[i+1] - quad_values_checked[i])
            if i in [224, 232, 240, 248, 255]:
                status = "✓" if gradient < 6 else "⚠️"
                print(f"  {status} Input {i:3d}→{i+1:3d}: 勾配 {gradient:.4f} "
                      f"(Quad {quad_values_checked[i]:5d} → {quad_values_checked[i+1]:5d})")

    # .quadファイル書き出し
    output_quad = 'PX1V-PtPd-v19.quad'
    with open(output_quad, 'w') as f:
        f.write('TITLE "PX1V-PtPd-v19"\n')
        f.write('COMMENT "Highlight Enhanced Curve for Platinum/Palladium"\n')
        f.write('COMMENT "Linear interpolation, based on v18 measurements"\n')
        f.write('COMMENT "232-240: +0.07D gradient enhancement"\n')
        f.write('COMMENT "248-255: +0.02D smooth transition to paper white"\n')
        f.write('COMMENT "2026 Daisuke Kinoshita"\n\n')

        f.write('K 257\n')
        for qv in quad_values_checked:
            f.write(f' {int(qv):5d}\n')

        f.write('\nC 2\n 0\n 65535\n')
        f.write('M 2\n 0\n 65535\n')
        f.write('Y 2\n 0\n 65535\n')
        f.write('P 2\n 0\n 65535\n')
        f.write('k 2\n 0\n 65535\n')
        f.write('c 2\n 0\n 65535\n')
        f.write('m 2\n 0\n 65535\n')

    print(f"\n✓ .quadファイル生成: {output_quad}")

    # .txtファイル（詳細データ）
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

    # 1. 濃度カーブ（全範囲）
    axes[0, 0].plot(input_255_scale, target_densities, 'b-', linewidth=2, label='v19 Curve')
    axes[0, 0].scatter(anchor_inputs, anchor_densities, c='red', s=50,
                       zorder=5, label='Anchor Points')
    axes[0, 0].set_xlabel('Input Value (0-255)', fontsize=12)
    axes[0, 0].set_ylabel('Negative Density', fontsize=12)
    axes[0, 0].set_title('v19: Density Curve (Full Range)', fontsize=14, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 2. ハイライト域拡大
    highlight_mask = input_255_scale >= 200
    axes[0, 1].plot(input_255_scale[highlight_mask], target_densities[highlight_mask],
                    'b-', linewidth=3, label='v19')
    axes[0, 1].scatter([224, 232, 240, 248, 255],
                       [ANCHOR_POINTS[i] for i in [224, 232, 240, 248, 255]],
                       c='red', s=100, zorder=5, label='Key Points')

    # 各ポイントにラベル
    for inp in [224, 232, 240, 248, 255]:
        d = ANCHOR_POINTS[inp]
        axes[0, 1].annotate(f'{inp}\n{d:.2f}D', xy=(inp, d),
                           xytext=(inp, d + 0.03), fontsize=10,
                           ha='center', bbox=dict(boxstyle='round,pad=0.3',
                           facecolor='yellow', alpha=0.7))

    axes[0, 1].set_xlabel('Input Value', fontsize=12)
    axes[0, 1].set_ylabel('Negative Density', fontsize=12)
    axes[0, 1].set_title('v19: Highlight Detail (Input 200-255)', fontsize=14, fontweight='bold')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_xlim(200, 256)

    # 3. 勾配グラフ（全範囲）
    axes[1, 0].plot(input_values[:-1], gradients, 'g-', linewidth=1.5)
    axes[1, 0].axhline(y=6, color='red', linestyle='--', linewidth=2, label='Boundary Threshold (6.0)')
    axes[1, 0].set_xlabel('Input Value', fontsize=12)
    axes[1, 0].set_ylabel('Gradient (Quad差)', fontsize=12)
    axes[1, 0].set_title('v19: Gradient Analysis (Full Range)', fontsize=14, fontweight='bold')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_ylim(-1, 10)

    # 4. ハイライト勾配拡大
    highlight_grad_mask = input_values[:-1] >= 200
    axes[1, 1].plot(input_values[:-1][highlight_grad_mask], gradients[highlight_grad_mask],
                    'g-', linewidth=3, marker='o', markersize=4)
    axes[1, 1].axhline(y=6, color='red', linestyle='--', linewidth=2, label='Threshold')
    axes[1, 1].set_xlabel('Input Value', fontsize=12)
    axes[1, 1].set_ylabel('Gradient', fontsize=12)
    axes[1, 1].set_title('v19: Highlight Gradient (Input 200-255)', fontsize=14, fontweight='bold')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_xlim(200, 256)

    plt.tight_layout()
    plt.savefig('v19_linear_interp_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✓ グラフ保存: v19_linear_interp_analysis.png")

    print("\n次のステップ:")
    print(f"  1. sudo cp {output_quad} /Library/Printers/QTR/quadtone/QuadP700/")
    print(f"  2. /Library/Printers/QTR/bin/quadcurves QuadP700")
    print(f"  3. defaults delete com.quadtonerip.QTR-Print-Tool")
    print(f"  4. QTR Print-Toolで v19 を選択してテストプリント")
    print(f"  5. ハイライトディテールの改善を確認")

    return quad_values_checked, target_densities

if __name__ == '__main__':
    quad_values, densities = generate_v19_curve()

    print("\n" + "=" * 80)
    print("v19 カーブ生成完了")
    print("=" * 80)
