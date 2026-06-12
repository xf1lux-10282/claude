#!/usr/bin/env python3
"""
逆カーブのロジック検証テスト

目的: LUTの方向性が正しいか確認
"""

import numpy as np
from scipy import interpolate

print("=" * 70)
print("  逆カーブ ロジック検証")
print("=" * 70)
print()

# === シミュレーション: プリンターの非線形 ===
print("=== ステップ1: プリンター特性 (入力 → ネガ濃度) ===")
print()

# 仮想測定データ: プリンターは非線形
# 入力値が大きいほど、ネガ濃度は低くなる(明るくなる)
input_vals = np.array([0, 64, 128, 192, 255])
# ネガ濃度: 入力0で1.5(濃い)、255で0.1(薄い)
# しかし非線形(中間が予想より高い)
negative_density = np.array([1.5, 1.1, 0.8, 0.4, 0.1])

print("測定データ:")
for i, nd in zip(input_vals, negative_density):
    print(f"  入力 {i:3d} → ネガ濃度 {nd:.2f}")

# スプライン補間
printer_curve = interpolate.CubicSpline(input_vals, negative_density)

print()

# === ステップ2: 理想カーブ ===
print("=== ステップ2: 理想のネガ濃度カーブ (γ=1.8) ===")
print()

gamma = 1.8
dmin = 0.1
dmax = 1.5
density_range = dmax - dmin

def ideal_negative_density(x):
    """理想: 入力 → ネガ濃度"""
    normalized = x / 255.0
    return dmax - density_range * (normalized ** gamma)

print("理想カーブ:")
for i in input_vals:
    ideal_d = ideal_negative_density(i)
    print(f"  入力 {i:3d} → ネガ濃度 {ideal_d:.2f}")

print()

# === ステップ3: 逆カーブ生成 ===
print("=== ステップ3: 補正カーブ生成 ===")
print()

# 逆関数: ネガ濃度 → 入力値
# (ネガ濃度を逆順でソート)
neg_dens_sorted = negative_density[::-1]  # 小→大
input_sorted = input_vals[::-1]           # 大→小
inverse_printer_curve = interpolate.CubicSpline(neg_dens_sorted, input_sorted)

print("補正カーブの生成:")
print("(各入力値に対して、理想の濃度を出すために必要な実際の入力値を計算)")
print()

correction_curve = []

for input_val in input_vals:
    # この入力値が出すべき理想のネガ濃度
    ideal_dens = ideal_negative_density(input_val)

    # その濃度を実際に出すために必要な入力値
    corrected_input = inverse_printer_curve(ideal_dens)

    correction_curve.append((input_val, corrected_input))

    print(f"  入力 {input_val:3d}:")
    print(f"    理想ネガ濃度: {ideal_dens:.2f}")
    print(f"    → 実際の入力: {corrected_input:.1f}")

print()

# === ステップ4: 検証 ===
print("=== ステップ4: 補正カーブの効果を検証 ===")
print()

print("補正なし (実測カーブ):")
for i in input_vals:
    actual_dens = printer_curve(i)
    ideal_dens = ideal_negative_density(i)
    error = actual_dens - ideal_dens
    print(f"  入力 {i:3d} → 実測 {actual_dens:.2f}, 理想 {ideal_dens:.2f}, 誤差 {error:+.2f}")

print()
print("補正あり (LUT適用後):")
for input_val, corrected_input in correction_curve:
    # LUTを通した後の実際の濃度
    actual_dens = printer_curve(corrected_input)
    ideal_dens = ideal_negative_density(input_val)
    error = actual_dens - ideal_dens
    print(f"  入力 {input_val:3d} → LUT[{input_val}]={corrected_input:.1f} → 実測 {actual_dens:.2f}, 理想 {ideal_dens:.2f}, 誤差 {error:+.2f}")

print()
print("=" * 70)
print("結論:")
print("  補正後の誤差が小さくなっていれば、逆カーブは正しい方向です")
print("=" * 70)
