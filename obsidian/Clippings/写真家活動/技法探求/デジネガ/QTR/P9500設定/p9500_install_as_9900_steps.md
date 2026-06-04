# P9500をQuad9900として設定する手順

## 準備完了

✓ Quad9900.ppd.gz が存在: `/Library/Printers/PPDs/Contents/Resources/Quad9900.ppd.gz`
✓ Quad9900カーブが23個存在: `/Library/Printers/QTR/quadtone/Quad9900/`
✓ P9500が接続中（USB）

## 実行手順

### ステップ1: P9500のUSBデバイスURIを確認

```bash
lpinfo -v | grep -i "p9500\|9500"
```

**期待される出力**:
```
usb://EPSON/SC-P9500%20Series?serial=5836464A3030303889
```

### ステップ2: 新しいプリンターキューを作成

```bash
lpadmin -p Quad9900_for_P9500 \
  -v "usb://EPSON/SC-P9500%20Series?serial=5836464A3030303889" \
  -P /Library/Printers/PPDs/Contents/Resources/Quad9900.ppd.gz \
  -L "EPSON SC-P9500 (as Quad9900)" \
  -E
```

**パラメータ説明**:
- `-p Quad9900_for_P9500`: プリンター名
- `-v`: USBデバイスURI（ステップ1で確認したもの）
- `-P`: Quad9900のPPD
- `-L`: 場所/説明
- `-E`: 有効化

### ステップ3: デフォルトプリンターに設定（任意）

```bash
lpadmin -d Quad9900_for_P9500
```

### ステップ4: インストールを確認

```bash
# プリンターが追加されたか確認
lpstat -p Quad9900_for_P9500

# 利用可能なオプションを確認
lpoptions -p Quad9900_for_P9500 -l | head -50
```

**期待される出力**:
```
プリンタQuad9900_for_P9500は待機中です。...
PageSize/Media Size: Letter Tabloid 13x19 17x22 13x44 4x6 5x7 ...
ripCurve1/QuadTone RIP Curve 1: *- (None)
ripFeed/Feed Mode: *Sheet Roll RollSave ...
Resolution/Resolution: 1440dpi *2880 ...
```

### ステップ5: カーブを確認

quadtoneprintフィルターは自動的に`Quad9900`ディレクトリからカーブを読み込みます。

```bash
# カーブファイルを確認
ls -1 /Library/Printers/QTR/quadtone/Quad9900/*.quad
```

**利用可能なカーブ**（23個）:
- UCmk-HanPhotoRag-Cool
- UCmk-HanPhotoRag-Warm
- UCmk-HanPhotoRag-Sepia
- UCmk-HanPhotoRag-Coolse
- （以下省略、合計23個）

### ステップ6: テスト印刷

#### テスト1: シンプルなテキスト

```bash
cat > /tmp/test_9900.txt << 'TESTEOF'
Quad9900 for P9500 Test
=======================
Date: $(date)
Printer: Quad9900_for_P9500
TESTEOF

lpr -P Quad9900_for_P9500 -o PageSize=A4 /tmp/test_9900.txt
```

#### テスト2: グラデーションパッチ（カーブ指定）

```bash
# 72dpiテスト画像を使用
lpr -P Quad9900_for_P9500 \
  -o PageSize=A4 \
  -o ripCurve1=UCmk-HanPhotoRag-Cool \
  /tmp/qtr_p9550_test_72dpi.tif
```

#### テスト3: 360dpi画像（解像度明示）

```bash
lpr -P Quad9900_for_P9500 \
  -o PageSize=A4 \
  -o Resolution=2880 \
  -o ripCurve1=UCmk-HanPhotoRag-Cool \
  /tmp/qtr_p9550_gradient_test.tif
```

### ステップ7: ログ確認

```bash
# 印刷ジョブの状態を確認
lpq -P Quad9900_for_P9500

# エラーログを確認
tail -50 /var/log/cups/error_log | grep -i "9900\|error"
```

## トラブルシューティング

### 問題1: カーブが見つからない

**症状**: `cannot open curve file` エラー

**原因**: quadtoneprintが`Quad9900`ディレクトリを参照していない

**解決策**:
```bash
# PPDのModelNameを確認
grep "ModelName" /etc/cups/ppd/Quad9900_for_P9500.ppd

# 出力: *ModelName:     "escp2-9900"
# これにより /Library/Printers/QTR/quadtone/Quad9900/ が参照される
```

### 問題2: 解像度ミスマッチ

**症状**: 画像が拡大される

**解決策**: `-o Resolution=2880` を明示的に指定

### 問題3: デバイスが見つからない

**症状**: `Unable to locate printer`

**解決策**:
```bash
# P9500が接続されているか確認
lpinfo -v | grep P9500

# USBを再接続
```

## カーブの選択ガイド

### マット紙用（UCmk系）

| カーブ | 用紙 | トーン | 推奨用途 |
|--------|------|--------|----------|
| UCmk-HanPhotoRag-Cool | Photo Rag | クール | ファインアート、ニュートラル |
| UCmk-HanPhotoRag-Warm | Photo Rag | ウォーム | ポートレート |
| UCmk-HanPhotoRag-Sepia | Photo Rag | セピア | ヴィンテージ調 |
| UCmk-EpsEnhMatte-Cool | Enhanced Matte | クール | 展示用 |
| UCmk-PmJetAlpha-Cool1 | PremierArt Alpha | クール | デジタルネガ |

### 光沢紙用（UCpk系）

| カーブ | 用紙 | トーン | 推奨用途 |
|--------|------|--------|----------|
| UCpk-HmGloss-neutral | Gloss | ニュートラル | 光沢プリント |
| UCpk-HmGloss-warm | Gloss | ウォーム | 温かみのある仕上がり |
| UCpk-raw-neutral | 汎用 | ニュートラル | 光沢系全般 |

## 成功の確認

✓ プリンターキューが作成された
✓ 用紙サイズが豊富（A0〜A6、各種インチサイズ）
✓ カーブが23個利用可能
✓ テスト印刷がエラーなく完了
✓ 画像が正しいサイズで印刷される

## 次のステップ

1. **各カーブをテスト**: 用紙とトーンの組み合わせを試す
2. **解像度の最適化**: 2880dpiでの印刷品質を確認
3. **デジタルネガ作成**: QTR-Linearize-Dataでキャリブレーション
4. **ワークフロー確立**: Photoshopからの印刷手順を標準化

## 従来のP9550_QTRとの比較

| 項目 | P9550_QTR（手動） | Quad9900_for_P9500 |
|------|-------------------|-------------------|
| 設定時間 | 1時間以上 | 5分 |
| 用紙サイズ | 2種類 | 30種類以上 |
| カーブ | 1個 | 23個 |
| 解像度問題 | あり（要調整） | なし |
| 動作保証 | 不明 | 高い |

**結論**: Quad9900のPPDを使う方が圧倒的に優れています。
