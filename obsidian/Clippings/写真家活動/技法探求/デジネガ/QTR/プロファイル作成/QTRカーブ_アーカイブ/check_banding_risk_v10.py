#!/usr/bin/env python3
"""
SP1v10バンディングリスク詳細チェック

目的:
Quad値ベースでの修正案において、バンディングリスクがないか全範囲で確認

実行日: 2026-03-18
"""

import pandas as pd
import matplotlib.pyplot as plt

def read_quad_file(filepath):
    """Quadファイルを読み込んでQuad値のリストを返す"""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    quad_values = []
    for line in lines:
        line = line.strip()
        if line.isdigit():
            quad_values.append(int(line))

    return quad_values

def create_v10_quads():
    """SP1v10のQuad値配列を作成（修正方針に基づく）"""

    # V9とV7のQuadファイルを読み込み
    v9_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-SP1v9.quad"
    v7_path = "/Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-SP1v7.quad"

    v9_quads = read_quad_file(v9_path)
    v7_quads = read_quad_file(v7_path)

    # V10のQuad値配列を作成
    v10_quads = []

    for inp in range(256):
        if inp == 104:
            # V7のInput 112のQuad値を使用
            v10_quads.append(v7_quads[112])

        elif inp == 112:
            # V7のInput 120のQuad値を使用
            v10_quads.append(v7_quads[120])

        elif 128 <= inp <= 240:
            # V9のInput (inp+8)のQuad値を使用
            source_input = inp + 8
            if source_input <= 255:
                v10_quads.append(v9_quads[source_input])
            else:
                v10_quads.append(v9_quads[inp])

        else:
            # その他はV9のまま
            v10_quads.append(v9_quads[inp])

    return v10_quads, v9_quads, v7_quads

def analyze_banding_risk(quads, name, threshold=200):
    """バンディングリスクを全範囲で解析"""

    risks = []
    for inp in range(1, 256):
        diff = quads[inp] - quads[inp-1]
        risks.append({
            'input': inp,
            'quad_prev': quads[inp-1],
            'quad_current': quads[inp],
            'diff': diff,
            'is_risk': abs(diff) > threshold
        })

    df = pd.DataFrame(risks)
    risk_count = len(df[df['is_risk']])

    return df, risk_count

def compare_banding_risks(v9_risks, v10_risks):
    """V9とV10のバンディングリスクを比較"""

    print("\n" + "=" * 100)
    print("【バンディングリスク比較】")
    print("=" * 100)

    # V9のリスク箇所
    v9_risk_inputs = v9_risks[v9_risks['is_risk']]['input'].tolist()
    v10_risk_inputs = v10_risks[v10_risks['is_risk']]['input'].tolist()

    print(f"\nV9のリスク箇所数: {len(v9_risk_inputs)}箇所")
    print(f"V10のリスク箇所数: {len(v10_risk_inputs)}箇所")

    # 新規追加されたリスク
    new_risks = set(v10_risk_inputs) - set(v9_risk_inputs)
    removed_risks = set(v9_risk_inputs) - set(v10_risk_inputs)

    if new_risks:
        print(f"\n⚠️ V10で新たに追加されたリスク箇所: {len(new_risks)}箇所")
        for inp in sorted(new_risks):
            row = v10_risks[v10_risks['input'] == inp].iloc[0]
            print(f"   Input {inp-1}→{inp}: Δ={row['diff']} Quad")
    else:
        print(f"\n✓ V10で新たに追加されたリスク箇所はありません")

    if removed_risks:
        print(f"\n✓ V10で解消されたリスク箇所: {len(removed_risks)}箇所")

    # 修正箇所付近の詳細確認
    print("\n" + "=" * 100)
    print("【修正箇所付近の詳細確認】")
    print("=" * 100)

    critical_regions = [
        (96, 120, "Input 104, 112修正領域"),
        (120, 136, "Input 128シフト開始領域"),
        (240, 256, "Input 248, 255最終領域")
    ]

    for start, end, description in critical_regions:
        print(f"\n{description} (Input {start}-{end-1}):")
        print(f"{'Input':<8} {'V9_Quad':<10} {'V10_Quad':<10} {'V9_Δ':<10} {'V10_Δ':<10} {'リスク':<10}")
        print("-" * 70)

        for inp in range(start, end):
            if inp == 0:
                continue

            v9_row = v9_risks[v9_risks['input'] == inp].iloc[0]
            v10_row = v10_risks[v10_risks['input'] == inp].iloc[0]

            v9_risk_mark = "⚠️" if v9_row['is_risk'] else ""
            v10_risk_mark = "⚠️" if v10_row['is_risk'] else ""

            # 新規リスクは特に強調
            if inp in new_risks:
                v10_risk_mark = "🔴 NEW"

            print(f"{inp:<8} "
                  f"{v9_row['quad_current']:<10} "
                  f"{v10_row['quad_current']:<10} "
                  f"{v9_row['diff']:+10} "
                  f"{v10_row['diff']:+10} "
                  f"{v9_risk_mark:<5} {v10_risk_mark:<5}")

    return new_risks, removed_risks

