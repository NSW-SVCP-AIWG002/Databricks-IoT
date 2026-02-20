# app-templates

## 概要

このリポジトリは、Flask Webアプリケーションの開発環境テンプレートです。
**Gitからクローンするだけで、すぐに開発を始めることができます。**

srcフォルダで開発を行います。

## 開発環境のセットアップ

### 前提条件

- Git
- Docker（Dev Container使用の場合）
- Python 3.11以上（ローカル開発の場合）

### セットアップ手順

#### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd app
```

#### 2. 開発環境の起動

**方法A: Dev Container使用（推奨）**

VS Codeでリポジトリを開き、Dev Containerで再度開きます：

1. VS Codeでフォルダを開く
2. コマンドパレット（Ctrl+Shift+P / Cmd+Shift+P）から「Dev Containers: Reopen in Container」を選択
3. コンテナのビルドと起動を待つ

→ **これだけで開発環境が自動的に構築されます！**

**方法B: ローカル環境**

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定（必要に応じて）
cp .env.example .env
# .envファイルを編集
```

#### 3. アプリケーションの起動

**Hello World アプリ：**

```bash
cd src/flask-hello-world-app
flask --app app.py run
```

ブラウザで `http://127.0.0.1:5000/` にアクセス

**ユーザー管理アプリ：**

```bash
cd src/test
python test.py
```

ブラウザで `http://127.0.0.1:5001/` にアクセス

## プロジェクト構成

```
/
├── .devcontainer/          # Dev Container設定
│   └── devcontainer.json   # Python 3.11環境
├── .vscode/                # VS Code設定
│   └── settings.json       # Jupyter設定
├── docs/                   # 設計ドキュメント
├── src/                    # アプリケーションコード（開発フォルダ）
│   ├── flask-hello-world-app/  # Hello Worldサンプル
│   │   ├── app.py
│   │   └── app.yaml
│   └── test/               # ユーザー管理サンプル
│       ├── test.py
│       └── templates/
│           └── users.html
├── Dockerfile              # Docker設定
├── requirements.txt        # Python依存関係
├── .env.example            # 環境変数テンプレート
├── .gitignore              # Git除外設定
└── README.md               # このファイル
```

## 技術スタック

- **言語**: Python 3.11
- **Webフレームワーク**: Flask 3.0+
- **データ処理**: pandas 2.0+
- **開発環境**: Dev Container (VS Code)
- **コンテナ**: Docker

## 開発コマンド

### 依存関係の管理

```bash
# 依存関係のインストール
pip install -r requirements.txt

# パッケージの追加（例）
pip install <package-name>
# requirements.txtに追記
echo "<package-name>>=<version>" >> requirements.txt
```

### アプリケーションの実行

```bash
# Flaskアプリの起動（デバッグモード）
flask --app src/flask-hello-world-app/app.py run --debug

# 特定のポートで起動
flask --app src/flask-hello-world-app/app.py run --port 8000

# 外部アクセスを許可
flask --app src/flask-hello-world-app/app.py run --host 0.0.0.0
```

### Dockerでの起動

```bash
# イメージのビルド
docker build -t flask-app .

# コンテナの起動
docker run -p 5000:5000 flask-app

# バックグラウンドで起動
docker run -d -p 5000:5000 flask-app
```

## 開発の始め方

1. **リポジトリをクローン**
2. **Dev Containerで開く**（または `pip install -r requirements.txt`）
3. **srcフォルダで開発開始**

これだけで、すぐに開発を始められます！

## ライセンス

詳細は `LICENSE` ファイルを参照してください。
