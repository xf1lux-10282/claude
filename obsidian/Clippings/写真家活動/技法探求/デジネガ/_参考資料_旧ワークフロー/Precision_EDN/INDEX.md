# Precision EDN - ドキュメント INDEX

**最終更新**: 2026-03-09

---

## 📋 このディレクトリについて

Precision EDN（デジタルネガ精密キャリブレーションシステム）の完全ドキュメント集です。

**プログラム本体の場所**:
```
/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision_edn_v2/
```

---

## 🎯 すぐに使いたい時

### ⭐ START_HERE.md
**用途**: 後日すぐに使い始める
**内容**:
- 起動方法（Streamlit GUI）
- 完全ワークフロー
- トラブルシューティング
- チェックリスト

**こんな時に読む**:
- 「どうやって起動するんだっけ？」
- 「測定から本番までの流れは？」
- 「エラーが出た、どうしよう」

---

## 📖 使い方を知りたい時

### QUICK_REFERENCE.md
**用途**: コマンドとパスのクイックリファレンス
**内容**:
- よく使うコマンド
- 重要なパス
- 設定まとめ
- 超簡易ワークフロー

**こんな時に読む**:
- 「起動コマンドだけ知りたい」
- 「プリンター設定は何だっけ？」

### STREAMLIT_GUIDE.md
**用途**: Streamlit GUI の詳細使用方法
**内容**:
- 起動方法
- 各タブの使い方
- データアップロード
- LUT生成手順
- ダウンロード方法

**こんな時に読む**:
- 「GUIの各ボタンは何をするの？」
- 「CSVはどうやってアップロードする？」
- 「生成されたLUTはどこ？」

### USAGE.md
**用途**: コマンドライン版の使用方法
**内容**:
- CLIコマンド詳細
- テンプレート作成
- LUT生成
- オプション説明

**こんな時に読む**:
- 「GUIじゃなくてCLIで使いたい」
- 「スクリプトに組み込みたい」

### WORKFLOW_RGB_ColorBlocker.md
**用途**: RGB + Color Blocker 完全ワークフロー
**内容**:
- 測定フェーズ詳細
- 本番フェーズ詳細
- Photoshop操作
- プリンター設定
- 期待される結果

**こんな時に読む**:
- 「Photoshopでどう操作する？」
- 「Color Blockerって何？」
- 「プリンター設定の詳細は？」

---

## 🧠 理解を深めたい時

### ⭐ DESIGN_PHILOSOPHY.md
**用途**: プロジェクトの背景と設計思想を理解する
**内容**:
- なぜPrecision EDNを作ったのか
- どういう問題を解決するのか
- どうやって動作するのか
- 開発の経緯
- 他人への説明用（1分版・5分版）

**こんな時に読む**:
- 「そもそも何のためのシステム？」
- 「どういう仕組みで動いてるの？」
- 「他の人に説明したい」
- 「後で見返して思い出したい」

### ⭐ VERSION_COMPARISON.md
**用途**: Version 1 と Version 2 の違いを理解する
**内容**:
- Precision EDN Version 1の詳細
- Precision EDN Version 2の詳細
- 2つのアプローチの違い
- 使い分けガイド
- 今後の発展

**こんな時に読む**:
- 「Version 1と2は何が違うの？」
- 「なぜVersion 2を作ったの？」
- 「どっちを使えばいい？」
- 「アプローチの違いを理解したい」

### Precision_EDN_Version2_設計書.md
**用途**: Version 2の技術仕様を理解する
**内容**:
- Version 1からの変更点
- 設計思想の詳細
- カーブ設計の数式
- 測定プロトコル
- 検証計画

**こんな時に読む**:
- 「γ=1.8の根拠は？」
- 「弱逆Sカーブって何？」
- 「32点カーブの配置は？」
- 「測定の詳細は？」

### プラチナプリント×デジタルネガ設計_技術的総括.md
**用途**: デジタルネガの理論的背景を理解する
**内容**:
- デジタルネガの3つの非線形
- プラチナプリントの特性
- 和紙の光学特性
- 理論的基礎

**こんな時に読む**:
- 「そもそもなぜ補正が必要？」
- 「プラチナプリントの特性は？」
- 「理論的背景を知りたい」

---

## 📝 開発記録

