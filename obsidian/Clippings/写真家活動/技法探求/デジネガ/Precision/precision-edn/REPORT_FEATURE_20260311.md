# Precision EDN - レポート機能追加

**追加日**: 2026-03-11
**バージョン**: 20260311q

---

## 📋 概要

測定結果と品質分析の包括的なレポート生成機能を追加しました。

---

## ✅ 追加機能

### 1. テキストレポート (.md)

**マークダウン形式**の詳細レポート:
- 測定ファイル情報
- 設定情報
- 品質スコア
- 測定サマリー
- 単調性チェック
- トーンジャンプ検出
- 問題領域
- 推奨事項
- ステップごとの誤差（上位10件）

### 2. HTMLレポート (.html)

**ビジュアルレポート**:
- 美しいレイアウト
- カラースコアカード
- テーブル表示
- 印刷対応
- レスポンシブデザイン

**今後の拡張予定**:
- グラフ画像の埋め込み
- Chart.jsグラフのPNG export

---

## 📁 追加ファイル

### 新規作成

1. **[js/report.js](file:///Users/daisukekinoshita/Library/Mobile%20Documents/iCloud~md~obsidian/Documents/precision-edn/js/report.js)**
   - `ReportGenerator` クラス
   - `generateTextReport()` - マークダウンレポート生成
   - `generateHTMLReport()` - HTMLレポート生成

### 修正ファイル

2. **[index.html](file:///Users/daisukekinoshita/Library/Mobile%20Documents/iCloud~md~obsidian/Documents/precision-edn/index.html)**
   - レポートダウンロードボタン追加（2種類）
   - `report.js` の読み込み
   - バージョンを `20260311q` に更新

3. **[js/ui.js](file:///Users/daisukekinoshita/Library/Mobile%20Documents/iCloud~md~obsidian/Documents/precision-edn/js/ui.js)**
   - `downloadReportText()` メソッド追加
   - `downloadReportHTML()` メソッド追加
   - `enableDownloadButtons()` にレポートボタン追加
   - `downloadAll()` にレポート含める

---

## 🎯 使い方

### レポートのダウンロード

1. **測定ファイルをアップロード**
2. **分析が完了**すると、レポートボタンが有効化
3. **2種類のレポート**から選択:
   - **📋 分析レポート (.md)**: マークダウン形式（Obsidian等で閲覧）
   - **📊 分析レポート (.html)**: HTML形式（ブラウザで閲覧）

### 一括ダウンロードに含まれるレポート

**📦 全ファイル一括ダウンロード (ZIP)** に自動的に含まれます:
- `Analysis_Report.md`
- `Analysis_Report.html`

---

## 📊 レポート内容の詳細

### テキストレポート (.md)

```markdown
# Precision EDN - 測定分析レポート

**生成日時**: 2026-03-11 05:30:00

---

## 📁 測定ファイル情報

**測定ファイル数**: 3枚

1. scan_001.png
2. scan_002.png
3. scan_003.png

## ⚙️ 設定情報

| 項目 | 値 |
|------|-----|
| **補正モード** | 1次補正 |
| **チャート種類** | EDN_256 |
| **サンプリングポイント** | 52点 |
...
```

### HTMLレポート (.html)

- **ヘッダー**: グラデーション背景、生成日時
- **品質スコアカード**: グリッド表示、大きな数値
- **測定サマリーテーブル**: 主要指標
- **推奨事項**: カラーボーダー
- **フッター**: バージョン情報

---

## 🔮 今後の拡張予定

### 1. グラフ画像の埋め込み

HTMLレポートにChart.jsグラフのPNG画像を埋め込む:

```javascript
// Chart.jsのcanvasからPNG export
const linearityChart = document.getElementById('linearityChart');
const linearityImage = linearityChart.toDataURL('image/png');

// HTMLレポートに埋め込み
<img src="${linearityImage}" alt="リニアリティ検証グラフ">
```

### 2. 詳細統計情報

- ヒストグラム
- 誤差分布グラフ
- 濃度カーブ比較

### 3. PDF出力

- jsPDFライブラリ使用
- 印刷用レイアウト
- 高品質グラフ画像

---

## ✅ 動作確認

- [x] テキストレポートダウンロード
- [x] HTMLレポートダウンロード
- [x] 一括ダウンロードにレポート含まれる
- [x] レポートボタンの有効化/無効化
- [ ] グラフ画像の埋め込み（今後）

---

**Precision EDN - レポート機能**
**追加日: 2026-03-11**
**バージョン: 20260311q**
