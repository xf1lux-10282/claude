#!/usr/bin/env python3
"""
SP1v18カーブ生成スクリプト - 段階的削減版

修正方針:
V7をベースに、段階的に濃度を削減
- Input 0-79: V7のまま
- Input 80-120: 徐々に削減を増やす（0 → -1500 Quad）
- Input 121-220: 一律-1500 Quad削減
- Input 221-248: 線形補間でV7に戻る
- Input 249-255: V7のまま

目的:
- ミッドトーン（120-220）を明るくしてコントラストを下げる
- 段階的削減で単調増加違反を回避
- シンプルな設計でバンディングリスクを最小化

実行日: 2026-03-19
作成者: Claude Code
"""

import numpy as np
import matplotlib.pyplot as plt

def read_quad_file(filename):
    """Quadファイルを読み込む"""
    with open(filename, 'r') as f:
        lines = f.readlines()

    header_lines = []
    quad_values = []

    for line in lines:
        line = line.strip()
        if line.startswith('#') or line.startswith('##'):
            header_lines.append(line)
        elif line.isdigit():
            quad_values.append(int(line))

    return header_lines, np.array(quad_values[:256])

def create_sp1v18_quads():
    """SP1v18のQuad値配列を作成"""

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    v7_file = f"{base_path}/PX1V-PtPd-SP1v7.quad"

    print("[Step 1] Quad値配列を作成中...")
    v7_header, v7_quads = read_quad_file(v7_file)

    print(f"✓ V7 Quadファイル読み込み: {len(v7_quads)}値")

    # V18を作成
    v18_quads = v7_quads.copy().astype(float)

    max_reduction = 1500

    # Input 80-120: 徐々に削減を増やす（線形）
    print(f"\n[Step 2] Input 80-120で徐々に削減...")
    for i in range(80, 121):
        progress = (i - 80) / (120 - 80)  # 0.0 → 1.0
        reduction = max_reduction * progress
        v18_quads[i] = v7_quads[i] - reduction

    # Input 121-220: 一律-1500 Quad削減
    print(f"\n[Step 3] Input 121-220で一律削減...")
    for i in range(121, 221):
        v18_quads[i] = v7_quads[i] - max_reduction

    # Input 221-248: 線形補間でV7に戻る
    print(f"\n[Step 4] Input 221-248で線形補間...")
    start_value = v18_quads[220]
    end_value = v7_quads[248]
    steps = 248 - 220

    for i in range(221, 249):
        progress = (i - 220) / steps
        v18_quads[i] = start_value + (end_value - start_value) * progress

    # 整数化
    v18_quads = v18_quads.astype(int)

    # 単調増加を保証
    print(f"\n[Step 5] 単調増加を保証中...")
    violations_before = 0
    for i in range(1, 256):
        if v18_quads[i] <= v18_quads[i-1]:
            violations_before += 1
            v18_quads[i] = v18_quads[i-1] + 1

    print(f"✓ 修正箇所: {violations_before}箇所")

    def quad_to_density(quad, max_density=1.73, max_quad=55891):
        return quad * max_density / max_quad

    print(f"\n【主要ポイントの確認】")
    for inp in [0, 80, 100, 120, 176, 220, 240, 248, 255]:
        diff = v18_quads[inp] - v7_quads[inp]
        print(f"  Input {inp:3d}: V7={v7_quads[inp]:5d} ({quad_to_density(v7_quads[inp]):.4f}D) → V18={v18_quads[inp]:5d} ({quad_to_density(v18_quads[inp]):.4f}D) [Δ={diff:+5d}]")

    return v7_header, v18_quads, v7_quads

def analyze_banding_risk(quads, threshold=200):
    """バンディングリスクを解析"""
    risks = []
    for inp in range(1, 256):
        diff = quads[inp] - quads[inp-1]
        if abs(diff) > threshold:
            risks.append((inp, diff))
    return risks

def write_quad_file(quads, filename):
    """Quadファイルを出力"""

    with open(filename, 'w') as f:
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        f.write('# QuadProfile Version 2.8.0\n')
        f.write('# PX1V-PtPd-SP1v18 - Gradual contrast reduction\n')
        f.write('# Input 0-79: V7 baseline\n')
        f.write('# Input 80-120: Gradual density reduction (0 to -1500 Quad)\n')
        f.write('# Input 121-220: Uniform density reduction -1500 Quad (-0.05D)\n')
        f.write('# Input 221-248: Linear interpolation back to V7\n')
        f.write('# Input 249-255: V7 baseline\n')
        f.write('# Created: 2026-03-19 SP1v18\n')
        f.write('# Purpose: Reduce contrast by brightening midtones\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')
        f.write('# K curve\n')

        # 2560値を出力（10チャンネル分）
        # チャンネル1（K）: 実際のカーブ
        # チャンネル2-10（C,M,Y,LC,LM,LK,LLK,V,MK）: すべて0（使用しない）

        # チャンネル1: Kカーブ
        for quad in quads:
            f.write(f'{quad}\n')

        # チャンネル2-10: すべて0（各チャンネルにコメント行を追加）
        channels = ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']
        for channel in channels:
            f.write(f'# {channel} curve\n')
            for j in range(256):
                f.write('0\n')

