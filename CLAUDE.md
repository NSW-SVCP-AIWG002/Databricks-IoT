<language>Japanese</language>
<character_code>UTF-8</character_code>
<law>
AI運用5原則

第1原則： AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告し、y/nでユーザー確認を取り、yが返るまで一切の実行を停止する。

第2原則： AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る。

第3原則： AIはツールであり決定権は常にユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。

第4原則： AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。

第5原則： AIは全てのチャットの冒頭にこの5原則を逐語的に必ず画面出力してから対応する。
</law>

<every_chat>
[AI運用5原則]

[main_output]

#[n] times. # n = increment each chat, end line, etc(#1, #2...)
</every_chat>





# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## プロジェクト概要

Databricks IoTシステム - IoTデバイスからのセンサーデータを収集・分析・可視化するWebアプリケーション

---

## 技術スタック

### バックエンド
- **Webフレームワーク**: Flask + Jinja2（SSR）
- **認証基盤**: Azure Easy Auth認証（Entra ID統合）
- **デプロイ環境**: Azure App Service

### データベース
| 種別               | 用途                                   | 技術                                    |
| ------------------ | -------------------------------------- | --------------------------------------- |
| OLTP DB            | マスタデータ管理、トランザクション処理 | Azure Database for MySQL 8.0 (utf8mb4)  |
| デバイスデータ用DB | センサーデータ管理                     | Unity Catalog (Delta Lake) on ADLS Gen2 |

### フロントエンド
- **HTML5** + **CSS3**（カスタムプロパティ）
- **BEM命名規則**: Block__Element--Modifier
- **JavaScript**: バニラJS（ライブラリなし）
- UIライブラリ不使用（Bootstrap、Tailwind等は使用しない）

---

## データベース設計方針

### OLTP DB (MySQL)
- 第3正規形まで正規化
- 論理削除（delete_flag）を使用、物理削除は行わない
- 監査証跡: create_date, creator, update_date, modifier を全テーブルに設定
- 外部キー制約でデータ整合性を保持

### Unity Catalog (Delta Lake)
- **メダリオンアーキテクチャ**: Bronze → Silver → Gold
- データ保持期間: ブロンズ層7日、シルバー層5年、ゴールド層10年
- 命名規則: `bronze_*`, `silver_*`, `gold_*`, `*_view`

---

## 認証・認可

### ロール定義
| ロール               | 説明                         |
| -------------------- | ---------------------------- |
| system_admin         | システム保守者（最上位権限） |
| management_admin     | 管理者                       |
| sales_company_user   | 販社ユーザー                 |
| service_company_user | サービス利用者               |

### データアクセス制御
- 組織閉包テーブル（organization_closure）でユーザーのデータアクセス範囲を制限
- ユーザーは所属組織と配下組織のデータのみアクセス可能

---

## コーディング規約

### Flask実装
```python
# バリデーションエラー
if not form.validate_on_submit():
    return render_template('xxx/form.html', form=form), 422

# 権限チェックデコレータ
@require_role('system_admin', 'management_admin')
def create_user():
    pass

# トランザクション管理
try:
    db.session.add(entity)
    db.session.commit()
except IntegrityError:
    db.session.rollback()
    # エラー処理
```

### CSS変数（主要なもの）
```css
/* カラー */
--color-primary: #2272B4;
--color-danger: #F44336;
--color-success: #28A745;

/* スペーシング（8pxベース） */
--spacing-2: 8px;
--spacing-4: 16px;
--spacing-6: 24px;

/* フォント */
--font-family-base: 'メイリオ', 'Meiryo', sans-serif;
--font-size-base: 14px;
```

### BEM命名例
```html
<button class="button button--primary">
  <span class="button__text">登録</span>
</button>
```

---

## HTTPステータスコード

| コード | 使用場面         | Flask実装                            |
| ------ | ---------------- | ------------------------------------ |
| 200    | 正常処理         | `render_template()`                  |
| 302    | リダイレクト     | `redirect()`                         |
| 400    | パラメータエラー | メッセージモーダル表示               |
| 403    | 権限不足         | メッセージモーダル表示               |
| 404    | リソース未検出   | メッセージモーダル表示               |
| 500    | サーバーエラー   | `render_template('errors/500.html')` |

---

## ファイル構成

### 処理フロー

```
リクエスト → middleware.py（認証） → views（ルーティング） → forms（バリデーション）
  → services（ビジネスロジック・CRUD） → models（DB操作） → DB
```

