#!/usr/bin/env python3
"""
SP1v19カーブ生成スクリプト - ハイライト諧調拡張版（最終版）

修正方針:
V18をベースに、ハイライト部分（Input 224-255）の諧調を拡張
- Input 0-223: V18のまま（コントラスト削減効果を維持）
- Input 224-255: ハイライトストレッチ
  - 224 → V18[216] (0.92D)
  - 232 → V18[224] (0.99D)
  - 240 → V18[232] (1.06D)
  - 248 → V18[240] (1.12D)
  - 255 → 1.25D

目的:
- Kプリント（Pt/Pd）のK3-15%の諧調をしっかり表現
- ハイライトの細かい濃度変化を滑らかに再現
- 0.92D-1.25Dの範囲に32ステップを配置

実行日: 2026-03-19
作成者: Claude Code
"""

import numpy as np
import matplotlib.pyplot as plt

def read_quad_file(filename):
    """Quadファイルを読み込む"""
    with open(filename, 'r') as f:
        lines = f.readlines()

    quad_values = []
    for line in lines:
        line = line.strip()
        if line.isdigit():
            quad_values.append(int(line))

    return np.array(quad_values[:256])

def quad_to_density(quad, max_density=1.73, max_quad=55891):
    """Quad値を濃度に変換"""
    return quad * max_density / max_quad

def density_to_quad(density, max_density=1.73, max_quad=55891):
    """濃度をQuad値に変換"""
    return int(density * max_quad / max_density)

def create_sp1v19_quads():
    """SP1v19のQuad値配列を作成"""

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    v18_file = f"{base_path}/PX1V-PtPd-SP1v18.quad"

    print("[Step 1] Quad値配列を作成中...")
    v18_quads = read_quad_file(v18_file)

    print(f"✓ V18 Quadファイル読み込み: {len(v18_quads)}値")

    # V19を作成: Input 0-223はV18をコピー
    v19_quads = v18_quads.copy().astype(int)

    # Input 224-255: ハイライトストレッチ
    print(f"\n[Step 2] ハイライトストレッチ（Input 224-255）を適用中...")

    # アンカーポイント
    anchor_inputs = [224, 232, 240, 248, 255]
    anchor_quads = [
        v18_quads[216],   # 224 → V18[216]
        v18_quads[224],   # 232 → V18[224]
        v18_quads[232],   # 240 → V18[232]
        v18_quads[240],   # 248 → V18[240]
        density_to_quad(1.25)  # 255 → 1.25D
    ]

    print(f"\nアンカーポイント:")
    print(f"  Input 223 (V18): Quad={v18_quads[223]:5d}, Density={quad_to_density(v18_quads[223]):.4f}D")
    for inp, quad in zip(anchor_inputs, anchor_quads):
        dens = quad_to_density(quad)
        print(f"  Input {inp:3d} → Quad={quad:5d}, Density={dens:.4f}D")

    # 線形補間
    interp_inputs = np.arange(224, 256)
    interp_quads = np.interp(interp_inputs, anchor_inputs, anchor_quads).astype(int)

    # V19に適用
    v19_quads[224:256] = interp_quads

    # 単調増加を保証
    print(f"\n[Step 3] 単調増加を保証中...")
    violations_before = 0
    for i in range(1, 256):
        if v19_quads[i] <= v19_quads[i-1]:
            violations_before += 1
            v19_quads[i] = v19_quads[i-1] + 1

    print(f"✓ 修正箇所: {violations_before}箇所")

    # Input 220-235の詳細確認
    print(f"\n【Input 220-235の詳細確認】")
    print(f"{'Input':<8} {'V18 Quad':<10} {'V19 Quad':<10} {'Δ Quad':<10} {'V19 Density':<15}")
    print("-" * 70)

    for inp in range(220, 236):
        v18_q = v18_quads[inp]
        v19_q = v19_quads[inp]
        diff = v19_q - v18_q
        v19_d = quad_to_density(v19_q)

        marker = ""
        if inp >= 224:
            marker = " ← ストレッチ"

        print(f"{inp:<8} {v18_q:<10} {v19_q:<10} {diff:+10} {v19_d:.4f}D{marker}")

    # 全体の主要ポイント
    print(f"\n【主要ポイントの確認】")
    for inp in [0, 80, 120, 176, 220, 223, 224, 232, 240, 248, 255]:
        v18_q = v18_quads[inp]
        v19_q = v19_quads[inp]
        diff = v19_q - v18_q
        v19_d = quad_to_density(v19_q)

        marker = ""
        if inp >= 224:
            marker = " ← ストレッチ"

        print(f"  Input {inp:3d}: V18={v18_q:5d}, V19={v19_q:5d}, Δ={diff:+5d}, Density={v19_d:.4f}D{marker}")

    return v19_quads, v18_quads

