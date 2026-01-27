# 共通仕様

## 📑 目次

1. [概要](#概要)
2. [HTTPステータスコード](#httpステータスコード)
3. [エラーコード](#エラーコード)
4. [エラーハンドリング方針](#エラーハンドリング方針)
   - 4.1 [エラー分類とHTTPステータス](#エラー分類とhttpステータス)
   - 4.2 [エラーログ出力](#エラーログ出力)
5. [認証・認可](#認証認可)
   - 5.1 [認証方式](#認証方式)
   - 5.2 [認証フロー](#認証フロー)
   - 5.3 [ユーザー情報取得](#ユーザー情報取得)
   - 5.4 [ロール定義](#ロール定義)
   - 5.5 [ロールチェック](#ロールチェック)
   - 5.6 [組織種別定義](#組織種別定義)
6. [一覧ソート](#一覧ソート)
   - 6.1 [一覧ソートの種類](#一覧ソートの種類)
7. [日時フォーマット](#日時フォーマット)
   - 7.1 [形式](#形式)
   - 7.2 [タイムゾーン](#タイムゾーン)
8. [セキュリティ](#セキュリティ)
   - 8.1 [通信セキュリティ](#通信セキュリティ)
   - 8.2 [リクエストサイズ制限](#リクエストサイズ制限)
   - 8.3 [入力値検証](#入力値検証)
   - 8.4 [CSRF対策](#csrf対策)
9.  [トランザクション管理](#トランザクション管理)
   - 9.1 [デフォルト設定](#デフォルト設定)
   - 9.2 [トランザクション分離レベル](#トランザクション分離レベル)
   - 9.3 [トランザクション開始・終了タイミング](#トランザクション開始終了タイミング)
   - 9.4 [ロック戦略](#ロック戦略)
   - 9.5 [デッドロック対策](#デッドロック対策)
   - 9.6 [トランザクション管理のベストプラクティス](#トランザクション管理のベストプラクティス)
10. [ログ出力ポリシー](#ログ出力ポリシー)
   - 10.1 [ログレベル定義](#ログレベル定義)
   - 10.2 [必須ログ出力項目](#必須ログ出力項目)
   - 10.3 [出力禁止項目（機密情報）](#出力禁止項目機密情報)
   - 10.4 [マスキング方針](#マスキング方針)
   - 10.5 [ログローテーション](#ログローテーション)
   - 10.6 [ログ保存先](#ログ保存先)
11. [関連ドキュメント](#関連ドキュメント)

---

## 概要

このドキュメントは、Databricks IoTシステムにおけるFlask Webアプリケーションの全機能に共通する仕様を定義します。

**対象:**
- Flask SSRルート（サーバーサイドレンダリング）
- HTMLレスポンスまたはリダイレクト

**アーキテクチャ:**
- **Webフレームワーク**: Flask + Jinja2
- **認証基盤**: Databricks認証（Entra ID統合）
- **データベース**: MySQL互換DB（OLTP）、Unity Catalog（分析）
- **デプロイ環境**: Azure App Service

---

## HTTPステータスコード

すべてのFlaskルートで使用する共通HTTPステータスコードを定義します。

| コード | 説明                  | 使用場面                           | Flask実装                            |
| ------ | --------------------- | ---------------------------------- | ------------------------------------ |
| 200    | OK                    | 正常処理（画面表示成功）           | `render_template()`                  |
| 302    | Found                 | リダイレクト（処理成功後）         | `redirect()`                         |
| 400    | Bad Request           | リクエスト不正（パラメータエラー） | `render_template()` with error       |
| 401    | Unauthorized          | 認証エラー                         | Databricksが自動処理                 |
| 403    | Forbidden             | 権限不足                           | `render_template('errors/403.html')` |
| 404    | Not Found             | リソース未検出                     | `render_template('errors/404.html')` |
| 409    | Conflict              | 競合エラー（重複登録など）         | `render_template()` with error       |
| 422    | Unprocessable Entity  | バリデーションエラー               | `render_template()` with form errors |
| 500    | Internal Server Error | サーバーエラー                     | `render_template('errors/500.html')` |
| 502    | Bad Gateway           | 外部API連携エラー                  | `render_template('errors/502.html')` |
| 503    | Service Unavailable   | メンテナンス中                     | `render_template('errors/503.html')` |

**注:** Flask SSRでは、エラー時もHTMLページを返却します（JSONレスポンスは使用しません）。

---

## エラーコード

アプリケーション内部で使用するエラーコードを定義します。

| コード             | 説明                 | HTTPステータス | 表示方法                             |
| ------------------ | -------------------- | -------------- | ------------------------------------ |
| AUTH_FAILED        | 認証失敗             | 401            | Databricksログイン画面へリダイレクト |
| PERMISSION_DENIED  | 権限不足             | 403            | エラーページまたはFlashメッセージ    |
| RESOURCE_NOT_FOUND | リソース不在         | 404            | エラーページ                         |
| DUPLICATE_ENTRY    | 重複エラー           | 409            | フォームエラーメッセージ             |
| INVALID_PARAMETER  | パラメータ不正       | 400            | フォームエラーメッセージ             |
| VALIDATION_ERROR   | バリデーションエラー | 422            | フォームエラーメッセージ             |
| INTERNAL_ERROR     | サーバーエラー       | 500            | エラーページ                         |
| EXTERNAL_API_ERROR | 外部API連携エラー    | 502            | エラーページ                         |
| DATABASE_ERROR     | データベースエラー   | 500            | エラーページ                         |

**Flask実装例:**

```python
# フォームバリデーションエラー
if not form.validate_on_submit():
    # エラーメッセージはフォームフィールドに表示
    return render_template('users/form.html', form=form), 422

# リソース不在エラー
user = User.query.get(user_id)
if not user:
    flash('指定されたユーザーが見つかりません', 'error')
    return render_template('errors/404.html'), 404

# 権限エラー
if not current_user.has_permission('user:delete'):
    flash('この操作を実行する権限がありません', 'error')
    return render_template('errors/403.html'), 403

# データベースエラー（例外ハンドラで処理）
try:
    db.session.commit()
except Exception as e:
    db.session.rollback()
    logger.error(f"Database error: {e}")
    flash('データベースエラーが発生しました', 'error')
    return render_template('errors/500.html'), 500
```

---

## エラーハンドリング方針

すべてのFlaskルートで共通するエラーハンドリングの方針を定義します。

### エラー分類とHTTPステータス

| エラー分類           | 説明                           | 対応方針                   | HTTPステータス | トランザクション       |
| -------------------- | ------------------------------ | -------------------------- | -------------- | ---------------------- |
| バリデーションエラー | 入力パラメータの形式・値が不正 | フォームにエラー表示       | 400, 422       | 開始前                 |
| 認証エラー           | 認証失敗                       | Databricksログイン画面へ   | 401            | 開始前                 |
| 認可エラー           | 権限不足                       | エラーページまたはFlash    | 403            | 開始前                 |
| リソース不在エラー   | 対象データが存在しない         | エラーページまたはFlash    | 404            | 読み取りのみ           |
| 競合エラー           | データの重複・競合             | フォームにエラー表示       | 409            | 開始後（ロールバック） |
| データベースエラー   | DB接続失敗、SQL実行失敗        | ロールバック後エラーページ | 500            | 開始後（ロールバック） |
| 外部API連携エラー    | 外部サービスとの連携失敗       | ロールバック後エラーページ | 502            | 開始後（ロールバック） |
| タイムアウト         | 処理時間超過                   | ロールバック後エラーページ | 504            | 開始後（ロールバック） |

**注:** トランザクション管理の詳細は[トランザクション管理](#トランザクション管理)セクションを参照してください。

### エラーログ出力

エラー発生時は、以下の情報をログに出力します。

**必須項目:**
- リクエストID（トレーシング用）
- タイムスタンプ
- エラーコード
- HTTPステータス
- エンドポイント（Flaskルート）
- HTTPメソッド
- ユーザーID（認証済みの場合）
- 組織ID（認証済みの場合）

**任意項目:**
- エラーメッセージ
- スタックトレース（500エラーのみ）
- クエリパラメータ
- フォームデータ（機密情報を除く）

**注:** ログ出力の詳細は[ログ出力ポリシー](#ログ出力ポリシー)セクションを参照してください。

---

## 認証・認可

### 認証方式

| 項目           | 内容                                                          |
| -------------- | ------------------------------------------------------------- |
| 認証基盤       | Databricks認証（Entra ID統合）                                |
| 認証方式       | Databricksワークスペース認証（Databricks標準機能）            |
| セッション管理 | Databricksが自動管理                                          |
| アクセス制限   | アクセス元IP制限（Databricksワークスペース、Databricks Apps） |

**重要:** Flaskアプリケーション内で認証処理は実装しません。Databricks Appsのリバースプロキシが認証を処理します。

### 認証フロー

1. ユーザーがDatabricks Appsにアクセス
2. Databricksが自動的にEntra ID認証を要求
3. 認証成功後、リバースプロキシがリクエストヘッダーにユーザー情報を付与
4. Flaskアプリケーションはヘッダーからユーザー情報を取得
5. 組織IDでデータスコープを制限

### ユーザー情報取得

Flaskアプリケーションは、リバースプロキシから以下のヘッダーでユーザー情報を取得します：

```python
from flask import request

def get_current_user():
    """リバースプロキシヘッダーからユーザー情報を取得"""
    user_id = request.headers.get('X-Forwarded-User')
    email = request.headers.get('X-Forwarded-Email')

    if not user_id or not email:
        # 認証エラー（通常は発生しない）
        abort(401)

    # データベースからユーザー情報を取得
    user = User.query.filter_by(email=email).first()
    if not user:
        # ユーザーが未登録の場合の処理
        abort(403)

    return user
```

**注:** ヘッダー名（`X-Forwarded-User`、`X-Forwarded-Email`）は、Databricks Appsの実際の仕様に合わせて調整してください。

### ロール定義

システムには以下のロールが定義されています。：

| ロール                 | 説明           |
| ---------------------- | -------------- |
| `system_admin`         | システム保守者 |
| `management_admin`     | 管理者         |
| `sales_company_user`   | 販社ユーザー   |
| `service_company_user` | サービス利用者 |


**注:** ロールはユーザー種別マスタ内で管理され、UI機能の表示/非表示等の各機能の利用可/不可に関する権限制御に使用されます。
ロール定義の詳細は要件定義書を参照してください。

### ロールチェック

すべてのFlaskルートで、必要に応じて権限チェックを実施します：

```python
from functools import wraps
from flask import abort, flash, redirect, url_for

def require_role(*roles):
    """ロールチェックデコレータ"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()
            if current_user.role not in roles:
                flash('この操作を実行する権限がありません', 'error')
                return render_template('errors/403.html'), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# 使用例
@bp.route('/users/create', methods=['POST'])
@require_role('system_admin', 'organization_admin')
def create_user():
    # ユーザー登録処理
    pass
```

### 組織種別定義

システムには以下の組織が定義されています：

| 組織種別             | 説明             | 対応するロール |
| -------------------- | ---------------- | -------------- |
| `system_company`     | システム保守会社 | システム保守者 |
| `management_company` | 管理会社         | 管理者         |
| `sales_company`      | 販売会社         | 販社ユーザー   |
| `service_company`    | サービス利用会社 | サービス利用者 |

---

## 一覧ソート

一覧のソート方法について定義します。

### 一覧ソートの種類

1. 全体ソート
2. ページ内ソート

#### 全体ソート

検索結果として表示される一覧の表示内容に対して、ページをまたいでソートを行います。
ソートに使用する項目は、各画面の検索条件欄にあるソート項目ドロップダウンから選択することができます。
ソート順序は、各画面の検索条件欄にあるソート順ドロップダウンから選択することができます。
各一覧画面で表示されるソート項目ドロップダウンの表示内容は各機能のUI仕様書を参照してください。
各一覧画面で表示されるソート順ドロップダウンの表示内容は以下の通りとします。
- 空白
- 昇順
- 降順

各画面でソート項目ドロップダウン、ソート順序ドロップダウンの内容としてDBからsort_item_masterの内容を取得するとき、画面に渡す際の形式は以下の通りとします。
```Python
SORT_ORDER = [{sort_order_id: -1, sort_order_name:""}, 
              {sort_order_id: 1, sort_order_name: "昇順"},
              {sort_order_id: 2, sort_order_name: "降順"}
            ]
sort_item = [{sort_item_id: NNN, sort_item_name: SSS }, ...] # sort_item_masterを検索した結果を格納した辞書配列
```
検索実行時、画面から受け取ったsort_item_idは検索クエリのパラメータとして、sort_order_idは検索関数内でASCまたはDESCに置換して検索クエリに渡されます。

**sort_order_idを置換する過程の実装例**
```Python
if sort_order_id == 1:
    sort_order = 'ASC'
elif sort_order_id == 2:
    sort_order = 'DESC'
else:
    sort_order = None
```


#### ページ内ソート

検索結果として表示される一覧の表示内容に対して、選択中のページ内に表示された内容のみに対してフロントエンド側の処理を用いてソートを行います。
一覧のヘッダの項目を選択することで、選択したヘッダの項目に対してソートを行い、ソート順序については以下の通りとします。

- 初回のヘッダクリック：昇順
- 2回目のヘッダクリック：降順
- 3回目のヘッダクリック：デフォルトの表示順
- 4回目のクリック：昇順
以降、繰り返し

---

## 日時フォーマット

すべての日時はISO 8601形式（JST）で表現します。

### 形式

```
YYYY-MM-DDTHH:mm:ss+09:00
```

### 例

```
2025-11-01T00:00:00+09:00
2025-12-09T15:30:45+09:00
```

### タイムゾーン

- すべての日時はJST（日本標準時、UTC+9）で処理されます
- データベース（MySQL互換DB、Unity Catalog）はJSTで設定されています
- Jinja2テンプレートでの日時表示もJSTで行います
- ユーザー側でのタイムゾーン変換は不要です

**Jinja2テンプレート例:**

```jinja2
{# 日時フォーマット表示 #}
{{ user.created_at.strftime('%Y年%m月%d日 %H:%M') }}

{# ISO 8601形式 #}
{{ user.created_at.isoformat() }}
```

---

## セキュリティ

### 通信セキュリティ

- **HTTPS必須**: すべての通信はHTTPS経由で行われます（Databricks Appsが自動対応）
- **TLS 1.2以上**: TLS 1.2以上のプロトコルを使用
- **Private Link**: Event Hubs、ADLS、MySQL、Databricks UI/APIへのPrivate Link接続

### リクエストサイズ制限

| 項目                 | 制限値                |
| -------------------- | --------------------- |
| フォーム送信サイズ   | 10MB                  |
| ファイルアップロード | 10MB（CSVインポート） |
| URLの長さ            | 2,048文字             |

**Flask設定例:**

```python
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
```

### 入力値検証

すべての入力値はサーバー側（Flask）でバリデーションを実施します：

- **SQLインジェクション対策**: SQLAlchemyのプリペアドステートメント使用
- **XSS対策**: Jinja2の自動エスケープ機能を有効化
- **パスワード管理**: bcryptによるハッシュ化（該当する場合）
- **入力値検証**: Flask-WTFによるフォームバリデーション

**Flask-WTF バリデーション例:**

```python
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField
from wtforms.validators import DataRequired, Email, Length

class UserCreateForm(FlaskForm):
    name = StringField('名前', validators=[
        DataRequired(message='名前は必須です'),
        Length(min=1, max=100, message='名前は1〜100文字で入力してください')
    ])
    email = EmailField('メールアドレス', validators=[
        DataRequired(message='メールアドレスは必須です'),
        Email(message='有効なメールアドレスを入力してください')
    ])
```

### CSRF対策

Flask-WTFによるCSRF保護を全フォームで実施します：

```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
```

**Jinja2テンプレート:**

```jinja2
<form method="post">
  {{ form.csrf_token }}
  {# フォームフィールド #}
</form>
```

---

## トランザクション管理

すべてのFlaskルートで共通するデータベーストランザクション管理の方針を定義します。

### デフォルト設定

| 項目             | 設定値         | 理由                                                                             |
| ---------------- | -------------- | -------------------------------------------------------------------------------- |
| **分離レベル**   | READ COMMITTED | デフォルト設定。ダーティリードを防ぎつつ、パフォーマンスと整合性のバランスを確保 |
| **ロック戦略**   | 行レベルロック | 同時実行性を最大化。テーブルロックは使用しない                                   |
| **タイムアウト** | 30秒           | デッドロック防止。長時間ロックを防ぐ                                             |
| **自動コミット** | 無効           | 明示的なトランザクション制御を行う（SQLAlchemyデフォルト）                       |

### トランザクション分離レベル

| 分離レベル          | 使用場面                            | 特徴                                         |
| ------------------- | ----------------------------------- | -------------------------------------------- |
| **READ COMMITTED**  | ほとんどのFlaskルート（デフォルト） | ダーティリード防止、ファントムリード許容     |
| **REPEATABLE READ** | 一貫性が重要な処理                  | 同一トランザクション内で同じデータを読む場合 |
| **SERIALIZABLE**    | 厳密な整合性が必要な処理            | パフォーマンス低下のため慎重に使用           |

**注:** デフォルト以外の分離レベルを使用する場合は、個別のworkflow-specification.mdで明記してください。

### トランザクション開始・終了タイミング

#### トランザクション開始

以下の条件を**すべて満たす**場合にトランザクションを開始します：

1. データベースへの書き込み操作（INSERT/UPDATE/DELETE）がある
2. フォームバリデーションが完了している
3. 認証・認可チェックが完了している

**トランザクションを開始しない場合:**
- 読み取り専用（SELECT）のみのルート（一覧表示、詳細表示）
- フォームバリデーションエラーの可能性がある処理の前
- 認証・認可チェックの前

**理由:** バリデーションエラーや認証エラーでトランザクションを開始すると、無駄なリソース消費とロールバック処理が発生するため。

**Flask実装例:**

```python
@bp.route('/users/create', methods=['POST'])
@require_role('system_admin', 'organization_admin')
def create_user():
    form = UserCreateForm()

    # バリデーション（トランザクション開始前）
    if not form.validate_on_submit():
        return render_template('users/form.html', form=form), 422

    # トランザクション開始（SQLAlchemyは暗黙的に開始）
    try:
        user = User(
            email=form.email.data,
            name=form.name.data,
            organization_id=current_user.organization_id
        )
        db.session.add(user)
        db.session.commit()  # コミット

        flash('ユーザーを登録しました', 'success')
        return redirect(url_for('users.list_users'))

    except IntegrityError as e:
        db.session.rollback()  # ロールバック
        if 'email' in str(e):
            form.email.errors.append('このメールアドレスは既に使用されています')
        return render_template('users/form.html', form=form), 409

    except Exception as e:
        db.session.rollback()  # ロールバック
        logger.error(f"Database error: {e}")
        flash('データベースエラーが発生しました', 'error')
        return render_template('errors/500.html'), 500
```

#### トランザクション終了（コミット）

以下の条件を**すべて満たす**場合にコミットします：

- すべてのデータベース操作が正常に完了
- 外部API連携がある場合は、そのレスポンスも正常
- ビジネスロジックエラーが発生していない
- タイムアウトが発生していない

#### トランザクション終了（ロールバック）

以下のいずれかのエラーが発生した場合、トランザクションをロールバックします：

| エラー種別                 | 発生タイミング                          | ロールバック実施 | 理由                   |
| -------------------------- | --------------------------------------- | ---------------- | ---------------------- |
| バリデーションエラー       | トランザクション開始前                  | ❌ 不要           | トランザクション未開始 |
| 認証・認可エラー           | トランザクション開始前                  | ❌ 不要           | トランザクション未開始 |
| リソース不在エラー         | 読み取り処理中                          | ❌ 不要           | データ変更なし         |
| **競合エラー**             | 更新処理中                              | ✅ **実施**       | データ整合性保持       |
| **データベースエラー**     | SQL実行時                               | ✅ **実施**       | データ整合性保持       |
| **外部API連携エラー**      | API呼び出し時（トランザクション開始後） | ✅ **実施**       | データ整合性保持       |
| **ビジネスロジックエラー** | ビジネスルール違反検出時                | ✅ **実施**       | データ整合性保持       |
| **タイムアウト**           | 処理時間超過                            | ✅ **実施**       | 不完全なデータ登録防止 |

**注:** エラー分類の詳細は[エラーハンドリング方針](#エラーハンドリング方針)セクションを参照してください。

#### ロールバック失敗時の対応

ロールバック処理自体が失敗した場合（稀なケース）：

1. **エラーログに詳細を記録**
   - リクエストID
   - トランザクションID
   - 失敗理由
   - 実行されたSQL履歴
   - データベース接続状態

2. **システム管理者へアラート通知**
   - 即座に通知（メール・Slack等）
   - 緊急度: Critical

3. **HTTPステータス 500 でエラーページ返却**
   - ユーザーには「サーバーエラー」として表示
   - リクエストIDを含める（手動調査用）

4. **手動確認の準備**
   - トランザクションIDをログに記録
   - データベースの状態を確認できるよう、関連テーブルのスナップショットを保存（可能な場合）

### ロック戦略

#### 基本方針

- **行レベルロック**: 標準使用
- **テーブルロック**: 原則使用禁止（メンテナンス時のみ）
- **楽観的ロック**: バージョン管理カラム（version）を使用する場合
- **悲観的ロック**: SELECT ... FOR UPDATE を使用する場合

#### 楽観的ロック vs 悲観的ロック

| 項目               | 楽観的ロック                   | 悲観的ロック                   |
| ------------------ | ------------------------------ | ------------------------------ |
| **使用場面**       | 競合が少ない処理               | 競合が多い処理、在庫管理など   |
| **実装方法**       | versionカラムで更新時チェック  | SELECT ... FOR UPDATE          |
| **競合時**         | 更新失敗、リトライまたはエラー | ロック待ち（タイムアウトあり） |
| **パフォーマンス** | 高い                           | 低い（ロック待ち発生）         |

**実装例（楽観的ロック）:**
```python
# SQLAlchemy ORM with version column
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    version = db.Column(db.Integer, default=1)

# 更新処理
user = User.query.get(user_id)
current_version = user.version

user.name = new_name
user.version = current_version + 1

result = db.session.execute(
    update(User)
    .where(User.id == user_id)
    .where(User.version == current_version)
    .values(name=new_name, version=current_version + 1)
)

if result.rowcount == 0:
    # 競合エラー
    db.session.rollback()
    flash('他のユーザーによって更新されています。再度お試しください', 'error')
    return redirect(url_for('users.edit_user', user_id=user_id))
```

**実装例（悲観的ロック）:**
```python
# ロック取得
user = db.session.query(User).filter_by(id=user_id).with_for_update().first()

# 更新処理
user.name = new_name
db.session.commit()
```

### デッドロック対策

**デッドロック防止策:**

1. **ロック順序の統一**: 複数テーブルをロックする場合、常に同じ順序でアクセス
2. **ロック時間の最小化**: トランザクション内の処理を最小限にする
3. **タイムアウト設定**: 30秒でタイムアウト
4. **インデックス利用**: WHERE句で使用するカラムにインデックスを設定し、ロック範囲を最小化

**デッドロック発生時の対応:**

1. エラーログに記録（関連するSQL、テーブル、トランザクションID）
2. トランザクションをロールバック
3. HTTPステータス 500 でエラーページ返却
4. リトライは行わない（ユーザーが再度操作）

### トランザクション管理のベストプラクティス

1. ✅ **トランザクションは短く保つ**: 不要な処理はトランザクション外で実施
2. ✅ **外部API呼び出しはトランザクション外**: ネットワーク遅延でロック時間が延びる
3. ✅ **ファイルI/Oはトランザクション外**: I/O待ちでロック時間が延びる
4. ✅ **バリデーションはトランザクション前**: 入力チェックでトランザクション時間を無駄にしない
5. ❌ **トランザクション内でのループ処理は避ける**: バッチ処理を検討

---

## ログ出力ポリシー

すべてのFlaskルートで共通するログ出力の方針を定義します。

### ログレベル定義

| ログレベル | 使用場面       | 出力内容                                                     |
| ---------- | -------------- | ------------------------------------------------------------ |
| **ERROR**  | エラー発生時   | HTTPステータス 500系、データベースエラー、外部API連携エラー  |
| **WARN**   | 警告事象発生時 | HTTPステータス 400系、バリデーションエラー、認証・認可エラー |
| **INFO**   | 通常処理       | ルート呼び出し開始・終了、主要な処理ステップ                 |
| **DEBUG**  | 開発・調査用   | 詳細な処理内容、変数値（本番環境では無効化）                 |

### 必須ログ出力項目

すべてのFlaskルートで以下の項目をログ出力します：

#### リクエスト開始時（INFO）

```json
{
  "level": "INFO",
  "timestamp": "2025-11-01T10:00:00.123+09:00",
  "requestId": "req_abc123",
  "method": "POST",
  "endpoint": "/users/create",
  "userId": "usr_001",
  "organizationId": "org_001",
  "ipAddress": "192.168.1.100",
  "userAgent": "Mozilla/5.0..."
}
```

#### レスポンス返却時（INFO）

```json
{
  "level": "INFO",
  "timestamp": "2025-11-01T10:00:00.456+09:00",
  "requestId": "req_abc123",
  "method": "POST",
  "endpoint": "/users/create",
  "httpStatus": 302,
  "processingTime": 123,
  "userId": "usr_001",
  "organizationId": "org_001"
}
```

**注:** `processingTime` はミリ秒単位

#### エラー発生時（ERROR/WARN）

```json
{
  "level": "ERROR",
  "timestamp": "2025-11-01T10:00:00.789+09:00",
  "requestId": "req_abc123",
  "method": "POST",
  "endpoint": "/users/create",
  "httpStatus": 500,
  "errorCode": "DATABASE_ERROR",
  "errorMessage": "データベース接続に失敗しました",
  "userId": "usr_001",
  "organizationId": "org_001",
  "stackTrace": "..."
}
```

### 出力禁止項目（機密情報）

以下の情報は**絶対にログ出力してはいけません**：

#### 認証情報
- ❌ パスワード（平文・ハッシュ化後問わず）
- ❌ 認証トークン（Databricksトークン、アクセストークン）
- ❌ セッションID（トレーシング以外の目的）
- ❌ CSRFトークン

#### 個人情報
- ❌ クレジットカード番号
- ❌ マイナンバー
- ❌ 生年月日（フルフォーマット）
- ❌ メールアドレス（一部マスキングなしの場合）
- ❌ 電話番号（一部マスキングなしの場合）
- ❌ 住所（詳細）

#### その他機密情報
- ❌ 暗号化キー
- ❌ Salt値
- ❌ データベース接続文字列（パスワード部分）

### マスキング方針

個人情報を出力する必要がある場合は、以下のルールでマスキングします：

| 項目           | マスキング方法           | 例                   |
| -------------- | ------------------------ | -------------------- |
| メールアドレス | ローカル部の一部をマスク | `ya****@example.com` |
| 電話番号       | 中間4桁をマスク          | `090-****-5678`      |
| ユーザー名     | 姓のみ表示               | `山田****`           |

### ログローテーション

| 項目               | 設定値                                |
| ------------------ | ------------------------------------- |
| ローテーション周期 | 日次（毎日0時）                       |
| 保存期間           | 90日間                                |
| 圧縮               | あり（gzip）                          |
| ファイルサイズ上限 | 100MB（超過時は即座にローテーション） |

### ログ保存先

| 環境     | 保存先                                        | 備考                               |
| -------- | --------------------------------------------- | ---------------------------------- |
| 開発環境 | Databricks Apps標準ログ                       | Databricks Apps環境                |
| 本番環境 | Databricks Apps標準ログ + Azure Log Analytics | クエリ・分析可能、アラート設定済み |

**注:** Databricks Appsの標準ログ出力先は、Databricksの仕様に従ってください。

---

## 関連ドキュメント

### 機能設計・仕様

- [機能別実装ガイド作成ルール](../feature-guide.md) - 実装ガイドの作成方法
- [UI仕様書テンプレート](../templates/ui-specification-template.md) - ui-specification.md のテンプレート
- [ワークフロー仕様書テンプレート](../templates/workflow-specification-template.md) - workflow-specification.md のテンプレート
- [機能要件定義書](../../02-requirements/functional-requirements.md) - 全機能の要件定義
- [技術要件定義書](../../02-requirements/technical-requirements.md) - 技術仕様・セキュリティ要件
- [非機能要件定義書](../../02-requirements/non-functional-requirements.md) - パフォーマンス・可用性要件

### アーキテクチャ設計

- [アーキテクチャ概要](../../01-architecture/overview.md)
- [バックエンド設計](../../01-architecture/backend.md) - Flask/LDP設計
- [フロントエンド設計](../../01-architecture/frontend.md) - Flask + Jinja2設計
- [インフラストラクチャ設計](../../01-architecture/infrastructure.md)

### データベース

- [データベース設計書](../../01-architecture/database.md) - テーブル定義、インデックス設計、データスコープ制限（TODO: 今後03-features/common/に移動予定）

---

**この共通仕様は、すべてのFlask機能実装で必ず遵守してください。**
