# 組織管理画面 - ワークフロー仕様書

## 📑 目次

- [組織管理画面 - ワークフロー仕様書](#組織管理画面---ワークフロー仕様書)
  - [📑 目次](#-目次)
  - [概要](#概要)
  - [使用するFlaskルート一覧](#使用するflaskルート一覧)
  - [ルート呼び出しマッピング](#ルート呼び出しマッピング)
  - [ワークフロー一覧](#ワークフロー一覧)
    - [初期表示](#初期表示)
      - [処理フロー](#処理フロー)
      - [Flaskルート](#flaskルート)
      - [バリデーション](#バリデーション)
      - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド)
      - [表示メッセージ](#表示メッセージ)
      - [エラーハンドリング](#エラーハンドリング)
      - [ログ出力タイミング](#ログ出力タイミング)
      - [検索条件の保持方法](#検索条件の保持方法)
      - [UI状態](#ui状態)
    - [検索・絞り込み](#検索絞り込み)
      - [処理フロー](#処理フロー-1)
      - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド-1)
      - [表示メッセージ](#表示メッセージ-1)
      - [エラーハンドリング](#エラーハンドリング-1)
      - [ログ出力タイミング](#ログ出力タイミング-1)
      - [検索条件の保持方法](#検索条件の保持方法-1)
      - [UI状態](#ui状態-1)
    - [全体ソート](#全体ソート)
      - [処理詳細](#処理詳細)
    - [ページ内ソート](#ページ内ソート)
      - [処理詳細](#処理詳細-1)
    - [ページング](#ページング)
      - [処理フロー](#処理フロー-2)
      - [処理詳細](#処理詳細-2)
    - [組織登録](#組織登録)
      - [登録ボタン押下](#登録ボタン押下)
        - [処理フロー](#処理フロー-3)
        - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド-2)
      - [登録実行](#登録実行)
        - [処理フロー](#処理フロー-4)
        - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド-3)
        - [バリデーション](#バリデーション-1)
        - [表示メッセージ](#表示メッセージ-2)
      - [ログ出力タイミング](#ログ出力タイミング-2)
    - [組織更新](#組織更新)
      - [更新画面表示](#更新画面表示)
        - [処理フロー](#処理フロー-5)
        - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド-4)
      - [更新実行](#更新実行)
        - [処理フロー](#処理フロー-6)
        - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド-5)
        - [バリデーション](#バリデーション-2)
        - [表示メッセージ](#表示メッセージ-3)
      - [ログ出力タイミング](#ログ出力タイミング-3)
    - [組織参照](#組織参照)
      - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド-6)
      - [ログ出力タイミング](#ログ出力タイミング-4)
    - [組織削除](#組織削除)
      - [処理フロー](#処理フロー-7)
        - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド-7)
      - [表示メッセージ](#表示メッセージ-4)
      - [ログ出力タイミング](#ログ出力タイミング-5)
    - [CSVエクスポート](#csvエクスポート)
        - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド-8)
  - [使用データベース詳細](#使用データベース詳細)
    - [使用テーブル一覧](#使用テーブル一覧)
    - [インデックス最適化](#インデックス最適化)
  - [トランザクション管理](#トランザクション管理)
    - [トランザクション開始・終了タイミング](#トランザクション開始終了タイミング)
  - [セキュリティ実装](#セキュリティ実装)
    - [認証・認可実装](#認証認可実装)
    - [入力検証](#入力検証)
    - [ログ出力ルール](#ログ出力ルール)
  - [関連ドキュメント](#関連ドキュメント)
    - [機能設計・仕様](#機能設計仕様)
    - [アーキテクチャ設計](#アーキテクチャ設計)
    - [共通仕様](#共通仕様)
    - [類似機能](#類似機能)

---

## 概要

このドキュメントは、組織管理画面のユーザー操作に対する処理フロー、バリデーション実行タイミング、データベース処理の詳細を記載します。

**このドキュメントの役割:**
- ✅ ユーザー操作のトリガー条件
- ✅ 処理フローの詳細（Flaskルート呼び出しシーケンス、フォーム送信、リダイレクト）
- ✅ バリデーション実行タイミング（いつチェックするか）
- ✅ エラーハンドリングフロー
- ✅ サーバーサイド処理詳細（SQL、変数、条件分岐、コード例）
- ✅ データベース利用詳細（トランザクション管理、テーブル操作、インデックス）
- ✅ セキュリティ実装詳細（認証、入力検証、ログ出力）
- ✅ Databricks API連携詳細（ワークスペースグループ作成・更新・削除）

**UI仕様書との役割分担:**
- **UI仕様書**: バリデーションルール定義（何をチェックするか）、UI要素の詳細仕様
- **ワークフロー仕様書**: バリデーション実行タイミング（いつどのようにチェックするか）、処理フロー、サーバーサイド実装詳細

**注:** UI要素の詳細やバリデーションルールは [UI仕様書](./ui-specification.md) を参照してください。

---

## 使用するFlaskルート一覧

この画面で使用するすべてのFlaskルート（エンドポイント）を記載します。

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 | 備考 |
|----|---------|---------------|---------|------|---------------|------|
| 1 | 組織一覧初期表示 | `/admin/organizations` | GET | 組織一覧の初期表示 | HTML | 組織一覧の初期表示 |
| 2 | 組織一覧検索 | `/admin/organizations` | POST | 組織検索・一覧表示 | HTML | 組織一覧の検索、ページング対応 |
| 3 | 組織登録画面 | `/admin/organizations/create` | GET | 組織登録画面表示 | HTML（モーダル） | 組織種別・所属組織・契約状態選択肢を含む |
| 4 | 組織登録実行 | `/admin/organizations/register` | POST | 組織登録処理 | リダイレクト (302) | 成功時: `/admin/organizations`、失敗時: フォーム再表示 |
| 5 | 組織参照画面 | `/admin/organizations/<databricks_group_id>` | GET | 組織詳細情報表示 | HTML（モーダル） | - |
| 6 | 組織更新画面 | `/admin/organizations/<databricks_group_id>/edit` | GET | 組織更新画面表示 | HTML（モーダル） | 現在の値を初期表示 |
| 7 | 組織更新実行 | `/admin/organizations/<databricks_group_id>/update` | POST | 組織更新処理 | リダイレクト (302) | 成功時: `/admin/organizations` |
| 8 | 組織削除実行 | `/admin/organizations/delete` | POST | 組織削除処理 | リダイレクト (302) | 成功時: `/admin/organizations` |
| 9 | CSVエクスポート | `/admin/organizations?export=csv` | GET | 組織一覧CSVダウンロード | CSV | 現在の検索条件を適用 |

**注:**
- **レスポンス形式**:
  - `HTML`: Jinja2テンプレートをレンダリングして返す（`render_template()`）
  - `リダイレクト (302)`: 成功時に別のルートへリダイレクト（`redirect(url_for())`）、失敗時はフォームを再表示
  - `CSV`: CSVファイルをダウンロードレスポンスとして返す
- **Flask Blueprint構成**: 組織管理機能は `admin.organizations` Blueprintとして実装

---

## ルート呼び出しマッピング

| ユーザー操作 | トリガー | 呼び出すルート | パラメータ | レスポンス | エラー時の挙動 |
|-------------|---------|-------------|-----------|-----------|---------------|
| 画面初期表示 | URL直接アクセス | `GET /admin/organizations` | `page=1` | HTML（組織一覧画面） | エラーページ表示 |
| 検索ボタン押下 | フォーム送信 | `POST /admin/organizations` | `organization_name, organization_type_id, contact_person_name, contract_status_id, sort_by, order, page` | HTML（検索結果画面） | エラーメッセージ表示 |
| ページボタン押下 | フォーム送信 | `GET /admin/organizations` | `page` | HTML（検索結果画面 | エラーページ表示 |
| 登録ボタン押下 | ボタンクリック | `GET /admin/organizations/create` | なし | HTML（登録モーダル） | エラーページ表示 |
| 登録実行 | フォーム送信 | `POST /admin/organizations/register` | フォームデータ | リダイレクト → `GET /admin/organizations` | フォーム再表示（エラーメッセージ付き） |
| 参照ボタン押下 | ボタンクリック | `GET /admin/organizations/<databricks_group_id>` | databricks_group_id | HTML（参照モーダル） | 404エラーページ表示 |
| 更新ボタン押下 | ボタンクリック | `GET /admin/organizations/<databricks_group_id>/edit` | databricks_group_id | HTML（更新モーダル） | 404エラーページ表示 |
| 更新実行 | フォーム送信 | `POST /admin/organizations/<databricks_group_id>/update` | フォームデータ | リダイレクト → `GET /admin/organizations` | フォーム再表示（エラーメッセージ付き） |
| 削除実行 | フォーム送信 | `POST /admin/organizations/delete` | databricks_group_id | リダイレクト → `GET /admin/organizations` | エラーメッセージ表示 |
| CSVエクスポート | ボタンクリック | `GET /admin/organizations?export=csv` | 検索条件 | CSVダウンロード | エラーメッセージ表示 |

---

## ワークフロー一覧

### 初期表示

**トリガー:** URL直接アクセス時（ユーザーが画面にアクセスしたとき）

**前提条件:**
- ユーザーがログイン済み（Databricks認証完了）
- 適切な権限を持っている（システム保守者、管理者、販社ユーザー）

#### 処理フロー

```mermaid
flowchart TD
    Start([URL直接アクセス]) --> Auth[認証チェック<br>Databricksリバースプロキシヘッダ確認]
    Auth --> CheckAuth{認証済み?}
    CheckAuth -->|未認証| LoginRedirect[ログイン画面へリダイレクト]

    CheckAuth -->|認証OK| Permission[権限チェック]
    Permission --> CheckPerm{権限OK?}
    CheckPerm -->|権限なし| Error403[403エラーページ表示]

    CheckPerm -->|権限OK| Init[検索条件を初期化<br>page=1,<br>sort_by=organization_id, order=asc]
    Init --> Scope[データスコープ制限を適用<br>organization_id]
    Scope --> SetParams[Cookieに検索条件を格納]
    SetParams --> Count[検索結果件数取得DBクエリ実行]
    Count --> CheckDB0{DBクエリ結果}

    CheckDB0 -->|成功| Query[検索結果取得DBクエリ実行]
    CheckDB0 -->|失敗| Error500[500エラーページ表示]

    Query --> CheckDB{DBクエリ結果}

    CheckDB -->|成功| Template[Jinja2テンプレートレンダリング<br>render_template<br>admin/organizations/list.html<br>organizations=organizations, total=total]
    Template --> Response[HTMLレスポンス返却]

    CheckDB -->|失敗| Error500

    LoginRedirect --> End([処理完了])
    Response --> End
    Error403 --> End
    Error500 --> End
```

#### Flaskルート

| ルート | エンドポイント | 詳細 |
|-------|---------------|------|
| 組織一覧初期表示表示 | `GET /admin/organizations` | クエリパラメータ: `page`, `organization_name`, `organization_type_id`, `contact_person_name`, `contract_status_id`, `sort_by`, `order` |

#### バリデーション

**実行タイミング:** なし（初期表示のため、デフォルト値を使用）

**データスコープ制限:**
- ログインユーザーの `organization_id` でフィルタリング

#### 処理詳細（サーバーサイド）

**認証・認可チェック**

リバースプロキシヘッダから認証情報を取得し、権限を確認します。

**処理内容:**
- ヘッダ `X-Forwarded-User` からユーザーIDを取得
- データベースから現在ユーザー情報を取得（ロール、組織ID）

**変数・パラメータ:**
- `current_user_id`: string - リバースプロキシヘッダから取得したユーザーID
- `current_user`: User - データベースから取得したユーザーオブジェクト
- `role`: string - ユーザーのロール
- `organization_id`: string - データスコープ制限用の組織ID

**実装例:**
```python
# app/auth.py
from flask import request, abort, g
from functools import wraps
from app.models import User, Organization, OrganizationClosure
from app import db
import logging

logger = logging.getLogger(__name__)

def get_current_user():
    """
    リバースプロキシヘッダからユーザー情報を取得

    フロー:
    1. X-Forwarded-UserヘッダからユーザーIDを取得
    2. ユーザーIDがない場合は401エラー
    3. データベースからユーザー情報を取得
    4. ユーザーが存在しない、または削除済みの場合は403エラー
    5. ユーザー情報を返却
    """
    # ① ヘッダからユーザーID取得
    user_id = request.headers.get('X-Forwarded-User')

    # ② 認証チェック
    if not user_id:
        logger.warning('認証ヘッダが存在しません')
        abort(401)

    # ③ ユーザー情報取得
    user = User.query.filter_by(
        user_id=user_id,
        delete_flag=0
    ).first()

    # ④ ユーザー存在チェック
    if not user:
        logger.warning(f'ユーザーが見つかりません: {user_id}')
        abort(403)

    # ⑤ ユーザー情報を返却
    return user


def require_permission(permission):
    """
    権限チェックデコレーター

    Args:
        permission: 必要な権限（例: 'organization:read', 'organization:write'）

    フロー:
    1. ユーザー情報を取得
    2. ユーザーの権限をチェック
    3. 権限がない場合は403エラー
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # ① ユーザー情報取得
            current_user = get_current_user()

            # ② 権限チェック
            if not has_permission(current_user, permission):
                logger.warning(f'権限がありません: user_id={current_user.user_id}, permission={permission}')
                abort(403)

            # ③ リクエストコンテキストにユーザー情報を保存
            g.current_user = current_user

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def has_permission(user, permission):
    """
    ユーザーが指定された権限を持っているか確認

    Args:
        user: ユーザーオブジェクト
        permission: 確認する権限

    Returns:
        bool: 権限がある場合True
    """
    # ロールIDに基づいた権限チェック
    # 1: システム保守者, 2: 管理者, 3: 販社ユーザー, 4: サービス利用者

    if user.role_id == 4:  # サービス利用者
        return False

    # システム保守者、管理者、販社ユーザーは組織管理権限あり
    if permission in ['organization:read', 'organization:write']:
        return user.role_id in [1, 2, 3]

    return False


def apply_data_scope(query, user):
    """
    データスコープ制限を適用

    Args:
        query: SQLAlchemyクエリオブジェクト
        user: ユーザーオブジェクト

    Returns:
        フィルタ適用済みクエリ

    フロー:
    1. organization_closureテーブルをJOIN
    2. parent_organization_idがユーザーの組織IDと一致する条件を追加
    3. delete_flag=0の条件を追加
    """
    return query\
        .join(OrganizationClosure,
              Organization.organization_id == OrganizationClosure.subsidiary_organization_id)\
        .filter(OrganizationClosure.parent_organization_id == user.organization_id)\
        .filter(Organization.delete_flag == 0)
```

**初期表示**

**実装例:**
```python
# app/blueprints/admin/organizations/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, make_response, g
from app.models import Organization, OrganizationClosure, OrganizationType, ContractStatus
from app.auth import get_current_user, require_permission, apply_data_scope
from app import db
import logging

logger = logging.getLogger(__name__)

# Blueprint作成
admin_organizations_bp = Blueprint(
    'admin.organizations',
    __name__,
    url_prefix='/admin/organizations'
)


@admin_organizations_bp.route('', methods=['GET'])
@require_permission('organization:read')
def list_organizations():
    """
    組織一覧画面の初期表示・検索

    フロー:
    1. 認証チェック（デコレーターで実施）
    2. 権限チェック（デコレーターで実施）
    3. ロールチェック（サービス利用者は画面表示不可）
    4. クエリパラメータ取得
    5. CSVエクスポート分岐
    6. データスコープ制限を適用
    7. 検索結果件数取得
    8. 検索結果取得
    9. HTMLレンダリング
    """
    try:
        # ① ② 認証・権限チェック（デコレーターで実施済み）
        current_user = g.current_user

        # ③ ロールチェック: サービス利用者は画面表示不可
        if current_user.role_id == 4:
            logger.warning(f'サービス利用者による組織一覧画面アクセス: user_id={current_user.user_id}')
            abort(403)

        logger.info(f'組織一覧画面表示開始: user_id={current_user.user_id}')

        # ④ クエリパラメータ取得
        page = request.args.get('page', 1, type=int)
        per_page = 25  # 固定
        organization_name = request.args.get('organization_name', '')
        organization_type_id = request.args.get('organization_type_id', type=int)
        contact_person_name = request.args.get('contact_person_name', '')
        contract_status_id = request.args.get('contract_status_id', type=int)
        sort_by = request.args.get('sort_by', 'organization_id')
        order = request.args.get('order', 'asc')

        # ⑤ CSVエクスポート分岐
        if request.args.get('export') == 'csv':
            return export_organizations_csv(current_user)

        # ⑥ ベースクエリ作成とデータスコープ制限適用
        query = db.session.query(Organization)
        query = apply_data_scope(query, current_user)

        # ⑦ 検索条件適用
        # 部分一致検索用にLIKEパラメータを作成
        if organization_name:
            organization_name_like = f'%{organization_name}%'
            query = query.filter(Organization.organization_name.like(organization_name_like))

        if organization_type_id:
            query = query.filter(Organization.organization_type_id == organization_type_id)

        if contact_person_name:
            contact_person_like = f'%{contact_person_name}%'
            query = query.filter(Organization.contact_person.like(contact_person_like))

        if contract_status_id:
            query = query.filter(Organization.contract_status_id == contract_status_id)

        # ⑧ 検索結果件数取得
        logger.info(f'組織検索件数取得開始: user_id={current_user.user_id}')
        total = query.count()
        logger.info(f'組織検索件数取得成功: total={total}')

        # ⑨ ソート適用
        if hasattr(Organization, sort_by):
            if order == 'asc':
                query = query.order_by(getattr(Organization, sort_by).asc())
            else:
                query = query.order_by(getattr(Organization, sort_by).desc())

        # ⑩ ページング適用
        offset = (page - 1) * per_page

        logger.info(f'組織一覧取得開始: user_id={current_user.user_id}, page={page}')
        organizations = query.limit(per_page).offset(offset).all()
        logger.info(f'組織一覧取得成功: count={len(organizations)}')

        # ⑪ HTMLレンダリング
        return render_template(
            'admin/organizations/list.html',
            organizations=organizations,
            total=total,
            page=page,
            per_page=per_page,
            search_params={
                'organization_name': organization_name,
                'organization_type_id': organization_type_id,
                'contact_person_name': contact_person_name,
                'contract_status_id': contract_status_id
            },
            sort_by=sort_by,
            order=order
        )

    except Exception as e:
        logger.error(f'組織一覧表示エラー: user_id={current_user.user_id}, error={str(e)}')
        abort(500)
```

#### 表示メッセージ

| メッセージID | 表示内容 | 表示タイミング | 表示場所 |
|-------------|---------|---------------|---------|
| ERR_001 | データの取得に失敗しました | DBクエリ失敗時 | エラーページ |

#### エラーハンドリング

| HTTPステータス | エラー種別 | 処理内容 | 表示内容 |
|--------------|-----------|---------|---------|
| 401 | 認証エラー | ログイン画面へリダイレクト | - |
| 403 | 権限エラー | 403エラーページ表示 | この操作を実行する権限がありません |
| 500 | データベースエラー | 500エラーページ表示 | データの取得に失敗しました |

#### ログ出力タイミング
DBクエリ実行の直前、直後に操作ログを出力する

#### 検索条件の保持方法
Cookieに検索条件を保持する

#### UI状態

- 検索条件: デフォルト値
  - 組織名: 空
  - 組織種別: すべて
  - 担当者名: 空
  - 契約状態: すべて
  - ソート項目: 空
  - ソート順: 空
- テーブル: 組織一覧データ表示
- ページネーション: 1ページ目を選択状態

---

### 検索・絞り込み

**トリガー:** (2.7) 検索ボタンクリック（フォーム送信）

**前提条件:**
- 検索条件が入力されている（空でも可）

#### 処理フロー

```mermaid
flowchart TD
    Start([検索ボタンクリック]) --> Permission[権限チェック]
    Permission --> CheckPerm{権限OK?}
    CheckPerm -->|権限なし| Error403[403エラーページ表示]

    CheckPerm -->|権限OK| PutParams[Cookieに検索条件を格納]
    PutParams --> Convert[検索条件をクエリパラメータに変換<br>page: 1（リセット）]
    Convert --> Scope[データスコープ制限を適用]
    Scope --> Count[検索結果件数取得DBクエリ実行<br>検索条件を適用]
    Count --> CheckDB0{DBクエリ結果}

    CheckDB0 -->|成功|Query[検索結果DBクエリ実行<br>検索条件を適用]
    CheckDB0 -->|失敗| Error500[500エラーページ表示]

    Query --> CheckDB{DBクエリ結果}

    CheckDB -->|成功| Template[Jinja2テンプレートレンダリング]
    Template --> Response[HTMLレスポンス返却]

    CheckDB -->|失敗| Error500

    Response --> End
    Error403 --> End
    Error500 --> End
```

#### 処理詳細（サーバーサイド）

**実装例:**
```python
@admin_organizations_bp.route('', methods=['POST'])
@require_permission('organization:read')
def search_organizations():
    """
    組織検索処理

    フロー:
    1. 権限チェック（デコレーターで実施）
    2. フォームデータ取得
    3. クエリパラメータに変換
    4. ページ番号を1にリセット
    5. GETリクエストにリダイレクト（PRGパターン）
    """
    try:
        # ① 権限チェック（デコレーターで実施済み）
        current_user = g.current_user

        logger.info(f'組織検索開始: user_id={current_user.user_id}')

        # ② フォームデータ取得
        organization_name = request.form.get('organization_name', '')
        organization_type_id = request.form.get('organization_type_id', type=int)
        contact_person_name = request.form.get('contact_person_name', '')
        contract_status_id = request.form.get('contract_status_id', type=int)
        sort_by = request.form.get('sort_by', 'organization_id')
        order = request.form.get('order', 'asc')

        # ③④⑤ GETリクエストにリダイレクト（PRGパターン）
        logger.info(f'組織検索リダイレクト: user_id={current_user.user_id}')

        return redirect(url_for(
            'admin.organizations.list_organizations',
            organization_name=organization_name,
            organization_type_id=organization_type_id,
            contact_person_name=contact_person_name,
            contract_status_id=contract_status_id,
            page=1,  # ページ番号をリセット
            sort_by=sort_by,
            order=order
        ))

    except Exception as e:
        logger.error(f'組織検索エラー: user_id={current_user.user_id}, error={str(e)}')
        flash('検索処理に失敗しました', 'error')
        return redirect(url_for('admin.organizations.list_organizations'))
```

**② DBクエリ実行**

初期表示と同じクエリを実行します（検索条件が追加されます）。

#### 表示メッセージ

| メッセージID | 表示内容 | 表示タイミング | 表示場所 |
|-------------|---------|---------------|---------|
| ERR_001 | データの取得に失敗しました | DBクエリ失敗時 | エラーページ |

#### エラーハンドリング

| HTTPステータス | エラー種別 | 処理内容 | 表示内容 |
|--------------|-----------|---------|---------|
| 403 | 権限エラー | 403エラーページ表示 | この操作を実行する権限がありません |
| 500 | データベースエラー | 500エラーページ表示 | データの取得に失敗しました |

#### ログ出力タイミング
DBクエリ実行の直前、直後に操作ログを出力する

#### 検索条件の保持方法
Cookieに検索条件を保持する

#### UI状態
- 検索条件: 入力値を保持（フォームに再設定）
- テーブル: 検索結果データ表示
- ページネーション: 1ページ目にリセット

---

### 全体ソート

**トリガー:** (2) 検索条件欄でソート項目、ソート順ドロップダウンで具体値を選択し、検索を実行

#### 処理詳細
検索条件欄のソート項目ドロップダウンで選択した内容に対して、ソート順ドロップダウンで選択した順序でページをまたいだソートを行う。
詳細は[共通仕様書](../../common/common-specification.md)参照のこと。

---

### ページ内ソート

**トリガー:**（6）データテーブルのソート可能カラム（組織名、組織種別、住所、電話番号、担当者名、契約状態、操作）のヘッダをクリック

#### 処理詳細
データテーブルのヘッダをクリックすることで、ページ内で閉じたソートを行う。
詳細は[共通仕様書](../../common/common-specification.md)参照のこと

---

### ページング

**トリガー:** (6.9) ページネーションのページ番号ボタンクリック

#### 処理フロー

```mermaid
flowchart TD
    Start([ページ番号ボタンクリック]) --> GetParams[Cookieから検索条件を取得]
    GetParams --> Convert[検索条件をクエリパラメータに変換]
    Convert --> Scope[データスコープ制限を適用]
    Scope --> Count[検索結果件数取得DBクエリ実行<br>検索条件を適用]
    Count --> CheckDB0{DBクエリ結果}
    
    CheckDB0 -->|成功| Query[検索結果DBクエリ実行<br>検索条件を適用]
    CheckDB0 -->|失敗| Error500[500エラーページ表示]
    
    Query --> CheckDB{DBクエリ結果}

    CheckDB -->|成功| Template[Jinja2テンプレートレンダリング]
    Template --> Response[HTMLレスポンス返却]

    CheckDB -->|失敗| Error500

    Response --> 処理完了
    Error500 --> 処理完了
```

#### 処理詳細
ページネーションのページ番号を選択することで、選択されたページ番号に対応するデータをデータテーブルに表示する。
具体的な処理は[検索・絞り込み](#検索絞り込み)の処理と同様とする。

---

### 組織登録

#### 登録ボタン押下

**トリガー:** (3.1) 登録ボタンクリック

**前提条件:**
- ユーザーがシステム保守者、管理者、または販社ユーザー権限を持っている

##### 処理フロー

```mermaid
flowchart TD
    Start([登録ボタンクリック]) --> Permission[権限チェック]
    Permission --> CheckPerm{権限OK?}
    CheckPerm -->|権限なし| Error403[403エラー ※1]

    CheckPerm -->|権限OK| LoadOrgType[組織種別マスタを取得<br>SELECT * FROM organization_type_master]
    LoadOrgType --> CheckDB1{DBクエリ結果}

    CheckDB1 -->|成功| LoadOrgs[組織マスタを取得<br>SELECT * FROM organization_master<br>データスコープ制限適用]
    CheckDB1 -->|失敗| Error500[ステータスメッセージモーダル（エラー）]

    LoadOrgs --> CheckDB2{DBクエリ結果}

    CheckDB2 -->|成功| LoadContractStatus[契約状態マスタを取得<br>SELECT * FROM contract_status_master]
    CheckDB2 -->|失敗| Error500

    LoadContractStatus --> CheckDB3{DBクエリ結果}

    CheckDB3 -->|成功| Template[登録モーダルをレンダリング<br>render_template<br>admin/oraganizations/form.html]
    CheckDB3 -->|失敗| Error500

    Template --> View[モーダル表示]

    Error403 --> End([処理完了])
    Error500 --> End
    View --> End
```

※1　403エラー発生時、ドロップダウン、テキストボックスに具体的なデータは表示せず、空で表示する。

##### 処理詳細（サーバーサイド）

**実装例:**
```python
@admin_organizations_bp.route('/create', methods=['GET'])
@require_permission('organization:write')
def create_organization_form():
    """
    組織登録画面表示

    フロー:
    1. 権限チェック（デコレーターで実施）
    2. 組織種別一覧取得
    3. 所属組織一覧取得（データスコープ制限適用）
    4. 契約状態一覧取得
    5. 登録モーダルレンダリング
    """
    try:
        # ① 権限チェック（デコレーターで実施済み）
        current_user = g.current_user

        logger.info(f'組織登録画面表示開始: user_id={current_user.user_id}')

        # ② 組織種別一覧取得
        logger.info('組織種別一覧取得開始')
        organization_types = OrganizationType.query.filter_by(delete_flag=0).order_by(
            OrganizationType.organization_type_id
        ).all()
        logger.info(f'組織種別一覧取得成功: count={len(organization_types)}')

        # ③ 所属組織一覧取得（データスコープ制限適用）
        logger.info('所属組織一覧取得開始')
        affiliated_organizations = db.session.query(Organization)\
            .join(OrganizationClosure,
                  Organization.organization_id == OrganizationClosure.subsidiary_organization_id)\
            .filter(OrganizationClosure.parent_organization_id == current_user.organization_id)\
            .filter(Organization.delete_flag == 0)\
            .order_by(Organization.organization_name)\
            .all()
        logger.info(f'所属組織一覧取得成功: count={len(affiliated_organizations)}')

        # ④ 契約状態一覧取得
        logger.info('契約状態一覧取得開始')
        contract_statuses = ContractStatus.query.filter_by(delete_flag=0).order_by(
            ContractStatus.contract_status_id
        ).all()
        logger.info(f'契約状態一覧取得成功: count={len(contract_statuses)}')

        # ⑤ 登録モーダルレンダリング
        return render_template(
            'admin/organizations/form.html',
            mode='create',
            organization_types=organization_types,
            affiliated_organizations=affiliated_organizations,
            contract_statuses=contract_statuses
        )

    except Exception as e:
        logger.error(f'組織登録画面表示エラー: user_id={current_user.user_id}, error={str(e)}')
        abort(500)
```

---

#### 登録実行

**トリガー:** (7.12) 登録ボタンクリック（モーダル内）クリック後に表示される登録実施確認モーダルで「はい」を選択

##### 処理フロー

```mermaid
flowchart TD
    Start([登録ボタンクリック]) --> CheckAuth{権限チェック}
    
    CheckAuth --> |権限OK| FrontValidate[フロントサイドバリデーション]
    CheckAuth --> |権限なし| Error403[403エラー ※1]

    FrontValidate --> ScopeCheck[所属組織IDのデータスコープチェック]

    ScopeCheck --> CheckDB1{DBクエリ結果}

    CheckDB1 --> |成功| CheckScope{スコープOK?}
    CheckDB1 --> |失敗| Error500[ステータスメッセージモーダル（エラー）]

    CheckScope --> |NG| Error404[404エラー]
    CheckScope --> |OK| CreateOrgId[組織ID生成<br>AutoIncrement]

    CreateOrgId --> CheckDB2{DBクエリ結果}

    CheckDB2 -->|成功| CreateDbxGroup[Databricksグループ作成、<br>メンバーに所属組織のDatabricksグループを追加]
    CheckDB2 -->|失敗| Error500

    CreateDbxGroup --> CreateDbxGroupResult{グループ作成結果}

    CreateDbxGroupResult -->|成功| InsertUC[UnitiyCatalog<br>organization_master<br>組織登録]
    CreateDbxGroupResult -->|失敗| Error500

    InsertUC --> CheckUC{UnitiyCatalog<br>操作結果}

    CheckUC -->|成功| StartDBTx[OLTP DB<br>トランザクション開始]
    CheckUC -->|失敗| RollbackDbxGroup[Databricksグループ削除]
    RollbackDbxGroup --> Error500

    StartDBTx --> InsertDBMstr[OLTP DB<br>organization_master<br>へ組織登録]
    InsertDBMstr --> CheckDBMstr{DB操作結果}

    CheckDBMstr -->|成功| InsertDBClosure[OLTP DB<br>organization_closure<br>組織登録]
    CheckDBMstr -->|失敗| RollbackUC[UnitiyCatalog<br>oraganization_master<br>組織削除]
    RollbackUC --> RollbackDbxGroup

    InsertDBClosure --> CheckDBClosure{DB操作結果}

    CheckDBClosure -->|成功| CommitDBTx[OLTP DB<br>コミット]
    CheckDBClosure -->|失敗| RollbackMstr[OLTP DB<br>organization_master<br>組織削除]
    RollbackMstr --> RollbackUC

    CommitDBTx --> Redirect[一覧画面へリダイレクト<br>redirect url_for admin.list_organizations]
    Redirect --> Success[ステータスメッセージモーダル（成功）]

    Error403 --> End([処理完了])
    Error404 --> End
    Error500 --> End
    Success --> End
```

※1　403エラー発生時、ドロップダウン、テキストボックスに具体的なデータは表示せず、空で表示する。

---

##### 処理詳細（サーバーサイド）

**実装例:**
```python
from app.databricks_client import create_databricks_group, DatabricksAPIError
from datetime import datetime


@admin_organizations_bp.route('/register', methods=['POST'])
@require_permission('organization:write')
def register_organization():
    """
    組織登録実行

    フロー:
    1. 権限チェック（デコレーターで実施）
    2. フォームデータ取得・バリデーション
    3. 所属組織のデータスコープチェック
    4. Databricksグループ作成
    5. トランザクション開始
    6. organization_master登録
    7. organization_closure登録
    8. コミット
    9. 成功メッセージ表示
    10. 一覧画面へリダイレクト

    エラー時のロールバック:
    - organization_master登録失敗 → Databricksグループ削除
    - organization_closure登録失敗 → organization_master削除 + Databricksグループ削除
    """
    current_user = g.current_user
    databricks_group_id = None

    try:
        logger.info(f'組織登録開始: user_id={current_user.user_id}')

        # ② フォームデータ取得
        organization_name = request.form.get('organization_name')
        organization_type_id = request.form.get('organization_type_id', type=int)
        affiliated_organization_id = request.form.get('affiliated_organization_id', type=int)
        address = request.form.get('address')
        phone_number = request.form.get('phone_number')
        fax_number = request.form.get('fax_number')
        contact_person = request.form.get('contact_person')
        contract_status_id = request.form.get('contract_status_id', type=int)
        contract_start_date = request.form.get('contract_start_date')
        contract_end_date = request.form.get('contract_end_date')

        # バリデーション（簡易版、実際はFlask-WTFを使用）
        if not all([organization_name, organization_type_id, affiliated_organization_id,
                   address, phone_number, contact_person, contract_status_id, contract_start_date]):
            flash('必須項目を入力してください', 'error')
            return redirect(url_for('admin.organizations.create_organization_form'))

        # ③ 所属組織のデータスコープチェック
        logger.info(f'所属組織データスコープチェック開始: affiliated_organization_id={affiliated_organization_id}')
        affiliated_org = db.session.query(Organization)\
            .join(OrganizationClosure,
                  Organization.organization_id == OrganizationClosure.subsidiary_organization_id)\
            .filter(OrganizationClosure.parent_organization_id == current_user.organization_id)\
            .filter(Organization.organization_id == affiliated_organization_id)\
            .filter(Organization.delete_flag == 0)\
            .first()

        if not affiliated_org:
            logger.warning(f'所属組織が見つかりません: affiliated_organization_id={affiliated_organization_id}')
            abort(404)

        logger.info('所属組織データスコープチェック成功')

        # ④ Databricksグループ作成
        # 組織ID生成（AutoIncrementのため、先にダミーレコードを作成してIDを取得）
        temp_org = Organization(
            organization_name='temp',
            organization_type_id=organization_type_id,
            address='temp',
            phone_number='temp',
            contact_person='temp',
            contract_status_id=contract_status_id,
            contract_start_date=contract_start_date,
            creater=current_user.user_id,
            delete_flag=1  # 一時的に削除フラグを立てる
        )
        db.session.add(temp_org)
        db.session.flush()  # IDを取得するためにフラッシュ
        organization_id = temp_org.organization_id
        db.session.rollback()  # ダミーレコードを削除

        logger.info(f'組織ID生成: organization_id={organization_id}')

        # Databricksグループ作成
        group_name = f'organization_{organization_id}'
        databricks_group_id = create_databricks_group(
            group_name=group_name,
            parent_group_id=affiliated_org.databricks_group_id
        )

        logger.info(f'Databricksグループ作成成功: group_id={databricks_group_id}')

        # ⑤ トランザクション開始（明示的ではなくSQLAlchemyのセッション管理）

        # ⑥ organization_master登録
        logger.info('organization_master登録開始')
        organization = Organization(
            organization_id=organization_id,
            organization_name=organization_name,
            organization_type_id=organization_type_id,
            affiliated_organization_id=affiliated_organization_id,
            address=address,
            phone_number=phone_number,
            fax_number=fax_number,
            contact_person=contact_person,
            contract_status_id=contract_status_id,
            contract_start_date=datetime.strptime(contract_start_date, '%Y-%m-%d').date(),
            contract_end_date=datetime.strptime(contract_end_date, '%Y-%m-%d').date() if contract_end_date else None,
            databricks_group_id=databricks_group_id,
            creater=current_user.user_id,
            create_date=datetime.now()
        )
        db.session.add(organization)
        db.session.flush()  # エラーチェック
        logger.info('organization_master登録成功')

        # ⑦ organization_closure登録
        logger.info('organization_closure登録開始')

        # 自己参照（depth=0）
        closure_self = OrganizationClosure(
            parent_organization_id=organization_id,
            subsidiary_organization_id=organization_id,
            depth=0
        )
        db.session.add(closure_self)

        # 所属組織との関係（depth=1）
        closure_parent = OrganizationClosure(
            parent_organization_id=affiliated_organization_id,
            subsidiary_organization_id=organization_id,
            depth=1
        )
        db.session.add(closure_parent)

        # 所属組織の祖先すべてとの関係を登録
        ancestor_closures = OrganizationClosure.query.filter_by(
            subsidiary_organization_id=affiliated_organization_id
        ).all()

        for ancestor_closure in ancestor_closures:
            if ancestor_closure.parent_organization_id != affiliated_organization_id:
                new_closure = OrganizationClosure(
                    parent_organization_id=ancestor_closure.parent_organization_id,
                    subsidiary_organization_id=organization_id,
                    depth=ancestor_closure.depth + 1
                )
                db.session.add(new_closure)

        db.session.flush()  # エラーチェック
        logger.info('organization_closure登録成功')

        # ⑧ コミット
        db.session.commit()
        logger.info(f'組織登録コミット成功: organization_id={organization_id}')

        # ⑨ 成功メッセージ
        flash('組織を登録しました', 'success')

        # ⑩ 一覧画面へリダイレクト
        return redirect(url_for('admin.organizations.list_organizations'))

    except DatabricksAPIError as e:
        # Databricksグループ作成失敗
        db.session.rollback()
        logger.error(f'組織登録失敗（Databricks API）: error={str(e)}')
        flash('Databricksグループの作成に失敗しました', 'error')
        return redirect(url_for('admin.organizations.create_organization_form'))

    except Exception as e:
        # DB操作失敗
        db.session.rollback()

        # Databricksグループのロールバック
        if databricks_group_id:
            try:
                from app.databricks_client import delete_databricks_group
                delete_databricks_group(databricks_group_id)
                logger.info(f'Databricksグループロールバック成功: group_id={databricks_group_id}')
            except Exception as rollback_error:
                logger.error(f'Databricksグループロールバック失敗: group_id={databricks_group_id}, error={str(rollback_error)}')

        logger.error(f'組織登録失敗: error={str(e)}')
        flash('組織の登録に失敗しました', 'error')
        return redirect(url_for('admin.organizations.create_organization_form'))
```

##### バリデーション

**実行タイミング:** 登録ボタンクリック直後（サーバーサイド）

**バリデーションルール:** [UI仕様書](./ui-specification.md) の要素詳細 (7) 組織登録/更新モーダル > バリデーション を参照

##### 表示メッセージ

| メッセージID | 表示内容 | 表示タイミング | 表示場所 |
|-------------|---------|---------------|---------|
| - | 組織を登録しました | 組織登録成功時 | ステータスメッセージモーダル（成功） |
| - | 組織登録に失敗しました | API呼び出し失敗時、DB操作失敗時 | ステータスメッセージモーダル（エラー） |

#### ログ出力タイミング
DBクエリ実行の直前、直後に操作ログを出力する

---

### 組織更新

#### 更新画面表示

**トリガー:** (6.8) 更新ボタンクリック

##### 処理フロー

```mermaid
flowchart TD
    Start([更新ボタンクリック]) --> Permission[権限チェック]
    Permission --> CheckPerm{権限OK?}
    CheckPerm -->|権限なし| Error403[403エラー ※1]

    CheckPerm -->|権限OK| LoadOrganization[組織情報を取得<br>SELECT * FROM organization_master<br>WHERE databricks_group_id = :databricks_group_id]
    LoadOrganization --> CheckDB1{DBクエリ結果}

    CheckDB1 -->|成功| CheckData{データ存在?}
    CheckDB1 -->|失敗| Error500[ステータスメッセージモーダル（エラー）]

    CheckData -->|なし| Error404[404エラー]

    CheckData -->|あり| ScopeCheck[データスコープチェック]
    ScopeCheck --> CheckScope{スコープOK?}
    CheckScope -->|NG| Error404

    CheckScope -->|OK| LoadContractStatus[契約状態マスタを取得<br>SELECT * FROM contract_status_master]
    LoadContractStatus --> CheckDB2{DBクエリ結果}

    CheckDB2 -->|成功| Template[更新モーダルをレンダリング<br>現在の値を初期表示]
    CheckDB2 -->|失敗| Error500

    Template --> View[モーダル表示]

    Error403 --> View
    Error404 --> View

    View --> End([処理完了])
    Error500 --> End   
```

※1　403エラー発生時、ドロップダウン、テキストボックスに具体的なデータは表示せず、空で表示する。

##### 処理詳細（サーバーサイド）

**実装例:**
```python
@admin_organizations_bp.route('/<databricks_group_id>/edit', methods=['GET'])
@require_permission('organization:write')
def edit_organization_form(databricks_group_id):
    """
    組織更新画面表示

    フロー:
    1. 権限チェック（デコレーターで実施）
    2. 組織情報取得（データスコープ制限適用）
    3. データ存在チェック
    4. 契約状態一覧取得
    5. 更新モーダルレンダリング
    """
    try:
        # ① 権限チェック（デコレーターで実施済み）
        current_user = g.current_user

        logger.info(f'組織更新画面表示開始: user_id={current_user.user_id}, databricks_group_id={databricks_group_id}')

        # ② 組織情報取得（データスコープ制限適用）
        logger.info('組織情報取得開始')
        organization = db.session.query(Organization)\
            .join(OrganizationClosure,
                  Organization.organization_id == OrganizationClosure.subsidiary_organization_id)\
            .filter(OrganizationClosure.parent_organization_id == current_user.organization_id)\
            .filter(Organization.databricks_group_id == databricks_group_id)\
            .filter(Organization.delete_flag == 0)\
            .first()

        # ③ データ存在チェック
        if not organization:
            logger.warning(f'組織が見つかりません: databricks_group_id={databricks_group_id}')
            abort(404)

        logger.info(f'組織情報取得成功: organization_id={organization.organization_id}')

        # ④ 契約状態一覧取得
        logger.info('契約状態一覧取得開始')
        contract_statuses = ContractStatus.query.filter_by(delete_flag=0).order_by(
            ContractStatus.contract_status_id
        ).all()
        logger.info(f'契約状態一覧取得成功: count={len(contract_statuses)}')

        # ⑤ 更新モーダルレンダリング
        return render_template(
            'admin/organizations/form.html',
            mode='edit',
            organization=organization,
            contract_statuses=contract_statuses
        )

    except Exception as e:
        logger.error(f'組織更新画面表示エラー: databricks_group_id={databricks_group_id}, error={str(e)}')
        abort(500)
```

---

#### 更新実行

**トリガー:** (7.12) 更新ボタン（モーダル内）クリック後に表示される更新実行確認モーダルで「はい」を選択

##### 処理フロー

```mermaid
flowchart TD
    Start([更新ボタンクリック]) --> CheckAuth{権限チェック}

    CheckAuth --> |権限OK| FrontValidate[フロントサイドバリデーション]
    CheckAuth --> |権限なし| Error403[403エラー ※1]

    FrontValidate --> CheckExists[組織の存在チェック<br>SELECT * FROM organization_master<br>WHERE databricks_group_id = :databricks_group_id]
    CheckExists --> CheckDB1{DBクエリ結果}

    CheckDB1 -->|成功| CheckExistsResult{組織存在?}
    CheckDB1 -->|失敗| Error500[ステータスメッセージモーダル（エラー）]

    CheckExistsResult -->|存在しない| NotFoundError[エラー表示<br>指定された組織が見つかりません]
    NotFoundError --> ValidEnd[処理中断]

    CheckExistsResult -->|存在する| UpdateUC[UnitiyCatalog<br>organization_master<br>組織更新]
    UpdateUC --> CheckUC{UnitiyCatalog<br>操作結果}

    CheckUC -->|成功| UpdateDB[OLTP DB<br>organization_master<br>組織更新]
    CheckUC -->|失敗| Error500

    UpdateDB --> CheckDBMstr{DB操作結果}

    CheckDBMstr -->|成功| Redirect[一覧画面へリダイレクト<br>redirect url_for admin.list_organizations]
    CheckDBMstr -->|失敗| RollbackUC[UnitiyCatalog<br>oraganization_master<br>元データを復元]
    RollbackUtc --> Error500

    Redirect --> Success[ステータスメッセージモーダル（成功）]

    ValidEnd --> End([処理完了])
    Success --> End
    Error500 --> End
    Error403 --> End
```

※1　403エラー発生時、ドロップダウン、テキストボックスに具体的なデータは表示せず、空で表示する。

**注:** 組織更新時にDatabricks API連携は不要

##### 処理詳細（サーバーサイド）

**実装例:**
```python
@admin_organizations_bp.route('/<databricks_group_id>/update', methods=['POST'])
@require_permission('organization:write')
def update_organization(databricks_group_id):
    """
    組織更新実行

    フロー:
    1. 権限チェック（デコレーターで実施）
    2. フォームデータ取得・バリデーション
    3. 元データ取得（データスコープチェック含む）
    4. 存在チェック
    5. organization_master更新
    6. コミット
    7. 成功メッセージ表示
    8. 一覧画面へリダイレクト
    """
    current_user = g.current_user

    try:
        logger.info(f'組織更新開始: user_id={current_user.user_id}, databricks_group_id={databricks_group_id}')

        # ② フォームデータ取得
        organization_name = request.form.get('organization_name')
        organization_type_id = request.form.get('organization_type_id', type=int)
        address = request.form.get('address')
        phone_number = request.form.get('phone_number')
        fax_number = request.form.get('fax_number')
        contact_person = request.form.get('contact_person')
        contract_status_id = request.form.get('contract_status_id', type=int)
        contract_start_date = request.form.get('contract_start_date')
        contract_end_date = request.form.get('contract_end_date')

        # バリデーション（簡易版）
        if not all([organization_name, organization_type_id, address,
                   phone_number, contact_person, contract_status_id, contract_start_date]):
            flash('必須項目を入力してください', 'error')
            return redirect(url_for('admin.organizations.edit_organization_form',
                                  databricks_group_id=databricks_group_id))

        # ③④ 元データ取得とデータスコープチェック
        logger.info('元データ取得開始')
        organization = db.session.query(Organization)\
            .join(OrganizationClosure,
                  Organization.organization_id == OrganizationClosure.subsidiary_organization_id)\
            .filter(OrganizationClosure.parent_organization_id == current_user.organization_id)\
            .filter(Organization.databricks_group_id == databricks_group_id)\
            .filter(Organization.delete_flag == 0)\
            .first()

        if not organization:
            logger.warning(f'組織が見つかりません: databricks_group_id={databricks_group_id}')
            flash('指定された組織が見つかりません', 'error')
            return redirect(url_for('admin.organizations.list_organizations'))

        logger.info(f'元データ取得成功: organization_id={organization.organization_id}')

        # ⑤ organization_master更新
        logger.info('organization_master更新開始')
        organization.organization_name = organization_name
        organization.organization_type_id = organization_type_id
        organization.address = address
        organization.phone_number = phone_number
        organization.fax_number = fax_number
        organization.contact_person = contact_person
        organization.contract_status_id = contract_status_id
        organization.contract_start_date = datetime.strptime(contract_start_date, '%Y-%m-%d').date()
        organization.contract_end_date = datetime.strptime(contract_end_date, '%Y-%m-%d').date() if contract_end_date else None
        organization.updater = current_user.user_id
        organization.update_date = datetime.now()

        db.session.flush()  # エラーチェック
        logger.info('organization_master更新成功')

        # ⑥ コミット
        db.session.commit()
        logger.info(f'組織更新コミット成功: organization_id={organization.organization_id}')

        # ⑦ 成功メッセージ
        flash('組織を更新しました', 'success')

        # ⑧ 一覧画面へリダイレクト
        return redirect(url_for('admin.organizations.list_organizations'))

    except Exception as e:
        db.session.rollback()
        logger.error(f'組織更新失敗: databricks_group_id={databricks_group_id}, error={str(e)}')
        flash('組織の更新に失敗しました', 'error')
        return redirect(url_for('admin.organizations.edit_organization_form',
                              databricks_group_id=databricks_group_id))
```

##### バリデーション

**実行タイミング:** 更新ボタンクリック直後（フロントサイド）

**バリデーションルール:** [UI仕様書](./ui-specification.md) の要素詳細 (7) 組織登録/更新モーダル > バリデーション を参照

##### 表示メッセージ

| メッセージID | 表示内容 | 表示タイミング | 表示場所 |
|-------------|---------|---------------|---------|
| - | 組織を更新しました | 更新成功時 | ステータスメッセージモーダル（成功） |
| - | 組織の更新に失敗しました | DB操作失敗時 | ステータスメッセージモーダル（エラー） |
| - | 指定された組織が見つかりません | 存在チェック時 | ステータスメッセージモーダル（エラー） |

#### ログ出力タイミング
DBクエリ実行の直前、直後に操作ログを出力する

---

### 組織参照

**トリガー:** (6.8) 参照ボタンクリック

#### 処理詳細（サーバーサイド）

**実装例:**
```python
@admin_organizations_bp.route('/<databricks_group_id>', methods=['GET'])
@require_permission('organization:read')
def view_organization(databricks_group_id):
    """
    組織参照画面表示

    フロー:
    1. 権限チェック（デコレーターで実施）
    2. 組織情報取得（データスコープ制限適用）
    3. データ存在チェック
    4. 参照モーダルレンダリング
    """
    try:
        # ① 権限チェック（デコレーターで実施済み）
        current_user = g.current_user

        logger.info(f'組織参照画面表示開始: user_id={current_user.user_id}, databricks_group_id={databricks_group_id}')

        # ② 組織情報取得（データスコープ制限適用）
        logger.info('組織情報取得開始')
        organization = db.session.query(Organization)\
            .join(OrganizationClosure,
                  Organization.organization_id == OrganizationClosure.subsidiary_organization_id)\
            .filter(OrganizationClosure.parent_organization_id == current_user.organization_id)\
            .filter(Organization.databricks_group_id == databricks_group_id)\
            .filter(Organization.delete_flag == 0)\
            .first()

        # ③ データ存在チェック
        if not organization:
            logger.warning(f'組織が見つかりません: databricks_group_id={databricks_group_id}')
            abort(404)

        logger.info(f'組織情報取得成功: organization_id={organization.organization_id}')

        # ④ 参照モーダルレンダリング
        return render_template(
            'admin/organizations/view.html',
            organization=organization
        )

    except Exception as e:
        logger.error(f'組織参照画面表示エラー: databricks_group_id={databricks_group_id}, error={str(e)}')
        abort(500)
```
#### ログ出力タイミング
DBクエリ実行の直前、直後に操作ログを出力する

---

### 組織削除

**トリガー:** (3.2) 削除ボタンクリック → (9) 削除確認モーダル → 削除ボタンクリック

#### 処理フロー

```mermaid
flowchart TD
    Start([削除ボタンクリック]) --> Confirm[削除確認ダイアログ表示<br>本当に削除してもよろしいですか？]
    Confirm --> CheckAuth{権限チェック}

    CheckAuth -->|権限OK| ConfirmResult{ユーザー確認}
    CheckAuth -->|権限なし| Error403[403エラー ※1]

    ConfirmResult -->|削除| GetOriginal[元データ取得<br>SELECT * FROM organization_master<br>WHERE databricks_group_id = :databricks_group_id]
    ConfirmResult -->|キャンセル| ValidEnd[処理中断]

    GetOriginal --> CheckDB1{DBクエリ結果}

    CheckDB1 -->|成功| CheckResult1{組織存在?}
    CheckDB1 -->|失敗| Error500[ステータスメッセージモーダル（エラー）]

    CheckResult1 -->|存在する| CheckAffiliatedOrg[傘下組織の存在チェック<br>SELECT * FROM organization_closure<br>WHERE parent_organization_id = :organization_id]
    CheckAffiliatedOrg --> CheckDB2{DBクエリ結果}

    CheckResult1 -->|存在しない| NotFoundError[エラー表示<br>指定された組織が見つかりません]
    NotFoundError --> ValidEnd

    CheckDB2 -->|成功| CheckResult2{傘下組織存在?}
    CheckDB2 -->|失敗| Error500

    CheckResult2 -->|存在しない| CheckAffiliatedUser[傘下ユーザーの存在チェック<br>SELECT * FROM user_master<br>WHERE organization_id = :organization_id]
    CheckResult2 -->|存在する| CheckOrgError[エラー表示<br>傘下の組織が存在するため削除できません]
    CheckOrgError --> ValidEnd

    CheckAffiliatedUser --> CheckDB3{DBクエリ結果}

    CheckDB3 -->|成功| CheckResult3{傘下ユーザー存在?}
    CheckDB3 -->|失敗| Error500

    CheckResult3 -->|存在しない| CheckAffiliatedDevice[傘下デバイスの存在チェック<br>SELECT * FROM device_master<br>WHERE organization_id = :organization_id]
    CheckResult3 -->|存在する| CheckUserError[エラー表示<br>傘下のユーザーが存在するため削除できません]
    CheckUserError --> ValidEnd

    CheckAffiliatedDevice --> CheckDB4{DBクエリ結果}

    CheckDB4 -->|成功| CheckResult4{傘下デバイス存在?}
    CheckDB4 -->|失敗| Error500

    CheckResult4 -->|存在しない| DeleteUC[UnitiyCatalog<br>organization_master<br>組織削除]
    CheckResult4 -->|存在する| CheckDeviceError[エラー表示<br>傘下のデバイスが存在するため削除できません]
    CheckDeviceError --> ValidEnd

    DeleteUC --> CheckUC{UnityCatalog<br>操作結果}

    CheckUC -->|成功| StartDBTx[OLTP DB<br>トランザクション開始]
    CheckUC -->|失敗| Error500

    StartDBTx --> DeleteDBMstr[OLTP DB<br>organization_master<br>組織削除]
    DeleteDBMstr --> CheckDBMstr{DB操作結果}

    CheckDBMstr -->|成功| DeleteDBClosure[OLTP DB<br>organization_closure<br>組織削除]
    CheckDBMstr -->|失敗| RollbackUC[UnityCatalog<br>organization_master<br>元データを復元]
    RollbackUC --> Error500

    DeleteDBClosure --> CheckDBClosure{DB操作結果}

    CheckDBClosure -->|成功| DeleteDbxGroup[Databricksグループ削除]
    CheckDBClosure -->|失敗| RollbackDBMstr[OLTP DB<br>organization_master<br>元データを復元]
    RollbackDBMstr --> RollbackUC

    DeleteDbxGroup --> DeleteDbxGroupResult{グループ削除結果}

    DeleteDbxGroupResult -->|成功| CommitDBTx[OLTP DB<br>コミット]
    DeleteDbxGroupResult -->|失敗| RollbackDBClosure[OLTP DB<br>organization_closure<br>元データを復元]
    RollbackDBClosure --> RollbackDBMstr

    CommitDBTx --> Redirect[一覧画面へリダイレクト<br>redirect url_for admin.list_organizations]
    Redirect --> Success[ステータスメッセージモーダル（成功）]

    ValidEnd --> End([処理完了])
    Error500 --> End
    Error403 --> End
    Success --> End
```

※1　403エラー発生時、ドロップダウン、テキストボックスに具体的なデータは表示せず、空で表示する。

##### 処理詳細（サーバーサイド）

**実装例:**
```python
from app.databricks_client import delete_databricks_group

@admin_organizations_bp.route('/delete', methods=['POST'])
@require_permission('organization:write')
def delete_organizations():
    """
    組織削除実行

    フロー:
    1. 権限チェック（デコレーターで実施）
    2. 削除対象のdatabricks_group_id取得
    3. 各組織に対して以下を実行:
       a. 元データ取得（データスコープチェック含む）
       b. 傘下組織の存在チェック
       c. 傘下ユーザーの存在チェック
       d. 傘下デバイスの存在チェック
       e. organization_master論理削除
       f. organization_closure物理削除
       g. Databricksグループ削除
    4. コミット
    5. 成功メッセージ表示
    6. 一覧画面へリダイレクト

    エラー時のロールバック:
    - organization_master更新失敗 → ロールバック
    - organization_closure削除失敗 → organization_master復元 + ロールバック
    """
    current_user = g.current_user

    try:
        # ② 削除対象のdatabricks_group_id取得
        databricks_group_ids = request.form.getlist('databricks_group_ids')

        if not databricks_group_ids:
            flash('削除する組織を選択してください', 'error')
            return redirect(url_for('admin.organizations.list_organizations'))

        logger.info(f'組織削除開始: user_id={current_user.user_id}, count={len(databricks_group_ids)}')

        deleted_count = 0

        # ③ 各組織に対して削除処理実行
        for databricks_group_id in databricks_group_ids:
            logger.info(f'組織削除処理開始: databricks_group_id={databricks_group_id}')

            # a. 元データ取得とデータスコープチェック
            logger.info('元データ取得開始')
            organization = db.session.query(Organization)\
                .join(OrganizationClosure,
                      Organization.organization_id == OrganizationClosure.subsidiary_organization_id)\
                .filter(OrganizationClosure.parent_organization_id == current_user.organization_id)\
                .filter(Organization.databricks_group_id == databricks_group_id)\
                .filter(Organization.delete_flag == 0)\
                .first()

            if not organization:
                logger.warning(f'組織が見つかりません: databricks_group_id={databricks_group_id}')
                continue

            logger.info(f'元データ取得成功: organization_id={organization.organization_id}')

            # b. 傘下組織の存在チェック
            logger.info('傘下組織の存在チェック開始')
            affiliated_org_count = OrganizationClosure.query.filter(
                OrganizationClosure.parent_organization_id == organization.organization_id,
                OrganizationClosure.subsidiary_organization_id != organization.organization_id
            ).count()

            if affiliated_org_count > 0:
                logger.warning(f'傘下組織が存在します: organization_id={organization.organization_id}, count={affiliated_org_count}')
                flash(f'組織「{organization.organization_name}」: 傘下の組織が存在するため削除できません', 'error')
                continue

            logger.info('傘下組織の存在チェック成功')

            # c. 傘下ユーザーの存在チェック
            logger.info('傘下ユーザーの存在チェック開始')
            from app.models import User
            affiliated_user_count = User.query.filter(
                User.organization_id == organization.organization_id,
                User.delete_flag == 0
            ).count()

            if affiliated_user_count > 0:
                logger.warning(f'傘下ユーザーが存在します: organization_id={organization.organization_id}, count={affiliated_user_count}')
                flash(f'組織「{organization.organization_name}」: 傘下のユーザーが存在するため削除できません', 'error')
                continue

            logger.info('傘下ユーザーの存在チェック成功')

            # d. 傘下デバイスの存在チェック
            logger.info('傘下デバイスの存在チェック開始')
            from app.models import Device
            affiliated_device_count = Device.query.filter(
                Device.organization_id == organization.organization_id,
                Device.delete_flag == 0
            ).count()

            if affiliated_device_count > 0:
                logger.warning(f'傘下デバイスが存在します: organization_id={organization.organization_id}, count={affiliated_device_count}')
                flash(f'組織「{organization.organization_name}」: 傘下のデバイスが存在するため削除できません', 'error')
                continue

            logger.info('傘下デバイスの存在チェック成功')

            # e. organization_master論理削除
            logger.info('organization_master論理削除開始')
            organization.delete_flag = 1
            organization.updater = current_user.user_id
            organization.update_date = datetime.now()
            db.session.flush()  # エラーチェック
            logger.info('organization_master論理削除成功')

            # f. organization_closure物理削除
            logger.info('organization_closure物理削除開始')
            closures = OrganizationClosure.query.filter_by(
                subsidiary_organization_id=organization.organization_id
            ).all()

            for closure in closures:
                db.session.delete(closure)

            db.session.flush()  # エラーチェック
            logger.info(f'organization_closure物理削除成功: count={len(closures)}')

            # g. Databricksグループ削除
            if organization.databricks_group_id:
                try:
                    delete_databricks_group(organization.databricks_group_id)
                    logger.info(f'Databricksグループ削除成功: group_id={organization.databricks_group_id}')
                except DatabricksAPIError as e:
                    # Databricks API失敗は警告ログのみで続行
                    logger.warning(f'Databricksグループ削除失敗: group_id={organization.databricks_group_id}, error={str(e)}')

            deleted_count += 1
            logger.info(f'組織削除処理完了: organization_id={organization.organization_id}')

        # ④ コミット
        db.session.commit()
        logger.info(f'組織削除コミット成功: deleted_count={deleted_count}')

        # ⑤ 成功メッセージ
        if deleted_count > 0:
            flash(f'{deleted_count}件の組織を削除しました', 'success')

        # ⑥ 一覧画面へリダイレクト
        return redirect(url_for('admin.organizations.list_organizations'))

    except Exception as e:
        db.session.rollback()
        logger.error(f'組織削除失敗: error={str(e)}')
        flash('組織の削除に失敗しました', 'error')
        return redirect(url_for('admin.organizations.list_organizations'))
```

#### 表示メッセージ

| メッセージID | 表示内容 | 表示タイミング | 表示場所 |
|-------------|---------|---------------|---------|
| - | 組織を削除しました | 削除成功時 | ステータスメッセージモーダル（成功） |
| - | 組織の削除に失敗しました | Databricks API失敗時、DB操作失敗時 | ステータスメッセージモーダル（エラー） |
| - | 指定された組織が見つかりません | 存在チェック時 | ステータスメッセージモーダル（エラー） |
| - | 傘下の組織が存在するため削除できません | 傘下組織の存在チェック時 | ステータスメッセージモーダル（エラー） |
| - | 傘下のユーザーが存在するため削除できません | 傘下ユーザーの存在チェック時 | ステータスメッセージモーダル（エラー） |
| - | 傘下のデバイスが存在するため削除できません | 傘下デバイスの存在チェック時 | ステータスメッセージモーダル（エラー） |

#### ログ出力タイミング
DBクエリ実行の直前、直後に操作ログを出力する

---

### CSVエクスポート

**トリガー:** (3.3) CSVエクスポートボタンクリック

##### 処理詳細（サーバーサイド）

**実装例:**
```python
@admin_bp.route('/organizations', methods=['GET'])
def list_organizations():
    # ... 初期表示と同じ検索処理 ...

    # CSVエクスポート処理
    if request.args.get('export') == 'csv':
        import csv
        from io import StringIO
        from flask import make_response

        # 検索条件に基づいてすべてのデータを取得（ページング制限なし）
        organizations = query.all()

        # CSV形式で出力
        si = StringIO()
        writer = csv.writer(si)

        # ヘッダー行
        writer.writerow([
            '組織ID',
            '組織名',
            '組織種別',
            '住所',
            '電話番号',
            'FAX番号',
            '担当者',
            '契約状態',
            '契約開始日',
            '契約終了日'
        ])

        # データ行
        for org in organizations:
            writer.writerow([
                org.organization_id,
                org.organization_name,
                org.organization_type.organization_type_name if org.organization_type else '',
                org.address,
                org.phone_number,
                org.fax_number or '',
                org.contact_person,
                org.contract_status.contract_status_name if org.contract_status else '',
                org.contract_start_date.strftime('%Y-%m-%d') if org.contract_start_date else '',
                org.contract_end_date.strftime('%Y-%m-%d') if org.contract_end_date else ''
            ])

        # レスポンス作成
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename=organizations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output.headers["Content-type"] = "text/csv; charset=utf-8"

        return output

    # 通常の画面表示
    return render_template('admin/organizations/list.html',
                          organizations=organizations,
                          total=total,
                          page=page,
                          per_page=per_page)
```

---

## 使用データベース詳細

### 使用テーブル一覧

| No | テーブル名 | 論理名 | 操作種別 | ワークフロー | 目的 | インデックス利用 |
|----|-----------|--------|---------|------------|------|----------------|
| 1 | organization_master | 組織マスタ | SELECT | 初期表示、検索 | 組織情報取得 | PRIMARY KEY (organization_id) |
| 2 | organization_master | 組織マスタ | INSERT | 組織登録 | 新規組織作成 | - |
| 3 | organization_master | 組織マスタ | UPDATE | 組織更新、組織削除 | 組織情報更新、論理削除 | - |
| 4 | organization_closure | 組織閉包テーブル | SELECT | 初期表示、検索 | データスコープ制限 | PRIMARY KEY (parent_organization_id, subsidiary_organization_id) |
| 5 | organization_closure | 組織閉包テーブル | INSERT | 組織登録 | 組織階層構造登録 | - |
| 6 | organization_closure | 組織閉包テーブル | UPDATE | 組織更新 | 組織階層構造更新 | - |
| 6 | organization_closure | 組織閉包テーブル | DELETE | 組織削除 | 組織階層構造物理削除 | - |
| 7 | organization_type_master | 組織種別マスタ | SELECT | 初期表示、組織登録画面、組織更新画面 | 組織種別選択肢取得 | - |
| 8 | contract_status_master | 契約状態マスタ | SELECT | 初期表示、組織登録画面、組織更新画面 | 契約状態選択肢取得 | - |

### インデックス最適化

**使用するインデックス:**
- organization_master.organization_id: PRIMARY KEY - 組織一意識別
- organization_closure.parent_organization_id: PRIMARY KEY - データスコープ制限高速化
- organization_closure.subsidiary_organization_id: PRIMARY KEY - 組織階層検索高速化

---

## トランザクション管理

### トランザクション開始・終了タイミング

**トランザクション開始:**
- ワークフロー: 組織登録/更新/削除
- 開始タイミング: バリデーション完了後、DB操作開始前
- 開始条件: バリデーションが成功

**トランザクション終了（コミット）:**
- 終了タイミング: すべてのDB操作とDatabricks API呼び出しが成功した後
- 終了条件:
  - **組織登録**: Databricks API POST成功 AND organization_master INSERT成功 AND organization_closure INSERT成功
  - **組織更新**: organization_master UPDATE成功
  - **組織削除**: organization_master UPDATE成功 organization_closure DELETE成功 Databricks API DELETE成功

**トランザクション終了（ロールバック）:**
- ロールバックタイミング: いずれかのDB操作またはDatabricks API呼び出しが失敗した時
- ロールバック対象:
  - **組織登録**: Databricksグループ POST、 organization_master INSERT、organization_closure INSERT
  - **組織更新**: organization_master UPDATE
  - **組織削除**: organization_master UPDATE、organization_closure DELETE
- ロールバック条件:
  - **組織登録**: organization_master INSERTエラー、organization_closure INSERTエラー
  - **組織更新**: organization_master UPDATEエラー
  - **組織削除**: organization_master UPDATEエラー、organization_closure DELETEエラー、Databricksグループ DELETE

---

## セキュリティ実装

### 認証・認可実装

**認証方式:**
- Databricksリバースプロキシヘッダ認証（`X-Forwarded-User`）

**認可ロジック:**
- システム保守者: すべての組織を管理可能
- 管理者: すべての組織を管理可能
- 販社ユーザー: 自社に紐づく、または自社の傘下組織の組織のみ管理可能
- サービス利用者: 組織管理画面へのアクセス不可

---

### 入力検証

**検証項目:**
- organization_name: 最大200文字、必須
- organization_type_id: 許可された値のみ、必須
- affiliated_organization_id: 存在する組織IDのみ、必須
- address: 最大500文字、必須
- phone_number: 電話番号形式、最大20文字、必須
- fax_number: 電話番号形式、最大20文字、任意
- contact_person: 最大20文字、必須
- contract_status_id: 許可された値のみ、必須
- contract_start_date: 日付形式、必須
- contract_end_date: 日付形式、任意、契約開始日以降
- SQLインジェクション対策: SQLAlchemy ORM使用（プリペアドステートメント）
- XSS対策: Jinja2自動エスケープ
- CSRF対策: Flask-WTF CSRF保護

### ログ出力ルール

**出力する情報:**
- リクエストID
- ユーザーID（操作者）
- 操作種別（組織登録、更新、削除等）
- 対象リソースID（organization_id）
- 処理結果（成功/失敗）
- エラー種別（バリデーションエラー、DBエラー等）

**出力しない情報:**
- 認証トークン
- 機密情報

---

## 関連ドキュメント

### 機能設計・仕様

- [機能概要 README](./README.md) - 画面の概要、データモデル、使用するテーブル一覧
- [UI仕様書](./ui-specification.md) - 画面レイアウト、UI要素の詳細仕様
- [機能要件定義書](../../02-requirements/functional-requirements.md) - FR-004-4（組織管理）
- [技術要件定義書](../../02-requirements/technical-requirements.md) - TR-SEC-001, TR-SEC-004, TR-SEC-005
- [非機能要件定義書](../../02-requirements/non-functional-requirements.md) - NFR-SEC-006, NFR-SEC-007

### アーキテクチャ設計

- [バックエンド設計](../../01-architecture/backend.md) - Flask/LDP設計、Blueprint構成
- [データベース設計](../../01-architecture/database.md) - テーブル定義、インデックス設計
- [インフラストラクチャ設計](../../01-architecture/infrastructure.md) - Databricks環境、Private Link

### 共通仕様

- [共通仕様書](../common/common-specification.md) - HTTPステータスコード、エラーコード、トランザクション管理
- [UI共通仕様書](../common/ui-common-specification.md) - すべての画面に共通するUI仕様

### 類似機能

- [デバイス管理機能](../devices/README.md) - 同様のCRUD画面構成
- [ユーザー管理機能](../users/README.md) - 同様のDatabricks連携（ワークスペースグループ）

---

**このワークフロー仕様書は、実装前に必ずレビューを受けてください。**

**最終更新日:** 2025-12-18
**作成者:** Claude Sonnet 4.5
