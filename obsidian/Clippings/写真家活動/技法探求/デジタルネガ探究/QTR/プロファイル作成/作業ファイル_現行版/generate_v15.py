#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v15 QTRカーブ生成
v14ベース: Input 240-255を等分補完で50000まで滑らかに到達

設計思想:
- v14の0-239をそのまま使用
- Input 240-255を等分補完（1373.3 K/step）
- 狙い: 紙白への滑らかで自然な移行 + 確実な紙白到達

Generated: 2026-04-08 (Revised for smooth gradient)
"""
import numpy as np

print("=" * 80)
print("PX1V-PtPd-xf1-v15 カーブ生成開始（240-255等分補完版）")
print("=" * 80)

# Zone 1: Shadow (0-24) - v14と同じ
print("\n[Step 1] Zone 1生成（v14と同じ）")
zone1_k_values = []
for i in range(0, 25):
    k = round(4148 * i / 24)
    zone1_k_values.append(k)

print(f"✓ Zone 1完了: Input 0-24")
print(f"  K[0] = {zone1_k_values[0]}")
print(f"  K[24] = {zone1_k_values[24]}")

# Zone 2: Midtone (24-239) - v14と同じ（115.0 K/step）
print("\n[Step 2] Zone 2生成（v14と同じ）")
zone2_k_start = 4148
target_zone2_grad = 115.0
zone2_steps = 239 - 24  # 215 steps

zone2_k_values = []
for i in range(1, zone2_steps + 1):
    k = round(zone2_k_start + target_zone2_grad * i)
    zone2_k_values.append(k)

print(f"✓ Zone 2完了: Input 24-239")
print(f"  K[25] = {zone2_k_values[0]}")
print(f"  K[239] = {zone2_k_values[-1]}")

# Input 240: 指定値 - v14と同じ
print("\n[Step 3] Input 240設定（v14と同じ）")
k_240 = 29400
print(f"✓ Input 240: K = {k_240}")

# Input 255: 50000（★v15の目標値）
print("\n[Step 4] Input 255設定（★v15の変更点）")
k_255 = 50000
print(f"✓ Input 255: K = {k_255} (v14: 33800 → v15: 50000, +48%)")

# Zone 3 NEW: Highlight (240-255) 等分補完 ★v15の改良点
print("\n[Step 5] Zone 3生成（Input 240-255等分補完, ★v15の改良点）")
zone3_total_steps = 15  # 240→255の間は15ステップ
zone3_grad = (k_255 - k_240) / zone3_total_steps

zone3_k_values = []
for i in range(1, zone3_total_steps + 1):
    k = round(k_240 + zone3_grad * i)
    zone3_k_values.append(k)

print(f"✓ Zone 3完了: Input 241-255")
print(f"  勾配: {zone3_grad:.1f} K/step（一定）")
print(f"  K[241] = {zone3_k_values[0]}")
print(f"  K[254] = {zone3_k_values[13]}")
print(f"  K[255] = {zone3_k_values[14]}")

# 全K-values結合
k_values = zone1_k_values + zone2_k_values + [k_240] + zone3_k_values

# 検証
print("\n[Step 6] K-values検証")
print(f"Total: {len(k_values)} values")
print(f"K[0]: {k_values[0]}")
print(f"K[24]: {k_values[24]}")
print(f"K[128]: {k_values[128]}")
print(f"K[192]: {k_values[192]}")
print(f"K[240]: {k_values[240]}")
print(f"K[254]: {k_values[254]}")
print(f"K[255]: {k_values[255]}")

assert len(k_values) == 256, f"K-values count error: {len(k_values)}"
assert k_values[0] == 0
assert k_values[240] == k_240
assert k_values[255] == k_255

print("✓ 全検証OK")

# 勾配分析
print("\n[Step 7] 勾配分析")
gradients = np.diff(k_values)
zone1_grad = gradients[0:24].mean()
zone2_grad = gradients[24:240].mean()
zone3_grad_actual = gradients[240:255].mean()
zone3_std = gradients[240:255].std()

print(f"Zone 1 (0-24):        {zone1_grad:.1f} K/step")
print(f"Zone 2 (24-240):      {zone2_grad:.1f} K/step")
print(f"Zone 3 (240-255):     {zone3_grad_actual:.1f} K/step ★v15改良点")
print(f"Zone 3 勾配標準偏差:   {zone3_std:.1f} (0.0に近いほど滑らか)")

# v14との比較
print("\n[Step 8] v14との比較")
print(f"Input | v14    | v15    | 差分     | 差分%")
print(f"------|--------|--------|----------|-------")

v14_key_points = {
    0: 0, 24: 4148, 128: 16108, 192: 23468,
    240: 29400, 248: 31900, 254: 33800, 255: 33800
}

for inp in [0, 24, 128, 192, 240, 248, 254, 255]:
    v14_k = v14_key_points[inp]
    v15_k = k_values[inp]
    diff = v15_k - v14_k
    diff_percent = (diff / v14_k * 100) if v14_k > 0 else 0.0
    marker = "★" if inp >= 240 else " "
    print(f"{inp:5} | {v14_k:6} | {v15_k:6} | {diff:+8} | {diff_percent:+6.2f}% {marker}")

# 露光時間の推定
print("\n[Step 9] 露光時間の推定")
v14_exposure_min = 6.75  # 6分45秒
k_increase_percent = (50000 - 33800) / 33800 * 100  # +47.9%
estimated_reduction_percent = k_increase_percent * 0.3  # K値増加の30%程度露光短縮
v15_exposure_min = v14_exposure_min * (1 - estimated_reduction_percent / 100)
v15_min = int(v15_exposure_min)
v15_sec = int((v15_exposure_min - v15_min) * 60)

print(f"v14露光時間: 6分45秒（6.75分）")
print(f"K[255]増加: +{k_increase_percent:.1f}%")
print(f"推定露光短縮: -{estimated_reduction_percent:.1f}%")
print(f"v15推定露光時間: {v15_min}分{v15_sec:02d}秒（{v15_exposure_min:.2f}分）")
print(f"※実測で±15秒調整推奨")

# .quadファイル生成
print("\n[Step 10] Quadファイル生成")

quad_content = f"""## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v15
# Printer: EPSON SC-PX1V
# PPD: EPSON SC-PX1V
# - Base curve: v14 (Input 0-239)
# - Input 240-255: Linear interpolation to 50000 ({zone3_grad:.1f} K/step)
# - Shadow (0-24): 172.8 K/step (same as v14)
# - Midtone (24-240): 115.0 K/step (same as v14)
# - Highlight (240-255): {zone3_grad:.1f} K/step (smooth gradient to paper white)
# - Input 240: 29400 (same as v14)
# - Input 254: {k_values[254]} (v14: 33800, diff: {k_values[254]-33800:+d})
# - Input 255: 50000 (★enhanced for reliable paper white, v14: 33800)
# - Zone 3 gradient std dev: {zone3_std:.1f} (perfectly smooth)
# - Target: Smooth transition to paper white + reliable achievement
# - Exposure: ~{v15_min}:{v15_sec:02d} (estimated, adjust ±15sec as needed)
# Generated: 2026-04-08 by Claude Code (Revised for smooth gradient)

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
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v15.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v15カーブ生成完了: {output_path}")

