#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v14-washi-v6 QTRカーブ生成
和紙専用版: ハイライト拡張アプローチ（修正版）

v5の問題:
1. K[239] = K[240] = 28000（バンディングリスク）
2. K[255] = 34500（高すぎる、32000程度が適切）

v6の修正:
1. Input 240の値を先に確定: K[240] = 27000
2. Zone 2 (24-240): 均等補間で4148→27000
3. Zone 3 (240-255): ハイライト拡張で27000→32000
   → 240-255の範囲: 5000 K（v14の4400 Kより拡張）

設計:
- Zone 1 (0-24): v14と同じ (4148 K)
- Zone 2 (24-240): 均等補間 (4148→27000, 約106 K/step)
- Zone 3 (240-255): ハイライト拡張 (27000→32000, 約333 K/step)
  → ネガ濃度差を大きくし、和紙でも階調表現可能に
"""
import numpy as np
import matplotlib.pyplot as plt

# Zone 1: Shadow (0-24) - v14と同じ
zone1_k_values = []
for i in range(0, 25):
    k = round(4148 * i / 24)
    zone1_k_values.append(k)

# Zone 3の設定（先に決める）
k_240 = 27000  # Input 240の確定値
k_255 = 32000  # Input 255の確定値（適切な範囲）

# Zone 2: Midtone (24-240) - 均等補間
zone2_k_start = 4148
zone2_k_end = k_240
zone2_steps = 240 - 24  # 216 steps

zone2_k_values = []
for i in range(1, zone2_steps + 1):
    k = round(zone2_k_start + (zone2_k_end - zone2_k_start) * i / zone2_steps)
    zone2_k_values.append(k)

# Zone 3: Highlight Expansion (241-255) - 線形補間
# 240はZone 2の最後のポイントなので、241から開始
zone3_steps = 15  # 241→255は15ポイント

zone3_k_values = []
for i in range(1, zone3_steps + 1):  # 241-255 (15ポイント)
    k = round(k_240 + (k_255 - k_240) * i / zone3_steps)
    zone3_k_values.append(k)

# 全K-values結合
k_values = zone1_k_values + zone2_k_values + zone3_k_values

# 検証
print("=== v14-washi-v6 K-values検証 ===")
print(f"Total: {len(k_values)} values")
print(f"K[0]: {k_values[0]}")
print(f"K[24]: {k_values[24]}")
print(f"K[128]: {k_values[128]}")
print(f"K[192]: {k_values[192]}")
print(f"K[239]: {k_values[239]} (Zone 2終点)")
print(f"K[240]: {k_values[240]} (Zone 3開始 - 確定値)")
print(f"K[248]: {k_values[248]}")
print(f"K[255]: {k_values[255]} (K_max - 確定値)")

assert len(k_values) == 256, f"K-values count error: {len(k_values)}"
assert k_values[0] == 0
assert k_values[24] == 4148
assert k_values[240] == k_240
assert k_values[255] == k_255

# 連続性チェック
print(f"\n=== 239-240連続性チェック ===")
if k_values[239] == k_values[240]:
    print(f"❌ K[239]とK[240]が同じ値: {k_values[239]}")
else:
    print(f"✓ K[239]とK[240]は異なる値")
    print(f"  K[239]: {k_values[239]}")
    print(f"  K[240]: {k_values[240]}")
    print(f"  差分: {k_values[240] - k_values[239]}")

# 勾配分析
gradients = np.diff(k_values)
zone1_grad = gradients[0:24].mean()
zone2_grad = gradients[24:240].mean()
zone3_grad = gradients[240:255].mean()

gradient_ratio_z3_z2 = zone3_grad / zone2_grad

print(f"\n=== 勾配分析 ===")
print(f"Zone 1 (0-24):     {zone1_grad:.1f} K/step")
print(f"Zone 2 (24-240):   {zone2_grad:.1f} K/step")
print(f"Zone 3 (240-255):  {zone3_grad:.1f} K/step ← ハイライト拡張")
print(f"勾配比 (Zone3/Zone2): {gradient_ratio_z3_z2:.2f}")

if gradient_ratio_z3_z2 > 2.5:
    print(f"✓ ハイライト拡張成功: Zone3がZone2の{gradient_ratio_z3_z2:.2f}倍（急勾配）")
elif gradient_ratio_z3_z2 > 1.5:
    print(f"⚠️  ハイライト拡張効果あり: Zone3がZone2の{gradient_ratio_z3_z2:.2f}倍")
else:
    print(f"❌ ハイライト拡張不足: Zone3がZone2の{gradient_ratio_z3_z2:.2f}倍")

# v14との比較
v14_k_values = {
    0: 0, 24: 4148, 128: 16108, 192: 23468, 239: 28983, 240: 29400, 248: 31793, 255: 33800
}

print(f"\n=== v14との比較 ===")
print(f"Input | v14    | v14-washi-v6 | 差分    | 差分%")
print(f"------|--------|--------------|---------|-------")

for inp in [0, 24, 128, 192, 239, 240, 248, 255]:
    if inp in v14_k_values:
        v14_k = v14_k_values[inp]
        v6_k = k_values[inp]
        diff = v6_k - v14_k
        diff_percent = (diff / v14_k * 100) if v14_k > 0 else 0.0
        print(f"{inp:5} | {v14_k:6} | {v6_k:12} | {diff:+7} | {diff_percent:+6.2f}%")

# 240-255の範囲比較
v14_240_255_range = v14_k_values[255] - v14_k_values[240]
v6_240_255_range = k_values[255] - k_values[240]
expansion_ratio = v6_240_255_range / v14_240_255_range

print(f"\n=== 240-255のK値範囲比較 ===")
print(f"v14:          {v14_240_255_range} K")
print(f"v14-washi-v6: {v6_240_255_range} K")
print(f"拡張率: {expansion_ratio:.2f}x (v14の{expansion_ratio:.2f}倍に拡張)")

# 239-241の詳細
print(f"\n=== Zone 2→3遷移詳細 (238-241) ===")
print(f"Input | K-value | 前ステップとの差分")
print(f"------|---------|------------------")
for inp in range(238, 242):
    k = k_values[inp]
    if inp > 238:
        diff = k - k_values[inp-1]
        marker = " ← Zone境界" if inp == 240 else ""
        print(f"{inp:5} | {k:7} | {diff:+7}{marker}")
    else:
        print(f"{inp:5} | {k:7} | (開始)")

# 240-255の詳細
print(f"\n=== ハイライト拡張詳細 (240-255) ===")
print(f"Input | K-value | 前ステップとの差分")
print(f"------|---------|------------------")
for inp in range(240, 256):
    k = k_values[inp]
    if inp > 240:
        diff = k - k_values[inp-1]
        print(f"{inp:5} | {k:7} | {diff:+7}")
    else:
        diff_from_239 = k - k_values[239]
        print(f"{inp:5} | {k:7} | {diff_from_239:+7} (from 239)")

# 主要ポイント
print(f"\n=== v14-washi-v6 設計コンセプト ===")
print(f"✓ Zone 1 (0-24): v14と同じ ({zone1_grad:.1f} K/step)")
print(f"✓ Zone 2 (24-240): 均等補間 ({zone2_grad:.1f} K/step)")
print(f"✓ Zone 3 (240-255): ハイライト拡張 ({zone3_grad:.1f} K/step)")
print(f"✓ K[240]: {k_values[240]} (確定値)")
print(f"✓ K_max: {k_values[255]} (適切な範囲)")
print(f"✓ 240-255のK範囲: {v6_240_255_range} K (v14の{expansion_ratio:.2f}倍)")
print(f"✓ 239-240連続性: 確保")
print(f"\n推奨露光時間: 7.0-7.5min (v14の6.75minより長く)")

# .quadファイル生成
quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v14-washi-v6
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Base curve: v14 (v14-washi-v6 - Highlight Expansion for Washi Paper)
# - Highlight expansion approach for washi translucency issues
# - Fixed design: K[240]=27000 confirmed, then interpolate 24-240
# - Shadow (0-24): 172.8 K/step (same as v14)
# - Midtone (24-240): 105.9 K/step (uniform interpolation to 27000)
# - Highlight (240-255): EXPANDED to 333.3 K/step
#   → Input 240-255 expanded into wide 27000-32000 K range (5000 K)
#   → 1.14x wider than v14's 240-255 K range (4400 K)
#   → Maximizes negative density differences in highlight region
#   → Large density differences = distinct light transmission on washi
#   → Allows washi to express subtle 240-255 tonal separation
# - K_max: 32000 (appropriate range, not too high)
# - Continuous gradation: K[239]≠K[240] ensured
# - Target: Washi paper with thin, translucent characteristics
# - Exposure: 7.0-7.5min (longer than v14's 6.75min due to denser negative)
# Generated: 2026-04-01 by Claude Code

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
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v14-washi-v6.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"\n✓ v14-washi-v6カーブ生成完了: {output_path}")

# グラフ生成
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

# v14のK値
v14_full = {
    0: 0, 8: 1383, 16: 2765, 24: 4148, 32: 5087, 40: 6026, 48: 6965, 56: 7904,
    64: 8843, 72: 9782, 80: 10721, 88: 11660, 96: 12599, 104: 13538, 112: 14477, 120: 15416,
    128: 16355, 136: 17293, 144: 18232, 152: 19171, 160: 20110, 168: 21049, 176: 21988, 184: 22927,
    192: 23866, 200: 24805, 208: 25744, 216: 26683, 224: 27622, 232: 28561, 240: 29400, 248: 31793, 255: 33800
}

# 1. 全体カーブ比較
v14_inputs = sorted(v14_full.keys())
v14_k_list = [v14_full[i] for i in v14_inputs]
all_inputs = list(range(256))

ax1.plot(v14_inputs, v14_k_list, 'b-', linewidth=2.5, label='v14 (western paper)', marker='o', markersize=4, alpha=0.8)
ax1.plot(all_inputs, k_values, 'r-', linewidth=2.5, label='v14-washi-v6 (highlight expansion)', alpha=0.8)
ax1.axhline(y=k_240, color='green', linestyle=':', alpha=0.5, label=f'K[240]={k_240}')
ax1.axhline(y=k_255, color='red', linestyle=':', alpha=0.5, label=f'K[255]={k_255}')
ax1.set_xlabel('Input (0-255)', fontsize=12)
ax1.set_ylabel('K value (0-65535)', fontsize=12)
ax1.set_title('v14 vs v14-washi-v6: Corrected Highlight Expansion', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, 255)
ax1.set_ylim(0, 35000)

# 2. ハイライト領域拡大（220-255）
highlight_range = range(220, 256)
v14_highlight = [v14_full.get(i, np.interp(i, v14_inputs, v14_k_list)) for i in highlight_range]
v6_highlight = [k_values[i] for i in highlight_range]

ax2.plot(highlight_range, v14_highlight, 'b-', linewidth=3, label='v14', marker='o', markersize=6, alpha=0.8)
ax2.plot(highlight_range, v6_highlight, 'r-', linewidth=3, label='v14-washi-v6', marker='s', markersize=6, alpha=0.8)
ax2.axvline(x=240, color='green', linestyle='--', linewidth=2, alpha=0.5, label=f'Input 240 (K={k_240})')
ax2.fill_between(highlight_range, v14_highlight, v6_highlight,
                  where=[v6_highlight[i] > v14_highlight[i] for i in range(len(highlight_range))],
                  alpha=0.2, color='red', label='Expansion area')
ax2.set_xlabel('Input', fontsize=12)
ax2.set_ylabel('K value', fontsize=12)
ax2.set_title('Highlight Region (220-255): Expansion Effect', fontsize=14, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.set_xlim(220, 255)

# 3. 勾配比較
v14_gradient = np.diff(v14_k_list)
v6_gradient = np.diff(k_values)

ax3.plot(range(len(v14_gradient)), v14_gradient, 'b-', linewidth=2, label='v14 gradient', alpha=0.7)
ax3.plot(range(len(v6_gradient)), v6_gradient, 'r-', linewidth=2, label='v14-washi-v6 gradient', alpha=0.8)
ax3.axvline(x=24, color='gray', linestyle='--', alpha=0.3)
ax3.axvline(x=240, color='green', linestyle='--', linewidth=2, alpha=0.5, label='Highlight expansion start')
ax3.axhline(y=zone3_grad, color='red', linestyle=':', linewidth=2, alpha=0.5, label=f'v6 Zone3: {zone3_grad:.1f} K/step')
ax3.set_xlabel('Input', fontsize=12)
ax3.set_ylabel('Gradient (K/step)', fontsize=12)
ax3.set_title('Gradient Comparison: Highlight Expansion', fontsize=14, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3)
ax3.set_xlim(0, 255)
ax3.set_ylim(0, 400)

# 4. 240-255のK範囲比較
versions = ['v14', 'v14-washi-v6']
ranges = [v14_240_255_range, v6_240_255_range]
colors = ['blue', 'red']

bars = ax4.bar(versions, ranges, color=colors, alpha=0.7, edgecolor='black', linewidth=2)

for i, (bar, r) in enumerate(zip(bars, ranges)):
    height = bar.get_height()
    ratio = r / v14_240_255_range
    ax4.text(bar.get_x() + bar.get_width()/2., height,
             f'{r} K\n({ratio:.2f}x)',
             ha='center', va='bottom', fontsize=12, fontweight='bold')

ax4.set_ylabel('K value range (240-255)', fontsize=12)
ax4.set_title('240-255 K Range: Expansion Effect', fontsize=14, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')
ax4.set_ylim(0, 6000)

# 詳細情報
details = f"""v14-washi-v6 Design:

K[240] = {k_240} (confirmed)
K[255] = {k_255} (appropriate)

240-255 range:
  v14:  {v14_240_255_range} K
  v6:   {v6_240_255_range} K

Expansion: {expansion_ratio:.2f}x

Gradient ratio: {gradient_ratio_z3_z2:.2f}x
(Zone 3 / Zone 2)

Exposure: 7.0-7.5min
"""
ax4.text(0.5, 0.35, details, transform=ax4.transAxes,
         fontsize=10, verticalalignment='center', horizontalalignment='center',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
         family='monospace')

plt.tight_layout()
output_png = '/tmp/v14_washi_v6_expansion.png'
plt.savefig(output_png, dpi=150, bbox_inches='tight')
print(f"\nグラフ保存完了: {output_png}")
