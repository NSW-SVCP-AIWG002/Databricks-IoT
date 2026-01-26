---
description: Playwrightを使用したE2Eテストの運用ルール
globs:
  - e2e/**/*.ts
  - playwright.config.ts
alwaysApply: true
---

# Playwright E2Eテスト概要
- E2Eテストは`e2e/`ディレクトリに配置し、Playwright Testを用いて主要な顧客利用シナリオ（CUJ: Critical User Journeys）を検証します。
- `playwright.config.ts`でAPI (`http://localhost:3000`) とWeb (`http://localhost:3001`) の開発サーバーを自動起動し、テスト中は`baseURL`としてWebアプリを利用します。
- 共通で利用するテストユーザーは`demo@example.com / password123`です。環境変数`PLAYWRIGHT_API_BASE_URL`を設定するとAPIシード先を切り替えられます（未設定時は`http://localhost:3000`）。

## CUJに基づくテスト方針
- ログイン→タスク一覧表示→タスク操作（追加・削除・完了）の一連フローを通しで検証し、ユーザーが業務上必須の操作を完遂できることを担保します。
- 契約管理の検索・絞り込み・詳細参照・契約登録・一括操作といった管理者向けCUJを再現し、重要なマネジメント業務の成功パスを保証します。
- CUJの成否に関係しない細かなUI挙動（バリデーション詳細や境界値の検証など）はUnit/Integrationテストで担保し、E2Eは「重要な流れが完走できるか」に集中させます。
- 新たなE2Eを追加する場合は、追加シナリオが既存CUJと重複しないか、またCUJの本質的な価値（ユーザーが達成したい成果）を表しているかを確認してから実装します。

## テスト環境のセットアップ
- `e2e/global-setup.ts`
  - `app/task-api`でテスト用マイグレーション/シード (`AIOPS_ENV=test`) を実行し、E2Eに必要なデータベース状態を準備します。
- `e2e/global-teardown.ts`
  - テスト終了後に`taskdb_test`をドロップし、残存データをクリーンに保ちます（失敗時は警告のみ）。
- `playwright.config.ts`
  - `webServer`設定でAPI・Webの開発サーバーを起動し、CI環境では`workers: 1`・`retries: 2`など安定性を重視した設定に切り替わります。
  - `use.trace = 'on-first-retry'`により、失敗が再現された場合のみトレースを採取します。

## 実行方法
- 依存ツールの初期セットアップ: `bun run test:e2e:setup`
- ヘッドレス実行: `bun run test:e2e`
- UIデバッグ: `bun run test:e2e:ui`
- 実行前にPostgreSQLサーバーが起動し、`app/task-api`/`app/task-web`の依存がインストール済みであることを確認してください。

## E2Eテストのコード例

### フロントエンド（Playwright）のE2Eテスト例

**特徴**: 実際のブラウザで、ユーザーの操作フローを再現してテスト

```typescript
// e2e/users.spec.ts
import { test, expect } from '@playwright/test';

test.describe('ユーザー管理', () => {
  test('ユーザー登録フロー', async ({ page }) => {
    // Step 1: ユーザー一覧ページに移動
    await page.goto('/users');

    // Step 2: 新規登録ボタンをクリック
    await page.getByRole('button', { name: '新規登録' }).click();

    // Step 3: フォームに入力
    await page.getByLabel('メールアドレス').fill('newuser@example.com');
    await page.getByLabel('名前').fill('New User');
    await page.getByLabel('パスワード').fill('password123');

    // Step 4: 登録ボタンをクリック
    await page.getByRole('button', { name: '登録' }).click();

    // Step 5: 成功メッセージが表示される
    await expect(page.getByText('ユーザーを登録しました')).toBeVisible();

    // Step 6: 一覧ページに戻る
    await expect(page).toHaveURL('/users');
    await expect(page.getByText('New User')).toBeVisible();
  });
});
```

### バックエンド（REST Assured）のE2Eテスト例

