# Claude Code 自動実行システム

このディレクトリには、Claude Codeでの作業を自動化し、ルールを確実に実行するためのスクリプトとフックが含まれています。

## 📁 ディレクトリ構造

```
.claude/
├── README.md                           # このファイル
├── rules.md                            # 作業ルール定義
├── settings.local.json                 # Claude Code設定とフック定義
├── hooks/
│   └── conversation_start.sh          # 会話開始時の自動実行フック
└── scripts/
    ├── add_daily_note.sh              # デイリーノート追記
    ├── save_chat_log.sh               # チャットログ保存
    └── check_token_usage.sh           # トークン使用量チェック
```

---

## 🚀 自動実行される機能

### 会話開始時（SessionStart）
新しいClaude Codeセッションを開始すると、自動的に以下が実行されます：

1. **デイリーノートの自動作成**
   - パス: `obsidian/DailyNotes/YYYY/MM/YYYY-MM-DD.md`
   - 既に存在する場合はスキップ
   - 日時と曜日を自動取得して記録

2. **ルールファイルの確認**
   - `.claude/rules.md` の存在を確認
   - 警告がある場合は表示

3. **セッション情報の表示**
   - 現在の日時
   - デイリーノートのパス

---

### 会話終了時（SessionEnd）
「終了します」と伝えてセッションを終了すると、自動的に以下が実行されます：

1. **作業サマリーの自動生成**
   - Git変更ファイル統計
   - 変更ファイル一覧
   - 今日のコミット履歴
   - デイリーノートに自動追記

2. **セッション終了記録**
   - 終了時刻をデイリーノートに記録

3. **Git自動コミット**（デフォルト有効）
   - すべての変更を自動ステージング
   - タイムスタンプ付きコミット
   - Claude Co-Authored-By付与
   - ※プッシュは手動（`AUTO_PUSH=true`で自動化可能）

---

### トークン使用量が高い時（PreCompact）
トークン使用量が高くなり、コンテキスト圧縮が必要になる前に自動的に：

1. **作業サマリーの自動保存**
   - 現在までの作業内容をデイリーノートに記録
   - Git変更状況を記録

2. **警告メッセージの表示**
   - トークン使用率の通知
   - ログ保存完了の確認

---

## 🛠️ 利用可能なスクリプト

### 1. 作業サマリー自動生成スクリプト

Git履歴から作業内容を自動生成してデイリーノートに追記します。

#### 使用方法
```bash
.claude/scripts/generate_work_summary.sh
```

#### 生成される内容
- 変更ファイル数の統計
- 変更ファイル一覧（最大10件）
- 今日のコミット履歴

---

### 2. Git自動コミットスクリプト

変更をステージングしてコミットします。

#### 使用方法
```bash
.claude/scripts/auto_commit.sh [コミットメッセージ（オプション）]
```

#### 例
```bash
.claude/scripts/auto_commit.sh "機能追加: ユーザー認証"
```

#### 環境変数
- `AUTO_PUSH=true`: コミット後に自動プッシュ（デフォルト: false）

---

### 3. デイリーノート追記スクリプト

作業記録をデイリーノートに追記します。

#### 使用方法
```bash
.claude/scripts/add_daily_note.sh "作業タイトル" "作業内容"
```

#### 例
```bash
.claude/scripts/add_daily_note.sh "バグ修正" "**実施内容:**
1. ログイン機能のバグを修正
2. テストケースを追加

**作成ファイル:**
- [src/auth/login.ts](src/auth/login.ts)
- [tests/auth/login.test.ts](tests/auth/login.test.ts)"
```

---

### 4. チャットログ保存スクリプト

プロジェクトごとのチャットログを保存します。

#### 使用方法
```bash
.claude/scripts/save_chat_log.sh "プロジェクト名" "作業タイトル" "チャット内容"
```

#### 例
```bash
.claude/scripts/save_chat_log.sh "Alternative Process Lab" "事業計画書作成" "## 会話内容
ユーザー: 事業計画書のフォーマットを教えてください
Claude: 以下のフォーマットをお勧めします..."
```

#### 保存先
- `obsidian/チャットログ/[プロジェクト名]/[作業タイトル]_YYYYMMDD.md`

---

### 5. トークン使用量チェックスクリプト

現在のトークン使用率をチェックし、警告を表示します。

#### 使用方法
```bash
.claude/scripts/check_token_usage.sh <現在のトークン数> <最大トークン数>
```

#### 例
```bash
.claude/scripts/check_token_usage.sh 160000 200000
# 出力: トークン使用率: 80%
#       ⚠️ 注意: トークン使用率が80%を超えています。
```

#### 警告レベル
- **80%以上**: デイリーノートとチャットログを更新推奨
- **90%以上**: 作業を中断してログ保存必須

---

## 📋 ルールの概要

