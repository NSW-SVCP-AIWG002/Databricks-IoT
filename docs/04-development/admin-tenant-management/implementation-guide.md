# SCR010-admin-tenant-management 実装ガイド

## 📋 概要

このドキュメントは、テナント管理画面（SCR010-admin-tenant-management）の開発を遂行する際の技術的な指針と作業手順をまとめたものです。`docs/03-features/admin-tenant-management/` に定義された仕様（UI・API・テスト）をもとに実装を行います。

## 🎯 実装スコープ

### フェーズ1: MVP
- テナント一覧表示（テーブル／モバイルカード）
- 検索・フィルターフォーム（テナント名/ID、ステータス、プラン、作成日範囲）
- ページネーション・表示件数切り替え
- 利用状況サマリー表示（トークン／ストレージ進捗バー）

### フェーズ2: 管理操作
- 新規テナント登録モーダル
- 編集モーダル（プラン変更、上限更新、連絡先編集）
- ステータス変更（active/suspended/inactive）
- CSVエクスポート＆一括操作
- 成功・エラー用トースト通知

### フェーズ3: 品質強化
- アクセシビリティ対応（キーボード操作、ARIA属性、フォーカスマネジメント）
- パフォーマンス最適化（lazy fetch、仮想リスト検討）
- 監査ログ連携・操作履歴表示
- ユニット／統合／E2Eテスト拡充

## 🏗️ アーキテクチャ

### 技術スタック
```yaml
Frontend:
  Framework: Next.js 14 App Router
  Language: TypeScript
  Styling: Tailwind CSS + appTheme design tokens
  UI Components: 既存デザインシステム（`@/components/Button`, `Input`, `Select`, `Table`, `ModalOverlay` など）
  State: React hooks + Zustand (global filters) / TanStack Query
  Forms: React Hook Form + Zod

Backend:
  Runtime: Bun + Hono (API)
  Database: PostgreSQL
  ORM: Prisma
  Auth: Entra External ID + NextAuth

Testing:
  Unit: Vitest + React Testing Library
  Integration: Vitest + MSW + Testing Library
  E2E: Playwright
```

### ディレクトリ構造（提案）
```
src/
├── app/
│   └── admin/
│       └── tenants/
│           ├── page.tsx              # テナント一覧ページ
│           ├── layout.tsx            # レイアウト
│           ├── loading.tsx           # ローディングUI
│           ├── error.tsx             # エラーバウンダリ
│           └── head.tsx              # メタ情報
│
├── components/
│   └── admin/
│       └── tenants/
│           ├── TenantList/
│           │   ├── index.tsx         # 一覧コンテナ（ContractListのパターンを踏襲）
│           │   ├── TenantTable.tsx   # 共通Tableコンポーネントを利用
│           │   ├── TenantCard.tsx    # モバイルカード
│           │   ├── UsageSummary.tsx  # 利用状況バー（ContractUsageIndicator相当を再利用）
│           ├── TenantSearch/
│           │   ├── index.tsx
│           │   ├── SearchForm.tsx    # Input/Select/DatePickerは既存UIを使用
│           │   ├── QuickFilters.tsx
│           ├── TenantModals/
│           │   ├── CreateTenantModal.tsx  # ModalOverlayとFormFieldコンポーネントを活用
│           │   ├── EditTenantModal.tsx
│           │   ├── StatusChangeDialog.tsx
│           │   └── validation.ts
│           └── shared/
│               ├── TenantActionMenu.tsx
│               ├── TenantStatusBadge.tsx   # ContractStatusBadgeの派生
│               └── ExportMenu.tsx
│
├── lib/
│   ├── api/
│   │   └── tenants/
│   │       ├── client.ts             # fetchラッパー
│   │       ├── hooks.ts              # TanStack Query hooks
│   │       └── types.ts              # APIレスポンス型
│   ├── constants/
│   │   └── tenants.ts                # ステータス、プラン定義
│   └── utils/
│       ├── tenantFilters.ts          # クエリパラメータ整形
│       └── formatting.ts             # 日付・数値フォーマット
│
├── services/
│   └── tenants/
│       ├── TenantService.ts          # ドメインロジック
│       └── TenantRepository.ts       # DBアクセス
│
└── tests/
    ├── tenants/
    │   ├── TenantList.test.tsx       # ユニット/統合
    │   └── TenantFlows.spec.ts       # Playwright
    └── fixtures/
        └── tenants.ts                # テストデータ生成
```

