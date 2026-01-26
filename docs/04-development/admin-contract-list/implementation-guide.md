# SCR002-admin-contract-list 実装ガイド

## 📋 概要

このドキュメントは、契約検索一覧画面（SCR002-admin-contract-list）の実装手順と技術的な詳細をまとめたガイドです。

## 🎯 実装スコープ

### フェーズ1: 基本機能（MVP）
- 契約一覧表示
- 基本的な検索機能
- ページネーション
- 詳細画面への遷移

### フェーズ2: 拡張機能
- 高度な検索フィルター
- ソート機能
- 契約新規登録モーダル
- 一括操作機能

### フェーズ3: 最適化
- パフォーマンスチューニング
- アクセシビリティ対応
- レスポンシブ最適化

## 🏗️ アーキテクチャ

### 技術スタック
```yaml
Frontend:
  Framework: Next.js 14 (App Router)
  Language: TypeScript
  Styling: Tailwind CSS + appTheme design tokens
  State: React Context / Zustand
  Forms: React Hook Form
  Validation: Zod
  Data Fetching: TanStack Query (React Query)

Backend:
  Runtime: Node.js
  Framework: Next.js API Routes
  Database: PostgreSQL
  ORM: Prisma
  Authentication: NextAuth.js + Entra ID

Testing:
  Unit: Jest + React Testing Library
  E2E: Playwright
  API: Supertest
```

### ディレクトリ構造
```
src/
├── app/
│   └── admin/
│       └── contracts/
│           ├── page.tsx              # 契約一覧ページ
│           ├── layout.tsx            # レイアウト
│           ├── loading.tsx           # ローディング
│           └── error.tsx             # エラーハンドリング
│
├── components/
│   └── admin/
│       └── contracts/
│           ├── ContractList/
│           │   ├── index.tsx         # メインコンポーネント
│           │   ├── ContractTable.tsx # テーブル表示
│           │   ├── ContractCard.tsx  # カード表示（モバイル）
│           │   └── styles.module.css
│           ├── ContractSearch/
│           │   ├── index.tsx
│           │   ├── SearchForm.tsx
│           │   └── FilterPanel.tsx
│           ├── ContractModal/
│           │   ├── index.tsx
│           │   ├── CompanyForm.tsx
│           │   ├── ContractForm.tsx
│           │   └── UserForm.tsx
│           └── shared/
│               ├── Pagination.tsx
│               ├── StatusBadge.tsx
│               └── ActionButtons.tsx
│
├── lib/
│   ├── api/
│   │   └── contracts/
│   │       ├── client.ts             # APIクライアント
│   │       ├── types.ts              # 型定義
│   │       └── hooks.ts              # カスタムフック
│   ├── utils/
│   │   ├── validation.ts             # バリデーション
│   │   ├── formatting.ts             # フォーマット
│   │   └── date.ts                   # 日付処理
│   └── constants/
│       └── contracts.ts              # 定数定義
│
├── services/
│   └── contracts/
│       ├── ContractService.ts        # ビジネスロジック
│       └── ContractRepository.ts     # データアクセス
│
└── types/
    └── contracts.ts                   # グローバル型定義
```

## 📦 コンポーネント実装

### 1. ContractList コンポーネント

