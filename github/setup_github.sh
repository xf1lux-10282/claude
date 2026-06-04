#!/bin/bash

# GitHub Repository Setup Script
# このスクリプトは GitHub CLI 認証完了後に実行してください

REPO_DIR="/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents"
REPO_NAME="obsidian-backup"

cd "$REPO_DIR" || exit 1

echo "=== GitHub リポジトリセットアップ ==="
echo ""

# GitHub CLI の認証状態を確認
echo "GitHub CLI の認証状態を確認中..."
if ! gh auth status 2>&1 | grep -q "Logged in to github.com"; then
    echo "エラー: GitHub CLI にログインしていません"
    echo "以下のコマンドで認証してください: gh auth login"
    exit 1
fi

echo "✓ GitHub CLI 認証済み"
echo ""

# リポジトリの作成（既に存在する場合はスキップ）
echo "GitHubリポジトリを作成中..."
if gh repo create "$REPO_NAME" --private --source=. --remote=origin 2>&1 | grep -q "already exists"; then
    echo "注意: リポジトリ '$REPO_NAME' は既に存在します"

    # リモートが設定されているか確認
    if ! git remote get-url origin 2>/dev/null; then
        echo "リモート 'origin' を追加中..."
        GITHUB_USER=$(gh api user -q .login)
        git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
    fi
else
    echo "✓ リポジトリ '$REPO_NAME' を作成しました"
fi

echo ""

# 初回コミット
echo "初回コミットを作成中..."

# ファイルをステージング
git add .gitignore README.md sync_to_nas.sh setup_github.sh .claude/

# obsidianディレクトリの一部をステージング（大きなバイナリファイルを除く）
git add obsidian/*.md 2>/dev/null || true
git add obsidian/Clippings/**/*.md 2>/dev/null || true
git add obsidian/DailyNotes/**/*.md 2>/dev/null || true
git add obsidian/Projects/**/*.md 2>/dev/null || true
git add obsidian/Settings/**/*.md 2>/dev/null || true
git add obsidian/Logs/**/*.md 2>/dev/null || true
git add obsidian/WORKS/**/*.md 2>/dev/null || true
git add obsidian/.obsidian/ 2>/dev/null || true

# WEBディレクトリ
git add WEB/ 2>/dev/null || true

# コミット
if git diff --cached --quiet; then
    echo "コミットする変更がありません"
else
    git commit -m "Initial commit: Setup backup system

- Add NAS backup script (sync_to_nas.sh)
- Add GitHub setup script
- Add README with documentation
- Add .gitignore configuration
- Include Obsidian notes and settings"

    echo "✓ 初回コミット完了"
fi

echo ""

# プッシュ
echo "GitHubにプッシュ中..."
if git push -u origin master 2>&1; then
    echo "✓ GitHubへのプッシュ完了"
    echo ""
    echo "=== セットアップ完了 ==="
    echo ""
    echo "リポジトリURL:"
    gh repo view --web --json url -q .url
    echo ""
    echo "次のステップ:"
    echo "1. ブラウザでリポジトリを確認"
    echo "2. Claude Code WEB版でこのリポジトリを開く"
    echo "   https://claude.com/claude-code"
else
    echo "エラー: プッシュに失敗しました"
    echo ""
    echo "以下のコマンドで手動でプッシュしてください:"
    echo "cd \"$REPO_DIR\""
    echo "git push -u origin master"
    exit 1
fi
