# アラート履歴画面 - ワークフロー仕様書

## 📑 目次

- [アラート履歴画面 - ワークフロー仕様書](#アラート履歴画面---ワークフロー仕様書)
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
      - [処理詳細](#処理詳細-2)
      - [UI状態](#ui状態-2)
    - [詳細表示](#詳細表示)
      - [処理フロー](#処理フロー-2)
      - [処理詳細（サーバーサイド）](#処理詳細サーバーサイド-2)
      - [ログ出力タイミング](#ログ出力タイミング-2)
  - [使用データベース詳細](#使用データベース詳細)
    - [使用テーブル一覧](#使用テーブル一覧)
    - [インデックス最適化](#インデックス最適化)
  - [セキュリティ実装](#セキュリティ実装)
    - [認証・認可実装](#認証認可実装)
    - [ログ出力ルール](#ログ出力ルール)
  - [関連ドキュメント](#関連ドキュメント)
    - [画面仕様](#画面仕様)
    - [アーキテクチャ設計](#アーキテクチャ設計)
    - [共通仕様](#共通仕様)

---

## 概要

このドキュメントは、アラート履歴画面のユーザー操作に対する処理フロー、バリデーション実行タイミング、データベース処理の詳細を記載します。

**このドキュメントの役割:**
- ✅ ユーザー操作のトリガー条件
- ✅ 処理フローの詳細（Flaskルート呼び出しシーケンス、フォーム送信、リダイレクト）
- ✅ バリデーション実行タイミング（いつチェックするか）
- ✅ エラーハンドリングフロー
- ✅ サーバーサイド処理詳細（SQL、変数、条件分岐、コード例）
- ✅ データベース利用詳細（テーブル操作、インデックス）
- ✅ セキュリティ実装詳細（認証、データスコープ制限、ログ出力）

**UI仕様書との役割分担:**
- **UI仕様書**: バリデーションルール定義（何をチェックするか）、UI要素の詳細仕様
- **ワークフロー仕様書**: バリデーション実行タイミング（いつどのようにチェックするか）、処理フロー、サーバーサイド実装詳細

**注:** UI要素の詳細やバリデーションルールは [UI仕様書](./ui-specification.md) を参照してください。

---

## 使用するFlaskルート一覧

この画面で使用するすべてのFlaskルート（エンドポイント）を記載します。

| No | ルート名 | エンドポイント | メソッド | 用途 | レスポンス形式 | 備考 |
|----|---------|---------------|---------|------|---------------|------|
| 1 | アラート履歴初期表示 | `/alert/alert-history` | GET | アラート履歴の初期表示・ページング | HTML | pageパラメータなし=初期表示、あり=ページング |
| 2 | アラート履歴検索 | `/alert/alert-history` | POST | アラート履歴検索実行 | HTML | 検索条件をCookieに格納 |
| 3 | アラート履歴参照画面 | `/alert/alert-history/<alert_history_uuid>` | GET | アラート履歴詳細情報表示 | HTML（モーダル） | - |

**注:**
- **レスポンス形式**:
  - `HTML`: Jinja2テンプレートをレンダリングして返す（`render_template()`）
  - `HTML（モーダル）`: モーダル内容のみのHTMLフラグメントを返す
- **Flask Blueprint**: `alert_bp` として実装

---

## ルート呼び出しマッピング

| ユーザー操作 | トリガー | 呼び出すルート | パラメータ | レスポンス | エラー時の挙動 |
|-------------|----------|--------------|------------|-----------|---------------|
| 画面初期表示 | URL直接アクセス | `GET /alert/alert-history` | なし | HTML（アラート履歴一覧画面） | エラーページ表示 |
| 検索ボタン押下 | フォーム送信 | `POST /alert/alert-history` | `start_datetime, end_datetime, device_name, device_location, alert_name, alert_level_id, alert_status_id, sort_by, order` | HTML（検索結果画面） | エラーメッセージ表示 |
| ページボタン押下 | リンククリック | `GET /alert/alert-history` | `page` | HTML（検索結果画面） | エラーページ表示 |
| 参照ボタン押下 | ボタンクリック | `GET /alert/alert-history/<alert_history_uuid>` | alert_history_uuid | HTML（参照モーダル） | 404エラーページ表示 |

---

## ワークフロー一覧

### 初期表示

**トリガー:** URL直接アクセス時（ユーザーが `/alert/alert-history` にアクセスしたとき）

**前提条件:**
- ユーザーがログイン済み（Databricks認証完了）
- 適切な権限を持っている

#### 処理フロー

```mermaid
flowchart TD
    Start([GET /alert/alert-history]) --> Auth[認証チェック<br>Databricksリバースプロキシヘッダ確認]
    Auth --> CheckAuth{認証済み?}
    CheckAuth -->|未認証| LoginRedirect[ログイン画面へリダイレクト]

    CheckAuth -->|認証OK| CheckPage{request.args に<br>'page' パラメータあり?}

    CheckPage -->|なし<br>初期表示| ClearCookie[Cookie検索条件をクリア<br>response.delete_cookie]
    CheckPage -->|あり<br>ページング| GetCookie[Cookieから検索条件取得<br>request.cookies.get]

    ClearCookie --> InitParams[検索条件を初期化<br>page=1, sort_by=alert_occurrence_datetime, order=dsc]
    GetCookie --> OverridePage[Cookie検索条件に<br>pageパラメータを上書き<br>page=request.args.get'page']

    InitParams --> Scope[データスコープ制限適用<br>organization_closureテーブルから下位組織IDリスト取得]
    OverridePage --> Scope

    Scope --> Count[検索結果件数取得DBクエリ実行]
    Count --> CheckDB0{DBクエリ結果}

    CheckDB0 -->|成功| Query[検索結果取得DBクエリ実行]
    CheckDB0 -->|失敗| Error500[500エラーページ表示]

    Query --> CheckDB{DBクエリ結果}

    CheckDB -->|成功| CheckInitial{初期表示?<br>page not in args}
    CheckDB -->|失敗| Error500

    CheckInitial -->|Yes 初期表示| SaveCookie[レンダリング直前<br>Cookieに検索条件を格納<br>response.set_cookie<br>max_age=86400]
    CheckInitial -->|No ページング| Template[Jinja2テンプレートレンダリング<br>render_template<br>alert/alert-history/list.html]

    SaveCookie --> Template
    Template --> Response[HTMLレスポンス返却]

    LoginRedirect --> End([処理完了])
    Response --> End
    Error500 --> End
```

#### Flaskルート

| ルート | エンドポイント | 詳細 |
|-------|---------------|------|
| アラート履歴一覧表示 | `GET /alert/alert-history` | クエリパラメータ: `page` |

#### バリデーション

**実行タイミング:** なし（初期表示のため、デフォルト値を使用）

**データスコープ制限:**
- **フィルタリングロジックは全ユーザーで共通、実質的なアクセス可能範囲に差分あり**
- システム保守者・管理者: すべてのユーザーにアクセス可能
- 販社ユーザー・サービス利用者: ログインユーザーの `organization_id` に紐づく全子組織でフィルタリング

#### 処理詳細（サーバーサイド）

**① 認証・認可チェック**

リバースプロキシヘッダから認証情報を取得し、権限を確認します。

**処理内容:**
- ヘッダ `X-Forwarded-User` からユーザーIDを取得
- データベースから現在ユーザー情報を取得（ユーザー種別、組織ID）
- 組織に応じてデータスコープを決定

**変数・パラメータ:**
- `current_user_id`: string - リバースプロキシヘッダから取得したユーザーID
- `current_user`: User - データベースから取得したユーザーオブジェクト
- `user_type_id`: int - ユーザー種別ID（user_type_masterへの外部キー）
- `organization_id`: string - データスコープ制限用の組織ID

**実装例:**
```python
from flask import request, abort, g
from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('X-Forwarded-User')
        if not user_id:
            abort(401)

        user = User.query.filter_by(user_id=user_id, delete_flag=0).first()
        if not user:
            abort(403)

        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function
```

**② クエリパラメータ取得**

デフォルトの検索条件を設定します。

**処理内容:**
- `start_datetime`: 現在日時から7日前の00:00
- `end_datetime`: 現在日時の23:59
- `page`: 1
- `per_page`: 25（固定）
- `sort_by`: alert_occurrence_datetime
- `order`: desc（降順、最新のアラートが上）

```python
from datetime import datetime, timedelta

# デフォルト値を設定（設定ファイルから取得）
now = datetime.now()
default_start = (now - timedelta(days=INIT_START_DATETIME)).replace(hour=0, minute=0, second=0)
default_end = now.replace(hour=23, minute=59, second=59)

start_datetime = request.args.get('start_datetime', default_start.strftime('%Y/%m/%d %H:%M'))
end_datetime = request.args.get('end_datetime', default_end.strftime('%Y/%m/%d %H:%M'))

page = request.args.get('page', 1, type=int)
per_page = ITEM_PER_PAGE
sort_by = request.args.get('sort_by', 'alert_occurrence_datetime')
order = request.args.get('order', 'desc')
```

**③ データスコープ制限の適用**

組織階層に基づいてデータスコープ制限を適用します。

**処理内容:**
- **全ユーザー共通**: 組織階層（`organization_closure`）でフィルタ
  - ユーザーの `organization_id` を親組織IDとして検索
  - 下位組織リスト（`subsidiary_organization_id`）を取得
  - そのリストに該当する組織のデータのみアクセス可能
  - **ロールによる条件分岐は一切行わない**

**注**: システム保守者・管理者が全データにアクセスできるのは、ルート組織に所属しているため

**変数・パラメータ:**
- `accessible_org_ids`: list - アクセス可能な組織IDリスト

**実装例:**
```python
def apply_data_scope_filter(query, current_user):
    # organization_closure テーブルから下位組織リストを取得（全ユーザー共通）
    accessible_org_ids = db.session.query(
        OrganizationClosure.subsidiary_organization_id
    ).filter(
        OrganizationClosure.parent_organization_id == current_user.organization_id
    ).all()

    # 下位組織IDのリストを抽出
    org_ids = [org_id[0] for org_id in accessible_org_ids]

    if not org_ids:
        # アクセス可能な組織がない場合は空の結果を返す
        # （通常は発生しない - 最低でも自組織は含まれる）
        return query.filter(User.organization_id.in_([]))

    # 組織IDリストでフィルタリング
    return query.filter(User.organization_id.in_(org_ids))
```

**④ データベースクエリ実行**

アラート履歴データを取得します。

**使用テーブル:** alert_history, alert_status_master, alert_setting_master, alert_level_master, device_master

**SQL詳細:**
- 検索結果件数取得DBクエリ
```sql
SELECT
  COUNT(alert_history_id) AS data_count
FROM
  alert_history ah
LEFT JOIN alert_setting_master am
  ON ah.alert_id = am.alert_id
  AND am.delete_flag = FALSE
LEFT JOIN device_master dm
  ON am.device_id = dm.device_id
  AND dm.delete_flag = FALSE
WHERE
  ah.alert_occurrence_datetime BETWEEN :start_datetime AND :end_datetime
  AND ah.delete_flag = FALSE
  AND dm.organization_id IN (:accessible_org_ids)
```

- 検索結果取得DBクエリ
```sql
SELECT
  ah.alert_occurrence_datetime,
  dm.device_name,
  dm.device_location,
  am.alert_name,
  al.alert_level_id,
  al.alert_level_name,
  asm.alert_status_id,
  asm.alert_status_name
FROM
  alert_history ah
LEFT JOIN alert_status_master asm
  ON ah.alert_status_id = asm.alert_status_id
  AND asm.delete_flag = FALSE
LEFT JOIN alert_setting_master am
  ON ah.alert_id = am.alert_id
  AND am.delete_flag = FALSE
LEFT JOIN alert_level_master al
  ON am.alert_level_id = al.alert_level_id
  AND al.delete_flag = FALSE
LEFT JOIN device_master dm
  ON am.device_id = dm.device_id
  AND dm.delete_flag = FALSE
WHERE
  ah.alert_occurrence_datetime BETWEEN :start_datetime AND :end_datetime
  AND ah.delete_flag = FALSE
  AND dm.organization_id IN (:accessible_org_ids)
ORDER BY
  ah.alert_occurrence_datetime DESC,
  ah.alert_history_id DESC -- 第二ソートキー
LIMIT :item_per_page OFFSET 0
```

**実装例:**
```python
offset = (page - 1) * per_page

# ベースクエリ
query = AlertHistory.query.filter_by(delete_flag=0)

# データスコープ制限適用
query = apply_data_scope_filter(query, g.current_user)

# ソート適用
if order == 'asc':
    query = query.order_by(getattr(AlertHistory, sort_by).asc())
else:
    query = query.order_by(getattr(AlertHistory, sort_by).desc())

# ページング適用
alert_histories = query.limit(per_page).offset(offset).all()
total = query.count()
```

**⑤ HTMLレンダリング**

Jinja2テンプレートをレンダリングしてHTMLレスポンスを返却します。  
検索条件欄に初期値を設定します。

**実装例:**
```python
return render_template('alert/alert-history/list.html',
                      alert_histories=alert_histories,
                      total=total,
                      page=page,
                      per_page=per_page,
                      sort_by=sort_by,
                      order=order,
                      search_params={
                          'start_datetime': start_datetime,
                          'end_datetime': end_datetime,
                          'device_name': device_name,
                          'device_location': device_location,
                          'alert_name': alert_name,
                          'alert_level_id': alert_level_id,
                          'alert_level_name': alert_level_name,
                          'alert_status_id': alert_status_id,
                          'alert_status_name': alert_status_name
                      })
```

**初期表示とページングの実装例**
```python
@alert_bp.route('/alert/alert-history', methods=['GET'])
@require_auth
def alert_histories_list():
    """初期表示・ページング（統合）"""

    # 初期表示 vs ページング判定
    if 'page' not in request.args:
        # 初期表示: デフォルト値
        search_params = {
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'device_name': '',
            'device_location': '',
            'alert_name': '',
            'alert_level_id': None,
            'alert_level_name': 'すべて',
            'alert_status_id': None,
            'alert_status_name': 'すべて'
        }
        save_cookie = True
    else:
        # ページング: Cookieから取得
        cookie_data = request.cookies.get('user_search_params')
        if cookie_data:
            search_params = json.loads(cookie_data)
        else:
            search_params = get_default_search_params()

        search_params['page'] = request.args.get('page', 1, type=int)
        save_cookie = False

    # データスコープ制限適用
    accessible_org_ids = get_accessible_organizations(g.current_user.organization_id)

    # DB検索実行
    alert_histories, total = search_alert_histories(search_params, accessible_org_ids)

    # レンダリング
    response = make_response(render_template(
        'alert/alert-history/list.html',
        alert_histories=alert_histories,
        total=total,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        order=order,
        search_params=search_params
    ))

    # 初期表示時のみCookie格納
    if save_cookie:
        response.set_cookie(
            'alert_history_search_params',
            json.dumps(search_params),
            max_age=86400,  # 24時間
            httponly=True,
            samesite='Lax'
        )

    return response
```

#### 表示メッセージ

| メッセージID | 表示内容 | 表示タイミング | 表示場所 |
|-------------|---------|---------------|---------|
| ERR_001 | データの取得に失敗しました | DBクエリ失敗時 | エラーページ |

#### エラーハンドリング

| HTTPステータス | エラー種別 | 処理内容 | 表示内容 |
|--------------|-----------|---------|---------|
| 401 | 認証エラー | ログイン画面へリダイレクト | - |
| 500 | データベースエラー | 500エラーページ表示 | データの取得に失敗しました |

#### ログ出力タイミング
DBクエリ実行の直前、直後に操作ログを出力する

#### 検索条件の保持方法
Cookieに検索条件を保持する

#### UI状態

- 検索条件: デフォルト値（期間は直近7日間）
- テーブル: アラート履歴一覧データ表示（最新順）
- ページネーション: 1ページ目を選択状態

---

### 検索・絞り込み

**トリガー:** (2.10) 検索ボタンクリック（フォーム送信）

**前提条件:**
- 検索条件が入力されている（空でも可）

#### 処理フロー

```mermaid
flowchart TD
    Start([検索ボタンクリック]) --> ClearCookie[Cookieの検索条件をクリア]
    ClearCookie --> Convert[検索条件をクエリパラメータに変換<br>page: 1（リセット）]
    Convert --> Scope[データスコープ制限を適用]
    Scope -->  Count[検索結果件数取得DBクエリ実行<br>検索条件を適用]
    Count --> CheckDB0{DBクエリ結果}

    CheckDB0 -->|成功|Query[検索結果DBクエリ実行<br>検索条件を適用]
    CheckDB0 -->|失敗| Error500[500エラーページ表示]

    Query --> CheckDB{DBクエリ結果}

    CheckDB -->|成功| Template[Jinja2テンプレートレンダリング]
    Template --> PutParams[Cookieに検索条件を格納<br>max_age=86400]
    PutParams --> Response[HTMLレスポンス返却]

    CheckDB -->|失敗| Error500

    Response --> 処理完了
    Error500 --> 処理完了
```

#### 処理詳細（サーバーサイド）

**検索クエリ実行**
**使用テーブル:** alert_history, alert_status_master, alert_setting_master, alert_level_master, device_master

**SQL詳細:**
- 検索結果件数取得DBクエリ
```sql
SELECT
  COUNT(alert_history_id) AS data_count
FROM
  alert_history ah
LEFT JOIN alert_status_master asm
  ON ah.alert_status_id = asm.alert_status_id
  AND asm.delete_flag = FALSE
LEFT JOIN alert_setting_master am
  ON ah.alert_id = am.alert_id
  AND am.delete_flag = FALSE
LEFT JOIN alert_level_master al
  ON am.alert_level_id = al.alert_level_id
  AND al.delete_flag = FALSE
LEFT JOIN device_master dm
  ON am.device_id = dm.device_id
  AND dm.delete_flag = FALSE
WHERE
  ah.delete_flag = FALSE
  AND dm.organization_id IN (:accessible_org_ids)
  AND CASE WHEN :start_datetime IS NULL OR :end_datetime IS NULL THEN TRUE ELSE alert_occurrence_datetime BETWEEN :start_datetime AND :end_datetime END
  AND CASE WHEN :device_name IS NULL THEN TRUE ELSE dm.device_name LIKE CONCAT('%', :device_name, '%') END
  AND CASE WHEN :device_location IS NULL THEN TRUE ELSE dm.device_location LIKE CONCAT('%', :device_location, '%') END
  AND CASE WHEN :alert_name IS NULL THEN TRUE ELSE am.alert_name LIKE CONCAT('%', :alert_name, '%') END
  AND CASE WHEN :alert_level_id IS NULL THEN TRUE ELSE al.alert_level_id = :alert_level_id END
  AND CASE WHEN :alert_status_id IS NULL THEN TRUE ELSE asm.alert_status_id = :alert_status_id END
```

- 検索結果取得DBクエリ
```sql
SELECT
  ah.alert_occurrence_datetime,
  dm.device_name,
  dm.device_location,
  am.alert_name,
  al.alert_level_id,
  al.alert_level_name,
  asm.alert_status_id,
  asm.alert_status_name
FROM
  alert_history ah
LEFT JOIN alert_status_master asm
  ON ah.alert_status_id = asm.alert_status_id
  AND asm.delete_flag = FALSE
LEFT JOIN alert_setting_master am
  ON ah.alert_id = am.alert_id
  AND am.delete_flag = FALSE
LEFT JOIN alert_level_master al
  ON am.alert_level_id = al.alert_level_id
  AND al.delete_flag = FALSE
LEFT JOIN device_master dm
  ON am.device_id = dm.device_id
  AND dm.delete_flag = FALSE
WHERE
  ah.delete_flag = FALSE
  AND dm.organization_id IN (:accessible_org_ids)
  AND CASE WHEN :start_datetime IS NULL OR :end_datetime IS NULL THEN TRUE ELSE alert_occurrence_datetime BETWEEN :start_datetime AND :end_datetime END
  AND CASE WHEN :device_name IS NULL THEN TRUE ELSE dm.device_name LIKE CONCAT('%', :device_name, '%') END
  AND CASE WHEN :device_location IS NULL THEN TRUE ELSE dm.device_location LIKE CONCAT('%', :device_location, '%') END
  AND CASE WHEN :alert_name IS NULL THEN TRUE ELSE am.alert_name LIKE CONCAT('%', :alert_name, '%') END
  AND CASE WHEN :alert_level_id IS NULL THEN TRUE ELSE al.alert_level_id = :alert_level_id END
  AND CASE WHEN :alert_status_id IS NULL THEN TRUE ELSE asm.alert_status_id = :alert_status_id END
ORDER BY
  {sort_by} {order},
  ah.alert_history_id {order} -- 第二ソートキー
LIMIT :item_per_page OFFSET (:page -1) * :item_per_page
```

#### 表示メッセージ

| メッセージID | 表示内容 | 表示タイミング | 表示場所 |
|-------------|---------|---------------|---------|
| ERR_001 | データの取得に失敗しました | DBクエリ失敗時 | エラーページ |

#### エラーハンドリング

| HTTPステータス | エラー種別 | 処理内容 | 表示内容 |
|--------------|-----------|---------|---------|
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

**トリガー:**（5）データテーブルのソート可能カラムのヘッダをクリック

#### 処理詳細
データテーブルのヘッダをクリックすることで、ページ内で閉じたソートを行う。
詳細は[共通仕様書](../../common/common-specification.md)参照のこと

---

### ページング

**トリガー:** (5.8) ページネーションのページ番号ボタンクリック

#### 処理詳細
ページネーションのページ番号を選択することで、選択されたページ番号に対応するデータをデータテーブルに表示する。
具体的な処理は[初期表示](#初期表示)の処理と同様とする。

#### UI状態

- 検索条件: 保持
- ソート条件: 保持
- テーブル: 選択ページのデータ表示
- ページネーション: 選択ページをアクティブ状態

---

### 詳細表示

**トリガー:** (5.7) 参照ボタンクリック

**前提条件:**
- データスコープ制限内のアラート履歴である

#### 処理フロー

```mermaid
flowchart TD
    Start([参照ボタンクリック]) --> DataScope[データスコープチェック]
    DataScope --> GetAlertHistory[アラート履歴詳細情報取得]
    GetAlertHistory --> CheckDB{DB取得<br>成功?}

    CheckDB -->|成功| Modal[詳細モーダル表示<br>render_template<br>'alert/alert-history/detail_modal.html']
    Modal --> End([処理完了])

    CheckDB -->|失敗| Error404[404エラーページ表示]
    Error404 --> End
```

#### 処理詳細（サーバーサイド）

**実装例:**
```python
@alert_bp.route('/alert/alert-history/<alert_history_uuid>', methods=['GET'])
@require_auth
def view_alert_history_detail(alert_history_uuid):
    try:
        # アラート履歴詳細情報取得（データスコープチェック含む）
        query = AlertHistory.query.options(
            joinedload(AlertHistory.alert_status)
        ).filter_by(alert_history_uuid=alert_history_uuid, delete_flag=0)

        query = apply_data_scope_filter(query, g.current_user)
        alert_history = query.first_or_404()

        return render_template('alert/alert-history/detail_modal.html', alert_history=alert_history)

    except Exception as e:
        logger.error(f"アラート履歴詳細表示に失敗: {str(e)}")
        abort(404)
```

#### ログ出力タイミング
DBクエリ実行の直前、直後に操作ログを出力する

---

## 使用データベース詳細

### 使用テーブル一覧

| No | テーブル名 | 論理名 | 操作種別 | ワークフロー | 目的 | インデックス利用 |
|----|-----------|--------|---------|------------|------|----------------|
| 1 | alert_history | アラート履歴 | SELECT | 全ワークフロー | アラート履歴データ取得 | PRIMARY KEY (alert_history_id) |
| 2 | alert_status_master | アラートステータスマスタ | SELECT | 全ワークフロー | アラートステータスの参照 | PRIMARY KEY (alert_status_id) |
| 3 | alert_setting_master | アラート設定マスタ | SELECT | 全ワークフロー | アラート名・条件の参照 | PRIMARY KEY (alert_id) |
| 4 | alert_level_master | アラートレベルマスタ | SELECT | 全ワークフロー | アラートレベルの参照 | PRIMARY KEY (alert_level_id) |
| 5 | device_master | デバイスマスタ | SELECT | 全ワークフロー | デバイス名・設置場所の参照 | PRIMARY KEY (device_id) |
| 6 | organization_closure | 組織閉包テーブル | SELECT | 全ワークフロー | データスコープ制限（下位組織取得） | PRIMARY KEY (parent_organization_id, subsidiary_organization_id) |
| 7 | user_master | ユーザーマスタ | SELECT | 認証チェック | ユーザー情報・権限取得 | PRIMARY KEY (user_id) |

### インデックス最適化

**使用するインデックス:**
- alert_history.alert_history_id: PRIMARY KEY - アラート履歴一意識別
- alert_status_master.alert_status_id: PRIMARY KEY - アラートステータス一意識別

---

## セキュリティ実装

### 認証・認可実装

**認証方式:**
- Databricksリバースプロキシヘッダ認証（`X-Forwarded-User`）

**認可ロジック:**

組織階層に基づいて、ユーザーがアクセスできるデータを制限します。

**処理内容:**
- **全ユーザー共通**: 組織階層（`organization_closure`）でフィルタ
  - ユーザーの `organization_id` を親組織IDとして検索
  - 下位組織リスト（`subsidiary_organization_id`）を取得
  - そのリストに該当する組織のデータのみアクセス可能
  - **ロールによる条件分岐は一切行わない**

**注**: システム保守者・管理者が全データにアクセスできるのは、
ルート組織（すべての組織を子組織に持つ）に所属しているため

**実装例:**
```python
def apply_data_scope_filter(query, current_user):
    """組織階層に基づいたデータスコープ制限を適用

    すべてのユーザーに対して同じフィルタリングロジックを適用。
    ロールによる条件分岐は一切行わない。

    システム保守者・管理者が全データにアクセスできるのは、
    ルート組織に所属しており、すべての組織がその下位組織として
    登録されているため。
    """
    # organization_closure テーブルから下位組織リストを取得（全ユーザー共通）
    accessible_org_ids = db.session.query(
        OrganizationClosure.subsidiary_organization_id
    ).filter(
        OrganizationClosure.parent_organization_id == current_user.organization_id
    ).all()

    # 下位組織IDのリストを抽出
    org_ids = [org_id[0] for org_id in accessible_org_ids]

    if not org_ids:
        # アクセス可能な組織がない場合は空の結果を返す
        return query.filter(User.organization_id.in_([]))

    # 組織IDリストでフィルタリング
    return query.filter(User.organization_id.in_(org_ids))

# 使用例
@alert_bp.route('/alert/alert-history', methods=['GET'])
@require_auth
def list_alert_histories():
    query = AlertHistory.query.filter_by(delete_flag=0)

    # データスコープ制限適用
    query = apply_data_scope_filter(query, g.current_user)

    alert_histories = query.all()
    return render_template('alert/alert-history/list.html', alert_histories=alert_histories)
```

### ログ出力ルール

**出力する情報:**
- リクエストID
- ユーザーID（操作者）
- 操作種別（一覧表示、詳細表示）
- 対象リソースID（alert-history_uuid）
- 処理結果（成功/失敗）
- エラー種別（DBエラー）
- タイムスタンプ（UTC）

**出力しない情報（機密情報）:**
- 認証トークン
- 機密情報

---

## 関連ドキュメント

### 画面仕様
- [機能概要 README](./README.md) - 画面の概要、データモデル、使用するテーブル一覧
- [UI仕様書](./ui-specification.md) - UI要素の詳細、バリデーションルール定義

### アーキテクチャ設計
- [バックエンド設計](../../01-architecture/backend.md) - Flask/LDP設計、Blueprint構成
- [データベース設計](../../01-architecture/database.md) - テーブル定義、インデックス設計

### 共通仕様
- [共通仕様書](../common/common-specification.md) - HTTPステータスコード、エラーコード、トランザクション管理、セキュリティ等
- [UI共通仕様書](../common/ui-common-specification.md) - すべての画面に共通するUI仕様

---

**このワークフロー仕様書は、実装前に必ずレビューを受けてください。**
