#!/usr/bin/env python3
"""
SP1v10カーブ生成スクリプト - スプライン補間版

修正内容:
1. Input 0-16: S字カーブ（シグモイド関数）でスムーズに接続
2. Input 17-126: V9のまま維持（スムーズな接続を保持）
3. Input 127-134: リニア補間（濃度逆転を解消）
4. Input 135-240: V9のInput (inp+8)のQuad値を使用（シフト）
5. Input 241-248: Input 240から248へリニア補間（滑らかな接続）
6. Input 248: 1.29Dに設定（41675 Quad）
7. Input 249-254: Input 248から255へリニア補間（滑らかな接続）
8. Input 255: V7のInput 255のQuad値を使用（1.73D）

目的:
- Input 0-16のシャドウ部の階調を保持（S字カーブで急激な変化を回避）
- Input 127-128の濃度逆転を完全に解消
- Input 135以降のコントラストを調整（+8シフト）
- Input 248の濃度を1.29Dに引き上げ（薬品調合変更に対応）
- バンディングリスクを最小化
- スムーズな濃度カーブを実現

実行日: 2026-03-18
作成者: Claude Code
"""

import numpy as np
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt

def read_quad_file(filepath):
    """Quadファイルを読み込んでQuad値のリストを返す"""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    quad_values = []
    header_lines = []

    for line in lines:
        line_stripped = line.strip()
        if line_stripped.isdigit():
            quad_values.append(int(line_stripped))
        else:
            header_lines.append(line_stripped)

    return header_lines, quad_values

def smooth_transition(v9_quads, anchor_points):
    """
    アンカーポイントを使ってスプライン補間で滑らかに接続

    anchor_points: {input: quad_value} の辞書
    """

    # V9をベースにして、アンカーポイントで上書き
    v10_quads = v9_quads.copy()

    # アンカーポイント周辺をスプライン補間
    for anchor_inp, anchor_quad in anchor_points.items():
        # アンカーポイントの前後2点ずつを補間範囲とする
        interp_start = max(0, anchor_inp - 2)
        interp_end = min(255, anchor_inp + 2)

        # 補間用の制御点を作成
        control_inputs = []
        control_quads = []

        # 開始点（V9の値）
        control_inputs.append(interp_start)
        control_quads.append(v9_quads[interp_start])

        # アンカーポイント（目標値）
        control_inputs.append(anchor_inp)
        control_quads.append(anchor_quad)

        # 終了点（V9の値）
        control_inputs.append(interp_end)
        control_quads.append(v9_quads[interp_end])

        # スプライン補間
        cs = CubicSpline(control_inputs, control_quads)

        # 補間範囲のQuad値を更新
        for inp in range(interp_start, interp_end + 1):
            v10_quads[inp] = int(cs(inp))
            v10_quads[inp] = max(0, min(65535, v10_quads[inp]))  # クリップ

    return v10_quads