詳細は [rules.md](rules.md) を参照してください。

### 主要ルール

1. **日時・曜日の確認**
   - 日付記載時は必ず `date` コマンドで確認
   - 推測や記憶に頼らない

2. **デイリーノート作成**
   - 作業開始時に必ず作成（自動化済み）
   - 作業の区切りごとに追記

3. **ディレクトリ・ファイル管理**
   - 構造化されたディレクトリに保存
   - プロジェクトごとに整理

4. **トークン管理**
   - 80%で警告、90%で保存必須
   - 長時間作業時は定期的にチェック

---

## 🔧 システム設定

### フックの設定

[settings.local.json](settings.local.json) でフックが定義されています：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/.claude/hooks/conversation_start.sh",
            "timeout": 10
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/.claude/hooks/session_end.sh",
            "timeout": 30
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/.claude/hooks/pre_compact.sh",
            "timeout": 30
          }
        ]
      }
    ]
  },
  "env": {
    "AUTO_COMMIT_ON_SESSION_END": "true",
    "AUTO_PUSH": "false"
  }
}
```

### 環境変数

システムの動作を制御する環境変数：

- `AUTO_COMMIT_ON_SESSION_END`: セッション終了時に自動コミット（デフォルト: `true`）
- `AUTO_PUSH`: コミット後に自動プッシュ（デフォルト: `false`）

これらは [settings.local.json](settings.local.json) の `env` セクションで設定できます。

### パーミッション設定

必要なBashコマンドはすべて `permissions.allow` に追加されています：
- `date:*` - 日時取得
- `mkdir:*` - ディレクトリ作成
- `git *` - Git操作
- その他、ファイル操作に必要なコマンド

---

## 📝 使用例

### 典型的なワークフロー

#### 1. 会話開始
```
$ claude-code
✓ デイリーノート作成: obsidian/DailyNotes/2026/01/2026-01-14.md
✓ ルールファイル確認済み

=== Claude Code セッション準備完了 ===
日付: 2026年01月14日 Wednesday 22:31
デイリーノート: obsidian/DailyNotes/2026/01/2026-01-14.md
==================================
```

#### 2. 作業実施
```
ユーザー: 新機能を実装してください
Claude: 実装しました...
```

#### 3. 作業記録の追加
```bash
.claude/scripts/add_daily_note.sh "新機能実装" "**実施内容:**
1. ユーザー認証機能を追加
2. テストを作成

**作成ファイル:**
- [src/auth/index.ts](src/auth/index.ts)"
```

#### 4. トークンチェック
```bash
.claude/scripts/check_token_usage.sh 180000 200000
# トークン使用率: 90%
# ⚠️ 警告: トークン使用率が90%を超えています！
```

#### 5. チャットログ保存（必要に応じて）
```bash
.claude/scripts/save_chat_log.sh "プロジェクト名" "作業タイトル" "会話内容..."
```

---

## 🐛 トラブルシューティング

### フックが実行されない

#### 確認事項
1. スクリプトに実行権限があるか確認
   ```bash
   ls -la .claude/hooks/conversation_start.sh
   # -rwxr-xr-x であることを確認
   ```

2. 実行権限がない場合は付与
   ```bash
   chmod +x .claude/hooks/conversation_start.sh
   ```

3. settings.local.json が正しい形式か確認
   ```bash
   cat .claude/settings.local.json | grep -A 10 "hooks"
   ```

### デイリーノートが作成されない

#### 手動で実行してエラーを確認
```bash
.claude/hooks/conversation_start.sh
```

#### よくあるエラー
- **Permission denied**: `chmod +x` で実行権限を付与
- **Directory not found**: ディレクトリパスが正しいか確認

---

## 🔄 システムの更新

### スクリプトを修正した場合

1. 変更をテスト
   ```bash
   .claude/scripts/add_daily_note.sh "テスト" "テスト内容"
   ```

2. 問題なければコミット
   ```bash
   git add .claude/
   git commit -m "Update Claude Code automation scripts"
   git push
   ```

---

## 📚 関連ドキュメント

- [rules.md](rules.md) - 詳細なルール定義
- [settings.local.json](settings.local.json) - Claude Code設定
- [Obsidian DailyNotes](../obsidian/DailyNotes/) - デイリーノート保存先
- [チャットログ](../obsidian/チャットログ/) - チャットログ保存先

---

## 🎯 今後の拡張案

### 実装検討中の機能

- [ ] トークン80%/90%での自動ログ保存
- [ ] 定期的なバックアップ（Git push）の自動化
- [ ] 作業時間の自動トラッキング
- [ ] チャットログのMarkdown形式最適化
- [ ] Obsidianプラグインとの連携

---

**作成日**: 2026年01月14日 Wednesday
**最終更新**: 2026年01月14日 Wednesday 22:40
