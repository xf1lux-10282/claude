#!/bin/bash

# Claude Code 会話開始時フック
# このスクリプトは会話開始時に自動実行され、デイリーノートの作成を行います

set -e

# 作業ディレクトリ
WORK_DIR="/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents"
cd "$WORK_DIR"

# ============================================================
# Git 自動プル（他デバイスの変更を取得）
# ============================================================
echo ""
echo "=== Git 自動プル ==="

# 環境変数で制御（デフォルト: true）
if [ "${AUTO_PULL_ON_SESSION_START:-true}" = "true" ]; then
    if git rev-parse --git-dir > /dev/null 2>&1; then
        # リモートの最新状態を取得
        if git fetch origin 2>&1; then
            # 現在のブランチ名を取得
            CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

            # ローカルとリモートのコミットを比較
            LOCAL=$(git rev-parse @)
            REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")

            if [ -n "$REMOTE" ]; then
                if [ "$LOCAL" = "$REMOTE" ]; then
                    echo "✓ 既に最新です（プルする変更なし）"
                elif [ "$LOCAL" != "$REMOTE" ]; then
                    # コミットされていない変更があるかチェック
                    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
                        echo "⚠ ローカルに未コミットの変更があります"
                        echo "   プル前に変更を自動コミットします..."

                        # 自動コミット
                        git add .
                        CURRENT_TIME=$(date "+%Y年%m月%d日 %A %H:%M")
                        git commit -m "Auto-save before pull at ${CURRENT_TIME}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
                        echo "✓ 自動コミット完了"
                    fi

                    # プル実行
                    echo "リモートから変更を取得中..."
                    if git pull --rebase origin "$CURRENT_BRANCH" 2>&1; then
                        echo "✓ プル完了（他デバイスの変更を取得しました）"
                    else
                        echo "⚠ プルに失敗しました（コンフリクトの可能性）"
                        echo "   手動で確認してください: git status"
                    fi
                fi
            else
                echo "✓ リモートブランチが設定されていません（初回プッシュ前）"
            fi
        else
            echo "⚠ リモートとの接続に失敗しました"
        fi
    else
        echo "ℹ️  Gitリポジトリではありません"
    fi
else
    echo "ℹ️  自動プルは無効です（AUTO_PULL_ON_SESSION_START=false）"
fi

echo "=================================="
echo ""

# 現在の日付を取得
CURRENT_DATE=$(date "+%Y-%m-%d")
CURRENT_YEAR=$(date "+%Y")
CURRENT_MONTH=$(date "+%m")
CURRENT_DATETIME=$(date "+%Y年%m月%d日 %A %H:%M")

# デイリーノートのパス
DAILY_NOTE_DIR="obsidian/DailyNotes/${CURRENT_YEAR}/${CURRENT_MONTH}"
DAILY_NOTE_FILE="${DAILY_NOTE_DIR}/${CURRENT_DATE}.md"

# ディレクトリが存在しない場合は作成
mkdir -p "$DAILY_NOTE_DIR"

# デイリーノートが存在しない場合は作成
if [ ! -f "$DAILY_NOTE_FILE" ]; then
    cat > "$DAILY_NOTE_FILE" << EOF
# ${CURRENT_DATETIME}

## 作業記録

### 会話開始
- Claude Code セッション開始

---
EOF
    echo "✓ デイリーノート作成: $DAILY_NOTE_FILE"
else
    echo "✓ デイリーノート既存: $DAILY_NOTE_FILE"
fi

# ルールファイルの存在確認
if [ -f ".claude/rules.md" ]; then
    echo "✓ ルールファイル確認済み"
else
    echo "⚠ 警告: ルールファイルが見つかりません"
fi

echo ""
echo "=== Claude Code セッション準備完了 ==="
echo "日付: $CURRENT_DATETIME"
echo "デイリーノート: $DAILY_NOTE_FILE"
echo "=================================="

# ============================================================
# 直近の作業内容をClaudeのコンテキストに渡す
# （VS Code等、別環境での直前/作業中の内容を把握し、
#   同じ作業を重複して行わないようにするため）
# ============================================================
echo ""
echo "=== 直前/作業中の内容（Claude向けコンテキスト） ==="

# 今日のデイリーノート全文を出力
echo ""
echo "--- 本日のデイリーノート: ${CURRENT_DATE} ---"
cat "$DAILY_NOTE_FILE"

# 直前の作業日のデイリーノートも出力（今日の1つ前に作業した日）
# 日付形式（YYYY-MM-DD.md）のファイルだけを対象にする（INDEX.md等を除外）
PREV_NOTE=$(find obsidian/DailyNotes -type f 2>/dev/null \
    | grep -E '[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$' \
    | grep -v "${CURRENT_DATE}.md" \
    | sort \
    | tail -n 1)

if [ -n "$PREV_NOTE" ] && [ -f "$PREV_NOTE" ]; then
    echo ""
    echo "--- 直前の作業日のデイリーノート: $(basename "$PREV_NOTE" .md) ---"
    cat "$PREV_NOTE"
fi

echo ""
echo "=== ↑ これらは過去の作業記録です。重複作業を避けるため参照してください ==="