```typescript
// src/components/admin/contracts/ContractList/index.tsx
'use client';

import { useState, useCallback } from 'react';
import { useContracts } from '@/lib/api/contracts/hooks';
import { ContractTable } from './ContractTable';
import { ContractCard } from './ContractCard';
import { Pagination } from '../shared/Pagination';
import { appTheme } from '@/styles';
import styles from './styles.module.css';

interface ContractListProps {
  initialFilters?: ContractFilters;
}

export function ContractList({ initialFilters }: ContractListProps) {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(10);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const { data, isLoading, error } = useContracts({
    page,
    perPage,
    ...initialFilters,
  });

  const handleSelectAll = useCallback(() => {
    if (selectedIds.length === data?.contracts.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(data?.contracts.map(c => c.contract_id) || []);
    }
  }, [selectedIds, data]);

  const handleSelect = useCallback((id: string) => {
    setSelectedIds(prev =>
      prev.includes(id)
        ? prev.filter(i => i !== id)
        : [...prev, id]
    );
  }, []);

  if (isLoading) {
    return <div className={styles.loading}>読み込み中...</div>;
  }

  if (error) {
    return <div className={styles.error}>エラーが発生しました</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span style={{ color: appTheme.textColors.primary }}>
          検索結果: {data?.total || 0}件
        </span>
        {selectedIds.length > 0 && (
          <BulkActions
            selectedIds={selectedIds}
            onClear={() => setSelectedIds([])}
          />
        )}
      </div>

      {/* デスクトップ表示 */}
      <div className={styles.desktopOnly}>
        <ContractTable
          contracts={data?.contracts || []}
          selectedIds={selectedIds}
          onSelectAll={handleSelectAll}
          onSelect={handleSelect}
        />
      </div>

      {/* モバイル表示 */}
      <div className={styles.mobileOnly}>
        {data?.contracts.map(contract => (
          <ContractCard
            key={contract.contract_id}
            contract={contract}
            selected={selectedIds.includes(contract.contract_id)}
            onSelect={() => handleSelect(contract.contract_id)}
          />
        ))}
      </div>

      <Pagination
        currentPage={page}
        totalPages={data?.total_pages || 1}
        perPage={perPage}
        onPageChange={setPage}
        onPerPageChange={setPerPage}
      />
    </div>
  );
}
```

### 2. 検索フォーム実装

```typescript
// src/components/admin/contracts/ContractSearch/SearchForm.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { contractSearchSchema } from '@/lib/validation/contracts';
import { appTheme } from '@/styles';
import styles from './styles.module.css';

interface SearchFormData {
  contractId?: string;
  companyName?: string;
  startDateFrom?: string;
  startDateTo?: string;
  endDateFrom?: string;
  endDateTo?: string;
}

interface SearchFormProps {
  onSearch: (data: SearchFormData) => void;
  onClear: () => void;
}

export function SearchForm({ onSearch, onClear }: SearchFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<SearchFormData>({
    resolver: zodResolver(contractSearchSchema),
  });

  const handleClear = () => {
    reset();
    onClear();
  };

  return (
    <form
      onSubmit={handleSubmit(onSearch)}
      className={styles.searchForm}
    >
      <div className={styles.formRow}>
        <div className={styles.formGroup}>
          <label
            htmlFor="contractId"
            style={{ fontSize: appTheme.fontSize.ja.body }}
          >
            契約ID
          </label>
          <input
            id="contractId"
            type="text"
            {...register('contractId')}
            placeholder="契約IDを入力"
            style={{
              fontSize: appTheme.fontSize.ja.body,
              padding: appTheme.padding.xs,
            }}
          />
          {errors.contractId && (
            <span
              className={styles.error}
              style={{ color: appTheme.colors.danger }}
            >
              {errors.contractId.message}
            </span>
          )}
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="companyName">企業名</label>
          <input
            id="companyName"
            type="text"
            {...register('companyName')}
            placeholder="企業名を入力"
          />
        </div>
      </div>

      <div className={styles.formRow}>
        <div className={styles.formGroup}>
          <label>契約期間</label>
          <div className={styles.dateRange}>
            <input
              type="date"
              {...register('startDateFrom')}
            />
            <span>～</span>
            <input
              type="date"
              {...register('startDateTo')}
            />
          </div>
        </div>
      </div>

      <div className={styles.formActions}>
        <button
          type="button"
          onClick={handleClear}
          className={styles.secondaryButton}
          style={{
            backgroundColor: appTheme.colors.surface,
            color: appTheme.textColors.secondary,
          }}
        >
          クリア
        </button>
        <button
          type="submit"
          className={styles.primaryButton}
          style={{
            backgroundColor: appTheme.colors.primary,
            color: appTheme.textColors.onFill,
          }}
        >
          検索
        </button>
      </div>
    </form>
  );
}
```

