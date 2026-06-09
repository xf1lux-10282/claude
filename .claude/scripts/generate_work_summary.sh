#!/bin/bash

# 作業サマリー生成スクリプト
# Git履歴とファイル変更から作業内容を自動生成してデイリーノートに追記

set -e

# 作業ディレクトリ
WORK_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$WORK_DIR"

# 現在の日付を取得
CURRENT_DATE=$(date "+%Y-%m-%d")
CURRENT_YEAR=$(date "+%Y")
CURRENT_MONTH=$(date "+%m")
CURRENT_TIME=$(date "+%H:%M")

# デイリーノートのパス
DAILY_NOTE_DIR="obsidian/DailyNotes/${CURRENT_YEAR}/${CURRENT_MONTH}"
DAILY_NOTE_FILE="${DAILY_NOTE_DIR}/${CURRENT_DATE}.md"

# Gitリポジトリかチェック
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "⚠ Gitリポジトリではありません"
    exit 1
fi

# 変更ファイル数を取得
CHANGED_FILES=$(git status --short | wc -l | tr -d ' ')
MODIFIED_FILES=$(git status --short | grep "^ M" | wc -l | tr -d ' ')
NEW_FILES=$(git status --short | grep "^??" | wc -l | tr -d ' ')
STAGED_FILES=$(git status --short | grep "^M" | wc -l | tr -d ' ')

# サマリーを生成
SUMMARY="### ${CURRENT_TIME} - 作業サマリー（自動生成）

**変更統計:**
- 変更ファイル数: ${CHANGED_FILES}
- 修正: ${MODIFIED_FILES}, 新規: ${NEW_FILES}, ステージ済み: ${STAGED_FILES}

**変更ファイル一覧:**"

# 変更ファイルリストを追加（最大10件）
if [ "$CHANGED_FILES" -gt 0 ]; then
    SUMMARY="$SUMMARY
\`\`\`
$(git status --short | head -10)
\`\`\`"
else
    SUMMARY="$SUMMARY
- 変更なし"
fi

# 最近のコミット情報（今日のコミット）
TODAY_COMMITS=$(git log --since="today 00:00" --oneline --no-merges | wc -l | tr -d ' ')
if [ "$TODAY_COMMITS" -gt 0 ]; then
    SUMMARY="$SUMMARY

**今日のコミット: ${TODAY_COMMITS}件**
\`\`\`
$(git log --since="today 00:00" --oneline --no-merges)
\`\`\`"
fi

SUMMARY="$SUMMARY

---"

# デイリーノートに追記
if [ -f "$DAILY_NOTE_FILE" ]; then
    echo "" >> "$DAILY_NOTE_FILE"
    echo "$SUMMARY" >> "$DAILY_NOTE_FILE"
    echo "✓ 作業サマリーをデイリーノートに追記: $DAILY_NOTE_FILE"
else
    echo "⚠ デイリーノートが見つかりません: $DAILY_NOTE_FILE"
    exit 1
fi
