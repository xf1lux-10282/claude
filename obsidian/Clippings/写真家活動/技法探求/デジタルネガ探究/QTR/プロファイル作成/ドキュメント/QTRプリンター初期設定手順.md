# QTRプリンター初期設定手順

**作成日**: 2026年3月15日
**対象**: 新しいプリンターでQuadToneRIPを初めて使用する場合
**前提**: QuadToneRIPがインストール済み

---

## 概要

QuadToneRIP (QTR)を使用してデジタルネガを作成するには、以下の手順でプリンターを設定する必要があります:

1. QuadToneRIPのインストール（既にインストール済みの場合はスキップ）
2. プリンター固有のプロファイル・カーブのインストール
3. macOSシステム環境設定でのプリンター追加
4. QTR Print-Toolでの動作確認
5. カスタムカーブの配置とデータベース更新

---

## 1. QuadToneRIPのインストール

### 1.1 ダウンロードとインストール

**ダウンロード先**:
- QuadToneRIP公式サイト: https://www.quadtonerip.com/

**インストール手順**:
```bash
# 1. ダウンロードしたdmgファイルをマウント
open QuadToneRIP-<version>.dmg

# 2. インストーラーを実行
# Finderでパッケージを開いてインストール
```

**インストール先**:
- アプリケーション: `/Applications/QuadToneRIP/`
- システムファイル: `/Library/Printers/QTR/`

### 1.2 インストール確認

```bash
# QTRディレクトリが存在するか確認
ls -la /Library/Printers/QTR/

# 出力例:
# drwxr-xr-x  bin/
# drwxr-xr-x  quadtone/
# drwxr-xr-x  logs/
```

---

## 2. プリンター固有のプロファイル・カーブのインストール

### 2.1 使用プリンターの確認

**プリンター名**: Epson SC-PX1V
**QTR対応名**: P700（SC-PX1VはEpson SureColor P700の日本名）

### 2.2 プロファイルディレクトリの確認

```bash
# P700用プロファイルディレクトリを確認
ls -la /Applications/QuadToneRIP/Profiles/

# P700-900-UC ディレクトリが存在することを確認
ls -la /Applications/QuadToneRIP/Profiles/P700-900-UC/
```

**P700-900-UCディレクトリの内容**:
- `InstallP700.command`: P700用インストールスクリプト
- `InstallP900.command`: P900用インストールスクリプト
- `UCmk-*.txt`: Matt Black用カーブ（Enhanced Matte Paper用）
- `UCpk-*.txt`: Photo Black用カーブ（Baryta Paper用など）

### 2.3 InstallP700.commandの実行

**方法1: Finderから実行（推奨）**:
```
1. Finderで /Applications/QuadToneRIP/Profiles/P700-900-UC/ を開く
2. InstallP700.command をダブルクリック
3. 管理者パスワードを入力
4. ターミナルウィンドウが開き、インストールが実行される
5. 完了メッセージを確認
```

**方法2: ターミナルから実行**:
```bash
# P700-900-UCディレクトリに移動
cd /Applications/QuadToneRIP/Profiles/P700-900-UC/

# InstallP700.commandを実行
./InstallP700.command

# 管理者パスワードを入力
```

### 2.4 インストール内容の確認

InstallP700.commandは以下の処理を実行します:

```bash
# 1. プリンター固有のディレクトリを作成
/Library/Printers/QTR/quadtone/QuadP700/

# 2. UCカーブ（.txt形式）を.quad形式に変換してコピー
/Library/Printers/QTR/quadtone/QuadP700/*.quad

# 3. QTRデータベースを更新
/Library/Printers/QTR/bin/quadcurves QuadP700
```

**確認コマンド**:
```bash
# QuadP700ディレクトリが作成されたか確認
ls -la /Library/Printers/QTR/quadtone/

# 出力例:
# drwxr-xr-x  QuadP700/
# drwxr-xr-x  QuadP900/
# ...

# QuadP700内のカーブファイルを確認
ls -la /Library/Printers/QTR/quadtone/QuadP700/

# 出力例:
# -rw-r--r--  UCmk-EnhMatte-neut.quad
# -rw-r--r--  UCpk-HMBaryta-neut.quad
# ...
```

