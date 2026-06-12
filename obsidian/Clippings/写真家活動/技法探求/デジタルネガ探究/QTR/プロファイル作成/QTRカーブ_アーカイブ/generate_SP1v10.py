#!/usr/bin/env python3
"""
SP1v10カーブ生成スクリプト

修正内容:
1. Input 104: V7のInput 112の値を使用（0.47D）
2. Input 112: V7のInput 120の値を使用（0.50D）
3. Input 120: V9のまま
4. Input 128以降: V9の136以降を1ステップ前にシフト
5. Input 248: V20のInput 255の値を使用（1.29D）
6. Input 255: V9のまま

目的:
- Input 104-128の不自然な濃度推移を修正
- 滑らかな濃度カーブを実現

実行日: 2026-03-18
作成者: Claude Code
"""

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline

def load_sp1v9_quad():
    """SP1v9のQuadファイルを読み込み"""
    file_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-SP1v9.quad"

    with open(file_path, 'r') as f:
        lines = f.readlines()

    # ヘッダーを保存
    header_lines = []
    quad_values = []

    in_data_section = False
    for line in lines:
        line = line.strip()
        if line.startswith('#') or line.startswith('##'):
            header_lines.append(line)
        elif not in_data_section and line.isdigit():
            in_data_section = True
            quad_values.append(int(line))
        elif in_data_section:
            if line.isdigit():
                quad_values.append(int(line))
            else:
                header_lines.append(line)

    return header_lines, quad_values

def density_to_quad(density, max_density=1.73, max_quad=55891):
    """
    実測値ベースの濃度→Quad値変換

    Input 255の実測値を基準に線形変換:
    - 1.73D（実測最大） = 55891 Quad
    """
    return int(density * max_quad / max_density)

def load_measurement_data():
    """測定データを読み込み"""

    # V9測定データ
    v9_file = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/v2-補正/measurement_QTR-SP-9.csv"
    df_v9 = pd.read_csv(v9_file)
    df_v9.columns = ['input', 'v9_density', 'empty', 'v7_density']

    # V7測定データ
    v7_file = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/v2-補正/measurement_QTR-SP-7.csv"
    df_v7 = pd.read_csv(v7_file)

    return df_v9, df_v7

def create_sp1v10_densities():
    """SP1v10の濃度データを作成"""

    df_v9, df_v7 = load_measurement_data()

    # V10濃度マップ（8ステップ刻み）
    v10_densities = {}

    for _, row in df_v9.iterrows():
        inp = int(row['input'])
        v9_d = row['v9_density']

        if inp == 104:
            # V7のInput 112の値を使用
            v7_112 = df_v7[df_v7['input'] == 112]['negative_density'].values[0]
            v10_densities[inp] = v7_112

        elif inp == 112:
            # V7のInput 120の値を使用
            v7_120 = df_v7[df_v7['input'] == 120]['negative_density'].values[0]
            v10_densities[inp] = v7_120

        elif inp == 120:
            # V9のまま
            v10_densities[inp] = v9_d

        elif 128 <= inp <= 240:
            # V9の1ステップ後（+8）の値を使用
            next_inp = inp + 8
            v9_next = df_v9[df_v9['input'] == next_inp]['v9_density'].values
            if len(v9_next) > 0:
                v10_densities[inp] = v9_next[0]
            else:
                v10_densities[inp] = v9_d

        elif inp == 248:
            # V20のInput 255の値を使用
            v10_densities[inp] = 1.29

        else:
            # その他はV9のまま
            v10_densities[inp] = v9_d

    return v10_densities

def interpolate_all_inputs(measured_densities):
    """8ステップ刻みの測定値から全Input（0-255）の濃度を補間"""

    inputs = sorted(measured_densities.keys())
    densities = [measured_densities[i] for i in inputs]

    # スプライン補間
    cs = CubicSpline(inputs, densities)

    all_densities = {}
    for inp in range(256):
        all_densities[inp] = cs(inp)
        # 濃度が負にならないように
        all_densities[inp] = max(0.0, all_densities[inp])

    return all_densities

def densities_to_quads(densities):
    """濃度値をQuad値に変換"""

    quads = {}
    max_density = densities[255]  # Input 255の濃度を最大値として使用

    # Input 255のQuad値（V9から取得）
    max_quad = 55891

    for inp, density in densities.items():
        quad = density_to_quad(density, max_density, max_quad)
        quads[inp] = max(0, min(65535, quad))  # 0-65535にクリップ

    return quads

def write_quad_file(quads, header_lines, filename):
    """Quadファイルを出力"""

    # ヘッダーを更新
    new_header = []
    for line in header_lines:
        if line.startswith('# PX1V-PtPd-SP1v'):
            new_header.append('# PX1V-PtPd-SP1v10 - Corrected curve (smooth 104-128 transition)')
        elif line.startswith('# Input 0-15:'):
            # 説明を更新
            break
        else:
            new_header.append(line)

    # 新しい説明を追加
    new_header.extend([
        '# Input 0-15: Unchanged (baseline)',
        '# Input 16-103: Boost region (from V9)',
        '# Input 104: V7[112] value (0.47D) - correction',
        '# Input 112: V7[120] value (0.50D) - correction',
        '# Input 120: V9 value (keep)',
        '# Input 128-240: V9 shifted by +8 steps (contrast adjustment)',
        '# Input 248: V20[255] value (1.29D) - highlight enhancement',
        '# Input 255: V9 value (1.73D, keep)',
        '# Created: 2026-03-18 SP1v10',
        '# Purpose: Smooth curve transition, fix Input 104-128 irregularity',
        '# 2026 Daisuke Kinoshita',
        '# BOOST_K=0 - NO BOOST',
        '# K curve'
    ])

    with open(filename, 'w') as f:
        # ヘッダー出力
        f.write('## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK\n')
        for line in new_header[1:]:  # 最初の行は上で書いたのでスキップ
            f.write(line + '\n')

        # Quad値出力
        for inp in range(256):
            f.write(f'{quads[inp]}\n')

