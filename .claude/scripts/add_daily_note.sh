#!/bin/bash

# デイリーノートに作業記録を追記するスクリプト
# 使用方法: ./add_daily_note.sh "作業タイトル" "作業内容"

set -e

# 引数チェック
if [ $# -lt 2 ]; then
    echo "使用方法: $0 <作業タイトル> <作業内容>"
    exit 1
fi

WORK_TITLE="$1"
WORK_CONTENT="$2"

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

# ディレクトリが存在しない場合は作成
mkdir -p "$DAILY_NOTE_DIR"

# デイリーノートが存在しない場合は作成
if [ ! -f "$DAILY_NOTE_FILE" ]; then
    CURRENT_DATETIME=$(date "+%Y年%m月%d日 %A %H:%M")
    cat > "$DAILY_NOTE_FILE" << EOF
# ${CURRENT_DATETIME}

## 作業記録

EOF
fi

# 作業記録を追記
cat >> "$DAILY_NOTE_FILE" << EOF

### ${CURRENT_TIME} - ${WORK_TITLE}

${WORK_CONTENT}

---
EOF

echo "✓ デイリーノートに記録追加: $DAILY_NOTE_FILE"
