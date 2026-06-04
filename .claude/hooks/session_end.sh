#!/bin/bash

# Claude Code 会話終了時フック
# このスクリプトは会話終了時に自動実行され、作業サマリーを保存します

set -e

# 作業ディレクトリ
WORK_DIR="/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents"
cd "$WORK_DIR"

# 現在の日付を取得
CURRENT_DATE=$(date "+%Y-%m-%d")
CURRENT_YEAR=$(date "+%Y")
CURRENT_MONTH=$(date "+%m")
CURRENT_TIME=$(date "+%H:%M")
CURRENT_DATETIME=$(date "+%Y年%m月%d日 %A %H:%M")

# デイリーノートのパス
DAILY_NOTE_DIR="obsidian/DailyNotes/${CURRENT_YEAR}/${CURRENT_MONTH}"
DAILY_NOTE_FILE="${DAILY_NOTE_DIR}/${CURRENT_DATE}.md"

echo ""
echo "=== Claude Code セッション終了処理 ==="
echo "日時: $CURRENT_DATETIME"
echo ""

# 1. 作業サマリーを自動生成してデイリーノートに追記
echo "--- 作業サマリー生成 ---"
if [ -x ".claude/scripts/generate_work_summary.sh" ]; then
    .claude/scripts/generate_work_summary.sh
else
    echo "⚠ 作業サマリースクリプトが見つかりません"
fi

# 2. デイリーノートに終了記録を追記
echo ""
echo "--- セッション終了記録 ---"
if [ -f "$DAILY_NOTE_FILE" ]; then
    cat >> "$DAILY_NOTE_FILE" << EOF

### ${CURRENT_TIME} - セッション終了

**セッション情報:**
- 終了時刻: ${CURRENT_DATETIME}
- 作業内容: Claude Codeセッション完了

---
EOF
    echo "✓ デイリーノートに終了記録を追記"
else
    echo "⚠ デイリーノートが見つかりません: $DAILY_NOTE_FILE"
fi

# 3. Git自動コミット（環境変数で制御）
echo ""
echo "--- Git 自動コミット ---"
if [ "${AUTO_COMMIT_ON_SESSION_END:-true}" = "true" ]; then
    if [ -x ".claude/scripts/auto_commit.sh" ]; then
        .claude/scripts/auto_commit.sh "Session end auto-save at ${CURRENT_DATETIME}"
    else
        echo "⚠ 自動コミットスクリプトが見つかりません"
    fi
else
    echo "ℹ️  自動コミットは無効です（AUTO_COMMIT_ON_SESSION_END=false）"

    # Git状態をチェック
    if git rev-parse --git-dir > /dev/null 2>&1; then
        if ! git diff-index --quiet HEAD -- 2>/dev/null; then
            echo "⚠ コミットされていない変更があります"
            echo ""
            git status --short | head -10
            echo ""
            echo "💡 変更をコミットする場合は以下を実行:"
            echo "   .claude/scripts/auto_commit.sh"
        else
            echo "✓ すべての変更がコミット済みです"
        fi
    fi
fi

echo ""
echo "==================================="
echo "セッション終了処理が完了しました"
echo "==================================="
echo ""
