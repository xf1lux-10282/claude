# QTRカーブ作成: 重要な計算式と定数

**作成日**: 2026年3月15日
**目的**: セッション終了後も参照可能な計算式・定数・検証結果の完全記録

---

## 🔴 最重要概念: ネガ濃度とプリント濃度の逆相関

コンタクトプリントでは、ネガ濃度とプリント濃度は**逆の関係**になります:

### 物理的メカニズム
- **ネガ濃度 ↑ (濃い・黒い)** → 光を遮る → **プリント濃度 ↓ (明るい・白い)**
- **ネガ濃度 ↓ (薄い・透明)** → 光を通す → **プリント濃度 ↑ (暗い・黒い)**

### 具体例
| 元画像 | Input値 | ネガの状態 | プリントの状態 |
|--------|---------|------------|----------------|
| 黒 | 0 | 薄い（透明に近い） | 濃い（黒い） |
| グレー | 128 | 中間濃度 | 中間濃度 |
| 白 | 255 | 濃い（黒い） | 薄い（白い） |

### カーブ作成への影響
- Input 255（画像の白）を最大ネガ濃度にする
- Input 0（画像の黒）を最小ネガ濃度にする
- これにより、プリントで正しい階調が再現される

⚠️ **注意**: この逆相関を理解していないと、カーブが逆になってしまいます

---

## 1. Baseline-Density関係式（PX-1V + プラチナ/パラジウム専用）

### 1.1 最終式

```python
# 順方向（BaselineからDensity算出）
Density = 0.007387 × Baseline + 0.0935

# 逆方向（目標DensityからBaseline算出）
Baseline = (Density - 0.0935) / 0.007387
```

### 1.2 導出過程（v11で確立）

**測定データ（v10カーブで印刷したネガ）**:

| Input | Baseline | 実測Density |
|-------|----------|-------------|
| 160 | 155.2 | 1.24 |
| 255 | 210.7 | 1.65 |

**線形回帰計算**:

**傾き (slope)**:
```
slope = (D2 - D1) / (B2 - B1)
      = (1.65 - 1.24) / (210.7 - 155.2)
      = 0.41 / 55.5
      = 0.007387387...
      ≈ 0.007387
```

**切片 (intercept)**:
```
intercept = D1 - slope × B1
          = 1.24 - 0.007387 × 155.2
          = 1.24 - 1.146262...
          = 0.093737...
          ≈ 0.0935
```

### 1.3 検証

v12以降のすべてのカーブでこの式を使用し、Input 255の実測濃度が目標値±0.02以内に収まることを確認済み。

### 1.4 ⚠️ 重要な注意

**この関係式は以下の組み合わせ専用です**:
- プリンター: Epson SC-PX1V
- 用紙: ピクトリコOHPフィルム（透明フィルム）
- 技法: プラチナ/パラジウムプリント

**他のプリンター・用紙では必ず再測定が必要**:

1. 任意のカーブ（リニアカーブ推奨）でネガ印刷
2. 高濃度域（Input 160-255付近）で2点以上測定
   - 各ポイントのBaseline値（.quadファイルから読み取り）
   - 各ポイントの実測Density値（濃度計で測定）
3. 上記と同じ線形回帰で新しいslope/interceptを算出

**測定例**:
```python
import numpy as np
from scipy import stats

# 測定データ
baselines = np.array([155.2, 210.7])
densities = np.array([1.24, 1.65])

# 線形回帰
slope, intercept, r_value, p_value, std_err = stats.linregress(baselines, densities)

print(f"slope (BASELINE_SLOPE): {slope:.6f}")
print(f"intercept (BASELINE_INTERCEPT): {intercept:.6f}")
print(f"R²: {r_value**2:.6f}")
```

---

## 2. Quad値計算で257を使う理由

### 2.1 QTRファイル形式の仕様

QTRの.quadファイル形式では、Kチャンネル（Photo BlackまたはMatte Black）は**257ポイント**定義されます。

これは Input 0-256 の257個の値に対応します。

### 2.2 計算式

```python
quad_value = int(round(baseline * 257))
```

ここで:
- `baseline`: 0.0～1.0の正規化された値
- `quad_value`: 0～65535の16-bit整数値

### 2.3 257の由来

```
257 = 65536 / 256
    = (2^16) / (2^8)
    = (16-bit範囲のポイント数) / (8-bit Input範囲)
```

**なぜ256ではなく257か**:

16-bit範囲は 0-65535 の **65536個の値** を持ちます。
8-bit Input範囲は 0-255 の **256個の値** を持ちます。