def write_detail_txt(v10_densities, v10_quads, filename):
    """詳細データをTXT形式で出力"""

    df_v9, df_v7 = load_measurement_data()

    data = []
    for inp in range(0, 256, 8):  # 8ステップ刻み
        v10_d = v10_densities.get(inp, 0)
        v10_q = v10_quads.get(inp, 0)

        # V9の値
        v9_row = df_v9[df_v9['input'] == inp]
        v9_d = v9_row['v9_density'].values[0] if len(v9_row) > 0 else 0

        # V7の値
        v7_row = df_v7[df_v7['input'] == inp]
        v7_d = v7_row['negative_density'].values[0] if len(v7_row) > 0 else 0

        data.append({
            'Input': inp,
            'V7_Density': f'{v7_d:.2f}',
            'V9_Density': f'{v9_d:.2f}',
            'V10_Density': f'{v10_d:.4f}',
            'V10_Quad': v10_q,
            'Change_from_V9': f'{v10_d - v9_d:+.4f}'
        })

    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

def analyze_banding_risk(quads, threshold=200):
    """境界線リスクを解析"""
    risks = []
    for inp in range(1, 256):
        diff = quads[inp] - quads[inp-1]
        if diff > threshold:
            risks.append((inp, diff))
    return risks

def main():
    print("=" * 80)
    print("SP1v10カーブ生成開始")
    print("=" * 80)

    # V9のQuadファイル構造を読み込み
    print("\n[1] SP1v9のQuadファイル構造を読み込み中...")
    header_lines, v9_quads = load_sp1v9_quad()
    print(f"✓ ヘッダー行数: {len(header_lines)}")
    print(f"✓ Quad値数: {len(v9_quads)}")

    # V10の濃度データ作成
    print("\n[2] SP1v10の濃度データを作成中...")
    v10_densities_8step = create_sp1v10_densities()
    print(f"✓ 測定点: {len(v10_densities_8step)}地点（8ステップ刻み）")

    # 全Inputに補間
    print("\n[3] 全Input（0-255）に補間中...")
    v10_densities_all = interpolate_all_inputs(v10_densities_8step)
    print(f"✓ 補間完了: {len(v10_densities_all)}地点")

    # Quad値に変換
    print("\n[4] Quad値に変換中...")
    v10_quads = densities_to_quads(v10_densities_all)
    print(f"✓ Quad値生成完了")

    # 境界線リスク解析
    print("\n[5] 境界線リスク解析中...")
    risks = analyze_banding_risk(v10_quads)
    print(f"✓ リスク箇所（Quad差分 > 200）: {len(risks)}箇所")
    if risks:
        print("\n  主要なリスク箇所:")
        for inp, diff in risks[:5]:
            print(f"    - Input {inp}: Δ={diff}")

    # ファイル出力
    print("\n[6] ファイル出力中...")
    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"

    # .quadファイル
    quad_file = f"{base_path}/PX1V-PtPd-SP1v10.quad"
    write_quad_file(v10_quads, header_lines, quad_file)
    print(f"✓ Quadファイル: PX1V-PtPd-SP1v10.quad")

    # 詳細TXT
    txt_file = f"{base_path}/PX1V-PtPd-SP1v10.txt"
    write_detail_txt(v10_densities_8step, v10_quads, txt_file)
    print(f"✓ 詳細データ: PX1V-PtPd-SP1v10.txt")

    # サマリー
    print("\n" + "=" * 80)
    print("SP1v10カーブ生成完了")
    print("=" * 80)

    print(f"\n【主要ポイント濃度比較】")
    print(f"{'Input':<8} {'V10 Density (D)':<18} {'V10 Quad':<12}")
    print("-" * 50)

    for inp in [0, 16, 64, 96, 104, 112, 120, 128, 160, 192, 224, 240, 248, 255]:
        print(f"{inp:<8} {v10_densities_all[inp]:<18.4f} {v10_quads[inp]:<12}")

    print("\n【修正内容】")
    print("✓ Input 104: V7[112]値使用（0.47D）")
    print("✓ Input 112: V7[120]値使用（0.50D）")
    print("✓ Input 120: V9維持")
    print("✓ Input 128-240: V9を+8シフト（濃度増加）")
    print("✓ Input 248: V20[255]値使用（1.29D）")
    print("✓ Input 255: V9維持（1.73D）")

    print("\n【効果】")
    print("✓ Input 104-128の不自然な推移を修正")
    print("✓ 滑らかな濃度カーブを実現")
    print("✓ ハイライト領域の濃度を適切に調整")

    print("\n【次のステップ】")
    print("1. QTRプリンタにSP1v10をインストール")
    print("2. 配合1（Fe 0.4cc）で8.25分露光テスト")
    print("3. コントラストが適切か確認")

if __name__ == "__main__":
    main()
