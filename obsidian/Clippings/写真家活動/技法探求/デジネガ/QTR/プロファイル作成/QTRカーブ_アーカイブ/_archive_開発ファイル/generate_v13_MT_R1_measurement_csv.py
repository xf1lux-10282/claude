#!/usr/bin/env python3
"""
v13-MT-R1 測定用CSVファイル生成
Input 232=28000 指定版の測定データ
"""
import csv

# v13-MT-R1 K-values生成（generate_v13_MT_R1.pyと同じロジック）
def generate_v13_mt_r1():
    # Zone 1: Shadow (0-24) - v12と同じ
    zone1_k_values = []
    for i in range(0, 25):
        k = round(4148 * i / 24)
        zone1_k_values.append(k)

    # Zone 2: Midtone (24-231) - 110.0 K/step
    zone2_k_values = []
    zone2_k_start = 4148
    target_zone2_grad = 110.0
    for i in range(1, 208):  # 24から231まで（207ステップ）
        k = round(zone2_k_start + target_zone2_grad * i)
        zone2_k_values.append(k)

    # Input 232: 指定値28000
    k_232 = 28000

    # Input 233-239: 232→240を線形補間
    k_240 = 29500
    steps_232_to_240 = 8
    transition_k_values = []
    for i in range(1, steps_232_to_240):  # 233-239
        k = round(k_232 + (k_240 - k_232) * i / steps_232_to_240)
        transition_k_values.append(k)

    # Zone 3: Highlight (240-255) - v12と同じ
    zone3_k_values = []
    zone3_k_start = 29500
    zone3_k_end = 33800
    zone3_steps = 15
    for i in range(0, zone3_steps + 1):  # 240-255（16個）
        k = round(zone3_k_start + (zone3_k_end - zone3_k_start) * i / zone3_steps)
        zone3_k_values.append(k)

    # 全K-valuesを結合
    k_values = zone1_k_values + zone2_k_values + [k_232] + transition_k_values + zone3_k_values

    return k_values

# K-values生成
v13_mt_r1_k_values = generate_v13_mt_r1()

# 検証
print("=== v13-MT-R1 K-values検証 ===")
print(f"Total: {len(v13_mt_r1_k_values)} values")
print(f"K[0]: {v13_mt_r1_k_values[0]}")
print(f"K[24]: {v13_mt_r1_k_values[24]}")
print(f"K[128]: {v13_mt_r1_k_values[128]}")
print(f"K[232]: {v13_mt_r1_k_values[232]} (指定値28000)")
print(f"K[240]: {v13_mt_r1_k_values[240]} (v12と同じ29500)")
print(f"K[255]: {v13_mt_r1_k_values[255]} (v12と同じ33800)")

assert len(v13_mt_r1_k_values) == 256, f"K-values count error: {len(v13_mt_r1_k_values)}"
assert v13_mt_r1_k_values[232] == 28000, f"K[232] error: {v13_mt_r1_k_values[232]}"
assert v13_mt_r1_k_values[240] == 29500, f"K[240] error: {v13_mt_r1_k_values[240]}"
assert v13_mt_r1_k_values[255] == 33800, f"K[255] error: {v13_mt_r1_k_values[255]}"

# 8ステップ間隔でサンプリング
sample_inputs = list(range(0, 256, 8))

# v13-MT-R1 測定用CSV生成
output_mt_r1 = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/測定記録/v13_MT_R1_measurement_data.csv'
with open(output_mt_r1, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['curve_name', 'input_value', 'k_value', 'negative_density_transmission', 'print_density_reflection_6_5min'])

    for inp in sample_inputs:
        k = v13_mt_r1_k_values[inp]
        # ネガ透過濃度は概算（K-value → 濃度変換）
        # K_max=33800を基準に、ネガのmax densityを0.96Dと仮定
        neg_density = round(0.07 + (k / 33800) * 0.96, 2) if k > 0 else 0.07
        writer.writerow(['v13-MT-R1', inp, k, neg_density, ''])

print(f"\n✓ v13-MT-R1測定用CSV生成: {output_mt_r1}")

# v12との比較CSV生成
output_comparison = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/測定記録/v13_MT_R1_vs_v12_comparison.csv'

# v12のK-values（既知）
v12_k_values_dict = {
    0: 0, 8: 1383, 16: 2765, 24: 4148, 32: 5087, 40: 6026, 48: 6965, 56: 7904,
    64: 8843, 72: 9782, 80: 10721, 88: 11660, 96: 12599, 104: 13538, 112: 14477, 120: 15416,
    128: 16355, 136: 17293, 144: 18232, 152: 19171, 160: 20110, 168: 21049, 176: 21988, 184: 22927,
    192: 23866, 200: 24805, 208: 25744, 216: 26683, 224: 27622, 232: 28561, 240: 29500, 248: 31793
}

with open(output_comparison, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['input_value', 'v12_k', 'v13_MT_R1_k', 'k_diff', 'k_diff_percent'])

    for inp in sample_inputs:
        v12_k = v12_k_values_dict.get(inp, 0)
        v13_mt_r1_k = v13_mt_r1_k_values[inp]
        diff = v13_mt_r1_k - v12_k
        diff_percent = round((diff / v12_k * 100), 2) if v12_k > 0 else 0.0
        writer.writerow([inp, v12_k, v13_mt_r1_k, diff, diff_percent])

print(f"✓ v13-MT-R1 vs v12 比較CSV生成: {output_comparison}")

# 主要ポイントの表示
print("\n=== 主要K-values比較（8ステップ間隔） ===")
print("Input | v12    | v13-MT-R1 | 差分    | 差分%")
print("------|--------|-----------|---------|-------")
for inp in [0, 8, 24, 32, 64, 104, 128, 176, 192, 232, 240, 248]:
    v12_k = v12_k_values_dict.get(inp, 0)
    v13_mt_r1_k = v13_mt_r1_k_values[inp]
    diff = v13_mt_r1_k - v12_k
    diff_percent = round((diff / v12_k * 100), 1) if v12_k > 0 else 0.0
    print(f"{inp:5} | {v12_k:6} | {v13_mt_r1_k:9} | {diff:+7} | {diff_percent:+6.1f}%")
