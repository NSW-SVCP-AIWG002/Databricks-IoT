# Task Manager 開発環境構築ガイド

このガイドでは、タスク管理アプリプロジェクトの開発環境を構築する手順を説明します。

## 前提条件

以下のツールがインストールされていることを確認してください：

- **Bun**: v1.0 以上
- **Node.js**: v18.x 以上（バックアップとして）
- **Git**: 最新版
- **PostgreSQL**: v14.x 以上（または Supabase）

### 推奨開発環境
- **OS**: macOS / Linux / Windows (WSL2)
- **エディタ**: Cursor / VS Code
- **端末**: iTerm2 (macOS) / Windows Terminal

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/KOS-LLC/ai-dev-ops.git
cd ai-dev-ops
```

### 2. 依存関係のインストール

```bash
# ルートディレクトリで
bun install
```

### 3. バックエンド（task-api）のセットアップ

```bash
cd app/task-api

# 依存関係のインストール
bun install

# 環境変数の設定
cp .env.example .env
# .env を編集してSupabaseの接続情報を設定

# Prismaクライアント生成
bunx prisma generate

# データベースマイグレーション
bunx prisma migrate dev --name init

# 開発サーバーの起動
bun run dev
```

### 4. フロントエンド（task-web）のセットアップ

```bash
cd app/task-web

# 依存関係のインストール
bun install

# 開発サーバーの起動
bun run dev
```

### 5. 両方を同時に起動

```bash
# ルートディレクトリで
bun run dev
```

## 開発フロー

### 1. ブランチ戦略

```bash
# 機能開発
git checkout -b feature/機能名

# バグ修正
git checkout -b bugfix/バグ名

# ホットフィックス
git checkout -b hotfix/修正内容
```

### 2. コミットメッセージ

Conventional Commitsに従ってください：

```bash
# 機能追加
git commit -m "feat: ユーザー認証機能を追加"

# バグ修正
git commit -m "fix: ログイン時のエラーを修正"

# ドキュメント
git commit -m "docs: READMEを更新"
```

### 3. コードフォーマット

```bash
# フロントエンド
cd app/task-web
bun run lint

# バックエンド
cd app/task-api
# Prismaスキーマのフォーマット
bunx prisma format
```

## 便利なコマンド

### フロントエンド（task-web）

```bash
# 開発サーバー起動
bun run dev

# ビルド
bun run build

# 本番サーバー起動
bun run start

# リンター実行
bun run lint
```

### バックエンド（task-api）

```bash
# 開発サーバー起動
bun run dev

# ビルド
bun run build

# 本番サーバー起動
bun run start

# Prisma関連
bunx prisma generate
bunx prisma migrate dev
bunx prisma studio
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. bun installでエラーが発生する
```bash
# キャッシュをクリア
bun install --force

# node_modulesを削除して再インストール
rm -rf node_modules bun.lockb
bun install
```

#### 2. Prisma関連のエラー
```bash
# Prismaクライアントを再生成
bunx prisma generate

# データベースをリセット
bunx prisma migrate reset

# スキーマとデータベースを同期
bunx prisma db push
```

#### 3. データベース接続エラー
```bash
# Supabaseの接続情報を確認
# .envファイルのDATABASE_URLとDIRECT_URLを確認

# ネットワーク接続確認
ping aws-0-ap-northeast-1.pooler.supabase.com
```

#### 4. ポートが既に使用されている
```bash
# ポート3000, 3001を使用しているプロセスを確認
lsof -ti:3000
lsof -ti:3001

# プロセスを終了
kill -9 $(lsof -ti:3000)
kill -9 $(lsof -ti:3001)
```

## 開発に役立つリソース

- [ドキュメントホーム](../README.md)
- [タスク管理機能仕様](../03-features/task-management/)
- [コーディング規約](../00-rules/)

## 技術スタック詳細

### フロントエンド
- **Next.js 14**: React フレームワーク（App Router使用）
- **TypeScript**: 型安全な開発
- **Tailwind CSS**: ユーティリティファーストCSS

### バックエンド
- **Bun**: 高速JavaScriptランタイム
- **Hono**: 軽量Webフレームワーク
- **Prisma**: 型安全なORM
- **PostgreSQL**: リレーショナルデータベース（Supabase）

## サポート

開発で困ったことがあれば：

1. このドキュメントのトラブルシューティングを確認
2. GitHub Issueを作成
3. プロジェクトメンバーに相談

Happy Coding! 🚀 