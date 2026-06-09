#!/bin/bash
# Mac 常駐の定期同期（launchd から実行）
set -e
REPO="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"
cd "$REPO" || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
# 最新を取り込み（ローカル変更は自動退避して衝突回避）
git pull --rebase --autostash origin "$BRANCH" >/dev/null 2>&1 || exit 0
# vault 配下の変更だけをコミット対象に（他サブプロジェクトに触れない）
git add obsidian
if ! git diff --cached --quiet; then
  git commit -m "Auto-sync vault at $(date '+%Y-%m-%d %H:%M')" >/dev/null 2>&1 || true
fi
git push origin "$BRANCH" >/dev/null 2>&1 || true
