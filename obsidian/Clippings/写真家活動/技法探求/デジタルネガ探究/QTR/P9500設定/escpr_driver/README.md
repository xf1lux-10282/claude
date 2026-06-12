# ESC/P-R Python Driver for EPSON SC-P9500/P9550

QuadToneRIPカーブファイルを使用した、EPSON SC-P9500/P9550向けの最小限ESC/P-Rasterドライバー

**作成日:** 2026年4月6日
**バージョン:** 0.1.0 (実験的)
**ライセンス:** 実装参考元のepson-escpr-improvedに準拠（GPL-2.0想定）

---

## 概要

このドライバーは、EPSON SC-P9500/P9550プリンター向けにESC/P-Rasterプロトコルを実装し、QuadToneRIPのカーブファイル（.quad）を使用したデジタルネガ印刷を可能にします。

### 特徴

- ✅ ESC/P-Rasterプロトコルの基本実装
- ✅ QuadToneRIP .quadカーブファイル対応
- ✅ Python実装で読みやすく拡張しやすい
- ✅ TIFF/PNG/JPEG等の画像フォーマット対応
- ⚠️ **実験的実装** - コマンドパラメータは暫定版

### 非対応機能

- ❌ RLE圧縮（非圧縮のみ）
- ❌ カラー印刷（グレースケールのみ）
- ❌ 双方向通信・ステータス取得
- ❌ エラーリカバリ

---

## インストール

### 必要なソフトウェア

- Python 3.6以上
- PIL/Pillow
- numpy

```bash
pip3 install pillow numpy
```

### ファイル構成

```
/tmp/escpr_driver/
├── README.md                    # このファイル
├── ESCPR_DRIVER_COMPLETE.md     # 完成報告書
├── TESTING_GUIDE.md             # 実機テストガイド
├── escpr_commands.py            # ESC/P-Rコマンド生成
├── escpr_driver.py              # ESCPRDriverクラス
├── quad_parser.py               # QuadToneRIPカーブ解析
└── test_print_image.py          # メインスクリプト
```

---

## 使い方

### 基本的な使用例

```bash
# TIFFファイルをQuadToneRIPカーブ適用して変換
python3 test_print_image.py \
  input.tiff \
  /Library/Printers/QTR/quadtone/QTR_P9550/P9550-PtPd-xf1-3ink.quad \
  -o output.bin

# 生成されたバイナリをプリンターに送信（USB）
sudo cat output.bin > /dev/usb/lp0
```

### オプション指定

```bash
# 解像度指定（デフォルト: 720x720）
python3 test_print_image.py input.tiff curve.quad -o output.bin \
  --dpi 2880x1440

# 用紙サイズ指定（デフォルト: 210x297 = A4）
python3 test_print_image.py input.tiff curve.quad -o output.bin \
  --paper 210x297

# 標準出力に出力（パイプ経由）
python3 test_print_image.py input.tiff curve.quad | sudo tee /dev/usb/lp0 > /dev/null
```

### ヘルプ表示

```bash
python3 test_print_image.py --help
```

---

## 実機テスト

詳細は [TESTING_GUIDE.md](TESTING_GUIDE.md) を参照してください。

### クイックスタート

```bash
cd /tmp/escpr_driver

# 1. テストバイナリ生成
python3 test_print_image.py \
  /tmp/test_simple_rect.tiff \
  /Library/Printers/QTR/quadtone/QTR_P9550/P9550-PtPd-xf1-3ink.quad \
  -o test.bin

# 2. プリンターへ送信
sudo cat test.bin > /dev/usb/lp0
```

---

## 技術仕様

### サポートする画像形式

- TIFF
- PNG
- JPEG
- その他PIL/Pillowが対応する形式

すべてグレースケールに変換されます。

### ESC/P-Rasterコマンド

実装済みのコマンド:

- `ESC @` - プリンター初期化
- `ESC ( R "REMOTE1"` - リモートモード開始
- `ESC ( R "ESCPR"` - ESC/P-Rモード設定
- `ESC j "sets"` - 用紙サイズ設定
- `ESC q "setq"` - 解像度・品質設定
- `ESC j "setj"` - ジョブ属性設定
- `ESC d "dsnd"` - ラスターデータ送信
- `ESC p "endp"` - ページ終了
- `ESC j "endj"` - ジョブ終了