def analyze_banding_risk(quads, threshold=200):
    """バンディングリスクを解析"""
    risks = []
    for inp in range(1, 256):
        diff = quads[inp] - quads[inp-1]
        if abs(diff) > threshold:
            risks.append((inp, diff))
    return risks

def write_quad_file(quads, filename):
    """Quadファイルを出力（正しい10チャンネル構造）"""

    with open(filename, 'w') as f:
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        f.write('# QuadProfile Version 2.8.0\n')
        f.write('# PX1V-PtPd-SP1v19 - Highlight tonal extension\n')
        f.write('# Input 0-223: V18 baseline (contrast reduction -0.05D)\n')
        f.write('# Input 224-255: Highlight stretch for smooth K3-15% gradation\n')
        f.write('#   224 → V18[216] (0.92D)\n')
        f.write('#   232 → V18[224] (0.99D)\n')
        f.write('#   240 → V18[232] (1.06D)\n')
        f.write('#   248 → V18[240] (1.12D)\n')
        f.write('#   255 → 1.25D\n')
        f.write('# Created: 2026-03-19 SP1v19\n')
        f.write('# Purpose: Expand highlight tonal range for Pt/Pd printing\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')
        f.write('# K curve\n')

        # チャンネル1: Kカーブ
        for quad in quads:
            f.write(f'{quad}\n')

        # チャンネル2-10: すべて0（各チャンネルにコメント行を追加）
        channels = ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']
        for channel in channels:
            f.write(f'# {channel} curve\n')
            for j in range(256):
                f.write('0\n')