---

## 3. macOSシステム環境設定でのプリンター追加

### 3.1 プリンターをUSB接続

```
1. SC-PX1VをUSBケーブルでMacに接続
2. プリンターの電源をON
3. macOSが自動的にプリンターを認識
```

### 3.2 システム環境設定でプリンター追加

**macOS Ventura以降**:
```
1. システム設定 > プリンタとスキャナ
2. 「プリンタまたはスキャナを追加...」をクリック
3. SC-PX1Vを選択
4. 「使用」ドロップダウンから「QuadToneRIP - QuadP700」を選択
   ⚠️ 重要: 通常のEpsonドライバーではなく、QuadToneRIPを選択
5. 「追加」をクリック
```

**macOS Big Sur / Monterey**:
```
1. システム環境設定 > プリンタとスキャナ
2. 「+」ボタンをクリック
3. SC-PX1Vを選択
4. 「使用」から「QuadToneRIP - QuadP700」を選択
5. 「追加」をクリック
```

### 3.3 プリンター名の確認

システム環境設定で追加されたプリンター名を確認:
```
例: "SC-PX1V (QuadP700)"
または
例: "QuadP700"
```

このプリンター名がQTR Print-Toolで表示されます。

---

## 4. QTR Print-Toolでの動作確認

### 4.1 QTR Print-Toolの起動

```bash
# Finderからアプリケーションを開く
open /Applications/QuadToneRIP/QTR-Print-Tool.app

# またはSpotlight検索で "QTR Print Tool" を検索
```

### 4.2 設定確認

**QTR Print-Toolウィンドウ**:
```
1. "Printer"ドロップダウン:
   → "SC-PX1V (QuadP700)" または "QuadP700" が表示されることを確認

2. "Curve"ドロップダウン:
   → UCmk-EnhMatte-neut, UCpk-HMBaryta-neut などが表示されることを確認

3. "Paper"ドロップダウン:
   → 使用する用紙を選択（例: Pictorico OHP Transparency Film）
```

### 4.3 テストプリント

**テスト画像の準備**:
```python
# 簡単なグラデーションテスト画像を作成
from PIL import Image
import numpy as np

# 256段階グラデーション
width = 2560
height = 100
gradient = np.linspace(0, 255, width).astype(np.uint8)
img_array = np.tile(gradient, (height, 1))
img = Image.fromarray(img_array, mode='L')
img.save('test_gradient.tif')
```

**QTR Print-Toolでプリント**:
```
1. "Open Image" ボタンで test_gradient.tif を開く
2. Curve: UCpk-HMBaryta-neut（またはリニアカーブ）
3. Paper: Pictorico OHP Film
4. "Print" ボタンをクリック
5. プリントが正常に実行されることを確認
```

---

## 5. カスタムカーブの配置とデータベース更新

### 5.1 カスタムカーブの配置

**生成したカーブファイルの配置先**:
```bash
# カーブファイル（.quad形式）をQuadP700ディレクトリにコピー
sudo cp /path/to/your/CustomCurve.quad /Library/Printers/QTR/quadtone/QuadP700/

# 例: PX1V-PtPd-v18.quadをコピー
sudo cp PX1V-PtPd-v18.quad /Library/Printers/QTR/quadtone/QuadP700/

# パスワードを入力
```

### 5.2 QTRデータベースの更新

**重要**: カーブファイルをコピーした後、必ずデータベースを更新してください。

```bash
# QuadP700のデータベースを更新
/Library/Printers/QTR/bin/quadcurves QuadP700

# 出力例:
# Updating curves for QuadP700...
# Processing PX1V-PtPd-v18.quad
# Processing UCmk-EnhMatte-neut.quad
# ...
# Database updated successfully.
```

### 5.3 QTR Print-Toolキャッシュのクリア

データベース更新後、QTR Print-Toolのキャッシュをクリアする必要があります:

```bash
# QTR Print-Toolの設定キャッシュをクリア
defaults delete com.quadtonerip.QTR-Print-Tool

# QTR Print-Toolを再起動
killall "QTR Print Tool" 2>/dev/null
open /Applications/QuadToneRIP/QTR-Print-Tool.app
```

