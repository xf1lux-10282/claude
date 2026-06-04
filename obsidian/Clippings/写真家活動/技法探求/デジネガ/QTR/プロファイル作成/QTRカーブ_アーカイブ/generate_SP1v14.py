#!/usr/bin/env python3
"""
SP1v14カーブ生成スクリプト - スプライン補間版

修正方針:
V7をベースに、スプライン補間で完全に滑らかなコントラスト調整
1. Input 0-99: V7を+8シフト（固定）
2. Input 100-210: スプライン補間で滑らかに接続
3. Input 211-247: V7を-8シフト（固定）
4. Input 248: 1.10Dに設定（ハイライト表現域を広げる）
5. Input 249-254: リニア補間（248から255へ）
6. Input 255: V7のまま維持（1.73D、完全遮光）

目的:
- V7で得られた良好な結果を維持しつつ、コントラストを下げる
- 完全に滑らかな遷移でバンディングリスクを最小化
- ハイライト表現域を広げて階調を豊かに

実行日: 2026-03-19
作成者: Claude Code
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline

def read_quad_file(filename):
    """Quadファイルを読み込む"""
    with open(filename, 'r') as f:
        lines = f.readlines()

    # ヘッダー行を保存
    header_lines = []
    quad_values = []

    for line in lines:
        line = line.strip()
        if line.startswith('#') or line.startswith('##'):
            header_lines.append(line)
        elif line.isdigit():
            quad_values.append(int(line))

    return header_lines, np.array(quad_values[:256])

def create_sp1v14_quads():
    """SP1v14のQuad値配列を作成"""

    # ファイルパス
    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"

    v7_file = f"{base_path}/PX1V-PtPd-SP1v7.quad"

    # Quadファイルを読み込み
    print("[Step 1] Quad値配列を作成中...")
    v7_header, v7_quads = read_quad_file(v7_file)

    print(f"✓ V7 Quadファイル読み込み: {len(v7_quads)}値")

    # V14をベースに作成
    v14_quads = v7_quads.copy()

    def quad_to_density(quad, max_density=1.73, max_quad=55891):
        return quad * max_density / max_quad

    def density_to_quad(density, max_density=1.73, max_quad=55891):
        return int(density * max_quad / max_density)

    # Input 0-99: V7を+8シフト
    print(f"\n[1] Input 0-99: V7を+8シフト（シャドウを明るく）")
    for inp in range(0, 100):
        source_input = inp + 8
        if source_input <= 255:
            v14_quads[inp] = v7_quads[source_input]

    # Input 211-247: V7を-8シフト
    print(f"\n[2] Input 211-247: V7を-8シフト（ハイライトを暗く）")
    for inp in range(211, 248):
        source_input = inp - 8
        if source_input >= 0:
            v14_quads[inp] = v7_quads[source_input]

    # Input 248: 1.10Dに設定（ハイライト表現域を広げる）
    print(f"\n[3] Input 248: 1.10Dに設定（ハイライト表現域を広げる）")
    target_density_248 = 1.10
    target_quad_248 = density_to_quad(target_density_248)
    v14_quads[248] = target_quad_248

    print(f"   Input 248: {v14_quads[248]} Quad ({quad_to_density(v14_quads[248]):.4f}D)")

    # Input 100-210: スプライン補間
    print(f"\n[4] Input 100-210: スプライン補間で滑らかに接続")

    # スプライン補間のアンカーポイント
    # より多くのアンカーポイントで自然な曲線を作る
    anchor_inputs = [99, 100, 155, 210, 211]
    anchor_quads = [
        v14_quads[99],   # V7+8シフトの最後
        v14_quads[100],  # スプライン開始点
        v7_quads[155],   # 中間点（V7そのまま）
        v14_quads[210],  # スプライン終了点
        v14_quads[211]   # V7-8シフトの最初
    ]

    # CubicSplineで補間
    cs = CubicSpline(anchor_inputs, anchor_quads, bc_type='clamped')

    # Input 101-209を補間
    for inp in range(101, 210):
        v14_quads[inp] = int(cs(inp))

    print(f"   Input 100: {v14_quads[100]} Quad ({quad_to_density(v14_quads[100]):.4f}D)")
    print(f"   Input 155: {v14_quads[155]} Quad ({quad_to_density(v14_quads[155]):.4f}D) [中間点]")
    print(f"   Input 210: {v14_quads[210]} Quad ({quad_to_density(v14_quads[210]):.4f}D)")

    # Input 249-254: リニア補間（248から255へ）
    print(f"\n[5] Input 249-254: リニア補間（248から255へ）")

    start_input_249 = 248
    end_input_249 = 255
    start_quad_249 = v14_quads[248]
    end_quad_249 = v7_quads[255]  # 1.73D

    for inp in range(249, 255):
        ratio = (inp - start_input_249) / (end_input_249 - start_input_249)
        v14_quads[inp] = int(start_quad_249 + (end_quad_249 - start_quad_249) * ratio)

    # Input 255: V7のまま
    print(f"\n[6] Input 255: V7のまま維持（1.73D）")
    v14_quads[255] = v7_quads[255]

    print(f"   Input 255: {v14_quads[255]} Quad ({quad_to_density(v14_quads[255]):.4f}D)")

    return v7_header, v14_quads, v7_quads

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
        # ヘッダー出力
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        f.write('# QuadProfile Version 2.8.0\n')
        f.write('# PX1V-PtPd-SP1v14 - Spline interpolation with extended highlight range\n')
        f.write('# Input 0-99: V7 shifted by +8 steps (brighter shadows)\n')
        f.write('# Input 100-210: Cubic spline interpolation (smooth transition)\n')
        f.write('# Input 211-247: V7 shifted by -8 steps (darker highlights)\n')
        f.write('# Input 248: 1.10D (extended highlight tonal range)\n')
        f.write('# Input 249-254: Linear interpolation from 248 to 255\n')
        f.write('# Input 255: V7[255] value (1.73D - complete opacity)\n')
        f.write('# Created: 2026-03-19 SP1v14\n')
        f.write('# Purpose: Smooth contrast reduction with rich highlights\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')
        f.write('# K curve\n')

        # 2560値を出力（最初の256値を10回繰り返し）
        for i in range(10):
            for quad in quads:
                f.write(f'{quad}\n')

def plot_comparison(v7_quads, v14_quads):
    """V7とV14の比較グラフを生成"""
    fig, axes = plt.subplots(4, 1, figsize=(14, 14))

    inputs = np.arange(256)

    def quad_to_density(quad):
        return quad * 1.73 / 55891

    # グラフ1: 全体比較
    ax1 = axes[0]
    ax1.plot(inputs, v7_quads, 'b-', label='V7 (Original)', linewidth=2, alpha=0.7)
    ax1.plot(inputs, v14_quads, 'r-', label='V14 (Spline)', linewidth=2)
    ax1.axvline(x=100, color='orange', linestyle='--', alpha=0.5, label='Spline Start (100)')
    ax1.axvline(x=155, color='purple', linestyle=':', alpha=0.5, label='Midpoint (155)')
    ax1.axvline(x=210, color='green', linestyle='--', alpha=0.5, label='Spline End (210)')
    ax1.set_xlabel('Input Value')
    ax1.set_ylabel('Quad Value')
    ax1.set_title('V7 vs V14 Quad Values - Spline Interpolation', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # グラフ2: 濃度比較
    ax2 = axes[1]
    v7_density = [quad_to_density(q) for q in v7_quads]
    v14_density = [quad_to_density(q) for q in v14_quads]
    ax2.plot(inputs, v7_density, 'b-', label='V7', linewidth=2, alpha=0.7)
    ax2.plot(inputs, v14_density, 'r-', label='V14', linewidth=2)
    ax2.axvline(x=100, color='orange', linestyle='--', alpha=0.5)
    ax2.axvline(x=155, color='purple', linestyle=':', alpha=0.5)
    ax2.axvline(x=210, color='green', linestyle='--', alpha=0.5)
    ax2.axhline(y=1.25, color='red', linestyle=':', alpha=0.5, label='Paper White Limit (1.25D)')
    ax2.axhline(y=1.10, color='orange', linestyle=':', alpha=0.5, label='V14[248] Target (1.10D)')
    ax2.set_xlabel('Input Value')
    ax2.set_ylabel('Density (D)')
    ax2.set_title('Density Comparison - Extended Highlight Range')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # グラフ3: 差分比較（全体）
    ax3 = axes[2]
    v7_diff = np.diff(v7_quads)
    v14_diff = np.diff(v14_quads)
    ax3.plot(inputs[1:], v7_diff, 'b-', label='V7 Gradient', linewidth=1, alpha=0.7)
    ax3.plot(inputs[1:], v14_diff, 'r-', label='V14 Gradient', linewidth=1)
    ax3.axhline(y=200, color='red', linestyle='--', alpha=0.5, label='Banding Threshold')
    ax3.axhline(y=-200, color='red', linestyle='--', alpha=0.5)
    ax3.axvline(x=100, color='orange', linestyle='--', alpha=0.5)
    ax3.axvline(x=155, color='purple', linestyle=':', alpha=0.5)
    ax3.axvline(x=210, color='green', linestyle='--', alpha=0.5)
    ax3.set_xlabel('Input Value')
    ax3.set_ylabel('Quad Difference (Δ)')
    ax3.set_title('Gradient Comparison - Banding Risk')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # グラフ4: Input 90-220の拡大図
    ax4 = axes[3]
    zoom_range = range(90, 221)
    ax4.plot([i for i in zoom_range], [v7_quads[i] for i in zoom_range],
             'b-', label='V7', linewidth=2, alpha=0.7)
    ax4.plot([i for i in zoom_range], [v14_quads[i] for i in zoom_range],
             'r-', label='V14 (Spline)', linewidth=2)
    ax4.axvline(x=100, color='orange', linestyle='--', alpha=0.5, label='Spline Start')
    ax4.axvline(x=155, color='purple', linestyle=':', alpha=0.5, label='Midpoint')
    ax4.axvline(x=210, color='green', linestyle='--', alpha=0.5, label='Spline End')
    ax4.set_xlabel('Input Value')
    ax4.set_ylabel('Quad Value')
    ax4.set_title('Detail: Input 90-220 (Spline Transition Zone)', fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    plt.savefig(f"{base_path}/SP1v14_preview.png", dpi=150, bbox_inches='tight')

    print(f"\n✓ グラフ保存: SP1v14_preview.png")

    plt.close()

def main():
    print("=" * 80)
    print("SP1v14カーブ生成開始（スプライン補間版）")
    print("=" * 80)

    # Quad値作成
    v7_header, v14_quads, v7_quads = create_sp1v14_quads()

    # バンディングリスク解析
    print("\n[Step 2] バンディングリスク解析中...")
    v7_risks = analyze_banding_risk(v7_quads)
    v14_risks = analyze_banding_risk(v14_quads)

    print(f"✓ V7リスク箇所: {len(v7_risks)}箇所")
    print(f"✓ V14リスク箇所: {len(v14_risks)}箇所")

    # 新規追加されたリスク
    v7_risk_inputs = set([r[0] for r in v7_risks])
    v14_risk_inputs = set([r[0] for r in v14_risks])
    new_risks = v14_risk_inputs - v7_risk_inputs
    resolved_risks = v7_risk_inputs - v14_risk_inputs

    if new_risks:
        print(f"\n⚠️ V14で新たに追加されたリスク箇所: {len(new_risks)}箇所")
        for inp in sorted(new_risks)[:10]:
            for r in v14_risks:
                if r[0] == inp:
                    print(f"   Input {r[0]-1}→{r[0]}: Δ={r[1]} Quad")
                    break

    if resolved_risks:
        print(f"\n✓ V14で解消されたリスク箇所: {len(resolved_risks)}箇所")

    # グラフ生成
    print("\n[Step 3] 比較グラフを生成中...")
    plot_comparison(v7_quads, v14_quads)

    # ファイル出力
    print("\n[Step 4] Quadファイルを出力中...")
    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    quad_file = f"{base_path}/PX1V-PtPd-SP1v14.quad"

    write_quad_file(v14_quads, quad_file)
    print(f"✓ Quadファイル: PX1V-PtPd-SP1v14.quad")

    # サマリー
    print("\n" + "=" * 80)
    print("SP1v14カーブ生成完了")
    print("=" * 80)

    def quad_to_density(quad, max_density=1.73, max_quad=55891):
        return quad * max_density / max_quad

    print(f"\n【修正内容】")
    print(f"✓ Input 0-99: V7を+8シフト（シャドウを明るく）")
    print(f"✓ Input 100-210: スプライン補間（完全に滑らかな遷移）")
    print(f"✓ Input 211-247: V7を-8シフト（ハイライトを暗く）")
    print(f"✓ Input 248: {v14_quads[248]} Quad = {quad_to_density(v14_quads[248]):.2f}D（ハイライト表現域拡張）")
    print(f"✓ Input 249-254: リニア補間（248から255へ）")
    print(f"✓ Input 255: V7値（{v14_quads[255]} = {quad_to_density(v14_quads[255]):.2f}D）を使用")

    print(f"\n【バンディングリスク】")
    if len(new_risks) == 0:
        print(f"✓ 新たなリスク箇所なし")
    else:
        print(f"⚠️ 新たなリスク箇所: {len(new_risks)}箇所")

    if len(resolved_risks) > 0:
        print(f"✓ 解消されたリスク箇所: {len(resolved_risks)}箇所")

    print(f"\n【次のステップ】")
    print(f"1. グラフを確認してスプライン補間の滑らかさを評価")
    print(f"2. 問題なければQTRプリンタにインストール")
    print(f"3. テストプリントで実際の効果を確認")

if __name__ == "__main__":
    main()
