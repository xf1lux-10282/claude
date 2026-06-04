#!/bin/bash

# トークン使用量をチェックするスクリプト
# 使用方法: ./check_token_usage.sh <現在のトークン数> <最大トークン数>

set -e

# 引数チェック
if [ $# -lt 2 ]; then
    echo "使用方法: $0 <現在のトークン数> <最大トークン数>"
    exit 1
fi

CURRENT_TOKENS=$1
MAX_TOKENS=$2

# トークン使用率を計算
USAGE_PERCENT=$((CURRENT_TOKENS * 100 / MAX_TOKENS))

echo "トークン使用率: ${USAGE_PERCENT}%"
echo "現在: ${CURRENT_TOKENS} / 最大: ${MAX_TOKENS}"

# 使用率が80%以上の場合は警告
if [ $USAGE_PERCENT -ge 90 ]; then
    echo ""
    echo "⚠️ 警告: トークン使用率が90%を超えています！"
    echo "   今すぐログを保存してください。"
    exit 90
elif [ $USAGE_PERCENT -ge 80 ]; then
    echo ""
    echo "⚠️ 注意: トークン使用率が80%を超えています。"
    echo "   デイリーノートとチャットログを更新してください。"
    exit 80
else
    echo "✓ トークン使用率は正常範囲内です。"
    exit 0
fi