**特徴**: ユーザー視点でのエンドツーエンドのフローを検証（API経由）

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class UserE2ETest {

    @LocalServerPort
    private int port;

    @Autowired
    private UserRepository userRepository;

    @BeforeEach
    void setUp() {
        RestAssured.port = port;
        RestAssured.basePath = "/api";
        userRepository.deleteAll();
    }

    @Test
    @DisplayName("ユーザー登録から取得までの一連のフロー")
    void testUserRegistrationFlow() {
        // Step 1: ユーザー作成
        UserCreateRequest createRequest = new UserCreateRequest(
            "test@example.com",
            "Test User"
        );

        ValidatableResponse createResponse = given()
            .contentType(ContentType.JSON)
            .body(createRequest)
        .when()
            .post("/users")
        .then()
            .statusCode(201)
            .body("email", equalTo("test@example.com"))
            .body("name", equalTo("Test User"));

        Long userId = createResponse.extract().path("id");

        // Step 2: 作成したユーザーを取得
        given()
        .when()
            .get("/users/" + userId)
        .then()
            .statusCode(200)
            .body("id", equalTo(userId.intValue()))
            .body("email", equalTo("test@example.com"))
            .body("name", equalTo("Test User"));
    }
}
```

**注**: 上記のバックエンドの例はAPIレベルのE2Eテストです。フロントエンドを含む完全なE2Eテストには、Playwrightを使用してブラウザ経由でテストすることを推奨します。

## Playwrightベストプラクティス
- アクセシビリティ対応セレクター: `getByRole` / `getByLabel` / `getByText`を優先し、UI変更に強いテストを心掛けます。
- 並列処理の競合防止: `Promise.all`でナビゲーションとクリックを同時に待機し、`waitForResponse`ヘルパーでAPI完了を監視します。
- 安定した同期: `waitForLoadState('networkidle')`や`waitForSelector`で描画完了を保証し、動的リストに対する操作前に必ず待機を挟みます。
- テストデータ管理: 固有値（`Date.now()`など）で重複を避け、API経由のフィクスチャ作成と`afterAll`でのクリーンアップを徹底します。
- シナリオの独立性: 共有状態がある場合のみ`mode: 'serial'`や`beforeEach`ログインを組み合わせ、できる限りテスト同士の副作用を排除します。
- 診断性の確保: 失敗時はPlaywrightレポート (`playwright-report/`) とトレースを確認し、必要に応じて`--debug`や`--headed`オプションで再実行します。
- 細かなコンポーネント挙動はUnitテスト・Integrationテストで担保し、E2Eでは顧客視点の完走性を重視します。

## E2Eテスト作成のチェックリスト

新しいE2Eテストを作成する際は、以下のチェックリストを確認してください。

### テストが含むべき項目

- [ ] クリティカルパスのテストがある
- [ ] ユーザーフローのテストがある
- [ ] ブラウザ互換性のテストがある（複数ブラウザ）
- [ ] レスポンシブデザインのテストがある（モバイル）
- [ ] 認証フローのテストがある
- [ ] エラーハンドリングのテストがある

### 実装時の確認事項

- [ ] 既存CUJがカバーする成果を確認し、重複を避けつつ不足しているユーザーフローを補う
- [ ] 認証・データ生成は既存のヘルパー関数やAPIフィクスチャを流用し、後処理でテストデータを確実に削除する
- [ ] 待機とアサーションは`getBy*`系セレクターと`expect`の組み合わせで記述し、タイムアウトを避けるための待機ロジックを明記する
- [ ] CI環境での安定実行を意識し、並列化による競合リスクがある場合は`test.describe.configure`やローカルフィクスチャで制御する
- [ ] 微細な挙動の検証はUnit/Integrationテストへ委ね、E2EではCUJの完走性と統合観点に集中する
- [ ] 新しいテストを追加した際は、このドキュメントと関連する開発ルールを必要に応じて更新する
