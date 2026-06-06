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

## 2. 現在のステータス（2026-06-06 第2セッション終了時点）

**🟢 本番稼働中。** Secrets/Pages 設定済み、実サイトから価格取得に成功している。

- ✅ PR #1〜#4 を master へマージ・Pages デプロイ済み
  - #1 本体 / #2 グラフ改善 / #3 cron:17 / #4 PWAキャッシュ修正
- ✅ **実価格を取得できている**（手動Runで3点記録、append+commit 正常）
  | id | 商品 | 直近価格 |
  |---|---|---|
  | `bs-na2-platinum-20` | Sodium Platinum (Na2) 20% 10ml | $87.29 |
  | `bs-platinum-3-25` | Platinum Solution #3 25ml | $170.30 |
  | `bs-palladium-3-25` | Palladium Solution #3 25ml | $211.25 |
  - 抽出方式は `css:.usg_product_field_3`（このサイトは JSON-LD 非搭載のため CSS セレクタ指定）
  - 為替も記録中（例: 1$=160.163、open.er-api.com）
- ✅ cron は `17 21,0,3,6,9,12 * * *`（JST 6:17/9:17/12:17/15:17/18:17/21:17）
- ✅ ダッシュボードのグラフ改善（日付軸・期間切替 1ヶ月/3ヶ月/1年/全期間・左右スクロール）公開済み
- ✅ PWA は network-first＋キャッシュ v2（更新が確実に反映される。シェル更新時は CACHE 版を上げる）

### ⏳ 唯一の未確認事項（最優先で確認）
- **GitHub の定期実行(schedule)が初日は一度も発火しなかった**（cron :00 era も :17 era も全枠スキップ）。
  GitHub Actions の schedule はベストエフォートで、スロットがまるごと落ちることがある既知の挙動。
- **対策（採用方針）: 外部トリガーで確実化** → 手順は [EXTERNAL_TRIGGER.md](EXTERNAL_TRIGGER.md)。
  外部の無料 cron サービス（cron-job.org 等）から GitHub の workflow_dispatch API を叩いて起動する。
  ワークフロー側は変更不要。GitHub の cron は予備として残す。
  - **未完了のユーザー操作**: ①Fine-grained トークン作成（Actions: Read/Write、対象リポジトリのみ）
    ②cron-job.org にジョブ登録（手順書の通り）③テスト実行
- （任意）値動き発生時に ntfy/Discord 通知が実際に届くか。

> 💡 開発サンドボックスは外部サイト/為替API/CDN へ到達できない（許可リスト制）。
> 実取得の確認は GitHub Actions ランナー側で行うこと（ローカルの monitor.py 実行で
> 失敗しても、それは環境制約であってコードの問題ではない場合がある）。

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
