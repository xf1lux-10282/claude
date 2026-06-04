#!/usr/bin/env python3
"""
v14 測定用CSVファイル生成
8ステップ間隔でK-valuesを抽出
"""
import csv
import numpy as np

# v14 K-values生成（generate_v14.pyと同じロジック）
def generate_v14():
    # Zone 1: Shadow (0-24)
    zone1_k_values = []
    for i in range(0, 25):
        k = round(4148 * i / 24)
        zone1_k_values.append(k)

    # Zone 2: Midtone (24-239)
    zone2_k_start = 4148
    target_zone2_grad = 115.0
    zone2_steps = 239 - 24
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
    for i in range(1, steps_240_to_248):
        k = round(k_240 + (k_248 - k_240) * i / steps_240_to_248)
        transition_k_values.append(k)

    # Zone 3: Highlight (248-255)
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
v14_k_values = generate_v14()

# 検証
print("=== v14 K-values検証 ===")
print(f"Total: {len(v14_k_values)} values")
print(f"K[0]: {v14_k_values[0]}")
print(f"K[128]: {v14_k_values[128]}")
print(f"K[240]: {v14_k_values[240]}")
print(f"K[248]: {v14_k_values[248]}")
print(f"K[255]: {v14_k_values[255]}")

assert len(v14_k_values) == 256
assert v14_k_values[0] == 0
assert v14_k_values[255] == 33800

# 8ステップ間隔でサンプリング
sample_inputs = list(range(0, 256, 8))

# v14 測定用CSV生成
output_v14 = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/測定記録/v14_measurement_data.csv'
with open(output_v14, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['curve_name', 'input_value', 'k_value', 'negative_density_transmission', 'print_density_reflection_6_5min'])

    for inp in sample_inputs:
        k = v14_k_values[inp]
        # ネガ透過濃度は概算（K-value → 濃度変換）
        neg_density = round(0.07 + (k / 33800) * 0.96, 2) if k > 0 else 0.07
        writer.writerow(['v14', inp, k, neg_density, ''])

print(f"\n✓ v14測定用CSV生成: {output_v14}")

# v12との比較CSV生成
output_comparison = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/測定記録/v14_vs_v12_comparison.csv'

# v12のK-values（既知）
v12_k_values_dict = {
    0: 0, 8: 1383, 16: 2765, 24: 4148, 32: 5087, 40: 6026, 48: 6965, 56: 7904,
    64: 8843, 72: 9782, 80: 10721, 88: 11660, 96: 12599, 104: 13538, 112: 14477, 120: 15416,
    128: 16355, 136: 17293, 144: 18232, 152: 19171, 160: 20110, 168: 21049, 176: 21988, 184: 22927,
    192: 23866, 200: 24805, 208: 25744, 216: 26683, 224: 27622, 232: 28561, 240: 29500, 248: 31793
}

with open(output_comparison, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['input_value', 'v12_k', 'v14_k', 'k_diff', 'k_diff_percent'])

    for inp in sample_inputs:
        v12_k = v12_k_values_dict.get(inp, 0)
        v14_k = v14_k_values[inp]
        diff = v14_k - v12_k
        diff_percent = round((diff / v12_k * 100), 2) if v12_k > 0 else 0.0
        writer.writerow([inp, v12_k, v14_k, diff, diff_percent])

print(f"✓ v14 vs v12 比較CSV生成: {output_comparison}")

# 主要ポイントの表示
print(f"\n=== 主要K-values比較（8ステップ間隔） ===")
print(f"Input | v12    | v14       | 差分    | 差分%")
print(f"------|--------|-----------|---------|-------")

for inp in [0, 8, 24, 32, 64, 104, 128, 176, 192, 232, 240, 248]:
    v12_k = v12_k_values_dict.get(inp, 0)
    v14_k = v14_k_values[inp]
    diff = v14_k - v12_k
    diff_percent = round((diff / v12_k * 100), 1) if v12_k > 0 else 0.0
    print(f"{inp:5} | {v12_k:6} | {v14_k:9} | {diff:+7} | {diff_percent:+6.1f}%")

print(f"\n=== v14 特性まとめ ===")
print(f"ミッドトーン最適化: -1.5% ~ -1.7% (Input 64-192)")
print(f"Input 240: -0.34% (わずかに明るく)")
print(f"Input 248: +0.34% (少し濃く)")
print(f"K_max: 33800 (紙白保証)")
print(f"推奨露光時間: 6.5min (v12と同じ)")
