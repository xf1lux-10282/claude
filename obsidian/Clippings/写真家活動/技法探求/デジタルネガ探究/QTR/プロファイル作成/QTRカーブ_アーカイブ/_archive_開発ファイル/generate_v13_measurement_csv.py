#!/usr/bin/env python3
"""
v13-NA および v13-MT の測定用CSVファイル生成
8ステップ間隔でK-valuesを抽出
"""
import csv

# v13-NA K-values生成（generate_v13_NA.pyと同じロジック）
def generate_v13_na():
    ZONE_CONFIGS = {
        'zone1': {'start': 0, 'end': 24, 'k_start': 0, 'k_end': 4148},
        'zone2': {'start': 24, 'end': 240, 'k_start': 4148, 'k_end': 29500},
        'zone3': {'start': 240, 'end': 255, 'k_start': 29500, 'k_end': 33051}
    }

    k_values = []

    # Zone 1
    zone1 = ZONE_CONFIGS['zone1']
    for i in range(zone1['start'], zone1['end'] + 1):
        k = round(zone1['k_end'] * i / zone1['end'])
        k_values.append(k)

    # Zone 2
    zone2 = ZONE_CONFIGS['zone2']
    steps = zone2['end'] - zone2['start']
    for i in range(1, steps + 1):
        k = round(zone2['k_start'] + (zone2['k_end'] - zone2['k_start']) * i / steps)
        k_values.append(k)

    # Zone 3
    zone3 = ZONE_CONFIGS['zone3']
    steps = zone3['end'] - zone3['start']
    for i in range(1, steps + 1):
        k = round(zone3['k_start'] + (zone3['k_end'] - zone3['k_start']) * i / steps)
        k_values.append(k)

    return k_values

# v13-MT K-values生成（generate_v13_MT.pyと同じロジック）
def generate_v13_mt():
    zone2_k_start = 4148
    target_zone2_grad = 110.0
    zone2_steps = 216
    zone2_k_end = int(zone2_k_start + target_zone2_grad * zone2_steps)

    target_gradient_ratio = 2.7
    zone3_grad = target_zone2_grad * target_gradient_ratio
    zone3_steps = 15
    zone3_k_end = int(zone2_k_end + zone3_grad * zone3_steps)

    ZONE_CONFIGS = {
        'zone1': {'start': 0, 'end': 24, 'k_start': 0, 'k_end': 4148},
        'zone2': {'start': 24, 'end': 240, 'k_start': 4148, 'k_end': zone2_k_end},
        'zone3': {'start': 240, 'end': 255, 'k_start': zone2_k_end, 'k_end': zone3_k_end}
    }

    k_values = []

    # Zone 1
    zone1 = ZONE_CONFIGS['zone1']
    for i in range(zone1['start'], zone1['end'] + 1):
        k = round(zone1['k_end'] * i / zone1['end'])
        k_values.append(k)

    # Zone 2
    zone2 = ZONE_CONFIGS['zone2']
    steps = zone2['end'] - zone2['start']
    for i in range(1, steps + 1):
        k = round(zone2['k_start'] + (zone2['k_end'] - zone2['k_start']) * i / steps)
        k_values.append(k)

    # Zone 3
    zone3 = ZONE_CONFIGS['zone3']
    steps = zone3['end'] - zone3['start']
    for i in range(1, steps + 1):
        k = round(zone3['k_start'] + (zone3['k_end'] - zone3['k_start']) * i / steps)
        k_values.append(k)

    return k_values

# K-values生成
v13_na_k_values = generate_v13_na()
v13_mt_k_values = generate_v13_mt()

# 検証
print("=== K-values検証 ===")
print(f"v13-NA: {len(v13_na_k_values)} values, K[0]={v13_na_k_values[0]}, K[255]={v13_na_k_values[255]}")
print(f"v13-MT: {len(v13_mt_k_values)} values, K[0]={v13_mt_k_values[0]}, K[255]={v13_mt_k_values[255]}")

# 8ステップ間隔でサンプリング
sample_inputs = list(range(0, 256, 8))

# v13-NA CSV生成
output_na = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/測定記録/v13_NA_measurement_data.csv'
with open(output_na, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['curve_name', 'input_value', 'k_value', 'negative_density_transmission', 'print_density_reflection_7min'])

    for inp in sample_inputs:
        k = v13_na_k_values[inp]
        # ネガ透過濃度は概算（K-value → 濃度変換）
        neg_density = round(0.07 + (k / 33051) * 0.96, 2) if k > 0 else 0.07
        writer.writerow(['v13-NA', inp, k, neg_density, ''])

print(f"✓ v13-NA測定用CSV生成: {output_na}")

# v13-MT CSV生成
output_mt = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/測定記録/v13_MT_measurement_data.csv'
with open(output_mt, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['curve_name', 'input_value', 'k_value', 'negative_density_transmission', 'print_density_reflection_6_75min', 'print_density_reflection_7min'])

    for inp in sample_inputs:
        k = v13_mt_k_values[inp]
        # ネガ透過濃度は概算
        neg_density = round(0.07 + (k / 32363) * 0.93, 2) if k > 0 else 0.07
        writer.writerow(['v13-MT', inp, k, neg_density, '', ''])

print(f"✓ v13-MT測定用CSV生成: {output_mt}")

# 比較用統合CSV生成
output_comparison = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/測定記録/v13_comparison_data.csv'
with open(output_comparison, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['input_value', 'v12_k', 'v13_NA_k', 'v13_MT_k', 'v12_v13_NA_diff', 'v12_v13_MT_diff'])

    # v12のK-values（既知）
    v12_k_values = {
        0: 0, 8: 1383, 16: 2765, 24: 4148, 32: 5087, 40: 6026, 48: 6965, 56: 7904,
        64: 8843, 72: 9782, 80: 10721, 88: 11660, 96: 12599, 104: 13538, 112: 14477, 120: 15416,
        128: 16355, 136: 17293, 144: 18232, 152: 19171, 160: 20110, 168: 21049, 176: 21988, 184: 22927,
        192: 23866, 200: 24805, 208: 25744, 216: 26683, 224: 27622, 232: 28561, 240: 29500, 248: 31793, 255: 33800
    }

    for inp in sample_inputs:
        v12_k = v12_k_values.get(inp, 0)
        v13_na_k = v13_na_k_values[inp]
        v13_mt_k = v13_mt_k_values[inp]
        diff_na = v13_na_k - v12_k
        diff_mt = v13_mt_k - v12_k
        writer.writerow([inp, v12_k, v13_na_k, v13_mt_k, diff_na, diff_mt])

print(f"✓ v13比較用CSV生成: {output_comparison}")

# 主要ポイントの表示
print("\n=== 主要K-values比較（8ステップ間隔） ===")
print("Input | v12    | v13-NA | v13-MT | NA差分 | MT差分")
print("------|--------|--------|--------|--------|--------")
for inp in [0, 8, 24, 32, 64, 128, 176, 240, 248, 255]:
    v12_k = v12_k_values.get(inp, 0)
    v13_na_k = v13_na_k_values[inp]
    v13_mt_k = v13_mt_k_values[inp]
    diff_na = v13_na_k - v12_k
    diff_mt = v13_mt_k - v12_k
    print(f"{inp:5} | {v12_k:6} | {v13_na_k:6} | {v13_mt_k:6} | {diff_na:+6} | {diff_mt:+6}")
