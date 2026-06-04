#!/usr/bin/env python3
"""
SP1v12カーブ生成スクリプト

修正方針:
V7をベースに、コントラストを下げる
1. Input 0-128: V7を+8シフト（濃度を上げる → プリント時シャドウが明るくなる）
2. Input 129-183: V7のまま維持（中間調を保持）
3. Input 184-248: V7を-8シフト（濃度を下げる → プリント時ハイライトが暗くなる）
4. Input 249-254: リニア補間（248から255へ滑らかに接続）
5. Input 255: V7のまま維持（1.73D、完全遮光）

目的:
- V7で得られた良好な結果を維持しつつ、コントラストを下げる
- シャドウを明るく、ハイライトを暗くすることで全体的に階調を均等化

実行日: 2026-03-18
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

def create_sp1v12_quads():
    """SP1v12のQuad値配列を作成"""

    # ファイルパス
    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"

    v7_file = f"{base_path}/PX1V-PtPd-SP1v7.quad"

    # Quadファイルを読み込み
    print("[Step 1] Quad値配列を作成中...")
    v7_header, v7_quads = read_quad_file(v7_file)

    print(f"✓ V7 Quadファイル読み込み: {len(v7_quads)}値")

    # V7をベースにコピー
    v12_quads = v7_quads.copy()

    # Input 0-128: V7を+8シフト（濃度を上げる）
    print(f"\n[1] Input 0-128: V7を+8シフト（濃度を上げる）")

    for inp in range(0, 129):
        source_input = inp + 8
        if source_input <= 255:
            v12_quads[inp] = v7_quads[source_input]
        else:
            # 範囲外の場合はV7のまま
            v12_quads[inp] = v7_quads[inp]

    def quad_to_density(quad, max_density=1.73, max_quad=55891):
        return quad * max_density / max_quad

    print(f"   Input 0: {v12_quads[0]} Quad ({quad_to_density(v12_quads[0]):.4f}D)")
    print(f"   Input 64: {v12_quads[64]} Quad ({quad_to_density(v12_quads[64]):.4f}D)")
    print(f"   Input 128: {v12_quads[128]} Quad ({quad_to_density(v12_quads[128]):.4f}D)")

    # Input 129-183: V7のまま維持
    print(f"\n[2] Input 129-183: V7のまま維持（中間調を保持）")

    # Input 184-248: V7を-8シフト（濃度を下げる）
    print(f"\n[3] Input 184-248: V7を-8シフト（濃度を下げる）")

    for inp in range(184, 249):
        source_input = inp - 8
        if source_input >= 0:
            v12_quads[inp] = v7_quads[source_input]
        else:
            # 範囲外の場合はV7のまま
            v12_quads[inp] = v7_quads[inp]

    print(f"   Input 184: {v12_quads[184]} Quad ({quad_to_density(v12_quads[184]):.4f}D)")
    print(f"   Input 216: {v12_quads[216]} Quad ({quad_to_density(v12_quads[216]):.4f}D)")
    print(f"   Input 248: {v12_quads[248]} Quad ({quad_to_density(v12_quads[248]):.4f}D)")

    # Input 249-254: リニア補間（248から255へ）
    print(f"\n[4] Input 249-254: リニア補間（248から255へ）")

    start_input_249 = 248
    end_input_249 = 255
    start_quad_249 = v12_quads[248]
    end_quad_249 = v7_quads[255]  # 1.73D

    for inp in range(249, 255):
        ratio = (inp - start_input_249) / (end_input_249 - start_input_249)
        v12_quads[inp] = int(start_quad_249 + (end_quad_249 - start_quad_249) * ratio)

    # Input 255: V7のまま
    print(f"\n[5] Input 255: V7のまま維持（1.73D）")
    v12_quads[255] = v7_quads[255]

    print(f"   Input 255: {v12_quads[255]} Quad ({quad_to_density(v12_quads[255]):.4f}D)")

    return v7_header, v12_quads, v7_quads

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
        f.write('# PX1V-PtPd-SP1v12 - Contrast reduction curve based on V7\n')
        f.write('# Input 0-128: V7 shifted by +8 steps (increase shadow density)\n')
        f.write('# Input 129-183: V7 baseline (midtones preserved)\n')
        f.write('# Input 184-248: V7 shifted by -8 steps (decrease highlight density)\n')
        f.write('# Input 249-254: Linear interpolation from 248 to 255\n')
        f.write('# Input 255: V7[255] value (1.73D - complete opacity)\n')
        f.write('# Created: 2026-03-18 SP1v12\n')
        f.write('# Purpose: Reduce contrast - brighter shadows, darker highlights\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')
        f.write('# K curve\n')

        # 2560値を出力（最初の256値を10回繰り返し）
        for i in range(10):
            for quad in quads:
                f.write(f'{quad}\n')

def plot_comparison(v7_quads, v12_quads):
    """V7とV12の比較グラフを生成"""
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    inputs = np.arange(256)

    def quad_to_density(quad):
        return quad * 1.73 / 55891

    # グラフ1: 全体比較
    ax1 = axes[0]
    ax1.plot(inputs, v7_quads, 'b-', label='V7', linewidth=2)
    ax1.plot(inputs, v12_quads, 'r-', label='V12 (Contrast Reduced)', linewidth=2)
    ax1.axvline(x=128, color='orange', linestyle='--', alpha=0.5, label='Shift Boundary')
    ax1.axvline(x=184, color='green', linestyle='--', alpha=0.5)
    ax1.set_xlabel('Input Value')
    ax1.set_ylabel('Quad Value')
    ax1.set_title('V7 vs V12 Quad Values - Contrast Reduction')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # グラフ2: 濃度比較
    ax2 = axes[1]
    v7_density = [quad_to_density(q) for q in v7_quads]
    v12_density = [quad_to_density(q) for q in v12_quads]
    ax2.plot(inputs, v7_density, 'b-', label='V7', linewidth=2)
    ax2.plot(inputs, v12_density, 'r-', label='V12', linewidth=2)
    ax2.axvline(x=128, color='orange', linestyle='--', alpha=0.5)
    ax2.axvline(x=184, color='green', linestyle='--', alpha=0.5)
    ax2.axhline(y=1.25, color='red', linestyle=':', alpha=0.5, label='Paper White Limit (1.25D)')
    ax2.set_xlabel('Input Value')
    ax2.set_ylabel('Density (D)')
    ax2.set_title('Density Comparison')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # グラフ3: 差分比較
    ax3 = axes[2]
    v7_diff = np.diff(v7_quads)
    v12_diff = np.diff(v12_quads)
    ax3.plot(inputs[1:], v7_diff, 'b-', label='V7 Gradient', linewidth=1)
    ax3.plot(inputs[1:], v12_diff, 'r-', label='V12 Gradient', linewidth=1)
    ax3.axhline(y=200, color='red', linestyle='--', alpha=0.5, label='Banding Threshold')
    ax3.axhline(y=-200, color='red', linestyle='--', alpha=0.5)
    ax3.axvline(x=128, color='orange', linestyle='--', alpha=0.5)
    ax3.axvline(x=184, color='green', linestyle='--', alpha=0.5)
    ax3.set_xlabel('Input Value')
    ax3.set_ylabel('Quad Difference (Δ)')
    ax3.set_title('Gradient Comparison')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    plt.savefig(f"{base_path}/SP1v12_preview.png", dpi=150, bbox_inches='tight')

    print(f"\n✓ グラフ保存: SP1v12_preview.png")

    plt.close()

def main():
    print("=" * 80)
    print("SP1v12カーブ生成開始")
    print("=" * 80)

    # Quad値作成
    v7_header, v12_quads, v7_quads = create_sp1v12_quads()

    # バンディングリスク解析
    print("\n[Step 2] バンディングリスク解析中...")
    v7_risks = analyze_banding_risk(v7_quads)
    v12_risks = analyze_banding_risk(v12_quads)

    print(f"✓ V7リスク箇所: {len(v7_risks)}箇所")
    print(f"✓ V12リスク箇所: {len(v12_risks)}箇所")

    # 新規追加されたリスク
    v7_risk_inputs = set([r[0] for r in v7_risks])
    v12_risk_inputs = set([r[0] for r in v12_risks])
    new_risks = v12_risk_inputs - v7_risk_inputs

    if new_risks:
        print(f"\n⚠️ V12で新たに追加されたリスク箇所: {len(new_risks)}箇所")
        for inp in sorted(new_risks)[:10]:
            for r in v12_risks:
                if r[0] == inp:
                    print(f"   Input {r[0]-1}→{r[0]}: Δ={r[1]} Quad")
                    break

    # グラフ生成
    print("\n[Step 3] 比較グラフを生成中...")
    plot_comparison(v7_quads, v12_quads)

    # ファイル出力
    print("\n[Step 4] Quadファイルを出力中...")
    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    quad_file = f"{base_path}/PX1V-PtPd-SP1v12.quad"

    write_quad_file(v12_quads, quad_file)
    print(f"✓ Quadファイル: PX1V-PtPd-SP1v12.quad")

    # サマリー
    print("\n" + "=" * 80)
    print("SP1v12カーブ生成完了")
    print("=" * 80)

    def quad_to_density(quad, max_density=1.73, max_quad=55891):
        return quad * max_density / max_quad

    print(f"\n【修正内容】")
    print(f"✓ Input 0-128: V7を+8シフト（シャドウ濃度を上げる）")
    print(f"✓ Input 129-183: V7のまま維持（中間調を保持）")
    print(f"✓ Input 184-248: V7を-8シフト（ハイライト濃度を下げる）")
    print(f"✓ Input 249-254: リニア補間（248から255へ）")
    print(f"✓ Input 255: V7値（{v12_quads[255]} = {quad_to_density(v12_quads[255]):.2f}D）を使用")

    print(f"\n【バンディングリスク】")
    if len(new_risks) == 0:
        print(f"✓ 新たなリスク箇所なし")
    else:
        print(f"⚠️ 新たなリスク箇所: {len(new_risks)}箇所（要確認）")

    print(f"\n【次のステップ】")
    print(f"1. グラフを確認してバンディングリスクを評価")
    print(f"2. 問題なければQTRプリンタにインストール")
    print(f"3. テストプリントで実際の効果を確認")

if __name__ == "__main__":
    main()
