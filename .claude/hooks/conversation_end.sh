#!/bin/bash

# セッション終了時フック
# 自動コミット＆GitHubプッシュ

WORK_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$WORK_DIR" || exit 1

DAILY_NOTE="$WORK_DIR/obsidian/DailyNotes/$(date '+%Y/%m/%Y-%m-%d').md"

# --- 1. 作業サマリーをデイリーノートに追記 ---
{
  echo ""
  echo "---"
  echo ""
  echo "### $(date '+%H:%M') - 作業サマリー（自動生成）"
  echo ""

  # 変更ファイル統計
  MODIFIED=$(git status --short | grep -c '^ M')
  ADDED=$(git status --short | grep -c '^??')
  STAGED=$(git status --short | grep -c '^A')
  TOTAL=$((MODIFIED + ADDED + STAGED))

  echo "**変更統計:**"
  echo "- 変更ファイル数: $TOTAL"
  echo "- 修正: $MODIFIED, 新規: $ADDED, ステージ済み: $STAGED"
  echo ""

  # 変更ファイル一覧
  echo "**変更ファイル一覧:**"
  if [ "$TOTAL" -eq 0 ]; then
    echo "- 変更なし"
  else
    echo "\`\`\`"
    git status --short
    echo "\`\`\`"
  fi
  echo ""

  # 今日のコミット履歴
  TODAY=$(date '+%Y-%m-%d')
  COMMIT_COUNT=$(git log --since="$TODAY 00:00:00" --oneline | wc -l | xargs)
  if [ "$COMMIT_COUNT" -gt 0 ]; then
    echo "**今日のコミット: ${COMMIT_COUNT}件**"
    echo "\`\`\`"
    git log --since="$TODAY 00:00:00" --oneline
    echo "\`\`\`"
  fi
  echo ""

} >> "$DAILY_NOTE"

# --- 2. セッション終了記録を追記 ---
{
  echo "---"
  echo ""
  echo "### $(date '+%H:%M') - セッション終了"
  echo ""
  echo "**セッション情報:**"
  echo "- 終了時刻: $(date '+%Y年%m月%d日 %A %H:%M')"
  echo "- 作業内容: Claude Codeセッション完了"
  echo ""
  echo "---"
  echo ""
} >> "$DAILY_NOTE"

# --- 3. Gitコミット＆プッシュ ---
git add .

# 変更がある場合のみコミット＆プッシュ
if git diff --cached --quiet; then
  echo "変更なし。コミット＆プッシュをスキップしました。" >&2
else
  TIMESTAMP=$(date '+%Y年%m月%d日 %A %H:%M')
  git commit -m "Session end auto-save at $TIMESTAMP" >/dev/null 2>&1

  # GitHubへプッシュ（SSH接続前提）
  if git push origin main >/dev/null 2>&1; then
    echo "✓ GitHubへ自動プッシュ完了: $TIMESTAMP" >&2
  else
    echo "⚠ GitHubプッシュに失敗しました（ネットワーク確認）" >&2
  fi
fi

exit 0
