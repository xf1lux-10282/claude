# Obsidian バックアップと同期設定（詳細版）

> **注**: このファイルは詳細な技術ドキュメントです。クイックスタートガイドは[ルートREADME](../README.md)を参照してください。

## 概要
このリポジトリは、iCloudに保存されたObsidianノートのバックアップとバージョン管理を行います。

## ディレクトリ構造

```
/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/
├── obsidian/           # メインのObsidianノート
│   ├── Clippings/      # クリッピング
│   ├── DailyNotes/     # 日次ノート
│   ├── Logs/           # ログ
│   ├── Projects/       # プロジェクト
│   ├── Settings/       # 設定
│   └── WORKS/          # 作業ファイル
├── github/             # GitHub関連ドキュメント
│   ├── README.md       # このファイル（詳細版）
│   ├── SETUP_GUIDE.md  # セットアップガイド
│   └── setup_github.sh # GitHubセットアップスクリプト
├── .claude/            # Claude Code設定
├── sync_to_nas.sh      # NASバックアップスクリプト
├── sync_logs/          # 同期ログ（gitignore対象）
├── NAS_ONLY_FILES_REPORT.md  # NAS専用ファイルレポート
└── README.md           # クイックスタートガイド
```

## バックアップ設定

### NASバックアップ

NASへのバックアップは、`sync_to_nas.sh` スクリプトを使用します。

**NASマウントポイント**: `/Volumes/obsidian`

#### バックアップスクリプトの実行

```bash
cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents"
./sync_to_nas.sh
```

#### 機能
- iCloudのデータを優先してNASへバックアップ
- NASにのみ存在するファイルを検出して報告（削除はしない）
- 同期ログを `sync_logs/` に保存
- `.DS_Store` などのシステムファイルを除外

#### 自動バックアップ設定（オプション）

毎日自動的にバックアップを実行する場合は、以下のコマンドでcrontabに追加できます：

```bash
# crontabエディタを開く
crontab -e

# 以下の行を追加（毎日午前2時に実行）
0 2 * * * /Users/daisukekinoshita/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/sync_to_nas.sh >> /Users/daisukekinoshita/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/sync_logs/cron.log 2>&1
```

## GitHub設定

### 初期設定

1. GitHub CLIで認証（初回のみ）:
   ```bash
   gh auth login
   ```

2. GitHubリポジトリの作成:
   ```bash
   cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents"
   gh repo create obsidian-backup --private --source=. --remote=origin
   ```

3. 初回コミットとプッシュ:
   ```bash
   git add .
   git commit -m "Initial commit: Setup backup system"
   git push -u origin master
   ```

### 日常的な使い方

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

## Claude Code WEB版での使用

### 前提条件
- GitHubリポジトリが作成されていること
- リポジトリがプライベートまたはパブリックに設定されていること

### アクセス方法

1. Claude Code WEB版にアクセス: https://claude.com/claude-code
2. GitHubアカウントで認証
3. このリポジトリを選択して作業開始

## Git設定

現在のGit設定:
- **ユーザー名**: xf1kux-10282
- **メールアドレス**: daisuke10282@me.com
- **LFS**: 有効

## 注意事項

### バックアップの優先順位
1. **iCloud**: メインストレージ（最優先）
2. **NAS**: バックアップストレージ（iCloudから同期）
3. **GitHub**: バージョン管理とリモートバックアップ

### 同期の方向
- iCloud → NAS（一方向同期）
- iCloud ↔ GitHub（双方向、ただし通常はiCloud→GitHub）

### 除外ファイル
`.gitignore` により以下のファイルは Git管理から除外されています:
- システムファイル（.DS_Store等）
- 同期ログ（sync_logs/）
- Obsidianのワークスペースキャッシュ
- バックアップファイル

## トラブルシューティング

### NASがマウントされていない場合

```bash
# NASのマウント状態を確認
mount | grep obsidian

# Finderから手動でマウント
# サーバーに接続: smb://XF1LUX_NAS/obsidian
```

### Git認証エラーの場合

```bash
# 認証状態を確認
gh auth status

# 再認証
gh auth login
```

## 更新履歴

- 2025-12-04: 初期設定完了
  - NASバックアップスクリプト作成
  - .gitignore設定
  - GitHub CLI インストール
  - README作成