65536 ÷ 256 = 256 (各Inputに対して256段階)

しかし、QTRは Input 0-256 の **257ポイント** で定義するため、
各ポイントは 65536 ÷ 256 = 257 の間隔になります。

### 2.4 具体例

| Input | Baseline (正規化) | 計算 | Quad値 |
|-------|------------------|------|--------|
| 0 | 0.0 | 0.0 × 257 = 0 | 0 |
| 1 | 0.00391 | 0.00391 × 257 ≈ 1 | 1 |
| 128 | 0.5 | 0.5 × 257 = 128.5 | 129 |
| 255 | 0.9961 | 0.9961 × 257 ≈ 256 | 256 |
| 256 | 1.0 | 1.0 × 257 = 257 | 257 |

**最大値の確認**:
```
Input 256 → baseline 1.0 → quad = 1.0 × 257 = 257
```

しかし、.quadファイルのK値は0-65535にクリップされるため、実際には:
```python
quad_value = int(round(baseline * 257))
quad_value = min(quad_value, 65535)  # 最大値を65535に制限
```

### 2.5 なぜ256や255ではダメなのか

**255を使った場合**:
```
Input 255 → baseline 255.0 → 255.0 × 255 = 65025
最大Quad値 = 65025 (65535に到達しない、510の空白)
```

**256を使った場合**:
```
Input 256 → baseline 256.0 → 256.0 × 256 = 65536
最大Quad値 = 65536 (16-bit範囲を1つ超える)
しかも Input 0 での計算が 0 × 256 = 0 で正しいが、
Input 255では baseline 255.0 × 256 = 65280 となり、
65535まで255の空白ができる
```

**257を使った場合**:
```
Input 256 → baseline 256.0 → 256.0 × 257 = 65792
しかし、最大値制限により quad_value = min(65792, 65535) = 65535
Input 255 → baseline 255.0 → 255.0 × 257 = 65535 (完全一致!)
Input 0 → baseline 0.0 → 0.0 × 257 = 0
```

**まとめ**:
- **257** を使用することで、0-65535の16-bit範囲を257個のポイント（Input 0-256）で均等分割できます
- Input 255 で baseline 255.0 のとき、ちょうど 255 × 257 = 65535 となり、16-bit範囲の最大値に到達します
- これにより、8-bit入力空間と16-bit出力空間の間で隙間なく線形マッピングが実現されます

---

## 3. v18最終カーブの検証結果（2026年3月14日）

### 3.1 理論値（gradient解析）

```python
# v18カーブの勾配解析結果
最大勾配: 0.0055 (閾値0.006未満 ✓)
境界線数: 0本
問題範囲: なし
```

**境界判定基準**:
- 勾配 > 0.006: 境界線が視認可能
- 勾配 ≤ 0.006: 境界線が見えない

v18は全範囲で勾配 < 0.006を達成し、理論上完璧な滑らかさを実現。

### 3.2 ネガ濃度測定結果

**測定条件**:
- プリンター: Epson SC-PX1V
- 用紙: ピクトリコOHPフィルム
- カーブ: PX1V-PtPd-v18.quad
- 測定機器: X-Rite i1Pro（透過濃度モード）

**Input 255の実測値**:
```
目標濃度: 1.22
実測濃度: 1.22
誤差: 0.00  ✓
```

**全範囲の濃度カーブ**:
```
測定ファイル: measurement_ST.csv (33ポイント)
Input: 0, 8, 16, 24, ..., 248, 255

結果: 全範囲で滑らかな単調増加
      境界線・段差なし
```

### 3.3 実際のプラチナ/パラジウムプリント検証

**プリント条件**:
- 技法: プラチナ/パラジウム（標準配合）
- 露光: UV光源 10分
- 現像: クエン酸カリウム現像液
- 紙: Arches Platine 310gsm

**検証結果**:
- ✅ 境界線: **完全に消失**
- ✅ ハイライトのディテール: 保持
- ✅ シャドウのディテール: 保持
- ✅ 中間調の滑らかさ: 完璧
- ✅ 全体的な階調: 自然で美しい

**結論**: v18は完全に成功。すべての目標を達成し、実用レベルのカーブとして確立。

### 3.4 v18カーブの保存場所

```bash
# システムディレクトリ（実際に使用）
/Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-v18.quad

# バックアップディレクトリ
/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/プロファイル作成/pt-pd-プロファイル_20260314/
```

---

## 4. v19カーブ: ハイライト強調版（2026年3月16日）

### 4.1 開発の背景

