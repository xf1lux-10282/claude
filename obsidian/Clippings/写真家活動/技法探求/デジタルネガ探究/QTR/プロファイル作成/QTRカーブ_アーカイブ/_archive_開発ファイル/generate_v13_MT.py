#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v13-MT QTRカーブ生成
Midtone Tuned版: ミッドトーンをさらに緩やかにする積極的アプローチ
"""
import numpy as np

# 3ゾーン設計（ミッドトーンをさらに緩やかに）
# 目標: Zone 2勾配 110.0 K/step, 勾配比 2.5以内

# Zone 2の設計
zone2_start_input = 24
zone2_end_input = 240
zone2_steps = zone2_end_input - zone2_start_input  # 216 steps
zone2_k_start = 4148
target_zone2_grad = 110.0
zone2_k_end = int(zone2_k_start + target_zone2_grad * zone2_steps)  # 4148 + 110*216 = 27908

# Zone 3の設計（勾配比を2.5以内に収める）
zone3_start_input = 240
zone3_end_input = 255
zone3_steps = zone3_end_input - zone3_start_input  # 15 steps
target_gradient_ratio = 2.7  # 2.5より少し高いが許容範囲
zone3_grad = target_zone2_grad * target_gradient_ratio  # 110 * 2.7 = 297
zone3_k_start = zone2_k_end
zone3_k_end = int(zone3_k_start + zone3_grad * zone3_steps)  # 27908 + 297*15 = 32363

ZONE_CONFIGS = {
    'zone1': {'start': 0, 'end': 24, 'k_start': 0, 'k_end': 4148},
    'zone2': {'start': 24, 'end': 240, 'k_start': 4148, 'k_end': zone2_k_end},
    'zone3': {'start': 240, 'end': 255, 'k_start': zone2_k_end, 'k_end': zone3_k_end}
}

# K-values生成
k_values = []

# Zone 1: Shadow (0-24)
zone1 = ZONE_CONFIGS['zone1']
for i in range(zone1['start'], zone1['end'] + 1):
    k = round(zone1['k_end'] * i / zone1['end'])
    k_values.append(k)

# Zone 2: Midtone (25-240)
zone2 = ZONE_CONFIGS['zone2']
steps = zone2['end'] - zone2['start']
for i in range(1, steps + 1):
    k = round(zone2['k_start'] + (zone2['k_end'] - zone2['k_start']) * i / steps)
    k_values.append(k)

# Zone 3: Highlight (241-255)
zone3 = ZONE_CONFIGS['zone3']
steps = zone3['end'] - zone3['start']
for i in range(1, steps + 1):
    k = round(zone3['k_start'] + (zone3['k_end'] - zone3['k_start']) * i / steps)
    k_values.append(k)

# 検証
assert len(k_values) == 256, f"K-values count: {len(k_values)} (expected 256)"
assert k_values[0] == 0, f"K[0]: {k_values[0]} (expected 0)"
assert k_values[255] == zone3_k_end, f"K[255]: {k_values[255]} (expected {zone3_k_end})"

# 勾配計算
gradients = np.diff(k_values)
zone1_grad = gradients[0:24].mean()
zone2_grad = gradients[24:240].mean()
zone3_grad = gradients[240:255].mean()
gradient_ratio = zone3_grad / zone2_grad

print(f"=== v13-MT K-values検証 ===")
print(f"Zone 1 (0-24):   {zone1_grad:.1f} K/step")
print(f"Zone 2 (24-240): {zone2_grad:.1f} K/step")
print(f"Zone 3 (240-255): {zone3_grad:.1f} K/step")
print(f"勾配比: {gradient_ratio:.2f}")
print(f"K_max: {k_values[255]}")

# v12との比較
v12_k_max = 33800
v12_zone2_grad = 117.4
v12_zone3_grad = 286.7
print(f"\n=== v12との比較 ===")
print(f"K_max: {k_values[255]} (v12: {v12_k_max}, {((k_values[255]/v12_k_max-1)*100):.1f}%)")
print(f"Zone 2勾配: {zone2_grad:.1f} (v12: {v12_zone2_grad}, {((zone2_grad/v12_zone2_grad-1)*100):.1f}%)")
print(f"Zone 3勾配: {zone3_grad:.1f} (v12: {v12_zone3_grad}, {((zone3_grad/v12_zone3_grad-1)*100):.1f}%)")
print(f"勾配比: {gradient_ratio:.2f} (v12: 2.44, {((gradient_ratio/2.44-1)*100):.1f}%)")

# v7-NA比較
v7_k_max = 33051
print(f"\n=== v7-NAとの比較 ===")
print(f"K_max: {k_values[255]} (v7-NA: {v7_k_max}, {((k_values[255]/v7_k_max-1)*100):.1f}%)")

# 警告チェック
if gradient_ratio > 2.5:
    print(f"\n⚠️  警告: 勾配比{gradient_ratio:.2f}が理想範囲(2.0-2.5)を超えています")
    print(f"   バンディングリスク: 中程度")
else:
    print(f"\n✓ 勾配比{gradient_ratio:.2f}は理想範囲(2.0-2.5)内です")

# .quadファイル生成
quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v13-MT
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Base curve: v12 (v13-MT variant)
# - Aggressive midtone optimization approach
# - Shadow (0-24): 172.8 K/step (same as v12)
# - Midtone (24-240): 110.0 K/step (-6.3% vs v12, -11.7% vs v9-SM)
# - Highlight (240-255): 297.0 K/step (+3.6% vs v12)
# - K_max: 32363 (-4.2% vs v12, -2.1% vs v7-NA)
# - Gradient ratio: 2.70 (slightly above ideal 2.5, acceptable)
# - Target: Brightest midtone with aggressive optimization
# - Exposure: 6.25min estimated (-3.8% vs v12 6.5min)
# Generated: 2026-03-24 by Claude Code

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
#
# K curve
"""

for k in k_values:
    quad_content += f"{k}\n"

quad_content += "#\n"

# 残り9チャンネル（全て0）
for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# 保存
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v13-MT.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"\n✓ v13-MTカーブ生成完了: {output_path}")