### 5.4 新しいカーブの確認

```
1. QTR Print-Toolを開く
2. "Curve"ドロップダウンをクリック
3. 新しく追加したカーブ（例: PX1V-PtPd-v18）が表示されることを確認
```

---

## 6. 複数カーブの管理

### 6.1 カーブの命名規則

推奨される命名規則:
```
[プリンター名]-[技法名]-[バージョン].quad

例:
- PX1V-PtPd-v18.quad          (プラチナ/パラジウム用 v18)
- PX1V-PtPd-Linear-v18.quad   (リニアカーブ)
- PX1V-Gelatin-Silver-G2.quad (銀塩グレード2用)
- PX1V-Cyanotype.quad         (サイアノタイプ用)
```

### 6.2 カーブのバックアップ

```bash
# QuadP700ディレクトリ全体をバックアップ
sudo cp -R /Library/Printers/QTR/quadtone/QuadP700 \
          /Users/$USER/Documents/QTR-Backup/QuadP700-$(date +%Y%m%d)

# 例: QuadP700-20260315 というディレクトリが作成される
```

### 6.3 カーブの削除

```bash
# 不要なカーブファイルを削除
sudo rm /Library/Printers/QTR/quadtone/QuadP700/OldCurve.quad

# データベース更新
/Library/Printers/QTR/bin/quadcurves QuadP700

# キャッシュクリア
defaults delete com.quadtonerip.QTR-Print-Tool
```

---

## 7. トラブルシューティング

### 問題1: QTR Print-Toolでプリンターが表示されない

**原因と解決策**:
```
1. プリンターがシステム環境設定で正しく追加されていない
   → システム環境設定 > プリンタとスキャナ で再確認

2. QTRドライバーが選択されていない
   → プリンターを削除して、"QuadToneRIP - QuadP700"を選択して再追加

3. QTR Print-Toolのキャッシュが古い
   → defaults delete com.quadtonerip.QTR-Print-Tool で再起動
```

### 問題2: カーブが表示されない

**原因と解決策**:
```
1. カーブファイルが正しいディレクトリにない
   → ls /Library/Printers/QTR/quadtone/QuadP700/ で確認

2. データベースが更新されていない
   → /Library/Printers/QTR/bin/quadcurves QuadP700 を実行

3. QTR Print-Toolのキャッシュが古い
   → defaults delete com.quadtonerip.QTR-Print-Tool で再起動

4. .quad形式でない
   → .txt形式の場合は quadcurves が自動変換するが、
     手動で .quad 形式にする必要がある場合もある
```

### 問題3: プリント時に「Cannot open printer」エラー

**原因と解決策**:
```
1. プリンターの電源が入っていない
   → プリンターの電源をON

2. USBケーブルが接続されていない
   → USBケーブルを確認

3. プリンタードライバーがクラッシュ
   → システム環境設定でプリンターを削除して再追加

4. CUPS（印刷システム）の再起動が必要
   → sudo launchctl stop org.cups.cupsd
   → sudo launchctl start org.cups.cupsd
```

### 問題4: カーブ追加後もQTR Print-Toolで表示されない

**完全な再起動手順**:
```bash
# 1. QTR Print-Toolを終了
killall "QTR Print Tool" 2>/dev/null

# 2. キャッシュクリア
defaults delete com.quadtonerip.QTR-Print-Tool

# 3. データベース更新
/Library/Printers/QTR/bin/quadcurves QuadP700

# 4. QTR Print-Tool再起動
open /Applications/QuadToneRIP/QTR-Print-Tool.app

# 5. それでも表示されない場合は、.quadファイルの権限を確認
ls -la /Library/Printers/QTR/quadtone/QuadP700/YourCurve.quad

# 読み取り権限がない場合:
sudo chmod 644 /Library/Printers/QTR/quadtone/QuadP700/YourCurve.quad

# 6. 再度データベース更新とキャッシュクリア
```

---

## 8. カーブ作成ワークフローとの統合

### 8.1 新しいカーブを作成した場合の手順

