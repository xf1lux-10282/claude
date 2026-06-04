#!/usr/bin/env python3
"""
v14の均等補間（線形補間）検証
"""
import numpy as np

# v14のK-values生成（generate_v14.pyと同じロジック）
def generate_v14():
    # Zone 1: Shadow (0-24)
    zone1_k_values = []
    for i in range(0, 25):
        k = round(4148 * i / 24)
        zone1_k_values.append(k)

    # Zone 2: Midtone (24-239) - 均等勾配
    zone2_k_start = 4148
    target_zone2_grad = 115.0
    zone2_steps = 239 - 24  # 215 steps
    zone2_k_values = []
    for i in range(1, zone2_steps + 1):
        k = round(zone2_k_start + target_zone2_grad * i)
        zone2_k_values.append(k)

    # Input 240
    k_240 = 29400

    # Input 241-247: 240→248を線形補間
    k_248 = 31900
    transition_k_values = []
    steps_240_to_248 = 8
    for i in range(1, steps_240_to_248):  # 241-247
        k = round(k_240 + (k_248 - k_240) * i / steps_240_to_248)
        transition_k_values.append(k)

    # Zone 3: Highlight (248-255) - 線形補間
    zone3_k_start = k_248
    zone3_k_end = 33800
    zone3_steps = 7
    zone3_k_values = []
    for i in range(1, zone3_steps + 1):
        k = round(zone3_k_start + (zone3_k_end - zone3_k_start) * i / zone3_steps)
        zone3_k_values.append(k)

    # 全K-values結合
    k_values = zone1_k_values + zone2_k_values + [k_240] + transition_k_values + [k_248] + zone3_k_values

    return k_values

# K-values生成
k_values = generate_v14()

print("=== v14 均等補間検証 ===\n")

# Zone 1 (0-24) 検証
print("【Zone 1: Shadow (0-24)】")
print("Input 0 → 24 を24分割（理論値: 4148/24 = 172.83 K/step）\n")

gradients_zone1 = np.diff(k_values[0:25])
print(f"実際の勾配:")
for i in range(len(gradients_zone1)):
    print(f"  Input {i}→{i+1}: {gradients_zone1[i]} K/step")

zone1_grad_mean = gradients_zone1.mean()
zone1_grad_std = gradients_zone1.std()
print(f"\n平均勾配: {zone1_grad_mean:.2f} K/step")
print(f"標準偏差: {zone1_grad_std:.2f}")

if zone1_grad_std < 0.5:
    print("✓ Zone 1は均等補間されています（標準偏差が小さい）")
else:
    print("⚠️ Zone 1に不均等な箇所があります")

# Zone 2 (24-239) 検証
print("\n" + "="*60)
print("【Zone 2: Midtone (24-239)】")
print("Input 24 → 239 を215ステップで線形補間（目標: 115.0 K/step）\n")

gradients_zone2 = np.diff(k_values[24:240])
print(f"勾配のサンプル（最初10個と最後10個）:")
print("  最初10個:")
for i in range(10):
    print(f"    Input {24+i}→{25+i}: {gradients_zone2[i]} K/step")

print("  最後10個:")
for i in range(len(gradients_zone2)-10, len(gradients_zone2)):
    inp = 24 + i
    print(f"    Input {inp}→{inp+1}: {gradients_zone2[i]} K/step")

zone2_grad_mean = gradients_zone2.mean()
zone2_grad_std = gradients_zone2.std()
print(f"\n平均勾配: {zone2_grad_mean:.2f} K/step（目標: 115.0）")
print(f"標準偏差: {zone2_grad_std:.2f}")

if zone2_grad_std < 0.5:
    print("✓ Zone 2は均等補間されています（標準偏差が小さい）")
else:
    print("⚠️ Zone 2に不均等な箇所があります")

# Transition (240-248) 検証
print("\n" + "="*60)
print("【Transition: Input 240 → 248】")
print(f"Input 240 (K={k_values[240]}) → 248 (K={k_values[248]}) を8ステップで線形補間\n")

gradients_transition = np.diff(k_values[240:249])
expected_transition_grad = (k_values[248] - k_values[240]) / 8

print(f"理論勾配: {expected_transition_grad:.1f} K/step")
print(f"実際の勾配:")
for i in range(len(gradients_transition)):
    inp = 240 + i
    print(f"  Input {inp}→{inp+1}: {gradients_transition[i]} K/step")

transition_grad_mean = gradients_transition.mean()
transition_grad_std = gradients_transition.std()
print(f"\n平均勾配: {transition_grad_mean:.2f} K/step")
print(f"標準偏差: {transition_grad_std:.2f}")

if transition_grad_std < 1.0:
    print("✓ Transitionは均等補間されています")
else:
    print("⚠️ Transitionに不均等な箇所があります")

# Zone 3 (248-255) 検証
print("\n" + "="*60)
print("【Zone 3: Highlight (248-255)】")
print(f"Input 248 (K={k_values[248]}) → 255 (K={k_values[255]}) を7ステップで線形補間\n")

gradients_zone3 = np.diff(k_values[248:256])
expected_zone3_grad = (k_values[255] - k_values[248]) / 7

print(f"理論勾配: {expected_zone3_grad:.1f} K/step")
print(f"実際の勾配:")
for i in range(len(gradients_zone3)):
    inp = 248 + i
    print(f"  Input {inp}→{inp+1}: {gradients_zone3[i]} K/step")

zone3_grad_mean = gradients_zone3.mean()
zone3_grad_std = gradients_zone3.std()
print(f"\n平均勾配: {zone3_grad_mean:.2f} K/step")
print(f"標準偏差: {zone3_grad_std:.2f}")

if zone3_grad_std < 1.0:
    print("✓ Zone 3は均等補間されています")
else:
    print("⚠️ Zone 3に不均等な箇所があります")

# 総合判定
print("\n" + "="*60)
print("【総合判定】\n")

all_stds = [zone1_grad_std, zone2_grad_std, transition_grad_std, zone3_grad_std]
all_uniform = all(std < 1.0 for std in all_stds)

if all_uniform:
    print("✅ v14のすべての区間で均等補間（線形補間）が正しく行われています")
else:
    print("⚠️ 一部の区間で不均等な箇所があります")

print(f"\n各区間の標準偏差:")
print(f"  Zone 1 (0-24):      {zone1_grad_std:.3f}")
print(f"  Zone 2 (24-239):    {zone2_grad_std:.3f}")
print(f"  Transition (240-248): {transition_grad_std:.3f}")
print(f"  Zone 3 (248-255):   {zone3_grad_std:.3f}")

# 主要K-values表示
print("\n" + "="*60)
print("【主要K-values】\n")
key_points = [0, 24, 128, 192, 239, 240, 248, 255]
for inp in key_points:
    print(f"K[{inp:3}] = {k_values[inp]:5}")
