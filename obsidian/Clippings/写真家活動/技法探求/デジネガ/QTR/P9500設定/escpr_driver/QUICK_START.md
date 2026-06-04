# クイックスタートガイド
# EPSON SC-P9550 ESC/P-Raster QuadToneRIP Driver

**最速セットアップ（5分）**

---

## 方法A: 自動インストール（推奨）

```bash
cd /tmp/escpr_driver
sudo ./install.sh
```

完了！　次は[使い方](#使い方)へ

---

## 方法B: 手動インストール（より理解できる）

### Step 1: ファイル配置（コピー&ペースト）

```bash
# 1. ドライバーモジュールをインストール
sudo mkdir -p /Library/Printers/QTR/escpr_driver
sudo mkdir -p /Library/Printers/QTR/filter
sudo cp /tmp/escpr_driver/{escpr_commands.py,escpr_driver.py,quad_parser.py} \
    /Library/Printers/QTR/escpr_driver/

# 2. CUPSフィルターをインストール
sudo cp /tmp/escpr_driver/rastertop9550 /Library/Printers/QTR/filter/
sudo chmod +x /Library/Printers/QTR/filter/rastertop9550

# 3. フィルター内のパス設定を更新
sudo sed -i '' 's|DRIVER_DIR = .*|DRIVER_DIR = "/Library/Printers/QTR/escpr_driver"|' \
    /Library/Printers/QTR/filter/rastertop9550

# 4. PPDファイルをインストール
sudo cp /tmp/escpr_driver/P9550_ESCPR_QTR.ppd \
    /Library/Printers/PPDs/Contents/Resources/
sudo sed -i '' 's|/tmp/escpr_driver/rastertop9550|/Library/Printers/QTR/filter/rastertop9550|' \
    /Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd
sudo gzip -f /Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd
```

### Step 2: プリンター追加（GUI - あなたの提案通り）

#### システム環境設定から追加（最も簡単）

1. **システム環境設定** → **プリンタとスキャナ** を開く

2. **「+」ボタン**をクリック

3. **既存のSC-P9500/P9550を選択**
   - USB接続の場合: `EPSON SC-P9500 Series` が表示される
   - ネットワークの場合: IPアドレスで検出される

4. **「使用」（ドライバー選択）**のドロップダウンメニューで
   - **「その他...」** を選択
   - `/Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd.gz` を選択
   - または リストから **「P9550 QTR ESC/P-R」** を選択

5. **「追加」**をクリック

完了！

#### コマンドライン（より確実）

```bash
# プリンターURIを確認
lpstat -v | grep SC-P9

# プリンターキュー登録
sudo lpadmin -p P9550_QTR_ESCPR \
    -v 'usb://EPSON/SC-P9500%20Series?serial=XXXXXXXX' \
    -P /Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd.gz \
    -D "EPSON SC-P9550 QuadToneRIP ESC/P-Raster" \
    -E

# プリンターを有効化
sudo cupsenable P9550_QTR_ESCPR
sudo cupsaccept P9550_QTR_ESCPR
```

---

## 使い方

### 印刷手順

1. **任意のアプリケーションで印刷** (⌘P)

2. **プリンター選択**
   - `P9550 QTR ESC/P-R` または `P9550_QTR_ESCPR` を選択

3. **「詳細を表示」をクリック**

4. **QuadTone RIP Curve 1** を選択
   - `P9550-PtPd-xf1-3ink` （利用可能なカーブ）
   - または `None (Linear)` （カーブなし）

5. **解像度を選択**（オプション）
   - `720 DPI` （推奨・標準）
   - `1440 DPI` （高品質）
   - `2880 DPI` （最高品質・遅い）

6. **印刷**ボタンをクリック

---

## トラブルシューティング（2つだけ）

### 問題1: プリンターリストに出てこない

```bash
# CUPS再起動
sudo launchctl stop org.cups.cupsd
sudo launchctl start org.cups.cupsd
```

### 問題2: 印刷されない

```bash
# ログ確認
tail -f /var/log/cups/error_log

# プリンター状態確認
lpstat -p
```

エラーメッセージをコピーして、INSTALLATION_GUIDE.mdの該当箇所を参照。

---

## カーブファイルの追加

新しい`.quad`カーブファイルを使用する場合：

```bash
# 1. カーブファイルをコピー
sudo cp my_curve.quad /Library/Printers/QTR/quadtone/QTR_P9550/

# 2. PPDファイルを編集
sudo gunzip /Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd.gz
sudo nano /Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd

# 以下の行を "ripCurve1" セクションに追加:
# *ripCurve1 my_curve/My Custom Curve: ""

# 保存して再圧縮
sudo gzip /Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd

# 3. CUPS再起動
sudo launchctl stop org.cups.cupsd
sudo launchctl start org.cups.cupsd
```

---

## アンインストール

```bash
# プリンターキュー削除
sudo lpadmin -x P9550_QTR_ESCPR

# ファイル削除
sudo rm -rf /Library/Printers/QTR/escpr_driver
sudo rm /Library/Printers/QTR/filter/rastertop9550
sudo rm /Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd.gz

# CUPS再起動
sudo launchctl stop org.cups.cupsd
sudo launchctl start org.cups.cupsd
```

---

## 次のステップ

- **詳細な技術情報**: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) を参照
- **トラブルシューティング**: [INSTALLATION_GUIDE.md#トラブルシューティング](INSTALLATION_GUIDE.md#トラブルシューティング)
- **実機テスト結果**: [TESTING_GUIDE.md](TESTING_GUIDE.md) を参照

---

**これであなたのP9550でQuadToneRIPが使えます！**