def plot_comparison(v18_quads, v19_quads):
    """V18とV19の比較グラフを生成"""
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    inputs = np.arange(256)

    def quad_to_dens(quad):
        return quad * 1.73 / 55891

    # グラフ1: Quad値の比較
    ax1 = axes[0]
    ax1.plot(inputs, v18_quads, 'g-', label='V18 (Contrast reduced)', linewidth=2, alpha=0.7)
    ax1.plot(inputs, v19_quads, 'r-', label='V19 (Highlight extended)', linewidth=2)

    # ハイライトストレッチ範囲
    ax1.axvline(x=224, color='orange', linestyle='--', alpha=0.5, label='Stretch Start (224)')
    ax1.axvspan(224, 255, color='orange', alpha=0.1)

    ax1.set_xlabel('Input Value', fontsize=12)
    ax1.set_ylabel('Quad Value', fontsize=12)
    ax1.set_title('V18 vs V19 - Highlight Tonal Extension', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # グラフ2: 濃度比較（全体）
    ax2 = axes[1]
    v18_density = [quad_to_dens(q) for q in v18_quads]
    v19_density = [quad_to_dens(q) for q in v19_quads]

    ax2.plot(inputs, v18_density, 'g-', label='V18', linewidth=2, alpha=0.7)
    ax2.plot(inputs, v19_density, 'r-', label='V19', linewidth=2)

    ax2.axvline(x=224, color='orange', linestyle='--', alpha=0.5)
    ax2.axhspan(0.92, 1.25, color='orange', alpha=0.1, label='V19 Highlight Range')

    ax2.set_xlabel('Input Value', fontsize=12)
    ax2.set_ylabel('Density (D)', fontsize=12)
    ax2.set_title('Density Comparison', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # グラフ3: ハイライト部分の拡大（Input 200-255）
    ax3 = axes[2]
    highlight_inputs = np.arange(200, 256)
    v18_highlight = [quad_to_dens(v18_quads[i]) for i in highlight_inputs]
    v19_highlight = [quad_to_dens(v19_quads[i]) for i in highlight_inputs]

    ax3.plot(highlight_inputs, v18_highlight, 'g-s', label='V18', linewidth=2, markersize=3, alpha=0.7)
    ax3.plot(highlight_inputs, v19_highlight, 'r-^', label='V19', linewidth=2, markersize=3)

    ax3.axvline(x=224, color='orange', linestyle='--', alpha=0.5)
    ax3.axhline(y=0.92, color='red', linestyle=':', alpha=0.3, label='0.92D')
    ax3.axhline(y=1.25, color='red', linestyle=':', alpha=0.3, label='1.25D')

    ax3.set_xlabel('Input Value', fontsize=12)
    ax3.set_ylabel('Density (D)', fontsize=12)
    ax3.set_title('Highlight Detail (Input 200-255)', fontsize=14)
    ax3.set_xlim(200, 255)
    ax3.set_ylim(0.8, 1.4)
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    plt.savefig(f"{base_path}/SP1v19_preview.png", dpi=150, bbox_inches='tight')

    print(f"\n✓ グラフ保存: SP1v19_preview.png（上書き）")

    plt.close()

def main():
    print("=" * 80)
    print("SP1v19カーブ生成開始（ハイライト諧調拡張版・最終版）")
    print("=" * 80)

    # Quad値作成
    v19_quads, v18_quads = create_sp1v19_quads()

    # バンディングリスク解析
    print("\n[Step 4] バンディングリスク解析中...")
    v18_risks = analyze_banding_risk(v18_quads)
    v19_risks = analyze_banding_risk(v19_quads)

    print(f"✓ V18リスク箇所: {len(v18_risks)}箇所")
    print(f"✓ V19リスク箇所: {len(v19_risks)}箇所")

    # 新規追加されたリスク
    v18_risk_inputs = set([r[0] for r in v18_risks])
    v19_risk_inputs = set([r[0] for r in v19_risks])
    new_risks = v19_risk_inputs - v18_risk_inputs

    if new_risks:
        print(f"\n⚠️ V19で新たに追加されたリスク箇所: {len(new_risks)}箇所")
        for inp in sorted(new_risks)[:10]:
            for r in v19_risks:
                if r[0] == inp:
                    print(f"   Input {r[0]-1}→{r[0]}: Δ={r[1]} Quad")
                    break
    else:
        print(f"✓ 新たなリスク箇所なし")

    # グラフ生成
    print("\n[Step 5] 比較グラフを生成中...")
    plot_comparison(v18_quads, v19_quads)

    # ファイル出力
    print("\n[Step 6] Quadファイルを出力中...")
    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    quad_file = f"{base_path}/PX1V-PtPd-SP1v19.quad"

    write_quad_file(v19_quads, quad_file)
    print(f"✓ Quadファイル: PX1V-PtPd-SP1v19.quad（上書き）")

    # サマリー
    print("\n" + "=" * 80)
    print("SP1v19カーブ生成完了")
    print("=" * 80)

    print(f"\n【修正内容】")
    print(f"✓ Input 0-223: V18のまま（コントラスト削減-0.05D維持）")
    print(f"✓ Input 224-255: ハイライトストレッチ（0.92D-1.25D）")
    print(f"  - 224 → V18[216] (0.92D)")
    print(f"  - 232 → V18[224] (0.99D)")
    print(f"  - 240 → V18[232] (1.06D)")
    print(f"  - 248 → V18[240] (1.12D)")
    print(f"  - 255 → 1.25D")
    print(f"  - 32ステップで約0.33Dをカバー")
    print(f"  - 各ステップ約0.0103D")

    print(f"\n【期待される効果】")
    print(f"✓ Kプリント（Pt/Pd）のK3-15%の諧調を滑らかに表現")
    print(f"✓ ハイライトのディテール保持")
    print(f"✓ 紙白に近い領域の繊細な濃度変化を再現")

    print(f"\n【バンディングリスク】")
    if len(new_risks) == 0:
        print(f"✓ 新たなリスク箇所なし")
    else:
        print(f"⚠️ 新たなリスク箇所: {len(new_risks)}箇所")

    print(f"\n【次のステップ】")
    print(f"1. グラフを確認してハイライト部分の形状を評価")
    print(f"2. Input 220-235の濃度変化が滑らかか確認")
    print(f"3. 問題なければQTRプリンタにインストール")
    print(f"4. テストプリントでK3-15%の諧調を確認")

if __name__ == "__main__":
    main()
