# Precision EDN v2

デジタルネガ キャリブレーション・解析プログラム

---

## 概要

プラチナプリント用デジタルネガの科学的なキャリブレーションを行うツールです。

### 主要機能

1. **測定データ解析**
   - 入力値 → ネガ濃度
   - ネガ濃度 → プリント濃度
   - 2段階測定の統合解析

2. **カーブ可視化**
   - プリンター特性曲線
   - プラチナプリント特性曲線
   - 合成特性曲線

3. **逆カーブ自動生成**
   - リニア化補正カーブ
   - Version 2設計(γ=1.8, 弱逆S)の適用

4. **LUT/カーブ出力**
   - CUBE LUT形式
   - Photoshop用カーブデータ
   - グラデーションマップ用RGB値

---

## ファイル構成

```
precision_edn_v2/
├── README.md              # このファイル
├── main.py               # メインプログラム
├── config.py             # 設定・定数
├── data_input.py         # CSV読み込み
├── curve_analyzer.py     # カーブ解析
├── inverse_curve.py      # 逆カーブ生成
├── lut_export.py         # LUT出力
├── utils.py              # ユーティリティ
├── data/                 # 測定データ保存
│   ├── measurement_template.csv
│   └── (測定データCSV)
└── output/               # 出力ファイル
    ├── graphs/
    ├── luts/
    └── reports/
```

---

## インストール

### 必要な環境

- Python 3.8 以上
- pip（Pythonパッケージマネージャー）

### 1. プロジェクトのダウンロード

```bash
# GitHubからクローン（または）
git clone https://github.com/yourusername/precision_edn_v2.git
cd precision_edn_v2

# またはZIPをダウンロードして解凍
```

### 2. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

または、Python仮想環境を使用する場合（推奨）：

```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 依存ライブラリのインストール
pip install -r requirements.txt
```

### 3. 動作確認

**コマンドライン版:**
```bash
python3 main.py --help
```

**Streamlit GUI版:**
```bash
streamlit run app.py
# または
./run_app.sh
```

ブラウザが自動的に開き、http://localhost:8501 でアプリが表示されます。

---

## 使用方法

### 1. 測定データ準備

33ステップチャートを印刷・測定し、CSVファイルを作成:

```csv
input,negative_density,print_density
0,1.55,0.05
8,1.52,0.08
16,1.47,0.12
...
255,0.10,2.10
```

### 2. プログラム実行

```bash
python3 main.py --input data/measurement_2026-03-09.csv
```

### 3. 出力確認

- `output/graphs/` : 解析グラフ(PDF)
- `output/luts/` : CUBE LUT
- `output/reports/` : 解析レポート

---

## Version 2 設計思想

### 基本パラメータ

- **ネガγ**: 1.8
- **カーブ形状**: 弱い逆Sカーブ
- **中間調基準**: 入力128 → ネガ濃度0.70
- **測定方法**: 2段階分離測定

### 対象環境

- プリンター: EPSON PX-1V
- メディア: ピクトリコOHP (TPS100)
- プロセス: 和紙プラチナプリント
- 光源: 蛍光UV
- 目標Dmax: 2.1

---

## 技術背景

詳細な技術的背景は以下を参照:

- [プラチナプリント×デジタルネガ設計_技術的総括.md](../obsidian/Clippings/写真家活動/技法探求/デジタルネガ探究/プラチナプリント×デジタルネガ設計_技術的総括.md)
- [Precision_EDN_Version2_設計書.md](../obsidian/Clippings/写真家活動/技法探求/デジタルネガ探究/Precision_EDN_Version2_設計書.md)

---

**作成**: 2026-03-09
**バージョン**: 2.0
**対象**: 和紙プラチナプリント × デジタルネガ
