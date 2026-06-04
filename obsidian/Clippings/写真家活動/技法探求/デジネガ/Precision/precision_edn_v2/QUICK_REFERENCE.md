# Precision EDN v2 - クイックリファレンス

**後日すぐに使えるコマンド集**

---

## 🚀 起動（最短）

### Streamlit GUI版（推奨）

```bash
cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision_edn_v2" && streamlit run app.py
```

→ ブラウザで `http://localhost:8501`

---

## 📝 よく使うコマンド

### テンプレート作成

```bash
cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision_edn_v2"

python3 main.py --create-template
```

### LUT生成（CLI）

```bash
python3 main.py --input data/measurement_template.csv --output 出力名
```

### ヘルプ

```bash
python3 main.py --help
```

---

## 📁 重要なパス

### プログラムフォルダ

```
/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision_edn_v2
```

### Photoshopスクリプト

```
/Users/daisukekinoshita/Desktop/Create_33Step_Chart_with_CropMarks.jsx
```

### 出力先

```
precision_edn_v2/output/luts/*.cube
precision_edn_v2/output/graphs/analysis_curves.pdf
```

---

## ⚙️ プリンター設定

```
プリンタ: SC-PX1V
用紙設定: EPSON 写真用紙 <クリスピア>
カラー: カラー ✓
解像度: 5760x1440dpi
品質: レベル4
双方向印刷: OFF
カラーマッチング: なし

プリセット名: "Precision_EDN_v2_RGB_Color_Dmax2.1"
```

---

## 📊 測定の基準値

```
ネガDmin: 0.10
ネガDmax: 2.10
中間調: 入力128 → ネガ濃度0.70
プリントDmax: 2.1以上
```

---

## 🔄 ワークフロー（超簡易版）

### 測定フェーズ

```
チャート作成 → RGB変換 → 反転 → Color Blocker → 印刷
  ↓
ネガ濃度測定① → CSV入力
  ↓
プリント作成 → プリント濃度測定② → CSV追記
  ↓
Streamlit起動 → CSVアップロード → LUT生成
```

### 本番フェーズ

```
RAW現像（16bit RGB）
  ↓
Photoshop編集
  ↓
CUBE LUT適用
  ↓
反転 → Color Blocker → 印刷
  ↓
コンタクトプリント → 完成
```

---

## 🎯 Photoshop LUT適用

```
レイヤー > 新規調整レイヤー > カラールックアップ
  ↓
3DLUT ファイル: output/luts/[名前].cube
  ↓
読み込み → 適用
```

---

## 🛑 終了

### Streamlit終了

ターミナルで:
```
Ctrl + C
```

---

## 📚 ドキュメント

| ファイル | 用途 |
|---------|------|
| **START_HERE.md** | 完全マニュアル |
| **QUICK_REFERENCE.md** | このファイル（コマンド集） |
| **STREAMLIT_GUIDE.md** | GUI詳細ガイド |
| **WORKFLOW_RGB_ColorBlocker.md** | ワークフロー詳細 |

---

**Precision EDN v2 - Version 2.0**
**Created: 2026-03-09**
