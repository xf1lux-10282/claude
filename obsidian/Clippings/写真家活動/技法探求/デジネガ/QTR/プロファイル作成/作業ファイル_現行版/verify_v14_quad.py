#!/usr/bin/env python3
"""
PX1V-PtPd-xf1-v14.quad ファイルの検証
"""

# .quadファイル読み込み
quad_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/作業ファイル_現行版/PX1V-PtPd-xf1-v14.quad'

with open(quad_path, 'r') as f:
    lines = f.readlines()

# K-curve抽出
k_curve_start = None
k_curve_end = None

for i, line in enumerate(lines):
    if line.strip() == '# K curve':
        k_curve_start = i + 1
    elif k_curve_start is not None and line.strip() == '#':
        k_curve_end = i
        break

if k_curve_start is None or k_curve_end is None:
    print("❌ K-curveセクションが見つかりません")
    exit(1)

# K-values抽出
k_values = []
for i in range(k_curve_start, k_curve_end):
    line = lines[i].strip()
    if line:
        try:
            k = int(line)
            k_values.append(k)
        except ValueError:
            print(f"❌ 行{i+1}: 数値でない値 '{line}'")
            exit(1)

print("=== v14 .quadファイル検証 ===")
print(f"K-curve行: {k_curve_start+1} - {k_curve_end}")
print(f"K-values数: {len(k_values)}")

# 基本検証
if len(k_values) != 256:
    print(f"❌ K-values数エラー: {len(k_values)} (期待値: 256)")
    exit(1)
else:
    print("✓ K-values数: 256 (正常)")

if k_values[0] != 0:
    print(f"❌ K[0]エラー: {k_values[0]} (期待値: 0)")
    exit(1)
else:
    print("✓ K[0] = 0 (正常)")

if k_values[255] != 33800:
    print(f"❌ K[255]エラー: {k_values[255]} (期待値: 33800)")
    exit(1)
else:
    print("✓ K[255] = 33800 (正常)")

# 主要ポイント検証
expected_values = {
    24: 4148,
    128: 16108,
    240: 29400,
    248: 31900
}

print("\n=== 主要K-values検証 ===")
all_ok = True
for inp, expected in expected_values.items():
    actual = k_values[inp]
    if actual == expected:
        print(f"✓ K[{inp:3}] = {actual:5} (期待値: {expected})")
    else:
        print(f"❌ K[{inp:3}] = {actual:5} (期待値: {expected}, 差分: {actual - expected:+d})")
        all_ok = False

# 単調増加チェック
print("\n=== 単調増加チェック ===")
monotonic = True
for i in range(1, len(k_values)):
    if k_values[i] < k_values[i-1]:
        print(f"❌ Input {i-1}→{i}: {k_values[i-1]} → {k_values[i]} (減少)")
        monotonic = False
        break

if monotonic:
    print("✓ K-valuesは単調増加している (正常)")

# 他チャンネル検証
print("\n=== 他チャンネル検証 ===")
channels_to_check = ['C', 'M', 'Y', 'LC', 'LM', 'LK', 'LLK', 'V', 'MK']

for channel in channels_to_check:
    channel_start = None
    channel_end = None

    for i, line in enumerate(lines):
        if line.strip() == f'# {channel} curve':
            channel_start = i + 1
        elif channel_start is not None and line.strip() == '#':
            channel_end = i
            break

    if channel_start is None or channel_end is None:
        print(f"❌ {channel} curveセクションが見つかりません")
        continue

    channel_values = []
    for i in range(channel_start, channel_end):
        line = lines[i].strip()
        if line:
            try:
                v = int(line)
                channel_values.append(v)
            except ValueError:
                print(f"❌ {channel} curve 行{i+1}: 数値でない値 '{line}'")
                continue

    if len(channel_values) != 256:
        print(f"❌ {channel} curve: {len(channel_values)} values (期待値: 256)")
    elif all(v == 0 for v in channel_values):
        print(f"✓ {channel} curve: 256個の0 (正常)")
    else:
        non_zero_count = sum(1 for v in channel_values if v != 0)
        print(f"⚠️  {channel} curve: {non_zero_count}個の非ゼロ値")

# 最終判定
print("\n=== 最終判定 ===")
if all_ok and monotonic and len(k_values) == 256:
    print("✅ v14.quadファイルは正常です")
    print("   インストール可能です")
    exit(0)
else:
    print("❌ v14.quadファイルにエラーがあります")
    print("   修正が必要です")
    exit(1)
