# P9550_QTR 拡張PPDインストール手順

## 概要
P9550_QTR.ppdに豊富な用紙サイズと給紙オプションを追加した拡張版PPDです。

## 追加された用紙サイズ

### 元の設定
- A4
- Letter

### 追加した用紙サイズ
- Tabloid（11x17インチ）
- 13x19（A3ノビ相当）
- 13x44（ロール紙用）
- 4x6
- 5x7
- 7x10
- 8x10
- 11x14
- A6
- A5
- A4（元からあり）
- A3
- A3+（A3ノビ）

### 追加した給紙オプション
- Sheet Feed（シート給紙）
- Roll Feed（ロール給紙）
- Roll - Save Paper（ロール・用紙節約）
- Front - Fine Art（前面・ファインアート紙）
- Front - Poster Board（前面・ポスターボード）
- Front - No Eject Roller（前面・排紙ローラーなし）

## インストール手順

### 1. 現在のPPDをバックアップ

```bash
sudo cp /etc/cups/ppd/P9550_QTR.ppd /etc/cups/ppd/P9550_QTR.ppd.backup_$(date +%Y%m%d)
```

### 2. 拡張PPDをインストール

```bash
sudo cp "obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/P9500設定/P9550_QTR_expanded.ppd" \
  /etc/cups/ppd/P9550_QTR.ppd
```

### 3. PPDのパーミッションを設定

```bash
sudo chmod 644 /etc/cups/ppd/P9550_QTR.ppd
sudo chown root:_lp /etc/cups/ppd/P9550_QTR.ppd
```

### 4. CUPSを再起動

```bash
sudo launchctl stop org.cups.cupsd
sudo launchctl start org.cups.cupsd
```

### 5. 設定を確認

```bash
lpoptions -p P9550_QTR -l | grep -E "PageSize|ripFeed"
```

**期待される出力**:
```
PageSize/Media Size: Letter Tabloid 13x19 13x44 4x6 5x7 7x10 8x10 11x14 A6 A5 *A4 A3 A3Plus
ripFeed/Paper Feed: *Sheet Roll RollSave FrontFineArt FrontPoster FrontNoEject
```

## 使用例

### A3サイズで印刷
```bash
lpr -P P9550_QTR -o PageSize=A3 画像ファイル.tif
```

### 13x19（A3ノビ）で印刷
```bash
lpr -P P9550_QTR -o PageSize=13x19 画像ファイル.tif
```

### ロール紙で印刷
```bash
lpr -P P9550_QTR -o PageSize=A4 -o ripFeed=Roll 画像ファイル.tif
```

### ファインアート紙（前面給紙）で印刷
```bash
lpr -P P9550_QTR -o PageSize=A4 -o ripFeed=FrontFineArt 画像ファイル.tif
```

## 注意事項

1. **マージン設定**: QuadP700から移植したImageableArea（マージン9pt）を使用しています。実際のP9500の物理マージンと異なる場合は調整が必要です。

2. **給紙オプション**: P9500の実際の給紙機構に合わせて、必要なオプションのみを使用してください。

3. **PPD更新後**: システム設定の「プリンタとスキャナ」でP9550_QTRの設定を開き、用紙サイズが正しく表示されるか確認してください。

## トラブルシューティング

### 用紙サイズが増えない場合

```bash
# PPDの構文エラーをチェック
cupstestppd /etc/cups/ppd/P9550_QTR.ppd

# CUPSのキャッシュをクリア
sudo rm -rf /var/cache/cups/*
sudo launchctl stop org.cups.cupsd
sudo launchctl start org.cups.cupsd
```

### 元に戻す場合

```bash
# バックアップから復元
sudo cp /etc/cups/ppd/P9550_QTR.ppd.backup_YYYYMMDD /etc/cups/ppd/P9550_QTR.ppd
sudo launchctl stop org.cups.cupsd
sudo launchctl start org.cups.cupsd
```

## 関連ファイル

- 拡張PPD: `obsidian/Clippings/写真家活動/技法探求/デジネガ/QTR/P9500設定/P9550_QTR_expanded.ppd`
- 元のPPD: `/etc/cups/ppd/P9550_QTR.ppd`
- 参考元: `/etc/cups/ppd/QuadP700.ppd`

## 今後の拡張案

1. **カスタム用紙サイズ**: 特殊サイズの追加
2. **用紙タイプ**: 光沢紙、マット紙などのプリセット
3. **マージン調整**: より詳細なマージン設定