def create_sp1v10_quads():
    """SP1v10のQuad値配列を作成"""

    # V9、V7、V20のQuadファイルを読み込み
    v9_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-SP1v9.quad"
    v7_path = "/Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-SP1v7.quad"
    v20_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/QTR_Archive_2026-03-17/PX1V-PtPd-v20.quad"

    v9_header, v9_quads = read_quad_file(v9_path)
    v7_header, v7_quads = read_quad_file(v7_path)
    v20_header, v20_quads = read_quad_file(v20_path)

    # 最初の256値のみ使用
    v9_quads = v9_quads[:256]
    v7_quads = v7_quads[:256]
    v20_quads = v20_quads[:256]

    print(f"✓ V9 Quadファイル読み込み: {len(v9_quads)}値")
    print(f"✓ V7 Quadファイル読み込み: {len(v7_quads)}値")
    print(f"✓ V20 Quadファイル読み込み: {len(v20_quads)}値")

    # Step 1: V9をベースにコピー
    v10_quads = v9_quads.copy()

    # Step 0: Input 0-16をS字カーブで補間
    print(f"\n[0] Input 0-16: S字カーブで滑らかに接続中...")

    def sigmoid(x, steepness=1.0):
        """シグモイド関数（S字カーブ）"""
        return 1 / (1 + np.exp(-steepness * (x - 0.5)))

    # Input 0と16の値を始点・終点とする
    start_quad_0 = v9_quads[0]  # 0 Quad
    end_quad_16 = v9_quads[16]  # 2133 Quad

    # Input 0-16をS字カーブで補間
    for inp in range(0, 17):
        # 0-16を0.0-1.0にマッピング
        x_normalized = inp / 16.0

        # シグモイド関数を適用（steepness=6で適度なS字カーブ）
        sigmoid_value = sigmoid(x_normalized, steepness=6.0)

        # シグモイド値を0から始まるように調整
        sigmoid_min = sigmoid(0, steepness=6.0)
        sigmoid_max = sigmoid(1, steepness=6.0)
        sigmoid_normalized = (sigmoid_value - sigmoid_min) / (sigmoid_max - sigmoid_min)

        # Quad値を計算
        v10_quads[inp] = int(start_quad_0 + (end_quad_16 - start_quad_0) * sigmoid_normalized)

    def quad_to_density(quad, max_density=1.73, max_quad=55891):
        return quad * max_density / max_quad

    print(f"   Input 0: {v10_quads[0]} Quad ({quad_to_density(v10_quads[0]):.4f}D)")
    print(f"   Input 1-15: S字カーブ補間")
    print(f"   Input 16: {v10_quads[16]} Quad ({quad_to_density(v10_quads[16]):.4f}D)")

    print(f"\n[1] Input 17-126: V9のまま維持（スムーズな接続を保持）")

    # Step 2: Input 135-240のシフトを適用
    print(f"[2] Input 135-240のシフトを適用中...")
    for inp in range(135, 241):
        source_input = inp + 8
        if source_input <= 255:
            v10_quads[inp] = v9_quads[source_input]

    def quad_to_density(quad, max_density=1.73, max_quad=55891):
        return quad * max_density / max_quad

    def density_to_quad(density, max_density=1.73, max_quad=55891):
        return int(density * max_quad / max_density)

    # Step 2.5: Input 127-134をリニア補間（濃度逆転を解消）
    print(f"[2.5] Input 127-134: リニア補間で滑らかに接続中...")

    # リニア補間の始点と終点
    start_input_127 = 126
    end_input_127 = 135
    start_quad_127 = v10_quads[start_input_127]  # V9[126]の値
    end_quad_127 = v10_quads[end_input_127]  # V9[143]の値（135+8）

    # Input 127-134をリニア補間
    for inp in range(127, 135):
        ratio = (inp - start_input_127) / (end_input_127 - start_input_127)
        v10_quads[inp] = int(start_quad_127 + (end_quad_127 - start_quad_127) * ratio)

    print(f"   Input 126: {v10_quads[126]} Quad ({quad_to_density(v10_quads[126]):.2f}D)")
    print(f"   Input 127-134: リニア補間")
    print(f"   Input 135: {v10_quads[135]} Quad ({quad_to_density(v10_quads[135]):.2f}D)")

    # Step 3: Input 248を先に設定（1.29D）
    target_density_248 = 1.29
    target_quad_248 = density_to_quad(target_density_248)

    # Step 4: Input 241-248をリニア補間
    print(f"[3] Input 241-248: Input 240から248へリニア補間中...")

    # リニア補間の始点と終点
    start_input = 240
    end_input = 248
    start_quad = v10_quads[start_input]  # V9[248]の値
    end_quad = target_quad_248  # 1.29Dの値

    # Input 241-248をリニア補間
    for inp in range(241, 249):
        # 線形補間の計算
        ratio = (inp - start_input) / (end_input - start_input)
        v10_quads[inp] = int(start_quad + (end_quad - start_quad) * ratio)

    # Input 248は目標値を設定
    v10_quads[248] = target_quad_248

    # Step 4: Input 249-254をリニア補間（248から255へ滑らかに接続）
    print(f"[4] Input 249-254: Input 248から255へリニア補間中...")

    start_input_249 = 248
    end_input_249 = 255
    start_quad_249 = target_quad_248  # 1.29Dの値
    end_quad_249 = v7_quads[255]  # 1.73Dの値

    for inp in range(249, 255):
        ratio = (inp - start_input_249) / (end_input_249 - start_input_249)
        v10_quads[inp] = int(start_quad_249 + (end_quad_249 - start_quad_249) * ratio)

    # Step 5: Input 255はV7のまま
    print(f"[5] Input 255をV7の値に設定...")
    v10_quads[255] = v7_quads[255]

    print(f"   Input 240: {v10_quads[240]} Quad ({quad_to_density(v10_quads[240]):.2f}D)")
    print(f"   Input 241-248: リニア補間")
    print(f"   Input 248: {v10_quads[248]} Quad ({quad_to_density(v10_quads[248]):.2f}D) - 目標1.29D")
    print(f"   Input 249-254: リニア補間（248から255へ）")
    print(f"   Input 255: V7[255] = {v7_quads[255]} Quad ({quad_to_density(v7_quads[255]):.2f}D)")

    return v9_header, v10_quads, v9_quads, v7_quads, v20_quads

def analyze_banding_risk(quads, threshold=200):
    """バンディングリスクを解析"""
    risks = []
    for inp in range(1, 256):
        diff = quads[inp] - quads[inp-1]
        if abs(diff) > threshold:
            risks.append((inp, diff))
    return risks

