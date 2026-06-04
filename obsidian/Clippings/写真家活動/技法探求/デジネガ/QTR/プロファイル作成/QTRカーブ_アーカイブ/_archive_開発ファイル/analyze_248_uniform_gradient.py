#!/usr/bin/env python3
"""
Input 248まで110 K/step均等勾配で計算した場合の分析
"""
import numpy as np

# Zone 1: Shadow (0-24) - 既存と同じ
zone1_k_values = []
for i in range(0, 25):
    k = round(4148 * i / 24)
    zone1_k_values.append(k)

# Zone 2 拡張: Midtone (24-248) - 110.0 K/step均等勾配
zone2_extended_k_values = []
zone2_k_start = 4148
target_zone2_grad = 110.0
zone2_steps = 248 - 24  # 224 steps
for i in range(1, zone2_steps + 1):  # 24から248まで
    k = round(zone2_k_start + target_zone2_grad * i)
    zone2_extended_k_values.append(k)

k_248_uniform = zone2_extended_k_values[-1]  # Input 248のK-value

print("=== Input 248まで均等勾配（110 K/step）の場合 ===")
print(f"Input 248: K = {k_248_uniform}")

# v12との比較
v12_k_248 = 31793
v12_k_255 = 33800

print(f"\n=== v12との比較 ===")
print(f"Input 248: {k_248_uniform} (v12: {v12_k_248}, {k_248_uniform - v12_k_248:+d}, {((k_248_uniform/v12_k_248-1)*100):+.2f}%)")
print(f"差分: {v12_k_248 - k_248_uniform} K-value低い")

# Zone 3の設計（248-255）をv12と同じにする場合
print(f"\n=== 249-255をどう設計するか ===")
print(f"Option A: Input 249-255をv12と同じ値にする")
print(f"  Input 248: {k_248_uniform}")
print(f"  Input 249-254: v12の値をそのまま使用")
print(f"  Input 255: {v12_k_255} (v12と同じ)")

# Input 248→255を線形補間する場合
zone3_steps = 255 - 248  # 7 steps
zone3_k_values_linear = []
for i in range(1, zone3_steps + 1):
    k = round(k_248_uniform + (v12_k_255 - k_248_uniform) * i / zone3_steps)
    zone3_k_values_linear.append(k)

print(f"\nOption B: Input 248→255を線形補間")
print(f"  Input 248: {k_248_uniform}")
print(f"  Input 249: {zone3_k_values_linear[0]}")
print(f"  Input 250: {zone3_k_values_linear[1]}")
print(f"  Input 251: {zone3_k_values_linear[2]}")
print(f"  Input 252: {zone3_k_values_linear[3]}")
print(f"  Input 253: {zone3_k_values_linear[4]}")
print(f"  Input 254: {zone3_k_values_linear[5]}")
print(f"  Input 255: {zone3_k_values_linear[6]} (v12: {v12_k_255})")

# 勾配計算
gradient_248_to_255 = (v12_k_255 - k_248_uniform) / zone3_steps
print(f"\n  Input 248→255の勾配: {gradient_248_to_255:.1f} K/step")
print(f"  勾配比 (Zone3/Zone2): {gradient_248_to_255 / target_zone2_grad:.2f}")

# 全体構成（Option Bの場合）
k_values_option_b = zone1_k_values + zone2_extended_k_values + zone3_k_values_linear

# 勾配分析
gradients = np.diff(k_values_option_b)
zone1_grad = gradients[0:24].mean()
zone2_extended_grad = gradients[24:248].mean()
zone3_grad = gradients[248:255].mean()
gradient_ratio = zone3_grad / zone2_extended_grad

print(f"\n=== Option B 全体勾配分析 ===")
print(f"Zone 1 (0-24):     {zone1_grad:.1f} K/step")
print(f"Zone 2 (24-248):   {zone2_extended_grad:.1f} K/step ← 均等勾配")
print(f"Zone 3 (248-255):  {zone3_grad:.1f} K/step")
print(f"勾配比 (Zone3/Zone2): {gradient_ratio:.2f}")

# 勾配比の評価
if gradient_ratio <= 2.5:
    print(f"✓ 勾配比{gradient_ratio:.2f}は理想範囲(2.0-2.5)内です")
elif gradient_ratio <= 2.7:
    print(f"⚠️  勾配比{gradient_ratio:.2f}が理想範囲(2.0-2.5)をわずかに超えていますが許容範囲です")
else:
    print(f"❌ 勾配比{gradient_ratio:.2f}が許容範囲(2.7以下)を超えています")

# v13-MT-R1（現行版）との比較
print(f"\n=== v13-MT-R1（現行版）との比較 ===")
v13_mt_r1_k_232 = 28000
v13_mt_r1_k_240 = 29500
v13_mt_r1_k_248 = 31793

print(f"現行版 Input 232: {v13_mt_r1_k_232}")
print(f"現行版 Input 240: {v13_mt_r1_k_240}")
print(f"現行版 Input 248: {v13_mt_r1_k_248}")

print(f"\n新案 Input 248: {k_248_uniform}")
print(f"差分: {k_248_uniform - v13_mt_r1_k_248:+d} ({((k_248_uniform/v13_mt_r1_k_248-1)*100):+.2f}%)")

# 主要ポイント比較
print(f"\n=== 主要K-values比較 ===")
print(f"Input | v12    | v13-MT-R1 | 新案(248均等) | v12差分 | R1差分")
print(f"------|--------|-----------|---------------|---------|--------")

comparison_points = {
    128: (16355, 15588),
    176: (21988, 20868),
    192: (23866, 22628),
    232: (28561, 28000),
    240: (29500, 29500),
    248: (31793, 31793),
    255: (33800, 33800)
}

# 全K-valuesリスト作成（比較用）
k_values_full = zone1_k_values + zone2_extended_k_values + zone3_k_values_linear

for inp, (v12_k, r1_k) in comparison_points.items():
    new_k = k_values_full[inp]
    v12_diff = new_k - v12_k
    r1_diff = new_k - r1_k
    print(f"{inp:5} | {v12_k:6} | {r1_k:9} | {new_k:13} | {v12_diff:+7} | {r1_diff:+6}")