### QuadToneRIPカーブ

対応チャンネル:
- K, C, M, Y, LC, LM, LK, LLK, V, MK

グレースケール印刷ではKチャンネルのみ使用。

---

## トラブルシューティング

### プリンターが反応しない

1. プリンター接続を確認
2. USB/ネットワーク接続をテスト
3. より小さいバイナリ（初期化のみ）で試す

### 用紙サイズエラー

`escpr_commands.py` の `make_size_command()` を調整。
詳細は [TESTING_GUIDE.md](TESTING_GUIDE.md) 参照。

### 解像度エラー

`escpr_commands.py` の `make_quality_command()` を調整。

---

## 開発情報

### アーキテクチャ

```
test_print_image.py (メインスクリプト)
  ↓
┌─────────────────┐
│ PIL/Pillow      │ 画像読み込み
└─────────────────┘
  ↓
┌─────────────────┐
│ quad_parser.py  │ QuadToneRIPカーブ適用
└─────────────────┘
  ↓
┌─────────────────┐
│ escpr_driver.py │ ESCPRDriverクラス
└─────────────────┘
  ↓
┌─────────────────┐
│escpr_commands.py│ ESC/P-Rコマンド生成
└─────────────────┘
  ↓
ESC/P-Rasterバイナリ
```

### コマンド生成のカスタマイズ

`escpr_commands.py` を編集してコマンドパラメータを調整:

```python
def make_size_command(width_mm, height_mm):
    # ここを変更
    width_units = int(width_mm * 100)  # 単位変換
    height_units = int(height_mm * 100)
    data = struct.pack('<II', width_units, height_units)  # エンコード
    return _make_escpr_command('j', 'sets', data)
```

---

## 参考資料

### プロジェクト内ドキュメント

- [完成報告書](ESCPR_DRIVER_COMPLETE.md) - 実装の詳細、統計情報
- [実機テストガイド](TESTING_GUIDE.md) - トラブルシューティング、デバッグ方法
- [設計書](/tmp/escpr_python_driver_design.md) - プロトコル仕様、設計方針

### 外部リソース

- [epson-printer-escpr-improved (GitHub)](https://github.com/mrnuke/epson-printer-escpr-improved) - 参考にしたオープンソースドライバー
- [QuadToneRIP](https://www.quadtonerip.com/) - カーブファイル形式の情報源

---

## 貢献

このドライバーは実験的実装です。改善案やバグ報告は歓迎します。

### 既知の問題

- コマンドパラメータが暫定実装（実機テストで調整必要）
- RLE圧縮未実装（データサイズが大きい）
- カラー印刷未対応

### 将来の拡張

- [ ] RLE圧縮実装
- [ ] カラー印刷対応（RGB/CMYK）
- [ ] CUPSフィルターとして統合
- [ ] PPDファイル作成
- [ ] エラーハンドリング強化
- [ ] 双方向通信対応

---

## ライセンス

このドライバーは、EPSON公式のオープンソースドライバー（epson-inkjet-printer-escpr）を参考に実装されています。

参考元ドライバーのライセンスに準拠することを想定しています（GPL-2.0等）。

---

## 免責事項

**このドライバーは実験的実装であり、動作を保証するものではありません。**

- プリンターの故障や損傷について、開発者は責任を負いません
- 実機テストは自己責任で行ってください
- 重要なプリントジョブでの使用は推奨しません

---

## クレジット

- **プロトコル解析:** epson-inkjet-printer-escpr-improved
- **開発:** Claude Code (Anthropic)
- **テスト:** EPSON SC-P9500/P9550ユーザー

---

## バージョン履歴

### 0.1.0 (2026-04-06)

- 初版リリース
- ESC/P-Raster基本実装
- QuadToneRIPカーブ統合
- グレースケール印刷対応

---

## サポート

問題が発生した場合:

1. [TESTING_GUIDE.md](TESTING_GUIDE.md) のトラブルシューティングを確認
2. エラーメッセージとバイナリの先頭部分を記録
3. 段階的テスト（初期化のみ→ジョブ設定→データ送信）を試す
4. EPSON純正ドライバーの出力と比較

---

**Happy Printing! 🖨️**
