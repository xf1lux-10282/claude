#!/bin/bash

# Claude Code トークン圧縮前フック（PreCompact）
# トークン使用量が高くなり、コンテキストが圧縮される前に実行されます
# このタイミングで作業ログを保存します

set -e

# 作業ディレクトリ
WORK_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$WORK_DIR"

# 現在の日付を取得
CURRENT_DATETIME=$(date "+%Y年%m月%d日 %A %H:%M")

echo ""
echo "=== トークン使用量警告 ==="
echo "⚠️  トークン使用率が高くなっています"
echo "日時: $CURRENT_DATETIME"
echo ""
echo "作業ログを自動保存します..."
echo ""

# 作業サマリーを生成してデイリーノートに追記
if [ -x ".claude/scripts/generate_work_summary.sh" ]; then
    .claude/scripts/generate_work_summary.sh
    echo ""
else
    echo "⚠ 作業サマリースクリプトが見つかりません"
fi

echo "==========================="
echo "ログ保存が完了しました"
echo "会話を続行できます"
echo "==========================="
echo ""