def write_quad_file(quads, header_lines, filename):
    """Quadファイルを出力"""

    with open(filename, 'w') as f:
        # ヘッダー出力
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        f.write('# QuadProfile Version 2.8.0\n')
        f.write('# PX1V-PtPd-SP1v11 - Contrast adjusted curve with sigmoid and linear interpolation\n')
        f.write('# Input 0-16: Sigmoid curve (smooth S-curve for shadow detail)\n')
        f.write('# Input 17-126: V9 baseline (smooth progression preserved)\n')
        f.write('# Input 127-134: Linear interpolation (eliminates density reversal)\n')
        f.write('# Input 135-240: V9 shifted by +8 steps (contrast adjustment)\n')
        f.write('# Input 241-248: Linear interpolation from 240 to 248 (smooth transition)\n')
        f.write('# Input 248: 1.29D (41675 Quad - highlight enhancement)\n')
        f.write('# Input 249-254: Linear interpolation from 248 to 255 (smooth transition)\n')
        f.write('# Input 255: V7[255] value (1.73D - complete opacity)\n')
        f.write('# Created: 2026-03-18 SP1v11 (renamed from v10 for clarity)\n')
        f.write('# Purpose: Contrast adjustment, smooth curve\n')
        f.write('# 2026 Daisuke Kinoshita\n')
        f.write('# BOOST_K=0 - NO BOOST\n')
        f.write('# K curve\n')

        # Quad値出力
        for inp in range(256):
            f.write(f'{quads[inp]}\n')