```bash
# 1. カーブ生成スクリプトを実行
python3 generate_curve.py
# → PX1V-PtPd-v18.quad が生成される

# 2. QuadP700ディレクトリにコピー
sudo cp PX1V-PtPd-v18.quad /Library/Printers/QTR/quadtone/QuadP700/

# 3. データベース更新
/Library/Printers/QTR/bin/quadcurves QuadP700

# 4. QTR Print-Toolキャッシュクリア
defaults delete com.quadtonerip.QTR-Print-Tool

# 5. QTR Print-Tool再起動
killall "QTR Print Tool" 2>/dev/null
open /Applications/QuadToneRIP/QTR-Print-Tool.app

# 6. カーブが表示されることを確認
```

### 8.2 自動化スクリプト（オプション）

カーブのインストールとデータベース更新を自動化:

```bash
#!/bin/bash
# install_qtr_curve.sh
# Usage: ./install_qtr_curve.sh PX1V-PtPd-v18.quad

CURVE_FILE="$1"
TARGET_DIR="/Library/Printers/QTR/quadtone/QuadP700"

if [ ! -f "$CURVE_FILE" ]; then
    echo "Error: $CURVE_FILE not found"
    exit 1
fi

echo "Installing $CURVE_FILE to QuadP700..."

# コピー
sudo cp "$CURVE_FILE" "$TARGET_DIR/"

# データベース更新
echo "Updating QTR database..."
/Library/Printers/QTR/bin/quadcurves QuadP700

# キャッシュクリア
echo "Clearing QTR Print-Tool cache..."
defaults delete com.quadtonerip.QTR-Print-Tool 2>/dev/null

echo "Done! Please restart QTR Print-Tool."
```

**使用方法**:
```bash
chmod +x install_qtr_curve.sh
./install_qtr_curve.sh PX1V-PtPd-v18.quad
```

---

## 9. 他のプリンター用の設定

### 9.1 新しいプリンターの追加

SC-PX1V以外のプリンター（例: Epson P900）を追加する場合:

```bash
# 1. 対応するInstallスクリプトを実行
cd /Applications/QuadToneRIP/Profiles/P700-900-UC/
./InstallP900.command

# 2. macOSでプリンター追加（"QuadToneRIP - QuadP900"を選択）

# 3. QTR Print-Toolで確認
```

### 9.2 複数プリンターの管理

```bash
# 各プリンターは独立したディレクトリを持つ
ls /Library/Printers/QTR/quadtone/

# 出力例:
# QuadP700/   (SC-PX1V用)
# QuadP900/   (P900用)
# Quad3880/   (3880用)
```

---

## 10. まとめ

### 初期設定のチェックリスト

- [ ] QuadToneRIPをインストール
- [ ] InstallP700.commandを実行
- [ ] QuadP700ディレクトリが作成されたことを確認
- [ ] macOSシステム環境設定でプリンターを追加（QuadToneRIP - QuadP700を選択）
- [ ] QTR Print-Toolでプリンターとカーブが表示されることを確認
- [ ] テストプリントで動作確認
- [ ] カスタムカーブを配置（必要に応じて）
- [ ] データベース更新 (`quadcurves QuadP700`)
- [ ] キャッシュクリア (`defaults delete com.quadtonerip.QTR-Print-Tool`)

### カーブ追加時のチェックリスト

- [ ] .quadファイルを `/Library/Printers/QTR/quadtone/QuadP700/` にコピー
- [ ] `quadcurves QuadP700` を実行
- [ ] `defaults delete com.quadtonerip.QTR-Print-Tool` を実行
- [ ] QTR Print-Toolを再起動
- [ ] 新しいカーブが表示されることを確認

---

**関連資料**:
- [QTRカーブ最適化_完全マニュアル.md](./QTRカーブ最適化_完全マニュアル.md)
- [最適化された手順_Phase_A詳細.md](./最適化された手順_Phase_A詳細.md)
- [他の技法用トーンカーブ作成ガイド.md](./他の技法用トーンカーブ作成ガイド.md)

**作成者**: 木下大輔
**最終更新**: 2026年3月15日