### ページネーション・ソート・検索の責務分担

| 機能             | サーバー側（Flask）                | クライアント側（JS）                  |
| ---------------- | ---------------------------------- | ------------------------------------- |
| ページネーション | データ取得・ページ計算             | UI描画・ページ遷移リクエスト発行      |
| 全件ソート       | 検索フォームのソート条件でDB問合せ | -                                     |
| 部分ソート       | -                                  | 表示中ページ内のソート（sort.js）     |
| 検索条件保持     | -                                  | sessionStorageで保存・復元（main.js） |

### ディレクトリ構成

```
src/
├── __init__.py                    # 空ファイル（srcはコンテナディレクトリ）
└── iot_app/                       # アプリケーションパッケージ（トップレベル）
    ├── __init__.py                # Flaskアプリケーションファクトリ（create_app）、db = SQLAlchemy()
    ├── config.py                  # 環境設定（Flask, MySQL, Databricks接続情報）
    │
    ├── auth/                      # 認証モジュール
    │   ├── __init__.py
    │   ├── factory.py             # AuthProvider生成（現状Azure固定、将来の拡張点）
    │   ├── middleware.py          # before_request認証フック（認証除外パス判定、セッション同期、トークン確保）
    │   ├── routes.py              # /auth/logout 等の認証関連ルート
    │   ├── services.py            # 認証関連データアクセス（ユーザー情報取得・セッション管理）
    │   ├── token_exchange.py      # IdP JWT → Databricksアクセストークン交換
    │   ├── exceptions.py          # 認証例外クラス定義（AuthError, TokenExchangeError等）
    │   └── providers/
    │       ├── __init__.py
    │       ├── base.py            # AuthProvider抽象基底クラス、UserInfo型定義
    │       ├── azure_easy_auth.py # Azure Easy Auth実装（X-MS-*ヘッダーからユーザー情報・JWT取得）
    │       └── dev.py             # ローカル開発用（DEV_AUTH_EMAIL / DEV_DATABRICKS_TOKEN使用）
    │
    ├── common/                    # 共通モジュール
    │   ├── __init__.py
    │   ├── exceptions.py          # 共通例外クラス定義
    │   ├── error_handlers.py      # 全エラーハンドラー登録（400/403/404→モーダル、500→エラーページ）
    │   └── logger.py              # AppLoggerAdapter（自動コンテキスト付与・マスキング）
    │
    ├── db/                        # データベース接続
    │   ├── __init__.py
    │   └── unity_catalog_connector.py # Unity Catalog接続（databricks-sql-connector、g.current_user.databricks_token使用）
    │
    ├── models/                    # SQLAlchemy ORMモデル（テーブル定義）
    │   ├── __init__.py
    │   ├── device.py              # device_master, device_type_master
    │   ├── user.py                # user_master, user_type_master
    │   ├── organization.py        # organization_master, organization_type_master, organization_closure
    │   ├── alert.py               # alert_setting_master, alert_level_master, alert_history, alert_status_master
    │   ├── notification.py        # mail_history, mail_type_master
    │   ├── device_stock.py        # device_stock_info_master, stock_status_master
    │   ├── contract.py            # contract_status_master
    │   ├── region.py              # region_master
    │   ├── language.py            # language_master
    │   ├── measurement.py         # measurement_item_master
    │   ├── sort_item.py           # sort_item_master
    │   └── device_status.py       # device_status_data
    │
    ├── forms/                     # Flask-WTFフォーム定義（入力バリデーション・CSRF保護）
    │   ├── __init__.py
    │   ├── device.py              # デバイス登録・更新フォーム
    │   ├── user.py                # ユーザー登録・更新フォーム
    │   ├── organization.py        # 組織登録・更新フォーム
    │   ├── alert_setting.py       # アラート設定登録・更新フォーム
    │   ├── device_stock.py        # デバイス台帳登録・更新フォーム
    │   ├── mail_setting.py        # メール通知設定フォーム
    │   └── transfer.py            # CSVインポートフォーム
    │
    ├── services/                  # ビジネスロジック（CRUD処理本体、トランザクション管理）
    │   ├── __init__.py
    │   ├── device_service.py      # デバイスCRUD
    │   ├── user_service.py        # ユーザーCRUD
    │   ├── organization_service.py # 組織CRUD（organization_closure連携含む）
    │   ├── alert_setting_service.py # アラート設定CRUD
    │   ├── device_stock_service.py  # デバイス台帳CRUD
    │   ├── mail_setting_service.py  # メール通知設定CRUD
    │   ├── alert_history_service.py # アラート履歴参照
    │   ├── mail_history_service.py  # メール通知履歴参照
    │   ├── dashboard_service.py   # ダッシュボードデータ取得（Unity Catalog経由）
    │   └── csv_service.py         # CSVインポート・エクスポート共通処理
    │
    ├── views/                     # Blueprint定義（ルーティング・リクエスト/レスポンス制御）
    │   ├── __init__.py
    │   ├── admin/                 # 管理機能 Blueprint（ADM-001〜016）
    │   │   ├── __init__.py        # Blueprint登録
    │   │   ├── devices.py         # /admin/devices/* デバイス管理ルーティング
    │   │   ├── users.py           # /admin/users/* ユーザー管理ルーティング
    │   │   ├── organizations.py   # /admin/organizations/* 組織管理ルーティング
    │   │   └── device_inventory.py # /admin/device-inventory/* デバイス台帳ルーティング
    │   ├── alert/                 # アラート機能 Blueprint（ALT-001〜006）
    │   │   ├── __init__.py
    │   │   ├── alert_settings.py  # /alert/alert-settings/* アラート設定ルーティング
    │   │   └── alert_history.py   # /alert/alert-history/* アラート履歴ルーティング
    │   ├── notice/                # 通知機能 Blueprint（NTC-001〜006）
    │   │   ├── __init__.py
    │   │   ├── mail_settings.py   # /notice/mail-settings/* メール通知設定ルーティング
    │   │   └── mail_history.py    # /notice/mail-history/* メール通知履歴ルーティング
    │   ├── dashboard/             # ダッシュボード Blueprint（DSH-001）
    │   │   ├── __init__.py
    │   │   └── views.py           # /, /dashboard ダッシュボード表示ルーティング
    │   ├── account/               # アカウント Blueprint（ACC-001〜002）
    │   │   ├── __init__.py
    │   │   └── views.py           # /account/* 言語設定・ユーザ情報参照ルーティング
    │   └── transfer/              # インポート Blueprint（TRF-001）
    │       ├── __init__.py
    │       └── views.py           # /transfer/* CSVインポートルーティング
    │
    ├── decorators/                # カスタムデコレータ
    │   ├── __init__.py
    │   └── auth.py                # @require_role 等の権限チェックデコレータ
    │
    ├── templates/                 # Jinja2テンプレート
    │   ├── base.html              # 共通レイアウト（ヘッダー、サイドバー、フッター）
    │   ├── components/            # 再利用可能なマクロ
    │   │   ├── pagination.html    # ページネーションマクロ
    │   │   ├── modal.html         # モーダルマクロ（メッセージ・確認・フォーム）
    │   │   ├── form_fields.html   # フォーム部品マクロ
    │   │   ├── table.html         # テーブルマクロ
    │   │   └── search.html        # 検索フォームマクロ
    │   ├── errors/
    │   │   ├── 403.html           # 403エラーページ（DB未登録ユーザー）
    │   │   └── 500.html           # 500エラーページ
    │   ├── admin/
    │   │   ├── devices/           # デバイス管理テンプレート（list, form, detail）
    │   │   ├── users/             # ユーザー管理テンプレート
    │   │   ├── organizations/     # 組織管理テンプレート
    │   │   └── device_inventory/  # デバイス台帳テンプレート
    │   ├── alert/
    │   │   ├── alert_settings/    # アラート設定テンプレート
    │   │   └── alert_history/     # アラート履歴テンプレート
    │   ├── notice/
    │   │   ├── mail_settings/     # メール通知設定テンプレート
    │   │   └── mail_history/      # メール通知履歴テンプレート
    │   ├── dashboard/             # ダッシュボードテンプレート
    │   ├── account/               # アカウントテンプレート
    │   └── transfer/              # CSVインポートテンプレート
    │
    └── static/                    # 静的ファイル
        ├── css/
        │   ├── variables.css      # CSS変数定義（カラー、スペーシング、フォント）
        │   ├── reset.css          # CSSリセット
        │   ├── base.css           # 基本スタイル
        │   ├── main.css           # メインスタイルシート（全CSSをインポート）
        │   └── components/        # BEMコンポーネント別CSS
        │       ├── button.css
        │       ├── alert.css
        │       ├── form.css
        │       ├── table.css
        │       ├── pagination.css
        │       ├── modal.css
        │       ├── sort.css
        │       └── spinner.css
        ├── images/                # アイコン等の画像
        └── js/
            ├── main.js            # グローバルJS（検索条件のsessionStorage保持等）
            └── components/        # コンポーネント別JS
                ├── modal.js       # Modalクラス
                ├── validation.js  # FormValidatorクラス
                ├── toast.js       # Toastクラス
                ├── sort.js        # TableSortクラス（部分ソート＝クライアント側）
                └── pagination.js  # Paginationクラス（UI描画・ページ遷移リクエスト発行）
```

