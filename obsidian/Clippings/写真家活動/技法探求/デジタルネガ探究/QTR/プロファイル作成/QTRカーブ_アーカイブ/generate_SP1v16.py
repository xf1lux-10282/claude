#!/usr/bin/env python3
"""
SP1v16カーブ生成スクリプト - 非対称上凸カーブ

修正方針:
V7をベースに、Input 80-248に非対称の下凸カーブを適用（濃度を下げる）
- Input 0-79: V7のまま
- Input 80-128: やや急な下降（勾配 1.0）
- Input 128-220: 緩やかな下降（勾配 0.6）
- Input 220-248: やや急な下降（勾配 1.4）
- Input 248-255: 弧を描いて急な上昇（V7の255に滑らかに接続）

Input 220での下降量: -1500 Quad (約-0.05D)

目的:
- ミッドトーン（80-220）のネガ濃度を下げてプリントを明るくし、コントラストを下げる
- ハイライト表現域を拡張（220-248）
- 完全に単調増加を保つ

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

def create_adjustment_curve(peak_value=1500):
    """
    非対称上凸カーブを生成
    - Input 80-128: 勾配 1.0
    - Input 128-220: 勾配 0.6
    - Input 220-248: 勾配 1.4
    - Input 220で最大値（peak_value）
    """
    adjustments = np.zeros(256)

    # 各区間の長さ
    len_80_128 = 128 - 80  # 48
    len_128_220 = 220 - 128  # 92
    len_220_248 = 248 - 220  # 28

    # 勾配比率
    slope_80_128 = 1.0
    slope_128_220 = 0.6
    slope_220_248 = 1.4

    # Input 220での高さをpeak_valueとする
    # 逆算して各区間の高さを計算

    # 220までの総上昇量 = peak_value
    # 80-128の上昇 + 128-220の上昇 = peak_value
    # 勾配を考慮して配分

    # 総勾配距離 = len_80_128 * slope_80_128 + len_128_220 * slope_128_220
    total_slope_distance_up = len_80_128 * slope_80_128 + len_128_220 * slope_128_220

    # 単位勾配あたりの上昇量
    unit_rise = peak_value / total_slope_distance_up

    # Input 80-128: 線形上昇
    for i in range(80, 129):
        progress = (i - 80) / len_80_128
        adjustments[i] = unit_rise * slope_80_128 * (i - 80)

    # Input 128での高さ
    height_at_128 = adjustments[128]

    # Input 128-220: 緩やかな上昇
    for i in range(129, 221):
        progress = (i - 128) / len_128_220
        rise = unit_rise * slope_128_220 * (i - 128)
        adjustments[i] = height_at_128 + rise

    # Input 220-248: やや急な下降（ピークからV7に戻る）
    # 248でV7に近づけるため、220から徐々に減少
    for i in range(221, 249):
        progress = (i - 220) / len_220_248
        # 指数関数的に減少させる
        decay = 1.0 - (progress ** 1.5)  # 1.5乗で緩やかに減少
        adjustments[i] = peak_value * decay

    # Input 248-255: 徐々に上昇率を大きくしてV7[255]に到達（加速カーブ）
    # V7はリニア（各ステップ +2485 Quad）だが、これを加速カーブに変更
    # 方針: 2次関数 y = x^2 を使い、初期は緩やか、後半で急上昇

    # Input 248での累積高さを0、Input 255での累積高さもV7と同じにする
    # V7の248から255への総上昇: 7 * 2485 = 17395 Quad
    # 2次カーブ: 各ステップの上昇量 = base * (2*k - 1) (k=1,2,3,...,7)
    # Σ(2k-1) = 1+3+5+7+9+11+13 = 49

    v7_total_rise = 7 * 2485  # 17395
    sum_coefficients = sum([2*k - 1 for k in range(1, 8)])  # 49
    base_rise = v7_total_rise / sum_coefficients  # 約355

    # Input 248-255の各点での累積調整量を計算
    # 2次カーブの累積は x^2 なので
    cumulative_v7 = 0  # V7のリニア累積
    cumulative_v16 = 0  # V16の2次カーブ累積

    for k in range(1, 8):  # k=1→249, k=2→250, ..., k=7→255
        i = 248 + k

        # V7のリニア累積
        cumulative_v7 = k * 2485

        # V16の2次カーブ累積: Σ(2j-1) * base_rise for j=1 to k
        cumulative_v16 = sum([2*j - 1 for j in range(1, k+1)]) * base_rise

        # 調整量 = V16累積 - V7累積
        adjustments[i] = cumulative_v16 - cumulative_v7

    return adjustments

def create_sp1v16_quads():
    """SP1v16のQuad値配列を作成"""

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    v7_file = f"{base_path}/PX1V-PtPd-SP1v7.quad"

    print("[Step 1] Quad値配列を作成中...")
    v7_header, v7_quads = read_quad_file(v7_file)

    print(f"✓ V7 Quadファイル読み込み: {len(v7_quads)}値")

    # 調整カーブを生成
    print(f"\n[Step 2] 非対称下凸カーブを生成中（濃度を下げる）...")
    adjustments = create_adjustment_curve(peak_value=1500)

    # V7に調整を適用（マイナス方向で濃度を下げる）
    v16_quads = v7_quads.copy().astype(float)
    v16_quads -= adjustments  # プラスからマイナスに変更
    v16_quads = v16_quads.astype(int)

    # 単調増加を保証
    print(f"\n[Step 3] 単調増加を保証中...")
    for i in range(1, 256):
        if v16_quads[i] <= v16_quads[i-1]:
            v16_quads[i] = v16_quads[i-1] + 1

    def quad_to_density(quad, max_density=1.73, max_quad=55891):
        return quad * max_density / max_quad

    print(f"\n【主要ポイントの確認】")
    print(f"  Input 80:  V7={v7_quads[80]:5d} ({quad_to_density(v7_quads[80]):.4f}D) → V16={v16_quads[80]:5d} ({quad_to_density(v16_quads[80]):.4f}D) [Δ={int(adjustments[80]):+5d}]")
    print(f"  Input 128: V7={v7_quads[128]:5d} ({quad_to_density(v7_quads[128]):.4f}D) → V16={v16_quads[128]:5d} ({quad_to_density(v16_quads[128]):.4f}D) [Δ={int(adjustments[128]):+5d}]")
    print(f"  Input 220: V7={v7_quads[220]:5d} ({quad_to_density(v7_quads[220]):.4f}D) → V16={v16_quads[220]:5d} ({quad_to_density(v16_quads[220]):.4f}D) [Δ={int(adjustments[220]):+5d}]")
    print(f"  Input 248: V7={v7_quads[248]:5d} ({quad_to_density(v7_quads[248]):.4f}D) → V16={v16_quads[248]:5d} ({quad_to_density(v16_quads[248]):.4f}D) [Δ={int(adjustments[248]):+5d}]")
    print(f"  Input 255: V7={v7_quads[255]:5d} ({quad_to_density(v7_quads[255]):.4f}D) → V16={v16_quads[255]:5d} ({quad_to_density(v16_quads[255]):.4f}D) [Δ={int(adjustments[255]):+5d}]")

    return v7_header, v16_quads, v7_quads, adjustments

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
        f.write('# PX1V-PtPd-SP1v16 - Asymmetric concave curve for contrast reduction\n')
        f.write('# Input 0-79: V7 baseline\n')
        f.write('# Input 80-128: Moderate density reduction (slope 1.0)\n')
        f.write('# Input 128-220: Gentle density reduction (slope 0.6)\n')
        f.write('# Input 220-248: Moderate density reduction (slope 1.4)\n')
        f.write('# Input 248-255: Curved steep rise to V7[255] (acceleration)\n')
        f.write('# Peak reduction at Input 220: -1500 Quad (-0.05D)\n')
        f.write('# Created: 2026-03-19 SP1v16\n')
        f.write('# Purpose: Reduce contrast, expand highlight tonal range\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')
        f.write('# K curve\n')

        # 2560値を出力
        for i in range(10):
            for quad in quads:
                f.write(f'{quad}\n')

def plot_comparison(v7_quads, v16_quads, adjustments):
    """V7とV16の比較グラフを生成"""
    fig, axes = plt.subplots(4, 1, figsize=(14, 14))

    inputs = np.arange(256)

    def quad_to_density(quad):
        return quad * 1.73 / 55891

    # グラフ1: Quad値の比較
    ax1 = axes[0]
    ax1.plot(inputs, v7_quads, 'b-', label='V7 (Original)', linewidth=2, alpha=0.7)
    ax1.plot(inputs, v16_quads, 'r-', label='V16 (Convex Curve)', linewidth=2)
    ax1.axvline(x=80, color='orange', linestyle='--', alpha=0.5, label='Start (80)')
    ax1.axvline(x=128, color='purple', linestyle=':', alpha=0.5, label='Point 128')
    ax1.axvline(x=220, color='green', linestyle='--', alpha=0.5, label='Peak (220)')
    ax1.axvline(x=248, color='red', linestyle='--', alpha=0.5, label='End (248)')
    ax1.set_xlabel('Input Value')
    ax1.set_ylabel('Quad Value')
    ax1.set_title('V7 vs V16 - Asymmetric Convex Curve', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # グラフ2: 調整量
    ax2 = axes[1]
    ax2.fill_between(inputs, adjustments, 0, alpha=0.3, color='red')
    ax2.plot(inputs, adjustments, 'r-', linewidth=2, label='Adjustment Amount')
    ax2.axvline(x=80, color='orange', linestyle='--', alpha=0.5)
    ax2.axvline(x=128, color='purple', linestyle=':', alpha=0.5)
    ax2.axvline(x=220, color='green', linestyle='--', alpha=0.5)
    ax2.axvline(x=248, color='red', linestyle='--', alpha=0.5)
    ax2.axhline(y=1500, color='green', linestyle=':', alpha=0.5, label='Peak: +1500 Quad')
    ax2.set_xlabel('Input Value')
    ax2.set_ylabel('Adjustment (Quad)')
    ax2.set_title('Adjustment Curve - Non-symmetric Convex Shape')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # グラフ3: 勾配比較
    ax3 = axes[2]
    v7_diff = np.diff(v7_quads)
    v16_diff = np.diff(v16_quads)
    ax3.plot(inputs[1:], v7_diff, 'b-', label='V7 Gradient', linewidth=1, alpha=0.7)
    ax3.plot(inputs[1:], v16_diff, 'r-', label='V16 Gradient', linewidth=1)
    ax3.axhline(y=200, color='red', linestyle='--', alpha=0.5, label='Banding Threshold')
    ax3.axhline(y=-200, color='red', linestyle='--', alpha=0.5)
    ax3.axvline(x=80, color='orange', linestyle='--', alpha=0.5)
    ax3.axvline(x=128, color='purple', linestyle=':', alpha=0.5)
    ax3.axvline(x=220, color='green', linestyle='--', alpha=0.5)
    ax3.axvline(x=248, color='red', linestyle='--', alpha=0.5)
    ax3.set_xlabel('Input Value')
    ax3.set_ylabel('Quad Difference (Δ)')
    ax3.set_title('Gradient Comparison')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # グラフ4: Input 70-255の拡大図
    ax4 = axes[3]
    zoom_range = range(70, 256)
    ax4.plot([i for i in zoom_range], [v7_quads[i] for i in zoom_range],
             'b-', label='V7', linewidth=2, alpha=0.7)
    ax4.plot([i for i in zoom_range], [v16_quads[i] for i in zoom_range],
             'r-', label='V16', linewidth=2)
    ax4.axvline(x=80, color='orange', linestyle='--', alpha=0.5, label='Start')
    ax4.axvline(x=128, color='purple', linestyle=':', alpha=0.5, label='Point 128')
    ax4.axvline(x=220, color='green', linestyle='--', alpha=0.5, label='Peak')
    ax4.axvline(x=248, color='red', linestyle='--', alpha=0.5, label='End')
    ax4.set_xlabel('Input Value')
    ax4.set_ylabel('Quad Value')
    ax4.set_title('Detail: Input 70-255 (Adjustment Zone)', fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    plt.savefig(f"{base_path}/SP1v16_preview.png", dpi=150, bbox_inches='tight')

    print(f"\n✓ グラフ保存: SP1v16_preview.png")

    plt.close()

def main():
    print("=" * 80)
    print("SP1v16カーブ生成開始（非対称上凸カーブ）")
    print("=" * 80)

    # Quad値作成
    v7_header, v16_quads, v7_quads, adjustments = create_sp1v16_quads()

    # バンディングリスク解析
    print("\n[Step 4] バンディングリスク解析中...")
    v7_risks = analyze_banding_risk(v7_quads)
    v16_risks = analyze_banding_risk(v16_quads)

    print(f"✓ V7リスク箇所: {len(v7_risks)}箇所")
    print(f"✓ V16リスク箇所: {len(v16_risks)}箇所")

    # 新規追加されたリスク
    v7_risk_inputs = set([r[0] for r in v7_risks])
    v16_risk_inputs = set([r[0] for r in v16_risks])
    new_risks = v16_risk_inputs - v7_risk_inputs
    resolved_risks = v7_risk_inputs - v16_risk_inputs

    if new_risks:
        print(f"\n⚠️ V16で新たに追加されたリスク箇所: {len(new_risks)}箇所")
        for inp in sorted(new_risks)[:10]:
            for r in v16_risks:
                if r[0] == inp:
                    print(f"   Input {r[0]-1}→{r[0]}: Δ={r[1]} Quad")
                    break

    if resolved_risks:
        print(f"\n✓ V16で解消されたリスク箇所: {len(resolved_risks)}箇所")

    # グラフ生成
    print("\n[Step 5] 比較グラフを生成中...")
    plot_comparison(v7_quads, v16_quads, adjustments)

    # ファイル出力
    print("\n[Step 6] Quadファイルを出力中...")
    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    quad_file = f"{base_path}/PX1V-PtPd-SP1v16.quad"

    write_quad_file(v16_quads, quad_file)
    print(f"✓ Quadファイル: PX1V-PtPd-SP1v16.quad")

    # サマリー
    print("\n" + "=" * 80)
    print("SP1v16カーブ生成完了")
    print("=" * 80)

    def quad_to_density(quad, max_density=1.73, max_quad=55891):
        return quad * max_density / max_quad

    print(f"\n【修正内容】")
    print(f"✓ Input 0-79: V7のまま")
    print(f"✓ Input 80-128: やや急な上昇（勾配 1.0）")
    print(f"✓ Input 128-220: 緩やかな上昇（勾配 0.6）")
    print(f"✓ Input 220-248: やや急な上昇（勾配 1.4）")
    print(f"✓ Input 248-255: V7に戻る")
    print(f"✓ Input 220での最大調整: +1500 Quad (+0.05D)")

    print(f"\n【バンディングリスク】")
    if len(new_risks) == 0:
        print(f"✓ 新たなリスク箇所なし")
    else:
        print(f"⚠️ 新たなリスク箇所: {len(new_risks)}箇所")

    if len(resolved_risks) > 0:
        print(f"✓ 解消されたリスク箇所: {len(resolved_risks)}箇所")

    print(f"\n【次のステップ】")
    print(f"1. グラフを確認して非対称カーブの形状を評価")
    print(f"2. 問題なければQTRプリンタにインストール")
    print(f"3. テストプリントで実際の効果を確認")

if __name__ == "__main__":
    main()
