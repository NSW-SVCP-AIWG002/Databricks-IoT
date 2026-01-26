# API実装ベストプラクティス

## 📑 目次

1. [概要](#1-概要)
2. [クライアント側キャッシュ実装](#2-クライアント側キャッシュ実装)
   - 2.1 [React Query使用時の基本実装](#21-react-query使用時の基本実装)
   - 2.2 [APIクライアント実装](#22-apiクライアント実装)
3. [クライアント側ページネーション実装](#3-クライアント側ページネーション実装)
   - 3.1 [基本的な実装方法](#31-基本的な実装方法)
   - 3.2 [実装例（基本）](#32-実装例基本)
   - 3.3 [React Query + TanStack Table での実装例](#33-react-query--tanstack-table-での実装例)
   - 3.4 [利点](#34-利点)
   - 3.5 [注意事項](#35-注意事項)
4. [クライアント側ソート実装](#4-クライアント側ソート実装)
   - 4.1 [基本的な実装方法](#41-基本的な実装方法)
   - 4.2 [実装例（基本）](#42-実装例基本)
   - 4.3 [実装例（日本語対応）](#43-実装例日本語対応)
   - 4.4 [実装例（日付ソート）](#44-実装例日付ソート)
   - 4.5 [React Query での実装例](#45-react-query-での実装例)
   - 4.6 [ソート可能なフィールド（例）](#46-ソート可能なフィールド例)
   - 4.7 [利点](#47-利点)
   - 4.8 [注意事項](#48-注意事項)
5. [サーバーサイドページネーション実装](#5-サーバーサイドページネーション実装)
   - 5.1 [大量データ（ドキュメント一覧など）の実装](#51-大量データドキュメント一覧などの実装)
   - 5.2 [デバウンスフック実装](#52-デバウンスフック実装)
6. [戦略切り替え可能な実装パターン](#6-戦略切り替え可能な実装パターン)
   - 6.1 [カスタムフック: useListData](#61-カスタムフック-uselistdata)
   - 6.2 [使用例](#62-使用例)
7. [パフォーマンス最適化](#7-パフォーマンス最適化)
   - 7.1 [デバウンス処理（検索入力時）](#71-デバウンス処理検索入力時)
   - 7.2 [ローディング状態の表示](#72-ローディング状態の表示)
   - 7.3 [前のデータを保持（ページ切り替え時）](#73-前のデータを保持ページ切り替え時)
   - 7.4 [短時間キャッシュ（サーバーサイドでも許容）](#74-短時間キャッシュサーバーサイドでも許容)
8. [サーバーサイド実装](#8-サーバーサイド実装)
   - 8.1 [データベースインデックスの最適化](#81-データベースインデックスの最適化)
   - 8.2 [ページネーションクエリの実装（Node.js + Prisma）](#82-ページネーションクエリの実装nodejs--prisma)
   - 8.3 [ページネーションクエリの実装（SQL直接）](#83-ページネーションクエリの実装sql直接)
   - 8.4 [レスポンス時間の最適化](#84-レスポンス時間の最適化)
9. [関連ドキュメント](#9-関連ドキュメント)

---

## 1. 概要

このドキュメントは、API共通仕様書に基づいた実装のベストプラクティスを提供します。

**関連ドキュメント:**
- [API共通仕様書](./common-specification.md) - 仕様の詳細
- [APIガイド](./api-guide.md) - API仕様書・処理設計書の作成方法

---

## 2. クライアント側キャッシュ実装

### 2.1 React Query使用時の基本実装

```typescript
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

const GroupList = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(10);
  const [keyword, setKeyword] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [order, setOrder] = useState<'asc' | 'desc'>('asc');

  // ✅ 全件取得してキャッシュ
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['groups'], // キャッシュキー
    queryFn: () => fetchGroups({ per_page: 1000 }), // 全件取得
    staleTime: 5 * 60 * 1000,  // 5分間は新鮮とみなす
    cacheTime: 30 * 60 * 1000, // 30分間メモリに保持
  });

  // ❌ APIコールなし（クライアント側フィルタリング）
  const filteredGroups = useMemo(() => {
    if (!data?.items) return [];
    return data.items.filter(g =>
      g.name.toLowerCase().includes(keyword.toLowerCase())
    );
  }, [data, keyword]);

  // ❌ APIコールなし（クライアント側ソート）
  const sortedGroups = useMemo(() => {
    return [...filteredGroups].sort((a, b) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      const comparison = aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      return order === 'asc' ? comparison : -comparison;
    });
  }, [filteredGroups, sortBy, order]);

  // ❌ APIコールなし（クライアント側ページング）
  const paginatedGroups = useMemo(() => {
    const start = (page - 1) * perPage;
    return sortedGroups.slice(start, start + perPage);
  }, [sortedGroups, page, perPage]);

  // ✅ 手動リフレッシュ時はAPIコール
  const handleRefresh = () => {
    refetch();
  };

  // ✅ グループ作成後はキャッシュ無効化→APIコール
  const queryClient = useQueryClient();
  const handleCreateGroup = async (newGroup: CreateGroupRequest) => {
    await createGroup(newGroup);
    queryClient.invalidateQueries(['groups']); // キャッシュ無効化
  };

  return (
    <div>
      <button onClick={handleRefresh}>更新</button>

      {/* 検索入力 */}
      <input
        value={keyword}
        onChange={(e) => {
          setKeyword(e.target.value);
          setPage(1); // 検索時は1ページ目に戻る
        }}
        placeholder="検索..."
      />

      {/* ソート選択 */}
      <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
        <option value="name">名前</option>
        <option value="createdAt">作成日時</option>
      </select>

      {/* ページサイズ選択 */}
      <select value={perPage} onChange={(e) => setPerPage(Number(e.target.value))}>
        <option value={10}>10件</option>
        <option value={25}>25件</option>
        <option value={50}>50件</option>
        <option value={100}>100件</option>
      </select>

      {/* データ表示 */}
      {isLoading ? (
        <Loader />
      ) : (
        <Table data={paginatedGroups} />
      )}

      {/* ページネーション */}
      <Pagination
        page={page}
        onChange={setPage}
        totalPages={Math.ceil(sortedGroups.length / perPage)}
      />
    </div>
  );
};
```

### 2.2 APIクライアント実装

```typescript
// api/groups.ts
export const fetchGroups = async (params: {
  per_page: number;
}): Promise<GroupListResponse> => {
  const response = await fetch(
    `${API_BASE_URL}/groups?per_page=${params.per_page}`,
    {
      headers: {
        'Authorization': `Bearer ${getAccessToken()}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch groups');
  }

  return response.json();
};
```

---

## 3. クライアント側ページネーション実装

### 3.1 基本的な実装方法

クライアント側でキャッシュされたデータに対して、`Array.slice()`を使用してページング処理を行います。

### 3.2 実装例（基本）

```typescript
// 1. 初回: 全件取得（per_page=1000で最大件数を指定）
const response = await fetch('/api/users?per_page=1000');
const allUsers = response.data.items; // キャッシュに保存

// 2. クライアント側でページング処理
const page = 1;           // 現在のページ番号
const perPage = 20;       // 1ページあたりの件数
const startIndex = (page - 1) * perPage;
const endIndex = startIndex + perPage;

// ページ分のデータを切り出し
const paginatedUsers = allUsers.slice(startIndex, endIndex);

// ページネーション情報を計算
const total = allUsers.length;
const totalPages = Math.ceil(total / perPage);

// UIに表示
const displayData = {
  items: paginatedUsers,
  page: page,
  perPage: perPage,
  total: total,
  totalPages: totalPages
};
```

### 3.3 React Query + TanStack Table での実装例

```typescript
import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

function UserList() {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);

  // 全件データをキャッシュ（5分間有効）
  const { data: allUsers } = useQuery({
    queryKey: ['users'],
    queryFn: () => fetch('/api/users?per_page=1000').then(r => r.json()),
    staleTime: 5 * 60 * 1000, // 5分
  });

  // クライアント側でページング
  const paginatedData = useMemo(() => {
    if (!allUsers) return { items: [], total: 0, totalPages: 0 };

    const startIndex = (page - 1) * perPage;
    const items = allUsers.slice(startIndex, startIndex + perPage);

    return {
      items,
      total: allUsers.length,
      totalPages: Math.ceil(allUsers.length / perPage),
    };
  }, [allUsers, page, perPage]);

  return (
    <div>
      {/* データ表示 */}
      {paginatedData.items.map(user => <div key={user.id}>{user.name}</div>)}

      {/* ページネーション */}
      <Pagination
        currentPage={page}
        totalPages={paginatedData.totalPages}
        onPageChange={setPage}
      />
    </div>
  );
}
```

### 3.4 利点

- ✅ ページ切り替え時にAPIコール不要（即座に表示）
- ✅ サーバー負荷の軽減
- ✅ ネットワーク遅延なし
- ✅ オフライン対応可能

### 3.5 注意事項

- 初回ロード時に全件取得するため、データ件数が多い場合は初回ロード時間が長くなる
- データ件数が1,000件を超える場合は、サーバーサイドページネーションへの移行を検討

---

## 4. クライアント側ソート実装

### 4.1 基本的な実装方法

クライアント側でキャッシュされたデータに対して、`Array.sort()`を使用してソート処理を行います。

### 4.2 実装例（基本）

```typescript
// 全件データをキャッシュから取得
const allUsers = [...cachedUsers]; // 元の配列を変更しないようコピー

// ソートフィールドとソート順
const sortField = 'name';
const sortOrder = 'asc'; // 'asc' または 'desc'

// ソート処理
const sortedUsers = allUsers.sort((a, b) => {
  const aValue = a[sortField];
  const bValue = b[sortField];

  if (sortOrder === 'asc') {
    return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
  } else {
    return aValue < bValue ? 1 : aValue > bValue ? -1 : 0;
  }
});
```

### 4.3 実装例（日本語対応）

```typescript
// 日本語の名前をソート（自然な順序）
const sortedUsers = allUsers.sort((a, b) => {
  return a.name.localeCompare(b.name, 'ja', { numeric: true });
});
```

### 4.4 実装例（日付ソート）

```typescript
// 作成日時の降順ソート（新しい順）
const sortedUsers = allUsers.sort((a, b) => {
  return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
});
```

### 4.5 React Query での実装例

```typescript
import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

type SortField = 'name' | 'email' | 'createdAt';
type SortOrder = 'asc' | 'desc';

function UserList() {
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  // 全件データをキャッシュ
  const { data: allUsers } = useQuery({
    queryKey: ['users'],
    queryFn: () => fetch('/api/users?per_page=1000').then(r => r.json()),
    staleTime: 5 * 60 * 1000,
  });

  // クライアント側でソート
  const sortedUsers = useMemo(() => {
    if (!allUsers) return [];

    const sorted = [...allUsers]; // 元の配列を変更しないようコピー

    return sorted.sort((a, b) => {
      let comparison = 0;

      // ソートフィールドによって処理を分岐
      if (sortField === 'name' || sortField === 'email') {
        // 文字列のソート（日本語対応）
        comparison = a[sortField].localeCompare(b[sortField], 'ja');
      } else if (sortField === 'createdAt') {
        // 日付のソート
        comparison = new Date(a[sortField]).getTime() - new Date(b[sortField]).getTime();
      }

      // ソート順を適用
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [allUsers, sortField, sortOrder]);

  return (
    <div>
      {/* ソート切り替えUI */}
      <select value={sortField} onChange={(e) => setSortField(e.target.value as SortField)}>
        <option value="name">名前</option>
        <option value="email">メールアドレス</option>
        <option value="createdAt">作成日時</option>
      </select>
      <button onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}>
        {sortOrder === 'asc' ? '昇順' : '降順'}
      </button>

      {/* データ表示 */}
      {sortedUsers.map(user => <div key={user.id}>{user.name}</div>)}
    </div>
  );
}
```

### 4.6 ソート可能なフィールド（例）

各APIエンドポイントでソート可能なフィールドは異なります。以下は一般的な例です：

| フィールド | 型 | 説明 | ソート方法 |
|-----------|-----|------|----------|
| name | string | 名前 | `localeCompare()` 使用 |
| email | string | メールアドレス | `localeCompare()` 使用 |
| createdAt | string | 作成日時 | `Date` オブジェクトで比較 |
| updatedAt | string | 更新日時 | `Date` オブジェクトで比較 |
| status | string | ステータス | 文字列比較 |

**注:** 各APIエンドポイントの詳細は、個別のAPI仕様書を参照してください。

### 4.7 利点

- ✅ ソート順変更時にAPIコール不要（即座に表示）
- ✅ サーバー負荷の軽減
- ✅ ネットワーク遅延なし
- ✅ 複数フィールドでの複合ソートも容易に実装可能

### 4.8 注意事項

- `Array.sort()` は元の配列を変更するため、必ずコピーしてからソート処理を行う
- 日本語のソートは `localeCompare('ja')` を使用することで自然な順序になる
- データ件数が1,000件を超える場合は、サーバーサイドソートへの移行を検討

---

## 5. サーバーサイドページネーション実装

### 5.1 大量データ（ドキュメント一覧など）の実装

```typescript
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';

const DocumentList = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [keywordInput, setKeywordInput] = useState('');
  const [sort, setSort] = useState('createdAt');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');

  // デバウンス処理（500ms待機）
  const debouncedKeyword = useDebouncedValue(keywordInput, 500);

  // ✅ パラメータが変わるたびにAPIコール
  const { data, isLoading } = useQuery({
    queryKey: ['documents', page, perPage, debouncedKeyword, sort, order],
    queryFn: () => fetchDocuments({
      page,
      per_page: perPage,
      keyword: debouncedKeyword,
      sort,
      order
    }),
    staleTime: 0, // キャッシュしない
    cacheTime: 0, // メモリに保持しない
    keepPreviousData: true, // ページ切り替え時に前のデータを表示
  });

  return (
    <div>
      {/* 検索入力（デバウンス） */}
      <input
        value={keywordInput}
        onChange={(e) => {
          setKeywordInput(e.target.value);
          setPage(1); // 検索時は1ページ目に戻る
        }}
        placeholder="検索..."
      />

      {/* ソート選択 */}
      <select value={sort} onChange={(e) => setSort(e.target.value)}>
        <option value="createdAt">作成日時</option>
        <option value="title">タイトル</option>
      </select>

      {/* ソート順選択 */}
      <select value={order} onChange={(e) => setOrder(e.target.value as 'asc' | 'desc')}>
        <option value="asc">昇順</option>
        <option value="desc">降順</option>
      </select>

      {/* ページサイズ選択 */}
      <select value={perPage} onChange={(e) => {
        setPerPage(Number(e.target.value));
        setPage(1); // ページサイズ変更時は1ページ目に戻る
      }}>
        <option value={10}>10件</option>
        <option value={25}>25件</option>
        <option value={50}>50件</option>
        <option value={100}>100件</option>
      </select>

      {/* データ表示 */}
      {isLoading ? (
        <SkeletonLoader />
      ) : (
        <DocumentTable data={data?.items} />
      )}

      {/* ページネーション */}
      <Pagination
        page={page}
        onChange={setPage}
        totalPages={data?.totalPages}
      />
    </div>
  );
};
```

### 5.2 デバウンスフック実装

```typescript
// hooks/useDebouncedValue.ts
import { useEffect, useState } from 'react';

export const useDebouncedValue = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};
```

---

## 6. 戦略切り替え可能な実装パターン

### 6.1 カスタムフック: useListData

クライアント側とサーバーサイドを簡単に切り替えられる実装パターン：

```typescript
// hooks/useListData.ts
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, useMemo } from 'react';

type PaginationStrategy = 'client' | 'server';

interface UseListDataOptions<T> {
  endpoint: string;
  strategy: PaginationStrategy;
  cacheTime?: number;
  fetchFn: (params: any) => Promise<{ items: T[]; total: number; page: number; per_page: number; totalPages: number }>;
}

export const useListData = <T,>(options: UseListDataOptions<T>) => {
  const { endpoint, strategy, cacheTime = 5 * 60 * 1000, fetchFn } = options;

  if (strategy === 'client') {
    return useClientSidePagination(endpoint, cacheTime, fetchFn);
  } else {
    return useServerSidePagination(endpoint, fetchFn);
  }
};

// クライアント側ページネーション
const useClientSidePagination = <T,>(
  endpoint: string,
  cacheTime: number,
  fetchFn: (params: any) => Promise<any>
) => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(10);
  const [keyword, setKeyword] = useState('');
  const [sort, setSort] = useState('');

  // 全件取得してキャッシュ
  const { data: allData, isLoading, refetch } = useQuery({
    queryKey: [endpoint],
    queryFn: () => fetchFn({ per_page: 1000 }),
    staleTime: cacheTime,
  });

  // クライアント側でフィルタリング・ソート・ページング
  const filteredData = useMemo(() => {
    if (!allData?.items) return [];
    let result = [...allData.items];

    // フィルタリング
    if (keyword) {
      result = result.filter((item: any) =>
        Object.values(item).some(val =>
          String(val).toLowerCase().includes(keyword.toLowerCase())
        )
      );
    }

    // ソート
    if (sort) {
      result.sort((a: any, b: any) => {
        const aVal = a[sort];
        const bVal = b[sort];
        return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      });
    }

    return result;
  }, [allData, keyword, sort]);

  const paginatedData = useMemo(() => {
    const start = (page - 1) * perPage;
    return filteredData.slice(start, start + perPage);
  }, [filteredData, page, perPage]);

  const queryClient = useQueryClient();
  const invalidateCache = () => {
    queryClient.invalidateQueries([endpoint]);
  };

  return {
    data: {
      items: paginatedData,
      total: filteredData.length,
      page,
      per_page: perPage,
      totalPages: Math.ceil(filteredData.length / perPage),
    },
    isLoading,
    page,
    setPage,
    perPage,
    setPerPage,
    keyword,
    setKeyword,
    sort,
    setSort,
    refetch,
    invalidateCache,
  };
};

// サーバーサイドページネーション
const useServerSidePagination = <T,>(
  endpoint: string,
  fetchFn: (params: any) => Promise<any>
) => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(10);
  const [keyword, setKeyword] = useState('');
  const [sort, setSort] = useState('');

  // パラメータ変更時に毎回APIコール
  const { data, isLoading, refetch } = useQuery({
    queryKey: [endpoint, page, perPage, keyword, sort],
    queryFn: () => fetchFn({ page, per_page: perPage, keyword, sort }),
    staleTime: 0,
    keepPreviousData: true,
  });

  const queryClient = useQueryClient();
  const invalidateCache = () => {
    queryClient.invalidateQueries([endpoint]);
  };

  return {
    data,
    isLoading,
    page,
    setPage,
    perPage,
    setPerPage,
    keyword,
    setKeyword,
    sort,
    setSort,
    refetch,
    invalidateCache,
  };
};
```

### 6.2 使用例

```typescript
// components/GroupList.tsx
const GroupList = () => {
  // ⭐ strategy を変更するだけで切り替え可能
  const {
    data,
    isLoading,
    page,
    setPage,
    perPage,
    setPerPage,
    keyword,
    setKeyword,
    invalidateCache,
  } = useListData({
    endpoint: '/groups',
    strategy: 'client', // ← 'client' or 'server' を切り替えるだけ
    fetchFn: fetchGroups,
  });

  const handleCreate = async (newGroup: CreateGroupRequest) => {
    await createGroup(newGroup);
    invalidateCache(); // キャッシュ無効化
  };

  return (
    <div>
      <input value={keyword} onChange={(e) => setKeyword(e.target.value)} />
      {/* ... */}
    </div>
  );
};
```

---

## 7. パフォーマンス最適化

### 7.1 デバウンス処理（検索入力時）

```typescript
import { useDebouncedValue } from '@/hooks/useDebouncedValue';

const [keywordInput, setKeywordInput] = useState('');
const debouncedKeyword = useDebouncedValue(keywordInput, 500); // 500ms待機

// debouncedKeywordをクエリに使用
const { data } = useQuery({
  queryKey: ['documents', debouncedKeyword],
  queryFn: () => fetchDocuments({ keyword: debouncedKeyword }),
});
```

### 7.2 ローディング状態の表示

```typescript
// スケルトンローダー
{isLoading ? (
  <SkeletonLoader rows={10} />
) : (
  <DataTable data={data?.items} />
)}

// スピナー
{isLoading && <Spinner />}
```

### 7.3 前のデータを保持（ページ切り替え時）

```typescript
const { data, isLoading } = useQuery({
  queryKey: ['documents', page],
  queryFn: () => fetchDocuments({ page }),
  keepPreviousData: true, // ページ切り替え時に前のデータを表示
});
```

### 7.4 短時間キャッシュ（サーバーサイドでも許容）

```typescript
// サーバーサイドでも、頻繁にページを行き来する場合は短時間キャッシュを許容
const { data } = useQuery({
  queryKey: ['documents', page],
  queryFn: () => fetchDocuments({ page }),
  staleTime: 30 * 1000, // 30秒間は再利用
  cacheTime: 5 * 60 * 1000, // 5分間メモリに保持
});
```

---

## 8. サーバーサイド実装

### 8.1 データベースインデックスの最適化

```sql
-- ドキュメント検索時のインデックス
CREATE INDEX idx_documents_title ON documents(title);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_documents_contract_id ON documents(contract_id);
CREATE INDEX idx_documents_status ON documents(status);

-- 全文検索インデックス（タイトル・内容の検索）
CREATE FULLTEXT INDEX idx_documents_fulltext ON documents(title, content);

-- 複合インデックス（よく一緒に使われる条件）
CREATE INDEX idx_documents_contract_status ON documents(contract_id, status);
CREATE INDEX idx_documents_contract_created ON documents(contract_id, created_at);
```

### 8.2 ページネーションクエリの実装（Node.js + Prisma）

```typescript
// api/documents.ts
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export const getDocuments = async (params: {
  contractId: string;
  page: number;
  per_page: number;
  keyword?: string;
  sort?: string;
  order?: 'asc' | 'desc';
}) => {
  const { contractId, page, per_page, keyword, sort = 'createdAt', order = 'desc' } = params;

  // WHERE条件の構築
  const where = {
    contractId,
    ...(keyword && {
      OR: [
        { title: { contains: keyword } },
        { content: { contains: keyword } },
      ],
    }),
  };

  // 総件数取得
  const total = await prisma.document.count({ where });

  // データ取得
  const items = await prisma.document.findMany({
    where,
    orderBy: { [sort]: order },
    skip: (page - 1) * per_page,
    take: per_page,
  });

  return {
    success: true,
    data: {
      total,
      page,
      per_page,
      totalPages: Math.ceil(total / per_page),
      items,
    },
    timestamp: new Date().toISOString(),
  };
};
```

### 8.3 ページネーションクエリの実装（SQL直接）

```typescript
// api/documents.ts
import { query } from '@/lib/db';

export const getDocuments = async (params: {
  contractId: string;
  page: number;
  per_page: number;
  keyword?: string;
  sort?: string;
  order?: 'asc' | 'desc';
}) => {
  const { contractId, page, per_page, keyword, sort = 'created_at', order = 'desc' } = params;

  const offset = (page - 1) * per_page;

  // WHERE条件の構築
  const whereConditions = ['contract_id = ?'];
  const params = [contractId];

  if (keyword) {
    whereConditions.push('(title LIKE ? OR content LIKE ?)');
    params.push(`%${keyword}%`, `%${keyword}%`);
  }

  const whereClause = whereConditions.join(' AND ');

  // 総件数取得
  const countResult = await query(
    `SELECT COUNT(*) as total FROM documents WHERE ${whereClause}`,
    params
  );
  const total = countResult[0].total;

  // データ取得
  const items = await query(
    `SELECT * FROM documents
     WHERE ${whereClause}
     ORDER BY ${sort} ${order}
     LIMIT ? OFFSET ?`,
    [...params, per_page, offset]
  );

  return {
    success: true,
    data: {
      total,
      page,
      per_page,
      totalPages: Math.ceil(total / per_page),
      items,
    },
    timestamp: new Date().toISOString(),
  };
};
```

### 8.4 レスポンス時間の最適化

```typescript
// キャッシュレイヤーの追加（Redis）
import { redis } from '@/lib/redis';

export const getDocuments = async (params: GetDocumentsParams) => {
  const cacheKey = `documents:${JSON.stringify(params)}`;

  // キャッシュチェック
  const cached = await redis.get(cacheKey);
  if (cached) {
    return JSON.parse(cached);
  }

  // DBクエリ実行
  const result = await fetchFromDatabase(params);

  // キャッシュ保存（30秒）
  await redis.setex(cacheKey, 30, JSON.stringify(result));

  return result;
};
```

---

## 9. 関連ドキュメント

- [API共通仕様書](./common-specification.md)
- [APIガイド](./api-guide.md)
- [データベース設計書](../01-architecture/database.md)
