#!/usr/bin/env python3
"""
PX1V-PtPd-v23: ハイライト強化版（修正版）

v22をベースに、ハイライト範囲を拡大:
- Input 0-247: v22のQuad値をそのまま使用（変更なし）
- Input 248: v22のInput 255のQuad値を使用（実測1.23D想定）
- Input 255: v20のInput 248のQuad値を使用（実測1.27D想定）
- Input 249-254: Input 248と255の間を線形補間
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ========== 基本定数 ==========
SLOPE = 0.007387
INTERCEPT = 0.0935

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

def generate_v23_correct():
    """v23カーブを生成 - ハイライト強化版（修正版）"""
    print("=" * 80)
    print("PX1V-PtPd-v23: ハイライト強化版（修正版）")
    print("=" * 80)

    # v22のQuad値を読み込み（ベース）
    v22_quad_values = read_quad_file('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/QTRカーブ_バックアップ_最終版/参照ファイル/PX1V-PtPd-v22.quad')
    print(f"\n✓ v22のQuad値を読み込み: {len(v22_quad_values)}ポイント")

    # v20のQuad値を読み込み
    v20_quad_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/QTRカーブ_アーカイブ_旧バージョン/PX1V-PtPd-v20.quad'
    v20_quad_values = read_quad_file(v20_quad_path)
    print(f"✓ v20のQuad値を読み込み: {len(v20_quad_values)}ポイント")

    # 測定データを読み込み
    v22_measured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/measurement_QTR2-22.csv')
    v20_measured = pd.read_csv('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/measurement_QTR2-20.csv')

    print("\n戦略（修正版）:")
    print("  ✓ Input 0-247: v22のQuad値をそのまま使用（変更なし）")
    print("  ✓ Input 248: v22のInput 255のQuad値を使用（実測1.23D想定）")
    print("  ✓ Input 255: v20のInput 248のQuad値を使用（実測1.27D想定）")
    print("  ✓ Input 249-254: 線形補間のみ")

    # v23のQuad値を構築（v22を完全コピー）
    v23_quad_values = np.copy(v22_quad_values)

    # Input 248: v22のInput 255のQuad値
    v22_255_quad = v22_quad_values[255]
    v23_quad_values[248] = v22_255_quad

    # Input 255: v20のInput 248のQuad値
    v20_248_quad = v20_quad_values[248]
    v23_quad_values[255] = v20_248_quad

    print("\nQuad値の設定:")
    print(f"  Input 248: Quad={v22_255_quad} (v22 Input255)")
    print(f"  Input 255: Quad={v20_248_quad} (v20 Input248)")

    # 実測値の予想
    v22_255_measured = v22_measured[v22_measured['input'] == 255]['negative_density'].values[0]
    v20_248_measured = v20_measured[v20_measured['input'] == 248]['negative_density'].values[0]

    print("\n予想実測値:")
    print(f"  Input 248: 約{v22_255_measured:.2f}D想定（v22 Input255実測）")
    print(f"  Input 255: 約{v20_248_measured:.2f}D想定（v20 Input248実測）")

    # アンカーポイント（Input 248, 255）のみ
    # Input 247までv22をそのまま使用、Input 248-255のみ補間
    anchor_inputs = [248, 255]
    anchor_quads = [v23_quad_values[248], v23_quad_values[255]]

    # 線形補間（Input 249-254のみ）
    print("\n線形補間（Input 249-254のみ）:")
    start_input = anchor_inputs[0]
    end_input = anchor_inputs[1]
    start_quad = anchor_quads[0]
    end_quad = anchor_quads[1]

    for inp in range(start_input + 1, end_input):
        ratio = (inp - start_input) / (end_input - start_input)
        interpolated_quad = int(round(start_quad + ratio * (end_quad - start_quad)))
        v23_quad_values[inp] = interpolated_quad

    num_points = end_input - start_input - 1
    avg_diff = (end_quad - start_quad) / (end_input - start_input)
    status = "✓" if avg_diff < 200 else "⚠️"
    print(f"  {status} Input {start_input}→{end_input}: {num_points}点補間（平均Quad勾配: {avg_diff:.1f}）")

    # 単調性チェック
    corrections = 0
    for i in range(1, len(v23_quad_values)):
        if v23_quad_values[i] < v23_quad_values[i-1]:
            v23_quad_values[i] = v23_quad_values[i-1]
            corrections += 1

    if corrections > 0:
        print(f"\n⚠️  単調性補正: {corrections}ポイント")
    else:
        print(f"\n✓ 単調性チェック: OK")

    # 境界線リスク解析
    quad_diffs = np.diff(v23_quad_values)
    max_diff = np.max(quad_diffs)
    max_diff_input = np.argmax(quad_diffs)

    print(f"\n境界線リスク解析:")
    print(f"  最大Quad差分: {max_diff:.1f} (Input {max_diff_input})")

    # ハイライト域のQuad差分
    print("\nハイライト域のQuad差分（Input 240-255）:")
    for i in range(240, 255):
        diff = quad_diffs[i]
        status = "✓" if diff < 200 else "⚠️"
        if i in [240, 247, 248, 254]:
            print(f"  {status} Input {i:3d}→{i+1:3d}: {diff:.1f}")

    # 最大Quad差分の位置を確認
    if max_diff_input >= 247:
        print(f"\n⚠️  注意: 最大Quad差分がハイライト域 (Input {max_diff_input})")

    # 濃度の逆算
    baselines = v23_quad_values / 257.0
    densities = baselines * SLOPE + INTERCEPT

    print("\nv23予想濃度（逆算）:")
    for inp in [232, 240, 247, 248, 255]:
        predicted_density = densities[inp]
        if inp in v22_measured['input'].values:
            v22_val = v22_measured[v22_measured['input'] == inp]['negative_density'].values[0]
            diff = predicted_density - v22_val
            print(f"  Input {inp}: {predicted_density:.4f}D (v22: {v22_val:.2f}D, 差: {diff:+.3f}D)")
        else:
            print(f"  Input {inp}: {predicted_density:.4f}D")

    # ハイライト範囲
    highlight_range_240_255 = densities[255] - densities[240]
    highlight_range_248_255 = densities[255] - densities[248]
    v22_range_240_255 = v22_measured[v22_measured['input'] == 255]['negative_density'].values[0] - v22_measured[v22_measured['input'] == 240]['negative_density'].values[0]

    print(f"\nハイライト範囲:")
    print(f"  v23 (240-255): {highlight_range_240_255:.4f}D")
    print(f"  v23 (248-255): {highlight_range_248_255:.4f}D")
    print(f"  v22 (240-255): {v22_range_240_255:.3f}D")

    # v22との比較
    print("\nv22からの変更点:")
    changes = 0
    for i in range(256):
        if v23_quad_values[i] != v22_quad_values[i]:
            changes += 1
            if i >= 247:
                print(f"  Input {i}: {v22_quad_values[i]} → {v23_quad_values[i]} (差: {v23_quad_values[i] - v22_quad_values[i]:+d})")

    print(f"\n変更されたポイント数: {changes}/256")

    # .quadファイル書き出し
    output_quad = 'PX1V-PtPd-v23.quad'
    with open(output_quad, 'w') as f:
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        f.write('# QuadProfile Version 2.8.0\n')
        f.write('# PX1V-PtPd-v23 - Highlight Boost (CORRECTED)\n')
        f.write('# Input 0-247: v22 Quad values (UNCHANGED)\n')
        f.write('# Input 248: v22 Input 255 Quad (measured 1.23D)\n')
        f.write('# Input 255: v20 Input 248 Quad (measured 1.27D)\n')
        f.write('# Input 249-254: Linear interpolation\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')

        # Kチャンネル（Photo Black）
        f.write('# K curve\n')
        for qv in v23_quad_values:
            f.write(f'{int(qv)}\n')

        # 残り9チャンネル（全て0 = 使用しない）
        for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
            f.write(f'# {channel} curve\n')
            for _ in range(256):
                f.write('0\n')

    print(f"\n✓ .quadファイル生成: {output_quad}")

    # .txtファイル
    output_txt = 'PX1V-PtPd-v23.txt'
    input_values = np.arange(256)
    df = pd.DataFrame({
        'Input': input_values,
        'Quad_Value': v23_quad_values,
        'Baseline': baselines,
        'Predicted_Density': densities
    })
    df.to_csv(output_txt, index=False, float_format='%.6f')
    print(f"✓ 詳細データ: {output_txt}")

    # グラフ作成
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1. 全範囲濃度カーブ
    axes[0, 0].plot(input_values, densities, 'b-', linewidth=2, label='v23 (predicted)')

    # v22実測値
    v22_inputs = v22_measured['input'].values
    v22_densities = v22_measured['negative_density'].values
    axes[0, 0].plot(v22_inputs, v22_densities, 'g--', linewidth=1.5,
                    marker='s', markersize=4, label='v22 measured', alpha=0.7)

    # v23特別ポイント
    axes[0, 0].scatter([248, 255], [densities[248], densities[255]],
                       c='red', s=200, zorder=6, marker='*',
                       label='v23 boost points', edgecolors='black', linewidths=2)

    axes[0, 0].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White (1.25D)')
    axes[0, 0].set_xlabel('Input Value', fontsize=12)
    axes[0, 0].set_ylabel('Negative Density', fontsize=12)
    axes[0, 0].set_title('v23: Highlight Boost (248, 255) - CORRECTED',
                         fontsize=14, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 2. ハイライト域拡大
    highlight_mask = input_values >= 224
    axes[0, 1].plot(input_values[highlight_mask], densities[highlight_mask],
                    'b-', linewidth=3, label='v23 (predicted)')

    # v22実測値
    v22_highlight_mask = v22_inputs >= 224
    axes[0, 1].plot(v22_inputs[v22_highlight_mask],
                    v22_densities[v22_highlight_mask],
                    'g--', linewidth=2, marker='s', markersize=6,
                    label='v22 measured', alpha=0.7)

    # v23特別ポイント
    axes[0, 1].scatter([248, 255], [densities[248], densities[255]],
                       c='red', s=250, zorder=6, marker='*',
                       label='v23 boost', edgecolors='black', linewidths=2)

    axes[0, 1].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White')
    axes[0, 1].set_xlabel('Input Value', fontsize=12)
    axes[0, 1].set_ylabel('Negative Density', fontsize=12)
    axes[0, 1].set_title('v23: Extended Highlight Range - CORRECTED',
                         fontsize=14, fontweight='bold')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_xlim(224, 256)
    axes[0, 1].set_ylim(1.10, 1.35)

    # 3. 全範囲Quad差分
    axes[1, 0].plot(input_values[:-1], quad_diffs, 'g-', linewidth=1.5)
    axes[1, 0].axhline(y=200, color='red', linestyle='--', linewidth=2,
                       label='Boundary Risk (200)')
    axes[1, 0].set_xlabel('Input Value', fontsize=12)
    axes[1, 0].set_ylabel('Quad Difference', fontsize=12)
    axes[1, 0].set_title('v23: Boundary Line Risk Analysis - CORRECTED',
                         fontsize=14, fontweight='bold')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_ylim(-10, min(max_diff + 20, 250))

    # 4. ハイライトQuad差分
    highlight_diff_mask = input_values[:-1] >= 224
    axes[1, 1].plot(input_values[:-1][highlight_diff_mask],
                    quad_diffs[highlight_diff_mask],
                    'g-', linewidth=3, marker='o', markersize=4)
    axes[1, 1].axhline(y=200, color='red', linestyle='--', linewidth=2,
                       label='Threshold')
    axes[1, 1].set_xlabel('Input Value', fontsize=12)
    axes[1, 1].set_ylabel('Quad Difference', fontsize=12)
    axes[1, 1].set_title('v23: Highlight Quad Differences (224-255) - CORRECTED',
                         fontsize=14, fontweight='bold')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_xlim(224, 256)
    axes[1, 1].set_ylim(-10, max(250, max_diff + 20))

    plt.tight_layout()
    plt.savefig('v23_correct_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✓ グラフ保存: v23_correct_analysis.png")

    print("\n次のステップ:")
    print(f"  1. sudo cp {output_quad} /Library/Printers/QTR/quadtone/QuadP700/")
    print(f"  2. /Library/Printers/QTR/bin/quadcurves QuadP700")
    print(f"  3. QTR Print-Toolで v23 を選択してテストプリント")
    print(f"  4. 濃度測定で実測値を確認")

    return v23_quad_values, densities

if __name__ == '__main__':
    quad_values, densities = generate_v23_correct()

    print("\n" + "=" * 80)
    print("v23 カーブ生成完了 - ハイライト強化版（修正版）")
    print("Input 0-247: v22と同一（変更なし）")
    print("Input 248: v22のInput 255のQuad値（実測1.23D想定）")
    print("Input 255: v20のInput 248のQuad値（実測1.27D想定）")
    print("Input 249-254: 線形補間")
    print("=" * 80)
