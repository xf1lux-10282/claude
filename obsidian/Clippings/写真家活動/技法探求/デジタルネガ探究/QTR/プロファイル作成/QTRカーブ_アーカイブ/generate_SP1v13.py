#!/usr/bin/env python3
"""
SP1v13カーブ生成スクリプト

修正方針:
V7をベースに、コサインカーブでシフト量を滑らかに変化させる
1. Input 0-119: V7を+8シフト（固定）
2. Input 120-192: シフト量を+8から-8まで滑らかに変化（コサインカーブ）
3. Input 193-248: V7を-8シフト（固定）
4. Input 249-254: リニア補間（248から255へ）
5. Input 255: V7のまま維持（1.73D、完全遮光）

目的:
- V7で得られた良好な結果を維持しつつ、コントラストを下げる
- 段差のない滑らかな遷移を実現
- バンディングリスクを最小化

実行日: 2026-03-19
作成者: Claude Code
"""

import numpy as np
import matplotlib.pyplot as plt

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

def calculate_shift_amount(inp, start=120, end=192):
    """
    Input 120-192でシフト量を+8から-8まで滑らかに変化させる
    コサインカーブを使用して滑らかな遷移を実現
    """
    if inp < start:
        return 8
    elif inp > end:
        return -8
    else:
        # 0から1までの正規化された位置
        t = (inp - start) / (end - start)

        # コサインカーブで+8から-8まで変化
        # cos(0) = 1 → shift = +8
        # cos(π) = -1 → shift = -8
        shift = 8 * np.cos(t * np.pi)

        return shift

def create_sp1v13_quads():
    """SP1v13のQuad値配列を作成"""

    # ファイルパス
    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"

    v7_file = f"{base_path}/PX1V-PtPd-SP1v7.quad"

    # Quadファイルを読み込み
    print("[Step 1] Quad値配列を作成中...")
    v7_header, v7_quads = read_quad_file(v7_file)

    print(f"✓ V7 Quadファイル読み込み: {len(v7_quads)}値")

    # V13をベースに作成
    v13_quads = np.zeros(256, dtype=int)

    # 全てのInputに対してシフト量を計算して適用
    print(f"\n[1] Input 0-255: コサインカーブによる滑らかなシフトを適用")

    for inp in range(256):
        shift = calculate_shift_amount(inp)
        source_input = int(inp + shift)

        # 範囲チェック
        if source_input < 0:
            source_input = 0
        elif source_input > 255:
            source_input = 255

        v13_quads[inp] = v7_quads[source_input]

    def quad_to_density(quad, max_density=1.73, max_quad=55891):
        return quad * max_density / max_quad

    print(f"   Input 0: {v13_quads[0]} Quad ({quad_to_density(v13_quads[0]):.4f}D) [shift: +8]")
    print(f"   Input 64: {v13_quads[64]} Quad ({quad_to_density(v13_quads[64]):.4f}D) [shift: +8]")
    print(f"   Input 120: {v13_quads[120]} Quad ({quad_to_density(v13_quads[120]):.4f}D) [shift: +8]")
    print(f"   Input 156: {v13_quads[156]} Quad ({quad_to_density(v13_quads[156]):.4f}D) [shift: 0]")
    print(f"   Input 192: {v13_quads[192]} Quad ({quad_to_density(v13_quads[192]):.4f}D) [shift: -8]")
    print(f"   Input 216: {v13_quads[216]} Quad ({quad_to_density(v13_quads[216]):.4f}D) [shift: -8]")
    print(f"   Input 248: {v13_quads[248]} Quad ({quad_to_density(v13_quads[248]):.4f}D) [shift: -8]")

    # Input 249-254: リニア補間（248から255へ）
    print(f"\n[2] Input 249-254: リニア補間（248から255へ）")

    start_input_249 = 248
    end_input_249 = 255
    start_quad_249 = v13_quads[248]
    end_quad_249 = v7_quads[255]  # 1.73D

    for inp in range(249, 255):
        ratio = (inp - start_input_249) / (end_input_249 - start_input_249)
        v13_quads[inp] = int(start_quad_249 + (end_quad_249 - start_quad_249) * ratio)

    # Input 255: V7のまま
    print(f"\n[3] Input 255: V7のまま維持（1.73D）")
    v13_quads[255] = v7_quads[255]

    print(f"   Input 255: {v13_quads[255]} Quad ({quad_to_density(v13_quads[255]):.4f}D)")

    return v7_header, v13_quads, v7_quads

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
        f.write('# PX1V-PtPd-SP1v13 - Smooth contrast reduction with cosine curve\n')
        f.write('# Input 0-119: V7 shifted by +8 steps (fixed)\n')
        f.write('# Input 120-192: Smooth shift transition using cosine curve (+8 to -8)\n')
        f.write('# Input 193-248: V7 shifted by -8 steps (fixed)\n')
        f.write('# Input 249-254: Linear interpolation from 248 to 255\n')
        f.write('# Input 255: V7[255] value (1.73D - complete opacity)\n')
        f.write('# Created: 2026-03-19 SP1v13\n')
        f.write('# Purpose: Smooth contrast reduction - no banding\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')
        f.write('# K curve\n')

        # 2560値を出力（最初の256値を10回繰り返し）
        for i in range(10):
            for quad in quads:
                f.write(f'{quad}\n')

