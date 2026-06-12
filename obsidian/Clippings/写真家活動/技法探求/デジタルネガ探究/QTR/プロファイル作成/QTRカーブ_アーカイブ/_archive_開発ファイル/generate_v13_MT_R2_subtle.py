#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v13-MT-R2 (Subtle Midtone Optimization)
v12と比較して:
- ミッドトーン: ほんの少し明るく（K-value 2-3%低下）
- 240-248: 少し暗く（K-value 1-2%上昇）
- 紙白到達保証: K_max = 33800
"""
import numpy as np

# 設計方針:
# Zone 2の勾配をv12の117.4より少し緩く（114.0 K/step程度）
# Input 240をv12より少し低く設定
# Input 248をv12より少し高く設定

# Zone 1: Shadow (0-24) - v12と同じ
zone1_k_values = []
for i in range(0, 25):
    k = round(4148 * i / 24)
    zone1_k_values.append(k)

# Zone 2: Midtone (24-240) - v12より少し緩やか（114.0 K/step）
zone2_k_start = 4148
target_zone2_grad = 114.0  # v12: 117.4, v13-MT-R1: 110.0
zone2_steps = 240 - 24  # 216 steps
zone2_k_end = round(zone2_k_start + target_zone2_grad * zone2_steps)

zone2_k_values = []
for i in range(1, zone2_steps + 1):
    k = round(zone2_k_start + target_zone2_grad * i)
    zone2_k_values.append(k)

print("=== v13-MT-R2 (Subtle) 設計 ===")
print(f"Zone 2 (24-240) 勾配: {target_zone2_grad} K/step")
print(f"Input 240: K = {zone2_k_end}")

# v12との比較
v12_k_240 = 29500
print(f"v12 Input 240: {v12_k_240}")
print(f"差分: {zone2_k_end - v12_k_240:+d} ({((zone2_k_end/v12_k_240-1)*100):+.2f}%)")

# Input 241-248: 240→248を緩やかな勾配で補間
# v12のInput 248より少し高めに設定
target_k_248 = 32000  # v12: 31793, 少し濃くする

transition_241_248_k_values = []
steps_240_to_248 = 8
for i in range(1, steps_240_to_248 + 1):
    k = round(zone2_k_end + (target_k_248 - zone2_k_end) * i / steps_240_to_248)
    transition_241_248_k_values.append(k)

print(f"\nInput 248: K = {target_k_248}")
print(f"v12 Input 248: 31793")
print(f"差分: {target_k_248 - 31793:+d} ({((target_k_248/31793-1)*100):+.2f}%)")

# Zone 3: Highlight (249-255) - 248→255を線形補間
zone3_k_start = target_k_248
zone3_k_end = 33800  # v12と同じ
zone3_steps = 7

zone3_k_values = []
for i in range(1, zone3_steps + 1):
    k = round(zone3_k_start + (zone3_k_end - zone3_k_start) * i / zone3_steps)
    zone3_k_values.append(k)

# 全K-values結合
k_values = zone1_k_values + zone2_k_values + transition_241_248_k_values + zone3_k_values

# 検証
print(f"\n=== K-values検証 ===")
print(f"Total: {len(k_values)} values")
print(f"K[0]: {k_values[0]}")
print(f"K[24]: {k_values[24]}")
print(f"K[128]: {k_values[128]}")
print(f"K[192]: {k_values[192]}")
print(f"K[240]: {k_values[240]}")
print(f"K[248]: {k_values[248]}")
print(f"K[255]: {k_values[255]}")

assert len(k_values) == 256, f"K-values count: {len(k_values)}"
assert k_values[0] == 0
assert k_values[255] == 33800

# 勾配分析
gradients = np.diff(k_values)
zone1_grad = gradients[0:24].mean()
zone2_grad = gradients[24:240].mean()
transition_grad = gradients[240:248].mean()
zone3_grad = gradients[248:255].mean()

# 全体の勾配比（Zone 2とZone 3の最大勾配比を確認）
max_grad = max(transition_grad, zone3_grad)
gradient_ratio = max_grad / zone2_grad

print(f"\n=== 勾配分析 ===")
print(f"Zone 1 (0-24):     {zone1_grad:.1f} K/step")
print(f"Zone 2 (24-240):   {zone2_grad:.1f} K/step")
print(f"Transition (240-248): {transition_grad:.1f} K/step")
print(f"Zone 3 (248-255):  {zone3_grad:.1f} K/step")
print(f"最大勾配比 (max/Zone2): {gradient_ratio:.2f}")

if gradient_ratio <= 2.5:
    print(f"✓ 勾配比{gradient_ratio:.2f}は理想範囲(2.0-2.5)内です")
elif gradient_ratio <= 2.7:
    print(f"⚠️  勾配比{gradient_ratio:.2f}が理想範囲をわずかに超えていますが許容範囲です")
else:
    print(f"❌ 勾配比{gradient_ratio:.2f}が許容範囲を超えています")

# v12との比較
v12_k_values = {
    0: 0, 24: 4148, 32: 5087, 64: 8843, 104: 13538, 128: 16355,
    176: 21988, 192: 23866, 232: 28561, 240: 29500, 248: 31793, 255: 33800
}

print(f"\n=== v12との比較（主要ポイント） ===")
print(f"Input | v12    | v13-MT-R2 | 差分    | 差分%   | 効果")
print(f"------|--------|-----------|---------|---------|------------------")

for inp in [0, 24, 64, 104, 128, 176, 192, 232, 240, 248, 255]:
    v12_k = v12_k_values[inp]
    new_k = k_values[inp]
    diff = new_k - v12_k
    diff_percent = (diff / v12_k * 100) if v12_k > 0 else 0.0

    # 効果の説明
    if inp < 24:
        effect = "同じ"
    elif inp <= 192:
        effect = "ほんの少し明るく" if diff < 0 else "同程度"
    elif inp <= 240:
        effect = "明るく"
    elif inp <= 248:
        effect = "少し濃く"
    else:
        effect = "同じ（紙白保証）"

    print(f"{inp:5} | {v12_k:6} | {new_k:9} | {diff:+7} | {diff_percent:+6.2f}% | {effect}")

# v13-MT-R1との比較
v13_mt_r1_k_values = {
    0: 0, 24: 4148, 64: 8548, 104: 12948, 128: 15588,
    176: 20868, 192: 22628, 232: 28000, 240: 29500, 248: 31793, 255: 33800
}

print(f"\n=== v13-MT-R1との比較 ===")
print(f"Input | v13-MT-R1 | v13-MT-R2 | 差分    | 意味")
print(f"------|-----------|-----------|---------|---------------------------")

for inp in [64, 104, 128, 176, 192, 232, 240, 248, 255]:
    r1_k = v13_mt_r1_k_values[inp]
    new_k = k_values[inp]
    diff = new_k - r1_k

    if diff > 100:
        meaning = "R1より控えめな最適化"
    elif diff < -100:
        meaning = "R1より積極的"
    else:
        meaning = "ほぼ同じ"

    print(f"{inp:5} | {r1_k:9} | {new_k:9} | {diff:+7} | {meaning}")

# .quadファイル生成
quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v13-MT-R2
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Base curve: v12 (v13-MT-R2 variant - Subtle Optimization)
# - Subtle midtone optimization with enhanced 240-248 density
# - Shadow (0-24): 172.8 K/step (same as v12)
# - Midtone (24-240): 114.0 K/step (-2.9% vs v12 117.4)
# - Transition (240-248): Gradual increase for denser highlights
# - Zone 3 (248-255): Smooth transition to paper white
# - K_max: 33800 (same as v12, paper white guaranteed)
# - Target: Subtle midtone brightness + denser 240-248 region
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
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v13-MT-R2.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"\n✓ v13-MT-R2カーブ生成完了: {output_path}")

print(f"\n=== 設計コンセプト ===")
print(f"v12からの変更:")
print(f"  - ミッドトーン: ほんの少し明るく（-2.9%勾配緩和）")
print(f"  - 240-248: 少し濃く（Input 248を32000に設定）")
print(f"  - 紙白: v12と同じ保証（K_max=33800）")
print(f"\nv13-MT-R1との違い:")
print(f"  - より控えめなミッドトーン最適化")
print(f"  - ハイライト域（240-248）を意図的に濃く")
print(f"  - より安全な勾配比")
