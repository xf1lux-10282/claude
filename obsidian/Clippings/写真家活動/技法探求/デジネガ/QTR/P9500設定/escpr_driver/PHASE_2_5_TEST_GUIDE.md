# Phase 2.5: 実機テスト完全ガイド

**推定所要時間:** 1-2時間
**作業日:** 2026年4月6日以降
**前提条件:** Phase 2.4完了、P9550がUSBまたはネットワーク接続済み

---

## 📋 テストの流れ

```
Step 1: プリンター接続確認 (5分)
  ↓
Step 2: 最小テストパターン送信 (10分)
  ↓
Step 3: エラー診断・パラメータ調整 (30-60分)
  ↓
Step 4: 実用テスト (30分)
  ↓
完了: 動作確認済みドライバー
```

---

## Step 1: プリンター接続確認

### 1.1 USB接続の場合

```bash
# プリンターデバイス確認
lpstat -v | grep P9500

# 期待される出力例:
# device for EPSON_SC_P9500_Series: usb://EPSON/SC-P9500%20Series?serial=...

# USB生デバイス確認
ls -la /dev/usb/lp*

# または
system_profiler SPUSBDataType | grep -A 10 "SC-P9500"
```

**デバイスパス候補:**
- `/dev/usb/lp0`
- `/dev/usb/lp1`
- `/dev/cu.usbmodemXXXXXX`

### 1.2 ネットワーク接続の場合

```bash
# プリンターIPアドレス確認（プリンターのネットワーク設定画面から）
# 例: 192.168.1.100

# 接続テスト
ping -c 3 192.168.1.100

# JetDirectポート確認（通常9100番ポート）
nc -zv 192.168.1.100 9100
```

---

## Step 2: 最小テストパターン送信

### 2.1 テストバイナリ生成

```bash
cd /tmp/escpr_driver

# 既存の小さいテストパターン（10x10ピクセル）を使用
python3 test_print_image.py \
  /tmp/test_simple_rect.tiff \
  /Library/Printers/QTR/quadtone/QTR_P9550/P9550-PtPd-xf1-3ink.quad \
  -o /tmp/phase2_5_test_minimal.bin

# 生成確認
ls -lh /tmp/phase2_5_test_minimal.bin
hexdump -C /tmp/phase2_5_test_minimal.bin | head -20
```

**期待される出力:**
- ファイルサイズ: 約300-500バイト
- 先頭バイト: `1b 40` (ESC @) で始まる
- 末尾: `1b 6a` (ESC j "endj") で終わる

### 2.2 USB経由で送信

```bash
# 方法1: cat経由（最もシンプル）
sudo cat /tmp/phase2_5_test_minimal.bin > /dev/usb/lp0

# 方法2: lpr経由（CUPS経由）
lpr -P EPSON_SC_P9500_Series -o raw /tmp/phase2_5_test_minimal.bin
```

### 2.3 ネットワーク経由で送信

```bash
# 方法1: nc経由
cat /tmp/phase2_5_test_minimal.bin | nc 192.168.1.100 9100

# 方法2: lpr経由（ネットワークプリンター設定済みの場合）
lpr -P EPSON_SC_P9500_Series -o raw /tmp/phase2_5_test_minimal.bin
```

### 2.4 結果の観察

**成功のサイン:**
- ✅ プリンターがデータを受信
- ✅ 用紙が給紙される
- ✅ 何かが印刷される（たとえ意図と違っても）
- ✅ エラーランプが点灯しない

**失敗のサイン:**
- ❌ プリンターが無反応
- ❌ エラーランプ点灯
- ❌ プリンターディスプレイにエラーメッセージ
- ❌ 用紙が給紙されるが何も印刷されない

---

## Step 3: エラー診断・パラメータ調整

### 3.1 完全無反応の場合

**原因候補:**
1. デバイスパスが間違っている
2. プリンターがESC/P-Rasterモードになっていない
3. 初期化シーケンスが不完全

**対処:**

```bash
# デバッグ用: 初期化シーケンスのみ送信
python3 -c "
from escpr_commands import get_full_init_sequence
import sys
sys.stdout.buffer.write(get_full_init_sequence())
" | sudo tee /dev/usb/lp0 > /dev/null

# プリンターの反応を観察
```

