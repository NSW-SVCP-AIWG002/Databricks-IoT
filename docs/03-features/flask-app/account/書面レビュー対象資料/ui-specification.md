# アカウント機能 UI仕様書

## 📑 目次

- [基本情報](#基本情報)
- [画面一覧](#画面一覧)
- [ACC-001: 言語設定画面](#acc-001-言語設定画面)
- [ACC-002: ユーザ情報参照画面](#acc-002-ユーザ情報参照画面)
- [共通UI仕様](#共通ui仕様)
- [関連ドキュメント](#関連ドキュメント)

---

## 基本情報

| 項目 | 内容 |
|------|------|
| 機能ID | FR-004-7 |
| 機能名 | アカウント機能 |
| カテゴリ | マスタ管理機能 |
| 実装領域 | Flask アプリケーション |
| ディレクトリ | `docs/03-features/flask-app/account/` |

---

## 画面一覧

| 画面ID | 画面名 | パス | 概要 | 備考 |
|--------|--------|------|------|------|
| ACC-001 | 言語設定画面 | `/account/language` | システム表示言語の変更 | |
| ACC-002 | ユーザ情報参照画面 | `/account/profile` | ログインユーザー自身の情報参照 | 読み取り専用 |

---

## ACC-001: 言語設定画面

### ワイヤーフレーム

```
┌────────────────────────────────────────────────────────────────────┐
│ [グローバルメニュー]                                                │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ 言語設定                                                     │ │
│ └──────────────────────────────────────────────────────────────┘ │
│  表示言語を選択してください。                                      │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ 言語設定フォーム                                             │ │
│ ├──────────────────────────────────────────────────────────────┤ │
│ │ 表示言語 *                                                   │ │
│ │ [ JA                               ▼]                       │ │
│ │                                                               │ │
│ │                                          [設定] [キャンセル]  │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### レイアウト

#### 画面構成
- **グローバルメニュー**: 画面左部に常時表示
- **画面タイトル**: 「言語設定」を画面左上に表示
- **言語設定フォーム**: 画面中央に配置
- **設定・キャンセルボタン**: フォーム右下に配置

#### レスポンシブ対応
- **デスクトップ（1920x1080）**: フォームを画面中央に配置、幅600px
- **タブレット（768x1024）**: フォーム幅を画面幅の90%に調整

### UI要素概要

| 要素ID | 要素名 | 種別 | I/O | 必須 | 説明 |
|--------|--------|------|-----|------|------|
| E-001 | 画面タイトル | テキスト | O | - | 「言語設定」を表示 |
| E-002 | 表示言語ラベル | ラベル | O | - | 「表示言語」を表示（必須マーク付き） |
| E-003 | 表示言語プルダウン | セレクト | I/O | ◎ | 言語選択 |
| E-004 | 設定ボタン | ボタン | I | - | 言語設定をPOST送信 |
| E-005 | キャンセルボタン | ボタン | I | - | 変更をキャンセルして元の画面に戻る |

### UI要素詳細

#### E-001: 画面タイトル

**概要**: 画面左上に表示される機能名タイトル

**HTML例**:
```html
<h1 class="page-title">言語設定</h1>
```

**CSSクラス**: `.page-title`

**表示内容**: 「言語設定」

---

#### E-002: 表示言語ラベル

**概要**: 言語選択フィールドのラベル

**HTML例**:
```html
<label for="preferred-language" class="form-label form-label--required">
  表示言語
</label>
```

**CSSクラス**: `.form-label`, `.form-label--required`

**表示内容**: 「表示言語」（必須マーク付き）

---

#### E-003: 表示言語プルダウン

**概要**: 言語選択用のプルダウン

**HTML例**:
```html
<select id="language" name="language_code" class="form-select" required>
  {% for language in languages %}
  <option value="{{ language.language_code }}" {% if language.language_code == current_language_code %}selected{% endif %}>
    {{ language.language_code }}
  </option>
  {% endfor %}
</select>
```

**CSSクラス**: `.form-select`

**初期値**: `language_code`

**選択肢**:
- language_masterテーブルから動的に取得（delete_flag = 0のレコードのみ）

**バリデーション**:
- 必須入力
- 値はlanguage_masterに存在するlanguage_code（delete_flag = 0）のみ許可

---

#### E-004: 設定ボタン

**概要**: 言語設定をPOST送信するボタン

**HTML例**:
```html
<button type="submit" class="btn btn--primary" id="save-button">設定</button>
```

**CSSクラス**: `.btn`, `.btn--primary`

**動作**: フォームをPOST送信（/account/language）

**活性条件**: 常時活性

---

#### E-005: キャンセルボタン

**概要**: 変更をキャンセルして元の画面に戻るボタン

**HTML例**:
```html
<button type="button" class="btn btn--secondary" id="cancel-button">キャンセル</button>
```

**CSSクラス**: `.btn`, `.btn--secondary`

**動作**: 前の画面に戻る（history.back()またはリダイレクト）

**活性条件**: 常時活性

---

### バリデーションルール

| 項目名 | 必須 | データ型 | 最大文字数 | 形式 | 値の範囲 | エラーメッセージ |
|--------|------|---------|-----------|------|---------|----------------|
| 言語コード（language_code） | ◎ | VARCHAR | 10 | 文字列 | language_masterに存在するlanguage_code（delete_flag = 0） | 「言語を選択してください」 |

**サーバーサイドバリデーション**:
```python
# Flask-WTF バリデーション例
from flask_wtf import FlaskForm
from wtforms import SelectField
from wtforms.validators import DataRequired

class LanguageSettingsForm(FlaskForm):
    language_code = SelectField(
        '言語',
        choices=[],  # 動的に設定（language_masterから取得）
        coerce=str,  # 文字列型に変換
        validators=[DataRequired(message='言語を選択してください')]
    )

# フォーム初期化時にlanguage_masterから選択肢を取得
def get_language_choices():
    """language_masterから言語選択肢を取得"""
    connection = mysql_pool.get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT language_code, language_name
            FROM language_master
            WHERE delete_flag = 0
            ORDER BY language_code
        """
        cursor.execute(query)
        languages = cursor.fetchall()
        return [(lang['language_code'], lang['language_code']) for lang in languages]
    finally:
        cursor.close()
        connection.close()

# フォーム使用時
form = LanguageSettingsForm()
form.language_code.choices = get_language_choices()
```

---

## ACC-002: ユーザ情報参照画面

### ワイヤーフレーム

```
┌────────────────────────────────────────────────────────────────────┐
│ [グローバルメニュー]                                                │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ ユーザー情報                                                 │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ ユーザー情報カード                                           │ │
│ ├──────────────────────────────────────────────────────────────┤ │
│ │ ユーザーID:        user-12345                                │ │
│ │ ユーザー名:        山田 太郎                                 │ │
│ │ メールアドレス:    yamada@example.com                        │ │
│ │ 所属組織:          株式会社サンプル                          │ │
│ │ ロール:            管理者                                    │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### レイアウト

#### 画面構成
- **グローバルメニュー**: 画面左部に常時表示
- **画面タイトル**: 「ユーザー情報」を画面左上に表示
- **ユーザー情報カード**: 画面中央に配置、カード形式で情報を表示

#### レスポンシブ対応
- **デスクトップ（1920x1080）**: カードを画面中央に配置、幅800px
- **タブレット（768x1024）**: カード幅を画面幅の90%に調整

### UI要素概要

| 要素ID | 要素名 | 種別 | I/O | 必須 | 説明 |
|--------|--------|------|-----|------|------|
| E-101 | 画面タイトル | テキスト | O | - | 「ユーザー情報」を表示 |
| E-102 | ユーザーID | テキスト | O | - | ログインユーザーのユーザーID |
| E-103 | ユーザー名 | テキスト | O | - | ログインユーザーのユーザー名 |
| E-104 | メールアドレス | テキスト | O | - | ログインユーザーのメールアドレス |
| E-105 | 所属組織 | テキスト | O | - | ログインユーザーの所属組織名 |
| E-106 | ロール | テキスト | O | - | ログインユーザーのロール |

### UI要素詳細

#### E-101: 画面タイトル

**概要**: 画面左上に表示される機能名タイトル

**HTML例**:
```html
<h1 class="page-title">ユーザー情報</h1>
```

**CSSクラス**: `.page-title`

**表示内容**: 「ユーザー情報」

---

#### E-102 〜 E-106: ユーザー情報カード

**概要**: ログインユーザー自身の情報を読み取り専用で表示

**HTML例**:
```html
<div class="info-card">
  <div class="info-card__header">
    <h2 class="info-card__title">ユーザー情報</h2>
  </div>
  <div class="info-card__body">
    <dl class="info-list">
      <dt class="info-list__term">ユーザーID</dt>
      <dd class="info-list__desc">{{ user.user_id }}</dd>

      <dt class="info-list__term">ユーザー名</dt>
      <dd class="info-list__desc">{{ user.user_name }}</dd>

      <dt class="info-list__term">メールアドレス</dt>
      <dd class="info-list__desc">{{ user.email_address }}</dd>

      <dt class="info-list__term">所属組織</dt>
      <dd class="info-list__desc">{{ user.organization_name }}</dd>

      <dt class="info-list__term">ロール</dt>
      <dd class="info-list__desc">{{ user.role }}</dd>
    </dl>
  </div>
</div>
```

**CSSクラス**: `.info-card`, `.info-card__header`, `.info-card__title`, `.info-card__body`, `.info-list`, `.info-list__term`, `.info-list__desc`

**データソース**:
- `user_master` テーブル（ログインユーザーのレコード）
- `organization_master` テーブル（所属組織名）

**表示項目**:
- ユーザーID: `user.user_id`
- ユーザー名: `user.user_name`
- メールアドレス: `user.email_address`
- 所属組織: `user.organization_name`（organization_masterと結合）
- ロール: `user.role`

---

## 共通UI仕様

### BEMクラス命名規則

**Block（ブロック）**: 独立したコンポーネント
```css
.form-select
.info-card
.modal
```

**Element（要素）**: ブロック内の要素
```css
.modal__header
.modal__title
.info-card__body
.info-list__term
```

**Modifier（修飾子）**: 状態やバリエーション
```css
.btn--primary
.btn--secondary
.form-label--required
.modal__icon--info
```

### カラースキーム

**ボタン色**:
- **プライマリボタン（保存）**: 青系（#007bff）
- **セカンダリボタン（キャンセル）**: グレー系（#6c757d）

**必須マーク**: 赤色（#dc3545）

**情報アイコン**: 青色（#17a2b8）

### レスポンシブデザイン

**ブレークポイント**:
- デスクトップ: 1920px以上
- タブレット: 768px〜1919px
- モバイル: 767px以下（初期実装対象外）

---

## 関連ドキュメント

### 機能設計・仕様

- [README](./README.md) - 機能概要、データモデル、画面一覧
- [ワークフロー仕様書](./workflow-specification.md) - ユーザー操作の処理フローと動作詳細
- [機能要件定義書](../../../02-requirements/functional-requirements.md) - FR-004-7: アカウント機能
- [UI共通仕様書](../../common/ui-common-specification.md) - すべての画面に共通するUI仕様

---

**このドキュメントは、実装前に必ずレビューを受けてください。**
