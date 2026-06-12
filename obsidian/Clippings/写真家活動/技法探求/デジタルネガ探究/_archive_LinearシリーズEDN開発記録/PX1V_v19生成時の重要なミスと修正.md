# PX1V v19生成時の重要なミスと修正

## 日付
2026年03月16日

## 問題の概要
v19カーブファイル生成時に、Input 255の値が間違っていたため、実測濃度が目標値より高くなっていた。

---

## 発生したミス

### 1. np.arange(256) vs np.linspace(0, 255, 256)の混同

**誤った生成方法:**
```python
input_vals = np.arange(256)  # 0, 1, 2, ..., 255
input_255_scale = input_vals * (255 / 256)  # 最後の値が254.00390625
```

**問題点:**
- `np.arange(256)`は0から255まで256個の整数を生成
- `* (255 / 256)`でスケールすると、最後の値が255ではなく254.00390625になる
- そのため、Input 255に対応する値がInput 254の値になっていた

**正しい生成方法:**
```python
input_indices = np.arange(256)  # 0, 1, 2, ..., 255（そのまま）
dens = np.interp(input_indices, anchor_inputs, anchor_dens)
```
または
```python
input_vals = np.linspace(0, 255, 256)  # 0から255まで256ポイント均等分割
```

---

### 2. ファイル構造の誤解（257ポイント vs 256ポイント）

**誤解:**
- QTRは257ポイント（Input 0-256）が必要だと思い込んでいた
- `np.arange(257)`で257個の値を生成していた

**実際:**
- v18を調査した結果、256ポイント（Input 0-255）が正しい
- `.quad`ファイル構造:
  - 行7: `# K curve`
  - 行8-263: 256個の値（Input 0-255）
  - 行264: `# C curve`

---

### 3. エンコーディングの問題（UTF-8 vs ASCII）

**問題:**
- 最初のPythonスクリプトがUTF-8で`.quad`ファイルを書き込んでいた
- QTRはASCII textを期待している可能性がある
- v18: `ASCII text`
- 最初のv19: `Unicode text, UTF-8 text`

**解決方法:**
```python
# バイナリモードでASCIIとして書き込み
with open('PX1V-PtPd-v19.quad', 'wb') as f:
    f.write(output_text.encode('ascii'))
```

---

## 実測値の比較

### 誤ったv19（Input 255 = 40484）
- 計算上の濃度: 1.24D
- 実測濃度: 1.30D（目標1.26Dより+0.04D高い）

### 修正後のv19（Input 255 = 40584）
- 計算上の濃度: 1.26D
- 期待される実測濃度: 1.26D付近

---

## 正しい生成方法（確定版）

```python
import numpy as np

BASELINE_SLOPE = 0.007387
BASELINE_INTERCEPT = 0.0935

def density_to_baseline(d):
    return max(0.0, min(65535.0, (d - BASELINE_INTERCEPT) / BASELINE_SLOPE))

def baseline_to_quad(b):
    return int(round(min(65535, max(0, b * 257))))

# アンカーポイント定義
v19_anchors = {
    0: 0.07, 8: 0.08, 16: 0.13, ..., 255: 1.26
}

anchor_inputs = np.array(sorted(v19_anchors.keys()))
anchor_dens = np.array([v19_anchors[i] for i in anchor_inputs])

# 重要: Input 0-255の256ポイントを直接生成
input_indices = np.arange(256)  # 0, 1, 2, ..., 255
dens = np.interp(input_indices, anchor_inputs, anchor_dens)

baselines = [density_to_baseline(d) for d in dens]
quads = [baseline_to_quad(b) for b in baselines]

# 単調性保証
quads_mono = [quads[0]]
for i in range(1, len(quads)):
    quads_mono.append(max(quads[i], quads_mono[i-1]))

# v18構造を完全コピーして、Kチャンネルのみ置き換え
# （詳細は別セッション参照）
```

---

## 検証方法

### 1. ファイル構造の確認
```bash
# 行数確認（2576行であること）
wc -l PX1V-PtPd-v19.quad

# エンコーディング確認（ASCII textであること）
file PX1V-PtPd-v19.quad

# Kチャンネルのポイント数確認（256であること）
sed -n '8,263p' PX1V-PtPd-v19.quad | wc -l
```

### 2. Input 255の値確認
```bash
# 行263がInput 255の値（40584であること）
sed -n '263p' PX1V-PtPd-v19.quad
```

### 3. C-MKチャンネルの確認
```bash
# v18と完全一致すること
diff <(sed -n '264,$p' PX1V-PtPd-Linear-v18.quad) \
     <(sed -n '264,$p' PX1V-PtPd-v19.quad)
```

---

## 教訓

1. **アンカーポイントの範囲と生成ポイント数を一致させる**
   - アンカーポイントが0-255なら、`np.arange(256)`で0-255を生成
   - スケール変換（`* 255/256`）は不要

2. **既存の動作しているファイルの構造を完全に踏襲する**
   - v18が256ポイントで動作しているなら、v19も256ポイント
   - 行数、エンコーディング、チャンネル構造をすべて一致させる

3. **エンコーディングに注意**
   - QTR用ファイルはASCII textで統一
   - Pythonで書き込む際は`encode('ascii')`を明示

4. **検証を段階的に行う**
   - ファイル構造の検証 → 値の検証 → 実測での検証
   - 各段階でv18との比較を行う

---

## 関連ファイル
- 正しいv19: `/Users/daisukekinoshita/Desktop/PX1V-PtPd-v19.quad`
- 参照したv18: `/Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-Linear-v18.quad`

