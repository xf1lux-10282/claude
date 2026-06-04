#!/usr/bin/env python3
"""
v22の詳細K値CSV生成
33ポイントのK値を含む完全な情報
"""
import csv

# v22のK値（33ポイント）
v22_k_values = [
    0, 2520, 2960, 3400, 4060, 4940, 5820, 6700, 7580, 8680, 9780,
    10880, 11980, 13080, 14180, 15280, 16380, 17480, 18580, 19680, 20780, 21880,
    22980, 24080, 25180, 26280, 27160, 27820, 28480, 29140, 29580, 30020, 30680
]

# v21のK値（参考用）
v21_k_values = [
    0, 2520, 2960, 3400, 4060, 4500, 5160, 6040, 7140, 8240, 9340,
    10440, 11540, 12640, 13740, 14840, 15940, 17040, 18140, 19240, 20340, 21440,
    22540, 23640, 24740, 25840, 26940, 27820, 28480, 29140, 29800, 30460, 31120
]

# Input値
inputs = [0] + list(range(8, 241, 8)) + [248, 255]

# CSV生成
csv_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/v22_k_values_detailed.csv'

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)

    # ヘッダー
    writer.writerow(['Input', 'V22_K', 'V21_K', 'Diff_v21', 'Note'])

    # データ
    for i in range(len(inputs)):
        inp = inputs[i]
        v22_k = v22_k_values[i]
        v21_k = v21_k_values[i]
        diff = v22_k - v21_k

        # 変更内容のメモ
        if diff == 0:
            note = "変更なし"
        elif diff > 0:
            note = f"深く（プリント浅く） +{diff}"
        else:
            note = f"浅く（プリント深く） {diff}"

        writer.writerow([inp, v22_k, v21_k, diff, note])

print(f"✓ v22詳細K値CSV生成完了: {csv_path}")
print(f"\n【v22 K値リスト（33ポイント）】")
print("Input | V22_K | V21_K | 差分")
print("------|-------|-------|------")
for i in range(len(inputs)):
    print(f"{inputs[i]:5} | {v22_k_values[i]:5} | {v21_k_values[i]:5} | {v22_k_values[i]-v21_k_values[i]:+5}")