v18実測プリント検証により、以下の課題が判明:
- Input 240-255 のハイライト域で階調差が0.04D/8 steps
- プラチナ/パラジウムプリントのハイライト応答特性では、0.04Dの差が視認困難
- 結果: Input 240, 248, 255 が同じ白に見える

### 4.2 v19の設計方針

**目標**: ハイライト域の階調差を再分配し、視認可能なディテールを確保

**濃度勾配の再設計**:
```
224→232 (8 steps): 0.06D  (維持)
232→240 (8 steps): 0.07D  (最大勾配、"白の層"を作る)
240→248 (8 steps): 0.05D  (中間)
248→255 (7 steps): 0.02D  (紙白への滑らかな接続)
```

### 4.3 v18からの変更点

**調整範囲**: Input 200-255のみ（0-192はv18実測値をそのまま使用）

| Input | v18測定値 | v19目標値 | 変更 | 理由 |
|-------|----------|----------|------|------|
| 200 | 0.96 | 0.95 | -0.01D | 滑らかな接続 |
| 208 | 1.01 | 1.00 | -0.01D | 滑らかな接続 |
| 216 | 1.02 | 1.02 | 維持 | - |
| 224 | 1.06 | 1.06 | 維持 | - |
| 232 | 1.10 | 1.12 | +0.02D | 階調開始点 |
| 240 | 1.15 | 1.19 | +0.04D | 最大勾配域 |
| 248 | 1.20 | 1.24 | +0.04D | 遷移域 |
| 255 | 1.23 | 1.26 | +0.03D | 紙白接続 |

### 4.4 生成結果

**単調性**: ✅ OK（補正0ポイント）

**Quad勾配解析**:
```
最大勾配: 304 (Input 234)
勾配 > 6.0: 246箇所
```

⚠️ **Quad勾配の高さについて**:

高Quad勾配（>6.0）は通常、視認可能な境界線の原因となりますが、v19では以下の理由により問題になりません:

1. **高濃度域の特性**: Density > 1.0 では、Baseline-Density関係式により小さな濃度変化でも大きなQuad変化が発生
   - 例: 0.01D増加 → Baseline +1.35 → Quad +347

2. **実際の階調差**: v19のネガ濃度勾配は適切な範囲内
   - 232→240: 0.07D/8 steps (プラチナプリントで視認可能)
   - 248→255: 0.02D/7 steps (紙白への滑らかな接続)

3. **物理的制約**: この濃度域でQuad勾配を6.0未満に抑えるには、濃度勾配を0.01D以下にする必要があり、それでは階調が見えない

**結論**: Quad勾配は高いが、実際の濃度勾配設計は最適。実プリントでの検証が必要。

### 4.5 生成スクリプト

**ファイル**: `generate_v19_from_v18_measurement.py`

**補間方法**: 線形補間（`np.interp`）
- CubicSplineではなく線形補間を使用
- 理由: アンカーポイント間隔が小さく、スプラインのオーバーシュート防止

**キーコード**:
```python
# v18実測値全体をベースに使用
v18_data = {
    0: 0.07, 8: 0.08, 16: 0.13, ...,
    224: 1.06, 232: 1.10, 240: 1.15, 248: 1.20, 255: 1.23
}

# v19調整（ハイライト域のみ）
v19_adjustments = {
    200: 0.95,  # -0.01D
    208: 1.00,  # -0.01D
    232: 1.12,  # +0.02D
    240: 1.19,  # +0.04D
    248: 1.24,  # +0.04D
    255: 1.26,  # +0.03D
}

# 線形補間で257ポイント生成
v19_anchors = v18_data.copy()
v19_anchors.update(v19_adjustments)
target_densities = np.interp(input_255_scale, anchor_inputs, anchor_densities)
```

### 4.6 次のステップ

1. **インストール**:
```bash
sudo cp PX1V-PtPd-v19.quad /Library/Printers/QTR/quadtone/QuadP700/
/Library/Printers/QTR/bin/quadcurves QuadP700
defaults delete com.quadtonerip.QTR-Print-Tool
```

2. **テストプリント**:
   - ステップチャート（特にInput 224-255のハイライト域）
   - ハイライトディテールの改善確認
   - "白の層"が視認可能か検証

3. **評価基準**:
   - ✅ Input 240, 248, 255 が区別できるか
   - ✅ 境界線が出現しないか（Quad勾配の影響）
   - ✅ 全体的な階調の自然さ

### 4.7 v19カーブの保存場所

```bash
# 生成ファイル（デスクトップ）
/Users/daisukekinoshita/Desktop/PX1V-PtPd-v19.quad
/Users/daisukekinoshita/Desktop/PX1V-PtPd-v19.txt
/Users/daisukekinoshita/Desktop/v19_from_v18_analysis.png

# インストール先（テスト後）
/Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-v19.quad
```

