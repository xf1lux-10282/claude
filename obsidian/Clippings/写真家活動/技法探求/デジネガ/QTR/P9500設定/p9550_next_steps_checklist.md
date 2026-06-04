# P9550 次回プリンター接続時のチェックリスト

## 事前準備（今回完了済み）

- [x] テスト用72dpi画像作成 (`/tmp/qtr_p9550_test_72dpi.tif`)
- [x] テスト用360dpi画像作成 (`/tmp/qtr_p9550_gradient_test.tif`)
- [x] 問題分析ドキュメント作成

## 次回プリンター接続時の作業

### 1. プリンター準備
- [ ] プリンター電源ON
- [ ] USB接続確認
- [ ] 用紙セット（A4、できればQTR用の半光沢紙）

### 2. 保留ジョブのクリア
```bash
cancel -a P9550_QTR
lpstat -p P9550_QTR  # オンライン状態を確認
```

### 3. テスト1: 72dpi画像（PPDと解像度一致）
```bash
lpr -P P9550_QTR -o media=A4 -o PageSize=A4 /tmp/qtr_p9550_test_72dpi.tif
```
- [ ] 印刷実行
- [ ] 結果: A4全体に収まっているか？
- [ ] メモ: ___________________________________

### 4. テスト2: 360dpi画像（解像度指定なし）
```bash
lpr -P P9550_QTR -o media=A4 -o PageSize=A4 /tmp/qtr_p9550_gradient_test.tif
```
- [ ] 印刷実行
- [ ] 結果: 拡大されて一部だけか？（問題再現）
- [ ] メモ: ___________________________________

### 5. テスト3: 360dpi画像（解像度明示）
```bash
lpr -P P9550_QTR -o media=A4 -o Resolution=2880 /tmp/qtr_p9550_gradient_test.tif
```
- [ ] 印刷実行
- [ ] 結果: A4全体に収まっているか？
- [ ] メモ: ___________________________________

### 6. ログ確認
```bash
# 最新ジョブのargv[5]を確認（解像度情報が含まれる）
tail -500 /var/log/cups/error_log | grep "argv\[5\]" | tail -3
```
- [ ] 解像度情報を記録
- [ ] メモ: ___________________________________

### 7. QuadP700との比較（参考）
```bash
# QuadP700で同じ360dpi画像を印刷
lpr -P QuadP700 -o media=A4 /tmp/qtr_p9550_gradient_test.tif
```
- [ ] 印刷実行
- [ ] 結果: 正常に収まるか？
- [ ] メモ: ___________________________________

## 判定基準

### 成功パターン
- テスト1 (72dpi): ✓ 収まる
- テスト2 (360dpi 指定なし): ✗ 拡大される
- テスト3 (360dpi Resolution指定): ✓ 収まる

→ **解決策**: 常に `-o Resolution=2880` を指定

### 問題パターン
- テスト1,2,3すべてで拡大される
→ PPDファイルの根本的な問題。QuadP700のPPDと詳細比較が必要

### 予想外パターン
- テスト2で正常に収まる
→ 問題が再現しない。前回の印刷条件を再確認

## 次のステップ（テスト結果により分岐）

### ケースA: Resolution指定で解決
1. PPDにデフォルト解像度を追加
2. QTR印刷時の標準手順にResolution指定を含める
3. ドキュメント更新

### ケースB: 解決しない
1. QuadP700とP9550_QTRのPPDを詳細比較
2. rastertop9550フィルターのソースコード確認
3. CUPS Rasterのヘッダーダンプで解像度確認

## 関連ファイル

- 分析ドキュメント: `obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/P9500設定/p9550_printing_scale_issue_analysis.md`
- PPD: `/etc/cups/ppd/P9550_QTR.ppd`
- ログ: `/var/log/cups/error_log`