---

## テスト構成

### テストレベル

| テストレベル | ツール                      | 対象                            | 実行方式       |
| ------------ | --------------------------- | ------------------------------- | -------------- |
| 単体テスト   | pytest + unittest.mock      | Service層、Model層、Utility関数 | 自動（pytest） |
| 結合テスト   | pytest + Flask test_client  | APIエンドポイント、DB連携       | 自動（pytest） |
| E2Eテスト    | 手動 / Playwright（必要時） | ユーザー業務フロー（CUJ）       | 手動基本       |

### テストディレクトリ構成

- 単体テスト: `src/`のレイヤー構成を1:1ミラー
- 結合テスト: Blueprint（エンドポイント）単位
- 命名規則: `test_<実装ファイル名>.py`

```
tests/
├── conftest.py                          # 共通フィクスチャ（app, client, db_session）
├── unit/                                # 単体テスト
│   ├── conftest.py
│   ├── services/                        # src/services/と1:1対応
│   │   ├── test_device_service.py
│   │   ├── test_user_service.py
│   │   ├── test_organization_service.py
│   │   ├── test_alert_setting_service.py
│   │   ├── test_alert_history_service.py
│   │   ├── test_device_stock_service.py
│   │   ├── test_mail_setting_service.py
│   │   ├── test_mail_history_service.py
│   │   ├── test_dashboard_service.py
│   │   └── test_csv_service.py
│   ├── models/                          # src/models/と1:1対応
│   │   ├── test_device.py
│   │   ├── test_user.py
│   │   ├── test_organization.py
│   │   ├── test_alert.py
│   │   ├── test_notification.py
│   │   └── test_device_stock.py
│   ├── auth/                            # src/auth/と1:1対応
│   │   ├── test_factory.py
│   │   ├── test_middleware.py
│   │   ├── test_token_exchange.py
│   │   └── providers/
│   │       └── test_azure_easy_auth.py
│   └── decorators/                      # src/decorators/と1:1対応
│       └── test_auth.py
├── integration/                         # 結合テスト（Blueprint単位）
│   ├── conftest.py
│   ├── test_device_routes.py
│   ├── test_user_routes.py
│   ├── test_organization_routes.py
│   ├── test_device_inventory_routes.py
│   ├── test_alert_setting_routes.py
│   ├── test_alert_history_routes.py
│   ├── test_mail_setting_routes.py
│   ├── test_mail_history_routes.py
│   ├── test_dashboard_routes.py
│   ├── test_account_routes.py
│   ├── test_transfer_routes.py
│   └── test_auth_routes.py
└── e2e/                                 # E2Eテスト（手動基本）
```

### テスト実行コマンド

```bash
pytest                          # 全テスト実行
pytest -m unit                  # 単体テストのみ
pytest -m integration           # 結合テストのみ
pytest --cov=src                # カバレッジ付き実行
```

---

## セキュリティ

- SQLインジェクション対策: SQLAlchemyプリペアドステートメント使用
- XSS対策: Jinja2自動エスケープ有効
- CSRF対策: Flask-WTF使用
- 入力値検証: Flask-WTFフォームバリデーション
- リクエストサイズ制限: 10MB

---

## 日時フォーマット

- 形式: ISO 8601（JST）`YYYY-MM-DDTHH:mm:ss+09:00`
- タイムゾーン: JST（UTC+9）で統一

---

## 関連ドキュメント

- `docs/03-features/common/common-specification.md` - 共通仕様
- `docs/03-features/common/app-database-specification.md` - OLTP DB設計
- `docs/03-features/common/unity-catalog-database-specification.md` - Unity Catalog設計
- `docs/03-features/common/ui-common-specification.md` - UI共通仕様
- `docs/03-features/common/authentication-specification.md` - 認証仕様
- `docs/00-rules/` - コーディングルール

