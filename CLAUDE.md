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
- **認証基盤**: Databricks認証（Entra ID統合）
- **デプロイ環境**: Databricks Apps (App Compute)

### データベース
| 種別 | 用途 | 技術 |
|------|------|------|
| OLTP DB | マスタデータ管理、トランザクション処理 | Azure Database for MySQL 8.0 (utf8mb4) |
| 分析DB | センサーデータ分析 | Unity Catalog (Delta Lake) on ADLS Gen2 |

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
| ロール | 説明 |
|--------|------|
| system_admin | システム保守者（最上位権限） |
| management_admin | 管理者 |
| sales_company_user | 販社ユーザー |
| service_company_user | サービス利用者 |

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

| コード | 使用場面 | Flask実装 |
|--------|----------|-----------|
| 200 | 正常処理 | `render_template()` |
| 302 | リダイレクト | `redirect()` |
| 400 | パラメータエラー | `render_template()` with error |
| 403 | 権限不足 | `render_template('errors/403.html')` |
| 404 | リソース未検出 | `render_template('errors/404.html')` |
| 422 | バリデーションエラー | `render_template()` with form errors |
| 500 | サーバーエラー | `render_template('errors/500.html')` |

---

## ファイル構成

```
static/
├── css/
│   ├── variables.css       # CSS変数定義
│   ├── components/         # コンポーネント別CSS
│   │   ├── button.css
│   │   ├── form.css
│   │   ├── table.css
│   │   └── modal.css
│   └── main.css
└── js/
    ├── components/
    │   ├── modal.js
    │   ├── validation.js
    │   └── toast.js
    └── main.js
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
- `docs/00-rules/` - コーディングルール