### 3. API クライアント実装

```typescript
// src/lib/api/contracts/client.ts
import { Contract, ContractSearchParams, ContractCreateParams } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

class ContractApiClient {
  private async request<T>(
    path: string,
    options?: RequestInit
  ): Promise<T> {
    const token = await this.getAccessToken();

    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new ApiError(error.message, response.status, error.code);
    }

    return response.json();
  }

  private async getAccessToken(): Promise<string> {
    // NextAuth.jsからトークンを取得
    const session = await getSession();
    if (!session?.accessToken) {
      throw new Error('認証が必要です');
    }
    return session.accessToken;
  }

  async getContracts(params?: ContractSearchParams) {
    const queryParams = new URLSearchParams();

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
    }

    return this.request<ContractListResponse>(
      `/admin/contracts?${queryParams}`
    );
  }

  async getContract(id: string) {
    return this.request<Contract>(`/admin/contracts/${id}`);
  }

  async createContract(data: ContractCreateParams) {
    return this.request<Contract>('/admin/contracts', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateContract(id: string, data: Partial<Contract>) {
    return this.request<Contract>(`/admin/contracts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteContract(id: string) {
    return this.request<void>(`/admin/contracts/${id}`, {
      method: 'DELETE',
    });
  }

  async bulkAction(
    action: string,
    contractIds: string[],
    params?: any
  ) {
    return this.request('/admin/contracts/bulk', {
      method: 'POST',
      body: JSON.stringify({
        action,
        contract_ids: contractIds,
        params,
      }),
    });
  }
}

export const contractApi = new ContractApiClient();
```

### 4. カスタムフック実装

```typescript
// src/lib/api/contracts/hooks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contractApi } from './client';
import { toast } from '@/lib/toast';

export function useContracts(params?: ContractSearchParams) {
  return useQuery({
    queryKey: ['contracts', params],
    queryFn: () => contractApi.getContracts(params),
    staleTime: 5 * 60 * 1000, // 5分
  });
}

export function useContract(id: string) {
  return useQuery({
    queryKey: ['contract', id],
    queryFn: () => contractApi.getContract(id),
    enabled: !!id,
  });
}

export function useCreateContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: contractApi.createContract,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] });
      toast.success('契約を登録しました');
    },
    onError: (error) => {
      toast.error('契約の登録に失敗しました');
      console.error(error);
    },
  });
}

export function useUpdateContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Contract> }) =>
      contractApi.updateContract(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] });
      queryClient.invalidateQueries({ queryKey: ['contract', id] });
      toast.success('契約情報を更新しました');
    },
    onError: (error) => {
      toast.error('契約情報の更新に失敗しました');
      console.error(error);
    },
  });
}

export function useDeleteContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: contractApi.deleteContract,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] });
      toast.success('契約を削除しました');
    },
    onError: (error) => {
      toast.error('契約の削除に失敗しました');
      console.error(error);
    },
  });
}

export function useBulkAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      action,
      contractIds,
      params
    }: {
      action: string;
      contractIds: string[];
      params?: any;
    }) => contractApi.bulkAction(action, contractIds, params),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] });
      toast.success(`${data.succeeded}件の処理が完了しました`);
    },
    onError: (error) => {
      toast.error('一括処理に失敗しました');
      console.error(error);
    },
  });
}
```

## 🎨 スタイリング実装

### Tailwind CSS + appTheme の基本原則

- レイアウト、スペーシング、レスポンシブ挙動は Tailwind ユーティリティで表現する。
- 色・タイポグラフィ・余白などブランドトークンに紐づく値は `appTheme` から取得し、`style` 属性やカスタムユーティリティで注入する。
- `clsx` / `cn` による条件付きクラスの組み立て時も、変化する値はすべて `appTheme` 由来にする。
- テーブルやモーダルなど繰り返し利用するスタイルは、`@layer components` でカスタムクラス化し、その中で CSS 変数としてトークンを参照することを推奨。

### コンテナレイアウト例

```tsx
// src/components/admin/contracts/ContractList/Container.tsx
import { cn } from '@/lib/utils'
import { appTheme } from '@/styles'

