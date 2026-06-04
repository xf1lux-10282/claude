# P9550 印刷拡大問題の分析と解決策

## 日付
2026年4月6日

## 問題
- **症状**: 印刷物が拡大されて、一部分だけがプリントされる
- **プリンター**: EPSON SC-P9500 Series (P9550_QTR)

## 原因分析

### 1. 解像度のミスマッチ

**作成した画像**:
- サイズ: 2970 x 4200 pixels
- 解像度: 360 dpi
- 物理サイズ: 210mm x 297mm (A4)

**PPD設定**:
- PageSize: 595 x 842 points (72dpi基準のポイント単位)
- HWResolution: 720 x 720 dpi
- ImageableArea: "0 0 595 842"

**スケール比**:
- 画像 ÷ PPD = 2970 ÷ 595 = **4.99倍**
- これが「5倍に拡大されて一部分だけ印刷」の原因

### 2. PPDとCUPS Rasterの関係

PPDファイルの数値はPostScriptポイント単位（72dpi）で記述されます。
しかし、実際のCUPS Rasterは異なる解像度で生成されることがあります。

**フィルターチェーン**:
1. cgtexttopdf: テキスト → PDF
2. cgpdftoraster: PDF → CUPS Raster
3. rastertop9550: CUPS Raster → ESC/P-R

問題は **cgpdftoraster** がどの解像度でRasterを生成するかです。

## 解決策の候補

### 方法1: 解像度をPPDに明示的に指定

印刷時にrastertop9550フィルターに渡される解像度を確認し、
画像の解像度と一致させる。

**テスト済み**:
- 72dpi画像: `/tmp/qtr_p9550_test_72dpi.tif` (595x842 pixels)
- 360dpi画像: `/tmp/qtr_p9550_gradient_test.tif` (2970x4200 pixels)

### 方法2: lprオプションで解像度を指定

```bash
lpr -P P9550_QTR -o Resolution=2880 -o media=A4 画像ファイル
```

### 方法3: cupsRasterInterpret設定の確認

PPDに以下の設定があるか確認:
```
*cupsFilter2: "image/png image/png 0 -"
```

### 方法4: rastertop9550フィルターのデバッグ

フィルターが受け取るCUPS Rasterの解像度を確認:
```bash
# CUPSフィルターのstderrをログに出力
tail -f /var/log/cups/error_log | grep rastertop9550
```

## 次回プリンター接続時の検証手順

### ステップ1: ジョブキューのクリア

```bash
# 保留中のジョブを全削除
cancel -a P9550_QTR
```

### ステップ2: プリンター状態の確認

```bash
lpstat -p P9550_QTR
# 「オフライン」の場合はプリンター電源とUSB接続を確認
```

### ステップ3: 72dpi画像でテスト

```bash
lpr -P P9550_QTR -o media=A4 -o PageSize=A4 /tmp/qtr_p9550_test_72dpi.tif
```

**期待結果**: A4用紙全体に収まる（拡大されない）

### ステップ4: 360dpi画像でテスト（解像度明示）

```bash
lpr -P P9550_QTR -o media=A4 -o Resolution=2880 /tmp/qtr_p9550_gradient_test.tif
```

**期待結果**: A4用紙全体に収まる

### ステップ5: ログで解像度を確認

```bash
tail -200 /var/log/cups/error_log | grep "Job.*argv\[5\]"
```

argv[5]に含まれる解像度情報を確認。

### ステップ6: CUPS Rasterヘッダーをダンプ

フィルターチェーンの途中でRasterファイルを保存してヘッダーを確認:

```bash
# cupsfilterコマンドでフィルター処理をシミュレート
cupsfilter -p /etc/cups/ppd/P9550_QTR.ppd \
  -m printer/P9550_QTR \
  /tmp/qtr_p9550_gradient_test.tif > /tmp/test.raster 2>&1

# Rasterヘッダーを確認
rastertopwg < /tmp/test.raster 2>&1 | head -50
```

## QuadP700との比較

QuadP700 (PX1V) では正常に動作しているため、以下を比較:

1. **PPD設定の違い**:
```bash
diff /etc/cups/ppd/QuadP700.ppd /etc/cups/ppd/P9550_QTR.ppd
```

2. **フィルター設定の違い**:
```bash
grep cupsFilter /etc/cups/ppd/QuadP700.ppd
grep cupsFilter /etc/cups/ppd/P9550_QTR.ppd
```

## 参考情報

### 作成したテストファイル
- `/tmp/qtr_p9550_test_72dpi.tif` - 72dpi, 595x842px (PPD一致)
- `/tmp/qtr_p9550_gradient_test.tif` - 360dpi, 2970x4200px (実用的なサイズ)

### PPDファイルの場所
- `/etc/cups/ppd/P9550_QTR.ppd`

### ログファイル
- `/var/log/cups/error_log`

## 暫定的な結論

**仮説**: cgpdftorasterが画像の埋め込み解像度（360dpi）を無視し、
PPDのPageSize（72dpi基準）を基にRasterを生成している可能性。

**次のアクション**:
1. 72dpi画像での印刷結果を確認（正常に収まるはず）
2. 360dpi画像で`-o Resolution=2880`オプションを付けて印刷
3. 両者の結果を比較して、解像度指定の効果を確認

## 備考

QTRでの実用的な印刷には360dpi以上の画像が必要。
72dpiでは階調が粗くなりすぎるため、解像度指定オプションの
有効性確認が最優先。
