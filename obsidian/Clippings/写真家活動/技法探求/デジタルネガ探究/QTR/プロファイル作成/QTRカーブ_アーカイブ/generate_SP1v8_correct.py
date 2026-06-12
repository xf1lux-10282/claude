#!/usr/bin/env python3
"""
SP1v8カーブ生成スクリプト - 正しい10チャンネル構造版

修正方針:
- SP1v7をベースに、シャドウ〜ミッドトーンのネガ濃度を上げる
- Input 0-192: ネガ濃度 +0.08-0.10D（Quad値を上げる）
- Input 192-255: SP1v7と同じ（露光レンジ維持）
- **10チャンネル構造で出力（Kチャンネルのみ有効、他は0）**

目的:
- プリント時の相対露光量が減り、コントラストが下がる
- インク量を適正に保つ（Kチャンネルのみ使用）

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

def create_sp1v8_quads():
    """SP1v8のQuad値配列を作成"""

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    v7_file = f"{base_path}/PX1V-PtPd-SP1v7.quad"

    print("[Step 1] Quad値配列を作成中...")
    v7_quads = read_quad_file(v7_file)

    print(f"✓ V7 Quadファイル読み込み: {len(v7_quads)}値")

    # V7をV8にコピー
    v8_quads = v7_quads.copy().astype(float)

    # Input 0-192: +0.08-0.10D（線形に変化）
    print(f"\n[Step 2] Input 0-192のネガ濃度を上げる...")
    for i in range(193):  # 0-192
        # Input 0で+0.10D、Input 192で+0.08D
        boost_density = 0.10 - (0.02 * i / 192)
        boost_quad = density_to_quad(boost_density)
        v8_quads[i] = v7_quads[i] + boost_quad

    # 65535を超えないようにクリップ
    v8_quads = np.clip(v8_quads, 0, 65535).astype(int)

    # 単調増加を保証
    print(f"\n[Step 3] 単調増加を保証中...")
    violations_before = 0
    for i in range(1, 256):
        if v8_quads[i] <= v8_quads[i-1]:
            violations_before += 1
            v8_quads[i] = v8_quads[i-1] + 1

    print(f"✓ 修正箇所: {violations_before}箇所")

    print(f"\n【主要ポイントの確認】")
    for inp in [0, 64, 96, 128, 160, 192, 220, 240, 248, 255]:
        diff = v8_quads[inp] - v7_quads[inp]
        print(f"  Input {inp:3d}: V7={v7_quads[inp]:5d} ({quad_to_density(v7_quads[inp]):.4f}D) → V8={v8_quads[inp]:5d} ({quad_to_density(v8_quads[inp]):.4f}D) [Δ={diff:+5d}]")

    return v8_quads, v7_quads

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
        f.write('# PX1V-PtPd-SP1v8 - Contrast reduction by negative density boost\n')
        f.write('# Input 0-192: Negative density +0.08-0.10D (boost Quad values)\n')
        f.write('# Input 192-255: V7 baseline (maintain exposure range)\n')
        f.write('# Created: 2026-03-19 SP1v8\n')
        f.write('# Purpose: Reduce print contrast by increasing negative density\n')
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

def plot_comparison(v7_quads, v8_quads):
    """V7とV8の比較グラフを生成"""
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    inputs = np.arange(256)

    # グラフ1: Quad値の比較
    ax1 = axes[0]
    ax1.plot(inputs, v7_quads, 'b-', label='V7 (Original)', linewidth=2, alpha=0.7)
    ax1.plot(inputs, v8_quads, 'r-', label='V8 (Softer)', linewidth=2)
    ax1.axvline(x=192, color='green', linestyle='--', alpha=0.5, label='Transition Point (192)')
    ax1.set_xlabel('Input Value')
    ax1.set_ylabel('Quad Value')
    ax1.set_title('V7 vs V8 - Negative Density Boost for Contrast Reduction', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # グラフ2: 濃度比較
    ax2 = axes[1]
    v7_density = [quad_to_density(q) for q in v7_quads]
    v8_density = [quad_to_density(q) for q in v8_quads]
    ax2.plot(inputs, v7_density, 'b-', label='V7', linewidth=2, alpha=0.7)
    ax2.plot(inputs, v8_density, 'r-', label='V8', linewidth=2)
    ax2.axvline(x=192, color='green', linestyle='--', alpha=0.5)
    ax2.set_xlabel('Input Value')
    ax2.set_ylabel('Density (D)')
    ax2.set_title('Density Comparison')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # グラフ3: 勾配比較
    ax3 = axes[2]
    v7_diff = np.diff(v7_quads)
    v8_diff = np.diff(v8_quads)
    ax3.plot(inputs[1:], v7_diff, 'b-', label='V7 Gradient', linewidth=1, alpha=0.7)
    ax3.plot(inputs[1:], v8_diff, 'r-', label='V8 Gradient', linewidth=1)
    ax3.axhline(y=200, color='red', linestyle='--', alpha=0.5, label='Banding Threshold')
    ax3.axhline(y=-200, color='red', linestyle='--', alpha=0.5)
    ax3.axvline(x=192, color='green', linestyle='--', alpha=0.5)
    ax3.set_xlabel('Input Value')
    ax3.set_ylabel('Quad Difference (Δ)')
    ax3.set_title('Gradient Comparison')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    plt.savefig(f"{base_path}/SP1v8_preview.png", dpi=150, bbox_inches='tight')

    print(f"\n✓ グラフ保存: SP1v8_preview.png")

    plt.close()

def main():
    print("=" * 80)
    print("SP1v8カーブ生成開始（正しい10チャンネル構造版）")
    print("=" * 80)

    # Quad値作成
    v8_quads, v7_quads = create_sp1v8_quads()

    # バンディングリスク解析
    print("\n[Step 4] バンディングリスク解析中...")
    v7_risks = analyze_banding_risk(v7_quads)
    v8_risks = analyze_banding_risk(v8_quads)

    print(f"✓ V7リスク箇所: {len(v7_risks)}箇所")
    print(f"✓ V8リスク箇所: {len(v8_risks)}箇所")

    # 新規追加されたリスク
    v7_risk_inputs = set([r[0] for r in v7_risks])
    v8_risk_inputs = set([r[0] for r in v8_risks])
    new_risks = v8_risk_inputs - v7_risk_inputs

    if new_risks:
        print(f"\n⚠️ V8で新たに追加されたリスク箇所: {len(new_risks)}箇所")
        for inp in sorted(new_risks)[:10]:
            for r in v8_risks:
                if r[0] == inp:
                    print(f"   Input {r[0]-1}→{r[0]}: Δ={r[1]} Quad")
                    break

    # グラフ生成
    print("\n[Step 5] 比較グラフを生成中...")
    plot_comparison(v7_quads, v8_quads)

    # ファイル出力
    print("\n[Step 6] Quadファイルを出力中...")
    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    quad_file = f"{base_path}/PX1V-PtPd-SP1v8.quad"

    write_quad_file(v8_quads, quad_file)
    print(f"✓ Quadファイル: PX1V-PtPd-SP1v8.quad")

    # サマリー
    print("\n" + "=" * 80)
    print("SP1v8カーブ生成完了")
    print("=" * 80)

    print(f"\n【修正内容】")
    print(f"✓ Input 0-192: ネガ濃度+0.08-0.10D（シャドウ〜ミッドトーン軟調化）")
    print(f"✓ Input 192-255: V7と同じ（露光レンジ維持）")
    print(f"✓ 10チャンネル構造で出力（Kチャンネルのみ有効）")

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
