# AP2 Lab 自動アップロード機能 クイックスタートガイド

## 🚀 セットアップ（初回のみ）

### 1. Node.jsのインストール確認

```bash
node --version
npm --version
```

→ バージョンが表示されればOK
→ 表示されない場合は `brew install node` でインストール

### 2. 依存パッケージのインストール

```bash
cd "obsidian/Clippings/Alternative Process Lab/HP/admin"
npm install
```

### 3. FTP設定ファイルの作成

```bash
cp ftp-config.example.json ftp-config.json
```

`ftp-config.json` を開いて、FTPサーバー情報を入力:

```json
{
  "host": "your-ftp-server.com",
  "user": "your-username",
  "password": "your-password",
  "secure": false,
  "remotePath": "/public_html/"
}
```

## 💻 日常的な使い方

### サーバーの起動

```bash
cd "obsidian/Clippings/Alternative Process Lab/HP/admin"
npm start
```

→ ターミナルに「サーバー起動」と表示されます

### 管理画面を開く

ブラウザで以下のURLを開く:

```
http://localhost:3000/admin/event-manager-auto.html
```

### イベントの追加・更新・アップロード

1. **イベント情報を入力**
   - タイトル、種別、募集状況、開催日時、技法、説明文など

2. **「保存」ボタンをクリック**
   - 自動的に `event.html` が更新されます

3. **「FTPアップロード」ボタンをクリック**
   - 本番サイトに自動的にアップロードされます

### サーバーの停止

ターミナルで `Ctrl + C`

## 📋 作業フロー比較

### 従来（手動）: 約10分
1. 管理画面でイベント追加
2. HTML生成ボタンをクリック
3. HTMLファイルをダウンロード
4. テキストエディタで開く
5. コピー
6. event.htmlを開く
7. 貼り付け
8. 保存
9. FTPクライアントで手動アップロード

### 新方式（自動）: 約30秒
1. 管理画面でイベント追加
2. 「保存」ボタンをクリック
3. 「FTPアップロード」ボタンをクリック

## ⚠️ トラブルシューティング

### 「サーバー未起動」と表示される
→ `npm start` を実行してサーバーを起動してください

### 「FTP未設定」と表示される
→ `ftp-config.json` を作成し、FTPサーバー情報を入力してください

### ポート3000が使用中
→ `server.js` の `PORT = 3000` を別の番号（例: 3001）に変更してください

### FTP接続エラー
1. `ftp-config.json` の設定を確認
2. FTPサーバーのファイアウォール設定を確認
3. `secure: true` に変更してみる（FTPS/SFTPの場合）

## 🔒 セキュリティ注意事項

- **重要**: `ftp-config.json` は絶対にGitにコミットしないでください
- パスワードは強力なものを使用してください
- 可能であればSFTP/FTPSを使用してください

## 📝 補足

- **自動非表示機能**: イベント開催日の翌日11:59に自動的に非表示になります
- **データ保存**: イベントデータは `admin/events-data.json` に保存されます
- **バックアップ**: 定期的に `events-data.json` のバックアップを取ることをお勧めします
