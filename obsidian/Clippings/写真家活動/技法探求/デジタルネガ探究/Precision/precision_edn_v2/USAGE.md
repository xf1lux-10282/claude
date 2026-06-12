# Precision EDN v2 - 使用ガイド

---

## セットアップ

### 1. 必要なライブラリのインストール (完了済み)

```bash
pip3 install -r requirements.txt
```

✓ 完了

---

## ワークフロー

### Step 1: 33ステップチャートの印刷

#### チャート生成

デスクトップの **Photoshopスクリプト** を実行:

```
Create_33Step_Chart_with_CropMarks.jsx
```

1. Photoshopを開く
2. ファイル > スクリプト > 参照
3. スクリプトを選択
4. `Precision_EDN_v2_33step_chart_A4.tif` が生成される

#### 印刷設定 (重要!)

```
プリンター: EPSON PX-1V
用紙: ピクトリコOHP (TPS100)
用紙サイズ: A4

重要:
□ カラーマネジメント: OFF
□ ICCプロファイル: なし
□ 色補正: すべてOFF
□ PhotoEnhance: OFF
□ オートフォトファイン: OFF
```

**なぜ重要か**: すべての補正がONだと、測定データが無意味になります。

---

### Step 2: 測定① - ネガ濃度測定

#### 準備

1. 印刷したチャートを用意
2. 濃度計を透過濃度測定モードに設定
3. 測定データテンプレートを開く

```bash
cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision_edn_v2"
python3 main.py --create-template
```

生成されたファイル:
```
data/measurement_template.csv
```

#### 測定方法

1. **各パッチの中央を測定**
2. **3箇所測定して平均を取る** (推奨)
3. **特に入力128は正確に** (中間調の基準点)

#### データ入力

`data/measurement_template.csv` を開いて、`negative_density` 列に測定値を入力:

```csv
input,negative_density,print_density
0,1.55,
8,1.52,
16,1.47,
...
128,0.70,  ← 中間調 (重要)
...
255,0.10,
```

---

### Step 3: 測定② - プラチナプリント濃度測定

#### プリント作成

1. 測定①と **同じネガ** を使用
2. 和紙にコンタクトプリント
3. FO高濃度配合
4. **適正露光** (Dmaxが出る露光)
5. 標準現像プロトコル

#### 乾燥・測定

1. プリントを完全乾燥
2. 濃度計で各パッチの濃度を測定
3. 各ステップ3箇所測定して平均

#### データ入力

同じCSVファイルの `print_density` 列に入力:

```csv
input,negative_density,print_density
0,1.55,0.05
8,1.52,0.08
16,1.47,0.12
...
128,0.70,0.85  ← 中間調
...
255,0.10,2.10
```

---

### Step 4: 解析実行

#### プログラム実行

```bash
cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision_edn_v2"
python3 main.py --input data/measurement_template.csv
```

#### 出力されるファイル

```
output/
├── luts/
│   ├── precision_edn_v2.cube              # CUBE LUT
│   ├── precision_edn_v2_curve.csv         # 33点カーブデータ
│   ├── precision_edn_v2_photoshop_curve.txt  # Photoshop用
│   └── precision_edn_v2_report.txt        # 解析レポート
└── graphs/
    └── analysis_curves.pdf                # 解析グラフ
```

---

## 出力ファイルの使い方

### 1. CUBE LUT (推奨)

**Photoshop**:
1. カラールックアップレイヤーを作成
2. `precision_edn_v2.cube` を読み込み
3. 16bit TIFFで書き出し

**Lightroom**:
1. 現像モジュール > カラーグレーディング
2. LUTを適用

### 2. Photoshopトーンカーブ

`precision_edn_v2_photoshop_curve.txt` を開いて:

1. Photoshopでトーンカーブレイヤーを作成
2. 33点の制御点を手動で入力
3. 保存してプリセット化

### 3. グラフで確認

`graphs/analysis_curves.pdf` を開いて:

- **左**: 入力値 → ネガ濃度 (プリンター特性)
- **中**: ネガ濃度 → プリント濃度 (プラチナ特性)
- **右**: 入力値 → プリント濃度 (合成特性)

**確認ポイント**:
- 線形領域が緑でハイライトされているか
- 合成カーブが理想(リニア)に近いか
- 異常な点がないか

---

## トラブルシューティング

### エラー: "必須フィールドがありません"

→ CSVのヘッダーを確認:

```csv
input,negative_density,print_density
```

### 警告: "ネガDminが高い"

→ プリンター設定を確認:
- カラーマネジメントがONになっていないか
- インクが古くなっていないか

### 警告: "プリントDmaxが低い"

→ プラチナプリント条件を確認:
- FO濃度が適切か
- 露光時間が足りているか
- 現像時間が適切か

---

## コマンドリファレンス

### テンプレート作成

```bash
python3 main.py --create-template
```

### 解析実行

```bash
python3 main.py --input data/measurement.csv
```

### 出力先を指定

```bash
python3 main.py --input data/measurement.csv --output my_calibration
```

### グラフ生成をスキップ

```bash
python3 main.py --input data/measurement.csv --no-graphs
```

### 詳細出力

```bash
python3 main.py --input data/measurement.csv --verbose
```

### ヘルプ

```bash
python3 main.py --help
```

---

## 測定のベストプラクティス

### 濃度計の使い方

1. **校正**: 測定前に校正
2. **測定位置**: パッチの中央
3. **複数回測定**: 3箇所平均
4. **安定を待つ**: 値が安定してから記録

### 重要なポイント

| 入力値 | 意味 | 重要度 |
|--------|------|--------|
| 0 | Dmax (最大濃度) | ★★★ |
| 128 | 中間調 (基準点) | ★★★★★ |
| 255 | Dmin (最小濃度) | ★★★ |

### 測定環境

- 温度: 20〜25℃
- 湿度: 40〜60%
- 照明: 一定の条件
- プリント: 完全乾燥後

---

## 次のステップ

1. **グラフを確認** - 測定データの妥当性を確認
2. **LUTを適用** - テスト画像で試す
3. **テストプリント** - 実際にプリントして確認
4. **微調整** - 必要に応じてカーブを調整
5. **本番運用** - 作品制作に使用

---

## 参考資料

- [プラチナプリント×デジタルネガ設計_技術的総括.md](../obsidian/Clippings/写真家活動/技法探求/デジタルネガ探究/プラチナプリント×デジタルネガ設計_技術的総括.md)
- [Precision_EDN_Version2_設計書.md](../obsidian/Clippings/写真家活動/技法探求/デジタルネガ探究/Precision_EDN_Version2_設計書.md)

---

**作成**: 2026-03-09
**バージョン**: 2.0
