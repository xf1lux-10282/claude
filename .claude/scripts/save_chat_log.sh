#!/bin/bash

# チャットログを保存するスクリプト
# 使用方法: ./save_chat_log.sh "プロジェクト名" "作業タイトル" "チャット内容"

set -e

# 引数チェック
if [ $# -lt 3 ]; then
    echo "使用方法: $0 <プロジェクト名> <作業タイトル> <チャット内容>"
    exit 1
fi

PROJECT_NAME="$1"
WORK_TITLE="$2"
CHAT_CONTENT="$3"

# 作業ディレクトリ
WORK_DIR="/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents"
cd "$WORK_DIR"

# 現在の日付を取得
CURRENT_DATE=$(date "+%Y%m%d")
CURRENT_DATETIME=$(date "+%Y年%m月%d日 %A %H:%M")

# チャットログのパス
CHAT_LOG_DIR="obsidian/チャットログ/${PROJECT_NAME}"
CHAT_LOG_FILE="${CHAT_LOG_DIR}/${WORK_TITLE}_${CURRENT_DATE}.md"

# ディレクトリが存在しない場合は作成
mkdir -p "$CHAT_LOG_DIR"

# チャットログが存在しない場合は作成
if [ ! -f "$CHAT_LOG_FILE" ]; then
    cat > "$CHAT_LOG_FILE" << EOF
# ${WORK_TITLE}

**作成日時**: ${CURRENT_DATETIME}

---

## チャットログ

${CHAT_CONTENT}

---
EOF
    echo "✓ チャットログ作成: $CHAT_LOG_FILE"
else
    # 既存のチャットログに追記
    cat >> "$CHAT_LOG_FILE" << EOF

---

## ${CURRENT_DATETIME}

${CHAT_CONTENT}

---
EOF
    echo "✓ チャットログ更新: $CHAT_LOG_FILE"
fi
