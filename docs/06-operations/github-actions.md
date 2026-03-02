# GitHub Actions 運用ガイド

このドキュメントでは、タスク管理アプリで利用している GitHub Actions ワークフローと、その活用方法・運用時の注意点をまとめます。

## ワークフロー一覧

| ワークフロー名 | ファイル | 主な目的 | トリガー |
| --- | --- | --- | --- |
| Task API Tests | `.github/workflows/task-api-test.yml` | API レイヤーのユニットテストを Bun で実行する | `app/task-api/**` の変更を含む push / PR |
| E2E Tests | `.github/workflows/e2e-test.yml` | Playwright を利用した E2E テストを CI 上で実施する | main への push、特定ブランチの PR |

## 各ワークフローの詳細

### Task API Tests
- `app/task-api` 配下の変更時に発火し、Bun と Prisma クライアントをセットアップして `bun test:unit` を実行します。
- `working-directory` を `./app/task-api` に固定しているため、テスト用スクリプトは同ディレクトリで管理してください。
- Prisma スキーマや依存関係の更新時は、CI 上でも `bun run db:generate` が成功するかローカルで確認しておくと安全です。

### E2E Tests
- main ブランチへの push と、`app/task-api/**`・`app/task-web/**`・`e2e/**` を変更する PR で実行されます。
- PostgreSQL サービスを CI 上に起動し、API のマイグレーション (`bun run db:push`) を適用してから Playwright の E2E テストを実行します。
- 失敗時の調査向けに Playwright レポートをアーティファクトとして 30 日間保存します。再現が難しい不具合はレポートをダウンロードして確認してください。

## Secrets と権限の管理

現状のワークフローでは GitHub リポジトリに追加の Secrets を設定する必要はありません。リポジトリ権限はデフォルト設定で問題ありませんが、新しいワークフローを追加する際は必要最小限の権限のみを付与する方針を維持してください。

## よくある運用タスク

### ワークフローを手動再実行する
1. GitHub の Actions タブで対象ジョブを選択します。
2. 失敗したジョブを開き、`Re-run jobs` をクリックします。
3. 依存パッケージやマイグレーションを更新した場合は、再実行前にローカルでも手順どおり動作するか確認しておくと安心です。

### 新しいワークフローを追加する際のガイドライン
- Bun を利用する処理では `oven-sh/setup-bun@v1` を使い、`bun install` の実行漏れに注意します。
- データベースが必要なケースは、`services` セクションでコンテナを立ち上げ、ヘルスチェックを定義してからテストを実行します。
- ワークフローやジョブの `permissions` は最小権限を明記し、不要な `write` 権限は付与しないようにします。
- アーティファクトやキャッシュを利用する場合は、保存期間や容量の上限にも注意してください。

### トラブルシューティング
- `setup-bun` でバージョン解決に失敗する場合は、`bun-version` を固定値で指定します。
- Playwright の依存解決エラーは `bunx playwright install --with-deps` が実行されているか確認し、CI 上でブラウザバイナリが取得できるようにします。
- E2E テストでデータベース接続に失敗する場合は、PostgreSQL サービスのヘルスチェック設定とポート競合の有無を確認してください。

## 参考リンク

- [GitHub Actions 公式ドキュメント](https://docs.github.com/ja/actions)
- [Playwright CI ガイド](https://playwright.dev/docs/ci)
