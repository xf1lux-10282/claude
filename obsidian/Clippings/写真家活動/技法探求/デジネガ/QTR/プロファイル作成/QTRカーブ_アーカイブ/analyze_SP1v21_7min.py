#!/usr/bin/env python3
"""
SP1v21 7分露光データの分析
- 8分15秒との比較
- ハイライト階調の復活確認
- Input 128ミッドトーンの検証
- 最適ネガ濃度の提案
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Hiragino Sans'

# データ読み込み
data_7m = pd.read_csv('measurement_QTR-SP-21-7m.csv', comment='#')
data_8m15s = pd.read_csv('measurement_QTR-SP-21_8m15s_overexposed.csv', comment='#')

# カラム名を統一
data_7m.columns = ['input', 'neg_t', 'print_r']
data_8m15s.columns = ['input', 'neg_t', 'print_r']

print("=" * 80)
print("SP1v21 7分露光データ分析")
print("=" * 80)

# 1. Dmax/Dmin/濃度範囲の確認
print("\n【1. プリント濃度範囲の確認】")
print("-" * 60)

dmax_7m = data_7m['print_r'].max()
dmin_7m = data_7m['print_r'].min()
range_7m = dmax_7m - dmin_7m

dmax_8m15s = data_8m15s['print_r'].max()
dmin_8m15s = data_8m15s['print_r'].min()
range_8m15s = dmax_8m15s - dmin_8m15s

print(f"\n7分露光:")
print(f"  Dmax (最大濃度): {dmax_7m:.2f}D  (Input {data_7m.loc[data_7m['print_r'].idxmax(), 'input']:.0f})")
print(f"  Dmin (最小濃度): {dmin_7m:.2f}D  (Input {data_7m.loc[data_7m['print_r'].idxmin(), 'input']:.0f})")
print(f"  濃度範囲:        {range_7m:.2f}D")

print(f"\n8分15秒露光（参考）:")
print(f"  Dmax (最大濃度): {dmax_8m15s:.2f}D  (Input {data_8m15s.loc[data_8m15s['print_r'].idxmax(), 'input']:.0f})")
print(f"  Dmin (最小濃度): {dmin_8m15s:.2f}D  (Input {data_8m15s.loc[data_8m15s['print_r'].idxmin(), 'input']:.0f})")
print(f"  濃度範囲:        {range_8m15s:.2f}D")

print(f"\n露光時間補正の効果:")
print(f"  Dmax差分:   {dmax_7m - dmax_8m15s:+.2f}D  (7分 - 8分15秒)")
print(f"  Dmin差分:   {dmin_7m - dmin_8m15s:+.2f}D")
print(f"  範囲差分:   {range_7m - range_8m15s:+.2f}D")

# 2. Input 128ミッドトーンの検証
print("\n【2. Input 128（ミッドトーン）の検証】")
print("-" * 60)

input_128_7m = data_7m.loc[data_7m['input'] == 128, 'print_r'].values[0]
input_128_8m15s = data_8m15s.loc[data_8m15s['input'] == 128, 'print_r'].values[0]

# 理論的なミッドトーン（50%濃度）
theoretical_midtone_7m = dmin_7m + (range_7m * 0.5)

print(f"\n7分露光:")
print(f"  Input 128実測値:     {input_128_7m:.2f}D")
print(f"  理論値（Dmin+範囲×0.5）: {theoretical_midtone_7m:.2f}D")
print(f"  差分:               {input_128_7m - theoretical_midtone_7m:+.2f}D")

if abs(input_128_7m - theoretical_midtone_7m) <= 0.05:
    print(f"  ✅ 判定: 理論値に近い（±0.05D以内）")
elif input_128_7m < theoretical_midtone_7m:
    print(f"  ⚠️  判定: 理論値より低い（軟調気味）")
else:
    print(f"  ⚠️  判定: 理論値より高い（硬調気味）")

print(f"\n8分15秒露光（参考）:")
print(f"  Input 128実測値: {input_128_8m15s:.2f}D")
print(f"  7分との差分:     {input_128_7m - input_128_8m15s:+.2f}D")

# ユーザー目標範囲との比較
target_min = 0.70
target_max = 0.76
print(f"\nユーザー目標範囲: {target_min:.2f}D - {target_max:.2f}D")
if target_min <= input_128_7m <= target_max:
    print(f"  ✅ Input 128は目標範囲内です！")
else:
    if input_128_7m < target_min:
        print(f"  ⚠️  Input 128は目標より低い（{input_128_7m - target_min:.2f}D低い）")
    else:
        print(f"  ⚠️  Input 128は目標より高い（{input_128_7m - target_max:.2f}D高い）")

# 3. ハイライト階調（Input 0-32）の復活確認
print("\n【3. ハイライト階調（Input 0-32）の復活確認】")
print("-" * 60)

highlight_7m = data_7m[data_7m['input'] <= 32].copy()
highlight_8m15s = data_8m15s[data_8m15s['input'] <= 32].copy()

# 濃度差の計算
highlight_7m['density_diff'] = -highlight_7m['print_r'].diff(-1)
highlight_8m15s['density_diff'] = -highlight_8m15s['print_r'].diff(-1)

print("\n7分露光（Input 0-32）:")
print(f"{'Input':<8} {'プリント濃度':<15} {'次との濃度差':<15} {'判定'}")
print("-" * 60)
for idx, row in highlight_7m.iterrows():
    diff = row['density_diff'] if not pd.isna(row['density_diff']) else 0
    status = "✓" if diff >= 0.01 else "⚠️" if diff > 0 else "❌"
    print(f"{row['input']:<8.0f} {row['print_r']:<15.2f} {diff:<15.3f} {status}")

total_range_7m = highlight_7m['print_r'].max() - highlight_7m['print_r'].min()
print(f"\nInput 0-32の濃度範囲: {total_range_7m:.2f}D")

if total_range_7m >= 0.2:
    print(f"✅ 判定: ハイライト階調が復活（0.2D以上の差）")
else:
    print(f"⚠️  判定: ハイライト階調がまだ不足（目標0.2D、実測{total_range_7m:.2f}D）")

print("\n8分15秒露光（参考）:")
total_range_8m15s = highlight_8m15s['print_r'].max() - highlight_8m15s['print_r'].min()
print(f"Input 0-32の濃度範囲: {total_range_8m15s:.2f}D")
print(f"7分との差分: {total_range_7m - total_range_8m15s:+.2f}D")

# 4. 全体の濃度カーブ分析
print("\n【4. 全体の濃度カーブ分析】")
print("-" * 60)

# 濃度勾配の計算
data_7m['density_gradient'] = -data_7m['print_r'].diff(-1) / 8  # 8 input刻み

# 急激な変化の検出
steep_changes = data_7m[data_7m['density_gradient'] > 0.015]
if len(steep_changes) > 0:
    print("\n急激な濃度変化（勾配>0.015D/input）:")
    for idx, row in steep_changes.iterrows():
        print(f"  Input {row['input']:.0f}: 勾配 {row['density_gradient']:.4f}D/input")
else:
    print("\n✅ 急激な濃度変化なし（滑らかなカーブ）")

# 濃度逆転の検出
reversed_density = []
for i in range(len(data_7m) - 1):
    if data_7m.iloc[i]['print_r'] < data_7m.iloc[i+1]['print_r']:
        reversed_density.append((data_7m.iloc[i]['input'], data_7m.iloc[i+1]['input']))

if len(reversed_density) > 0:
    print("\n⚠️  濃度逆転検出:")
    for start, end in reversed_density:
        print(f"  Input {start:.0f} → {end:.0f}")
else:
    print("\n✅ 濃度逆転なし（単調減少）")

# 5. 最適ネガ濃度の提案
print("\n【5. 最適ネガ濃度の提案】")
print("-" * 60)

# Input 128が目標範囲（0.70-0.76D）になるために必要なネガ濃度調整
target_midtone = (target_min + target_max) / 2  # 0.73D
current_midtone = input_128_7m

needed_adjustment = target_midtone - current_midtone

print(f"\nInput 128の現状:")
print(f"  実測値: {current_midtone:.2f}D")
print(f"  目標値: {target_midtone:.2f}D")
print(f"  必要な調整: {needed_adjustment:+.2f}D")

if abs(needed_adjustment) <= 0.03:
    print(f"\n✅ 判定: SP1v21で十分（±0.03D以内）")
    print(f"   → 現在のネガ濃度カーブを採用できます")
else:
    # ネガ濃度の調整量を推定
    # 簡易的な線形近似: プリント濃度 1D変化にネガ濃度約0.5D変化が必要
    neg_adjustment = needed_adjustment * 0.5

    print(f"\n⚠️  判定: ネガ濃度調整が必要")
    print(f"   → プリント濃度を{needed_adjustment:+.2f}D変化させるには")
    print(f"   → ネガ濃度を約{neg_adjustment:+.2f}D調整")

    current_neg_128 = data_7m.loc[data_7m['input'] == 128, 'neg_t'].values[0]
    target_neg_128 = current_neg_128 + neg_adjustment

    print(f"\nInput 128のネガ濃度:")
    print(f"  現在: {current_neg_128:.2f}D（透過）")
    print(f"  目標: {target_neg_128:.2f}D（透過）")
    print(f"\n→ SP1v22カーブでInput 128付近を調整")

# グラフ作成
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# グラフ1: 7分 vs 8分15秒の比較
ax1 = axes[0, 0]
ax1.plot(data_7m['input'], data_7m['print_r'], 'o-', label='7分露光', linewidth=2, markersize=6)
ax1.plot(data_8m15s['input'], data_8m15s['print_r'], 's--', label='8分15秒露光', linewidth=2, markersize=6, alpha=0.7)
ax1.axhline(y=dmax_7m, color='red', linestyle=':', alpha=0.5, label=f'7分 Dmax={dmax_7m:.2f}D')
ax1.axhline(y=dmin_7m, color='blue', linestyle=':', alpha=0.5, label=f'7分 Dmin={dmin_7m:.2f}D')
ax1.set_xlabel('Input値', fontsize=12)
ax1.set_ylabel('プリント濃度（反射）', fontsize=12)
ax1.set_title('露光時間による濃度変化', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.invert_yaxis()

# グラフ2: ハイライト詳細（Input 0-64）
ax2 = axes[0, 1]
highlight_detail_7m = data_7m[data_7m['input'] <= 64]
highlight_detail_8m15s = data_8m15s[data_8m15s['input'] <= 64]
ax2.plot(highlight_detail_7m['input'], highlight_detail_7m['print_r'], 'o-', label='7分露光', linewidth=2, markersize=8)
ax2.plot(highlight_detail_8m15s['input'], highlight_detail_8m15s['print_r'], 's--', label='8分15秒露光', linewidth=2, markersize=8, alpha=0.7)
ax2.set_xlabel('Input値', fontsize=12)
ax2.set_ylabel('プリント濃度（反射）', fontsize=12)
ax2.set_title('ハイライト階調詳細（Input 0-64）', fontsize=14, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.invert_yaxis()

# グラフ3: Input 128ミッドトーン
ax3 = axes[1, 0]
midtone_inputs = [112, 120, 128, 136, 144]
midtone_7m = data_7m[data_7m['input'].isin(midtone_inputs)]
ax3.bar(midtone_7m['input'], midtone_7m['print_r'], width=6, alpha=0.7, label='7分露光')
ax3.axhline(y=theoretical_midtone_7m, color='green', linestyle='--', linewidth=2, label=f'理論値={theoretical_midtone_7m:.2f}D')
ax3.axhspan(target_min, target_max, alpha=0.2, color='yellow', label=f'目標範囲={target_min:.2f}-{target_max:.2f}D')
ax3.axhline(y=input_128_7m, color='red', linestyle=':', linewidth=2, label=f'Input 128={input_128_7m:.2f}D')
ax3.set_xlabel('Input値', fontsize=12)
ax3.set_ylabel('プリント濃度（反射）', fontsize=12)
ax3.set_title('ミッドトーン範囲の濃度', fontsize=14, fontweight='bold')
ax3.legend(fontsize=10)
ax3.grid(True, alpha=0.3)
ax3.invert_yaxis()

# グラフ4: 濃度差分（7分 - 8分15秒）
ax4 = axes[1, 1]
merged = pd.merge(data_7m, data_8m15s, on='input', suffixes=('_7m', '_8m15s'))
merged['diff'] = merged['print_r_7m'] - merged['print_r_8m15s']
ax4.plot(merged['input'], merged['diff'], 'o-', linewidth=2, markersize=6, color='purple')
ax4.axhline(y=0, color='black', linestyle='-', linewidth=1)
ax4.fill_between(merged['input'], 0, merged['diff'], where=(merged['diff'] >= 0), alpha=0.3, color='blue', label='7分の方が薄い')
ax4.fill_between(merged['input'], 0, merged['diff'], where=(merged['diff'] < 0), alpha=0.3, color='red', label='7分の方が濃い')
ax4.set_xlabel('Input値', fontsize=12)
ax4.set_ylabel('濃度差（7分 - 8分15秒）', fontsize=12)
ax4.set_title('露光時間補正の効果', fontsize=14, fontweight='bold')
ax4.legend(fontsize=10)
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('SP1v21_7min_analysis.png', dpi=150, bbox_inches='tight')
print(f"\n✅ グラフ保存: SP1v21_7min_analysis.png")

# CSVレポート作成
report = pd.DataFrame({
    'input': data_7m['input'],
    'negative_transmission': data_7m['neg_t'],
    'print_reflection_7min': data_7m['print_r'],
    'print_reflection_8m15s': data_8m15s['print_r'],
    'difference_7m_minus_8m15s': merged['diff'],
    'density_gradient_7min': data_7m['density_gradient']
})

report.to_csv('SP1v21_7min_analysis.csv', index=False)
print(f"✅ CSVレポート保存: SP1v21_7min_analysis.csv")

print("\n" + "=" * 80)
print("分析完了")
print("=" * 80)
