# Precision EDN v2 - スタートガイド

**作成日**: 2026-03-09
**後日使用するための完全マニュアル**

---

## 📋 目次

1. [すぐに始める](#すぐに始める)
2. [Streamlit GUI版（推奨）](#streamlit-gui版推奨)
3. [コマンドライン版](#コマンドライン版)
4. [完全ワークフロー](#完全ワークフロー)
5. [トラブルシューティング](#トラブルシューティング)

---

## すぐに始める

### 📍 このフォルダの場所

```bash
/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision_edn_v2
```

### ✅ インストール済み

- ✓ Python 3.13
- ✓ 必要なライブラリ（numpy, scipy, matplotlib, streamlit）
- ✓ プログラム一式
- ✓ Photoshopスクリプト（デスクトップ）

**すぐに使えます！**

---

## Streamlit GUI版（推奨）

### 🎨 特徴

- ✓ ブラウザで動作する視覚的なインターフェース
- ✓ ドラッグ&ドロップでCSVアップロード
- ✓ リアルタイムグラフ表示
- ✓ ワンクリックダウンロード

---

### 🚀 起動方法（3ステップ）

#### ステップ1: ターミナルを開く

**Finder** → **アプリケーション** → **ユーティリティ** → **ターミナル**

または

**Spotlight検索** (⌘+Space) → "ターミナル" と入力

#### ステップ2: フォルダに移動

ターミナルに以下をコピー&ペーストして Enter:

```bash
cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision_edn_v2"
```

#### ステップ3: 起動

以下をコピー&ペーストして Enter:

```bash
streamlit run app.py
```

**自動的にブラウザが開きます！**

もし開かない場合は、手動でブラウザを開いて:
```
http://localhost:8501
```

---

### 📱 GUI の使い方

#### 画面構成

```
┌─────────────────────────────────────────┐
│  🎨 Precision EDN v2                    │
├──────────┬──────────────────────────────┤
│サイドバー│ メインエリア（3タブ）          │
│          │                              │
│⚙️ 設定   │ 📁 データ入力                 │
│          │ 🚀 LUT生成                   │
│出力名    │ 📚 ドキュメント                │
│          │                              │
│パラメータ│                              │
│ヘルプ    │                              │
└──────────┴──────────────────────────────┘
```

#### 使用手順

**1. データ入力タブ**

**オプションA: テンプレート作成**
1. 「📝 テンプレートCSVを作成」ボタンをクリック
2. 「💾 テンプレートをダウンロード」でCSV保存
3. エクセル/テキストエディタで開く
4. 測定データを入力して保存

**オプションB: CSVアップロード**
1. 測定済みCSVファイルをドラッグ&ドロップ
2. または「Browse files」をクリックして選択

**データプレビュー**
- 自動的にデータ表示
- 統計情報表示
- データ検証（エラーチェック）

✓ 「データは正常です。LUT生成を実行できます」が表示されればOK

**2. LUT生成タブ**

1. サイドバーで出力名を設定（例: `precision_edn_v2_20260309`）
2. 「🚀 LUT生成を実行」ボタンをクリック
3. 処理中（自動）:
   ```
   📊 データを読み込み中...
   📈 カーブを解析中...
   🔄 逆カーブを生成中...
   💾 LUTをエクスポート中...
   📊 グラフを生成中...
   ✓ 完了！
   ```
4. 解析グラフが表示される
5. ダウンロードボタンが表示される:
   - 📥 **CUBE LUT** ← これをPhotoshopで使用
   - 📥 カーブCSV
   - 📥 レポート
   - 📥 解析グラフ (PDF)

**3. ドキュメントタブ**

使い方・ワークフロー・設計パラメータを確認できます。

---

### 🛑 終了方法

**ターミナルで**:
```
Ctrl + C
```

または

ブラウザタブを閉じるだけでもOK（バックグラウンドで動作継続）

完全終了する場合は必ず `Ctrl+C` をターミナルで実行。

---

## コマンドライン版

GUIを使わず、ターミナルで直接実行する方法。

### 📝 テンプレート作成

```bash
cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision_edn_v2"

python3 main.py --create-template
```

**出力**: `data/measurement_template.csv`

### 🚀 LUT生成

測定データを入力したCSVで:

```bash
python3 main.py --input data/measurement_template.csv
```

**出力先変更**:
```bash
python3 main.py --input data/measurement_template.csv --output my_calibration_name
```

**出力ファイル**:
- `output/luts/[名前].cube` ← CUBE LUT
- `output/luts/[名前]_curve.csv` ← カーブデータ
- `output/luts/[名前]_report.txt` ← レポート
- `output/graphs/analysis_curves.pdf` ← グラフ

### 📖 ヘルプ

```bash
python3 main.py --help
```

---

## 完全ワークフロー

### Phase 1: 測定用チャート作成

#### 1-1. Photoshopスクリプト実行

デスクトップにある:
```
Create_33Step_Chart_with_CropMarks.jsx
```

1. Photoshopを開く
2. **ファイル > スクリプト > 参照**
3. デスクトップのスクリプトを選択
4. 実行 → `Precision_EDN_v2_33step_chart_A4.tif` が生成される

#### 1-2. RGB変換・反転・Color Blocker

Photoshopで:
1. 生成されたチャートを開く
2. **イメージ > モード > RGBカラー**
   - カラープロファイル: Adobe RGB (1998)
   - 16bit/チャンネル維持
3. **イメージ > 色調補正 > 階調の反転**
4. **EDN Color Blocker適用**:
   - ウェブ: http://www.easydigitalnegatives.com/color-blocker/
   - または手動で黒枠追加
5. **別名で保存**: `measurement_chart_RGB_inverted_blocked.tif`
   - 形式: TIFF、圧縮なし、16bit RGB

#### 1-3. カラーモード印刷

**Photoshop プリント設定**:
```
ファイル > プリント

カラーマネジメント:
  カラー処理: プリンターによるカラー管理
  ドキュメント: Adobe RGB (1998)
```

**macOS プリント設定**:
```
プリンタ: SC-PX1V
用紙サイズ: A4

「詳細を表示」→「印刷設定」:
  用紙種類: EPSON 写真用紙 <クリスピア>
  カラー: カラー ✓
  解像度: 5760x1440dpi
  品質: レベル4（高精細）
  双方向印刷: OFF

「カラー・マッチング」:
  カラーマッチング: カラーマッチングなし ✓
```

**プリセット保存**:
```
プリセット: 「現在の設定をプリセットとして保存」
名前: "Precision_EDN_v2_RGB_Color_Dmax2.1"
```

印刷後、30分乾燥。

---

### Phase 2: 測定①（ネガ濃度）

#### 準備

1. 印刷したチャートを用意
2. 濃度計を**透過濃度測定モード**に設定
3. テンプレートCSV作成:
   ```bash
   cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision_edn_v2"
   python3 main.py --create-template
   ```
   または Streamlit GUI で作成

#### 測定方法

1. 各パッチの中央を測定
2. 各パッチ3箇所測定して平均（推奨）
3. 特に**入力128は正確に**（中間調の基準点）

#### データ入力

`data/measurement_template.csv` を開いて、`negative_density` 列に入力:

```csv
input,negative_density,print_density
0,2.10,
8,2.05,
16,1.98,
...
128,0.70,  ← 中間調（重要）
...
255,0.10,
```

**確認ポイント**:
- Dmin ≈ 0.10
- Dmax ≈ 2.10
- 入力128 → ネガ濃度 ≈ 0.70

---

### Phase 3: 測定②（プリント濃度）

#### プリント作成

1. 測定①と**同じネガ**を使用
2. 和紙にコンタクトプリント
3. FO高濃度配合
4. **適正露光**（Dmaxが出る露光）
5. 標準現像プロトコル
6. **完全乾燥**（24時間推奨）

#### 測定

1. 濃度計を**反射濃度モード**に設定
2. 33ステップ各パッチの濃度測定
3. 各パッチ3箇所測定して平均

#### データ入力

同じCSVの `print_density` 列に追記:

```csv
input,negative_density,print_density
0,2.10,0.05
8,2.05,0.08
...
128,0.70,0.85  ← 中間調
...
255,0.10,2.10
```

保存。

---

### Phase 4: LUT生成

#### Streamlit GUI版（推奨）

1. ターミナルで起動:
   ```bash
   cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision_edn_v2"
   streamlit run app.py
   ```
2. ブラウザで操作:
   - データ入力タブ → CSVアップロード
   - LUT生成タブ → 出力名設定 → LUT生成実行
   - CUBE LUTダウンロード

#### コマンドライン版

```bash
cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision_edn_v2"

python3 main.py --input data/measurement_template.csv --output precision_edn_v2_RGB_color_Dmax2.1
```

**出力確認**:
- `output/luts/precision_edn_v2_RGB_color_Dmax2.1.cube` ✓
- `output/graphs/analysis_curves.pdf` ✓

---

### Phase 5: 本番作品制作

#### 5-1. RAW現像

Lightroom/Camera Rawで:
- 基本補正（露出・コントラスト・シャドウ/ハイライトなど）
- 16bit TIFF書き出し:
  - カラースペース: Adobe RGB (1998)
  - ビット深度: 16bit/チャンネル

#### 5-2. Photoshopで編集

1. 書き出したTIFFを開く
2. 必要な編集:
   - トリミング
   - 覆い焼き・焼き込み
   - 部分調整
   - 最終コントラスト調整
3. **重要**: R=G=Bを維持（ニュートラルグレー）

#### 5-3. LUT適用

```
レイヤー > 新規調整レイヤー > カラールックアップ
↓
3DLUT ファイル:
  output/luts/precision_edn_v2_RGB_color_Dmax2.1.cube
↓
読み込み → 適用
```

**確認**:
```
情報パネルで数値確認:
  適用前: R=128, G=128, B=128
  適用後: R=65, G=65, B=65
  ↓
  R=G=B維持されている ✓
```

#### 5-4. 反転・Color Blocker

1. **レイヤー > 画像を統合**
2. **イメージ > 色調補正 > 階調の反転**
3. **EDN Color Blocker適用** または 手動で黒枠追加
4. 統合

#### 5-5. 保存・印刷

1. **別名で保存**:
   - 形式: TIFF、圧縮なし、16bit RGB
   - ファイル名: `[作品名]_negative_RGB_blocked.tif`

2. **印刷**:
   ```
   ファイル > プリント
   ↓
   プリセット選択:
     "Precision_EDN_v2_RGB_Color_Dmax2.1"
   ↓
   印刷実行
   ```

#### 5-6. コンタクトプリント

1. ネガ完成
2. 和紙にコンタクトプリント
3. 測定時と同じプロセス:
   - 同じFO濃度
   - 同じ露光時間
   - 同じ現像
4. プラチナプリント完成 ✓

---

## トラブルシューティング

### Streamlitが起動しない

**症状**: `streamlit: command not found`

**解決策**:
```bash
pip3 install streamlit
```

---

### ブラウザが開かない

**解決策**:
```
手動でブラウザを開く
→ http://localhost:8501
```

---

### CSVアップロードエラー

**症状**: 「必須列が不足」

**解決策**:
```csv
ヘッダーを確認:
input,negative_density,print_density
```

文字化けしていないか、カンマ区切りか確認。

---

### 色かぶりが発生

**原因**: RGB画像がニュートラルグレーでない

**対策**:
1. 情報パネルで確認: R=G=B か？
2. グレースケール変換してからRGB変換
3. チャンネルミキサーで調整

---

### Dmaxが2.1より低い

**原因**: レベル4でインク量不足

**対策**:
- レベル5を試す
- または印刷濃度を+1〜+2に

---

### Dmaxが2.3以上

**原因**: インク量過多

**対策**:
- レベル3に下げる
- または印刷濃度を-1〜-2に

---

## 📁 ファイル構成

```
precision_edn_v2/
├── START_HERE.md                     ← このファイル
├── app.py                            # Streamlit GUIアプリ
├── run_app.sh                        # 起動スクリプト
├── main.py                           # CLIプログラム
├── config.py                         # 設定ファイル
├── data_input.py                     # データ入力モジュール
├── curve_analyzer.py                 # カーブ解析モジュール
├── inverse_curve.py                  # 逆カーブ生成モジュール
├── lut_export.py                     # LUTエクスポートモジュール
├── requirements.txt                  # 依存ライブラリ
├── STREAMLIT_GUIDE.md                # GUI詳細ガイド
├── USAGE.md                          # CLI詳細ガイド
├── WORKFLOW_RGB_ColorBlocker.md      # ワークフロー詳細
├── README.md                         # プロジェクト概要
├── data/                             # 測定データ
│   └── measurement_template.csv
└── output/                           # 出力ファイル
    ├── luts/                         # LUTファイル
    │   ├── *.cube                    # CUBE LUT
    │   ├── *_curve.csv               # カーブデータ
    │   └── *_report.txt              # レポート
    └── graphs/                       # グラフ
        └── analysis_curves.pdf
```

---

## 📚 関連ドキュメント

| ファイル名 | 内容 |
|-----------|------|
| **START_HERE.md** | このファイル（クイックスタート） |
| **STREAMLIT_GUIDE.md** | GUI詳細ガイド |
| **WORKFLOW_RGB_ColorBlocker.md** | 完全ワークフロー |
| **USAGE.md** | CLI詳細ガイド |
| **README.md** | プロジェクト概要 |

---

## ⚙️ 設定まとめ

### Photoshop設定

```
カラースペース: Adobe RGB (1998)
ビット深度: 16bit/チャンネル
カラー処理: プリンターによるカラー管理
```

### プリンター設定

```
機種: EPSON SC-PX1V
用紙（物理）: ピクトリコOHP TPS-100
用紙設定: EPSON 写真用紙 <クリスピア>
カラー: カラー
解像度: 5760x1440dpi
品質: レベル4（高精細）
双方向印刷: OFF
カラーマッチング: なし
```

### Precision EDN v2 設定

```python
# config.py
PRINT_MODE = "Color"
NEGATIVE_GAMMA = 1.8
NEGATIVE_DMIN = 0.10
NEGATIVE_DMAX = 2.10
MIDTONE_INPUT = 128
MIDTONE_NEGATIVE_DENSITY = 0.70
```

---

## 🎯 次回使用時の手順

### 【最短ルート】

1. **ターミナルを開く**

2. **以下をコピー&ペースト**:
   ```bash
   cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision_edn_v2" && streamlit run app.py
   ```

3. **ブラウザで操作**:
   - CSVアップロード → LUT生成 → ダウンロード

---

## ✅ チェックリスト

### 測定前準備

- [ ] Photoshopスクリプトで33ステップチャート作成
- [ ] RGB変換（Adobe RGB 1998, 16bit）
- [ ] 階調の反転
- [ ] Color Blocker適用
- [ ] TIFF保存（16bit RGB）
- [ ] プリンター設定確認（カラー、クリスピア、レベル4）

### 測定①

- [ ] 濃度計を透過濃度モードに設定
- [ ] 33ステップ測定（各3箇所平均）
- [ ] 特に入力128を正確に
- [ ] CSVに入力
- [ ] Dmin ≈ 0.10, Dmax ≈ 2.10 確認

### 測定②

- [ ] 同じネガでプラチナプリント作成
- [ ] FO高濃度配合
- [ ] 適正露光
- [ ] 標準現像
- [ ] 完全乾燥（24時間）
- [ ] 濃度計を反射濃度モードに設定
- [ ] 33ステップ測定
- [ ] CSVに追記
- [ ] プリントDmax ≈ 2.1以上 確認

### LUT生成

- [ ] Streamlit起動
- [ ] CSVアップロード
- [ ] データ検証OK確認
- [ ] 出力名設定
- [ ] LUT生成実行
- [ ] グラフ確認（異常なし）
- [ ] CUBE LUTダウンロード

### 本番制作

- [ ] RAW現像（16bit RGB, Adobe RGB 1998）
- [ ] Photoshopで基本編集
- [ ] R=G=B維持確認
- [ ] カラールックアップでCUBE LUT適用
- [ ] 統合
- [ ] 階調の反転
- [ ] Color Blocker適用
- [ ] TIFF保存（16bit RGB）
- [ ] プリセットで印刷
- [ ] コンタクトプリント
- [ ] 完成 ✓

---

## 📞 サポート

問題が発生した場合:
1. このSTART_HERE.mdのトラブルシューティングを確認
2. STREAMLIT_GUIDE.mdの詳細ガイドを確認
3. ターミナルのエラーメッセージを確認
4. データCSVの形式を確認

---

**Precision EDN v2**
**Version**: 2.0
**Created**: 2026-03-09
**Workflow**: RGB + Color Blocker
**Dmax**: 2.10 (Color Mode)
**Printer**: PX-1V

**🎨 プラチナプリント用デジタルネガ キャリブレーション**