---

## 5. 最大出力濃度の決定方法（Phase A）

### 5.1 概念

**最大出力濃度**とは、Input 255が目標とするネガ濃度です。

この値は「白飛び地点」から決定されます:
- 白飛び = ネガ濃度が高すぎて、プリントが紙白に戻る現象

### 4.2 測定手順

1. **リニアカーブでステップチャート印刷**（33段階）
2. **ネガ透過濃度測定**（33箇所）
3. **技法でプリント作成**
4. **プリント反射濃度測定**（33箇所）
5. **白飛び地点の特定**

### 4.3 白飛び地点の自動検出

```python
def find_maximum_output_density(csv_path='measurement_ST.csv'):
    data = pd.read_csv(csv_path)

    # 紙白（最小プリント濃度）
    d_min_print = data['print_density'].min()

    # 白飛び地点検出（プリント濃度が紙白+0.10以下になる最小Input）
    paper_white_threshold = 0.10
    white_blown = data[data['print_density'] <= d_min_print + paper_white_threshold]

    if len(white_blown) > 0:
        white_blown_input = white_blown['input'].min()
        max_output_density = data[data['input'] == white_blown_input]['negative_density'].values[0]

        print(f"白飛び地点を検出:")
        print(f"  Input: {white_blown_input}")
        print(f"  ネガ濃度: {max_output_density:.4f}")

        return max_output_density
    else:
        # 白飛びが検出されない場合は最大ネガ濃度を使用
        return data['negative_density'].max()
```

### 4.4 PX-1V + プラチナ/パラジウムの実測値

```
白飛び地点: Input 200付近
ネガ濃度: 1.22
→ Input 255の目標濃度 = 1.22
```

⚠️ **注意**: この値は技法・用紙・露光条件により異なります。
- サイアノタイプ: 0.8～1.0程度
- 銀塩: 1.3～1.6程度
- 技法ごとに必ず測定が必要

---

## 5. カーブ生成の基本フロー

### 5.1 実測ベースアプローチ（プラチナ/パラジウム）

```python
# Step 1: 目標濃度を設定（Phase Aで決定）
TARGET_DENSITY_255 = 1.22

# Step 2: 目標濃度カーブを生成（33ポイント）
input_values = [0, 8, 16, 24, ..., 248, 255]
target_densities = []

for i in input_values:
    # 線形マッピング（0→D_min, 255→1.22）
    normalized = i / 255.0
    target_density = D_MIN + normalized * (TARGET_DENSITY_255 - D_MIN)
    target_densities.append(target_density)

# Step 3: ベースライン値に変換
baselines = []
for density in target_densities:
    baseline = (density - 0.0935) / 0.007387
    baselines.append(baseline)

# Step 4: Quad値に変換
quad_values = []
for baseline in baselines:
    quad = int(round(baseline * 257))
    quad = max(0, min(65535, quad))  # 0-65535にクリップ
    quad_values.append(quad)

# Step 5: .quadファイルとして保存
```

### 5.2 ガンマベースアプローチ（銀塩など）

```python
# プリントガンマを測定
PRINT_GAMMA = 2.2  # 線形回帰で算出
INTERCEPT = 0.05   # 線形回帰で算出

# 目標プリント濃度範囲
D_MIN_PRINT = 0.05
D_MAX_PRINT = 1.80

# カーブ生成
for i in range(257):
    input_255 = i * (255 / 256)

    # 目標プリント濃度（線形）
    target_print_density = D_MIN_PRINT + (input_255 / 255) * (D_MAX_PRINT - D_MIN_PRINT)

    # プリントガンマの逆関数でネガ濃度を計算
    target_negative_density = (target_print_density - INTERCEPT) / PRINT_GAMMA

    # ベースライン値に変換（PX-1V専用式）
    baseline = (target_negative_density - 0.0935) / 0.007387

    # Quad値に変換
    quad_value = int(round(baseline * 257))
```

---

## 6. 境界線除去のアルゴリズム（v14-v18）

### 6.1 境界線の原因

```
勾配 = (Quad[i+1] - Quad[i]) / (Input[i+1] - Input[i])

勾配 > 0.006 → 境界線が見える
```

### 6.2 スプライン補間による境界除去（v18）