def plot_comparison(v9_quads, v10_quads, v7_quads):
    """比較グラフを生成"""

    fig, axes = plt.subplots(3, 1, figsize=(16, 12))

    inputs = range(256)

    # グラフ1: Quad値比較（全体）
    ax = axes[0]
    ax.plot(inputs, v9_quads, 'o-', label='V9', linewidth=1, markersize=2, alpha=0.7)
    ax.plot(inputs, v10_quads, 's-', label='V10 (Spline)', linewidth=1, markersize=2)
    ax.axvline(x=104, color='orange', linestyle='--', alpha=0.5, label='Anchor Points')
    ax.axvline(x=112, color='orange', linestyle='--', alpha=0.5)
    ax.axvline(x=128, color='purple', linestyle='--', alpha=0.5, label='Shift Start')
    ax.set_xlabel('Input Value', fontsize=12)
    ax.set_ylabel('Quad Value', fontsize=12)
    ax.set_title('V9 vs V10 Quad Values', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # グラフ2: 勾配比較（Input 96-144）
    ax = axes[1]

    region_inputs = range(96, 145)
    v9_gradients = [v9_quads[i] - v9_quads[i-1] for i in region_inputs]
    v10_gradients = [v10_quads[i] - v10_quads[i-1] for i in region_inputs]

    ax.plot(region_inputs, v9_gradients, 'o-', label='V9 Gradient', linewidth=2, markersize=4, alpha=0.7)
    ax.plot(region_inputs, v10_gradients, 's-', label='V10 Gradient', linewidth=2, markersize=4)
    ax.axhline(y=200, color='red', linestyle='--', linewidth=2, label='Risk Threshold')
    ax.axhline(y=-200, color='red', linestyle='--', linewidth=2)
    ax.axvline(x=104, color='orange', linestyle='--', alpha=0.5)
    ax.axvline(x=112, color='orange', linestyle='--', alpha=0.5)
    ax.axvline(x=128, color='purple', linestyle='--', alpha=0.5)
    ax.set_xlabel('Input Value', fontsize=12)
    ax.set_ylabel('Quad Difference (Δ)', fontsize=12)
    ax.set_title('Gradient Comparison: Input 96-144 (Critical Region)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-500, 700)

    # グラフ3: 詳細比較（Input 102-118）
    ax = axes[2]

    detail_inputs = range(102, 119)
    detail_v9 = [v9_quads[i] for i in detail_inputs]
    detail_v10 = [v10_quads[i] for i in detail_inputs]
    detail_v7_112 = v7_quads[112]
    detail_v7_120 = v7_quads[120]

    ax.plot(detail_inputs, detail_v9, 'o-', label='V9', linewidth=2, markersize=6, alpha=0.7)
    ax.plot(detail_inputs, detail_v10, 's-', label='V10 (Spline)', linewidth=2, markersize=6)
    ax.axhline(y=detail_v7_112, color='orange', linestyle='--', alpha=0.5, label=f'V7[112]={detail_v7_112}')
    ax.axhline(y=detail_v7_120, color='green', linestyle='--', alpha=0.5, label=f'V7[120]={detail_v7_120}')
    ax.axvline(x=104, color='orange', linestyle='--', linewidth=2)
    ax.axvline(x=112, color='green', linestyle='--', linewidth=2)
    ax.set_xlabel('Input Value', fontsize=12)
    ax.set_ylabel('Quad Value', fontsize=12)
    ax.set_title('Detail: Input 102-118 (Spline Smoothing Effect)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/SP1v10_smooth_preview.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ グラフ保存: SP1v10_smooth_preview.png")

def main():
    print("=" * 80)
    print("SP1v10カーブ生成開始（スプライン補間版）")
    print("=" * 80)

    # V10のQuad値配列を作成
    print("\n[Step 1] Quad値配列を作成中...")
    v9_header, v10_quads, v9_quads, v7_quads, v20_quads = create_sp1v10_quads()

    # バンディングリスク解析
    print("\n[Step 2] バンディングリスク解析中...")
    v9_risks = analyze_banding_risk(v9_quads)
    v10_risks = analyze_banding_risk(v10_quads)

    print(f"✓ V9リスク箇所: {len(v9_risks)}箇所")
    print(f"✓ V10リスク箇所: {len(v10_risks)}箇所")

    # 新規追加されたリスク
    v9_risk_inputs = set([r[0] for r in v9_risks])
    v10_risk_inputs = set([r[0] for r in v10_risks])
    new_risks = v10_risk_inputs - v9_risk_inputs

    if new_risks:
        print(f"\n⚠️ V10で新たに追加されたリスク箇所: {len(new_risks)}箇所")
        for inp in sorted(new_risks)[:10]:  # 最初の10箇所を表示
            risk = [r for r in v10_risks if r[0] == inp][0]
            print(f"   Input {inp-1}→{inp}: Δ={risk[1]} Quad")
    else:
        print(f"\n✓ V10で新たに追加されたリスク箇所はありません")

    # 重要箇所の詳細確認
    print("\n【重要箇所の詳細確認】")
    print(f"{'Input':<8} {'V9_Quad':<10} {'V10_Quad':<10} {'V9_Δ':<10} {'V10_Δ':<10} {'判定':<10}")
    print("-" * 70)

    for inp in [103, 104, 105, 111, 112, 113, 120, 127, 128, 129, 240, 241, 247, 248, 255]:
        v9_diff = v9_quads[inp] - v9_quads[inp-1]
        v10_diff = v10_quads[inp] - v10_quads[inp-1]

        v9_status = "⚠️" if abs(v9_diff) > 200 else "✓"
        v10_status = "⚠️" if abs(v10_diff) > 200 else "✓"

        print(f"{inp:<8} "
              f"{v9_quads[inp]:<10} "
              f"{v10_quads[inp]:<10} "
              f"{v9_diff:+10} "
              f"{v10_diff:+10} "
              f"{v9_status} → {v10_status}")

    # グラフ生成
    print("\n[Step 3] 比較グラフを生成中...")
    plot_comparison(v9_quads, v10_quads, v7_quads)

    # ファイル出力
    print("\n[Step 4] Quadファイルを出力中...")
    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"
    quad_file = f"{base_path}/PX1V-PtPd-SP1v11.quad"

    write_quad_file(v10_quads, v9_header, quad_file)
    print(f"✓ Quadファイル: PX1V-PtPd-SP1v11.quad")

    # サマリー
    print("\n" + "=" * 80)
    print("SP1v11カーブ生成完了")
    print("=" * 80)

    def quad_to_density(quad, max_density=1.73, max_quad=55891):
        return quad * max_density / max_quad

    print(f"\n【修正内容】")
    print(f"✓ Input 0-16: S字カーブ（シャドウ部の階調を保持）")
    print(f"✓ Input 17-126: V9のまま維持（スムーズな接続を保持）")
    print(f"✓ Input 127-134: リニア補間（濃度逆転を完全に解消）")
    print(f"✓ Input 135-240: V9を+8シフト（コントラスト調整）")
    print(f"✓ Input 241-248: リニア補間（240から248へ滑らかに接続）")
    print(f"✓ Input 248: 1.29Dに設定（{v10_quads[248]} Quad = {quad_to_density(v10_quads[248]):.2f}D）")
    print(f"✓ Input 249-254: リニア補間（248から255へ滑らかに接続）")
    print(f"✓ Input 255: V7[255]値（{v7_quads[255]} = {quad_to_density(v7_quads[255]):.2f}D）を使用")

    print(f"\n【バンディングリスク】")
    if len(new_risks) == 0:
        print(f"✓ 新たなリスク箇所なし")
    elif len(new_risks) < 10:
        print(f"△ 新たなリスク箇所: {len(new_risks)}箇所（許容範囲内）")
    else:
        print(f"⚠️ 新たなリスク箇所: {len(new_risks)}箇所（要確認）")

    print(f"\n【次のステップ】")
    print(f"1. グラフを確認してバンディングリスクを評価")
    print(f"2. 問題なければQTRプリンタにインストール")
    print(f"3. テストプリントで実際の効果を確認")

if __name__ == "__main__":
    main()
