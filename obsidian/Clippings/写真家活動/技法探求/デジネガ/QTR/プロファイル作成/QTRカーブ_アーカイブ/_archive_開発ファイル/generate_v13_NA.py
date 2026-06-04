#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v13-NA QTRカーブ生成
v7-NA準拠版: v7-NAのK_maxで3ゾーン設計の恩恵を得る保守的アプローチ
"""
import numpy as np

# 3ゾーン設計（v12と同じミッドトーン、v7-NAと同じK_max）
ZONE_CONFIGS = {
    'zone1': {'start': 0, 'end': 24, 'k_start': 0, 'k_end': 4148},
    'zone2': {'start': 24, 'end': 240, 'k_start': 4148, 'k_end': 29500},
    'zone3': {'start': 240, 'end': 255, 'k_start': 29500, 'k_end': 33051}
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
assert k_values[255] == 33051, f"K[255]: {k_values[255]} (expected 33051)"

# 勾配計算
gradients = np.diff(k_values)
zone1_grad = gradients[0:24].mean()
zone2_grad = gradients[24:240].mean()
zone3_grad = gradients[240:255].mean()
gradient_ratio = zone3_grad / zone2_grad

print(f"=== v13-NA K-values検証 ===")
print(f"Zone 1 (0-24):   {zone1_grad:.1f} K/step")
print(f"Zone 2 (24-240): {zone2_grad:.1f} K/step")
print(f"Zone 3 (240-255): {zone3_grad:.1f} K/step")
print(f"勾配比: {gradient_ratio:.2f}")
print(f"K_max: {k_values[255]}")

# v12との比較
v12_k_max = 33800
v12_zone3_grad = 286.7
print(f"\n=== v12との比較 ===")
print(f"K_max: {k_values[255]} (v12: {v12_k_max}, {((k_values[255]/v12_k_max-1)*100):.1f}%)")
print(f"Zone 3勾配: {zone3_grad:.1f} (v12: {v12_zone3_grad}, {((zone3_grad/v12_zone3_grad-1)*100):.1f}%)")
print(f"勾配比: {gradient_ratio:.2f} (v12: 2.44, {((gradient_ratio/2.44-1)*100):.1f}%)")

# .quadファイル生成
quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v13-NA
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Base curve: v12 (v13-NA variant)
# - Conservative approach: v7-NA K_max with 3-zone design
# - Shadow (0-24): 172.8 K/step (same as v12)
# - Midtone (24-240): 117.4 K/step (same as v12)
# - Highlight (240-255): 236.7 K/step (lower than v12, gentler)
# - K_max: 33051 (v7-NA proven baseline, -2.2% vs v12)
# - Gradient ratio: 2.02 (ideal range, low banding risk)
# - Target: v7-NA midtone brightness with 3-zone design benefits
# - Exposure: 7min (same as v7-NA)
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
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v13-NA.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"\n✓ v13-NAカーブ生成完了: {output_path}")
