# 同期環境セットアップ手順（Mac / VS Code で実施）

このドキュメントは、**Mac の VS Code 上の Claude Code セッションで実行する**ことを前提にした
セットアップ手順です。Web（リモートコンテナ）からは Mac の launchd 登録やフックの実地テストが
できないため、ここに残してあります。

## 目的のアーキテクチャ

- **読む層 = iCloud**：Obsidian の vault は iCloud（`iCloud~md~obsidian/Documents`）にあり、
  Mac ⇄ iPhone を自動同期。資料(md)の閲覧用。← 既に機能。
- **作る層 = git**：Claude（Web/iPhone アプリ）⇄ VS Code のファイル作業は git が背骨。
- **Mac が両者の合流点**：Mac 上では vault フォルダ＝git 作業ツリーが同一。
  ここで「git ⇄ フォルダ」を自動同期すれば、git ⇄ iCloud ⇄ iPhone が常に揃う。

## 済み（Web 側で実施済み・このブランチに含まれる）

- `.claude/hooks/*.sh` と `.claude/scripts/*.sh` の **Mac 絶対パス（WORK_DIR）を環境非依存化**。
  - 変更後: `WORK_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"`
  - Mac でも Web でも同じリポジトリ root に解決される（後方互換。Mac の挙動は従来どおり）。
  - 構文チェック・解決先の確認済み。

## Mac でやること（このセッションで実行）

### 1. フックを環境非依存に切り替えて実地テスト（効果大）
`.claude/settings.local.json` のフック command を、Mac 絶対パスから `$CLAUDE_PROJECT_DIR` 基準へ。

```jsonc
// 変更前（Mac 専用）
"command": "/Users/daisukekinoshita/Library/Mobile\\ Documents/iCloud~md~obsidian/Documents/.claude/hooks/conversation_start.sh"
// 変更後（環境非依存）
"command": "$CLAUDE_PROJECT_DIR/.claude/hooks/conversation_start.sh"
```
SessionStart / SessionEnd / PreCompact の 3 つとも同様に。

**テスト:** このセッションを一度終了→再開し、
- デイリーノートが自動作成・サマリー追記されるか
- `auto_commit.sh` が走り commit/push されるか
を確認（Mac では従来どおり動くはず。これで **Web/iPhone セッションでも記録が残る**ようになる）。

> ねらい：外出先で iPhone の Claude アプリで作業しても、デイリーノートに記録が残る。

### 2. 既知の不具合を整理
- `.claude/hooks/conversation_end.sh` は **settings に未登録（＝未使用の重複）** かつ
  中身が `git push origin main`（このリポジトリは `master`）。
- 対応案：削除する、または有効化するなら `main` → 現在ブランチに修正。
  （現状の有効フックは `session_end.sh` → `auto_commit.sh` の経路）

### 3. Mac の定期同期を launchd で常駐（pull/commit/push 漏れを構造的に解消）
「数分おきに git pull → vault の変更を commit → push」を回す。Mac は勤務中ほぼ起動しているのでハブになる。

`.claude/scripts/auto_sync.sh` を新規作成（このセッションで作成・テスト）:
```bash
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
```

launchd plist（`~/Library/LaunchAgents/com.daisuke.vault-sync.plist`、5 分間隔の例）:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.daisuke.vault-sync</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>--</string>
    <string>{REPO}/.claude/scripts/auto_sync.sh</string>
  </array>
  <key>StartInterval</key><integer>300</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardErrorPath</key><string>/tmp/vault-sync.err</string>
  <key>StandardOutPath</key><string>/tmp/vault-sync.out</string>
</dict>
</plist>
```
`{REPO}` は実際の Documents パスに置換。登録:
```bash
chmod +x "$REPO/.claude/scripts/auto_sync.sh"
launchctl load ~/Library/LaunchAgents/com.daisuke.vault-sync.plist
launchctl start com.daisuke.vault-sync
tail -f /tmp/vault-sync.out /tmp/vault-sync.err   # 動作確認
```

### 4. iPhone までの流れを確認
git に何か変更を push → 数分後に Mac が pull → iCloud → iPhone の Obsidian に反映されることを確認。

### 5. remotely-save を見直し
Mac ⇄ iPhone は iCloud が担うため remotely-save は二重。競合・重複の元になるなら
**停止、またはオフサイトバックアップ専用**に限定する。

## 注意：ブランチ運用
- Web/iPhone の Claude セッションは**作業ごとに専用ブランチ**を作る（例: `claude/...`）。
- Mac の日常 vault は通常 `master`。
- 上記フック/launchd の効果を全環境で揃えるには、**このインフラ変更を `master` にマージ**し、
  Web セッションの成果も**その日のうちに `master` へ取り込む**運用を決めておくとよい。
