#!/usr/bin/env python3
"""
SP1v8カーブ生成スクリプト - コントラスト軟調化版

設計方針:
- SP1v7をベースに、シャドウ〜ミッドトーンのネガ濃度を上げる
- Input 0-192: ネガ濃度 +0.08-0.10D（Quad値を上げる）
- Input 192-255: SP1v7と同じ（露光レンジ維持）
- 結果: プリント時の相対露光量が減り、コントラストが下がる

実行日: 2026-03-18
作成者: Claude Code
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline

# SP1v7のQuad値データ
sp1v7_data = {
    0: 0, 8: 227, 16: 1314, 24: 1966, 32: 3010, 40: 4054, 48: 5097, 56: 6098,
    64: 7149, 72: 7840, 80: 8909, 88: 10384, 96: 11384, 104: 12664, 112: 13773,
    120: 14795, 128: 15882, 136: 17683, 144: 18625, 152: 19716, 160: 21112,
    168: 22459, 176: 23927, 184: 25654, 192: 26832,
    200: 28264, 208: 29622, 216: 31339, 224: 33583, 232: 35756, 240: 36962,
    248: 38496, 255: 55891
}

def density_to_quad(density):
    """濃度値をQuad値に変換（0.0D=0, 4.0D=65535）"""
    return int(density * 65535 / 4.0)

def quad_to_density(quad):
    """Quad値を濃度値に変換"""
    return quad * 4.0 / 65535

def generate_sp1v8():
    """SP1v8カーブを生成"""

    # SP1v7の濃度を計算
    sp1v7_densities = {inp: quad_to_density(quad) for inp, quad in sp1v7_data.items()}

    # SP1v8の濃度を計算
    sp1v8_densities = {}

    for inp in range(256):
        if inp in sp1v7_densities:
            sp1v7_d = sp1v7_densities[inp]
        else:
            # 補間
            inputs = sorted(sp1v7_densities.keys())
            densities = [sp1v7_densities[i] for i in inputs]
            sp1v7_d = np.interp(inp, inputs, densities)

        # Input 0-192: +0.08-0.10D (線形に変化)
        # Input 192-255: 変更なし
        if inp <= 192:
            # Input 0で+0.10D、Input 192で+0.08D
            boost = 0.10 - (0.02 * inp / 192)
            sp1v8_d = sp1v7_d + boost
        else:
            # Input 192-255: SP1v7と同じ
            sp1v8_d = sp1v7_d

        sp1v8_densities[inp] = sp1v8_d

    # Quad値に変換
    sp1v8_quads = {inp: density_to_quad(d) for inp, d in sp1v8_densities.items()}

    # 65535を超えないようにクリップ
    sp1v8_quads = {inp: min(65535, quad) for inp, quad in sp1v8_quads.items()}

    return sp1v8_quads, sp1v8_densities

def smooth_quad_curve(quad_dict):
    """Quadカーブをスムーズにする（境界線リスク軽減）"""
    inputs = sorted(quad_dict.keys())
    quads = [quad_dict[i] for i in inputs]

    # スプライン補間
    cs = CubicSpline(inputs, quads)

    smoothed = {}
    for inp in range(256):
        smoothed[inp] = int(cs(inp))
        smoothed[inp] = max(0, min(65535, smoothed[inp]))  # クリップ

    return smoothed

def analyze_banding_risk(quad_dict, threshold=200):
    """境界線リスクを解析"""
    risks = []
    for inp in range(1, 256):
        diff = quad_dict[inp] - quad_dict[inp-1]
        if diff > threshold:
            risks.append((inp, diff))
    return risks

def write_quad_file(quad_dict, filename):
    """QTR .quadファイルを出力"""
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

        for inp in range(256):
            f.write(f'{quad_dict[inp]}\n')

def write_detail_csv(sp1v7_quads, sp1v8_quads, sp1v7_densities, sp1v8_densities, filename):
    """詳細データをCSV出力"""
    data = []
    for inp in range(256):
        sp1v7_q = sp1v7_quads.get(inp, 0)
        sp1v8_q = sp1v8_quads.get(inp, 0)
        sp1v7_d = sp1v7_densities.get(inp, 0)
        sp1v8_d = sp1v8_densities.get(inp, 0)

        data.append({
            'Input': inp,
            'SP1v7_Quad': sp1v7_q,
            'SP1v8_Quad': sp1v8_q,
            'Quad_Change': sp1v8_q - sp1v7_q,
            'SP1v7_Density': f'{sp1v7_d:.6f}',
            'SP1v8_Density': f'{sp1v8_d:.6f}',
            'Density_Boost': f'{sp1v8_d - sp1v7_d:.6f}'
        })

    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    return df

def plot_analysis(sp1v7_quads, sp1v8_quads, sp1v7_densities, sp1v8_densities, filename):
    """解析グラフを生成"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    inputs = range(256)

    # Quadカーブ比較
    ax = axes[0, 0]
    sp1v7_q_list = [sp1v7_quads.get(i, 0) for i in inputs]
    sp1v8_q_list = [sp1v8_quads.get(i, 0) for i in inputs]
    ax.plot(inputs, sp1v7_q_list, label='SP1v7', linewidth=2)
    ax.plot(inputs, sp1v8_q_list, label='SP1v8 (Softer)', linewidth=2)
    ax.set_xlabel('Input Value (0-255)')
    ax.set_ylabel('Quad Value (0-65535)')
    ax.set_title('Quad Curve Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 濃度カーブ比較
    ax = axes[0, 1]
    sp1v7_d_list = [sp1v7_densities.get(i, 0) for i in inputs]
    sp1v8_d_list = [sp1v8_densities.get(i, 0) for i in inputs]
    ax.plot(inputs, sp1v7_d_list, label='SP1v7', linewidth=2)
    ax.plot(inputs, sp1v8_d_list, label='SP1v8 (Softer)', linewidth=2)
    ax.set_xlabel('Input Value (0-255)')
    ax.set_ylabel('Negative Density (D)')
    ax.set_title('Density Curve Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Quad勾配（境界線リスク）
    ax = axes[1, 0]
    sp1v7_diffs = [sp1v7_q_list[i] - sp1v7_q_list[i-1] for i in range(1, 256)]
    sp1v8_diffs = [sp1v8_q_list[i] - sp1v8_q_list[i-1] for i in range(1, 256)]
    ax.plot(range(1, 256), sp1v7_diffs, label='SP1v7', alpha=0.7)
    ax.plot(range(1, 256), sp1v8_diffs, label='SP1v8', alpha=0.7)
    ax.axhline(y=200, color='red', linestyle='--', label='Banding Risk (>200)')
    ax.set_xlabel('Input Value (1-255)')
    ax.set_ylabel('Quad Difference (Δ)')
    ax.set_title('Quad Gradient (Banding Risk)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 300)

    # 濃度ブースト量
    ax = axes[1, 1]
    density_boost = [sp1v8_d_list[i] - sp1v7_d_list[i] for i in inputs]
    ax.plot(inputs, density_boost, linewidth=2, color='green')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.axvline(x=192, color='red', linestyle='--', label='Transition Point (192)')
    ax.set_xlabel('Input Value (0-255)')
    ax.set_ylabel('Density Boost (D)')
    ax.set_title('Density Boost Amount (SP1v8 - SP1v7)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"✓ 解析グラフ保存: {filename}")

def main():
    print("=" * 60)
    print("SP1v8カーブ生成開始 - コントラスト軟調化版")
    print("=" * 60)

    # SP1v8生成
    print("\n[1] SP1v8カーブ計算中...")
    sp1v8_quads_raw, sp1v8_densities = generate_sp1v8()

    # スムーズ化
    print("[2] Quadカーブをスムーズ化中...")
    sp1v8_quads = smooth_quad_curve(sp1v8_quads_raw)

    # SP1v7のQuad値を全Input用に補間
    sp1v7_quads_full = {}
    sp1v7_densities_full = {}
    inputs_ref = sorted(sp1v7_data.keys())
    quads_ref = [sp1v7_data[i] for i in inputs_ref]

    for inp in range(256):
        sp1v7_quads_full[inp] = int(np.interp(inp, inputs_ref, quads_ref))
        sp1v7_densities_full[inp] = quad_to_density(sp1v7_quads_full[inp])

    # 境界線リスク解析
    print("[3] 境界線リスク解析中...")
    sp1v7_risks = analyze_banding_risk(sp1v7_quads_full)
    sp1v8_risks = analyze_banding_risk(sp1v8_quads)

    print(f"\n【境界線リスク（Quad差分 > 200）】")
    print(f"SP1v7: {len(sp1v7_risks)}箇所")
    if sp1v7_risks:
        for inp, diff in sp1v7_risks[:5]:
            print(f"  - Input {inp}: Δ={diff}")

    print(f"\nSP1v8: {len(sp1v8_risks)}箇所")
    if sp1v8_risks:
        for inp, diff in sp1v8_risks[:5]:
            print(f"  - Input {inp}: Δ={diff}")

    # ファイル出力
    print("\n[4] ファイル出力中...")
    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"

    # .quadファイル
    quad_file = f"{base_path}/PX1V-PtPd-SP1v8.quad"
    write_quad_file(sp1v8_quads, quad_file)
    print(f"✓ Quadファイル: PX1V-PtPd-SP1v8.quad")

    # 詳細CSV
    csv_file = f"{base_path}/PX1V-PtPd-SP1v8.txt"
    df = write_detail_csv(sp1v7_quads_full, sp1v8_quads, sp1v7_densities_full, sp1v8_densities, csv_file)
    print(f"✓ 詳細データ: PX1V-PtPd-SP1v8.txt")

    # 解析グラフ
    graph_file = f"{base_path}/SP1v8_softer_analysis.png"
    plot_analysis(sp1v7_quads_full, sp1v8_quads, sp1v7_densities_full, sp1v8_densities, graph_file)

    # サマリー
    print("\n" + "=" * 60)
    print("SP1v8カーブ生成完了")
    print("=" * 60)
    print(f"\n【主要ポイント濃度比較】")
    print(f"{'Input':<8} {'SP1v7 (D)':<12} {'SP1v8 (D)':<12} {'Boost':<10}")
    print("-" * 50)

    for inp in [0, 64, 128, 192, 224, 240, 248, 255]:
        sp1v7_d = sp1v7_densities_full[inp]
        sp1v8_d = sp1v8_densities[inp]
        boost = sp1v8_d - sp1v7_d
        print(f"{inp:<8} {sp1v7_d:<12.4f} {sp1v8_d:<12.4f} {boost:+.4f}")

    print("\n【効果】")
    print("✓ Input 0-192: ネガ濃度+0.08-0.10D（シャドウ〜ミッドトーン軟調化）")
    print("✓ Input 192-255: SP1v7と同じ（露光レンジ維持）")
    print("✓ プリント時の相対露光量が減少 → コントラスト低下")
    print("✓ 露光時間: 8.25分のまま、または8.0分に短縮可能")

    print("\n【次のステップ】")
    print("1. QTRプリンタにSP1v8をインストール")
    print("2. 配合1（Fe 0.4cc）で8.25分または8.0分露光テスト")
    print("3. コントラストが適切か確認")

if __name__ == "__main__":
    main()