def plot_comparison(v7_quads, v13_quads):
    """V7とV13の比較グラフを生成"""
    fig, axes = plt.subplots(4, 1, figsize=(14, 14))

    inputs = np.arange(256)

    def quad_to_density(quad):
        return quad * 1.73 / 55891

    # グラフ1: 全体比較
    ax1 = axes[0]
    ax1.plot(inputs, v7_quads, 'b-', label='V7 (Original)', linewidth=2, alpha=0.7)
    ax1.plot(inputs, v13_quads, 'r-', label='V13 (Smooth Shift)', linewidth=2)
    ax1.axvline(x=120, color='orange', linestyle='--', alpha=0.5, label='Shift Start (120)')
    ax1.axvline(x=156, color='purple', linestyle=':', alpha=0.5, label='Midpoint (156)')
    ax1.axvline(x=192, color='green', linestyle='--', alpha=0.5, label='Shift End (192)')
    ax1.set_xlabel('Input Value')
    ax1.set_ylabel('Quad Value')
    ax1.set_title('V7 vs V13 Quad Values - Smooth Contrast Reduction', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # グラフ2: 濃度比較
    ax2 = axes[1]
    v7_density = [quad_to_density(q) for q in v7_quads]
    v13_density = [quad_to_density(q) for q in v13_quads]
    ax2.plot(inputs, v7_density, 'b-', label='V7', linewidth=2, alpha=0.7)
    ax2.plot(inputs, v13_density, 'r-', label='V13', linewidth=2)
    ax2.axvline(x=120, color='orange', linestyle='--', alpha=0.5)
    ax2.axvline(x=156, color='purple', linestyle=':', alpha=0.5)
    ax2.axvline(x=192, color='green', linestyle='--', alpha=0.5)
    ax2.axhline(y=1.25, color='red', linestyle=':', alpha=0.5, label='Paper White Limit (1.25D)')
    ax2.set_xlabel('Input Value')
    ax2.set_ylabel('Density (D)')
    ax2.set_title('Density Comparison')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # グラフ3: 差分比較（全体）
    ax3 = axes[2]
    v7_diff = np.diff(v7_quads)
    v13_diff = np.diff(v13_quads)
    ax3.plot(inputs[1:], v7_diff, 'b-', label='V7 Gradient', linewidth=1, alpha=0.7)
    ax3.plot(inputs[1:], v13_diff, 'r-', label='V13 Gradient', linewidth=1)
    ax3.axhline(y=200, color='red', linestyle='--', alpha=0.5, label='Banding Threshold')
    ax3.axhline(y=-200, color='red', linestyle='--', alpha=0.5)
    ax3.axvline(x=120, color='orange', linestyle='--', alpha=0.5)
    ax3.axvline(x=156, color='purple', linestyle=':', alpha=0.5)
    ax3.axvline(x=192, color='green', linestyle='--', alpha=0.5)
    ax3.set_xlabel('Input Value')
    ax3.set_ylabel('Quad Difference (Δ)')
    ax3.set_title('Gradient Comparison - Full Range')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # グラフ4: Input 110-200の拡大図
    ax4 = axes[3]
    zoom_range = range(110, 201)
    ax4.plot([i for i in zoom_range], [v7_quads[i] for i in zoom_range],
             'b-', label='V7', linewidth=2, alpha=0.7)
    ax4.plot([i for i in zoom_range], [v13_quads[i] for i in zoom_range],
             'r-', label='V13', linewidth=2)
    ax4.axvline(x=120, color='orange', linestyle='--', alpha=0.5, label='Shift Start')
    ax4.axvline(x=156, color='purple', linestyle=':', alpha=0.5, label='Midpoint')
    ax4.axvline(x=192, color='green', linestyle='--', alpha=0.5, label='Shift End')
    ax4.set_xlabel('Input Value')
    ax4.set_ylabel('Quad Value')
    ax4.set_title('Detail: Input 110-200 (Transition Zone)', fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    plt.savefig(f"{base_path}/SP1v13_preview.png", dpi=150, bbox_inches='tight')

    print(f"\n✓ グラフ保存: SP1v13_preview.png")

    plt.close()

def main():
    print("=" * 80)
    print("SP1v13カーブ生成開始")
    print("=" * 80)

    # Quad値作成
    v7_header, v13_quads, v7_quads = create_sp1v13_quads()

    # バンディングリスク解析
    print("\n[Step 2] バンディングリスク解析中...")
    v7_risks = analyze_banding_risk(v7_quads)
    v13_risks = analyze_banding_risk(v13_quads)

    print(f"✓ V7リスク箇所: {len(v7_risks)}箇所")
    print(f"✓ V13リスク箇所: {len(v13_risks)}箇所")

    # 新規追加されたリスク
    v7_risk_inputs = set([r[0] for r in v7_risks])
    v13_risk_inputs = set([r[0] for r in v13_risks])
    new_risks = v13_risk_inputs - v7_risk_inputs
    resolved_risks = v7_risk_inputs - v13_risk_inputs

    if new_risks:
        print(f"\n⚠️ V13で新たに追加されたリスク箇所: {len(new_risks)}箇所")
        for inp in sorted(new_risks)[:10]:
            for r in v13_risks:
                if r[0] == inp:
                    print(f"   Input {r[0]-1}→{r[0]}: Δ={r[1]} Quad")
                    break

    if resolved_risks:
        print(f"\n✓ V13で解消されたリスク箇所: {len(resolved_risks)}箇所")

    # グラフ生成
    print("\n[Step 3] 比較グラフを生成中...")
    plot_comparison(v7_quads, v13_quads)

    # ファイル出力
    print("\n[Step 4] Quadファイルを出力中...")
    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    quad_file = f"{base_path}/PX1V-PtPd-SP1v13.quad"

    write_quad_file(v13_quads, quad_file)
    print(f"✓ Quadファイル: PX1V-PtPd-SP1v13.quad")

    # サマリー
    print("\n" + "=" * 80)
    print("SP1v13カーブ生成完了")
    print("=" * 80)

    def quad_to_density(quad, max_density=1.73, max_quad=55891):
        return quad * max_density / max_quad

    print(f"\n【修正内容】")
    print(f"✓ Input 0-119: V7を+8シフト（固定）")
    print(f"✓ Input 120-192: コサインカーブで+8から-8まで滑らかに変化")
    print(f"✓ Input 193-248: V7を-8シフト（固定）")
    print(f"✓ Input 249-254: リニア補間（248から255へ）")
    print(f"✓ Input 255: V7値（{v13_quads[255]} = {quad_to_density(v13_quads[255]):.2f}D）を使用")

    print(f"\n【バンディングリスク】")
    if len(new_risks) == 0:
        print(f"✓ 新たなリスク箇所なし")
    else:
        print(f"⚠️ 新たなリスク箇所: {len(new_risks)}箇所")

    if len(resolved_risks) > 0:
        print(f"✓ 解消されたリスク箇所: {len(resolved_risks)}箇所")

    print(f"\n【次のステップ】")
    print(f"1. グラフを確認して遷移の滑らかさを評価")
    print(f"2. 問題なければQTRプリンタにインストール")
    print(f"3. テストプリントで実際の効果を確認")

if __name__ == "__main__":
    main()