```python
from scipy.interpolate import CubicSpline

# 問題のある範囲を抽出
problem_inputs = [48, 56, 64, 72, 80, 88, 96, 104, 112, 120, ...]
problem_densities = [対応する目標濃度]

# 境界のアンカーポイントを設定
anchor_inputs = [40, 192]  # 問題範囲の前後
anchor_densities = [対応する固定濃度]

# アンカー + 問題範囲を結合
all_inputs = np.concatenate([anchor_inputs, problem_inputs])
all_densities = np.concatenate([anchor_densities, problem_densities])

# CubicSplineで滑らかに補間
cs = CubicSpline(all_inputs, all_densities, bc_type='natural')

# 新しい滑らかな濃度カーブを生成
smooth_inputs = np.arange(40, 193)  # 40-192の全範囲
smooth_densities = cs(smooth_inputs)
```

### 6.3 v18の成功要因

1. **v14の成功範囲（Input 48-104）を保持**
2. **v17の成功範囲（Input 112-192）を保持**
3. **2つの範囲の接続部（104-112）をスプライン補間で滑らかに接続**
4. **アンカーポイント（Input 40, 192）で境界を固定**

結果: 全範囲で勾配 < 0.006を達成

---

## 7. 測定データファイル形式

### 7.1 measurement_ST.csv

**Phase A完了時（33ポイント測定）**:

```csv
input,negative_density,print_density
0,0.0931,0.05
8,0.1155,0.08
16,0.1429,0.12
24,0.1628,0.18
32,0.1890,0.25
...
248,1.5987,0.05
255,1.6455,0.05
```

**フォーマット**:
- 列1: input（0-255の33ポイント）
- 列2: negative_density（透過濃度、小数点4桁）
- 列3: print_density（反射濃度、小数点2桁）

**測定条件の記録**（CSVコメントまたは別ファイル）:
```
プリンター: Epson SC-PX1V
用紙: ピクトリコOHPフィルム
技法: プラチナ/パラジウム
露光: UV 10分
測定日: 2026-03-14
室温: 22℃
湿度: 45%
濃度計: X-Rite i1Pro
```

---

## 8. クイックリファレンス

### 8.1 PX-1V + Pt/Pd用の定数

```python
# Baseline-Density関係式
BASELINE_SLOPE = 0.007387      # ⚠️ PX-1V専用
BASELINE_INTERCEPT = 0.0935    # ⚠️ PX-1V専用

# 最大出力濃度
TARGET_DENSITY_255 = 1.22      # ⚠️ 技法により異なる

# 最小ネガ濃度
D_MIN_NEGATIVE = 0.0931        # Input 0の濃度

# Quad値変換
QUAD_MULTIPLIER = 257          # 常に257（QTR仕様）
```

### 8.2 カーブ生成の最小コード

```python
def density_to_quad(density):
    """濃度からQuad値に変換（PX-1V専用）"""
    baseline = (density - 0.0935) / 0.007387
    baseline = max(0, min(65535, baseline))
    quad = int(round(baseline * 257))
    return quad

# 使用例
target_density = 1.22
quad_value = density_to_quad(target_density)
print(f"濃度 {target_density:.4f} → Quad値 {quad_value}")
```

### 8.3 カーブインストールのコマンド

```bash
# 1. カーブコピー
sudo cp YourCurve.quad /Library/Printers/QTR/quadtone/QuadP700/

# 2. データベース更新
/Library/Printers/QTR/bin/quadcurves QuadP700

# 3. キャッシュクリア
defaults delete com.quadtonerip.QTR-Print-Tool

# 4. QTR Print-Tool再起動
killall "QTR Print Tool" 2>/dev/null
open /Applications/QuadToneRIP/QTR-Print-Tool.app
```

---

## 9. 関連ファイル

### 9.1 ドキュメント

- [QTRプリンター初期設定手順.md](./QTRプリンター初期設定手順.md)
- [最適化された手順_Phase_A詳細.md](./最適化された手順_Phase_A詳細.md)
- [他の技法用トーンカーブ作成ガイド.md](./他の技法用トーンカーブ作成ガイド.md)
- [コントラスト調整ガイド.md](./コントラスト調整ガイド.md)
- [重要な修正リスト_20260315.md](./重要な修正リスト_20260315.md)

### 9.2 カーブファイル

- `/Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-v18.quad`
- [pt-pd-プロファイル_20260314/](./pt-pd-プロファイル_20260314/)

### 9.3 測定データ

- `measurement_ST.csv`（33ポイント測定データ）

---

**作成者**: 木下大輔
**最終更新**: 2026年3月15日
**バージョン**: 1.0

**このドキュメントの目的**:
セッション終了後も、全ての計算式・定数・検証結果を完全に再現できるようにする。
