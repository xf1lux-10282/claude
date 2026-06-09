#!/bin/bash

# 自動Git コミット＆プッシュスクリプト
# 使用方法: ./auto_commit.sh [コミットメッセージ（オプション）]

set -e

# 作業ディレクトリ
WORK_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$WORK_DIR"

# Gitリポジトリかチェック
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "⚠ Gitリポジトリではありません"
    exit 1
fi

# 変更があるかチェック
if git diff-index --quiet HEAD -- 2>/dev/null; then
    echo "✓ コミットする変更はありません"
    exit 0
fi

# 現在の日時を取得
CURRENT_DATETIME=$(date "+%Y年%m月%d日 %A %H:%M")

# コミットメッセージを取得（引数がある場合はそれを使用、なければデフォルト）
if [ $# -gt 0 ]; then
    COMMIT_MESSAGE="$1"
else
    # デフォルトのコミットメッセージを生成
    CHANGED_FILES=$(git status --short | wc -l | tr -d ' ')
    COMMIT_MESSAGE="Auto-save: ${CHANGED_FILES} files updated at ${CURRENT_DATETIME}"
fi

echo ""
echo "=== 自動Gitコミット ==="
echo "日時: $CURRENT_DATETIME"
echo ""

# 変更ファイルを表示
echo "変更ファイル:"
git status --short | head -10
echo ""

# ステージング
echo "ファイルをステージング中..."
git add .

# コミット
echo "コミット中..."
git commit -m "$(cat <<EOF
${COMMIT_MESSAGE}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

echo ""
echo "✓ コミット完了"
echo ""

# プッシュ（オプション - 環境変数で制御）
if [ "${AUTO_PUSH:-false}" = "true" ]; then
    echo "リモートにプッシュ中..."
    if git push; then
        echo "✓ プッシュ完了"
    else
        echo "⚠ プッシュに失敗しました"
        exit 1
    fi
else
    echo "💡 プッシュする場合は: git push"
fi

echo ""
echo "====================="
