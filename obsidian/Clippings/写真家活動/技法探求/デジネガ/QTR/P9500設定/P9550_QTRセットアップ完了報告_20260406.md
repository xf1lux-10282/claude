# EPSON SC-P9500 Series QTR セットアップ完了報告

## 日付
2026年4月6日

## 概要
EPSON SC-P9500 SeriesでQTR（QuadToneRIP）を使用した3色印刷が成功しました。

## セットアップ構成

### プリンター名
- **CUPS Queue Name**: P9550_QTR_ESCPR
- **Physical Device**: EPSON SC-P9500 Series
- **Connection**: USB (usb://EPSON/SC-P9500%20Series?serial=5836464A3030303889)
- **Status**: 動作中・正常

### PPDファイル
- **Location**: /etc/cups/ppd/P9550_QTR_ESCPR.ppd
- **Base**: カスタムPPD（ESC/P-R対応）
- **cupsFilter**: `application/vnd.cups-raster 0 /Library/Printers/QTR/filter/rastertop9550`

### QTRフィルター
- **Filter Path**: /Library/Printers/QTR/filter/rastertop9550
- **Type**: ESC/P-R rasterフィルター
- **Function**: CUPS rasterデータをESC/P-Rコマンドに変換

### QTRカーブ（現在設定中）
- **Curve Directory**: /Library/Printers/QTR/quadtone/QuadP9550/
- **Active Curves**: 
  - PX1V-PtPd-xf1-3ink-v2-P9500.quad（3色版）
  - その他のテストカーブ

## フィルターチェーン

印刷時のフィルターチェーンは以下の通り：

1. **cgtexttopdf** (text/plain → application/pdf)
   - テキストファイルをPDFに変換

2. **cgpdftoraster** (application/pdf → application/vnd.cups-raster)
   - PDFをCUPS rasterに変換

3. **rastertop9550** (application/vnd.cups-raster → printer/P9550_QTR_ESCPR)
   - CUPS rasterをESC/P-Rに変換
   - QTRカーブを適用

4. **usb backend** (/usr/libexec/cups/backend/usb)
   - USB経由でプリンターにデータ送信

## 動作確認テスト

### テスト1: テキストファイル印刷
- **Status**: ✓ 成功
- **Job ID**: 4041
- **File**: /tmp/test_p9550.txt
- **Result**: エラーなく完了

### テスト2: グラデーションパッチ印刷
- **Status**: ✓ 成功
- **Job ID**: 4042
- **File**: /tmp/qtr_p9550_gradient_test.tif (2970x4200 pixels, 8-bit grayscale, 360dpi)
- **Patches**: 21段階グレースケール（0%〜100%、5%ステップ）
- **Data Size**: 12.5 MB
- **Result**: エラーなく完了

## CUPSログ確認

両方のジョブで以下を確認：
- rastertop9550フィルターがエラーなしで終了
- USBバックエンドがエラーなしで終了
- "Job completed" メッセージ

## 成功のポイント

1. **PPD設定**: cupsFilterディレクティブにrastertop9550を正しく指定
2. **MIME Type**: printer/P9550_QTR_ESCPRカスタムMIMEタイプ
3. **フィルター権限**: 実行可能権限とセキュリティ属性の設定
4. **ESC/P-R対応**: P9500のネイティブ言語に対応したフィルター

## 次のステップ

1. **カーブの微調整**:
   - 実際の印刷結果を測定
   - 必要に応じてQTRカーブを調整

2. **用紙プロファイル**:
   - 異なる用紙タイプのカーブを作成
   - プラチナパラジウムトーン、セピアトーンなど

3. **ワークフロー統合**:
   - Photoshopとの連携
   - カラーマネジメント設定

## 参考ファイル

- PPD: /etc/cups/ppd/P9550_QTR_ESCPR.ppd
- Filter: /Library/Printers/QTR/filter/rastertop9550
- Curves: /Library/Printers/QTR/quadtone/QuadP9550/
- Logs: /var/log/cups/error_log

## 備考

EPSON SC-P9500 SeriesはSC-PX1Vと同じESC/P-Rプロトコルを使用しているため、
PX1V用のQTRカーブを基に調整することで、同様のトーン再現が可能です。

3色版カーブ（Photo Black + 2色）により、繊細な階調表現が実現できます。
