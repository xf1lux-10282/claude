#!/usr/bin/env python3
"""
PX1V-PtPd-Linear v18 カーブ生成
v14のInput 48-104（最良の補間）+ v17のInput 112-192（追加補間）
全範囲で最適化された統合版
"""

import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline

# v12の実測データ読み込み
v12_data = pd.read_csv('/Users/daisukekinoshita/Desktop/measurement_QTR2-12.csv')

print("=== v18 カーブ生成開始 ===")
print("v14範囲（Input 48-104）+ v17範囲（Input 112-192）")
print("計算式: baseline * 257（v14/v17 FIXEDと同じ）\n")

# v14で使用した制御点（Input 48-104のスプライン補間）
v14_control_points_input = np.array([40, 48, 104, 112])
v14_control_points_density = []
for cp in v14_control_points_input:
    density = v12_data[v12_data['input'] == cp]['negative_density'].values[0]
    v14_control_points_density.append(density)
v14_control_points_density = np.array(v14_control_points_density)

# v14のスプライン補間
v14_spline = CubicSpline(v14_control_points_input, v14_control_points_density)

print("v14の補間範囲（Input 48-104）:")
for inp in [48, 56, 64, 72, 80, 88, 96, 104]:
    density = v14_spline(inp)
    v12_dens = v12_data[v12_data['input'] == inp]['negative_density'].values[0]
    diff = density - v12_dens
    print(f"  Input {inp:>3}: {density:.4f} (v12: {v12_dens:.4f}, 差: {diff:+.4f})")

# v17で追加する範囲の制御点（Input 112-192）
v17_control_points_input = np.array([104, 112, 144, 192, 200])
v17_control_points_density = []
for cp in v17_control_points_input:
    density = v12_data[v12_data['input'] == cp]['negative_density'].values[0]
    v17_control_points_density.append(density)
v17_control_points_density = np.array(v17_control_points_density)

# v17のスプライン補間
v17_spline = CubicSpline(v17_control_points_input, v17_control_points_density)

print("\nv17の追加補間範囲（Input 112-192）:")
for inp in [112, 120, 128, 136, 144, 152, 160, 168, 176, 184, 192]:
    if inp in v17_control_points_input:
        status = "（制御点）"
    else:
        status = "（補間）"
    density = v17_spline(inp)
    v12_dens = v12_data[v12_data['input'] == inp]['negative_density'].values[0]
    diff = density - v12_dens
    print(f"  Input {inp:>3}: {density:.4f} (v12: {v12_dens:.4f}, 差: {diff:+.4f}) {status}")

# v11のBaseline関係式（v14と同じ）
v11_data = {
    'input': [160, 255],
    'baseline': [155.2, 210.7],
    'density': [1.24, 1.65]
}

slope = (v11_data['density'][1] - v11_data['density'][0]) / (v11_data['baseline'][1] - v11_data['baseline'][0])
intercept = v11_data['density'][0] - slope * v11_data['baseline'][0]

print(f"\n=== Baseline計算式 ===")
print(f"Density = {slope:.6f} * Baseline + {intercept:.4f}")

# カーブデータ生成（全256ポイント）
remapped_curve_8bit = []
remapped_curve_16bit = []

