#!/bin/bash

# Claude Webの会話を素早くObsidianに保存するスクリプト

# 使い方:
# 1. Claude Webの会話をコピー（Cmd+A → Cmd+C）
# 2. このスクリプトを実行: ./save_claude_chat.sh
# 3. プロンプトに従って情報を入力

echo "=== Claude Web チャットログ保存 ==="
echo ""

# プロジェクト選択
echo "プロジェクトを選択してください:"
echo "1) Alternative Process Lab"
echo "2) 写真家活動"
echo "3) その他"
read -p "選択 (1-3): " project_choice

case $project_choice in
    1)
        PROJECT_DIR="obsidian/チャットログ/Alternative Process Lab"
        ;;
    2)
        PROJECT_DIR="obsidian/チャットログ/写真家活動"
        ;;
    3)
        read -p "プロジェクト名を入力: " custom_project
        PROJECT_DIR="obsidian/チャットログ/${custom_project}"
        ;;
    *)
        echo "無効な選択です"
        exit 1
        ;;
esac

# タイトル入力
read -p "会話のタイトル: " title

# 日時取得
DATE=$(date +"%Y-%m-%d")
TIME=$(date +"%H:%M")

# ファイル名生成
FILENAME="${PROJECT_DIR}/${title}_${DATE}.md"

# ディレクトリ作成（存在しない場合）
mkdir -p "$PROJECT_DIR"

# ファイル作成
cat > "$FILENAME" << EOF
---
作成日: ${DATE}
元の会話: Claude Web
ステータス: 継続予定
---

# ${title}

## 会話概要
<!-- Claude Webでの議論の要点を記載 -->

## 次のアクション（Claude Code用）
- [ ]

## 会話ログ

### 日時: ${DATE} ${TIME}

<!-- ここにClaude Webの会話内容を貼り付けてください -->


---

## Claude Codeでの作業記録

<!-- 翌日、Claude Codeでの作業内容を追記 -->

EOF

echo ""
echo "✅ ファイルを作成しました: $FILENAME"
echo ""
echo "次のステップ:"
echo "1. ファイルをObsidianで開く"
echo "2. 「会話ログ」セクションにClaude Webの会話を貼り付け"
echo "3. 「次のアクション」にタスクを記載"
echo "4. 翌日Claude Codeでこのファイルを参照して作業継続"
echo ""

# Obsidianで開く（オプション）
read -p "今すぐObsidianで開きますか？ (y/n): " open_choice
if [ "$open_choice" = "y" ]; then
    open "obsidian://open?vault=obsidian&file=${FILENAME}"
fi
