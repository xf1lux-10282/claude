#!/usr/bin/env python3
"""
v24の詳細K値CSV生成
v20との比較を含む
"""
import csv

# v20のK値を読み込み
v20_k_path = '/tmp/v20_k_values.txt'
with open(v20_k_path, 'r') as f:
    v20_k_values = [int(line.strip()) for line in f.readlines()]

# v24のK値（248-255を再計算）
v24_k_values = v20_k_values[:249].copy()  # 0-248

# 248-255を均等8分割
k_248 = v20_k_values[248]  # 29028
k_255_new = 32820
step = (k_255_new - k_248) / 7

for i in range(1, 8):
    k_value = round(k_248 + step * i)
    v24_k_values.append(k_value)

# CSV生成（全256ポイント）
csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v24_all_k_values.csv'

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Input', 'V24_K', 'V20_K', 'Diff', 'Note'])

    for i in range(256):
        v24_k = v24_k_values[i]
        v20_k = v20_k_values[i]
        diff = v24_k - v20_k

        if i <= 248:
            note = "v20と同一"
        else:
            note = f"紙白補正 (+{diff/v20_k*100:.1f}%)"

        writer.writerow([i, v24_k, v20_k, diff, note])

print(f"✓ CSV生成完了: {csv_path}")

# 主要ポイントを表示
print("\n【v24 K値一覧（主要ポイント）】")
print("Input | V24_K | V20_K | 差分 | 備考")
print("------|-------|-------|------|------------------")
for i in [0, 8, 16, 32, 48, 72, 96, 128, 160, 192, 216, 232, 240, 248, 249, 250, 251, 252, 253, 254, 255]:
    v24_k = v24_k_values[i]
    v20_k = v20_k_values[i]
    diff = v24_k - v20_k
    if i <= 248:
        note = "v20同一"
    else:
        note = f"+{diff/v20_k*100:.1f}%"
    print(f"{i:5} | {v24_k:5} | {v20_k:5} | {diff:+4} | {note}")

# 248-255の詳細
print("\n【248-255の紙白補正詳細】")
print("Input | V24_K | V20_K | 差分 | 増加率 | ステップ幅")
print("------|-------|-------|------|--------|----------")
for i in range(248, 256):
    v24_k = v24_k_values[i]
    v20_k = v20_k_values[i]
    diff = v24_k - v20_k
    increase = diff / v20_k * 100 if v20_k > 0 else 0
    if i == 248:
        step_width = 0
    else:
        step_width = v24_k - v24_k_values[i-1]
    print(f"{i:5} | {v24_k:5} | {v20_k:5} | {diff:+4} | {increase:+6.1f}% | {step_width:10}")

print(f"\n平均ステップ幅（249-255）: {step:.1f}")
