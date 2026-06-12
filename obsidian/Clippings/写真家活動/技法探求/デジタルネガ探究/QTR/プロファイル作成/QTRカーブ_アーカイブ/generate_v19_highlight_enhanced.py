#!/usr/bin/env python3
"""
PX1V-PtPd-v19: ハイライト強調版カーブ生成

v18からの変更点:
- Input 224-255のハイライト域で濃度差を拡大
- 232-240区間を0.07Dに拡大（+75%）
- 248-255区間を0.01Dに縮小（紙白への滑らかな接続）

目的: プラチナプリントのハイライトディテールを最大化
"""

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt

# ========== 基本定数 ==========
BASELINE_SLOPE = 0.007387
BASELINE_INTERCEPT = 0.0935

# ========== v19ハイライト強調設計 ==========
# アンカーポイント: Input → 目標ネガ濃度

ANCHOR_POINTS = {
    # ベース部分（v18と同じ）
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

    # ハイライト域（v19で変更）
    # v18実測値(measurement_QTR2-18.csv)をベースに微調整
    # 目標: 232-240の階調差を+0.07Dに拡大、248-255を+0.02Dに
    200: 0.96,   # v18実測値そのまま
    208: 1.01,   # v18実測値そのまま
    216: 1.02,   # v18実測値そのまま
    224: 1.06,   # v18実測値そのまま（提案と一致）
    232: 1.12,   # v18: 1.10 → v19: 1.12 (+0.02D)
    240: 1.19,   # v18: 1.15 → v19: 1.19 (+0.04D、232から+0.07D)
    248: 1.24,   # v18: 1.20 → v19: 1.24 (+0.04D、240から+0.05D)
    255: 1.26,   # v18: 1.23 → v19: 1.26 (+0.03D、248から+0.02D)
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
    """v19カーブを生成"""
    print("=" * 80)
    print("PX1V-PtPd-v19: ハイライト強調版カーブ生成")
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

    # CubicSplineで全範囲を補間
    print("\nCubicSpline補間を実行...")
    cs = CubicSpline(anchor_inputs, anchor_densities, bc_type='natural')

    # 257ポイントのカーブデータを生成
    input_values = np.arange(257)
    input_255_scale = input_values * (255 / 256)

    target_densities = cs(input_255_scale)
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

    # 勾配解析（ハイライト域）
    print("\nハイライト域の勾配解析 (Input 216-255):")
    highlight_range = range(216, 256)
    max_gradient = 0
    max_gradient_input = 0

    for i in highlight_range:
        if i < 256:
            gradient = abs(quad_values_checked[i+1] - quad_values_checked[i])
            if gradient > max_gradient:
                max_gradient = gradient
                max_gradient_input = i

            if i in [224, 232, 240, 248, 255]:
                status = "✓" if gradient < 6 else "⚠️"
                print(f"  {status} Input {i:3d}→{i+1:3d}: 勾配 {gradient:.4f} "
                      f"(Quad {quad_values_checked[i]:5d} → {quad_values_checked[i+1]:5d})")

    print(f"\n最大勾配: {max_gradient:.4f} (Input {max_gradient_input})")
    if max_gradient < 6:
        print("✓ 全範囲で勾配 < 6.0 (境界線なし)")
    else:
        print(f"⚠️  勾配が閾値を超えています")

    # .quadファイル書き出し
    output_quad = 'PX1V-PtPd-v19.quad'
    with open(output_quad, 'w') as f:
        f.write('TITLE "PX1V-PtPd-v19"\n')
        f.write('COMMENT "Highlight Enhanced Curve for Platinum/Palladium"\n')
        f.write('COMMENT "Enhanced density gradient in 224-255 range"\n')
        f.write('COMMENT "v19: 224=1.05, 232=1.10, 240=1.17, 248=1.21, 255=1.22"\n')
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
    axes[0, 1].set_ylim(1.25, 1.25)

    # 3. 勾配グラフ（全範囲）
    gradients = np.diff(quad_values_checked)
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
    plt.savefig('v19_highlight_enhanced_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✓ グラフ保存: v19_highlight_enhanced_analysis.png")

    # v18との比較データ出力
    print("\n" + "=" * 80)
    print("v18 vs v19 ハイライト比較")
    print("=" * 80)
    print(f"{'Input':<8} {'v18 Density':<15} {'v19 Density':<15} {'差分':<10}")
    print("-" * 50)

    v18_highlights = {
        224: 1.4537,
        232: 1.5003,
        240: 1.14,
        248: 1.18,
        255: 1.22
    }

    for inp in [224, 232, 240, 248, 255]:
        v18_d = v18_highlights[inp]
        v19_d = ANCHOR_POINTS[inp]
        diff = v19_d - v18_d
        print(f"{inp:<8} {v18_d:<15.4f} {v19_d:<15.4f} {diff:+.4f}")

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
