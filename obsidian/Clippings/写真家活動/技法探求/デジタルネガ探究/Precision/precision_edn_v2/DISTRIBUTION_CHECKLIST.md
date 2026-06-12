# Precision EDN v2 - 配布チェックリスト

他の人と共有する前に確認すべき項目

---

## ✅ 必須ファイル

### プログラムコード
- [x] `app.py` - Streamlit GUIアプリ
- [x] `main.py` - コマンドライン版
- [x] `config.py` - 設定ファイル
- [x] `data_input.py` - データ入力モジュール
- [x] `curve_analyzer.py` - カーブ解析モジュール
- [x] `inverse_curve.py` - 逆カーブ生成モジュール
- [x] `lut_export.py` - LUT出力モジュール
- [ ] `utils.py` - ユーティリティ（あれば）

### 依存関係
- [x] `requirements.txt` - Python依存ライブラリリスト
  ```
  numpy>=1.20.0
  scipy>=1.7.0
  streamlit>=1.28.0
  pandas>=1.3.0
  matplotlib>=3.4.0
  Pillow>=9.0.0
  ```

### ドキュメント
- [x] `README.md` - メインドキュメント（インストール手順含む）
- [x] `START_HERE.md` - クイックスタートガイド
- [x] `USAGE.md` - 使用方法詳細
- [x] `DESIGN_PHILOSOPHY.md` - 設計思想
- [x] `QUICK_REFERENCE.md` - リファレンス
- [x] `WORKFLOW_RGB_ColorBlocker.md` - RGBワークフロー
- [x] `VERSION_COMPARISON.md` - バージョン比較
- [x] `STREAMLIT_GUIDE.md` - Streamlit使用ガイド

### 実行スクリプト
- [x] `run_app.sh` - アプリ起動スクリプト（実行権限確認）

### テンプレート・サンプル
- [ ] `data/measurement_template.csv` - 測定データテンプレート
- [ ] サンプル測定データ（あれば）

### ディレクトリ
- [x] `data/` - 測定データ保存用
- [x] `output/` - 出力ファイル用
  - [ ] `output/graphs/`
  - [ ] `output/luts/`
  - [ ] `output/reports/`

---

## 🔍 確認事項

### 1. requirements.txtの完全性

```bash
# 現在の環境で実際に必要なパッケージを確認
pip freeze > current_packages.txt

# requirements.txtと比較
diff requirements.txt current_packages.txt
```

**確認済み内容:**
- [x] `numpy` ✅
- [x] `scipy` ✅
- [x] `streamlit` ✅（追加済み）
- [x] `pandas` ✅（追加済み）
- [x] `matplotlib` ✅
- [x] `Pillow` ✅（追加済み）

### 2. 実行権限の確認

```bash
chmod +x run_app.sh
chmod +x main.py
```

### 3. 動作テスト

**クリーンな環境でのテスト:**

```bash
# 新しい仮想環境を作成
python3 -m venv test_env
source test_env/bin/activate

# requirements.txtからインストール
pip install -r requirements.txt

# 動作確認
streamlit run app.py
python3 main.py --help
```

### 4. 不要ファイルの除外

**.gitignoreに含めるべきもの:**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# 出力ファイル
output/graphs/*.pdf
output/luts/*.cube
output/reports/*.txt

# データファイル（サンプル以外）
data/*.csv
!data/measurement_template.csv

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# 一時ファイル
*.log
*.tmp
current_packages.txt
test_env/
```

---

## 📦 配布方法

### オプション1: GitHub

1. リポジトリ作成
2. .gitignoreを設定
3. プッシュ

```bash
git init
git add .
git commit -m "Initial commit: Precision EDN v2"
git remote add origin https://github.com/yourusername/precision_edn_v2.git
git push -u origin main
```

### オプション2: ZIP配布

```bash
# 配布用ZIPを作成（不要ファイルを除外）
cd ..
zip -r precision_edn_v2_release.zip precision_edn_v2 \
  -x "*.pyc" \
  -x "*/__pycache__/*" \
  -x "*/output/*" \
  -x "*.log" \
  -x "*/test_env/*" \
  -x "*/.DS_Store"
```

### オプション3: Docker（上級者向け）

`Dockerfile`を作成：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

---

## 📋 配布前の最終チェック

- [ ] すべての`.py`ファイルにdocstringがある
- [ ] `README.md`にインストール手順が記載されている
- [ ] `requirements.txt`が完全（全ての依存関係が含まれている）
- [ ] サンプルデータまたはテンプレートが含まれている
- [ ] 実行スクリプトに実行権限が付与されている
- [ ] 個人情報・秘密情報が含まれていない
- [ ] ライセンス表示がある（MIT, GPL等）
- [ ] クリーンな環境でインストール＆実行テストが成功
- [ ] バージョン番号が明記されている

---

## 📝 推奨: LICENSEファイルの追加

`LICENSE`ファイルを作成して、ライセンスを明示：

**MIT Licenseの例:**

```
MIT License

Copyright (c) 2026 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🎯 まとめ

**最低限必要なもの:**

1. ✅ プログラムコード（.pyファイル）
2. ✅ `requirements.txt`（完全版）
3. ✅ `README.md`（インストール手順含む）
4. ✅ サンプルデータまたはテンプレート
5. ⏳ `.gitignore`（GitHub使用時）
6. ⏳ `LICENSE`（ライセンス明示）

**現在の状態:**
- ✅ プログラムコード完備
- ✅ `requirements.txt`更新済み
- ✅ `README.md`にインストール手順追加済み
- ⚠️ 測定データテンプレートの確認必要
- ⚠️ `.gitignore`未作成
- ⚠️ `LICENSE`未作成

---

**作成日:** 2026-03-11
**バージョン:** 1.0
