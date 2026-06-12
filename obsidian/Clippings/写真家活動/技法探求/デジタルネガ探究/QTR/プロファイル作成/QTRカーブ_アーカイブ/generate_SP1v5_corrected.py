#!/usr/bin/env python3
"""
PX1V-PtPd-SP1v5: SP-4の実測結果を使って修正

戦略：
- SP-4（SP1v4の実測）で濃度が高かった箇所を、目標値に合わせて下げる
- 実測値ベースで調整するため、より正確な結果が期待できる
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

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

def generate_sp1v5():
    """SP-1v5を生成：SP-4実測結果を使って修正"""
    print("=" * 80)
    print("PX1V-PtPd-SP1v5: SP-4実測結果に基づく修正版")
    print("Input 192-240の濃度を下げて目標値に合わせる")
    print("=" * 80)

    # 目標濃度を読み込み
    target = pd.read_csv('/Users/daisukekinoshita/Desktop/measurement_QTR-SP-1.csv')
    print(f"\n目標データ: {len(target)}ポイント")

    # SP-4の実測結果を読み込み
    sp4 = pd.read_csv('/Users/daisukekinoshita/Desktop/measurement_QTR-SP-4.csv')
    print(f"SP-4実測データ: {len(sp4)}ポイント")

    # SP1v4のQuad値を読み込み
    sp1v4_quads = read_quad_file('/Users/daisukekinoshita/Desktop/PX1V-PtPd-SP1v4.quad')
    print(f"SP1v4 Quad値: {len(sp1v4_quads)}ポイント")

    # SP1v5のQuad値配列を初期化（SP1v4からコピー）
    sp1v5_quads = np.copy(sp1v4_quads)

    print("\n調整が必要な地点を特定:")
    print("Input  目標濃度  SP4実測  差分    SP1v4_Quad  調整")
    print("=" * 80)

    adjustments = []

    for i in range(len(target)):
        input_val = int(target.iloc[i]['input'])
        target_d = target.iloc[i]['negative_density']
        sp4_d = sp4.iloc[i]['negative_density']
        diff = sp4_d - target_d

        # 0.025D以上高い地点を調整対象とする
        if diff > 0.025:
            sp1v4_quad = sp1v4_quads[input_val]

            # 濃度差に応じてQuad値を減少させる
            # 経験的に: 0.01D ≈ Quad 200程度の調整
            adjustment_ratio = diff / 0.01 * 200
            new_quad = int(sp1v4_quad - adjustment_ratio)

            # 単調性を保証（前のQuad値より小さくしない）
            if input_val > 0 and new_quad < sp1v5_quads[input_val - 1]:
                new_quad = sp1v5_quads[input_val - 1]

            adjustments.append({
                'input': input_val,
                'target': target_d,
                'sp4': sp4_d,
                'diff': diff,
                'old_quad': sp1v4_quad,
                'new_quad': new_quad,
                'quad_change': new_quad - sp1v4_quad
            })

            sp1v5_quads[input_val] = new_quad

            print(f"{input_val:3d}    {target_d:.2f}D     {sp4_d:.2f}D   {diff:+.3f}D  {sp1v4_quad:5d}      {new_quad - sp1v4_quad:+5d}")

    if not adjustments:
        print("  調整不要（全地点が許容範囲内）")

    # 測定点間を線形補間で再計算
    measured_inputs = target['input'].values
    measured_quads = np.array([sp1v5_quads[i] for i in measured_inputs])

    interp_func = interp1d(measured_inputs, measured_quads,
                           kind='linear', fill_value='extrapolate')

    for i in range(256):
        if i not in measured_inputs:
            interp_value = float(interp_func(i))
            sp1v5_quads[i] = int(round(interp_value))

    # 単調性を保証
    for i in range(1, 256):
        if sp1v5_quads[i] < sp1v5_quads[i-1]:
            sp1v5_quads[i] = sp1v5_quads[i-1]

    print(f"\n調整完了: {len(adjustments)}地点を修正")

    # 境界線リスク分析
    quad_diffs = np.diff(sp1v5_quads)
    max_diff = np.max(quad_diffs)
    max_diff_input = np.argmax(quad_diffs)

    print(f"\n境界線リスク解析:")
    print(f"  最大Quad差分: {max_diff:.0f} (Input {max_diff_input}→{max_diff_input+1})")
    if max_diff > 200:
        print(f"  ⚠️  境界線リスクあり")
        risky = np.where(quad_diffs > 200)[0]
        if len(risky) <= 15:
            print(f"  リスク箇所数: {len(risky)}個")
            for idx in risky[:10]:  # 最大10個表示
                print(f"     Input {idx}→{idx+1}: {quad_diffs[idx]:.0f}")
    else:
        print(f"  ✓ 境界線リスクなし")

    # SP1v4との比較
    print(f"\nSP1v4との変更点:")
    print(f"  修正地点数: {len(adjustments)}")
    if adjustments:
        total_change = sum([abs(a['quad_change']) for a in adjustments])
        print(f"  総Quad変更量: {total_change}")
        print(f"  平均Quad変更: {total_change / len(adjustments):.0f}")

    # .quadファイル書き出し
    output_quad = 'PX1V-PtPd-SP1v5.quad'
    with open(output_quad, 'w') as f:
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        f.write('# QuadProfile Version 2.8.0\n')
        f.write('# PX1V-PtPd-SP1v5 - Corrected based on SP-4 measurements\n')
        f.write('# Fixed Input 192-240 density overrun\n')
        f.write('# Based on SP1v4 with adjustments from measurement_QTR-SP-4.csv\n')
        f.write('# Created: 2026-03-17\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')

        f.write('# K curve\n')
        for qv in sp1v5_quads:
            f.write(f'{int(qv)}\n')

        for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
            f.write(f'# {channel} curve\n')
            for _ in range(256):
                f.write('0\n')

    print(f"\n✓ .quadファイル生成: {output_quad}")

    # 詳細データ
    detail_df = pd.DataFrame({
        'Input': range(256),
        'SP1v4_Quad': sp1v4_quads,
        'SP1v5_Quad': sp1v5_quads,
        'Quad_Change': sp1v5_quads - sp1v4_quads
    })
    detail_df.to_csv('PX1V-PtPd-SP1v5.txt', index=False)
    print(f"✓ 詳細データ: PX1V-PtPd-SP1v5.txt")

    # 調整ログ
    if adjustments:
        adj_df = pd.DataFrame(adjustments)
        adj_df.to_csv('SP1v5_adjustments.csv', index=False, float_format='%.4f')
        print(f"✓ 調整ログ: SP1v5_adjustments.csv")

    # グラフ作成
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    all_inputs = np.arange(256)

    # 1. Quad値の比較
    axes[0, 0].plot(all_inputs, sp1v4_quads, 'b-', linewidth=2, label='SP1v4', alpha=0.7)
    axes[0, 0].plot(all_inputs, sp1v5_quads, 'r-', linewidth=2, label='SP1v5 (corrected)')
    if adjustments:
        adj_inputs = [a['input'] for a in adjustments]
        adj_old = [a['old_quad'] for a in adjustments]
        adj_new = [a['new_quad'] for a in adjustments]
        axes[0, 0].scatter(adj_inputs, adj_old, c='blue', s=100, zorder=5, marker='o')
        axes[0, 0].scatter(adj_inputs, adj_new, c='red', s=100, zorder=5, marker='*')
    axes[0, 0].set_xlabel('Input Value', fontsize=12)
    axes[0, 0].set_ylabel('Quad Value', fontsize=12)
    axes[0, 0].set_title('SP1v5: Quad Value Correction', fontsize=14, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 2. Quad差分
    quad_diffs_v4 = np.diff(sp1v4_quads)
    quad_diffs_v5 = np.diff(sp1v5_quads)
    axes[0, 1].plot(all_inputs[:-1], quad_diffs_v4, 'b-', linewidth=1, label='SP1v4', alpha=0.5)
    axes[0, 1].plot(all_inputs[:-1], quad_diffs_v5, 'r-', linewidth=2, label='SP1v5')
    axes[0, 1].axhline(y=200, color='orange', linestyle='--', linewidth=2, label='Risk threshold')
    axes[0, 1].set_xlabel('Input Value', fontsize=12)
    axes[0, 1].set_ylabel('Quad Difference', fontsize=12)
    axes[0, 1].set_title('SP1v5: Boundary Line Risk', fontsize=14, fontweight='bold')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_ylim(-10, min(max(max_diff, np.max(quad_diffs_v4)) + 50, 500))

    # 3. Input 192-255拡大
    highlight_mask = all_inputs >= 192
    axes[1, 0].plot(all_inputs[highlight_mask], sp1v4_quads[highlight_mask],
                    'b-', linewidth=2, label='SP1v4', alpha=0.7)
    axes[1, 0].plot(all_inputs[highlight_mask], sp1v5_quads[highlight_mask],
                    'r-', linewidth=3, label='SP1v5 (corrected)')
    if adjustments:
        adj_high = [a for a in adjustments if a['input'] >= 192]
        if adj_high:
            adj_inputs_high = [a['input'] for a in adj_high]
            adj_old_high = [a['old_quad'] for a in adj_high]
            adj_new_high = [a['new_quad'] for a in adj_high]
            axes[1, 0].scatter(adj_inputs_high, adj_old_high, c='blue', s=150,
                              zorder=5, marker='o', label='Original')
            axes[1, 0].scatter(adj_inputs_high, adj_new_high, c='red', s=150,
                              zorder=5, marker='*', label='Corrected')
    axes[1, 0].set_xlabel('Input Value', fontsize=12)
    axes[1, 0].set_ylabel('Quad Value', fontsize=12)
    axes[1, 0].set_title('SP1v5: High Value Region (192-255)', fontsize=14, fontweight='bold')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_xlim(192, 256)

    # 4. Quad変更量
    quad_changes = sp1v5_quads - sp1v4_quads
    axes[1, 1].bar(all_inputs, quad_changes, width=1, color='green', alpha=0.7)
    axes[1, 1].axhline(y=0, color='black', linestyle='-', linewidth=1)
    axes[1, 1].set_xlabel('Input Value', fontsize=12)
    axes[1, 1].set_ylabel('Quad Change (v5 - v4)', fontsize=12)
    axes[1, 1].set_title('SP1v5: Quad Value Changes', fontsize=14, fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('SP1v5_correction_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✓ グラフ保存: SP1v5_correction_analysis.png")

    print("\n次のステップ:")
    print(f"  1. グラフで変更内容を確認")
    print(f"  2. sudo cp {output_quad} /Library/Printers/QTR/quadtone/QuadP700/")
    print(f"  3. /Library/Printers/QTR/bin/quadcurves QuadP700")
    print(f"  4. QTR Print-Toolで PX1V-PtPd-SP1v5 を選択してテストプリント")

    return sp1v5_quads, adjustments

if __name__ == '__main__':
    quads, adjustments = generate_sp1v5()

    print("\n" + "=" * 80)
    print("SP-1v5 カーブ生成完了")
    print("SP-4実測結果に基づき、Input 192-240の濃度超過を修正")
    print(f"修正地点数: {len(adjustments)}")
    print("=" * 80)
