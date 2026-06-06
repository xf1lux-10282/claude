# 🔖 プライスモニター 引き継ぎメモ（続きから再開するための入口）

> **「プライスモニターの続きをお願い」と言われたら、まずこのファイルを読んでください。**
> このリポジトリは毎回クローンし直す使い捨て環境で動くため、再開に必要な情報は
> すべてここ（とコミット履歴）に集約しています。

最終更新: 2026-06-06 / 作業ブランチ: `claude/product-price-monitoring-rmZQy`

---

## 1. これは何か

海外サイトの商品価格を **GitHub Actions で定期ウォッチ**し、変動を **ntfy / Discord** に
通知、価格と **USD/JPY 為替** を記録して **PWAダッシュボード** でグラフ表示するツール。
全体像・使い方は [README.md](README.md) を参照。

---

## 2. 現在のステータス（2026-06-06 時点）

- ✅ ツール一式を実装し、**PR #1 を master へマージ済み**
  （`feat(price-monitor): 商品価格の定期ウォッチ機能を追加` ほか）
- ✅ cron 設定済み（日本時間 6/9/12/15/18/21時台 = UTC `17 21,0,3,6,9,12 * * *`）
  ※ 分を :17 にしているのは GitHub の :00 混雑によるスキップ対策（公式推奨）
- ✅ 監視対象 3商品を登録（すべて Bostick & Sullivan、USD建て、自動抽出）
  | id | 商品 |
  |---|---|
  | `bs-na2-platinum-20` | Sodium Platinum (Na2) 20% Solution 10ml |
  | `bs-platinum-3-25` | Platinum Solution #3 25ml |
  | `bs-palladium-3-25` | Palladium Solution #3 25ml |

### ⏳ まだ動き出していない理由（＝ユーザー側の未完了アクション）
1. **Secrets 未登録** … `NTFY_TOPIC` または `DISCORD_WEBHOOK_URL`
   （未登録でも価格・為替の記録は動くが通知は飛ばない）
2. **GitHub Pages 未有効化** … `Settings → Pages → Source = GitHub Actions`
3. **初回の手動実行が未実施** … `Actions → 価格モニター → Run workflow`

> ⚠️ **重要な未検証点**: 開発サンドボックスはネットワーク許可リスト制で、実サイト
> （bostick-sullivan.com）・為替API・CDN に到達できない。よって **実サイトからの
> 価格取得は一度も成功確認できていない**。ロジックは WooCommerce 型のローカルHTMLと
> 為替スタブで検証済み。**本当に取れるかは「初回の Run workflow」で初めて分かる。**

---

## 3. 「続き」でやり得ること（バックログ / 着手候補）

優先度は状況次第。ユーザーの指示を優先しつつ、以下から選ぶ。

### A. 初回実行の結果対応（最優先候補）
- ユーザーが Run workflow を回した後、**価格抽出に失敗した商品があれば修正**する。
  - 失敗時の直し方: 対象ページのHTMLを見て価格のCSSセレクタを特定し、
    `python manage.py add` ではなく `config.json` の該当 `extract.css_selector` を設定、
    または一度 remove して `manage.py add --id ... --url ... --selector "..." --test`。
  - 為替取得が失敗していないかもログで確認（`fx.py` のフォールバックが効くか）。
- 監視: `gh run watch` または GitHub Actions 拡張、もしくは私（Claude）が
  `subscribe_pr_activity` 相当でCI/実行を見張る。

### B. 機能追加の候補
- [ ] **目標価格アラート**を使いたくなったら `config.json` の `target_price` を設定
      （現状は全商品 null。仕組みは実装済み）。
- [ ] **変化幅のしきい値**（例: ±1%未満は通知しない）オプション。
- [ ] **在庫状況**（在庫切れ/再入荷）の監視・通知（JSON-LD の `availability` を利用）。
- [ ] ダッシュボードに**全商品の比較ビュー**や**為替単体グラフ**（`data/fx_usdjpy.json` 利用）。
- [ ] 通知に**商品サムネイル画像**を添付（Discord embed）。
- [ ] **週次/月次サマリ**（「今週変動した商品」一覧）を Issue や通知で。
- [ ] 監視商品の追加（ユーザーが新URLを提示したら `manage.py add`）。

### C. 運用・品質
- [ ] スクレイパーのテストを増やす（Shopify型・楽天/Amazon型のフィクスチャ）。
- [ ] 取得失敗が続いた商品を自動で通知 or 一時停止する仕組み。

---

## 4. 再開時の実務メモ

- **作業ブランチ**: `claude/product-price-monitoring-rmZQy`（既に master へマージ済みだが、
  追加変更もこのブランチで行い、必要に応じてPRを作る運用）。
- **ローカル確認コマンド**:
  ```bash
  cd price-monitor
  pip install -r requirements.txt
  python tests/test_scraper.py     # ロジックテスト（ネット不要）
  python manage.py list            # 監視商品一覧
  python monitor.py                # 手動チェック（※外部到達できる環境でのみ実価格取得）
  ```
- **サンドボックスの制約**: 外部サイト/為替API/CDN へ到達できないことがある（許可リスト制）。
  実取得の確認は GitHub Actions ランナー側で行う。
- **デイリーノート**: 作業したら `obsidian/DailyNotes/YYYY/MM/YYYY-MM-DD.md` に
  会話要約を残す（`.claude/rules.md` のルール）。直近の詳細は
  [2026-06-06.md](../obsidian/DailyNotes/2026/06/2026-06-06.md)。

---

## 5. 主要ファイルの地図

| ファイル | 役割 |
|---|---|
| `config.json` | 監視対象・通知設定（ここを編集 or `manage.py`） |
| `monitor.py` | メイン: 取得→為替→記録→通知 |
| `scraper.py` | 価格自動抽出（JSON-LD/meta/CSS/regex） |
| `fx.py` | USD/JPY 為替取得（多重フォールバック） |
| `notifier.py` | ntfy / Discord 通知 |
| `storage.py` | 履歴・円換算・index.json 生成 |
| `manage.py` | 商品の追加/削除/一覧 CLI |
| `docs/` | PWAダッシュボード（GitHub Pages公開対象） |
| `data/` | 価格履歴・為替・index（Actionsが自動生成・コミット） |
| `../.github/workflows/price-monitor.yml` | 定期実行ワークフロー |
