# Precision EDN v2 - インストールガイド

**簡単3ステップで始められます！**

---

## 📋 必要な環境

- **Python 3.8以上** （3.9または3.10推奨）
- **pip** （Pythonパッケージマネージャー）
- **インターネット接続** （初回インストール時のみ）

### Pythonのバージョン確認

```bash
python3 --version
```

**出力例:** `Python 3.9.7`

もしPythonがインストールされていない場合：
- **macOS**: [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **Windows**: [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **Linux**: `sudo apt install python3 python3-pip` (Ubuntu/Debian)

---

## 🚀 インストール手順

### ステップ1: プロジェクトのダウンロード

**方法A: GitHubからクローン（推奨）**

```bash
git clone https://github.com/yourusername/precision_edn_v2.git
cd precision_edn_v2
```

**方法B: ZIPファイルをダウンロード**

1. GitHubページから「Code」→「Download ZIP」
2. ダウンロードしたZIPを解凍
3. ターミナル/コマンドプロンプトで解凍したフォルダに移動

```bash
cd /path/to/precision_edn_v2
```

### ステップ2: 依存ライブラリのインストール

**方法A: 直接インストール（簡単）**

```bash
pip3 install -r requirements.txt
```

**方法B: 仮想環境を使用（推奨、環境を汚さない）**

```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
# macOS/Linux:
source venv/bin/activate

# Windows（コマンドプロンプト）:
venv\Scripts\activate.bat

# Windows（PowerShell）:
venv\Scripts\Activate.ps1

# 依存ライブラリのインストール
pip install -r requirements.txt
```

**インストールされるパッケージ:**
- `numpy` - 数値計算
- `scipy` - 科学技術計算
- `streamlit` - Webアプリフレームワーク
- `pandas` - データ処理
- `matplotlib` - グラフ描画
- `Pillow` - 画像処理

### ステップ3: 動作確認

**GUI版（Streamlitアプリ）を起動:**

```bash
streamlit run app.py
```

または、起動スクリプトを使用：

```bash
./run_app.sh
```

**成功すると:**
- ブラウザが自動的に開きます
- アドレス: `http://localhost:8501`
- Precision EDN v2のインターフェースが表示されます

**コマンドライン版の確認:**

```bash
python3 main.py --help
```

---

## ❓ トラブルシューティング

### エラー: `command not found: python3`

**解決策:**
- `python`を試してください: `python --version`
- Pythonをインストールしてください

### エラー: `ModuleNotFoundError: No module named 'streamlit'`

**解決策:**
- requirements.txtからのインストールが失敗しています
- 再度実行: `pip3 install -r requirements.txt`
- pipのアップグレード: `pip3 install --upgrade pip`

### エラー: `Permission denied: ./run_app.sh`

**解決策:**
- 実行権限を付与: `chmod +x run_app.sh`

### Streamlitアプリがブラウザで開かない

**解決策:**
- 手動でブラウザを開き、`http://localhost:8501`にアクセス
- ポートが使用中の場合: `streamlit run app.py --server.port 8502`

### Windows PowerShellで仮想環境が有効化できない

**エラー:** `cannot be loaded because running scripts is disabled`

**解決策:**
```powershell
# PowerShellを管理者権限で開き、実行
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 再度仮想環境を有効化
venv\Scripts\Activate.ps1
```

---

## 📦 アンインストール

### 仮想環境を使用した場合

```bash
# 仮想環境を無効化
deactivate

# プロジェクトフォルダごと削除
cd ..
rm -rf precision_edn_v2
```

### 直接インストールした場合

```bash
# インストールしたパッケージを削除（任意）
pip3 uninstall numpy scipy streamlit pandas matplotlib Pillow

# プロジェクトフォルダを削除
cd ..
rm -rf precision_edn_v2
```

---

## ✅ インストール確認チェックリスト

- [ ] Python 3.8以上がインストールされている
- [ ] プロジェクトフォルダに移動できた
- [ ] `requirements.txt`が存在する
- [ ] `pip install -r requirements.txt`が成功した
- [ ] `streamlit run app.py`でアプリが起動した
- [ ] ブラウザでGUIが表示された

---

## 🎓 次のステップ

インストールが完了したら：

1. **[START_HERE.md](START_HERE.md)** を読む
2. **[USAGE.md](USAGE.md)** で使い方を学ぶ
3. サンプルデータで試してみる: `data/measurement_template.csv`

---

## 📞 サポート

問題が解決しない場合：

- GitHubのIssueを作成
- ドキュメントを確認: [README.md](README.md)
- システム情報を記載:
  ```bash
  python3 --version
  pip3 --version
  uname -a  # macOS/Linux
  systeminfo  # Windows
  ```

---

**最終更新:** 2026-03-11
**バージョン:** 2.0
