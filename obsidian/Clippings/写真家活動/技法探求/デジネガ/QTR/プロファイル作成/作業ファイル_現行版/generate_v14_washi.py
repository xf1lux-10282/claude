#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v14-washi QTRカーブ生成
和紙専用カーブ: Input 240-255の階調表現問題を解決

設計:
- Zone 1 (0-24): v14と同じ（Shadow階調維持）
- Zone 2+3 (24-255): 均等補間でK_max=29,400
- K_max: 29,400（v14のInput 240の値 = 和紙での紙白到達点）
- 勾配: 109.3 K/step（24-255で均一）

問題解決:
- v14では240-255が和紙で表現できない
- K_maxを29,400に下げることで、ネガをより濃くし階調を確保
- Shadow（0-24）はv14と同じで維持

露光時間:
- v14: 6.75分
- v14-washi推奨: 7.0-7.5分（ネガが濃くなるため延長が必要）

生成日: 2026-04-01
QTR作業ルールブック準拠（ルール2,5,6,7,9）
"""
import numpy as np
import matplotlib.pyplot as plt

# QTR定数（ルール9）
QTR_MAX_VALUE = 65535  # 16-bit maximum

# ===== Zone 1: Shadow (0-24) - v14と同じ =====
print("=" * 80)
print("v14-washi カーブ生成開始")
print("=" * 80)
print("\n[Step 1] Zone 1 (Shadow 0-24) - v14と同じ")

zone1_k_values = []
for i in range(0, 25):
    k = round(4148 * i / 24)
    zone1_k_values.append(k)

print(f"✓ Zone 1完成: {len(zone1_k_values)} values")
print(f"  K[0] = {zone1_k_values[0]}")
print(f"  K[24] = {zone1_k_values[24]}")

# ===== Zone 2+3: Midtone-Highlight (24-255) - 均等補間 =====
print("\n[Step 2] Zone 2+3 (Midtone-Highlight 24-255) - 均等補間")

k_start = 4148
k_end = 29400  # v14のInput 240の値 = 和紙での紙白到達点
steps = 255 - 24  # 231 steps

zone23_k_values = []
for i in range(1, steps + 1):
    k = round(k_start + (k_end - k_start) * i / steps)
    zone23_k_values.append(k)

gradient_zone23 = (k_end - k_start) / steps

print(f"✓ Zone 2+3完成: {len(zone23_k_values)} values")
print(f"  K[25] = {zone23_k_values[0]}")
print(f"  K[255] = {zone23_k_values[-1]}")
print(f"  勾配: {gradient_zone23:.1f} K/step")

# ===== 全K-values結合 =====
k_values = zone1_k_values + zone23_k_values

# ===== 基本検証（ルール6: 単調増加） =====
print("\n[Step 3] 基本検証")
print(f"Total: {len(k_values)} values")
print(f"K[0]: {k_values[0]}")
print(f"K[24]: {k_values[24]}")
print(f"K[128]: {k_values[128]}")
print(f"K[192]: {k_values[192]}")
print(f"K[240]: {k_values[240]}")
print(f"K[248]: {k_values[248]}")
print(f"K[255]: {k_values[255]}")

assert len(k_values) == 256, f"K-values count error: {len(k_values)}"
assert k_values[0] == 0
assert k_values[24] == 4148
assert k_values[255] == 29400

# 単調増加チェック（ルール6）
print("\n[Step 4] 単調増加保証（ルール6）")
violations = 0
for i in range(1, 256):
    if k_values[i] <= k_values[i-1]:
        violations += 1
        print(f"⚠️  Input {i}: K={k_values[i]} <= K[{i-1}]={k_values[i-1]}")
        k_values[i] = k_values[i-1] + 1

if violations == 0:
    print("✓ 単調増加保証: 完璧")
else:
    print(f"✓ 単調増加保証: {violations}箇所を修正")

# ===== 勾配分析 =====
print("\n[Step 5] 勾配分析")
gradients = np.diff(k_values)
zone1_grad = gradients[0:24].mean()
zone23_grad = gradients[24:255].mean()
gradient_ratio = zone1_grad / zone23_grad

print(f"Zone 1 (0-24):     {zone1_grad:.1f} K/step")
print(f"Zone 2+3 (24-255): {zone23_grad:.1f} K/step")
print(f"勾配比 (Zone1/Zone23): {gradient_ratio:.2f}")

if gradient_ratio <= 2.0:
    print(f"✓ 勾配比{gradient_ratio:.2f}は理想範囲(≤2.0)内です")
elif gradient_ratio <= 2.5:
    print(f"⚠️  勾配比{gradient_ratio:.2f}がやや高いですが許容範囲です")
else:
    print(f"❌ 勾配比{gradient_ratio:.2f}が許容範囲を超えています")

# ===== バンディングリスク解析（ルール7） =====
print("\n[Step 6] バンディングリスク解析（ルール7）")

def analyze_banding_risk(k_vals, threshold=200):
    """バンディングリスクを解析"""
    risks = []
    for inp in range(1, 256):
        diff = k_vals[inp] - k_vals[inp-1]
        if abs(diff) > threshold:
            risks.append((inp, diff))
    return risks

risks = analyze_banding_risk(k_values)
if len(risks) == 0:
    print("✓ バンディングリスク: なし（全域で勾配差 < 200）")
else:
    print(f"⚠️  バンディングリスク: {len(risks)}箇所")
    for inp, diff in risks[:5]:  # 最初の5箇所のみ表示
        print(f"  Input {inp}: Δ={diff}")

# ===== v14との比較 =====
v14_k_values = {
    0: 0, 8: 1383, 16: 2765, 24: 4148, 32: 5068, 40: 5988, 48: 6908, 56: 7828,
    64: 8748, 72: 9668, 80: 10588, 88: 11508, 96: 12428, 104: 13348, 112: 14268, 120: 15188,
    128: 16108, 136: 17028, 144: 17948, 152: 18868, 160: 19788, 168: 20708, 176: 21628, 184: 22548,
    192: 23468, 200: 24388, 208: 25308, 216: 26228, 224: 27148, 232: 28068, 240: 29400, 248: 31900, 255: 33800
}

print(f"\n[Step 7] v14との比較")
print(f"Input | v14    | v14-washi | 差分    | 差分%")
print(f"------|--------|-----------|---------|-------")

for inp in [0, 24, 32, 64, 104, 128, 176, 192, 232, 240, 248, 255]:
    v14_k = v14_k_values[inp]
    washi_k = k_values[inp]
    diff = washi_k - v14_k
    diff_percent = (diff / v14_k * 100) if v14_k > 0 else 0.0
    print(f"{inp:5} | {v14_k:6} | {washi_k:9} | {diff:+7} | {diff_percent:+6.2f}%")

# ===== グラフ生成（ルール5） =====
print(f"\n[Step 8] 比較グラフを生成中（ルール5）...")

fig, axes = plt.subplots(3, 1, figsize=(12, 10))
fig.suptitle('PX1V-PtPd-xf1-v14-washi vs v14 比較', fontsize=16, fontweight='bold')

inputs = np.arange(256)
v14_k_full = [v14_k_values.get(i, np.interp(i, list(v14_k_values.keys()), list(v14_k_values.values()))) for i in range(256)]

# グラフ1: K値の比較
ax1 = axes[0]
ax1.plot(inputs, v14_k_full, 'b-', linewidth=2, label='v14 (original)', alpha=0.7)
ax1.plot(inputs, k_values, 'r-', linewidth=2, label='v14-washi (和紙専用)')
ax1.axvline(x=24, color='green', linestyle='--', alpha=0.5, label='Zone境界 (24)')
ax1.axvline(x=240, color='orange', linestyle='--', alpha=0.5, label='和紙紙白点 (240)')
ax1.set_xlabel('Input Value (0-255)')
ax1.set_ylabel('K Value (0-65535)')
ax1.set_title('K値比較: v14 vs v14-washi')
ax1.legend()
ax1.grid(True, alpha=0.3)

# グラフ2: K値の差分
ax2 = axes[1]
k_diff = np.array(k_values) - np.array(v14_k_full)
ax2.plot(inputs, k_diff, 'purple', linewidth=2)
ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax2.axvline(x=24, color='green', linestyle='--', alpha=0.5)
ax2.axvline(x=240, color='orange', linestyle='--', alpha=0.5)
ax2.fill_between(inputs, 0, k_diff, where=(k_diff<0), alpha=0.3, color='blue', label='ネガが濃くなる')
ax2.set_xlabel('Input Value (0-255)')
ax2.set_ylabel('K Value差分 (washi - v14)')
ax2.set_title('K値差分: 負の値 = ネガが濃くなる = より多くの階調')
ax2.legend()
ax2.grid(True, alpha=0.3)

# グラフ3: 勾配比較（バンディングリスク）
ax3 = axes[2]
gradients_v14 = np.diff(v14_k_full)
gradients_washi = np.diff(k_values)
ax3.plot(inputs[1:], gradients_v14, 'b-', linewidth=1, label='v14 勾配', alpha=0.7)
ax3.plot(inputs[1:], gradients_washi, 'r-', linewidth=2, label='v14-washi 勾配')
ax3.axhline(y=200, color='red', linestyle='--', alpha=0.5, label='バンディング閾値 (±200)')
ax3.axhline(y=-200, color='red', linestyle='--', alpha=0.5)
ax3.axvline(x=24, color='green', linestyle='--', alpha=0.5)
ax3.axvline(x=240, color='orange', linestyle='--', alpha=0.5)
ax3.set_xlabel('Input Value (0-255)')
ax3.set_ylabel('勾配 (ΔK/ΔInput)')
ax3.set_title('勾配比較（バンディングリスク評価）')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.set_ylim(-50, 300)

plt.tight_layout()
output_png = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v14_washi_comparison.png'
plt.savefig(output_png, dpi=150, bbox_inches='tight')
print(f"✓ グラフ保存: {output_png}")

# ===== .quadファイル生成（ルール2: 10チャンネル構造） =====
print(f"\n[Step 9] Quadファイルを出力中（ルール2: 10チャンネル構造）...")

quad_content = """## QuadToneRIP K,C,M,Y,LC,LM,LK,LLK,V,MK
# QuadProfile Version 2.8.0
# Title: PX1V-PtPd-xf1-v14-washi
# Printer: EPSON Stylus Pro 3880
# PPD: EPSON Stylus Pro 3880
# - Base: v14 Shadow (0-24) + 均等補間 (24-255)
# - 和紙専用カーブ: Input 240-255の階調表現問題を解決
# - Shadow (0-24): 172.8 K/step (v14と同じ)
# - Midtone-Highlight (24-255): 109.3 K/step (均等補間)
# - K_max: 29400 (v14のInput 240 = 和紙での紙白到達点)
# - 勾配比: 1.58 (理想的)
# - Target: 和紙でInput 240-255の階調を表現可能にする
# - Exposure: 7.0-7.5min推奨 (v14より延長、ネガが濃くなるため)
# Generated: 2026-04-01 by Claude Code
# QTR作業ルールブック準拠

