#!/usr/bin/env python3
"""
SP1v10修正方針の検証スクリプト

目的:
既存のQuadファイルから直接Quad値を取得し、修正案を検証する

実行日: 2026-03-18
"""

import pandas as pd
import numpy as np

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

def quad_to_density(quad, max_density=1.73, max_quad=55891):
    """Quad値から濃度を推定（参考値）"""
    return quad * max_density / max_quad

def load_measurement_data():
    """測定データを読み込み"""
    v9_file = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/v2-補正/measurement_QTR-SP-9.csv"
    df_v9 = pd.read_csv(v9_file)
    df_v9.columns = ['input', 'v9_density', 'empty', 'v7_density']

    v7_file = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/v2-補正/measurement_QTR-SP-7.csv"
    df_v7 = pd.read_csv(v7_file)

    return df_v9, df_v7

def main():
    print("=" * 100)
    print("SP1v10修正方針の検証")
    print("=" * 100)

    # Quadファイルを読み込み
    print("\n[1] 既存Quadファイルの読み込み")

    v9_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-SP1v9.quad"
    v7_path = "/Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-SP1v7.quad"

    v9_quads = read_quad_file(v9_path)
    v7_quads = read_quad_file(v7_path)

    print(f"✓ V9 Quadファイル読み込み: {len(v9_quads)}値")
    print(f"✓ V7 Quadファイル読み込み: {len(v7_quads)}値")

    # 測定データ読み込み
    df_v9, df_v7 = load_measurement_data()

    # 修正方針を検証
    print("\n[2] 修正方針の検証")
    print("=" * 100)

    modifications = []

    # 各修正箇所を検証
    test_inputs = [0, 8, 16, 96, 104, 112, 120, 128, 136, 144, 152, 160, 192, 224, 240, 248, 255]

    print(f"\n{'Input':<8} {'修正内容':<35} {'V9_Quad':<10} {'修正後Quad':<12} {'V9実測(D)':<12} {'予測(D)':<12}")
    print("-" * 100)

    for inp in test_inputs:
        v9_quad = v9_quads[inp]
        v9_measured = df_v9[df_v9['input'] == inp]['v9_density'].values
        v9_measured_d = v9_measured[0] if len(v9_measured) > 0 else None

        modification = "変更なし"
        new_quad = v9_quad

        if inp == 104:
            # V7のInput 112のQuad値を使用
            new_quad = v7_quads[112]
            modification = "V7[112]のQuad値を使用"

        elif inp == 112:
            # V7のInput 120のQuad値を使用
            new_quad = v7_quads[120]
            modification = "V7[120]のQuad値を使用"

        elif inp == 120:
            # V9のまま
            new_quad = v9_quad
            modification = "V9のまま維持"

        elif 128 <= inp <= 240:
            # V9のInput (inp+8)のQuad値を使用
            source_input = inp + 8
            if source_input <= 248:
                new_quad = v9_quads[source_input]
                modification = f"V9[{source_input}]のQuad値を使用"
            else:
                new_quad = v9_quad
                modification = "V9のまま（範囲外）"

        elif inp == 248:
            # V20のInput 255のQuad値を使用
            # V20ファイルがない場合は、濃度1.29Dから逆算
            # ただし、ここでは一旦V9の値を維持して後で判断
            new_quad = v9_quad
            modification = "要確認: V20[255]値（現在はV9維持）"

        elif inp == 255:
            # V9のまま
            new_quad = v9_quad
            modification = "V9のまま維持"

        # 予測濃度
        predicted_d = quad_to_density(new_quad)

        # 紙白制約チェック
        warning = ""
        if predicted_d > 1.25:
            warning = " ⚠️ 紙白制約超過"

        v9_measured_str = f"{v9_measured_d:.2f}" if v9_measured_d is not None else "N/A"

        print(f"{inp:<8} {modification:<35} {v9_quad:<10} {new_quad:<12} {v9_measured_str:<12} {predicted_d:<12.4f}{warning}")

        modifications.append({
            'input': inp,
            'modification': modification,
            'v9_quad': v9_quad,
            'new_quad': new_quad,
            'v9_measured': v9_measured_d,
            'predicted_density': predicted_d,
            'change': new_quad - v9_quad
        })

    # 重要な確認事項
    print("\n" + "=" * 100)
    print("【重要確認事項】")
    print("=" * 100)

    # 1. Input 255の制約
    inp_255 = [m for m in modifications if m['input'] == 255][0]
    print(f"\n1. Input 255（最重要）:")
    print(f"   V9 Quad: {inp_255['v9_quad']}")
    print(f"   修正後Quad: {inp_255['new_quad']}")
    print(f"   V9実測: {inp_255['v9_measured']:.2f}D")
    print(f"   予測: {inp_255['predicted_density']:.4f}D")
    if inp_255['predicted_density'] > 1.25:
        print(f"   ⚠️ 警告: 紙白制約1.25Dを超過しています！")
    else:
        print(f"   ✓ OK: 紙白制約内")

    # 2. Input 248の制約
    inp_248 = [m for m in modifications if m['input'] == 248][0]
    print(f"\n2. Input 248:")
    print(f"   V9 Quad: {inp_248['v9_quad']}")
    print(f"   修正後Quad: {inp_248['new_quad']}")
    print(f"   V9実測: {inp_248['v9_measured']:.2f}D")
    print(f"   予測: {inp_248['predicted_density']:.4f}D")
    if inp_248['predicted_density'] > 1.25:
        print(f"   ⚠️ 警告: 紙白制約1.25Dを超過しています！")
    else:
        print(f"   ✓ OK: 紙白制約内")

    # 3. シフトによる影響
    print(f"\n3. Input 128-240のシフト影響:")
    shift_mods = [m for m in modifications if 128 <= m['input'] <= 240]
    for m in shift_mods:
        if m['predicted_density'] > 1.25:
            print(f"   ⚠️ Input {m['input']}: {m['predicted_density']:.4f}D > 1.25D")

    any_over = any(m['predicted_density'] > 1.25 for m in shift_mods)
    if not any_over:
        print(f"   ✓ すべて1.25D以内")

    # 4. V20の値について
    print(f"\n4. V20ファイルの確認:")
    print(f"   Input 248にV20[255]の値（1.29D）を使用する計画でしたが、")
    print(f"   これは紙白制約1.25Dを超過します。")
    print(f"   推奨: Input 248はV9のまま維持（1.23D）")

    # 最終判断
    print("\n" + "=" * 100)
    print("【最終判断】")
    print("=" * 100)

    critical_issues = []

    # Input 255チェック
    if inp_255['predicted_density'] > 1.25:
        critical_issues.append(f"Input 255が{inp_255['predicted_density']:.2f}Dで紙白制約超過")

    # Input 248チェック
    if inp_248['change'] != 0:  # 変更がある場合
        print(f"\n注意: Input 248を変更すると制約超過のリスクがあります")
        critical_issues.append("Input 248の変更は推奨されません")

    # シフト領域チェック
    shift_over = [m for m in shift_mods if m['predicted_density'] > 1.25]
    if shift_over:
        for m in shift_over:
            critical_issues.append(f"Input {m['input']}が{m['predicted_density']:.2f}Dで制約超過")

    if critical_issues:
        print("\n⚠️ 重大な問題が検出されました:")
        for issue in critical_issues:
            print(f"   - {issue}")
        print("\n推奨: 修正方針を見直してください")
    else:
        print("\n✓ この修正方針は安全です")
        print("\n次のステップ: SP1v10.quadファイルを生成")

    return modifications, critical_issues

if __name__ == "__main__":
    modifications, issues = main()