type Props = React.PropsWithChildren<{ className?: string }>

export function ContractListContainer({ className, children }: Props) {
  return (
    <section
      className={cn(
        'flex flex-col gap-6 rounded-lg border border-slate-200 bg-white shadow-sm',
        'xl:grid xl:grid-cols-[1fr_320px] xl:items-start',
        className,
      )}
      style={{
        padding: appTheme.padding.lg,
        borderRadius: appTheme.borderRadius.lg,
        boxShadow: appTheme.shadow.sm,
      }}
    >
      {children}
    </section>
  )
}
```

### ステータスバッジ例

```tsx
// src/components/admin/contracts/StatusBadge.tsx
import { cn } from '@/lib/utils'
import { appTheme } from '@/styles'

const palette = {
  active: {
    backgroundColor: appTheme.colors.success_light,
    color: appTheme.colors.success,
  },
  expired: {
    backgroundColor: appTheme.colors.warning_light,
    color: appTheme.colors.warning,
  },
  cancelled: {
    backgroundColor: appTheme.colors.slate_200,
    color: appTheme.colors.slate_600,
  },
} as const

type Status = keyof typeof palette

export function StatusBadge({ status }: { status: Status }) {
  const tone = palette[status]

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium uppercase tracking-wide',
      )}
      style={{
        backgroundColor: tone.backgroundColor,
        color: tone.color,
      }}
    >
      {status}
    </span>
  )
}
```

### レスポンシブ戦略

- PC レイアウトは `xl:grid` でサイドバーを表示し、`md` 以下は `flex` にフォールバック。
- テーブルは `overflow-x-auto` を標準で付与し、モバイルは `hidden md:table` / `md:hidden` など Tailwind の可視制御クラスを使用する。
- `gap` や `padding` をブレークポイントごとに調整する場合も、値は `appTheme` を参照して `style` で上書きするか、Tailwind テーマ拡張でトークンを同期させる。

## 🔐 認証・認可実装

### NextAuth.js 設定

```typescript
// src/app/api/auth/[...nextauth]/route.ts
import NextAuth from 'next-auth';
import AzureADProvider from 'next-auth/providers/azure-ad';

