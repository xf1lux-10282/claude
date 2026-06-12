#!/usr/bin/env python3
"""
SP1v9カーブ生成スクリプト - コントラスト低減版（逆S字カーブ）

設計方針（ユーザー提案）:
- Input 0-8: 変更なし（基準）
- Input 8-128: ネガ濃度を上げる（+0.05-0.10D）→ シャドウ持ち上げ
- Input 128-244: ネガ濃度を下げる（-0.03-0.05D）→ コントラスト縮小
- Input 244-255: 変更なし（露光レンジ維持）

実行日: 2026-03-18
作成者: Claude Code + Daisuke Kinoshita
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline

def quad_to_density(quad):
    """Quad値を濃度値に変換（0.0D=0, 4.0D=65535）"""
    return quad * 4.0 / 65535

def density_to_quad(density):
    """濃度値をQuad値に変換"""
    return int(density * 65535 / 4.0)

def read_sp1v7_full():
    """SP1v7の完全なQuadファイルを読み込む"""
    quad_file = "/Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-SP1v7.quad"

    with open(quad_file, 'r') as f:
        lines = f.readlines()

    # ヘッダー行を除外（"## " または "# " で始まる行）
    quad_values = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            try:
                quad_values.append(int(line))
            except ValueError:
                pass

    print(f"✓ SP1v7から{len(quad_values)}個のQuad値を読み込みました")

    # 最初の256個を使用（Input 0-255）
    if len(quad_values) >= 256:
        quad_dict = {i: quad_values[i] for i in range(256)}
    else:
        raise ValueError(f"Quad値が不足: {len(quad_values)}個（256個必要）")

    return quad_dict

def generate_sp1v9(sp1v7_quads):
    """SP1v9カーブを生成（逆S字カーブでコントラスト低減）"""

    sp1v9_quads = {}
    sp1v7_densities = {}
    sp1v9_densities = {}

    # SP1v7の濃度を計算
    for inp in range(256):
        sp1v7_densities[inp] = quad_to_density(sp1v7_quads[inp])

    # SP1v9の濃度を計算
    for inp in range(256):
        sp1v7_d = sp1v7_densities[inp]

        if inp < 8:
            # Input 0-7: 変更なし（基準）
            adjustment = 0.0

        elif 8 <= inp < 128:
            # Input 8-127: +0.05D → +0.10D（線形増加）
            # シャドウを持ち上げる
            progress = (inp - 8) / (128 - 8)  # 0.0 → 1.0
            adjustment = 0.05 + (0.05 * progress)  # +0.05D → +0.10D

        elif 128 <= inp < 244:
            # Input 128-243: -0.05D → -0.03D（線形減少）
            # コントラストを縮める
            progress = (inp - 128) / (244 - 128)  # 0.0 → 1.0
            adjustment = -0.05 + (0.02 * progress)  # -0.05D → -0.03D

        else:
            # Input 244-255: 変更なし（露光レンジ維持）
            adjustment = 0.0

        sp1v9_d = sp1v7_d + adjustment
        sp1v9_densities[inp] = sp1v9_d
        sp1v9_quads[inp] = density_to_quad(sp1v9_d)

    # 65535を超えないようにクリップ
    sp1v9_quads = {inp: min(65535, max(0, quad)) for inp, quad in sp1v9_quads.items()}

    # 濃度を再計算（クリップ後）
    sp1v9_densities = {inp: quad_to_density(quad) for inp, quad in sp1v9_quads.items()}

    return sp1v9_quads, sp1v9_densities, sp1v7_densities

def analyze_banding_risk(quad_dict, threshold=200):
    """境界線リスクを解析"""
    risks = []
    for inp in range(1, 256):
        diff = quad_dict[inp] - quad_dict[inp-1]
        if diff > threshold:
            risks.append((inp, diff))
    return risks

def write_quad_file_correct(sp1v7_file, sp1v9_quads, output_file):
    """SP1v7のヘッダーと構造を維持してSP1v9を出力"""
    with open(sp1v7_file, 'r') as f:
        sp1v7_lines = f.readlines()

    # ヘッダー行を抽出（"#"で始まる行）
    header_lines = []
    for line in sp1v7_lines:
        if line.strip().startswith('#'):
            header_lines.append(line)
        else:
            break

    # ヘッダーを修正
    new_header = []
    for line in header_lines:
        if 'SP1v7' in line:
            new_header.append(line.replace('SP1v7', 'SP1v9').replace(
                'Moderate opacity', 'Contrast reduction (inverse S-curve)'))
        elif 'Input 0-247' in line:
            new_header.append('# Input 0-7: Unchanged (baseline)\n')
            new_header.append('# Input 8-127: Density boost +0.05-0.10D (shadow lift)\n')
            new_header.append('# Input 128-243: Density reduction -0.05--0.03D (contrast compression)\n')
            new_header.append('# Input 244-255: Unchanged (exposure range maintained)\n')
        elif 'Created:' in line:
            new_header.append('# Created: 2026-03-18\n')
        elif 'WARNING' in line:
            new_header.append('# Purpose: Lower contrast for softer platinum prints\n')
        else:
            new_header.append(line)

    # ファイルに書き込み
    with open(output_file, 'w') as f:
        # ヘッダー
        for line in new_header:
            f.write(line)

        # Quad値（256個）
        for inp in range(256):
            f.write(f'{sp1v9_quads[inp]}\n')

        # 残りの行（ゼロパディングなど）
        # SP1v7の構造を維持
        remaining_lines = []
        quad_section_ended = False
        line_count = 0
        for line in sp1v7_lines:
            if not line.strip().startswith('#'):
                line_count += 1
                if line_count > 256:
                    remaining_lines.append(line)

        for line in remaining_lines:
            f.write(line)

def write_detail_csv(sp1v7_quads, sp1v9_quads, sp1v7_densities, sp1v9_densities, filename):
    """詳細データをCSV出力"""
    data = []
    for inp in range(256):
        sp1v7_q = sp1v7_quads[inp]
        sp1v9_q = sp1v9_quads[inp]
        sp1v7_d = sp1v7_densities[inp]
        sp1v9_d = sp1v9_densities[inp]

        data.append({
            'Input': inp,
            'SP1v7_Quad': sp1v7_q,
            'SP1v9_Quad': sp1v9_q,
            'Quad_Change': sp1v9_q - sp1v7_q,
            'SP1v7_Density': f'{sp1v7_d:.6f}',
            'SP1v9_Density': f'{sp1v9_d:.6f}',
            'Density_Change': f'{sp1v9_d - sp1v7_d:.6f}'
        })

    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    return df

def plot_analysis(sp1v7_quads, sp1v9_quads, sp1v7_densities, sp1v9_densities, filename):
    """解析グラフを生成"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    inputs = range(256)

    # Quadカーブ比較
    ax = axes[0, 0]
    sp1v7_q_list = [sp1v7_quads[i] for i in inputs]
    sp1v9_q_list = [sp1v9_quads[i] for i in inputs]
    ax.plot(inputs, sp1v7_q_list, label='SP1v7', linewidth=2)
    ax.plot(inputs, sp1v9_q_list, label='SP1v9 (Contrast reduction)', linewidth=2)
    ax.axvline(x=8, color='red', linestyle='--', alpha=0.3, label='Adjustment zones')
    ax.axvline(x=128, color='red', linestyle='--', alpha=0.3)
    ax.axvline(x=244, color='red', linestyle='--', alpha=0.3)
    ax.set_xlabel('Input Value (0-255)')
    ax.set_ylabel('Quad Value (0-65535)')
    ax.set_title('Quad Curve Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 濃度カーブ比較
    ax = axes[0, 1]
    sp1v7_d_list = [sp1v7_densities[i] for i in inputs]
    sp1v9_d_list = [sp1v9_densities[i] for i in inputs]
    ax.plot(inputs, sp1v7_d_list, label='SP1v7', linewidth=2)
    ax.plot(inputs, sp1v9_d_list, label='SP1v9 (Contrast reduction)', linewidth=2)
    ax.axvline(x=8, color='red', linestyle='--', alpha=0.3)
    ax.axvline(x=128, color='red', linestyle='--', alpha=0.3)
    ax.axvline(x=244, color='red', linestyle='--', alpha=0.3)
    ax.set_xlabel('Input Value (0-255)')
    ax.set_ylabel('Negative Density (D)')
    ax.set_title('Density Curve Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Quad勾配（境界線リスク）
    ax = axes[1, 0]
    sp1v7_diffs = [sp1v7_q_list[i] - sp1v7_q_list[i-1] for i in range(1, 256)]
    sp1v9_diffs = [sp1v9_q_list[i] - sp1v9_q_list[i-1] for i in range(1, 256)]
    ax.plot(range(1, 256), sp1v7_diffs, label='SP1v7', alpha=0.7)
    ax.plot(range(1, 256), sp1v9_diffs, label='SP1v9', alpha=0.7)
    ax.axhline(y=200, color='red', linestyle='--', label='Banding Risk (>200)')
    ax.set_xlabel('Input Value (1-255)')
    ax.set_ylabel('Quad Difference (Δ)')
    ax.set_title('Quad Gradient (Banding Risk)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 300)

    # 濃度変化量
    ax = axes[1, 1]
    density_changes = [sp1v9_d_list[i] - sp1v7_d_list[i] for i in inputs]
    ax.plot(inputs, density_changes, linewidth=2, color='green')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.axvline(x=8, color='red', linestyle='--', alpha=0.3)
    ax.axvline(x=128, color='red', linestyle='--', alpha=0.3)
    ax.axvline(x=244, color='red', linestyle='--', alpha=0.3)
    ax.set_xlabel('Input Value (0-255)')
    ax.set_ylabel('Density Change (D)')
    ax.set_title('Density Adjustment Amount (SP1v9 - SP1v7)')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"✓ 解析グラフ保存: {filename}")

def main():
    print("=" * 60)
    print("SP1v9カーブ生成開始 - コントラスト低減版（逆S字カーブ）")
    print("=" * 60)

    # SP1v7の完全データを読み込み
    print("\n[1] SP1v7カーブを読み込み中...")
    sp1v7_quads = read_sp1v7_full()

    # SP1v9生成
    print("[2] SP1v9カーブを計算中...")
    sp1v9_quads, sp1v9_densities, sp1v7_densities = generate_sp1v9(sp1v7_quads)

    # 境界線リスク解析
    print("[3] 境界線リスク解析中...")
    sp1v7_risks = analyze_banding_risk(sp1v7_quads)
    sp1v9_risks = analyze_banding_risk(sp1v9_quads)

    print(f"\n【境界線リスク（Quad差分 > 200）】")
    print(f"SP1v7: {len(sp1v7_risks)}箇所")
    if sp1v7_risks:
        for inp, diff in sp1v7_risks[:5]:
            print(f"  - Input {inp}: Δ={diff}")

    print(f"\nSP1v9: {len(sp1v9_risks)}箇所")
    if sp1v9_risks:
        for inp, diff in sp1v9_risks[:5]:
            print(f"  - Input {inp}: Δ={diff}")

    # 主要ポイント比較
    print("\n" + "=" * 60)
    print("【主要ポイント比較】")
    print("=" * 60)
    print(f"{'Input':<8} {'SP1v7 Quad':<12} {'SP1v9 Quad':<12} {'Quad Δ':<10} {'SP1v7 D':<10} {'SP1v9 D':<10} {'D Δ':<10}")
    print("-" * 90)

    key_inputs = [0, 8, 64, 128, 192, 224, 244, 248, 255]
    for inp in key_inputs:
        sp1v7_q = sp1v7_quads[inp]
        sp1v9_q = sp1v9_quads[inp]
        sp1v7_d = sp1v7_densities[inp]
        sp1v9_d = sp1v9_densities[inp]
        quad_diff = sp1v9_q - sp1v7_q
        d_diff = sp1v9_d - sp1v7_d

        print(f"{inp:<8} {sp1v7_q:<12} {sp1v9_q:<12} {quad_diff:+<10} {sp1v7_d:<10.4f} {sp1v9_d:<10.4f} {d_diff:+.4f}")

    # ファイル出力
    print("\n[4] ファイル出力中...")
    base_path = "obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"

    sp1v7_file = "/Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-SP1v7.quad"
    quad_file = f"{base_path}/PX1V-PtPd-SP1v9.quad"

    write_quad_file_correct(sp1v7_file, sp1v9_quads, quad_file)
    print(f"✓ Quadファイル: PX1V-PtPd-SP1v9.quad")

    csv_file = f"{base_path}/PX1V-PtPd-SP1v9.txt"
    df = write_detail_csv(sp1v7_quads, sp1v9_quads, sp1v7_densities, sp1v9_densities, csv_file)
    print(f"✓ 詳細データ: PX1V-PtPd-SP1v9.txt")

    graph_file = f"{base_path}/SP1v9_contrast_reduction_analysis.png"
    plot_analysis(sp1v7_quads, sp1v9_quads, sp1v7_densities, sp1v9_densities, graph_file)

    print("\n" + "=" * 60)
    print("SP1v9カーブ生成完了")
    print("=" * 60)

    print("\n【効果】")
    print("✓ Input 0-7: 変更なし（基準）")
    print("✓ Input 8-127: ネガ濃度 +0.05-0.10D（シャドウ持ち上げ）")
    print("✓ Input 128-243: ネガ濃度 -0.05--0.03D（コントラスト縮小）")
    print("✓ Input 244-255: 変更なし（露光レンジ維持）")
    print("✓ 逆S字カーブでコントラスト低減")

    print("\n【次のステップ】")
    print("1. SP1v9をQTRプリンタにインストール")
    print("2. 配合1（Fe 0.4cc）で8.25分テストプリント")
    print("3. コントラストが適切か確認")

if __name__ == "__main__":
    main()
