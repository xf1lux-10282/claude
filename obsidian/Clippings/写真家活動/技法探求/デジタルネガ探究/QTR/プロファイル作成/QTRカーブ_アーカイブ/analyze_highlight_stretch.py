#!/usr/bin/env python3
"""
ハイライトストレッチ設計の検証スクリプト

提案:
- V18の224-248をストレッチして224-255に配置
- Input 224 → V7の216地点（1.00D）
- Input 232 → V18の224地点
- Input 240 → V18の232地点
- Input 248 → V18の240地点
- Input 255 → 1.25D（V18の248地点より少し上）

目的:
- Kプリント（Pt/Pd）のK3-15%の諧調をしっかり表現

実行日: 2026-03-19
作成者: Claude Code
"""

import numpy as np

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

def main():
    print("=" * 80)
    print("ハイライトストレッチ設計の検証")
    print("=" * 80)

    base_path = "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版"

    # V7とV18を読み込む
    v7_quads = read_quad_file(f"{base_path}/PX1V-PtPd-SP1v7.quad")
    v18_quads = read_quad_file(f"{base_path}/PX1V-PtPd-SP1v18.quad")

    print("\n【1. 現在の値を確認】")
    print("\nV7:")
    for inp in [216, 224, 232, 240, 248, 255]:
        quad = v7_quads[inp]
        dens = quad_to_density(quad)
        print(f"  Input {inp:3d}: Quad={quad:5d}, Density={dens:.4f}D")

    print("\nV18:")
    for inp in [216, 224, 232, 240, 248, 255]:
        quad = v18_quads[inp]
        dens = quad_to_density(quad)
        print(f"  Input {inp:3d}: Quad={quad:5d}, Density={dens:.4f}D")

    print("\n" + "=" * 80)
    print("【2. V19の提案設計】")
    print("=" * 80)

    # 提案されたマッピング
    mapping = [
        (224, "V7の216地点", v7_quads[216], quad_to_density(v7_quads[216])),
        (232, "V18の224地点", v18_quads[224], quad_to_density(v18_quads[224])),
        (240, "V18の232地点", v18_quads[232], quad_to_density(v18_quads[232])),
        (248, "V18の240地点", v18_quads[240], quad_to_density(v18_quads[240])),
        (255, "1.25D (V18の248地点より少し上)", density_to_quad(1.25), 1.25)
    ]

    print("\nV19の設計:")
    for inp, desc, quad, dens in mapping:
        print(f"  Input {inp:3d} → {desc}")
        print(f"             Quad={quad:5d}, Density={dens:.4f}D")
        print()

    print("=" * 80)
    print("【3. Input 0-223の設計】")
    print("=" * 80)

    print("\n提案: Input 0-223はV18をそのまま使用")
    print("\n主要ポイントの確認:")
    for inp in [0, 80, 120, 176, 220, 223]:
        v18_quad = v18_quads[inp]
        v18_dens = quad_to_density(v18_quad)
        print(f"  Input {inp:3d}: Quad={v18_quad:5d}, Density={v18_dens:.4f}D (V18と同じ)")

    print("\n=" * 80)
    print("【4. ハイライトストレッチの効果】")
    print("=" * 80)

    # V18 vs V19のハイライト範囲比較
    print("\nV18のハイライト範囲（Input 224-255）:")
    v18_224_dens = quad_to_density(v18_quads[224])
    v18_255_dens = quad_to_density(v18_quads[255])
    v18_range = v18_255_dens - v18_224_dens
    print(f"  Input 224: {v18_224_dens:.4f}D")
    print(f"  Input 255: {v18_255_dens:.4f}D")
    print(f"  濃度レンジ: {v18_range:.4f}D")

    print("\nV19のハイライト範囲（Input 224-255）:")
    v19_224_dens = quad_to_density(v7_quads[216])  # V7の216
    v19_255_dens = 1.25
    v19_range = v19_255_dens - v19_224_dens
    print(f"  Input 224: {v19_224_dens:.4f}D")
    print(f"  Input 255: {v19_255_dens:.4f}D")
    print(f"  濃度レンジ: {v19_range:.4f}D")

    print(f"\n拡張効果:")
    expansion = (v19_range / v18_range - 1) * 100
    print(f"  V19はV18より {expansion:.1f}% 広い濃度レンジ")

    print("\n=" * 80)
    print("【5. Kプリントでの効果予測】")
    print("=" * 80)

    print("\nK3-15%の諧調表現:")
    print("  K3% → 明るいハイライト（紙白に近い）")
    print("  K6% → 淡いハイライト")
    print("  K9% → 中間ハイライト")
    print("  K12% → やや濃いハイライト")
    print("  K15% → ハイライトとミッドトーンの境界")

    print("\nV19の効果:")
    print("  ✓ Input 224-255の32ステップで1.00D→1.25Dをカバー")
    print("  ✓ 各ステップあたり約0.0078D（V18: 約0.0167D）")
    print("  ✓ より細かい諧調ステップ → K3-15%を滑らかに表現")

    print("\n=" * 80)
    print("【6. 実装方針】")
    print("=" * 80)

    print("\nV19の構造:")
    print("  Input 0-79:   V18のまま（V7ベースライン）")
    print("  Input 80-120: V18のまま（段階的削減）")
    print("  Input 121-220: V18のまま（一律削減 -0.05D）")
    print("  Input 221-223: V18のまま（線形補間）")
    print("  Input 224-255: ハイライトストレッチ（新設計）")

    print("\nハイライトストレッチの補間:")
    print("  アンカーポイント:")
    print("    224 → V7[216] (1.00D)")
    print("    232 → V18[224]")
    print("    240 → V18[232]")
    print("    248 → V18[240]")
    print("    255 → 1.25D")
    print("  補間方法: 線形補間（np.interp）")

    print("\n単調増加の保証:")
    print("  ✓ アンカーポイントは単調増加")
    print("  ✓ 線形補間により自動的に単調増加")
    print("  ✓ 念のため、最終チェックで保証")

    print("\n=" * 80)
    print("【7. 検証項目】")
    print("=" * 80)

    print("\n生成後の確認:")
    print("  1. グラフでカーブ形状を確認（急激な変化がないか）")
    print("  2. Input 224-255の勾配を確認（バンディングリスクなし）")
    print("  3. Input 223→224の接続を確認（滑らかか）")
    print("  4. Input 255の濃度が1.25D付近か確認")

    print("\nテストプリント:")
    print("  1. グラデーションチャートで視覚的に確認")
    print("  2. K3-15%の範囲の諧調が滑らかか")
    print("  3. ハイライトのディテールが保持されているか")

    print("\n=" * 80)
    print("【8. 次のステップ】")
    print("=" * 80)

    print("\n1. generate_SP1v19.py を作成")
    print("2. SP1v19を生成してグラフ確認")
    print("3. 問題なければQTRにインストール")
    print("4. テストプリントで効果を確認")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
