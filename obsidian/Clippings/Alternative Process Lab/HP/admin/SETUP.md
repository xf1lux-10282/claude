# AP2 Lab 自動アップロード機能 セットアップガイド

## 概要

このシステムを使うと、イベント情報を追加・編集すると自動的にHTMLを生成してFTPサーバーにアップロードできます。

## 必要なもの

- Node.js (バージョン14以上)
- FTPサーバーの接続情報

## セットアップ手順

### 1. Node.jsのインストール

まだインストールしていない場合:

```bash
# Homebrewを使ってインストール（Mac）
brew install node

# インストール確認
node --version
npm --version
```

### 2. 依存パッケージのインストール

```bash
cd "obsidian/Clippings/Alternative Process Lab/HP/admin"
npm install
```

### 3. FTP設定ファイルの作成

`ftp-config.example.json` をコピーして `ftp-config.json` を作成:

```bash
cp ftp-config.example.json ftp-config.json
```

`ftp-config.json` を編集してFTPサーバー情報を入力:

```json
{
  "host": "ftp.example.com",
  "user": "your-username",
  "password": "your-password",
  "secure": false,
  "remotePath": "/public_html/"
}
```

**注意:** `ftp-config.json` は `.gitignore` に含まれているため、Gitにコミットされません。

### 4. サーバーの起動

```bash
npm start
```

または、開発モード（ファイル変更時に自動再起動）:

```bash
npm run dev
```

### 5. 管理画面を開く

ブラウザで以下のURLを開く:

```
http://localhost:3000/admin/event-manager-auto.html
```

## 使い方

### イベントの追加・編集

1. 管理画面でイベント情報を入力
2. 「保存」ボタンをクリック
3. 自動的に `event.html` が更新される
4. 「FTPアップロード」ボタンをクリック
5. 自動的にサーバーにアップロード

### 自動アップロードの仕組み

```
イベント追加・編集
    ↓
データ保存 (events-data.json)
    ↓
event.html 自動生成
    ↓
FTPアップロード（ボタンクリック）
    ↓
本番サイトに反映
```

## API エンドポイント

### イベント一覧取得
```
GET http://localhost:3000/api/events
```

### イベント保存
```
POST http://localhost:3000/api/events
Content-Type: application/json

[events array]
```

### FTPアップロード
```
POST http://localhost:3000/api/upload
```

### FTP接続テスト
```
GET http://localhost:3000/api/test-ftp
```

## トラブルシューティング

### ポート3000が使用中

別のポートを使用する場合、`server.js` の `PORT` を変更:

```javascript
const PORT = 3001; // 任意のポート番号
```

### FTP接続エラー

1. `ftp-config.json` の設定を確認
2. FTPサーバーのファイアウォール設定を確認
3. パッシブモードが必要な場合は `secure: true` を試す

### アップロード先パスの確認

`remotePath` を正しく設定:

```json
{
  "remotePath": "/public_html/"  // ← サーバーのドキュメントルート
}
```

## セキュリティ注意事項

- `ftp-config.json` は絶対にGitにコミットしない
- パスワードは強力なものを使用
- 可能であればSFTP/FTPSを使用

## 従来の手動方式との比較

### 従来（手動）
1. 管理画面でイベント追加
2. 「HTML生成」ボタンをクリック
3. HTMLファイルをダウンロード
4. テキストエディタで開く
5. コピー
6. event.htmlを開く
7. 貼り付け
8. 保存
9. FTPクライアントで手動アップロード

### 新方式（自動）
1. 管理画面でイベント追加
2. 「保存」ボタンをクリック → HTML自動生成
3. 「FTPアップロード」ボタンをクリック → 自動アップロード

**作業時間: 約10分 → 約30秒**
