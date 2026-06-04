#!/usr/bin/env python3
"""
PX1V-PtPd-SP1v4: measurement_QTR-SP-1.csvに最も近いカーブ（シンプル版）

戦略：
- Input 248: v23のInput 248を使用（実測1.23D）
- Input 255: v21のInput 255を使用（実測1.34D）
- その他: v21/v22/v23から最適なものを選択
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# 基本定数
SLOPE = 0.007387
INTERCEPT = 0.0935

def quad_to_density(quad_value):
    """Quad値から濃度を計算"""
    baseline = quad_value / 257.0
    return baseline * SLOPE + INTERCEPT

def read_quad_file(filepath):
    """QUADファイルを読み込んでKチャンネルのQuad値配列を返す"""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    k_start = None
    for i, line in enumerate(lines):
        if '# K curve' in line:
            k_start = i + 1
            break

    if k_start is None:
        raise ValueError("K curve not found")

    quad_values = []
    for i in range(k_start, k_start + 256):
        quad_values.append(int(lines[i].strip()))

    return np.array(quad_values)

def generate_sp1v4():
    """SP-1v4を生成"""
    print("=" * 80)
    print("PX1V-PtPd-SP1v4: measurement_QTR-SP-1.csvに最も近いカーブ（シンプル版）")
    print("Input 248: v23のInput 248（実測1.23D）")
    print("Input 255: v21のInput 255（実測1.34D）")
    print("=" * 80)

    # 目標濃度を読み込み
    target = pd.read_csv('/Users/daisukekinoshita/Desktop/measurement_QTR-SP-1.csv')
    print(f"\n目標データ: {len(target)}ポイント")
    print(f"  濃度範囲: {target['negative_density'].min():.2f}D - {target['negative_density'].max():.2f}D")

    # v21, v22, v23のQuad値を読み込み
    v21_quads = read_quad_file('/Users/daisukekinoshita/Desktop/PX1V-PtPd-v21.quad')
    v22_quads = read_quad_file('/Users/daisukekinoshita/Desktop/PX1V-PtPd-v22.quad')
    v23_quads = read_quad_file('/Users/daisukekinoshita/Desktop/PX1V-PtPd-v23.quad')

    # 各バージョンの濃度を計算
    v21_densities = np.array([quad_to_density(q) for q in v21_quads])
    v22_densities = np.array([quad_to_density(q) for q in v22_quads])
    v23_densities = np.array([quad_to_density(q) for q in v23_quads])

    print("\n重要なQuad値（実測値ベース）:")
    print(f"  v23 Input 248: Quad={v23_quads[248]}, 計算={v23_densities[248]:.2f}D, 実測=1.23D")
    print(f"  v21 Input 255: Quad={v21_quads[255]}, 計算={v21_densities[255]:.2f}D, 実測=1.34D")

    # SP-1v4のQuad値配列を初期化
    sp1v4_quads = np.zeros(256, dtype=int)
    selection_log = []

    # 各測定ポイントに対して最適なQuad値を選択
    print("\n各地点の最適Quad値選択:")
    print("Input  目標濃度  選択  ソース       Quad値  計算濃度  差分")
    print("=" * 80)

    for _, row in target.iterrows():
        input_val = int(row['input'])
        target_d = row['negative_density']

        # 特別ルール: Input 248とInput 255
        if input_val == 248:
            # v23のInput 248を使用（実測1.23D）
            selected_quad = v23_quads[248]
            selected_density = v23_densities[248]
            version = 'v23'
            source_idx = 248
            print(f"{input_val:3d}    {target_d:.2f}D     {version}  Input {source_idx:3d}  {selected_quad:5d}   {selected_density:.2f}D    {selected_density - target_d:+.3f}D  ※実測1.23D")

        elif input_val == 255:
            # v21のInput 255を使用（実測1.34D）
            selected_quad = v21_quads[255]
            selected_density = v21_densities[255]
            version = 'v21'
            source_idx = 255
            print(f"{input_val:3d}    {target_d:.2f}D     {version}  Input {source_idx:3d}  {selected_quad:5d}   {selected_density:.2f}D    {selected_density - target_d:+.3f}D  ※実測1.34D")

        else:
            # その他: 最も近い濃度を持つバージョンから選択
            diff_v21 = np.abs(v21_densities - target_d)
            diff_v22 = np.abs(v22_densities - target_d)
            diff_v23 = np.abs(v23_densities - target_d)

            min_idx_v21 = np.argmin(diff_v21)
            min_idx_v22 = np.argmin(diff_v22)
            min_idx_v23 = np.argmin(diff_v23)

            candidates = [
                (diff_v21[min_idx_v21], 'v21', min_idx_v21, v21_quads[min_idx_v21], v21_densities[min_idx_v21]),
                (diff_v22[min_idx_v22], 'v22', min_idx_v22, v22_quads[min_idx_v22], v22_densities[min_idx_v22]),
                (diff_v23[min_idx_v23], 'v23', min_idx_v23, v23_quads[min_idx_v23], v23_densities[min_idx_v23])
            ]

            best = min(candidates, key=lambda x: x[0])
            min_diff, version, source_idx, selected_quad, selected_density = best

            print(f"{input_val:3d}    {target_d:.2f}D     {version}  Input {source_idx:3d}  {selected_quad:5d}   {selected_density:.2f}D    {selected_density - target_d:+.3f}D")

        sp1v4_quads[input_val] = selected_quad

        selection_log.append({
            'input': input_val,
            'target_density': target_d,
            'selected_quad': selected_quad,
            'selected_density': selected_density,
            'version': version,
            'source_input': source_idx,
            'error': selected_density - target_d
        })

    # 測定点間を線形補間
    measured_inputs = target['input'].values
    measured_quads = np.array([sp1v4_quads[i] for i in measured_inputs])

    interp_func = interp1d(measured_inputs, measured_quads,
                           kind='linear', fill_value='extrapolate')

    for i in range(256):
        if i not in measured_inputs:
            interp_value = float(interp_func(i))
            sp1v4_quads[i] = int(round(interp_value))

    # 単調性を保証
    for i in range(1, 256):
        if sp1v4_quads[i] < sp1v4_quads[i-1]:
            sp1v4_quads[i] = sp1v4_quads[i-1]

    # 統計
    errors = [log['error'] for log in selection_log]
    print(f"\n精度統計:")
    print(f"  平均誤差: {np.mean(errors):+.4f}D")
    print(f"  RMS誤差: {np.sqrt(np.mean(np.array(errors)**2)):.4f}D")
    print(f"  最大誤差: {np.max(np.abs(errors)):.4f}D")

    # Input 248とInput 255の実測との比較
    print(f"\n重要ポイントの実測との比較:")
    print(f"  Input 248: 目標1.23D, 計算{quad_to_density(sp1v4_quads[248]):.2f}D, 実測1.23D ✓")
    print(f"  Input 255: 目標1.35D, 計算{quad_to_density(sp1v4_quads[255]):.2f}D, 実測1.34D (誤差-0.01D)")

    # バージョン選択の内訳
    version_counts = {}
    for log in selection_log:
        v = log['version']
        version_counts[v] = version_counts.get(v, 0) + 1

    print(f"\nバージョン選択内訳:")
    for v in ['v21', 'v22', 'v23']:
        count = version_counts.get(v, 0)
        print(f"  {v}: {count}ポイント ({count/len(selection_log)*100:.1f}%)")

    # 濃度を計算
    sp1v4_densities = np.array([quad_to_density(q) for q in sp1v4_quads])

    # 境界線リスク
    quad_diffs = np.diff(sp1v4_quads)
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

    # 紙白制約チェック
    max_density = sp1v4_densities[255]
    print(f"\n紙白制約チェック:")
    print(f"  Input 255: {max_density:.2f}D（計算値）、1.34D（実測値）")
    if max_density > 1.25:
        print(f"  ⚠️  計算値は制約超過: {max_density - 1.25:+.2f}D")
        print(f"  ⚠️  実測値も制約超過: {1.34 - 1.25:+.2f}D")
    else:
        print(f"  ✓ 制約内")

    # .quadファイル書き出し
    output_quad = 'PX1V-PtPd-SP1v4.quad'
    with open(output_quad, 'w') as f:
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        f.write('# QuadProfile Version 2.8.0\n')
        f.write('# PX1V-PtPd-SP1v4 - Best match to measurement_QTR-SP-1.csv (simple)\n')
        f.write('# Input 248: v23[248] (measured 1.23D)\n')
        f.write('# Input 255: v21[255] (measured 1.34D)\n')
        f.write('# Others: Selected from v21/v22/v23 for optimal density match\n')
        f.write('# Created: 2026-03-17\n')
        f.write('# WARNING: Input 255 exceeds paper white constraint (1.34D > 1.25D)\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')

        f.write('# K curve\n')
        for qv in sp1v4_quads:
            f.write(f'{int(qv)}\n')

        for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
            f.write(f'# {channel} curve\n')
            for _ in range(256):
                f.write('0\n')

    print(f"\n✓ .quadファイル生成: {output_quad}")

    # CSVファイル（選択ログ）
    log_df = pd.DataFrame(selection_log)
    log_df.to_csv('SP1v4_selection_log.csv', index=False, float_format='%.4f')
    print(f"✓ 選択ログ: SP1v4_selection_log.csv")

    # 全256ポイントの詳細データ
    detail_df = pd.DataFrame({
        'Input': range(256),
        'Quad_Value': sp1v4_quads,
        'Calculated_Density': sp1v4_densities
    })
    detail_df.to_csv('PX1V-PtPd-SP1v4.txt', index=False, float_format='%.6f')
    print(f"✓ 詳細データ: PX1V-PtPd-SP1v4.txt")

    # measurement_QTR-SP-1v4.csv生成
    sp1v4_measured = pd.DataFrame({
        'input': target['input'],
        'negative_density': [sp1v4_densities[i] for i in target['input']],
        'print_density': ''
    })
    sp1v4_measured.to_csv('measurement_QTR-SP-1v4.csv', index=False, float_format='%.2f')
    print(f"✓ 実際のネガ濃度: measurement_QTR-SP-1v4.csv")

    # グラフ作成
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    all_inputs = np.arange(256)

    # 1. 濃度カーブ比較
    axes[0, 0].plot(all_inputs, sp1v4_densities, 'b-', linewidth=2, label='SP-1v4')
    axes[0, 0].scatter(target['input'], target['negative_density'],
                       c='red', s=100, zorder=5, marker='o',
                       label='Target (measurement_QTR-SP-1)',
                       edgecolors='black', linewidths=1)
    # Input 248とInput 255を強調
    axes[0, 0].scatter([248], [1.23], c='green', s=200, marker='*',
                       zorder=6, label='Input 248 (v23, 1.23D)', edgecolors='black', linewidths=2)
    axes[0, 0].scatter([255], [1.34], c='orange', s=200, marker='*',
                       zorder=6, label='Input 255 (v21, 1.34D)', edgecolors='black', linewidths=2)
    axes[0, 0].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White (1.25D)')
    axes[0, 0].set_xlabel('Input Value', fontsize=12)
    axes[0, 0].set_ylabel('Negative Density', fontsize=12)
    axes[0, 0].set_title('SP-1v4: Density Curve (v23[248] + v21[255])',
                         fontsize=14, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 2. ハイライト域拡大
    highlight_mask = all_inputs >= 200
    axes[0, 1].plot(all_inputs[highlight_mask], sp1v4_densities[highlight_mask],
                    'b-', linewidth=3, label='SP-1v4')
    target_highlight = target[target['input'] >= 200]
    axes[0, 1].scatter(target_highlight['input'],
                       target_highlight['negative_density'],
                       c='red', s=150, zorder=5, marker='o',
                       label='Target', edgecolors='black', linewidths=2)
    axes[0, 1].scatter([248], [1.23], c='green', s=250, marker='*',
                       zorder=6, label='248: v23 (1.23D)', edgecolors='black', linewidths=2)
    axes[0, 1].scatter([255], [1.34], c='orange', s=250, marker='*',
                       zorder=6, label='255: v21 (1.34D)', edgecolors='black', linewidths=2)
    axes[0, 1].axhline(y=1.25, color='red', linestyle='--', linewidth=2,
                       label='Paper White (1.25D)')
    axes[0, 1].set_xlabel('Input Value', fontsize=12)
    axes[0, 1].set_ylabel('Negative Density', fontsize=12)
    axes[0, 1].set_title('SP-1v4: Highlight Region (200-255)',
                         fontsize=14, fontweight='bold')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_xlim(200, 256)

    # 3. 誤差分布
    measured_errors = [log['error'] for log in selection_log]
    measured_inputs_list = [log['input'] for log in selection_log]
    colors = ['green' if log['version'] == 'v21' else 'blue' if log['version'] == 'v22' else 'cyan'
              for log in selection_log]

    axes[1, 0].bar(measured_inputs_list, measured_errors, width=6, color=colors, alpha=0.7)
    axes[1, 0].axhline(y=0, color='black', linestyle='-', linewidth=1)
    axes[1, 0].axhline(y=0.01, color='green', linestyle='--', linewidth=1, alpha=0.5)
    axes[1, 0].axhline(y=-0.01, color='green', linestyle='--', linewidth=1, alpha=0.5)
    axes[1, 0].set_xlabel('Input Value', fontsize=12)
    axes[1, 0].set_ylabel('Error (Calculated - Target)', fontsize=12)
    axes[1, 0].set_title('SP-1v4: Error (green=v21, blue=v22, cyan=v23)',
                         fontsize=14, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3)

    # 4. Quad差分
    axes[1, 1].plot(all_inputs[:-1], quad_diffs, 'g-', linewidth=2)
    axes[1, 1].axhline(y=200, color='red', linestyle='--', linewidth=2,
                       label='Boundary Risk (200)')
    axes[1, 1].set_xlabel('Input Value', fontsize=12)
    axes[1, 1].set_ylabel('Quad Difference', fontsize=12)
    axes[1, 1].set_title('SP-1v4: Boundary Line Risk',
                         fontsize=14, fontweight='bold')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_ylim(-10, min(max_diff + 20, 400))

    plt.tight_layout()
    plt.savefig('SP1v4_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✓ グラフ保存: SP1v4_analysis.png")

    print("\n次のステップ:")
    print(f"  1. measurement_QTR-SP-1v4.csvで目標との差異を確認")
    print(f"  2. sudo cp {output_quad} /Library/Printers/QTR/quadtone/QuadP700/")
    print(f"  3. /Library/Printers/QTR/bin/quadcurves QuadP700")
    print(f"  4. QTR Print-Toolで PX1V-PtPd-SP1v4 を選択してテストプリント")

    return sp1v4_quads, sp1v4_densities, selection_log

if __name__ == '__main__':
    quads, densities, log = generate_sp1v4()

    print("\n" + "=" * 80)
    print("SP-1v4 カーブ生成完了")
    print("Input 248: v23[248]（実測1.23D） ✓")
    print("Input 255: v21[255]（実測1.34D、目標1.35Dに対して-0.01D）")
    print("measurement_QTR-SP-1.csvに最も近いカーブ")
    print("⚠️  注意: Input 255が紙白制約を0.09D超過しています（実験版）")
    print("=" * 80)
