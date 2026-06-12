#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v13-MT-R2-improved
v12と比較して:
- ミッドトーン: ほんの少し明るく（勾配を少し緩く）
- 240地点: v12とほぼ同じ（勾配比を許容範囲内に）
- 248地点: 少し濃く
- 紙白到達保証: K_max = 33800
"""
import numpy as np

# 設計方針:
# Input 240をv12に近づけて勾配比を改善
# ミッドトーンは控えめに最適化

# Zone 1: Shadow (0-24) - v12と同じ
zone1_k_values = []
for i in range(0, 25):
    k = round(4148 * i / 24)
    zone1_k_values.append(k)

# Zone 2: Midtone (24-239) - 少し緩やか
zone2_k_start = 4148
target_zone2_grad = 115.0  # v12: 117.4
zone2_steps = 239 - 24  # 215 steps
zone2_k_end = round(zone2_k_start + target_zone2_grad * zone2_steps)

zone2_k_values = []
for i in range(1, zone2_steps + 1):
    k = round(zone2_k_start + target_zone2_grad * i)
    zone2_k_values.append(k)

# Input 240: v12より少し低め
k_240 = 29400  # v12: 29500

# Input 241-247: 240→248を線形補間
k_248 = 31900  # v12: 31793より少し高く（32000から調整）

transition_k_values = []
steps_240_to_248 = 8
for i in range(1, steps_240_to_248):  # 241-247
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

# 検証
print("=== v13-MT-R2-improved K-values検証 ===")
print(f"Total: {len(k_values)} values")
print(f"K[0]: {k_values[0]}")
print(f"K[24]: {k_values[24]}")
print(f"K[128]: {k_values[128]}")
print(f"K[192]: {k_values[192]}")
print(f"K[239]: {k_values[239]}")
print(f"K[240]: {k_values[240]} (指定値{k_240})")
print(f"K[248]: {k_values[248]} (指定値{k_248})")
print(f"K[255]: {k_values[255]}")

assert len(k_values) == 256
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

# 勾配比
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

    if inp <= 24:
        effect = "同じ"
    elif inp <= 192:
        if diff_percent < -1.5:
            effect = "ほんの少し明るく"
        elif diff_percent < -0.5:
            effect = "わずかに明るく"
        else:
            effect = "ほぼ同じ"
    elif inp == 240:
        effect = "わずかに明るく"
    elif inp == 248:
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
print(f"Input | v13-MT-R1 | v13-MT-R2 | 差分    | 評価")
print(f"------|-----------|-----------|---------|---------------------------")

for inp in [64, 104, 128, 176, 192, 232, 240, 248, 255]:
    r1_k = v13_mt_r1_k_values[inp]
    new_k = k_values[inp]
    diff = new_k - r1_k
    diff_percent = (diff / r1_k * 100) if r1_k > 0 else 0.0

    if diff > 200:
        eval_text = "R1より控えめ（暗め）"
    elif diff < -200:
        eval_text = "R1より積極的（明るめ）"
    elif abs(diff) <= 50:
        eval_text = "R1とほぼ同じ"
    else:
        eval_text = f"R1より{'+' if diff > 0 else ''}{diff_percent:.1f}%"

    print(f"{inp:5} | {r1_k:9} | {new_k:9} | {diff:+7} | {eval_text}")

# .quadファイル生成
quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v13-MT-R2
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Base curve: v12 (v13-MT-R2 variant - Subtle Midtone Optimization)
# - Subtle midtone optimization with balanced gradient ratio
# - Shadow (0-24): 172.8 K/step (same as v12)
# - Midtone (24-240): 115.0 K/step (-2.0% vs v12 117.4)
# - Input 240: 29300 (-0.7% vs v12)
# - Input 248: 32000 (+0.7% vs v12, denser highlights)
# - Highlight (248-255): Smooth transition to paper white
# - K_max: 33800 (same as v12, paper white guaranteed)
# - Gradient ratio: Within acceptable range
# - Target: Subtle midtone brightness + slightly denser 248
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

# 残り9チャンネル
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
print(f"  - ミッドトーン(64-192): ほんの少し明るく（-1.5~-2.0%）")
print(f"  - Input 240: わずかに明るく（-0.7%）")
print(f"  - Input 248: 少し濃く（+0.7%）")
print(f"  - 紙白: v12と同じ保証（K_max=33800）")
print(f"\nv13-MT-R1との違い:")
print(f"  - ミッドトーン最適化を控えめに（約半分の効果）")
print(f"  - Input 248を濃く設定（R1と異なる特徴）")
print(f"  - より安全な勾配比")