### Precision_EDN_セッション記録_20260309.md
**用途**: 開発時の詳細記録
**内容**:
- 開発過程の会話記録
- 試行錯誤の記録
- 発見と決定の経緯

**こんな時に読む**:
- 「どうやって開発したの？」
- 「何を悩んで何を決めたの？」
- 「開発の詳細経緯を知りたい」

---

## 🗂️ プログラム関連

### README.md
**用途**: プロジェクト概要
**内容**:
- プロジェクト説明
- ファイル構成
- セットアップ方法

**こんな時に読む**:
- 「プロジェクト全体の概要は？」
- 「どんなファイルがあるの？」

---

## 📂 ファイル構成（全体）

```
Precision_EDN/
├── INDEX.md                                           ← このファイル
│
├── 🎯 すぐ使う系
│   ├── START_HERE.md                                  ⭐ 最重要
│   ├── QUICK_REFERENCE.md
│   └── WORKFLOW_RGB_ColorBlocker.md
│
├── 📖 使い方詳細系
│   ├── STREAMLIT_GUIDE.md
│   └── USAGE.md
│
├── 🧠 理論・設計思想系
│   ├── DESIGN_PHILOSOPHY.md                           ⭐ 理解のために最重要
│   ├── VERSION_COMPARISON.md                          ⭐ 違いの理解に最重要
│   ├── Precision_EDN_Version2_設計書.md
│   └── プラチナプリント×デジタルネガ設計_技術的総括.md
│
├── 📝 開発記録系
│   ├── Precision_EDN_セッション記録_20260309.md
│   └── README.md
```

---

## 🚀 推奨される読み方

### ケース1: 初めて使う

```
1. DESIGN_PHILOSOPHY.md
   → なぜ作ったのか、何をするのか理解

2. START_HERE.md
   → 実際に起動してみる

3. WORKFLOW_RGB_ColorBlocker.md
   → 測定から本番までの流れを理解
```

### ケース2: 後日使う

```
START_HERE.md だけ見れば OK
```

### ケース3: 問題が起きた

```
1. START_HERE.md のトラブルシューティング

2. STREAMLIT_GUIDE.md のトラブルシューティング

3. それでもダメなら開発記録を確認
```

### ケース4: 他人に説明する

```
DESIGN_PHILOSOPHY.md の最後:
- 1分バージョン
- 5分バージョン
```

### ケース5: Version 1と2の違いを知りたい

```
VERSION_COMPARISON.md を読む
```

### ケース6: 理論を深く理解したい

```
1. プラチナプリント×デジタルネガ設計_技術的総括.md
   → 理論的基礎

2. Precision_EDN_Version2_設計書.md
   → 技術仕様

3. DESIGN_PHILOSOPHY.md
   → 設計思想

4. VERSION_COMPARISON.md
   → アプローチの違い
```

---

## 🔗 プログラム本体へのアクセス

**プログラムフォルダ**:
```
/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision_edn_v2/
```

**中身**:
```
precision_edn_v2/
├── app.py                 # Streamlit GUIアプリ
├── main.py               # CLIプログラム
├── config.py             # 設定
├── data_input.py         # データ入力モジュール
├── curve_analyzer.py     # カーブ解析モジュール
├── inverse_curve.py      # 逆カーブ生成モジュール
├── lut_export.py         # LUTエクスポートモジュール
├── run_app.sh           # 起動スクリプト
├── requirements.txt     # 依存ライブラリ
├── data/                # 測定データ
└── output/              # 出力ファイル
    ├── luts/            # LUTファイル
    └── graphs/          # グラフPDF
```

---

## 📞 困った時は

1. **START_HERE.md** のトラブルシューティングを確認
2. 各ガイドの該当セクションを確認
3. エラーメッセージをよく読む
4. データCSVの形式を確認
5. プリンター設定を確認

---

## 🎯 最も重要な3つ

### 1. START_HERE.md
後日使う時に必須。これさえあればすぐ始められる。

### 2. DESIGN_PHILOSOPHY.md
なぜ作ったのか、何をするのか。後で見返す時に必須。

### 3. VERSION_COMPARISON.md
Version 1と2の違い。アプローチを理解するために必須。

---

**Precision EDN - Complete Documentation Index**
**Created: 2026-03-09**
**Location: デジタルネガ探究/Precision_EDN/**

「迷ったらSTART_HERE.mdを開く」
