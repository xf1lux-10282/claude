# Obsidian バックアップシステム

このリポジトリは、iCloudに保存されたObsidianノートのバックアップとバージョン管理を行います。

---

## ⚠️ 重要：作業開始前の確認事項

**Claude Codeで作業を開始する前に、必ず以下のルールファイルを確認してください：**

### 📋 [Claude Code 作業ルール](.claude/rules.md)

このルールファイルには、以下の必須事項が記載されています：

1. **日時・曜日の確認ルール** - 必ずシステムカレンダーで確認
2. **デイリーノート作成ルール** - 作業開始時に必ず作成
3. **ディレクトリ・ファイル管理ルール** - 統一された構造で管理
4. **トークン管理ルール** - 80%、90%での対応を徹底
5. **実行ルールの確認** - チェックリストで必須事項を確認

**すべてのルールは必ず実行してください。**

---

## ディレクトリ構成

```
.
├── obsidian/              # Obsidianノート（メインコンテンツ）
├── github/                # GitHub関連ドキュメント
│   ├── README.md          # 詳細な説明
│   ├── SETUP_GUIDE.md     # セットアップガイド
│   └── setup_github.sh    # GitHubセットアップスクリプト
├── sync_to_nas.sh         # NASバックアップスクリプト
└── NAS_ONLY_FILES_REPORT.md  # NAS専用ファイルレポート
```

## クイックスタート

### NASへのバックアップ
```bash
./sync_to_nas.sh
```

### GitHubへのプッシュ
```bash
git add .
git commit -m "Update notes"
git push
```

### Claude Code WEB版
https://claude.com/claude-code

## 詳細情報

詳しい説明とセットアップ手順は以下を参照してください：
- [詳細README](github/README.md)
- [セットアップガイド](github/SETUP_GUIDE.md)

## システム構成

- **iCloud Drive**: メインストレージ
- **NAS** (`/Volumes/obsidian`): バックアップストレージ
- **GitHub**: バージョン管理とリモートバックアップ
- **Claude Code WEB版**: どこからでもアクセス可能な編集環境