# 2026 Daisuke Kinoshita
# BOOST_K=0 - NO BOOST
#
# K curve
"""

for k in k_values:
    quad_content += f"{k}\n"

quad_content += "#\n"

# 残り9チャンネル（全て0）- ルール2準拠
for channel in ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']:
    quad_content += f"# {channel} curve\n"
    for _ in range(256):
        quad_content += "0\n"
    quad_content += "#\n"

# 保存
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v14-washi.quad'
with open(output_path, 'w') as f:
    f.write(quad_content)

print(f"✓ v14-washiカーブ生成完了: {output_path}")

# ===== ファイル整合性確認 =====
print(f"\n[Step 10] ファイル整合性確認")
import os
file_size = os.path.getsize(output_path)
with open(output_path, 'r') as f:
    line_count = len(f.readlines())

print(f"ファイルサイズ: {file_size} bytes")
print(f"総行数: {line_count} 行（期待値: 2570-2582行）")

if 2570 <= line_count <= 2582:
    print("✓ 総行数: OK")
else:
    print(f"❌ 総行数エラー: {line_count}行（2570-2582行であるべき）")

# チャンネルコメント行確認
import subprocess
result = subprocess.run(['grep', '# .* curve', output_path], capture_output=True, text=True)
channel_lines = result.stdout.strip().split('\n')
print(f"チャンネル数: {len(channel_lines)}（期待値: 10）")
if len(channel_lines) == 10:
    print("✓ 10チャンネル構造: OK")
else:
    print(f"❌ チャンネル数エラー")

# ===== まとめ =====
print(f"\n{'=' * 80}")
print(f"v14-washi 設計コンセプト")
print(f"{'=' * 80}")
print(f"\n【問題】")
print(f"  v14では和紙でInput 240-255が表現できない")
print(f"  → Input 240（K=29400）が紙白になってしまう")
print(f"\n【解決策】")
print(f"  K_maxを29400に設定し、ネガをより濃くする")
print(f"  Shadow（0-24）はv14と同じで維持")
print(f"  Midtone-Highlight（24-255）を均等補間")
print(f"\n【特徴】")
print(f"  ✓ Shadow階調: v14と同じ（最適化済み）")
print(f"  ✓ 勾配比: 1.58（理想的）")
print(f"  ✓ バンディング: なし（均一勾配）")
print(f"  ✓ 和紙240-255: 階調表現可能に")
print(f"\n【推奨露光時間】")
print(f"  v14: 6.75分 → v14-washi: 7.0-7.5分")
print(f"  （ネガが濃くなるため延長が必要）")
print(f"\n【次のステップ】")
print(f"1. グラフを確認してカーブ形状を評価: open {output_png}")
print(f"2. 問題なければQTRプリンタにインストール（ルール8準拠）")
print(f"3. テストプリント（露光時間7.0分から開始）")
print(f"{'=' * 80}")