def plot_banding_comparison(v9_risks, v10_risks):
    """バンディングリスク比較グラフを生成"""

    fig, axes = plt.subplots(3, 1, figsize=(16, 12))

    inputs = v9_risks['input']

    # グラフ1: Quad差分比較
    ax = axes[0]
    ax.plot(inputs, v9_risks['diff'], 'o-', label='V9 Gradient', linewidth=1, markersize=3, alpha=0.7)
    ax.plot(inputs, v10_risks['diff'], 's-', label='V10 Gradient', linewidth=1, markersize=3)
    ax.axhline(y=200, color='red', linestyle='--', alpha=0.5, label='Banding Risk Threshold (+200)')
    ax.axhline(y=-200, color='red', linestyle='--', alpha=0.5)
    ax.axvline(x=104, color='orange', linestyle='--', alpha=0.3)
    ax.axvline(x=112, color='orange', linestyle='--', alpha=0.3)
    ax.axvline(x=128, color='purple', linestyle='--', alpha=0.3)
    ax.axvline(x=240, color='green', linestyle='--', alpha=0.3)
    ax.set_xlabel('Input Value', fontsize=12)
    ax.set_ylabel('Quad Difference (Δ)', fontsize=12)
    ax.set_title('Quad Gradient Comparison (Banding Risk)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-300, 600)

    # グラフ2: 修正箇所の拡大図 (Input 96-144)
    ax = axes[1]
    region1 = v9_risks[(v9_risks['input'] >= 96) & (v9_risks['input'] <= 144)]
    region1_v10 = v10_risks[(v10_risks['input'] >= 96) & (v10_risks['input'] <= 144)]

    ax.plot(region1['input'], region1['diff'], 'o-', label='V9', linewidth=2, markersize=6, alpha=0.7)
    ax.plot(region1_v10['input'], region1_v10['diff'], 's-', label='V10', linewidth=2, markersize=6)
    ax.axhline(y=200, color='red', linestyle='--', linewidth=2, label='Threshold')
    ax.axhline(y=-200, color='red', linestyle='--', linewidth=2)
    ax.axvline(x=104, color='orange', linestyle='--', linewidth=2, label='Correction Points')
    ax.axvline(x=112, color='orange', linestyle='--', linewidth=2)
    ax.axvline(x=128, color='purple', linestyle='--', linewidth=2, label='Shift Start')
    ax.set_xlabel('Input Value', fontsize=12)
    ax.set_ylabel('Quad Difference (Δ)', fontsize=12)
    ax.set_title('Detail: Input 96-144 (Correction Region)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # グラフ3: リスク箇所の分布
    ax = axes[2]

    v9_risk_flags = [1 if risk else 0 for risk in v9_risks['is_risk']]
    v10_risk_flags = [1 if risk else 0 for risk in v10_risks['is_risk']]

    ax.fill_between(inputs, 0, v9_risk_flags, alpha=0.3, color='blue', label='V9 Risk Regions')
    ax.fill_between(inputs, 0, v10_risk_flags, alpha=0.3, color='red', label='V10 Risk Regions')
    ax.axvline(x=104, color='orange', linestyle='--', alpha=0.5)
    ax.axvline(x=112, color='orange', linestyle='--', alpha=0.5)
    ax.axvline(x=128, color='purple', linestyle='--', alpha=0.5)
    ax.set_xlabel('Input Value', fontsize=12)
    ax.set_ylabel('Risk Flag (1=Risk)', fontsize=12)
    ax.set_title('Risk Region Distribution', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/SP1v10_banding_check.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ グラフ保存: SP1v10_banding_check.png")

def main():
    print("=" * 100)
    print("SP1v10バンディングリスク詳細チェック")
    print("=" * 100)

    # V10のQuad値配列を作成
    print("\n[1] V10のQuad値配列を作成中...")
    v10_quads, v9_quads, v7_quads = create_v10_quads()
    print(f"✓ V10 Quad配列作成完了: {len(v10_quads)}値")

    # バンディングリスク解析
    print("\n[2] バンディングリスク解析中...")
    v9_risks, v9_risk_count = analyze_banding_risk(v9_quads, "V9")
    v10_risks, v10_risk_count = analyze_banding_risk(v10_quads, "V10")

    print(f"✓ V9リスク箇所: {v9_risk_count}箇所")
    print(f"✓ V10リスク箇所: {v10_risk_count}箇所")

    # 比較
    new_risks, removed_risks = compare_banding_risks(v9_risks, v10_risks)

    # グラフ生成
    print("\n[3] 比較グラフを生成中...")
    plot_banding_comparison(v9_risks, v10_risks)

    # 最終判断
    print("\n" + "=" * 100)
    print("【最終判断】")
    print("=" * 100)

    if len(new_risks) == 0:
        print("\n✓ V10で新たなバンディングリスクは追加されていません")
        print("✓ この修正方針は安全です")
        print("\n次のステップ: SP1v10.quadファイルを生成")
        return True
    else:
        print(f"\n⚠️ V10で{len(new_risks)}箇所の新たなバンディングリスクが検出されました")
        print("\n新規リスク箇所:")
        for inp in sorted(new_risks):
            row = v10_risks[v10_risks['input'] == inp].iloc[0]
            print(f"  Input {inp-1}→{inp}: Δ={row['diff']} Quad")

        print("\n推奨:")
        print("  1. これらのリスク箇所が実際にバンディングを引き起こすか確認")
        print("  2. 問題がある場合は修正方針を調整")
        print("  3. 許容できる場合はそのまま生成")

        return False

if __name__ == "__main__":
    is_safe = main()