## 🧩 実装ガイドライン

### 1. ページエントリ (`page.tsx`)
- `TenantSearch` と `TenantList` を組み合わせ、フィルター状態をURLクエリと同期。
- 初期データは `generateStaticParams` / `fetch` を使用せず、サーバーアクションまたはクライアントサイドで取得（管理画面のためSSR必須要件なし）。
- ローディング・エラーコンポーネントは `appTheme` のトークンでスタイル統一し、`LoadingSpinner` など既存のUIパーツを利用。

```tsx
// src/app/admin/tenants/page.tsx
import TenantSearch from '@/components/admin/tenants/TenantSearch';
import TenantList from '@/components/admin/tenants/TenantList';

export default function TenantManagementPage() {
  return (
    <section>
      <TenantSearch />
      <TenantList />
    </section>
  );
}
```

### 2. 検索フォーム
- `React Hook Form` + `Zod` (`tenantSearchSchema`) でバリデーション。
- 入力UIは `@/components/Input`, `Select`, `DatePicker`（存在する場合）を流用し、新規スタイルは作成しない。
- ページング・ソート状態と組み合わせるため、`useTenantFiltersStore`（Zustand）を導入。
- フィルター確定時は `router.push` でクエリを更新し、`useQuery` の `queryKey` を自動的に更新。

### 3. 一覧・テーブル
- `TenantTable` は `@/components/Table` と `TableCell` をベースに実装し、チェックボックス・ボタンは `Checkbox`/`Button` コンポーネントを利用。
- 行アクションは `TenantActionMenu` に集約し、`Icon`/`Menu` 等の既存パーツを採用。
- 利用状況サマリーは `ContractUsageIndicator` のロジックを流用し、80%以上で警告色（`appTheme.colors.warning`）を適用。
- レスポンシブ対応：≥768px はテーブル、<768px は `TenantCard` 表示。

### 4. モーダル / ダイアログ
- `CreateTenantModal` : `ModalOverlay` と `@/components/Modal`系共通フレームを利用。初期管理者メール入力を `FieldArray` で複数対応し、`Input`/`Select` を再利用。登録前に `tenantService.validateUniqueId` を呼び重複チェック。
- `EditTenantModal` : プラン変更時に `usage_limits` をボタンで推奨値へセット。UIボタンは `Button` コンポーネントで統一し、API成功後に `queryClient.invalidateQueries(['tenants'])`。
- `StatusChangeDialog` : `ModalOverlay` + `Button` + `Checkbox` 等既存パーツを組み合わせ、confirm→API→成功トースト→`invalidateQueries`→`modal.close()` の順。失敗時はエラートーストとフォーカスリセット。

### 5. API クライアント
- `client.ts` で共通の `request` ヘルパを用意し、Authorizationヘッダーを付与。
- 例: `listTenants`, `createTenant`, `updateTenant`, `changeTenantStatus`, `deleteTenant`, `exportTenants`.
- エラー時は `APIError` を投げ、UI側で `error.code` に応じたメッセージを表示。`docs/03-features/admin-tenant-management/api-specification.md` のエラーコード一覧に準拠。
- 成功・失敗トーストは `@/components/Toast` など既存の通知システムに統合する。

### 6. 状態管理
- フィルター: Zustand ストア `useTenantFiltersStore`.
- 選択行: `useState<string[]>` で管理。ページ切替時は自動リセット。
- モーダル制御: `useDisclosure` ヘルパー（存在しなければ共通フックを作成）で状態を一元管理。

### 7. テーマ・スタイリング
- カラー・スペーシングはすべて `appTheme` のトークンを使用し、Tailwindクラスにはアプリ共通のCSS変数マッピングを活用。
- 状態バッジ色例：
  - active → `appTheme.status.success`
  - suspended → `appTheme.status.warning`
  - inactive → `appTheme.status.neutral`
