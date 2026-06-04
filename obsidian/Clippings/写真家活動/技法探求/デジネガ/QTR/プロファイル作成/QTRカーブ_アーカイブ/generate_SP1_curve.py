#!/usr/bin/env python3
"""
PX1V-PtPd-SP1カーブ生成

measurement_QTR-SP-1.csvの測定データから、
Quad値を逆算してQTRカーブを生成する
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# 基本定数（v22/v23と同じ）
SLOPE = 0.007387
INTERCEPT = 0.0935

def density_to_baseline(density):
    """濃度からBaseline値を計算（逆算）"""
    return (density - INTERCEPT) / SLOPE

def baseline_to_quad(baseline):
    """Baseline値からQuad値を計算"""
    return int(round(baseline * 257.0))

def generate_sp1_curve():
    """SP-1カーブを生成"""
    print("=" * 80)
    print("PX1V-PtPd-SP1: measurement_QTR-SP-1.csvからカーブ生成")
    print("=" * 80)

    # 測定データ読み込み
    measured = pd.read_csv('/Users/daisukekinoshita/Desktop/measurement_QTR-SP-1.csv')

    print(f"\n測定データ: {len(measured)}ポイント")
    print(f"  濃度範囲: {measured['negative_density'].min():.2f}D - {measured['negative_density'].max():.2f}D")

    # 紙白制約チェック
    max_density = measured['negative_density'].max()
    if max_density > 1.25:
        print(f"\n⚠️  警告: Input 255の濃度が紙白制約を超過")
        print(f"  実測: {max_density:.2f}D > 1.25D（超過: {max_density - 1.25:+.2f}D）")

    # 測定データからQuad値を逆算
    measured['baseline'] = density_to_baseline(measured['negative_density'])
    measured['quad_value'] = measured['baseline'].apply(baseline_to_quad)

    # 256ポイントのQuad値配列を作成（線形補間）
    measured_inputs = measured['input'].values
    measured_quads = measured['quad_value'].values

    # 線形補間関数を作成
    interp_func = interp1d(measured_inputs, measured_quads,
                           kind='linear', fill_value='extrapolate')

    # 全256ポイントのQuad値を生成
    all_inputs = np.arange(256)
    quad_values = np.zeros(256, dtype=int)

    for i in all_inputs:
        if i in measured_inputs:
            # 測定ポイントはそのまま使用
            quad_values[i] = int(measured_quads[list(measured_inputs).index(i)])
        else:
            # 補間
            interp_value = float(interp_func(i))
            quad_values[i] = int(round(interp_value))

    # 単調性を保証
    for i in range(1, 256):
        if quad_values[i] < quad_values[i-1]:
            quad_values[i] = quad_values[i-1]

    print("\nQuad値の範囲:")
    print(f"  Input 0: {quad_values[0]} (Baseline: {quad_values[0]/257.0:.2f})")
    print(f"  Input 255: {quad_values[255]} (Baseline: {quad_values[255]/257.0:.2f})")

    # 境界線リスク解析
    quad_diffs = np.diff(quad_values)
    max_diff = np.max(quad_diffs)
    max_diff_input = np.argmax(quad_diffs)

    print(f"\n境界線リスク解析:")
    print(f"  最大Quad差分: {max_diff:.0f} (Input {max_diff_input}→{max_diff_input+1})")

    if max_diff > 200:
        print(f"  ⚠️  境界線リスクあり（閾値200超過）")
        # リスク箇所を表示
        risky = np.where(quad_diffs > 200)[0]
        if len(risky) <= 10:
            for idx in risky:
                print(f"     Input {idx}→{idx+1}: {quad_diffs[idx]:.0f}")
    else:
        print(f"  ✓ 境界線リスクなし")

    # 濃度の再計算（検証用）
    baselines = quad_values / 257.0
    densities = baselines * SLOPE + INTERCEPT

    print("\n主要ポイントの検証:")
    print("Input  測定濃度  計算濃度  差分    Quad値")
    print("=" * 60)
    for i in measured['input']:
        measured_d = measured[measured['input'] == i]['negative_density'].values[0]
        calc_d = densities[i]
        diff = calc_d - measured_d
        quad = quad_values[i]
        status = "✓" if abs(diff) < 0.01 else "⚠️"
        print(f"{i:3d}    {measured_d:.2f}D     {calc_d:.2f}D    {diff:+.3f}D  {quad:5d}  {status}")

    # .quadファイル書き出し
    output_quad = 'PX1V-PtPd-SP1.quad'
    with open(output_quad, 'w') as f:
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        f.write('# QuadProfile Version 2.8.0\n')
        f.write('# PX1V-PtPd-SP1 - Generated from measurement_QTR-SP-1.csv\n')
        f.write('# Created: 2026-03-17\n')
        f.write('# WARNING: Input 255 exceeds paper white constraint (1.35D > 1.25D)\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')

        # Kチャンネル
        f.write('# K curve\n')
        for qv in quad_values:
            f.write(f'{int(qv)}\n')

        # 残り9チャンネル（全て0）
        for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
            f.write(f'# {channel} curve\n')
            for _ in range(256):
                f.write('0\n')

    print(f"\n✓ .quadファイル生成: {output_quad}")

    # .txtファイル
    output_txt = 'PX1V-PtPd-SP1.txt'
    df = pd.DataFrame({
        'Input': all_inputs,
        'Quad_Value': quad_values,
        'Baseline': baselines,
        'Calculated_Density': densities
    })
    df.to_csv(output_txt, index=False, float_format='%.6f')
    print(f"✓ 詳細データ: {output_txt}")

    # グラフ作成
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1. 濃度カーブ
    axes[0, 0].plot(all_inputs, densities, 'b-', linewidth=2, label='SP-1 calculated')
    axes[0, 0].scatter(measured['input'], measured['negative_density'],
                       c='red', s=100, zorder=5, marker='o',
                       label='Measured points', edgecolors='black', linewidths=1)
    axes[0, 0].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White Constraint (1.25D)')
    axes[0, 0].set_xlabel('Input Value', fontsize=12)
    axes[0, 0].set_ylabel('Negative Density', fontsize=12)
    axes[0, 0].set_title('SP-1: Density Curve', fontsize=14, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 2. ハイライト域拡大
    highlight_mask = all_inputs >= 200
    axes[0, 1].plot(all_inputs[highlight_mask], densities[highlight_mask],
                    'b-', linewidth=3, label='SP-1')
    measured_highlight = measured[measured['input'] >= 200]
    axes[0, 1].scatter(measured_highlight['input'],
                       measured_highlight['negative_density'],
                       c='red', s=150, zorder=5, marker='o',
                       label='Measured', edgecolors='black', linewidths=2)
    axes[0, 1].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White (1.25D)')
    axes[0, 1].set_xlabel('Input Value', fontsize=12)
    axes[0, 1].set_ylabel('Negative Density', fontsize=12)
    axes[0, 1].set_title('SP-1: Highlight Region (200-255)',
                         fontsize=14, fontweight='bold')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_xlim(200, 256)

    # 3. Quad差分
    axes[1, 0].plot(all_inputs[:-1], quad_diffs, 'g-', linewidth=2)
    axes[1, 0].axhline(y=200, color='red', linestyle='--', linewidth=2,
                       label='Boundary Risk (200)')
    axes[1, 0].set_xlabel('Input Value', fontsize=12)
    axes[1, 0].set_ylabel('Quad Difference', fontsize=12)
    axes[1, 0].set_title('SP-1: Boundary Line Risk Analysis',
                         fontsize=14, fontweight='bold')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_ylim(-10, min(max_diff + 20, 300))

    # 4. 測定値vs計算値の誤差
    measured_errors = []
    for i in measured['input']:
        measured_d = measured[measured['input'] == i]['negative_density'].values[0]
        calc_d = densities[i]
        measured_errors.append(calc_d - measured_d)

    axes[1, 1].bar(measured['input'], measured_errors, width=6, color='blue', alpha=0.7)
    axes[1, 1].axhline(y=0, color='black', linestyle='-', linewidth=1)
    axes[1, 1].axhline(y=0.01, color='green', linestyle='--', linewidth=1, alpha=0.5)
    axes[1, 1].axhline(y=-0.01, color='green', linestyle='--', linewidth=1, alpha=0.5)
    axes[1, 1].set_xlabel('Input Value', fontsize=12)
    axes[1, 1].set_ylabel('Error (Calculated - Measured)', fontsize=12)
    axes[1, 1].set_title('SP-1: Measurement vs Calculation Error',
                         fontsize=14, fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('SP1_curve_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✓ グラフ保存: SP1_curve_analysis.png")

    print("\n次のステップ:")
    print(f"  1. sudo cp {output_quad} /Library/Printers/QTR/quadtone/QuadP700/")
    print(f"  2. /Library/Printers/QTR/bin/quadcurves QuadP700")
    print(f"  3. QTR Print-Toolで PX1V-PtPd-SP1 を選択")

    return quad_values, densities

if __name__ == '__main__':
    quad_values, densities = generate_sp1_curve()

    print("\n" + "=" * 80)
    print("SP-1 カーブ生成完了")
    print("測定データから逆算したQuad値で生成")
    print("⚠️  注意: Input 255が紙白制約を超過しています")
    print("=" * 80)