# CSV出力
print("\n[Step 11] CSV出力")

csv_path = output_path.replace('.quad', '_values.csv')
with open(csv_path, 'w', encoding='utf-8') as f:
    f.write("Input,K_value,Diff_from_v14,Diff_percent\n")
    for i in range(256):
        # v14のK値を取得
        if i <= 239:
            v14_k = k_values[i]
        elif i == 240:
            v14_k = 29400
        elif i < 248:
            v14_k = round(29400 + (31900 - 29400) * (i - 240) / 8)
        elif i == 248:
            v14_k = 31900
        elif i < 255:
            v14_k = round(31900 + (33800 - 31900) * (i - 248) / 6)
        else:  # i == 255
            v14_k = 33800

        diff = k_values[i] - v14_k
        diff_pct = (diff / v14_k * 100) if v14_k > 0 else 0.0
        f.write(f"{i},{k_values[i]},{diff},{diff_pct:.2f}\n")

print(f"✓ CSV出力完了: {csv_path}")

# 240-255の詳細表示
print("\n[Step 12] Input 240-255の詳細（v14との比較）")
print(f"Input | v15 K  | v14 K  | 差分   | v15勾配")
print(f"------|--------|--------|--------|--------")
for i in range(240, 256):
    if i <= 239:
        v14_k = k_values[i]
    elif i == 240:
        v14_k = 29400
    elif i < 248:
        v14_k = round(29400 + (31900 - 29400) * (i - 240) / 8)
    elif i == 248:
        v14_k = 31900
    elif i < 255:
        v14_k = round(31900 + (33800 - 31900) * (i - 248) / 6)
    else:
        v14_k = 33800

    v15_k = k_values[i]
    diff = v15_k - v14_k

    if i > 240:
        grad = k_values[i] - k_values[i-1]
        print(f"{i:5} | {v15_k:6} | {v14_k:6} | {diff:+6} | +{grad:5}")
    else:
        print(f"{i:5} | {v15_k:6} | {v14_k:6} | {diff:+6} |")

# まとめ
print(f"\n{'=' * 80}")
print(f"PX1V-PtPd-xf1-v15 カーブ完成（240-255等分補完版）")
print(f"{'=' * 80}")
print(f"\n【v14からの変更点】")
print(f"  ★ Input 240-255: 等分補完（{zone3_grad:.1f} K/step）")
print(f"  ✓ Input 0-239: v14と完全に同じ")
print(f"  ✓ Input 255: 33800 → 50000 (+48%)")
print(f"\n【仕様】")
print(f"  ✓ Shadow (0-24): 172.8 K/step")
print(f"  ✓ Midtone (24-240): 115.0 K/step")
print(f"  ✓ Highlight (240-255): {zone3_grad:.1f} K/step ★完全に滑らか")
print(f"  ✓ Input 240: 29400")
print(f"  ✓ Input 254: {k_values[254]}")
print(f"  ✓ Input 255: 50000 ★")
print(f"  ✓ Zone 3勾配標準偏差: {zone3_std:.1f}（数学的に完璧）")
print(f"  ✓ 推定露光時間: {v15_min}分{v15_sec:02d}秒")
print(f"\n【狙い】")
print(f"  - 紙白への滑らかで自然な移行（段差なし）")
print(f"  - より確実な紙白到達")
print(f"  - v14の豊かな階調（0-239）を維持")
print(f"  - Input 254-255も自然（16200 K/stepの急峻ジャンプ回避）")
print(f"\n【v14との設計思想の違い】")
print(f"  v14: Input 254-255同値（紙白への配慮なし）")
print(f"  v15: Input 240-255等分補完（数学的に最も滑らか）")
print(f"\n【次のステップ】")
print(f"1. v15をQTRにインストール")
print(f"2. 推定露光時間（{v15_min}分{v15_sec:02d}秒）でテストプリント")
print(f"3. Input 255の紙白到達 + 254-255の自然さを確認")
print(f"4. 必要に応じて露光時間±15秒調整")
print(f"{'=' * 80}")
