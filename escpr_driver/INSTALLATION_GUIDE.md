# EPSON SC-P9550 ESC/P-Raster QuadToneRIP Driver
# インストールおよび使用ガイド

**バージョン:** 1.0
**対応プリンター:** EPSON SC-P9500 / SC-P9550
**対応OS:** macOS 10.15 (Catalina) 以降
**最終更新:** 2026年4月6日

---

## 📋 目次

1. [概要](#概要)
2. [システム要件](#システム要件)
3. [インストール](#インストール)
4. [使い方](#使い方)
5. [トラブルシューティング](#トラブルシューティング)
6. [アンインストール](#アンインストール)
7. [技術情報](#技術情報)

---

## 概要

このドライバーは、EPSON SC-P9500/P9550プリンターでQuadToneRIPカーブファイル（.quad）を使用したモノクロ印刷を可能にします。

### 主な機能

- ✅ QuadToneRIPカーブファイル（.quad）対応
- ✅ ESC/P-Rasterプロトコル対応（P9500/P9550ネイティブプロトコル）
- ✅ macOS標準印刷ダイアログから使用可能
- ✅ 複数の用紙サイズ対応（A4, A3, A3+, 11x17, 13x19など）
- ✅ 複数の解像度対応（360, 720, 1440, 2880 DPI）
- ✅ グレースケール印刷専用（デジタルネガ印刷に最適）

### 従来のQuadToneRIPとの違い

| 項目 | 従来のQuadToneRIP | このドライバー |
|------|-------------------|---------------|
| 対応プロトコル | ESC/P2（古い） | ESC/P-Raster（新しい） |
| 対応プリンター | P700等 | P9500/P9550 |
| 実装 | C言語（Gutenprint改造） | Python（独自実装） |
| カーブファイル | .quad | .quad（互換） |
| GUI | Print-Tool.app | macOS標準印刷ダイアログ |
| カスタマイズ | 困難 | 容易 |

---

## システム要件

### 必須要件

- macOS 10.15 (Catalina) 以降
- Python 3.7 以降
- EPSON SC-P9500 または SC-P9550 プリンター（USB または ネットワーク接続）
- 管理者権限

### 推奨要件

- macOS 12 (Monterey) 以降
- Python 3.9 以降
- USB接続（最も安定）

### Pythonライブラリ

インストールスクリプトが自動的にインストールします：

- Pillow (PIL) 8.0 以降
- NumPy 1.20 以降

---

## インストール

### Step 1: ダウンロード

プロジェクトファイルをダウンロードまたはクローン：

```bash
# 現在の場所（テスト版）
cd /tmp/escpr_driver

# 本番環境にコピー（推奨）
cp -r /tmp/escpr_driver ~/escpr_driver
cd ~/escpr_driver
```

### Step 2: ファイル確認

以下のファイルが存在することを確認：

```bash
ls -la
```

必要なファイル：
- `escpr_commands.py` - ESC/P-Rコマンド生成モジュール
- `escpr_driver.py` - ESCPRDriverクラス
- `quad_parser.py` - QuadToneRIPカーブパーサー
- `rastertop9550` - CUPSフィルター
- `P9550_ESCPR_QTR.ppd` - プリンター記述ファイル
- `install.sh` - インストールスクリプト

### Step 3: インストール実行

```bash
sudo ./install.sh
```

インストールスクリプトは以下を実行します：

1. ✅ 依存関係チェック（Python, Pillow, NumPy）
2. ✅ 必要なライブラリの自動インストール
3. ✅ ドライバーファイルを `/Library/Printers/QTR/escpr_driver/` にコピー
4. ✅ CUPSフィルターを `/Library/Printers/QTR/filter/` にコピー
5. ✅ PPDファイルを `/Library/Printers/PPDs/Contents/Resources/` にコピー
6. ✅ プリンターキュー登録（自動検出または手動入力）

### Step 4: インストール確認

```bash
lpstat -p P9550_QTR_ESCPR
```

期待される出力：
```
printer P9550_QTR_ESCPR is idle.  enabled since ...
```

---

## 使い方

### 方法1: macOS印刷ダイアログから印刷（推奨）

1. **アプリケーションから印刷を開始**
   - 任意のアプリケーション（Preview.app、Photoshop、Lightroom等）で印刷（⌘P）

2. **プリンター選択**
   - プリンター: `P9550_QTR_ESCPR` を選択

3. **QuadToneRIPカーブ選択**
   - 「詳細を表示」をクリック
   - 設定項目から「QuadTone RIP Curve 1」を探す
   - カーブを選択（例: `P9550-PtPd-xf1-3ink`）

4. **その他の設定**
   - **用紙サイズ**: A4, A3, 11x17, 13x19など
   - **解像度**: 720dpi（推奨）、1440dpi（高品質）、2880dpi（最高品質）
   - **メディアタイプ**: 使用する用紙に合わせて選択

5. **印刷実行**
   - 「印刷」ボタンをクリック

### 方法2: コマンドラインから印刷

```bash
# 画像ファイルを直接印刷
lpr -P P9550_QTR_ESCPR \
    -o ripCurve1=P9550-PtPd-xf1-3ink \
    -o media=A4 \
    -o Resolution=720dpi \
    /path/to/image.tiff

# PDFファイルを印刷
lpr -P P9550_QTR_ESCPR \
    -o ripCurve1=P9550-PtPd-xf1-3ink \
    /path/to/document.pdf
```

### オプション一覧

| オプション | 説明 | 例 |
|-----------|------|-----|
| `-P` | プリンター名 | `P9550_QTR_ESCPR` |
| `-o ripCurve1=` | QuadToneRIPカーブ | `P9550-PtPd-xf1-3ink` |
| `-o media=` | 用紙サイズ | `A4`, `A3`, `SuperB` |
| `-o Resolution=` | 解像度 | `720dpi`, `1440dpi`, `2880dpi` |
| `-o MediaType=` | 用紙種類 | `PlainPaper`, `PhotoPaper`, `MattePaper` |

### カーブファイルの追加

新しい.quadカーブファイルを追加する場合：

1. カーブファイルを `/Library/Printers/QTR/quadtone/QTR_P9550/` にコピー

```bash
sudo cp my_custom_curve.quad /Library/Printers/QTR/quadtone/QTR_P9550/
```

2. PPDファイルを編集してカーブを追加

```bash
sudo gunzip /Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd.gz

# PPDファイルを編集
sudo nano /Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd

# "ripCurve1" セクションに以下を追加:
# *ripCurve1 my_custom_curve/My Custom Curve: ""

# 再圧縮
sudo gzip /Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd
```

3. CUPSを再起動

```bash
sudo launchctl stop org.cups.cupsd
sudo launchctl start org.cups.cupsd
```

---

## トラブルシューティング

### 問題1: プリンターが印刷しない

**症状:** ジョブがキューに入るが印刷されない

**確認:**

```bash
# プリンター状態確認
lpstat -p P9550_QTR_ESCPR

# ジョブ確認
lpstat -o

# CUPSログ確認
tail -f /var/log/cups/error_log
```

**対処:**

1. プリンターがオンラインか確認
2. プリンターキューを有効化:
   ```bash
   sudo cupsenable P9550_QTR_ESCPR
   sudo cupsaccept P9550_QTR_ESCPR
   ```
3. ジョブを再送信

### 問題2: 「Filter failed」エラー

**症状:** CUPSログに「Filter failed」と表示

**原因:** Pythonモジュールまたはカーブファイルが見つからない

**確認:**

```bash
# フィルターファイル確認
ls -la /Library/Printers/QTR/filter/rastertop9550

# Pythonモジュール確認
ls -la /Library/Printers/QTR/escpr_driver/

# カーブファイル確認
ls -la /Library/Printers/QTR/quadtone/QTR_P9550/
```

**対処:**

```bash
# フィルターを手動テスト
/Library/Printers/QTR/filter/rastertop9550 123 user test 1 "" /tmp/test.pdf
```

### 問題3: カーブが適用されていない

**症状:** 印刷されるが意図したトーンカーブになっていない

**確認:**

1. PPDファイルでカーブ名が正しいか確認
2. カーブファイルが存在するか確認:
   ```bash
   ls /Library/Printers/QTR/quadtone/QTR_P9550/*.quad
   ```

**対処:**

1. カーブファイルの構文確認:
   ```bash
   python3 /Library/Printers/QTR/escpr_driver/quad_parser.py \
     /Library/Printers/QTR/quadtone/QTR_P9550/P9550-PtPd-xf1-3ink.quad
   ```

2. フォーマットが正しいことを確認（# K curve、256個の数値）

### 問題4: Permission denied

**症状:** フィルター実行時に権限エラー

**対処:**

```bash
# フィルターに実行権限を付与
sudo chmod +x /Library/Printers/QTR/filter/rastertop9550

# Pythonモジュールの読み取り権限確認
sudo chmod 644 /Library/Printers/QTR/escpr_driver/*.py
```

### 問題5: プリンターが検出されない

**症状:** インストール時にプリンターが自動検出されない

**対処:**

1. プリンターの電源とUSB/ネットワーク接続を確認
2. 手動でプリンターURIを取得:
   ```bash
   lpstat -v | grep SC-P9
   ```
3. 手動でキュー登録:
   ```bash
   sudo lpadmin -p P9550_QTR_ESCPR \
     -v 'usb://EPSON/SC-P9500%20Series?serial=XXXXXXXX' \
     -P /Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd.gz \
     -E
   ```

---

## アンインストール

### 完全アンインストール

```bash
# プリンターキュー削除
sudo lpadmin -x P9550_QTR_ESCPR

# ドライバーファイル削除
sudo rm -rf /Library/Printers/QTR/escpr_driver
sudo rm /Library/Printers/QTR/filter/rastertop9550
sudo rm /Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd.gz

# CUPSを再起動
sudo launchctl stop org.cups.cupsd
sudo launchctl start org.cups.cupsd
```

---

## 技術情報

### アーキテクチャ

```
macOS印刷ダイアログ
  ↓ PostScript/PDF
CUPS
  ↓ CUPS Raster
rastertop9550 (Python)
  ├─ quad_parser.py (QuadToneRIPカーブ適用)
  ├─ escpr_driver.py (ESC/P-Rasterコマンド生成)
  └─ escpr_commands.py (プロトコル実装)
  ↓ ESC/P-Raster Binary
EPSON SC-P9550
```

### ファイル配置

```
/Library/Printers/QTR/
├── escpr_driver/
│   ├── escpr_commands.py
│   ├── escpr_driver.py
│   └── quad_parser.py
├── filter/
│   └── rastertop9550
└── quadtone/
    └── QTR_P9550/
        └── *.quad

/Library/Printers/PPDs/Contents/Resources/
└── P9550_ESCPR_QTR.ppd.gz
```

### ESC/P-Rasterコマンドシーケンス

1. **初期化**: `ESC @`, `ESC ( R "REMOTE1"`, `ESC ( R "ESCPR"`
2. **ジョブ設定**: `ESC j "sets"` (用紙サイズ), `ESC q "setq"` (解像度)
3. **ページ開始**: `ESC p "strt"`
4. **データ送信**: `ESC d "dsnd"` (ラスターデータ)
5. **ページ終了**: `ESC p "endp"`
6. **ジョブ終了**: `ESC j "endj"`

### QuadToneRIPカーブファイル形式

```.quad
# コメント
# K curve
0
1
2
...
255
```

- 256個の値（0-255）
- K（黒）チャンネルのルックアップテーブル
- 入力値（画像の輝度）→ 出力値（プリンターへの値）

---

## サポート・コミュニティ

### バグ報告・機能要望

- プロジェクトページ: (TBD)
- メール: (TBD)

### 開発者向け情報

- ソースコード: `/tmp/escpr_driver/` (開発版)
- ライセンス: MIT License (予定)
- 貢献: Pull Requests歓迎

---

## 変更履歴

### Version 1.0 (2026-04-06)

- ✅ 初回リリース
- ✅ ESC/P-Rasterプロトコル基本実装
- ✅ QuadToneRIPカーブファイル統合
- ✅ CUPS統合
- ✅ macOS印刷ダイアログ対応
- ✅ 複数用紙サイズ・解像度対応

### 今後の予定

- ⏳ RLE圧縮実装（データサイズ削減）
- ⏳ カラー印刷対応
- ⏳ 高度なインク制御
- ⏳ Print-Tool.app統合

---

**製作者:** xf1lux
**テスト協力:** EPSON SC-P9550ユーザーコミュニティ
**謝辞:** EPSON, QuadToneRIP, epson-escpr project

---

**このドライバーでデジタルネガ印刷を楽しんでください！**
