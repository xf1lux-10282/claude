# セットアップガイド

## 完了した設定

### ✅ 1. NASバックアップシステム
- **場所**: `/Volumes/obsidian`
- **スクリプト**: `sync_to_nas.sh`
- **機能**: iCloudからNASへの一方向同期
- **実行方法**:
  ```bash
  cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents"
  ./sync_to_nas.sh
  ```

### ✅ 2. Git設定
- `.gitignore` ファイルを作成済み
- システムファイルとログファイルを除外
- ローカルGitリポジトリを初期化済み

### ✅ 3. GitHub CLI インストール
- `gh` コマンドが使用可能

## 次のステップ（手動で実行）

### ステップ 1: GitHub認証

ターミナルで以下のコマンドを実行してください：

```bash
gh auth login
```

プロンプトに従って選択：
1. **What account do you want to log into?** → `GitHub.com`
2. **What is your preferred protocol for Git operations?** → `HTTPS` または `SSH`（推奨: HTTPS）
3. **Authenticate Git with your GitHub credentials?** → `Yes`
4. **How would you like to authenticate GitHub CLI?** → `Login with a web browser`

その後、表示されるワンタイムコードをコピーして、ブラウザで認証を完了してください。

### ステップ 2: GitHubリポジトリのセットアップ

認証が完了したら、以下のスクリプトを実行してください：

```bash
cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents"
./setup_github.sh
```

このスクリプトは以下を自動実行します：
- プライベートリポジトリ `obsidian-backup` の作成
- 初回コミットの作成
- GitHubへのプッシュ

### ステップ 3: Claude Code WEB版での作業

1. **Claude Code WEB版にアクセス**:
   https://claude.com/claude-code

2. **GitHubアカウントで認証**

3. **リポジトリを選択**:
   - あなたのGitHubアカウントから `obsidian-backup` リポジトリを選択

4. **作業開始**:
   - Claude Code WEB版でファイルの編集、追加、削除が可能
   - 変更は自動的にコミット可能

## トラブルシューティング

### GitHub認証でエラーが出る場合

```bash
# 既存の認証をクリア
gh auth logout

# 再度認証
gh auth login
```

### リポジトリ作成でエラーが出る場合

手動でリポジトリを作成する場合：

1. GitHub.comにアクセス
2. 新しいリポジトリを作成（名前: `obsidian-backup`、プライベート）
3. 以下のコマンドでリモートを追加：

```bash
cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents"

# あなたのGitHubユーザー名に置き換えてください
git remote add origin https://github.com/YOUR_USERNAME/obsidian-backup.git

git add .
git commit -m "Initial commit"
git branch -M main
git push -u origin main
```

### NASがマウントされていない場合

```bash
# Finderで「移動」→「サーバへ接続」
# または以下のコマンドを実行：
open "smb://daisuke10282@XF1LUX_NAS/obsidian"
```

## 定期バックアップの設定（オプション）

NASへの自動バックアップを設定する場合：

```bash
# crontabエディタを開く
crontab -e

# 以下を追加（毎日午前2時に実行）
0 2 * * * "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/sync_to_nas.sh" >> "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/sync_logs/cron.log" 2>&1
```

または、macOSのLaunchAgentを使用する方法もあります（より推奨）。

## ファイル一覧

- `README.md` - メインのドキュメント
- `SETUP_GUIDE.md` - このファイル（セットアップ手順）
- `sync_to_nas.sh` - NASバックアップスクリプト
- `setup_github.sh` - GitHubリポジトリセットアップスクリプト
- `.gitignore` - Git除外設定

## 現在の状態

✅ VSCode設定確認完了
✅ iCloudとNAS同期設定完了
✅ ディレクトリ構造確認完了
✅ NASバックアップスクリプト作成完了
✅ Git除外設定完了
✅ GitHub CLI インストール完了
✅ GitHub認証完了（2025-12-04）
✅ GitHubリポジトリ作成完了（obsidian-backup）
✅ obsidianディレクトリをGitHubにプッシュ完了（279 Markdownファイル、63MB）
✅ Claude Code WEB版設定完了
✅ Claude Code WEB版での動作確認完了

## セットアップ完了日時

**2025年12月4日 14:30頃**

### 完了した作業の詳細

1. **NASバックアップ設定**
   - iCloud → NAS の一方向同期
   - NASにのみ存在するファイルの検出・報告機能
   - sync_to_nas.sh スクリプト作成

2. **GitHub設定**
   - リポジトリ: `xf1kux-10282/obsidian-backup` (private)
   - ブランチ: `master`
   - 認証方法: GitHub CLI (gh auth login)
   - 初回プッシュ: 541ファイル

3. **Claude Code WEB版**
   - URL: https://claude.com/claude-code
   - リポジトリ接続完了
   - obsidianディレクトリアクセス確認済み
   - ファイル編集・閲覧可能

4. **Git除外設定 (.gitignore)**
   - 画像ファイル（jpg, png等）除外
   - PDFファイル除外
   - 動画・音声ファイル除外
   - WEBディレクトリ除外
   - システムファイル除外

## 今後の運用方法

### デスクトップでの作業
```bash
cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents"

# 変更を確認
git status

# 変更をコミット
git add .
git commit -m "Update notes"

# GitHubにプッシュ
git push
```

### WEB版での作業
1. https://claude.com/claude-code にアクセス
2. `obsidian-backup` リポジトリを選択
3. Claude に指示を出してファイルを編集
4. 変更は自動的にコミット・プッシュされる

### WEB版からデスクトップへの同期
```bash
cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents"

# 最新の変更を取得
git pull
```

### NASへのバックアップ
```bash
cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents"
./sync_to_nas.sh
```

## サポート

問題が発生した場合は、以下のコマンドで状態を確認してください：

```bash
# Git状態
git status

# GitHub認証状態
gh auth status

# NASマウント状態
mount | grep obsidian

# ファイル一覧
ls -la "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents"
```
