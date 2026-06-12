# ESC/P-R Driver 実機テストガイド

**対象プリンター:** EPSON SC-P9500/P9550
**作成日:** 2026年4月6日

---

## 準備

### 1. 必要なもの

- EPSON SC-P9500/P9550プリンター（USB接続またはネットワーク接続）
- macOS環境
- Python 3.x
- PIL/Pillow (`pip3 install pillow`)
- numpy (`pip3 install numpy`)

### 2. ドライバーファイル確認

```bash
cd /tmp/escpr_driver
ls -l

# 必要なファイル:
# - escpr_commands.py
# - escpr_driver.py
# - quad_parser.py
# - test_print_image.py
```

---

## テスト方法

### 方法1: USB直接送信（最も確実）

#### ステップ1: プリンター接続確認

```bash
# プリンター一覧表示
lpstat -v | grep P9500

# 期待される出力例:
# device for EPSON_SC_P9500_Series: usb://EPSON/SC-P9500%20Series?serial=...
```

#### ステップ2: USBデバイスパス確認

```bash
# USB LPTデバイス確認
ls -l /dev/usb/lp*

# または
system_profiler SPUSBDataType | grep -A 10 "SC-P9"
```

#### ステップ3: テストバイナリ生成

```bash
cd /tmp/escpr_driver

# 小さなテストパターンで試す
python3 test_print_image.py \
  /tmp/test_simple_rect.tiff \
  /Library/Printers/QTR/quadtone/QTR_P9550/P9550-PtPd-xf1-3ink.quad \
  -o test_usb.bin \
  --dpi 720x720 \
  --paper 210x297

# ファイルサイズ確認
ls -lh test_usb.bin
```

#### ステップ4: プリンターに送信

```bash
# USB直接送信（要root権限）
sudo cat test_usb.bin > /dev/usb/lp0

# または、デバイスパスが異なる場合
sudo cat test_usb.bin > /dev/usb/lp1
```

**期待される結果:**
- プリンターが応答する
- エラーなし、または明確なエラーメッセージ
- 理想的には何らかの印刷動作（用紙送り、ヘッド移動など）

---

### 方法2: lpr経由（CUPS使用）

#### ステップ1: CUPS設定確認

```bash
lpstat -p EPSON_SC_P9500_Series
```

#### ステップ2: Rawモードで送信

```bash
# テストバイナリをRawモードで送信
lpr -P EPSON_SC_P9500_Series -o raw test_usb.bin

# ジョブ状態確認
lpstat -o
```

---

### 方法3: ネットワーク経由（IPP/Raw）

#### ステップ1: プリンターIPアドレス確認

```bash
lpstat -v | grep P9500

# 期待される出力例:
# device for EPSON_SC_P9500_Series: ipp://192.168.1.100:631/ipp/print
```

#### ステップ2: Raw Socket送信（ポート9100）

```bash
# ネットワークプリンターへ直接送信
cat test_usb.bin | nc 192.168.1.100 9100
```

---

## デバッグ手順

### エラーが発生した場合

#### 1. プリンターのエラーログ確認

```bash
# CUPSエラーログ
tail -f /var/log/cups/error_log

# プリンタージョブログ
lpstat -W all
```

#### 2. バイナリ内容の確認

```bash
# 最初の256バイト確認
hexdump -C test_usb.bin | head -20

# ESC/P-Rシーケンス確認
python3 /tmp/analyze_protocol_alternative.py test_usb.bin
```

#### 3. 段階的テスト

**テスト1: 初期化のみ**

```python
# test_init_only.py
from escpr_driver import ESCPRDriver

with ESCPRDriver('test_init.bin') as driver:
    driver.initialize()
    # ジョブ開始なし
```

**テスト2: 初期化 + ジョブ設定のみ**

```python
from escpr_driver import ESCPRDriver

with ESCPRDriver('test_job_setup.bin') as driver:
    driver.initialize()
    driver.start_job(width_mm=210, height_mm=297,
                    dpi_x=720, dpi_y=720)
    driver.end_job()
    # データ送信なし
```

**テスト3: 1行だけ送信**

```python
from escpr_driver import ESCPRDriver

with ESCPRDriver('test_one_line.bin') as driver:
    driver.initialize()
    driver.start_job(width_mm=210, height_mm=297,
                    dpi_x=720, dpi_y=720)
    driver.print_line(bytes([0xFF] * 100))  # 100バイトの白
    driver.end_page()
    driver.end_job()
```

#### 4. EPSON純正ドライバーとの比較

```bash
# 純正ドライバーでテスト印刷
lpr -P EPSON_SC_P9500_Series /tmp/test_simple_rect.tiff

# CUPSスプールファイルを取得
sudo cp /var/spool/cups/d<job-id>-001 /tmp/epson_native_output.bin

# 比較
hexdump -C /tmp/epson_native_output.bin | head -50
hexdump -C test_usb.bin | head -50
```

---

## よくある問題と対処

### 問題1: プリンターが反応しない

**原因:**
- バイナリが正しく送信されていない
- プリンターがESC/P-Rモードになっていない

