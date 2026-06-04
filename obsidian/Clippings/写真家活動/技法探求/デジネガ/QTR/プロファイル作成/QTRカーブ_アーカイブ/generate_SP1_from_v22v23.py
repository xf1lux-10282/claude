#!/usr/bin/env python3
"""
PX1V-PtPd-SP1カーブ生成（v22/v23ベース）

measurement_QTR-SP-1.csvのターゲット濃度に対して、
v22/v23の既存Quad値から最も近い濃度を持つQuad値を選択してカーブを生成
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 基本定数
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

def quad_to_density(quad_value):
    """Quad値から濃度を計算"""
    baseline = quad_value / 257.0
    density = baseline * SLOPE + INTERCEPT
    return density

def find_closest_quad_in_range(target_density, reference_quads, reference_densities,
                                 search_start, search_end):
    """指定範囲内でターゲット濃度に最も近いQuad値を見つける"""
    search_densities = reference_densities[search_start:search_end+1]
    search_quads = reference_quads[search_start:search_end+1]

    if len(search_densities) == 0:
        return None, None

    # 最も近い濃度を見つける
    idx = np.argmin(np.abs(search_densities - target_density))
    return search_quads[idx], search_start + idx

def generate_sp1_from_references():
    """v22/v23からSP-1カーブを生成"""
    print("=" * 80)
    print("PX1V-PtPd-SP1: v22/v23の既存Quad値から生成")
    print("=" * 80)

    # v22とv23を読み込み
    v22_quads = read_quad_file('/Users/daisukekinoshita/Desktop/PX1V-PtPd-v22.quad')
    v23_quads = read_quad_file('/Users/daisukekinoshita/Desktop/PX1V-PtPd-v23.quad')

    # 濃度を計算
    v22_densities = np.array([quad_to_density(q) for q in v22_quads])
    v23_densities = np.array([quad_to_density(q) for q in v23_quads])

    # 全範囲のQuad値と濃度（v22とv23を統合）
    all_quads = np.concatenate([v22_quads, v23_quads])
    all_densities = np.concatenate([v22_densities, v23_densities])
    all_inputs = np.concatenate([np.arange(256), np.arange(256)])

    print("\n参照データ:")
    print(f"  v22: 濃度範囲 {v22_densities.min():.3f}D - {v22_densities.max():.3f}D")
    print(f"  v23: 濃度範囲 {v23_densities.min():.3f}D - {v23_densities.max():.3f}D")

    # ターゲット濃度（SP-1）を読み込み
    sp1_target = pd.read_csv('/Users/daisukekinoshita/Desktop/measurement_QTR-SP-1.csv')

    print(f"\nターゲット濃度（SP-1）:")
    print(f"  ポイント数: {len(sp1_target)}")
    print(f"  濃度範囲: {sp1_target['negative_density'].min():.3f}D - {sp1_target['negative_density'].max():.3f}D")

    # SP-1カーブのQuad値を作成
    sp1_quads = np.zeros(256, dtype=int)
    sp1_selected_from = []  # どこから選んだか記録

    print("\nQuad値の選択:")
    print("Input  Target_D  Selected_Quad  From      Actual_D  Error")
    print("=" * 70)

    for _, row in sp1_target.iterrows():
        input_val = int(row['input'])
        target_d = row['negative_density']

        # ターゲット濃度に最も近いQuad値を探す
        # v22とv23の両方から探索
        diff_v22 = np.abs(v22_densities - target_d)
        diff_v23 = np.abs(v23_densities - target_d)

        min_idx_v22 = np.argmin(diff_v22)
        min_idx_v23 = np.argmin(diff_v23)

        if diff_v22[min_idx_v22] < diff_v23[min_idx_v23]:
            # v22の方が近い
            selected_quad = v22_quads[min_idx_v22]
            selected_density = v22_densities[min_idx_v22]
            source = f"v22[{min_idx_v22}]"
        else:
            # v23の方が近い
            selected_quad = v23_quads[min_idx_v23]
            selected_density = v23_densities[min_idx_v23]
            source = f"v23[{min_idx_v23}]"

        sp1_quads[input_val] = selected_quad
        sp1_selected_from.append({
            'input': input_val,
            'target_d': target_d,
            'selected_quad': selected_quad,
            'source': source,
            'actual_d': selected_density,
            'error': selected_density - target_d
        })

        error_str = f"{selected_density - target_d:+.3f}D"
        print(f"{input_val:3d}    {target_d:.3f}D   {selected_quad:5d}      {source:10}  {selected_density:.3f}D  {error_str}")

    # 測定ポイント間を線形補間
    print("\n測定ポイント間を線形補間:")
    measured_inputs = sp1_target['input'].values

    for i in range(len(measured_inputs) - 1):
        start_input = measured_inputs[i]
        end_input = measured_inputs[i + 1]
        start_quad = sp1_quads[start_input]
        end_quad = sp1_quads[end_input]

        # 間のポイントを補間
        for inp in range(start_input + 1, end_input):
            ratio = (inp - start_input) / (end_input - start_input)
            sp1_quads[inp] = int(round(start_quad + ratio * (end_quad - start_quad)))

        num_interpolated = end_input - start_input - 1
        if num_interpolated > 0:
            print(f"  Input {start_input}→{end_input}: {num_interpolated}点補間")

    # 単調性を保証
    corrections = 0
    for i in range(1, 256):
        if sp1_quads[i] < sp1_quads[i-1]:
            sp1_quads[i] = sp1_quads[i-1]
            corrections += 1

    if corrections > 0:
        print(f"\n⚠️  単調性補正: {corrections}ポイント")
    else:
        print(f"\n✓ 単調性チェック: OK")

    # 境界線リスク解析
    quad_diffs = np.diff(sp1_quads)
    max_diff = np.max(quad_diffs)
    max_diff_input = np.argmax(quad_diffs)

    print(f"\n境界線リスク解析:")
    print(f"  最大Quad差分: {max_diff:.0f} (Input {max_diff_input}→{max_diff_input+1})")

    if max_diff > 200:
        print(f"  ⚠️  境界線リスクあり")
        risky = np.where(quad_diffs > 200)[0]
        if len(risky) <= 10:
            for idx in risky:
                print(f"     Input {idx}→{idx+1}: {quad_diffs[idx]:.0f}")
    else:
        print(f"  ✓ 境界線リスクなし")

    # 実際の濃度を計算
    sp1_densities = np.array([quad_to_density(q) for q in sp1_quads])

    # 紙白制約チェック
    max_density = sp1_densities[255]
    print(f"\n紙白制約チェック:")
    print(f"  Input 255: {max_density:.3f}D")
    if max_density <= 1.25:
        print(f"  ✓ 制約内（≤ 1.25D）")
    else:
        print(f"  ⚠️  制約超過（> 1.25D、超過: {max_density - 1.25:+.3f}D）")

    # .quadファイル書き出し
    output_quad = 'PX1V-PtPd-SP1.quad'
    with open(output_quad, 'w') as f:
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        f.write('# QuadProfile Version 2.8.0\n')
        f.write('# PX1V-PtPd-SP1 - Generated from v22/v23 reference curves\n')
        f.write('# Target density from BK+GY printer measurements\n')
        f.write('# Created: 2026-03-17\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')

        # Kチャンネル
        f.write('# K curve\n')
        for qv in sp1_quads:
            f.write(f'{int(qv)}\n')

        # 残り9チャンネル
        for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
            f.write(f'# {channel} curve\n')
            for _ in range(256):
                f.write('0\n')

    print(f"\n✓ .quadファイル生成: {output_quad}")

    # .txtファイル
    output_txt = 'PX1V-PtPd-SP1.txt'
    all_inputs = np.arange(256)
    df = pd.DataFrame({
        'Input': all_inputs,
        'Quad_Value': sp1_quads,
        'Baseline': sp1_quads / 257.0,
        'Density': sp1_densities
    })
    df.to_csv(output_txt, index=False, float_format='%.6f')
    print(f"✓ 詳細データ: {output_txt}")

    # グラフ作成
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1. 濃度カーブ比較
    axes[0, 0].plot(all_inputs, sp1_densities, 'b-', linewidth=2, label='SP-1 (generated)')
    axes[0, 0].plot(all_inputs, v22_densities, 'g--', linewidth=1.5, alpha=0.7, label='v22 reference')
    axes[0, 0].plot(all_inputs, v23_densities, 'r--', linewidth=1.5, alpha=0.7, label='v23 reference')
    axes[0, 0].scatter(sp1_target['input'], sp1_target['negative_density'],
                       c='red', s=100, zorder=5, marker='o',
                       label='SP-1 target', edgecolors='black', linewidths=1)
    axes[0, 0].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White (1.25D)')
    axes[0, 0].set_xlabel('Input Value', fontsize=12)
    axes[0, 0].set_ylabel('Negative Density', fontsize=12)
    axes[0, 0].set_title('SP-1: Generated from v22/v23 Quad Values',
                         fontsize=14, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 2. ターゲットとの誤差
    errors = []
    for item in sp1_selected_from:
        errors.append(item['error'])

    axes[0, 1].bar(sp1_target['input'], errors, width=6, color='blue', alpha=0.7)
    axes[0, 1].axhline(y=0, color='black', linestyle='-', linewidth=1)
    axes[0, 1].axhline(y=0.01, color='green', linestyle='--', linewidth=1, alpha=0.5, label='±0.01D')
    axes[0, 1].axhline(y=-0.01, color='green', linestyle='--', linewidth=1, alpha=0.5)
    axes[0, 1].set_xlabel('Input Value', fontsize=12)
    axes[0, 1].set_ylabel('Error (Generated - Target)', fontsize=12)
    axes[0, 1].set_title('SP-1: Density Error from Target',
                         fontsize=14, fontweight='bold')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

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

    # 4. ハイライト域詳細
    highlight_mask = all_inputs >= 200
    axes[1, 1].plot(all_inputs[highlight_mask], sp1_densities[highlight_mask],
                    'b-', linewidth=3, label='SP-1')
    axes[1, 1].scatter(sp1_target[sp1_target['input'] >= 200]['input'],
                       sp1_target[sp1_target['input'] >= 200]['negative_density'],
                       c='red', s=150, zorder=5, marker='o',
                       label='Target', edgecolors='black', linewidths=2)
    axes[1, 1].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White')
    axes[1, 1].set_xlabel('Input Value', fontsize=12)
    axes[1, 1].set_ylabel('Negative Density', fontsize=12)
    axes[1, 1].set_title('SP-1: Highlight Region Detail (200-255)',
                         fontsize=14, fontweight='bold')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_xlim(200, 256)

    plt.tight_layout()
    plt.savefig('SP1_from_v22v23_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✓ グラフ保存: SP1_from_v22v23_analysis.png")

    # 誤差統計
    errors_array = np.array(errors)
    print("\n誤差統計:")
    print(f"  平均誤差: {np.mean(errors_array):.4f}D")
    print(f"  最大誤差: {np.max(np.abs(errors_array)):.4f}D")
    print(f"  RMS誤差: {np.sqrt(np.mean(errors_array**2)):.4f}D")

    print("\n次のステップ:")
    print(f"  1. cp /Users/daisukekinoshita/Desktop/{output_quad} /tmp/")
    print(f"  2. xattr -c /tmp/{output_quad}")
    print(f"  3. osascript -e 'do shell script \"cp /tmp/{output_quad} /Library/Printers/QTR/quadtone/QuadP700/\" with administrator privileges'")
    print(f"  4. /Library/Printers/QTR/bin/quadcurves QuadP700")

    return sp1_quads, sp1_densities

if __name__ == '__main__':
    quad_values, densities = generate_sp1_from_references()

    print("\n" + "=" * 80)
    print("SP-1 カーブ生成完了")
    print("v22/v23の既存Quad値からターゲット濃度に最も近い値を選択")
    print("BK+GYプリンターの良好な結果をPhoto Blackで再現")
    print("=" * 80)