def plot_comparison(v7_quads, v18_quads):
    """V7とV18の比較グラフを生成"""
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    inputs = np.arange(256)

    def quad_to_density(quad):
        return quad * 1.73 / 55891

    # グラフ1: Quad値の比較
    ax1 = axes[0]
    ax1.plot(inputs, v7_quads, 'b-', label='V7 (Original)', linewidth=2, alpha=0.7)
    ax1.plot(inputs, v18_quads, 'r-', label='V18 (Gradual Reduction)', linewidth=2)
    ax1.axvline(x=80, color='orange', linestyle='--', alpha=0.5, label='Start Reduction (80)')
    ax1.axvline(x=120, color='purple', linestyle='--', alpha=0.5, label='Max Reduction (120)')
    ax1.axvline(x=220, color='green', linestyle='--', alpha=0.5, label='End Reduction (220)')
    ax1.set_xlabel('Input Value')
    ax1.set_ylabel('Quad Value')
    ax1.set_title('V7 vs V18 - Gradual Contrast Reduction', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # グラフ2: 濃度比較
    ax2 = axes[1]
    v7_density = [quad_to_density(q) for q in v7_quads]
    v18_density = [quad_to_density(q) for q in v18_quads]
    ax2.plot(inputs, v7_density, 'b-', label='V7', linewidth=2, alpha=0.7)
    ax2.plot(inputs, v18_density, 'r-', label='V18', linewidth=2)
    ax2.axvline(x=80, color='orange', linestyle='--', alpha=0.5)
    ax2.axvline(x=120, color='purple', linestyle='--', alpha=0.5)
    ax2.axvline(x=220, color='green', linestyle='--', alpha=0.5)
    ax2.axhline(y=1.25, color='red', linestyle=':', alpha=0.5, label='Paper White Limit (1.25D)')
    ax2.set_xlabel('Input Value')
    ax2.set_ylabel('Density (D)')
    ax2.set_title('Density Comparison')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # グラフ3: 勾配比較
    ax3 = axes[2]
    v7_diff = np.diff(v7_quads)
    v18_diff = np.diff(v18_quads)
    ax3.plot(inputs[1:], v7_diff, 'b-', label='V7 Gradient', linewidth=1, alpha=0.7)
    ax3.plot(inputs[1:], v18_diff, 'r-', label='V18 Gradient', linewidth=1)
    ax3.axhline(y=200, color='red', linestyle='--', alpha=0.5, label='Banding Threshold')
    ax3.axhline(y=-200, color='red', linestyle='--', alpha=0.5)
    ax3.axvline(x=80, color='orange', linestyle='--', alpha=0.5)
    ax3.axvline(x=120, color='purple', linestyle='--', alpha=0.5)
    ax3.axvline(x=220, color='green', linestyle='--', alpha=0.5)
    ax3.set_xlabel('Input Value')
    ax3.set_ylabel('Quad Difference (Δ)')
    ax3.set_title('Gradient Comparison - Smooth Transition')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    plt.savefig(f"{base_path}/SP1v18_preview.png", dpi=150, bbox_inches='tight')

    print(f"\n✓ グラフ保存: SP1v18_preview.png")

    plt.close()

def main():
    print("=" * 80)
    print("SP1v18カーブ生成開始（段階的削減版）")
    print("=" * 80)

    # Quad値作成
    v7_header, v18_quads, v7_quads = create_sp1v18_quads()

    # バンディングリスク解析
    print("\n[Step 6] バンディングリスク解析中...")
    v7_risks = analyze_banding_risk(v7_quads)
    v18_risks = analyze_banding_risk(v18_quads)

    print(f"✓ V7リスク箇所: {len(v7_risks)}箇所")
    print(f"✓ V18リスク箇所: {len(v18_risks)}箇所")

    # 新規追加されたリスク
    v7_risk_inputs = set([r[0] for r in v7_risks])
    v18_risk_inputs = set([r[0] for r in v18_risks])
    new_risks = v18_risk_inputs - v7_risk_inputs

    if new_risks:
        print(f"\n⚠️ V18で新たに追加されたリスク箇所: {len(new_risks)}箇所")
        for inp in sorted(new_risks)[:10]:
            for r in v18_risks:
                if r[0] == inp:
                    print(f"   Input {r[0]-1}→{r[0]}: Δ={r[1]} Quad")
                    break

    # グラフ生成
    print("\n[Step 7] 比較グラフを生成中...")
    plot_comparison(v7_quads, v18_quads)

    # ファイル出力
    print("\n[Step 8] Quadファイルを出力中...")
    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    quad_file = f"{base_path}/PX1V-PtPd-SP1v18.quad"

    write_quad_file(v18_quads, quad_file)
    print(f"✓ Quadファイル: PX1V-PtPd-SP1v18.quad")

    # サマリー
    print("\n" + "=" * 80)
    print("SP1v18カーブ生成完了")
    print("=" * 80)

    print(f"\n【修正内容】")
    print(f"✓ Input 0-79: V7のまま")
    print(f"✓ Input 80-120: 段階的削減（0 → -1500 Quad）")
    print(f"✓ Input 121-220: 一律-1500 Quad（-0.05D）削減")
    print(f"✓ Input 221-248: 線形補間でV7に戻る")
    print(f"✓ Input 249-255: V7のまま")

    print(f"\n【バンディングリスク】")
    if len(new_risks) == 0:
        print(f"✓ 新たなリスク箇所なし")
    else:
        print(f"⚠️ 新たなリスク箇所: {len(new_risks)}箇所")

    print(f"\n【次のステップ】")
    print(f"1. グラフを確認してカーブ形状を評価")
    print(f"2. 問題なければQTRプリンタにインストール")
    print(f"3. テストプリントで実際の効果を確認")

if __name__ == "__main__":
    main()
