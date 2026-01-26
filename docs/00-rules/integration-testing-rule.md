---
description: 結合テスト（Integration Test）の実装ルール
globs:
  - tests/integration/**/*.py
alwaysApply: true
---

# 結合テスト（Integration Test）概要

結合テストは、複数のモジュールやレイヤーが連携して動作することを検証します。API結合テストでは、実際のHTTPリクエストを送信し、データベースを含む全レイヤーの動作を確認します。フロントエンドでは、APIをモック化してコンポーネントとAPIの連携を検証します。

## テスト方針

- **複数モジュールの連携**: 単体テストでは検証できない、モジュール間のインターフェースと連携を検証
- **実際のデータフロー**: データベースや実際のHTTPリクエストを使用し、本番に近い環境でテスト
- **エンドポイント網羅**: 全公開APIエンドポイントと主要な内部APIをカバー（目標: 90%以上）
- **認証・認可の検証**: セキュリティ要件が正しく実装されていることを確認
- **エラーハンドリング**: 異常系、境界値、タイムアウトなどの振る舞いを検証

## テスト対象

### バックエンドAPI結合テスト
- HTTPリクエスト/レスポンスの検証
- 認証・認可フロー
- データベースとの連携（CRUD操作）
- トランザクション処理
- エラーハンドリング
- ミドルウェアの動作

### フロントエンド結合テスト
- ページコンポーネントとAPIの連携
- フォーム送信からレスポンス表示まで
- データフェッチとローディング状態
- エラーハンドリングとリトライ
- APIモック（MSW）との統合

## ファイル配置ルール

結合テストは、Handlerやページコンポーネントと同じディレクトリまたは専用のtestsディレクトリに配置します。

```
app/task-api/src/handler/users/
├── get-users.ts
├── get-users.test.ts                # API結合テスト
├── create-user.ts
└── create-user.test.ts              # API結合テスト

app/task-web/src/app/users/
├── page.tsx
└── page.test.tsx                    # ページコンポーネントの結合テスト

app/task-web/src/components/
├── UserForm.tsx
└── UserForm.test.tsx                # フォームコンポーネントの結合テスト
```

**命名規則**: `<エンドポイント名>.test.ts` または `<実装ファイル名>.test.tsx`

## 実行方法

### バックエンド（Spring Boot）

```bash
# 結合テストのみ実行
./gradlew integrationTest

# 全てのテストを実行（単体テスト + 結合テスト）
./gradlew test

# カバレッジ付きで実行
./gradlew test jacocoTestReport
```

### フロントエンド（Next.js / Bun）

```bash
# 全てのテストを実行（単体テスト + 結合テスト）
bun test

# カバレッジ付きで実行
bun test --coverage

# 特定のテストファイルのみ実行
bun test page.test.tsx
```

## 結合テストのコード例

### バックエンド（Spring Boot）: API結合テスト

**特徴**: 実際のHTTPリクエストを送信し、データベースを含む全レイヤーの動作を検証

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@TestPropertySource(locations = "classpath:application-test.properties")
class UserApiIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private UserRepository userRepository;

    @BeforeEach
    void setUp() {
        userRepository.deleteAll();
    }

    @Test
    @DisplayName("ユーザー作成からデータベース保存までの一連の流れ")
    void testCreateUserEndToEnd() {
        // Arrange
        UserCreateRequest request = new UserCreateRequest("test@example.com", "Test User");

        // Act
        ResponseEntity<UserResponse> response = restTemplate.postForEntity(
            "/api/users",
            request,
            UserResponse.class
        );

        // Assert
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getEmail()).isEqualTo("test@example.com");

        // データベースに実際に保存されているか確認
        Optional<User> saved = userRepository.findByEmail("test@example.com");
        assertThat(saved).isPresent();
        assertThat(saved.get().getName()).isEqualTo("Test User");
    }
}
```

### フロントエンド（Next.js）: ページコンポーネントの結合テスト

**特徴**: MSWでAPIをモック化し、コンポーネントとAPIの連携を検証

```typescript
// app/users/page.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import UsersPage from './page';

