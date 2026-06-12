#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v14-washi-v5 QTRカーブ生成
和紙専用版: ハイライト拡張アプローチ（正しい設計）

問題の再理解:
- 和紙で240-255が全て紙白になる
- 原因: ネガの濃度差が小さすぎて、和紙透過時に識別不能

正しい解決策:
- 240-255のK値範囲を「拡張」する
- ネガの濃度差を大きくする
- 和紙を透過する光の差を大きくする
- プリントで240-255が識別可能に

設計:
- Zone 1 (0-24): v14と同じ (4148 K)
- Zone 2 (24-239): やや緩やか、240の開始値を抑える
- Zone 3 (240-255): 強力な拡張 (K値範囲を6000-7000 Kに)
  → v14の4400 Kより大幅に拡張
  → ネガの濃度差を最大化し、和紙でも階調表現可能に
"""
import numpy as np
import matplotlib.pyplot as plt

# Zone 1: Shadow (0-24) - v14と同じ
zone1_k_values = []
for i in range(0, 25):
    k = round(4148 * i / 24)
    zone1_k_values.append(k)

# Zone 3の設定（先に決める）- ハイライト拡張
zone3_k_start = 28000  # 240の開始値（v14の29400より低く）
zone3_k_end = 34500    # 255の終点（v14の33800より高く）
zone3_range = zone3_k_end - zone3_k_start  # 6500 K範囲（v14の4400より拡張）
zone3_steps = 15       # 240→255は16ポイント

# Zone 2: Midtone (24-239) - Zone 3の開始点に到達
zone2_k_start = 4148
zone2_k_end = zone3_k_start  # Zone 3の開始値に接続
zone2_steps = 239 - 24  # 215 steps

actual_zone2_grad = (zone2_k_end - zone2_k_start) / zone2_steps

zone2_k_values = []
for i in range(1, zone2_steps + 1):
    k = round(zone2_k_start + actual_zone2_grad * i)
    zone2_k_values.append(k)

# Zone 3: Highlight Expansion (240-255) - 拡張
zone3_k_values = []
for i in range(0, zone3_steps + 1):  # 240-255 (16ポイント)
    k = round(zone3_k_start + (zone3_k_end - zone3_k_start) * i / zone3_steps)
    zone3_k_values.append(k)

# 全K-values結合
k_values = zone1_k_values + zone2_k_values + zone3_k_values

# 検証
print("=== v14-washi-v5 K-values検証 ===")
print(f"Total: {len(k_values)} values")
print(f"K[0]: {k_values[0]}")
print(f"K[24]: {k_values[24]}")
print(f"K[128]: {k_values[128]}")
print(f"K[192]: {k_values[192]}")
print(f"K[239]: {k_values[239]} (Zone 2終点)")
print(f"K[240]: {k_values[240]} (Zone 3開始 - ハイライト拡張)")
print(f"K[248]: {k_values[248]}")
print(f"K[255]: {k_values[255]} (K_max)")

assert len(k_values) == 256, f"K-values count error: {len(k_values)}"
assert k_values[0] == 0
assert k_values[24] == 4148
assert k_values[255] == zone3_k_end

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

if gradient_ratio_z3_z2 > 2.0:
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
print(f"Input | v14    | v14-washi-v5 | 差分    | 差分%")
print(f"------|--------|--------------|---------|-------")

for inp in [0, 24, 128, 192, 239, 240, 248, 255]:
    if inp in v14_k_values:
        v14_k = v14_k_values[inp]
        v5_k = k_values[inp]
        diff = v5_k - v14_k
        diff_percent = (diff / v14_k * 100) if v14_k > 0 else 0.0
        print(f"{inp:5} | {v14_k:6} | {v5_k:12} | {diff:+7} | {diff_percent:+6.2f}%")

# 240-255の範囲比較
v14_240_255_range = v14_k_values[255] - v14_k_values[240]
v5_240_255_range = k_values[255] - k_values[240]
expansion_ratio = v5_240_255_range / v14_240_255_range

print(f"\n=== 240-255のK値範囲比較 ===")
print(f"v14:          {v14_240_255_range} K")
print(f"v14-washi-v5: {v5_240_255_range} K")
print(f"拡張率: {expansion_ratio:.2f}x (v14の{expansion_ratio:.2f}倍に拡張)")

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
print(f"\n=== v14-washi-v5 設計コンセプト ===")
print(f"✓ Zone 1 (0-24): v14と同じ ({zone1_grad:.1f} K/step)")
print(f"✓ Zone 2 (24-240): やや緩やか ({zone2_grad:.1f} K/step)")
print(f"✓ Zone 3 (240-255): 強力な拡張 ({zone3_grad:.1f} K/step)")
print(f"✓ K_max: {k_values[255]} (v14: 33800との差: {k_values[255] - 33800:+d})")
print(f"✓ 240-255のK範囲: {v5_240_255_range} K (v14の{expansion_ratio:.2f}倍)")
print(f"✓ ネガ濃度差: 大きい → 和紙でも識別可能")
print(f"\n推奨露光時間: 7.0-7.5min (v14の6.75minより長く)")
print(f"理由: K_maxが高い + 240-255が濃い → 全体的に濃いネガ → 露光時間延長")

# .quadファイル生成
quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v14-washi-v5
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Base curve: v14 (v14-washi-v5 - Highlight Expansion for Washi Paper)
# - Highlight expansion approach for washi translucency issues
# - CORRECT APPROACH: Expand 240-255 K range to increase negative density differences
# - Shadow (0-24): 172.8 K/step (same as v14)
# - Midtone (24-240): 111.0 K/step (gradual to reach 28000)
# - Highlight (240-255): EXPANDED to 433.3 K/step (vs v14's 293.3)
#   → Input 240-255 expanded into wide 28000-34500 K range (6500 K)
#   → Maximizes negative density differences in highlight region
#   → Large density differences = large light transmission differences
#   → Allows washi to express subtle 240-255 tonal separation
# - K_max: 34500 (vs v14's 33800, denser negative overall)
# - Expansion effect: 1.48x wider than v14's 240-255 K range
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
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v14-washi-v5.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"\n✓ v14-washi-v5カーブ生成完了: {output_path}")

print(f"\n=== 設計思想の転換 ===")
print(f"誤った理解（v3まで）:")
print(f"  ❌ ハイライト圧縮（K範囲を狭くする）")
print(f"  ❌ ネガ濃度差を小さくする")
print(f"  結果: 和紙では識別不能")
print(f"\n正しい理解（v5）:")
print(f"  ✓ ハイライト拡張（K範囲を広くする）")
print(f"  ✓ ネガ濃度差を大きくする")
print(f"  ✓ 和紙を透過する光の差を大きくする")
print(f"  期待結果: 和紙でも240-255が識別可能")

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
ax1.plot(all_inputs, k_values, 'r-', linewidth=2.5, label='v14-washi-v5 (highlight expansion)', alpha=0.8)
ax1.axhline(y=33800, color='blue', linestyle=':', alpha=0.3, label='v14 K_max')
ax1.axhline(y=34500, color='red', linestyle=':', alpha=0.3, label='v5 K_max')
ax1.set_xlabel('Input (0-255)', fontsize=12)
ax1.set_ylabel('K value (0-65535)', fontsize=12)
ax1.set_title('v14 vs v14-washi-v5: Highlight Expansion', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, 255)
ax1.set_ylim(0, 36000)

# 2. ハイライト領域拡大（220-255）
highlight_range = range(220, 256)
v14_highlight = [v14_full.get(i, np.interp(i, v14_inputs, v14_k_list)) for i in highlight_range]
v5_highlight = [k_values[i] for i in highlight_range]

ax2.plot(highlight_range, v14_highlight, 'b-', linewidth=3, label='v14', marker='o', markersize=6, alpha=0.8)
ax2.plot(highlight_range, v5_highlight, 'r-', linewidth=3, label='v14-washi-v5', marker='s', markersize=6, alpha=0.8)
ax2.axvline(x=240, color='green', linestyle='--', linewidth=2, alpha=0.5, label='Input 240 (expansion start)')
ax2.fill_between(highlight_range, v14_highlight, v5_highlight,
                  where=[v5_highlight[i] > v14_highlight[i] for i in range(len(highlight_range))],
                  alpha=0.2, color='red', label='Expansion area')
ax2.set_xlabel('Input', fontsize=12)
ax2.set_ylabel('K value', fontsize=12)
ax2.set_title('Highlight Region (220-255): Expansion Effect', fontsize=14, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.set_xlim(220, 255)

# 3. 勾配比較
v14_gradient = np.diff(v14_k_list)
v5_gradient = np.diff(k_values)

ax3.plot(range(len(v14_gradient)), v14_gradient, 'b-', linewidth=2, label='v14 gradient', alpha=0.7)
ax3.plot(range(len(v5_gradient)), v5_gradient, 'r-', linewidth=2, label='v14-washi-v5 gradient', alpha=0.8)
ax3.axvline(x=24, color='gray', linestyle='--', alpha=0.3)
ax3.axvline(x=240, color='green', linestyle='--', linewidth=2, alpha=0.5, label='Highlight expansion start')
ax3.axhline(y=zone3_grad, color='red', linestyle=':', linewidth=2, alpha=0.5, label=f'v5 Zone3: {zone3_grad:.1f} K/step')
ax3.set_xlabel('Input', fontsize=12)
ax3.set_ylabel('Gradient (K/step)', fontsize=12)
ax3.set_title('Gradient Comparison: Highlight Expansion', fontsize=14, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3)
ax3.set_xlim(0, 255)
ax3.set_ylim(0, 500)

# 4. 240-255のK範囲比較
versions = ['v14', 'v14-washi-v5']
ranges = [v14_240_255_range, v5_240_255_range]
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
ax4.set_ylim(0, 7000)

# 拡張効果の説明
explanation = f"""Highlight Expansion Strategy:

v14:  {v14_240_255_range} K range
v5:   {v5_240_255_range} K range

Expansion: {expansion_ratio:.2f}x

Effect on negative:
- Larger density differences
- More distinct light transmission
- Better tonal separation on washi
"""
ax4.text(0.5, 0.5, explanation, transform=ax4.transAxes,
         fontsize=10, verticalalignment='center', horizontalalignment='center',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

plt.tight_layout()
output_png = '/tmp/v14_washi_v5_expansion.png'
plt.savefig(output_png, dpi=150, bbox_inches='tight')
print(f"\nグラフ保存完了: {output_png}")
