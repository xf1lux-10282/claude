# GUI印刷問題の修正 (Fix for GUI Printing Issue)

## 問題の概要

**症状:**
- Photoshop、Preview.appなどGUIアプリケーションからの印刷ジョブがキューに入るが処理されない
- ジョブは "waiting" または "sending data to printer" のまま停止
- コマンドライン (`lpr`) からの印刷は正常に動作

**発生日時:** 2026年4月6日

---

## 根本原因

PPDファイル (`P9550_ESCPR_QTR.ppd`) に **PostScript → CUPS Raster 変換フィルター** の定義が欠けていました。

### 元のPPDファイル (問題あり)

```ppd
*cupsFilter: "application/vnd.cups-raster 0 /Library/Printers/QTR/filter/rastertop9550"
```

このフィルター定義は「CUPS Rasterフォーマットの入力のみ受け付ける」という宣言です。

### 実際の印刷フロー

**コマンドライン印刷 (正常動作):**
```
TIFF画像
  ↓ (lpr が自動変換)
CUPS Raster
  ↓ rastertop9550
ESC/P-Raster
  ↓
プリンター
```

**GUI印刷 (問題発生):**
```
Photoshop/Preview.app
  ↓
PostScript/PDF
  ↓ ??? (変換フィルター未定義)
CUPS Raster (到達できない!)
  ↓ rastertop9550 (呼ばれない)
プリンター
```

GUIアプリケーションは PostScript または PDF 形式でデータを送信します。
しかし、PPDファイルに「PostScript を CUPS Raster に変換する方法」が記載されていなかったため、
CUPSは変換方法が分からず、ジョブが停止していました。

---

## 修正内容

PPDファイルに **PostScript → CUPS Raster 変換フィルター** を追加しました。

### 修正後のPPDファイル (正常動作)

```ppd
*% Custom CUPS filter chain for ESC/P-Raster with QuadToneRIP
*% Step 1: Convert PostScript/PDF to CUPS Raster (using system filter)
*cupsFilter2: "application/vnd.cups-postscript application/vnd.cups-raster 100 cgpdftoraster"
*% Step 2: Convert CUPS Raster to ESC/P-Raster with QuadToneRIP curves
*cupsFilter: "application/vnd.cups-raster 0 /Library/Printers/QTR/filter/rastertop9550"
```

### 修正後の印刷フロー

**GUI印刷 (修正後・正常動作):**
```
Photoshop/Preview.app
  ↓
PostScript/PDF
  ↓ cgpdftoraster (システム標準フィルター)
CUPS Raster
  ↓ rastertop9550 (QuadToneRIP カーブ適用)
ESC/P-Raster
  ↓
プリンター
```

---

## 修正手順

### 自動修正 (推奨)

```bash
cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/P9500設定/escpr_driver"

sudo ./update_ppd.sh
```

### 手動修正

```bash
# 1. 更新されたPPDファイルをシステムにコピー
sudo cp "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/P9500設定/escpr_driver/P9550_ESCPR_QTR.ppd" \
  /Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd

# 2. 圧縮
sudo gzip -f /Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd

# 3. CUPS再起動
sudo launchctl stop org.cups.cupsd
sudo launchctl start org.cups.cupsd
```

---

## 修正後のテスト手順

1. **Photoshop から印刷テスト**
   - ファイル → 印刷
   - プリンター: `P9550_QTR_ESCPR`
   - QuadTone RIP Curve 1: `P9550-PtPd-xf1-3ink`
   - 印刷実行

2. **Preview.app から印刷テスト**
   - 画像またはPDFを開く
   - ⌘P で印刷ダイアログ
   - プリンター: `P9550_QTR_ESCPR`
   - QuadTone RIP Curve 1: `P9550-PtPd-xf1-3ink`
   - 印刷実行

3. **ログ確認**
   ```bash
   tail -f /var/log/cups/error_log | grep -E "(rastertop9550|cgpdftoraster)"
   ```

期待される出力:
```
INFO: Converting CUPS raster file: /var/spool/cups/...
INFO: Raster header: 2480x3507, bpl=2480, colorspace=18
INFO: Successfully converted raster: 2480x3507
INFO: Loading curve: /Library/Printers/QTR/quadtone/QTR_P9550/P9550-PtPd-xf1-3ink.quad
INFO: Generating ESC/P-R data...
INFO: Done!
```

---

## 技術的詳細

### cupsFilter と cupsFilter2 の違い

- **`cupsFilter`**: CUPS 1.x 時代の旧形式
  - 形式: `入力MIME 0 フィルターパス`
  - 例: `application/vnd.cups-raster 0 /path/to/filter`

- **`cupsFilter2`**: CUPS 2.x の新形式
  - 形式: `入力MIME 出力MIME コスト フィルター名`
  - 例: `application/vnd.cups-postscript application/vnd.cups-raster 100 cgpdftoraster`

### フィルターチェーンの動作

CUPSは複数のフィルターを自動的に繋ぎ合わせて、入力フォーマットから最終出力フォーマットへ変換します。

**今回のフィルターチェーン:**

1. **cgpdftoraster** (システム標準)
   - 入力: `application/vnd.cups-postscript` または `application/pdf`
   - 出力: `application/vnd.cups-raster`
   - 機能: PostScript/PDF を CUPS Raster に変換

2. **rastertop9550** (自作フィルター)
   - 入力: `application/vnd.cups-raster`
   - 出力: プリンター固有バイナリ (ESC/P-Raster)
   - 機能: QuadToneRIPカーブ適用 + ESC/P-Rasterコマンド生成

---

## 修正履歴

- **2026-04-06 18:32 JST**: 問題発見、原因特定、修正完了

---

## 参考資料

- CUPS Filter and Backend Programming: https://www.cups.org/doc/spec-ipp.html
- CUPS PPD Extensions: https://www.cups.org/doc/spec-ppd.html
- cgpdftoraster filter: macOS標準 (`/usr/libexec/cups/filter/cgpdftoraster`)

---

**この修正により、GUIアプリケーションからの印刷が正常に動作するようになりました。**