**対処:**
1. プリンター電源を入れ直す
2. USB/ネットワーク接続を確認
3. より小さいバイナリ（初期化のみ）で試す

### 問題2: 用紙サイズエラー

**原因:**
- `make_size_command()` のパラメータ形式が不正

**対処:**
1. `escpr_commands.py` の `make_size_command()` を確認
2. 純正ドライバーの出力と比較
3. パラメータの単位・エンコードを調整

**修正例:**

```python
def make_size_command(width_mm, height_mm):
    # 現在の実装（暫定）
    width_units = int(width_mm * 100)   # 0.01mm単位
    height_units = int(height_mm * 100)
    data = struct.pack('<II', width_units, height_units)

    # もし上記でエラーが出る場合、以下を試す:
    # 方法1: 単位を変更（例: 0.1mm単位）
    # width_units = int(width_mm * 10)

    # 方法2: 追加パラメータを含める
    # data = struct.pack('<IIHH', width_units, height_units, 0, 0)

    return _make_escpr_command('j', 'sets', data)
```

### 問題3: 解像度エラー

**対処:**

```python
def make_quality_command(dpi_x, dpi_y, quality=1):
    # 現在の実装（暫定）
    data = struct.pack('<HHB', dpi_x, dpi_y, quality)

    # もしエラーが出る場合、以下を試す:
    # 方法1: 32bitで格納
    # data = struct.pack('<IIB', dpi_x, dpi_y, quality)

    # 方法2: 追加パラメータを含める
    # data = struct.pack('<HHBBB', dpi_x, dpi_y, quality, 0, 0)

    return _make_escpr_command('q', 'setq', data)
```

### 問題4: データが印刷されない

**原因:**
- ラスターデータ形式が不正
- ピクセルフォーマットの不一致

**対処:**
1. データサイズを確認（幅と一致しているか）
2. バイトオーダーを確認
3. 純正ドライバーのデータと比較

---

## 成功した場合の次のステップ

### 1. より大きな画像でテスト

```bash
# A4サイズのグラデーション画像で試す
python3 test_print_image.py \
  /tmp/test_gradient_100.tiff \
  /Library/Printers/QTR/quadtone/QTR_P9550/P9550-PtPd-xf1-3ink.quad \
  -o test_gradient.bin \
  --dpi 720x720

sudo cat test_gradient.bin > /dev/usb/lp0
```

### 2. 高解像度テスト

```bash
# 2880x1440 DPIで試す
python3 test_print_image.py \
  input.tiff \
  curve.quad \
  -o test_hires.bin \
  --dpi 2880x1440

sudo cat test_hires.bin > /dev/usb/lp0
```

### 3. CUPSフィルターとして統合

```bash
# フィルタースクリプト作成
sudo cp test_print_image.py /usr/libexec/cups/filter/rastertop9550escpr
sudo chmod 755 /usr/libexec/cups/filter/rastertop9550escpr

# PPDファイル作成（QuadP9550.ppdベース）
# cupsFilterディレクティブを変更:
# *cupsFilter: "image/tiff 100 rastertop9550escpr"
```

---

## トラブルシューティングチェックリスト

- [ ] プリンターの電源が入っている
- [ ] USB/ネットワーク接続が正常
- [ ] Pythonモジュール（PIL, numpy）がインストール済み
- [ ] QuadToneRIPカーブファイルが存在する
- [ ] テストバイナリが正常に生成されている（0バイトでない）
- [ ] プリンターがESC/P-Rに対応している（P9500/P9550は対応）
- [ ] CUPSエラーログを確認した
- [ ] 段階的テスト（初期化のみ→ジョブ設定→データ送信）を試した

---

## サポートが必要な場合

### 報告すべき情報

1. **エラーメッセージ**
   ```bash
   # CUPSログから抽出
   tail -100 /var/log/cups/error_log
   ```

2. **生成されたバイナリの先頭部分**
   ```bash
   hexdump -C test_usb.bin | head -30
   ```

3. **プリンター情報**
   ```bash
   lpstat -v
   system_profiler SPPrintersDataType
   ```

4. **使用したコマンド**
   ```bash
   # 実行したコマンドをそのままコピー
   ```

---

## 参考資料

- [ESC/P-R Driver Complete Report](/tmp/escpr_driver/ESCPR_DRIVER_COMPLETE.md)
- [ESC/P-R Protocol Design](/tmp/escpr_python_driver_design.md)
- [Phase 1 Complete Report](/tmp/phase1_complete_report.md)
- [GitHub: epson-printer-escpr-improved](https://github.com/mrnuke/epson-printer-escpr-improved)

---

## クイックスタート

```bash
# 1. ドライバーディレクトリへ移動
cd /tmp/escpr_driver

# 2. テストバイナリ生成
python3 test_print_image.py \
  /tmp/test_simple_rect.tiff \
  /Library/Printers/QTR/quadtone/QTR_P9550/P9550-PtPd-xf1-3ink.quad \
  -o test.bin

# 3. プリンターへ送信
sudo cat test.bin > /dev/usb/lp0

# 4. 結果を確認
# - プリンターが反応したか？
# - エラーメッセージは？
# - 何か印刷されたか？
```

成功を祈ります！ 🍀