### 3.2 エラーメッセージが出る場合

**P9550ディスプレイのエラーメッセージを記録:**

例: "用紙サイズエラー"、"解像度エラー" など

**対処: パラメータ調整が必要**

#### 用紙サイズコマンド調整

現在の実装（`escpr_commands.py:make_size_command()`）:
```python
def make_size_command(width_mm, height_mm):
    width_units = int(width_mm * 100)   # 0.01mm単位と仮定
    height_units = int(height_mm * 100)
    data = struct.pack('<II', width_units, height_units)
    return _make_escpr_command('j', 'sets', data)
```

**調整案:**

```python
# 案1: 単位を変更（0.1mm単位）
width_units = int(width_mm * 10)
height_units = int(height_mm * 10)

# 案2: 追加パラメータが必要
data = struct.pack('<IIHH', width_units, height_units, paper_type, paper_source)

# 案3: 完全に異なるフォーマット
# → EPSON純正ドライバーのバイナリ解析が必要
```

**デバッグ手順:**

```bash
# 1. EPSON純正ドライバーで同じ画像を印刷
# System Preferences → Printers → SC-P9500 → Print Test Page

# 2. CUPSスプールファイルを探す
ls -lt /var/spool/cups/d*

# 3. スプールファイルの末尾（ESC/P-Rバイナリ）を抽出
sudo tail -c 10000 /var/spool/cups/d00001-001 > /tmp/epson_native_output.bin

# 4. hexdump比較
hexdump -C /tmp/epson_native_output.bin > /tmp/native.hex
hexdump -C /tmp/phase2_5_test_minimal.bin > /tmp/ours.hex

# 5. diffで差分確認
diff /tmp/native.hex /tmp/ours.hex | head -50
```

#### 解像度コマンド調整

現在の実装:
```python
def make_quality_command(dpi_x, dpi_y, quality=1):
    data = struct.pack('<HHB', dpi_x, dpi_y, quality)
    return _make_escpr_command('q', 'setq', data)
```

**調整が必要な場合は同様にバイナリ比較で正しい形式を推測**

### 3.3 用紙は給紙されるが何も印刷されない場合

**原因候補:**
1. ラスターデータフォーマットが間違っている
2. ピクセルの並び順（リトルエンディアン/ビッグエンディアン）
3. データ幅の不一致（パディングが必要）

**対処:**

```bash
# テストパターンをより明確に
python3 -c "
from PIL import Image
import numpy as np

# 50x50ピクセルの白黒チェッカーパターン
img = np.zeros((50, 50), dtype=np.uint8)
img[::2, ::2] = 255  # 白
img[1::2, 1::2] = 255  # 白
Image.fromarray(img).save('/tmp/test_checker_50.tiff')
"

# このパターンで再テスト
python3 test_print_image.py \
  /tmp/test_checker_50.tiff \
  /Library/Printers/QTR/quadtone/QTR_P9550/P9550-PtPd-xf1-3ink.quad \
  -o /tmp/test_checker_50.bin

sudo cat /tmp/test_checker_50.bin > /dev/usb/lp0
```

---

## Step 4: 実用テスト

### 4.1 より大きな画像でテスト

```bash
# A4サイズ、720DPI相当の画像（約2100x2970ピクセル）
python3 -c "
from PIL import Image, ImageDraw
import numpy as np

# A4 at 300 DPI (簡易版)
width, height = 2480, 3508  # 210mm x 297mm at 300 DPI
img = Image.new('L', (width, height), 255)
draw = ImageDraw.Draw(img)

# グラデーション
for i in range(height):
    gray = int(255 * (1 - i / height))
    draw.line([(0, i), (width, i)], fill=gray)

img.save('/tmp/test_a4_gradient.tiff')
print(f'Created: {width}x{height} gradient')
"

# QuadToneRIPカーブ適用して変換
python3 /tmp/escpr_driver/test_print_image.py \
  /tmp/test_a4_gradient.tiff \
  /Library/Printers/QTR/quadtone/QTR_P9550/P9550-PtPd-xf1-3ink.quad \
  -o /tmp/test_a4_gradient.bin \
  --dpi 720x720 \
  --paper 210x297

# ファイルサイズ確認
ls -lh /tmp/test_a4_gradient.bin

# 送信
sudo cat /tmp/test_a4_gradient.bin > /dev/usb/lp0
```

