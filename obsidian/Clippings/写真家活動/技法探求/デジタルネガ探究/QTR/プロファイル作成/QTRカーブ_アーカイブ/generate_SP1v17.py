#!/usr/bin/env python3
"""
SP1v17カーブ生成スクリプト - 簡潔版

修正方針:
V7をベースに、簡潔な調整を適用
- Input 0-79: V7のまま
- Input 80-220: 一律で濃度を-0.05D下げる（約-1500 Quad）
- Input 221-248: 線形補間でV7に戻る
- Input 249-255: V7のまま（加速不要）

目的:
- ミッドトーン（80-220）を明るくしてコントラストを下げる
- シンプルな設計でバンディングリスクを最小化
- 単調増加を確実に保つ

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

def create_sp1v17_quads():
    """SP1v17のQuad値配列を作成"""

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    v7_file = f"{base_path}/PX1V-PtPd-SP1v7.quad"

    print("[Step 1] Quad値配列を作成中...")
    v7_header, v7_quads = read_quad_file(v7_file)

    print(f"✓ V7 Quadファイル読み込み: {len(v7_quads)}値")

    # V17を作成
    v17_quads = v7_quads.copy().astype(int)

    # Input 80-220: 一律-1500 Quad
    print(f"\n[Step 2] Input 80-220の濃度を下げる...")
    reduction = 1500
    for i in range(80, 221):
        v17_quads[i] = v7_quads[i] - reduction

    # Input 221-248: 線形補間でV7に戻る
    print(f"\n[Step 3] Input 221-248で線形補間...")
    start_value = v17_quads[220]
    end_value = v7_quads[248]
    steps = 248 - 220

    for i in range(221, 249):
        progress = (i - 220) / steps
        v17_quads[i] = int(start_value + (end_value - start_value) * progress)

    # 単調増加を保証
    print(f"\n[Step 4] 単調増加を保証中...")
    violations_before = 0
    for i in range(1, 256):
        if v17_quads[i] <= v17_quads[i-1]:
            violations_before += 1
            v17_quads[i] = v17_quads[i-1] + 1

    print(f"✓ 修正箇所: {violations_before}箇所")

    def quad_to_density(quad, max_density=1.73, max_quad=55891):
        return quad * max_density / max_quad

    print(f"\n【主要ポイントの確認】")
    for inp in [0, 80, 128, 176, 220, 240, 248, 255]:
        diff = v17_quads[inp] - v7_quads[inp]
        print(f"  Input {inp:3d}: V7={v7_quads[inp]:5d} ({quad_to_density(v7_quads[inp]):.4f}D) → V17={v17_quads[inp]:5d} ({quad_to_density(v17_quads[inp]):.4f}D) [Δ={diff:+5d}]")

    return v7_header, v17_quads, v7_quads

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
        f.write('# PX1V-PtPd-SP1v17 - Simple contrast reduction\n')
        f.write('# Input 0-79: V7 baseline\n')
        f.write('# Input 80-220: Uniform density reduction -1500 Quad (-0.05D)\n')
        f.write('# Input 221-248: Linear interpolation back to V7\n')
        f.write('# Input 249-255: V7 baseline\n')
        f.write('# Created: 2026-03-19 SP1v17\n')
        f.write('# Purpose: Reduce contrast by brightening midtones\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')
        f.write('# K curve\n')

        # 2560値を出力
        for i in range(10):
            for quad in quads:
                f.write(f'{quad}\n')

def plot_comparison(v7_quads, v17_quads):
    """V7とV17の比較グラフを生成"""
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    inputs = np.arange(256)

    def quad_to_density(quad):
        return quad * 1.73 / 55891

    # グラフ1: Quad値の比較
    ax1 = axes[0]
    ax1.plot(inputs, v7_quads, 'b-', label='V7 (Original)', linewidth=2, alpha=0.7)
    ax1.plot(inputs, v17_quads, 'r-', label='V17 (Reduced)', linewidth=2)
    ax1.axvline(x=80, color='orange', linestyle='--', alpha=0.5, label='Start (80)')
    ax1.axvline(x=220, color='green', linestyle='--', alpha=0.5, label='End Reduction (220)')
    ax1.axvline(x=248, color='red', linestyle='--', alpha=0.5, label='Return to V7 (248)')
    ax1.set_xlabel('Input Value')
    ax1.set_ylabel('Quad Value')
    ax1.set_title('V7 vs V17 - Simple Contrast Reduction', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # グラフ2: 濃度比較
    ax2 = axes[1]
    v7_density = [quad_to_density(q) for q in v7_quads]
    v17_density = [quad_to_density(q) for q in v17_quads]
    ax2.plot(inputs, v7_density, 'b-', label='V7', linewidth=2, alpha=0.7)
    ax2.plot(inputs, v17_density, 'r-', label='V17', linewidth=2)
    ax2.axvline(x=80, color='orange', linestyle='--', alpha=0.5)
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
    v17_diff = np.diff(v17_quads)
    ax3.plot(inputs[1:], v7_diff, 'b-', label='V7 Gradient', linewidth=1, alpha=0.7)
    ax3.plot(inputs[1:], v17_diff, 'r-', label='V17 Gradient', linewidth=1)
    ax3.axhline(y=200, color='red', linestyle='--', alpha=0.5, label='Banding Threshold')
    ax3.axhline(y=-200, color='red', linestyle='--', alpha=0.5)
    ax3.axvline(x=80, color='orange', linestyle='--', alpha=0.5)
    ax3.axvline(x=220, color='green', linestyle='--', alpha=0.5)
    ax3.set_xlabel('Input Value')
    ax3.set_ylabel('Quad Difference (Δ)')
    ax3.set_title('Gradient Comparison')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    plt.savefig(f"{base_path}/SP1v17_preview.png", dpi=150, bbox_inches='tight')

    print(f"\n✓ グラフ保存: SP1v17_preview.png")

    plt.close()

def main():
    print("=" * 80)
    print("SP1v17カーブ生成開始（シンプル版）")
    print("=" * 80)

    # Quad値作成
    v7_header, v17_quads, v7_quads = create_sp1v17_quads()

    # バンディングリスク解析
    print("\n[Step 5] バンディングリスク解析中...")
    v7_risks = analyze_banding_risk(v7_quads)
    v17_risks = analyze_banding_risk(v17_quads)

    print(f"✓ V7リスク箇所: {len(v7_risks)}箇所")
    print(f"✓ V17リスク箇所: {len(v17_risks)}箇所")

    # 新規追加されたリスク
    v7_risk_inputs = set([r[0] for r in v7_risks])
    v17_risk_inputs = set([r[0] for r in v17_risks])
    new_risks = v17_risk_inputs - v7_risk_inputs

    if new_risks:
        print(f"\n⚠️ V17で新たに追加されたリスク箇所: {len(new_risks)}箇所")
        for inp in sorted(new_risks)[:10]:
            for r in v17_risks:
                if r[0] == inp:
                    print(f"   Input {r[0]-1}→{r[0]}: Δ={r[1]} Quad")
                    break

    # グラフ生成
    print("\n[Step 6] 比較グラフを生成中...")
    plot_comparison(v7_quads, v17_quads)

    # ファイル出力
    print("\n[Step 7] Quadファイルを出力中...")
    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    quad_file = f"{base_path}/PX1V-PtPd-SP1v17.quad"

    write_quad_file(v17_quads, quad_file)
    print(f"✓ Quadファイル: PX1V-PtPd-SP1v17.quad")

    # サマリー
    print("\n" + "=" * 80)
    print("SP1v17カーブ生成完了")
    print("=" * 80)

    print(f"\n【修正内容】")
    print(f"✓ Input 0-79: V7のまま")
    print(f"✓ Input 80-220: 一律-1500 Quad（-0.05D）削減")
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
