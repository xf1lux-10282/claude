#!/usr/bin/env python3
"""
Input 248=30500 指定、24-248均等補間の分析
"""
import numpy as np

# Zone 1: Shadow (0-24) - 既存と同じ
zone1_k_values = []
for i in range(0, 25):
    k = round(4148 * i / 24)
    zone1_k_values.append(k)

# Zone 2 拡張: Midtone (24-248) - 均等補間
zone2_k_start = 4148
zone2_k_end = 30500  # ユーザー指定値
zone2_steps = 248 - 24  # 224 steps
zone2_extended_k_values = []

for i in range(1, zone2_steps + 1):  # 24から248まで
    k = round(zone2_k_start + (zone2_k_end - zone2_k_start) * i / zone2_steps)
    zone2_extended_k_values.append(k)

# Zone 2の勾配計算
zone2_gradient = (zone2_k_end - zone2_k_start) / zone2_steps

print("=== Input 248=30500、24-248均等補間の場合 ===")
print(f"Input 248: K = {zone2_k_end}")
print(f"Zone 2 (24-248) 勾配: {zone2_gradient:.1f} K/step")

# Zone 3: Highlight (248-255) - v12と同じ
v12_k_248 = 31793
v12_k_255 = 33800
zone3_steps = 255 - 248  # 7 steps

# Option A: 248→255を線形補間
zone3_k_values_linear = []
for i in range(1, zone3_steps + 1):
    k = round(zone2_k_end + (v12_k_255 - zone2_k_end) * i / zone3_steps)
    zone3_k_values_linear.append(k)

zone3_gradient = (v12_k_255 - zone2_k_end) / zone3_steps

print(f"\n=== Zone 3 (248-255) 線形補間 ===")
print(f"Input 249: {zone3_k_values_linear[0]}")
print(f"Input 250: {zone3_k_values_linear[1]}")
print(f"Input 251: {zone3_k_values_linear[2]}")
print(f"Input 252: {zone3_k_values_linear[3]}")
print(f"Input 253: {zone3_k_values_linear[4]}")
print(f"Input 254: {zone3_k_values_linear[5]}")
print(f"Input 255: {zone3_k_values_linear[6]}")
print(f"\nZone 3 (248-255) 勾配: {zone3_gradient:.1f} K/step")

# 勾配比計算
gradient_ratio = zone3_gradient / zone2_gradient

print(f"\n=== 勾配比分析 ===")
print(f"Zone 2 (24-248): {zone2_gradient:.1f} K/step")
print(f"Zone 3 (248-255): {zone3_gradient:.1f} K/step")
print(f"勾配比 (Zone3/Zone2): {gradient_ratio:.2f}")

# 勾配比の評価
if gradient_ratio <= 2.5:
    print(f"✓ 勾配比{gradient_ratio:.2f}は理想範囲(2.0-2.5)内です")
elif gradient_ratio <= 2.7:
    print(f"⚠️  勾配比{gradient_ratio:.2f}が理想範囲(2.0-2.5)をわずかに超えていますが許容範囲です")
else:
    print(f"❌ 勾配比{gradient_ratio:.2f}が許容範囲(2.7以下)を超えています")

# 全K-valuesリスト作成
k_values_full = zone1_k_values + zone2_extended_k_values + zone3_k_values_linear

# 全体勾配分析
gradients = np.diff(k_values_full)
zone1_grad = gradients[0:24].mean()
zone2_grad = gradients[24:248].mean()
zone3_grad = gradients[248:255].mean()

print(f"\n=== 全体勾配分析 ===")
print(f"Zone 1 (0-24):     {zone1_grad:.1f} K/step")
print(f"Zone 2 (24-248):   {zone2_grad:.1f} K/step")
print(f"Zone 3 (248-255):  {zone3_grad:.1f} K/step")
print(f"勾配比 (Zone3/Zone2): {zone3_grad / zone2_grad:.2f}")

# v12との比較
v12_k_values = {
    0: 0, 24: 4148, 32: 5087, 64: 8843, 104: 13538, 128: 16355,
    176: 21988, 192: 23866, 232: 28561, 240: 29500, 248: 31793, 255: 33800
}

print(f"\n=== v12との比較 ===")
print(f"Input | v12    | 新案(248=30500) | 差分    | 差分%")
print(f"------|--------|-----------------|---------|-------")

for inp in [0, 24, 32, 64, 104, 128, 176, 192, 232, 240, 248, 255]:
    v12_k = v12_k_values[inp]
    new_k = k_values_full[inp]
    diff = new_k - v12_k
    diff_percent = (diff / v12_k * 100) if v12_k > 0 else 0.0
    print(f"{inp:5} | {v12_k:6} | {new_k:15} | {diff:+7} | {diff_percent:+6.2f}%")

# v13-MT-R1との比較
v13_mt_r1_k_values = {
    0: 0, 24: 4148, 32: 5028, 64: 8548, 104: 12948, 128: 15588,
    176: 20868, 192: 22628, 232: 28000, 240: 29500, 248: 31793, 255: 33800
}

print(f"\n=== v13-MT-R1（現行版）との比較 ===")
print(f"Input | v13-MT-R1 | 新案(248=30500) | 差分    | 差分%")
print(f"------|-----------|-----------------|---------|-------")

for inp in [0, 24, 32, 64, 104, 128, 176, 192, 232, 240, 248, 255]:
    r1_k = v13_mt_r1_k_values[inp]
    new_k = k_values_full[inp]
    diff = new_k - r1_k
    diff_percent = (diff / r1_k * 100) if r1_k > 0 else 0.0
    print(f"{inp:5} | {r1_k:9} | {new_k:15} | {diff:+7} | {diff_percent:+6.2f}%")

# ミッドトーン最適化の効果
print(f"\n=== ミッドトーン最適化の効果 ===")
print(f"Input 128: {k_values_full[128]} (v12: {v12_k_values[128]}, {k_values_full[128] - v12_k_values[128]:+d})")
print(f"Input 192: {k_values_full[192]} (v12: {v12_k_values[192]}, {k_values_full[192] - v12_k_values[192]:+d})")

# Zone 2の最大K-value低下地点
max_diff_input = None
max_diff_value = 0
for inp in range(24, 249):
    if inp in v12_k_values:
        diff = abs(k_values_full[inp] - v12_k_values[inp])
        if diff > max_diff_value:
            max_diff_value = diff
            max_diff_input = inp

if max_diff_input:
    print(f"\n最大K-value低下地点: Input {max_diff_input}, 差分 -{max_diff_value}")

print(f"\n=== 主要特性 ===")
print(f"K_max: {k_values_full[255]} (v12と同じ, 紙白到達保証)")
print(f"Input 248: {zone2_k_end} (v12: {v12_k_248}, {zone2_k_end - v12_k_248:+d}, {((zone2_k_end/v12_k_248-1)*100):+.2f}%)")
print(f"勾配比: {gradient_ratio:.2f}")
print(f"露光時間: 6.5min (v12と同じ推奨)")