### 4.2 高解像度テスト

```bash
# 2880x1440 DPIでテスト（小さい画像推奨）
python3 /tmp/escpr_driver/test_print_image.py \
  /tmp/test_simple_rect.tiff \
  /Library/Printers/QTR/quadtone/QTR_P9550/P9550-PtPd-xf1-3ink.quad \
  -o /tmp/test_high_dpi.bin \
  --dpi 2880x1440 \
  --paper 50x50

sudo cat /tmp/test_high_dpi.bin > /dev/usb/lp0
```

---

## 🎯 成功判定基準

### 最低限の成功（Phase 2.5完了）

- ✅ プリンターがデータを受信
- ✅ 用紙が給紙される
- ✅ 何かが印刷される（位置・濃度は問わない）
- ✅ エラーが発生しない

### 実用レベルの成功

- ✅ 指定した用紙サイズで印刷される
- ✅ 画像の位置が正しい
- ✅ グラデーションが滑らか（バンディングなし）
- ✅ QuadToneRIPカーブが正しく適用されている
- ✅ A4サイズが問題なく印刷できる

---

## 📝 テスト結果記録用テンプレート

```markdown
# Phase 2.5 実機テスト結果

**テスト日時:** 2026年X月X日 XX:XX
**プリンター:** EPSON SC-P9500/P9550
**接続方法:** USB / ネットワーク
**テスト担当:**

---

## Test 1: 最小テストパターン

**コマンド:**
```bash
python3 test_print_image.py /tmp/test_simple_rect.tiff ...
sudo cat /tmp/phase2_5_test_minimal.bin > /dev/usb/lp0
```

**結果:**
- [ ] 成功
- [ ] 失敗

**観察:**
- プリンターの反応:
- 印刷結果:
- エラーメッセージ:

---

## Test 2: パラメータ調整（必要な場合）

**調整内容:**
- `make_size_command()`:
- `make_quality_command()`:

**結果:**
- [ ] 成功
- [ ] 失敗

---

## Test 3: 実用テスト

**画像サイズ:**
**解像度:**
**用紙サイズ:**

**結果:**
- [ ] 成功
- [ ] 失敗

**印刷品質評価:**
- 位置:
- 濃度:
- グラデーション:
- カーブ適用:

---

## 総合評価

- [ ] Phase 2.5完了（最低限の動作確認）
- [ ] 実用レベル達成

**備考:**

```

---

## 🔧 トラブルシューティング早見表

| 症状 | 可能性 | 対処 |
|------|--------|------|
| プリンター完全無反応 | デバイスパス間違い | `lpstat -v`、`ls /dev/usb/` で確認 |
| Permission denied | sudo忘れ | `sudo cat` で実行 |
| "用紙サイズエラー" | size_command形式エラー | EPSON純正バイナリと比較 |
| 給紙するが白紙 | データフォーマットエラー | ピクセル並び順、パディング確認 |
| バンディング（縞模様） | 解像度設定ミス | DPI値を調整 |
| カーブが効いていない | .quadファイル読込失敗 | `python3 quad_parser.py curve.quad` で確認 |
| USB送信後フリーズ | プリンターが応答待ち | 双方向通信無効化を検討 |

---

## 📚 参考コマンド集

```bash
# プリンター情報取得
lpstat -v
lpstat -p
lpoptions -p EPSON_SC_P9500_Series -l

# CUPSログ確認
tail -f /var/log/cups/error_log

# USB通信モニタ（Wireshark等が必要）
# → 実用的ではない（macOS Big Sur以降）

# プリンタードライバー確認
ls -la /Library/Printers/EPSON/InkjetPrinter2/Filter/

# テストパターン生成（Python）
python3 -c "from PIL import Image; Image.new('L', (100, 100), 128).save('test.tiff')"

# hexdump比較
hexdump -C file1.bin > file1.hex
hexdump -C file2.bin > file2.hex
diff file1.hex file2.hex | less
```

---

**次のステップ:** このガイドに従ってStep 1から順に実行してください。