const handler = NextAuth({
  providers: [
    AzureADProvider({
      clientId: process.env.AZURE_AD_CLIENT_ID!,
      clientSecret: process.env.AZURE_AD_CLIENT_SECRET!,
      tenantId: process.env.AZURE_AD_TENANT_ID!,
      authorization: {
        params: {
          scope: 'openid profile email User.Read',
        },
      },
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
        token.roles = await getUserRoles(account.access_token);
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken;
      session.user.roles = token.roles;
      return session;
    },
  },
  pages: {
    signIn: '/admin/login',
    error: '/admin/auth/error',
  },
});

export { handler as GET, handler as POST };
```

### 権限チェックミドルウェア

```typescript
// src/middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

export async function middleware(request: NextRequest) {
  const token = await getToken({
    req: request,
    secret: process.env.NEXTAUTH_SECRET,
  });

  const isAdminPath = request.nextUrl.pathname.startsWith('/admin');

  if (isAdminPath) {
    if (!token) {
      return NextResponse.redirect(
        new URL('/admin/login', request.url)
      );
    }

    if (!token.roles?.includes('nsw_admin')) {
      return NextResponse.redirect(
        new URL('/unauthorized', request.url)
      );
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/admin/:path*'],
};
```

## 🧪 テスト実装

### コンポーネントテスト

```typescript
// src/components/admin/contracts/ContractList/__tests__/index.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ContractList } from '../index';

const mockContracts = [
  {
    contract_id: 'CNT-2024-001',
    company: { name: '株式会社ABC', code: 'ABC001' },
    period: { start_date: '2024-04-01', end_date: '2025-03-31' },
    status: 'active',
  },
];

jest.mock('@/lib/api/contracts/hooks', () => ({
  useContracts: jest.fn(() => ({
    data: {
      total: 1,
      contracts: mockContracts,
      total_pages: 1,
    },
    isLoading: false,
    error: null,
  })),
}));

describe('ContractList', () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  it('契約一覧を表示する', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ContractList />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('株式会社ABC')).toBeInTheDocument();
      expect(screen.getByText('CNT-2024-001')).toBeInTheDocument();
    });
  });

  it('契約を選択できる', async () => {
    const user = userEvent.setup();

    render(
      <QueryClientProvider client={queryClient}>
        <ContractList />
      </QueryClientProvider>
    );

    const checkbox = await screen.findByRole('checkbox', {
      name: /CNT-2024-001/i
    });

    await user.click(checkbox);
    expect(checkbox).toBeChecked();
  });
});
```

### API テスト

```typescript
// src/app/api/admin/contracts/__tests__/route.test.ts
import { createMocks } from 'node-mocks-http';
import { GET, POST } from '../route';
import { prisma } from '@/lib/prisma';

jest.mock('@/lib/prisma', () => ({
  prisma: {
    contract: {
      findMany: jest.fn(),
      count: jest.fn(),
      create: jest.fn(),
    },
  },
}));

describe('/api/admin/contracts', () => {
  describe('GET', () => {
    it('契約一覧を返す', async () => {
      const mockContracts = [
        { id: '1', company_name: 'Test Company' },
      ];

      (prisma.contract.findMany as jest.Mock).mockResolvedValue(
        mockContracts
      );
      (prisma.contract.count as jest.Mock).mockResolvedValue(1);

      const { req } = createMocks({
        method: 'GET',
        headers: {
          authorization: 'Bearer valid-token',
        },
      });

      const response = await GET(req);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.success).toBe(true);
      expect(data.data.contracts).toEqual(mockContracts);
    });
  });

  describe('POST', () => {
    it('新規契約を作成する', async () => {
      const newContract = {
        company: { name: 'New Company', code: 'NEW001' },
        contract: { start_date: '2024-04-01', end_date: '2025-03-31' },
      };

      (prisma.contract.create as jest.Mock).mockResolvedValue({
        id: '2',
        ...newContract,
      });

      const { req } = createMocks({
        method: 'POST',
        headers: {
          authorization: 'Bearer valid-token',
        },
        body: newContract,
      });

      const response = await POST(req);
      const data = await response.json();

      expect(response.status).toBe(201);
      expect(data.success).toBe(true);
      expect(data.data.message).toBe('契約を登録しました');
    });
  });
});
```

### E2Eテスト

```typescript
// tests/e2e/admin-contracts.spec.ts
import { test, expect } from '@playwright/test';