for input_val in range(256):
    # 優先順位:
    # 1. v14の補間値（Input 48-104、8刻み以外も含む）
    # 2. v17の補間値（Input 112-192、8刻み以外も含む）
    # 3. v12の実測値（その他の8刻み点）
    # 4. 線形補間（上記以外）

    if 48 <= input_val <= 104:
        # v14範囲はすべてv14スプラインを使用
        if input_val % 8 == 0:
            # 8刻み点はスプライン補間値
            target_density = v14_spline(input_val)
        else:
            # 8刻み以外も線形補間ではなく、前後の8刻み点から線形補間
            lower = (input_val // 8) * 8
            upper = lower + 8
            lower_density = v14_spline(lower)
            upper_density = v14_spline(upper)
            ratio = (input_val - lower) / 8
            target_density = lower_density + ratio * (upper_density - lower_density)

    elif 112 <= input_val <= 192:
        # v17範囲はすべてv17スプラインを使用
        if input_val in [112, 120, 128, 136, 144, 152, 160, 168, 176, 184, 192]:
            # 8刻み点はスプライン補間値
            target_density = v17_spline(input_val)
        else:
            # 8刻み以外も線形補間
            lower = (input_val // 8) * 8
            upper = lower + 8
            # v17範囲内なので両方v17スプライン
            lower_density = v17_spline(lower)
            upper_density = v17_spline(upper)
            ratio = (input_val - lower) / 8
            target_density = lower_density + ratio * (upper_density - lower_density)

    elif input_val % 8 == 0:
        # その他の8刻み点はv12実測値
        target_density = v12_data[v12_data['input'] == input_val]['negative_density'].values[0]

    else:
        # その他は線形補間
        lower = (input_val // 8) * 8
        upper = lower + 8
        upper = min(upper, 255)

        # lowerの濃度取得
        if 48 <= lower <= 104:
            lower_density = v14_spline(lower)
        elif 112 <= lower <= 192:
            lower_density = v17_spline(lower)
        else:
            lower_row = v12_data[v12_data['input'] == lower]
            if len(lower_row) > 0:
                lower_density = lower_row['negative_density'].values[0]
            else:
                lower_density = v12_data[v12_data['input'] <= lower].iloc[-1]['negative_density']

        # upperの濃度取得
        if 48 <= upper <= 104:
            upper_density = v14_spline(upper)
        elif 112 <= upper <= 192:
            upper_density = v17_spline(upper)
        else:
            upper_row = v12_data[v12_data['input'] == upper]
            if len(upper_row) > 0:
                upper_density = upper_row['negative_density'].values[0]
            else:
                upper_density = v12_data[v12_data['input'] >= upper].iloc[0]['negative_density']

        ratio = (input_val - lower) / (upper - lower)
        target_density = lower_density + ratio * (upper_density - lower_density)

    # Baselineを計算（v14と同じ方法）
    baseline_input = (target_density - intercept) / slope
    baseline_input = np.clip(baseline_input, 0, 255)

    remapped_curve_8bit.append(baseline_input)
    # v14/v17 FIXEDと同じ計算式（baseline * 257）
    remapped_curve_16bit.append(int(round(baseline_input * 257)))

# 検証
print("\n=== v18 主要ポイント検証 ===")
print(f"{'Input':<6} {'Baseline':<10} {'Quad値':<10} {'範囲':<15}")
print("-" * 50)
for inp in [0, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 136, 144, 192, 200, 255]:
    range_info = ""
    if 48 <= inp <= 104:
        range_info = "v14範囲"
    elif 112 <= inp <= 192:
        range_info = "v17範囲"
    else:
        range_info = "v12実測"
    print(f"{inp:<6} {remapped_curve_8bit[inp]:<10.2f} {remapped_curve_16bit[inp]:<10} {range_info:<15}")

print(f"\nInput 255検証:")
target_255 = v12_data[v12_data['input'] == 255]['negative_density'].values[0]
baseline_255 = (target_255 - intercept) / slope
print(f"  目標濃度: {target_255:.4f}")
print(f"  Baseline: {baseline_255:.2f}")
print(f"  Quad値: {remapped_curve_16bit[255]}")

# グラデーション検証
print("\n=== v18 グラデーション検証 ===")
print(f"{'Input範囲':<12} {'濃度範囲':<20} {'勾配':<10} {'状態':<15}")
print("-" * 70)

# 濃度を計算
densities = []
for baseline in remapped_curve_8bit:
    density = baseline * slope + intercept
    densities.append(density)

for i in range(0, 248, 8):
    dens_start = densities[i]
    dens_end = densities[i+8]
    gradient = (dens_end - dens_start) / 8

    if gradient > 0.006:
        status = "🎯 要注意"
    elif gradient > 0.005:
        status = "やや急"
    else:
        status = "✓ 滑らか"

    range_info = ""
    if 48 <= i <= 104:
        range_info = "[v14]"
    elif 112 <= i <= 192:
        range_info = "[v17]"

    print(f"{i:>3}→{i+8:<3}    {dens_start:.4f}→{dens_end:.4f}    {gradient:<10.6f} {status:<10} {range_info}")

# .quadファイル生成
quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# PX1V-PtPd-Linear v18 - Best of v14 + v17
# v14 range (Input 48-104) + v17 range (Input 112-192)
# Target: Complete gradient optimization across all ranges
# BOOST_K=0 - NO BOOST
# K curve
"""

for val in remapped_curve_16bit:
    quad_content += f"{val}\n"

# 他のインクカーブ（すべて0）
for ink_name in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
    quad_content += f"# {ink_name} curve\n"
    for _ in range(256):
        quad_content += "0\n"

quad_path = '/tmp/PX1V-PtPd-Linear-v18.quad'
with open(quad_path, 'w') as f:
    f.write(quad_content)

print(f"\n✓ v18 .quadファイル生成完了")
print(f"  保存先: {quad_path}")
print("\nv18の特徴:")
print("  - Input 48-104: v14のスプライン補間（境界線解消済み）")
print("  - Input 112-192: v17のスプライン補間（新規改善範囲）")
print("  - 濃度0.25-0.47範囲: v14の最良結果を使用")
print("  - 濃度0.55-0.93範囲: v17の改善を適用")
print("  - 計算式: baseline * 257（v14/v17 FIXEDと統一）")
