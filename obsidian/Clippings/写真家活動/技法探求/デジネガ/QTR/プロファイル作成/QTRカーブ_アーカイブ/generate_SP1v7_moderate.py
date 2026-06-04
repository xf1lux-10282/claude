#!/usr/bin/env python3
"""
PX1V-PtPd-SP1v7: Input 255を1.7Dに設定（適度な遮光）

戦略：
- Input 255を1.7Dにする（2.0Dよりも穏やかで境界線リスク低減）
- Input 248-254を再補間
- Input 0-240はSP1v5を維持
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# 基本定数
SLOPE = 0.007387
INTERCEPT = 0.0935

def density_to_quad(density):
    """濃度からQuad値を逆算"""
    baseline = (density - INTERCEPT) / SLOPE
    quad = int(round(baseline * 257.0))
    return quad

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

def generate_sp1v7():
    """SP-1v7を生成：Input 255を1.7Dに設定"""
    print("=" * 80)
    print("PX1V-PtPd-SP1v7: Input 255を1.7Dに設定（適度な遮光）")
    print("=" * 80)

    # SP1v5をベースとして読み込み
    sp1v5_quads = read_quad_file('/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/QTR_Archive_2026-03-17/PX1V-PtPd-SP1v5.quad')
    print(f"\nSP1v5をベースに使用")
    print(f"  SP1v5 Input 248: Quad={sp1v5_quads[248]}, 濃度={quad_to_density(sp1v5_quads[248]):.2f}D")
    print(f"  SP1v5 Input 255: Quad={sp1v5_quads[255]}, 濃度={quad_to_density(sp1v5_quads[255]):.2f}D")

    # Input 255を1.7Dにするために必要なQuad値を計算
    target_density_255 = 1.7
    quad_255_new = density_to_quad(target_density_255)

    # Quad値の上限チェック（65535が最大）
    if quad_255_new > 65535:
        print(f"\n⚠️  警告: 計算されたQuad値({quad_255_new})が上限(65535)を超えています")
        quad_255_new = 65535
        actual_density = quad_to_density(quad_255_new)
        print(f"  Quad値を上限65535に制限: 実際の濃度は{actual_density:.2f}D")
    else:
        actual_density = quad_to_density(quad_255_new)

    print(f"\nInput 255の設定:")
    print(f"  目標濃度: {target_density_255:.2f}D")
    print(f"  必要なQuad値: {quad_255_new}")
    print(f"  実際の濃度: {actual_density:.2f}D")
    print(f"  SP1v5からの変更: {quad_255_new - sp1v5_quads[255]:+d}")

    # SP1v7のQuad値配列を初期化（SP1v5からコピー）
    sp1v7_quads = np.copy(sp1v5_quads)

    # Input 255を更新
    sp1v7_quads[255] = quad_255_new

    # Input 248-254を再補間
    print(f"\nInput 248-254の再補間:")
    print(f"  Input 248: Quad={sp1v7_quads[248]} (SP1v5と同じ、濃度{quad_to_density(sp1v7_quads[248]):.2f}D)")
    print(f"  Input 255: Quad={quad_255_new} (新規、濃度{actual_density:.2f}D)")

    # 線形補間
    anchor_inputs = [248, 255]
    anchor_quads = [sp1v7_quads[248], quad_255_new]

    print(f"\n  補間されるInput:")
    for i in range(249, 255):
        ratio = (i - 248) / (255 - 248)
        sp1v7_quads[i] = int(round(anchor_quads[0] + ratio * (anchor_quads[1] - anchor_quads[0])))
        density = quad_to_density(sp1v7_quads[i])
        print(f"    Input {i}: Quad={sp1v7_quads[i]}, 濃度={density:.2f}D")

    # 単調性を保証
    for i in range(1, 256):
        if sp1v7_quads[i] < sp1v7_quads[i-1]:
            sp1v7_quads[i] = sp1v7_quads[i-1]

    # 境界線リスク分析
    quad_diffs = np.diff(sp1v7_quads)
    max_diff = np.max(quad_diffs)
    max_diff_input = np.argmax(quad_diffs)

    print(f"\n境界線リスク解析:")
    print(f"  最大Quad差分: {max_diff:.0f} (Input {max_diff_input}→{max_diff_input+1})")

    # Input 248-255の差分を詳細表示
    print(f"\n  Input 248-255のQuad差分:")
    for i in range(248, 255):
        diff = sp1v7_quads[i+1] - sp1v7_quads[i]
        if diff > 500:
            marker = " ⚠️⚠️ 大"
        elif diff > 300:
            marker = " ⚠️ 中"
        elif diff > 200:
            marker = " △ 小"
        else:
            marker = " ✓"
        print(f"    Input {i}→{i+1}: {diff:.0f}{marker}")

    risky = np.where(quad_diffs > 200)[0]
    print(f"\n  境界線リスク箇所（Quad差分>200）: {len(risky)}箇所")

    # Input 248-255の濃度を確認
    print(f"\nInput 248-255の濃度段階確認:")
    print(f"Input  Quad値  濃度    前地点との差")
    print("-" * 50)
    prev_density = quad_to_density(sp1v7_quads[248])
    print(f"248    {sp1v7_quads[248]:5d}  {prev_density:.2f}D  (anchor)")

    for i in range(249, 256):
        density = quad_to_density(sp1v7_quads[i])
        diff = density - prev_density
        print(f"{i:3d}    {sp1v7_quads[i]:5d}  {density:.2f}D  {diff:+.3f}D")
        prev_density = density

    # .quadファイル書き出し
    output_quad = 'PX1V-PtPd-SP1v7.quad'
    with open(output_quad, 'w') as f:
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        f.write('# QuadProfile Version 2.8.0\n')
        f.write('# PX1V-PtPd-SP1v7 - Moderate opacity at Input 255 (1.7D)\n')
        f.write('# Input 0-247: SP1v5 (corrected based on SP-4 measurements)\n')
        f.write('# Input 248: SP1v5 (1.20D calculated, 1.24D measured)\n')
        f.write('# Input 249-254: Linear interpolation\n')
        f.write(f'# Input 255: Moderate opacity (1.7D target, Quad={quad_255_new})\n')
        f.write('# Created: 2026-03-17\n')
        f.write('# WARNING: Input 255 exceeds paper white constraint (experimental)\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')

        f.write('# K curve\n')
        for qv in sp1v7_quads:
            f.write(f'{int(qv)}\n')

        for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
            f.write(f'# {channel} curve\n')
            for _ in range(256):
                f.write('0\n')

    print(f"\n✓ .quadファイル生成: {output_quad}")

    # 詳細データ
    detail_df = pd.DataFrame({
        'Input': range(256),
        'SP1v5_Quad': sp1v5_quads,
        'SP1v7_Quad': sp1v7_quads,
        'Quad_Change': sp1v7_quads - sp1v5_quads,
        'SP1v7_Density': [quad_to_density(q) for q in sp1v7_quads]
    })
    detail_df.to_csv('PX1V-PtPd-SP1v7.txt', index=False, float_format='%.6f')
    print(f"✓ 詳細データ: PX1V-PtPd-SP1v7.txt")

    # グラフ作成
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    all_inputs = np.arange(256)
    sp1v5_densities = np.array([quad_to_density(q) for q in sp1v5_quads])
    sp1v7_densities = np.array([quad_to_density(q) for q in sp1v7_quads])

    # 1. 濃度カーブ比較
    axes[0, 0].plot(all_inputs, sp1v5_densities, 'b-', linewidth=2, label='SP1v5', alpha=0.7)
    axes[0, 0].plot(all_inputs, sp1v7_densities, 'r-', linewidth=3, label='SP1v7 (1.7D)')
    axes[0, 0].axhline(y=1.7, color='green', linestyle='--', linewidth=2,
                       label='Target (1.7D)')
    axes[0, 0].axhline(y=1.25, color='orange', linestyle='--', linewidth=1,
                       label='Paper white (1.25D)')
    axes[0, 0].scatter([255], [quad_to_density(quad_255_new)], c='red', s=300,
                       marker='*', zorder=6, edgecolors='black', linewidths=2,
                       label=f'Input 255 ({actual_density:.2f}D)')
    axes[0, 0].set_xlabel('Input Value', fontsize=12)
    axes[0, 0].set_ylabel('Negative Density', fontsize=12)
    axes[0, 0].set_title('SP1v7: Moderate Opacity at Input 255 (1.7D)',
                         fontsize=14, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 2. ハイライト域拡大（200-255）
    highlight_mask = all_inputs >= 200
    axes[0, 1].plot(all_inputs[highlight_mask], sp1v5_densities[highlight_mask],
                    'b-', linewidth=2, label='SP1v5', alpha=0.7)
    axes[0, 1].plot(all_inputs[highlight_mask], sp1v7_densities[highlight_mask],
                    'r-', linewidth=3, label='SP1v7 (1.7D)')
    axes[0, 1].axhline(y=1.7, color='green', linestyle='--', linewidth=2,
                       label='Target (1.7D)')
    axes[0, 1].scatter([248], [quad_to_density(sp1v7_quads[248])], c='blue', s=200,
                       marker='o', zorder=5, edgecolors='black', linewidths=2,
                       label='Input 248 (anchor)')
    axes[0, 1].scatter([255], [quad_to_density(quad_255_new)], c='red', s=300,
                       marker='*', zorder=6, edgecolors='black', linewidths=2,
                       label=f'Input 255 ({actual_density:.2f}D)')
    axes[0, 1].set_xlabel('Input Value', fontsize=12)
    axes[0, 1].set_ylabel('Negative Density', fontsize=12)
    axes[0, 1].set_title('SP1v7: Highlight Region (200-255)',
                         fontsize=14, fontweight='bold')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_xlim(200, 256)
    axes[0, 1].set_ylim(0.8, 1.8)

    # 3. Quad差分
    quad_diffs_v5 = np.diff(sp1v5_quads)
    quad_diffs_v7 = np.diff(sp1v7_quads)
    axes[1, 0].plot(all_inputs[:-1], quad_diffs_v5, 'b-', linewidth=1,
                    label='SP1v5', alpha=0.5)
    axes[1, 0].plot(all_inputs[:-1], quad_diffs_v7, 'r-', linewidth=2,
                    label='SP1v7')
    axes[1, 0].axhline(y=200, color='orange', linestyle='--', linewidth=2,
                       label='Risk threshold (200)')
    axes[1, 0].axhline(y=300, color='red', linestyle='--', linewidth=1,
                       label='High risk (300)', alpha=0.5)
    axes[1, 0].set_xlabel('Input Value', fontsize=12)
    axes[1, 0].set_ylabel('Quad Difference', fontsize=12)
    axes[1, 0].set_title('SP1v7: Boundary Line Risk', fontsize=14, fontweight='bold')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_ylim(-10, min(max(max_diff, np.max(quad_diffs_v5)) + 100, 1000))

    # 4. Input 240-255のQuad値とQuad差分
    highlight_inputs = range(240, 256)
    v7_high_quads = [sp1v7_quads[i] for i in highlight_inputs]
    v7_high_diffs = [sp1v7_quads[i+1] - sp1v7_quads[i] for i in range(240, 255)]

    ax4_1 = axes[1, 1]
    ax4_2 = ax4_1.twinx()

    x_pos = np.arange(len(highlight_inputs))

    # Quad値を棒グラフで
    color = 'tab:blue'
    ax4_1.bar(x_pos, v7_high_quads, width=0.8, color=color, alpha=0.6, label='Quad Value')
    ax4_1.set_xlabel('Input Value', fontsize=12)
    ax4_1.set_ylabel('Quad Value', fontsize=12, color=color)
    ax4_1.tick_params(axis='y', labelcolor=color)
    ax4_1.set_xticks(x_pos)
    ax4_1.set_xticklabels(highlight_inputs)

    # Quad差分を折れ線で
    color = 'tab:red'
    x_pos_diff = np.arange(len(v7_high_diffs))
    ax4_2.plot(x_pos_diff + 0.5, v7_high_diffs, color=color, linewidth=3, marker='o',
               markersize=8, label='Quad Difference')
    ax4_2.axhline(y=200, color='orange', linestyle='--', linewidth=1, alpha=0.5)
    ax4_2.set_ylabel('Quad Difference', fontsize=12, color=color)
    ax4_2.tick_params(axis='y', labelcolor=color)

    axes[1, 1].set_title('SP1v7: Highlight Detail (240-255)', fontsize=14, fontweight='bold')
    ax4_1.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('SP1v7_moderate_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✓ グラフ保存: SP1v7_moderate_analysis.png")

    print("\n次のステップ:")
    print(f"  1. グラフで変更内容を確認")
    print(f"  2. sudo cp {output_quad} /Library/Printers/QTR/quadtone/QuadP700/")
    print(f"  3. /Library/Printers/QTR/bin/quadcurves QuadP700")
    print(f"  4. QTR Print-Toolで PX1V-PtPd-SP1v7 を選択してテストプリント")

    return sp1v7_quads, quad_255_new

if __name__ == '__main__':
    quads, quad_255 = generate_sp1v7()

    print("\n" + "=" * 80)
    print("SP-1v7 カーブ生成完了")
    print(f"Input 255を1.7D（適度な遮光、Quad={quad_255}）に設定")
    print("Input 0-247はSP1v5を維持（測定値ベースで最適化済み）")
    print("⚠️  注意: Input 255が紙白制約を0.45D超過（実験版）")
    print("境界線リスクはSP1v6より大幅に低減")
    print("=" * 80)
