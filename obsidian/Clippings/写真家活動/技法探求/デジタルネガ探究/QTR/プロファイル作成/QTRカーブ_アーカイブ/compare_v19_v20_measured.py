#!/usr/bin/env python3
"""
V19とV20の実測値比較スクリプト

目的:
- V20で-0.04D下げる設計だったが、実測では変化がほとんどない
- 原因を特定するため、V19とV20のQuad値と実測値を詳細比較

実行日: 2026-03-19
作成者: Claude Code
"""

import pandas as pd
import numpy as np

def load_quad_values():
    """V19とV20のQuad値を読み込む"""

    def load_curve(path):
        with open(path, 'r') as f:
            lines = f.readlines()

        k_data = []
        in_k_channel = False

        for line in lines:
            if line.strip() == "# K curve":
                in_k_channel = True
                continue
            elif line.strip().startswith("# C curve"):
                break

            if in_k_channel and not line.startswith('#'):
                try:
                    quad = int(line.strip())
                    k_data.append(quad)
                except ValueError:
                    continue

        return np.array(k_data, dtype=int)

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"

    v19_quads = load_curve(f"{base_path}/PX1V-PtPd-SP1v19.quad")
    v20_quads = load_curve(f"{base_path}/PX1V-PtPd-SP1v20.quad")

    return v19_quads, v20_quads

def quad_to_density(quad):
    """Quad値を濃度に変換"""
    return quad * 1.73 / 55891

def load_measured_data():
    """V19とV20の実測データを読み込む"""

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/使用チャート/新デジネガ/v2-補正"

    # V19実測データ
    v19_df = pd.read_csv(f"{base_path}/measurement_QTR-SP-19.csv")
    v19_df.columns = ['input', 'v19_density', 'v18_density', 'v7_density']

    # V20実測データ
    v20_df = pd.read_csv(f"{base_path}/measurement_QTR-SP-20.csv")
    v20_df.columns = ['input', 'v20_density']

    # マージ
    df = pd.merge(v19_df[['input', 'v19_density']], v20_df, on='input', how='outer')

    return df

def main():
    print("=" * 80)
    print("V19 vs V20 実測値比較分析")
    print("=" * 80)

    # Quad値読み込み
    print("\n[Step 1] Quad値読み込み...")
    v19_quads, v20_quads = load_quad_values()
    print(f"✓ V19: {len(v19_quads)}点")
    print(f"✓ V20: {len(v20_quads)}点")

    # 実測データ読み込み
    print("\n[Step 2] 実測データ読み込み...")
    measured_df = load_measured_data()
    print(f"✓ 測定点数: {len(measured_df)}点")

    # Input 220-255の詳細比較
    print("\n" + "=" * 80)
    print("Input 220-255の詳細比較")
    print("=" * 80)

    print(f"\n{'Input':<8} {'V19 Quad':<10} {'V20 Quad':<10} {'Δ Quad':<10} {'V19設計D':<12} {'V20設計D':<12} {'Δ設計D':<10}")
    print("-" * 90)

    for inp in range(220, 256):
        if inp < len(v19_quads) and inp < len(v20_quads):
            v19_q = v19_quads[inp]
            v20_q = v20_quads[inp]
            delta_q = v20_q - v19_q
            v19_d = quad_to_density(v19_q)
            v20_d = quad_to_density(v20_q)
            delta_d = v20_d - v19_d

            marker = ""
            if inp in [240, 248, 255]:
                marker = " ← ターゲット"

            print(f"{inp:<8} {v19_q:<10} {v20_q:<10} {delta_q:+<10} {v19_d:<12.4f} {v20_d:<12.4f} {delta_d:+.4f}D{marker}")

    # 実測値の比較
    print("\n" + "=" * 80)
    print("実測値の比較（ハイライト部分）")
    print("=" * 80)

    highlight_df = measured_df[measured_df['input'] >= 220].copy()

    print(f"\n{'Input':<8} {'V19実測D':<12} {'V20実測D':<12} {'Δ実測D':<12} {'期待Δ':<10} {'判定':<10}")
    print("-" * 75)

    for _, row in highlight_df.iterrows():
        inp = int(row['input'])
        v19_measured = row['v19_density']
        v20_measured = row['v20_density']

        if pd.notna(v19_measured) and pd.notna(v20_measured):
            delta_measured = v20_measured - v19_measured

            # 期待される変化（設計上）
            if inp < len(v19_quads) and inp < len(v20_quads):
                v19_design = quad_to_density(v19_quads[inp])
                v20_design = quad_to_density(v20_quads[inp])
                expected_delta = v20_design - v19_design
            else:
                expected_delta = 0

            # 判定
            if abs(delta_measured) < 0.02:
                judgment = "変化なし"
            elif abs(delta_measured - expected_delta) < 0.02:
                judgment = "✓ 期待通り"
            else:
                judgment = "⚠️ 予想外"

            marker = ""
            if inp in [240, 248, 255]:
                marker = " ← 調整箇所"

            print(f"{inp:<8} {v19_measured:<12.2f} {v20_measured:<12.2f} {delta_measured:+<12.3f} {expected_delta:+.4f}D   {judgment:<10}{marker}")

    # サマリー
    print("\n" + "=" * 80)
    print("分析結果")
    print("=" * 80)

    # Input 240/248/255の詳細
    target_inputs = [240, 248, 255]

    print("\n【調整箇所の検証】")
    for inp in target_inputs:
        row = measured_df[measured_df['input'] == inp]
        if not row.empty:
            v19_m = row['v19_density'].values[0]
            v20_m = row['v20_density'].values[0]
            delta_m = v20_m - v19_m

            if inp < len(v19_quads) and inp < len(v20_quads):
                v19_design = quad_to_density(v19_quads[inp])
                v20_design = quad_to_density(v20_quads[inp])
                delta_design = v20_design - v19_design

                print(f"\nInput {inp}:")
                print(f"  設計上の変化: {delta_design:+.4f}D (V19: {v19_design:.4f}D → V20: {v20_design:.4f}D)")
                print(f"  実測上の変化: {delta_m:+.3f}D (V19: {v19_m:.2f}D → V20: {v20_m:.2f}D)")
                print(f"  乖離: {abs(delta_m - delta_design):.4f}D")

                if abs(delta_m) < 0.02:
                    print(f"  判定: ⚠️ 実測値はほとんど変化していない")
                elif abs(delta_m - delta_design) > 0.03:
                    print(f"  判定: ⚠️ 設計と実測に大きな乖離がある")

    # 考えられる原因
    print("\n【考えられる原因】")
    print("1. **Quad値の変化が小さすぎる**")
    print("   - Input 240: Δ=-1452 Quad (約-0.04D)")
    print("   - 濃度計の測定誤差±0.01〜0.02Dでは検出困難")

    print("\n2. **ネガ露光条件の影響**")
    print("   - V19とV20で露光時間やUV光源の状態が微妙に異なる可能性")
    print("   - ハイライト領域（高濃度）では特に影響を受けやすい")

    print("\n3. **非線形応答**")
    print("   - Quad値と実際のネガ濃度の関係が完全に線形ではない")
    print("   - ハイライト領域では変換係数1.73/55891が適切でない可能性")

    print("\n【推奨対応】")
    print("1. より大きな調整（-0.08D以上）を試す → SP1v21")
    print("2. 複数回測定して平均を取る")
    print("3. V19の実測値（1.17D/1.24D/1.29D）を受け入れて使用")

if __name__ == "__main__":
    main()
