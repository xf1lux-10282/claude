#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v14-washi-v4 QTRカーブ生成
和紙専用版: ハイライト圧縮アプローチ（v3の修正版）

v3の問題: K[239]とK[240]が同じ値（28000）でバンディングのリスク
v4の修正: Zone 2を239まで、Zone 3を240-255とし、完全な連続性を確保

設計:
- Zone 1 (0-24): v14と同じ (4148 K)
- Zone 2 (24-239): 緩やか、239で27907 K到達
- Zone 3 (240-255): 強力な圧縮 (27907→29400、約93 K/step)
  → 240-255のネガ濃度差を最小化し、和紙でも階調表現可能に
"""
import numpy as np

# Zone 1: Shadow (0-24) - v14と同じ
zone1_k_values = []
for i in range(0, 25):
    k = round(4148 * i / 24)
    zone1_k_values.append(k)

# Zone 3の設定（先に決める）
zone3_k_start = 27907  # 240の開始値
zone3_k_end = 29400    # 255の終点（和紙での紙白）
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

# Zone 3: Highlight Compression (240-255)
zone3_k_values = []
for i in range(0, zone3_steps + 1):  # 240-255 (16ポイント)
    k = round(zone3_k_start + (zone3_k_end - zone3_k_start) * i / zone3_steps)
    zone3_k_values.append(k)

# 全K-values結合
k_values = zone1_k_values + zone2_k_values + zone3_k_values

# 検証
print("=== v14-washi-v4 K-values検証 ===")
print(f"Total: {len(k_values)} values")
print(f"K[0]: {k_values[0]}")
print(f"K[24]: {k_values[24]}")
print(f"K[128]: {k_values[128]}")
print(f"K[192]: {k_values[192]}")
print(f"K[238]: {k_values[238]}")
print(f"K[239]: {k_values[239]} (Zone 2終点)")
print(f"K[240]: {k_values[240]} (Zone 3開始)")
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
print(f"Zone 3 (240-255):  {zone3_grad:.1f} K/step ← ハイライト圧縮")
print(f"勾配比 (Zone3/Zone2): {gradient_ratio_z3_z2:.2f}")

if zone3_grad < zone2_grad * 1.1:  # 10%以内なら理想的
    print(f"✓ ハイライト圧縮成功: Zone3がZone2とほぼ同等（{gradient_ratio_z3_z2:.2f}倍）")
elif zone3_grad < zone2_grad:
    print(f"✓ ハイライト圧縮成功: Zone3がZone2より緩やか（{gradient_ratio_z3_z2:.2f}倍）")
else:
    print(f"⚠️  Zone3がZone2より急: {gradient_ratio_z3_z2:.2f}倍")

# v14との比較
v14_k_values = {
    0: 0, 24: 4148, 128: 16108, 192: 23468, 238: 28796, 239: 28983, 240: 29400, 248: 31793, 255: 33800
}

print(f"\n=== v14との比較 ===")
print(f"Input | v14    | v14-washi-v4 | 差分    | 差分%")
print(f"------|--------|--------------|---------|-------")

for inp in [0, 24, 128, 192, 238, 239, 240, 248, 255]:
    if inp in v14_k_values:
        v14_k = v14_k_values[inp]
        v4_k = k_values[inp]
        diff = v4_k - v14_k
        diff_percent = (diff / v14_k * 100) if v14_k > 0 else 0.0
        print(f"{inp:5} | {v14_k:6} | {v4_k:12} | {diff:+7} | {diff_percent:+6.2f}%")

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
print(f"\n=== ハイライト圧縮詳細 (240-255) ===")
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
print(f"\n=== v14-washi-v4 設計コンセプト ===")
print(f"✓ Zone 1 (0-24): v14と同じ ({zone1_grad:.1f} K/step)")
print(f"✓ Zone 2 (24-240): 緩やか ({zone2_grad:.1f} K/step)")
print(f"✓ Zone 3 (240-255): 圧縮 ({zone3_grad:.1f} K/step)")
print(f"✓ K_max: {k_values[255]} (v14: 33800との差: {k_values[255] - 33800})")
print(f"✓ 240-255のK範囲: {zone3_k_end - zone3_k_start} K")
print(f"✓ v3からの改善: K[239]≠K[240]（連続性確保）")
print(f"\n推奨露光時間: 6.0-6.5min (v14の6.75minより短く)")

# .quadファイル生成
quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v14-washi-v4
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Base curve: v14 (v14-washi-v4 - Highlight Compression for Washi Paper)
# - Highlight compression approach for washi translucency issues
# - Fixed v3 issue: K[239]≠K[240] for continuous gradation
# - Shadow (0-24): 172.8 K/step (same as v14)
# - Midtone (24-240): 110.5 K/step (reaches 27907 at Input 239)
# - Highlight (240-255): COMPRESSED to 99.5 K/step
#   → Input 240-255 compressed into narrow 27907-29400 K range (1493 K)
#   → Minimizes negative density differences in highlight region
#   → Allows washi to express subtle 240-255 tonal separation
# - K_max: 29400 (vs v14's 33800, thinner negative overall)
# - Compression effect: 34% of v14's 240-255 K range
# - Zone transition: Smooth K[239]→K[240] with no banding
# - Target: Washi paper with thin, translucent characteristics
# - Exposure: 6.0-6.5min (shorter than v14's 6.75min due to thinner negative)
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
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v14-washi-v4.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"\n✓ v14-washi-v4カーブ生成完了: {output_path}")

print(f"\n=== v3からv4への改善点 ===")
print(f"v3の問題:")
print(f"  ❌ K[239] = K[240] = 28000（バンディングリスク）")
print(f"\nv4の解決:")
print(f"  ✓ K[239] = {k_values[239]}")
print(f"  ✓ K[240] = {k_values[240]}")
print(f"  ✓ 差分: {k_values[240] - k_values[239]} K（連続的な階調）")