- バッジ実装は `ContractStatusBadge` をベースに `TenantStatusBadge` を薄いラッパーとして実装し、ロジック重複を避ける。
- モーダルは共通レイアウト（ヘッダー・コンテンツ・フッター）を共用コンポーネント化し、アクセシビリティ属性（`role="dialog"`, `aria-modal="true"`）を設定。

## 🔌 バックエンド連携

### エンドポイント対応表
| UI操作 | API | メソッド |
|--------|-----|----------|
| 一覧取得 | `/admin/tenants` | GET |
| 詳細取得 | `/admin/tenants/{tenantId}` | GET |
| 登録 | `/admin/tenants` | POST |
| 更新 | `/admin/tenants/{tenantId}` | PUT |
| ステータス変更 | `/admin/tenants/{tenantId}/status` | PATCH |
| 削除 | `/admin/tenants/{tenantId}` | DELETE |
| CSV出力 | `/admin/tenants/export` | GET |

### サーバー実装ポイント
- Hono ルーターで `admin/tenants` グループを作成。JWT ミドルウェアで `admin.tenants.*` 権限チェック。
- Prisma モデル例：
  ```prisma
  model Tenant {
    id              String   @id
    name            String
    contractId      String
    status          TenantStatus
    plan            TenantPlan
    adminUsers      Int
    seats           Int
    tokenLimit      Int
    tokenUsed       Int
    storageLimitGb  Int
    storageUsedGb   Float
    createdAt       DateTime @default(now())
    updatedAt       DateTime @updatedAt
  }
  ```
- レスポンスは API仕様のキーに一致させる（`tenant_id`, `tenant_name` 等）。
- ステータス変更・削除は冪等にし、監査ログ（tenant_id, action, actor）を必ず記録。

## 🧪 テスト戦略

`docs/03-features/admin-tenant-management/test-specification.md` に沿ってテストを実装する。

- **ユニットテスト**
  - `tenantFilters.ts`のクエリ生成
  - `TenantStatusBadge` のステータス別スタイル
  - フォームバリデーションスキーマ
- **統合テスト**
  - MSW を利用して `/admin/tenants` をモックし、検索→一覧レンダリングまでを検証。
  - モーダル送信→成功トースト→一覧再取得の一連の挙動。
- **E2Eテスト**
  - Playwright で登録／編集／削除のCUJを再現。`bun run test:e2e:setup` でシードデータを準備。
  - スクリーンショット・ビデオは CI アーティファクトに保存。

## ⚙️ 設定・環境変数

`.env` 例（セキュアストレージで管理）
```
API_BASE_URL=https://api.rw-aoai.example.com/api/v1
TENANT_EXPORT_BUCKET=rw-aoai-tenant-export
```
- Entra ID テナントID (`AZURE_AD_TENANT_ID`) は既存契約機能と共通値を使用。
- テスト用には `.env.test` を用意し、MSW + InMemory DBに切り替える。

## 📈 モニタリング・運用

- 監査ログ：`TENANT_CREATE`, `TENANT_UPDATE`, `TENANT_SUSPEND`, `TENANT_DELETE` を記録。
- メトリクス：一覧表示のレスポンスタイム（P95 < 3s）、登録成功率、ステータス変更失敗率。
- アラート：API 5xx が 5分間で5件以上発生した場合に通知。Playwright 失敗時はSlack連携。

## ✅ 作業チェックリスト

- [ ] UI仕様・API仕様との差異レビュー済み
- [ ] appTheme トークンのみでスタイル定義
- [ ] Button/Table/Modalなど共通UIコンポーネントの再利用を確認
- [ ] TanStack Query キャッシュキーと無効化ロジック実装
- [ ] API エラーハンドリング（コード別メッセージ）対応
- [ ] バリデーションエラー時のフォーカス制御
- [ ] Lighthouse アクセシビリティ スコア 90 以上
- [ ] ユニット／統合テストを追加し `bun test` パス
- [ ] Playwright シナリオを追加し `bun run test:e2e` パス
- [ ] ドキュメント（README, テスト仕様）最新化確認

---
*最終更新日: 2025年10月25日*