test.describe('契約管理画面', () => {
  test.beforeEach(async ({ page }) => {
    // ログイン処理
    await page.goto('/admin/login');
    await page.fill('[name="email"]', 'admin@example.com');
    await page.fill('[name="password"]', 'password');
    await page.click('[type="submit"]');

    await page.waitForURL('/admin/contracts');
  });

  test('契約一覧を表示する', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('契約一覧');
    await expect(page.locator('table')).toBeVisible();
  });

  test('契約を検索する', async ({ page }) => {
    await page.fill('[placeholder="契約IDを入力"]', 'CNT-2024');
    await page.click('button:has-text("検索")');

    await expect(page.locator('table tbody tr')).toHaveCount(3);
  });

  test('新規契約を登録する', async ({ page }) => {
    await page.click('button:has-text("新規契約登録")');

    // モーダルが表示される
    await expect(page.locator('[role="dialog"]')).toBeVisible();

    // 企業情報入力
    await page.fill('[name="company.name"]', 'テスト企業');
    await page.fill('[name="company.code"]', 'TEST001');
    await page.fill('[name="company.email"]', 'test@example.com');

    // 契約情報入力
    await page.fill('[name="contract.start_date"]', '2024-04-01');
    await page.fill('[name="contract.end_date"]', '2025-03-31');

    await page.click('button:has-text("登録")');

    // 成功メッセージ
    await expect(page.locator('.toast')).toContainText('契約を登録しました');
  });
});
```

## 🚀 デプロイメント

### 環境変数設定

```bash
# .env.local
NEXT_PUBLIC_API_URL=https://api.rw-aoai.example.com/api/v1
NEXTAUTH_URL=https://app.rw-aoai.example.com
NEXTAUTH_SECRET=your-secret-key

# Azure AD
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_CLIENT_SECRET=your-client-secret
AZURE_AD_TENANT_ID=your-tenant-id

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/rw_aoai

# Redis (キャッシュ用)
REDIS_URL=redis://localhost:6379
```

### ビルド・デプロイコマンド

```bash
# 開発環境
bun install
bun run dev

# ビルド
bun run build
bun run start

# テスト実行
bun test
bun test:e2e

# 型チェック
bun run type-check

# リンター実行
bun run lint

# デプロイ（Vercel）
vercel --prod

# デプロイ（Docker）
docker build -t rw-aoai-app .
docker run -p 3000:3000 rw-aoai-app
```

## 📊 パフォーマンス最適化

### 1. データフェッチング最適化
- React Queryでキャッシュ管理
- ページネーションでデータ量制限
- 無限スクロール実装（オプション）

### 2. レンダリング最適化
- React.memoで不要な再レンダリング防止
- useMemoでコストの高い計算をメモ化
- 仮想スクロール実装（大量データ時）

### 3. バンドル最適化
- Dynamic importで遅延ロード
- Tree shakingで不要コード削除
- 画像最適化（next/image使用）

## 🔍 モニタリング

### エラートラッキング
```typescript
// Sentryセットアップ
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 1.0,
});
```

### パフォーマンス計測
```typescript
// Web Vitals計測
export function reportWebVitals(metric: NextWebVitalsMetric) {
  console.log(metric);
  // Google Analytics送信など
}
```

## 📝 開発チェックリスト

- [ ] UI実装
  - [ ] 契約一覧テーブル
  - [ ] 検索フォーム
  - [ ] ページネーション
  - [ ] ソート機能
  - [ ] モバイル対応

- [ ] API実装
  - [ ] 契約一覧取得
  - [ ] 契約詳細取得
  - [ ] 契約新規登録
  - [ ] 契約更新
  - [ ] 契約削除
  - [ ] 一括操作

- [ ] 機能実装
  - [ ] 検索機能
  - [ ] フィルター機能
  - [ ] CSVエクスポート
  - [ ] 契約登録モーダル
  - [ ] エラーハンドリング

- [ ] テスト
  - [ ] ユニットテスト
  - [ ] 統合テスト
  - [ ] E2Eテスト

- [ ] 最適化
  - [ ] パフォーマンス改善
  - [ ] アクセシビリティ対応
  - [ ] SEO対策

## 🔗 関連ドキュメント

- [UI仕様書](/docs/03-features/admin-contract-list/ui-specification.md)
- [API仕様書](/docs/03-features/admin-contract-list/api-specification.md)
- [機能要件定義書](/docs/02-requirements/functional-requirements.md)
- [アーキテクチャ設計書](/docs/01-architecture/)
