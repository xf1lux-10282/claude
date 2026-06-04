#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v14 QTRカーブ生成
正式版: v12からの控えめなミッドトーン最適化
- ミッドトーン: ほんの少し明るく（-1.5~-1.7%）
- Input 248: 少し濃く（+0.34%）
- 紙白到達保証: K_max = 33800
"""
import numpy as np

# Zone 1: Shadow (0-24) - v12と同じ
zone1_k_values = []
for i in range(0, 25):
    k = round(4148 * i / 24)
    zone1_k_values.append(k)

# Zone 2: Midtone (24-239) - v12より少し緩やか（115.0 K/step）
zone2_k_start = 4148
target_zone2_grad = 115.0  # v12: 117.4 (-2.0%)
zone2_steps = 239 - 24  # 215 steps
zone2_k_end = round(zone2_k_start + target_zone2_grad * zone2_steps)

zone2_k_values = []
for i in range(1, zone2_steps + 1):
    k = round(zone2_k_start + target_zone2_grad * i)
    zone2_k_values.append(k)

# Input 240: 指定値
k_240 = 29400  # v12: 29500 (-0.34%)

# Input 241-247: 240→248を線形補間
k_248 = 31900  # v12: 31793 (+0.34%, 少し濃く)

transition_k_values = []
steps_240_to_248 = 8
for i in range(1, steps_240_to_248):  # 241-247
    k = round(k_240 + (k_248 - k_240) * i / steps_240_to_248)
    transition_k_values.append(k)

# Zone 3: Highlight (248-255)
zone3_k_start = k_248
zone3_k_end = 33800  # v12と同じ（紙白保証）
zone3_steps = 7

zone3_k_values = []
for i in range(1, zone3_steps + 1):
    k = round(zone3_k_start + (zone3_k_end - zone3_k_start) * i / zone3_steps)
    zone3_k_values.append(k)

# 全K-values結合
k_values = zone1_k_values + zone2_k_values + [k_240] + transition_k_values + [k_248] + zone3_k_values

# 検証
print("=== v14 K-values検証 ===")
print(f"Total: {len(k_values)} values")
print(f"K[0]: {k_values[0]}")
print(f"K[24]: {k_values[24]}")
print(f"K[128]: {k_values[128]}")
print(f"K[192]: {k_values[192]}")
print(f"K[240]: {k_values[240]} (指定値{k_240})")
print(f"K[248]: {k_values[248]} (指定値{k_248})")
print(f"K[255]: {k_values[255]}")

assert len(k_values) == 256, f"K-values count error: {len(k_values)}"
assert k_values[0] == 0
assert k_values[240] == k_240
assert k_values[248] == k_248
assert k_values[255] == 33800

# 勾配分析
gradients = np.diff(k_values)
zone1_grad = gradients[0:24].mean()
zone2_grad = gradients[24:240].mean()
transition_grad = gradients[240:248].mean()
zone3_grad = gradients[248:255].mean()

gradient_ratio = max(transition_grad, zone3_grad) / zone2_grad

print(f"\n=== 勾配分析 ===")
print(f"Zone 1 (0-24):     {zone1_grad:.1f} K/step")
print(f"Zone 2 (24-240):   {zone2_grad:.1f} K/step")
print(f"Transition (240-248): {transition_grad:.1f} K/step")
print(f"Zone 3 (248-255):  {zone3_grad:.1f} K/step")
print(f"勾配比 (max/Zone2): {gradient_ratio:.2f}")

if gradient_ratio <= 2.5:
    print(f"✓ 勾配比{gradient_ratio:.2f}は理想範囲(2.0-2.5)内です")
elif gradient_ratio <= 2.7:
    print(f"⚠️  勾配比{gradient_ratio:.2f}が理想範囲をわずかに超えていますが許容範囲です")
else:
    print(f"❌ 勾配比{gradient_ratio:.2f}が許容範囲を超えています")

# v12との比較
v12_k_values = {
    0: 0, 8: 1383, 16: 2765, 24: 4148, 32: 5087, 40: 6026, 48: 6965, 56: 7904,
    64: 8843, 72: 9782, 80: 10721, 88: 11660, 96: 12599, 104: 13538, 112: 14477, 120: 15416,
    128: 16355, 136: 17293, 144: 18232, 152: 19171, 160: 20110, 168: 21049, 176: 21988, 184: 22927,
    192: 23866, 200: 24805, 208: 25744, 216: 26683, 224: 27622, 232: 28561, 240: 29500, 248: 31793, 255: 33800
}

print(f"\n=== v12との比較 ===")
print(f"Input | v12    | v14       | 差分    | 差分%")
print(f"------|--------|-----------|---------|-------")

for inp in [0, 24, 32, 64, 104, 128, 176, 192, 232, 240, 248, 255]:
    v12_k = v12_k_values[inp]
    v14_k = k_values[inp]
    diff = v14_k - v12_k
    diff_percent = (diff / v12_k * 100) if v12_k > 0 else 0.0
    print(f"{inp:5} | {v12_k:6} | {v14_k:9} | {diff:+7} | {diff_percent:+6.2f}%")

# 主要ポイント詳細
print(f"\n=== 主要ポイント ===")
print(f"K_max: {k_values[255]} (v12と同じ, 紙白到達保証)")
print(f"Input 128: {k_values[128]} (v12: {v12_k_values[128]}, {k_values[128] - v12_k_values[128]:+d}, ミッドトーン最適化)")
print(f"Input 192: {k_values[192]} (v12: {v12_k_values[192]}, {k_values[192] - v12_k_values[192]:+d}, ミッドトーン最適化)")
print(f"Input 248: {k_values[248]} (v12: {v12_k_values[248]}, {k_values[248] - v12_k_values[248]:+d}, ハイライト濃度向上)")
print(f"勾配比: {gradient_ratio:.2f} (許容範囲内)")
print(f"露光時間: 6.5min (v12と同じ推奨)")

# .quadファイル生成
quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v14
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Base curve: v12 (v14 - Subtle Midtone Optimization)
# - Subtle midtone brightening with enhanced highlight density
# - Shadow (0-24): 172.8 K/step (same as v12)
# - Midtone (24-240): 116.9 K/step (-2.0% vs v12 117.4)
# - Input 240: 29400 (-0.34% vs v12)
# - Input 248: 31900 (+0.34% vs v12, denser highlights)
# - Highlight (248-255): 271.4 K/step, smooth transition to paper white
# - K_max: 33800 (same as v12, paper white guaranteed)
# - Gradient ratio: 2.67 (acceptable range)
# - Target: Subtle midtone brightness + slightly denser highlight region
# - Exposure: 6.5min (same as v12)
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
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v14.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"\n✓ v14カーブ生成完了: {output_path}")

print(f"\n=== v14 設計コンセプト ===")
print(f"v12からの改良:")
print(f"  ✓ ミッドトーン(64-192): ほんの少し明るく（-1.5~-1.7%）")
print(f"  ✓ Input 240: わずかに明るく（-0.34%）")
print(f"  ✓ Input 248: 少し濃く（+0.34%）")
print(f"  ✓ 紙白到達保証: K_max=33800（v12と同じ）")
print(f"  ✓ 勾配比: 2.67（許容範囲内）")
print(f"\n推奨用途:")
print(f"  - v12で満足しているが、ミッドトーンをほんの少し明るくしたい場合")
print(f"  - ハイライト域（240-248）に少し濃度を持たせたい場合")
print(f"  - 紙白到達を確実に保証しつつ、控えめな最適化を行いたい場合")