// MSWサーバーのセットアップ
const server = setupServer(
  http.get('/api/users', () => {
    return HttpResponse.json({
      data: [
        { id: 1, email: 'user1@example.com', name: 'User 1' },
        { id: 2, email: 'user2@example.com', name: 'User 2' },
      ]
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('UsersPage', () => {
  test('ユーザー一覧が表示される', async () => {
    // Act
    render(<UsersPage />);

    // Assert - ローディング表示
    expect(screen.getByText('読み込み中...')).toBeInTheDocument();

    // Assert - データ取得後に表示
    await waitFor(() => {
      expect(screen.getByText('User 1')).toBeInTheDocument();
      expect(screen.getByText('User 2')).toBeInTheDocument();
    });
  });
});
```

## 結合テストのベストプラクティス

### 1. テスト環境の分離

- テスト専用のデータベースを使用する（例: `taskdb_test`）
- テスト用の設定ファイルを用意する（`application-test.properties`）
- 環境変数でテスト環境を識別する（`AIOPS_ENV=test`）

### 2. データのクリーンアップ

- `@BeforeEach`でテストデータを初期化する
- トランザクションを使用してロールバックする（`@Transactional`）
- テスト終了後にデータを削除する（`@AfterEach`）

### 3. MSWの適切な使用（フロントエンド）

- APIレスポンスをモック化し、外部依存を排除する
- `beforeAll`でサーバーを起動し、`afterAll`で停止する
- `afterEach`でハンドラーをリセットし、テスト間の独立性を保つ

### 4. 認証・認可のテスト

- 認証トークンの生成と検証をテストする
- 権限のないユーザーがアクセスできないことを確認する
- 認証失敗時のエラーハンドリングをテストする

### 5. エラーハンドリングのテスト

- HTTPステータスコード（400, 401, 403, 404, 500等）を検証する
- エラーメッセージの内容を確認する
- タイムアウトやネットワークエラーをシミュレートする

### 6. トランザクションのテスト

- データベースのトランザクション境界を確認する
- ロールバックが正しく動作することを検証する
- 並行アクセス時の動作をテストする

### 7. パフォーマンスの考慮

- 結合テストは単体テストより実行時間が長いため、効率的に設計する
- 不要なデータセットアップを避ける
- 並列実行可能な場合は並列化を検討する

### 8. カバレッジ目標

- **統合ポイントカバレッジ**: 最低90%、推奨95%
- 全公開APIエンドポイント100%、主要な内部APIをカバー
- 認証・認可フローは100%カバー

## 結合テスト作成のチェックリスト

新しい結合テストを作成する際は、以下のチェックリストを確認してください。

- [ ] APIエンドポイントのテストがある
- [ ] 認証・認可のテストがある
- [ ] データフローのテストがある（リクエスト→処理→レスポンス→DB保存）
- [ ] エラーハンドリングのテストがある
- [ ] トランザクションのテストがある（該当する場合）
- [ ] データベースとの連携が正しく動作する
- [ ] テスト環境が適切に設定されている
- [ ] データのクリーンアップが実装されている
- [ ] HTTPステータスコードが正しく返される
- [ ] レスポンスボディの内容が期待通りである
- [ ] テストが独立している（他のテストに依存しない）
- [ ] MSW（フロントエンド）が適切に設定されている

## 新しい結合テストを追加する際の注意点

- 結合テストは、単体テストでカバーできない「連携」と「統合」に焦点を当てる
- 全ての詳細なロジックは単体テストでカバーし、結合テストはデータフローの確認に留める
- テスト専用のデータベースを使用し、本番データに影響を与えないようにする
- テスト実行後は必ずデータをクリーンアップする
- CI/CD パイプラインで自動実行されることを意識し、環境依存の処理は避ける
- 新しいテストを追加した際は、このドキュメントと関連する開発ルールを必要に応じて更新してください

## API結合テストの重要ポイント

### 1. 全レイヤーの統合

結合テストでは、Handler → UseCase → Repository → Database の全レイヤーが実際に連携して動作することを確認します。

### 2. 実際のHTTPリクエスト

`TestRestTemplate`や`WebTestClient`を使用して、実際のHTTPリクエストを送信し、本番環境に近い状態でテストします。

### 3. データベースの状態確認

APIのレスポンスだけでなく、データベースに実際にデータが保存されているかを確認することで、データフローの整合性を保証します。

---

**結合テストは、モジュール間の連携を保証する重要なテストです。適切なテストを実装し、システム全体の品質を維持してください。**
