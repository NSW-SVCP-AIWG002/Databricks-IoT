# UI共通仕様 - HTML + CSS版

**使用技術:** HTML + CSS + BEM命名規則 + Jinja2テンプレート

## 📑 目次

- [基本方針](#基本方針)
- [設計原則](#設計原則)
- [カラーパレット](#カラーパレット)
- [タイポグラフィ](#タイポグラフィ)
- [スペーシングシステム](#スペーシングシステム)
- [BEM命名規則](#bem命名規則)
- [アイコン](#アイコン)
- [共通UIコンポーネント](#共通uiコンポーネント)
  - [ボタン](#ボタン)
  - [アラート・通知](#アラート通知)
  - [フォーム要素](#フォーム要素)
  - [テーブル表示](#テーブル表示)
  - [ページネーション](#ページネーション)
  - [ソート](#ソート)
  - [モーダル・ダイアログ](#モーダルダイアログ)
- [バリデーション](#バリデーション)
- [エラーメッセージ表示](#エラーメッセージ表示)
- [ローディング表示](#ローディング表示)
- [アクセシビリティ](#アクセシビリティ)
- [レスポンシブデザイン](#レスポンシブデザイン)
- [ブラウザサポート](#ブラウザサポート)
- [画面遷移](#画面遷移)
- [JavaScriptインタラクション](#javascriptインタラクション)
- [関連ドキュメント](#関連ドキュメント)

---

すべての画面で共通するUI仕様をHTML + CSS + BEM命名規則を使用して定義します。

## 基本方針

### 技術スタック

- **HTML5**: セマンティックHTML
- **CSS3**: カスタムプロパティ（CSS変数）、Flexbox、Grid
- **BEM命名規則**: Block__Element--Modifier
- **Jinja2テンプレート**: Flask SSRテンプレートエンジン
- **JavaScript**: バニラJS（ライブラリなし）

### アーキテクチャ

- **Flask + Jinja2**: サーバーサイドレンダリング（SSR）
- **UIライブラリ不使用**: Bootstrap、Tailwind、CSS Modules等のライブラリは使用しない
- **カスタムCSS**: すべてのスタイルを独自に定義
- **Databricks Apps**: ホスティング環境（App Compute）

---

## 設計原則

### CSS設計原則

1. **CSS変数の活用**: 色、サイズ、スペーシング等は全てCSS変数で管理
2. **BEM命名規則**: クラス名の衝突を避け、保守性を向上
3. **デスクトップファースト**: 基本スタイルはデスクトップ、メディアクエリでタブレット対応
4. **アクセシビリティ優先**: WCAG 2.1 AA準拠

### ファイル構成

```
static/
├── css/
│   ├── variables.css       # CSS変数定義
│   ├── reset.css           # CSSリセット
│   ├── base.css            # 基本スタイル
│   ├── components/         # コンポーネント別CSS
│   │   ├── button.css
│   │   ├── alert.css
│   │   ├── form.css
│   │   ├── table.css
│   │   ├── pagination.css
│   │   ├── modal.css
|   |   ├── sort.css
│   │   └── spinner.css
│   └── main.css            # メインスタイルシート（全てをインポート）
├── images/                 # アイコンを格納
└── js/
    ├── components/
    │   ├── modal.js
    │   ├── validation.js
    │   ├── toast.js
    │   └── sort.js
    └── main.js
```

---

## カラーパレット

### CSS変数定義（variables.css）

```css
:root {
  /* プライマリカラー */
  --color-primary: #2272B4;
  --color-primary-hover: #1E639B;

  /* セカンダリカラー */
  --color-secondary: #6C757D;
  --color-secondary-hover: #555B61;

  /* ブランドカラー（ページネーション等） */
  --color-brand-blue: #DBE8F3;

  /* ステータスカラー */
  --color-success: #28A745;
  --color-success-light: #D4EDDA;
  --color-success-dark: #155724;

  --color-danger: #F44336;
  --color-danger-hover: #DA190B;
  --color-danger-light: #F8D7DA;
  --color-danger-dark: #721C24;

  --color-warning: #FFC107;
  --color-warning-light: #FFF3CD;
  --color-warning-dark: #856404;

  --color-info: #17A2B8;
  --color-info-light: #D1ECF1;
  --color-info-dark: #0C5460;

  /* グレースケール */
  --color-white: #FFFFFF;
  --color-gray-50: #F8F9FA;
  --color-gray-100: #F1F3F5;
  --color-gray-200: #E9ECEF;
  --color-gray-300: #DEE2E6;
  --color-gray-400: #CED4DA;
  --color-gray-500: #ADB5BD;
  --color-gray-600: #6C757D;
  --color-gray-700: #495057;
  --color-gray-800: #343A40;
  --color-gray-900: #212529;
  --color-black: #000000;

  /* テーブル */
  --color-table-header: #F3F3F4;

  /* ボーダー */
  --color-border: #CED4DA;

  /* フォーカス */
  --color-focus-shadow: rgba(128, 189, 255, 0.25);
  --color-danger-focus-shadow: rgba(220, 53, 69, 0.25);
}
```

---

## タイポグラフィ

### CSS変数定義

```css
:root {
  /* フォントファミリー */
  --font-family-base: 'メイリオ', 'Meiryo', sans-serif;

  /* フォントサイズ */
  --font-size-sm: 12px;
  --font-size-base: 14px;
  --font-size-lg: 16px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;

  /* フォントウェイト */
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* 行間 */
  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;
}
```

---

## スペーシングシステム

### 8pxベーススペーシング

```css
:root {
  --spacing-0: 0;
  --spacing-1: 4px;    /* 0.5 × 8px */
  --spacing-2: 8px;    /* 1 × 8px */
  --spacing-3: 12px;   /* 1.5 × 8px */
  --spacing-4: 16px;   /* 2 × 8px */
  --spacing-5: 20px;   /* 2.5 × 8px */
  --spacing-6: 24px;   /* 3 × 8px */
  --spacing-8: 32px;   /* 4 × 8px */
  --spacing-10: 40px;  /* 5 × 8px */
  --spacing-12: 48px;  /* 6 × 8px */
  --spacing-16: 64px;  /* 8 × 8px */

  /* 特殊サイズ */
  --border-radius-base: 4px;
  --border-radius-lg: 8px;
  --border-radius-full: 9999px;

  --border-width: 1px;
  --border-width-thick: 2px;
  --border-width-heavy: 4px;

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

  --transition-base: 0.2s ease;
  --transition-fast: 0.15s ease;
}
```

---

## BEM命名規則

### 命名パターン

```
Block__Element--Modifier
```

### 例

```css
/* Block（独立したコンポーネント） */
.button { }

/* Element（Blockの構成要素） */
.button__icon { }
.button__text { }

/* Modifier（状態や種類） */
.button--primary { }
.button--disabled { }
.button--large { }

/* 組み合わせ */
.button.button--primary { }
.button__icon--left { }
```

### 使用例（HTML）

```html
<button class="button button--primary">
  <span class="button__icon button__icon--left">✓</span>
  <span class="button__text">登録</span>
</button>
```

---

## アイコン

### 共通ルール

- Google Material Iconを使用する
- ファイル形式はSVGとする

---

## 共通UIコンポーネント

### ボタン

#### 仕様

| タイプ | 用途 | BEMクラス | 使用場面 |
|--------|------|-----------|----------|
| **プライマリボタン** | 主要なアクション | `.button--primary` | 登録、保存、検索、更新 |
| **セカンダリボタン** | 補助的なアクション | `.button--secondary` | キャンセル |
| **危険ボタン** | 削除などの危険な操作 | `.button--danger` | 削除、無効化 |

#### CSS定義（button.css）

```css
/* ボタン基本スタイル */
.button {
  display: inline-block;
  height: 40px;
  padding: var(--spacing-2) var(--spacing-5);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-normal);
  text-align: center;
  text-decoration: none;
  border: none;
  border-radius: var(--border-radius-base);
  cursor: pointer;
  transition: all var(--transition-base);
  outline: none;
  user-select: none;
}

.button:focus {
  box-shadow: 0 0 0 2px var(--color-focus-shadow);
}

/* プライマリボタン */
.button--primary {
  background-color: var(--color-primary);
  color: var(--color-white);
}

.button--primary:hover {
  background-color: var(--color-primary-hover);
}

/* セカンダリボタン */
.button--secondary {
  background-color: var(--color-secondary);
  color: var(--color-white);
}

.button--secondary:hover {
  background-color: var(--color-secondary-hover);
}

/* 危険ボタン */
.button--danger {
  background-color: var(--color-danger);
  color: var(--color-white);
}

.button--danger:hover {
  background-color: var(--color-danger-hover);
}

/* 無効化状態 */
.button:disabled,
.button--disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

/* サイズバリエーション */
.button--small {
  height: 32px;
  padding: var(--spacing-1) var(--spacing-3);
  font-size: var(--font-size-sm);
}

.button--large {
  height: 48px;
  padding: var(--spacing-3) var(--spacing-6);
  font-size: var(--font-size-lg);
}

/* 全幅ボタン */
.button--block {
  display: block;
  width: 100%;
}
```

#### Jinja2テンプレート例

```jinja2
{# macros/button.html #}
{% macro button(text, type='primary', size='normal', disabled=False, onclick='') %}
<button
  class="button button--{{ type }} {% if size != 'normal' %}button--{{ size }}{% endif %}"
  {% if disabled %}disabled{% endif %}
  {% if onclick %}onclick="{{ onclick }}"{% endif %}
  type="button"
>
  {{ text }}
</button>
{% endmacro %}

{# 使用例 #}
{% from 'macros/button.html' import button %}

{{ button('登録', type='primary') }}
{{ button('キャンセル', type='secondary') }}
{{ button('削除', type='danger') }}
{{ button('無効', type='primary', disabled=True) }}
```

---

### アラート・通知

#### 仕様

| タイプ | 用途 | BEMクラス | アイコン |
|--------|------|-----------|----------|
| **成功** | 操作成功メッセージ | `.alert--success` | ✓ チェックマーク |
| **エラー** | エラーメッセージ | `.alert--error` | ✕ エラーアイコン |
| **警告** | 警告メッセージ | `.alert--warning` | ⚠ 警告アイコン |
| **情報** | 情報メッセージ | `.alert--info` | ℹ 情報アイコン |

#### CSS定義（alert.css）

```css
/* アラート基本スタイル */
.alert {
  background-color: var(--color-white);
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--border-radius-base);
  box-shadow: var(--shadow-lg);
  min-width: 320px;
}

.alert__header {
  display: flex;
  align-items: center;
  text-align: left;
  padding: var(--spacing-4) var(--spacing-4) var(--spacing-2);
}

.alert__icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  font-size: var(--font-size-lg);
}

.alert__title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-900);
  margin-left: var(--spacing-2);
}

.alert__body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-0) var(--spacing-4) var(--spacing-4);
}

.alert__body button {
  align-items: right;
}

.alert__message {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-normal);
  color: var(--color-gray-900);
}

/* トースト（固定位置表示） */
.toast-container {
  position: fixed;
  top: var(--spacing-4);
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.toast {
  margin-bottom: var(--spacing-2);
  animation: fadeInDown 0.3s ease-out;
}

.toast--fade-out {
  animation: fadeOut 0.3s ease-out forwards;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeOut {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}
```

#### HTML例

```html
<!-- 成功メッセージ -->
<div class="alert" role="alert">
  <div class="alert__header">
    <span class="alert__icon">✔</span>
    <h2 class="alert__title">通知メッセージ</h2>
  </div>
  <div class="alert__body">
    <h4 class="alert__message">ユーザを登録しました</h4>
    <button class="button button--secondary button--small">
        <span class="button__text">閉じる</span>
    </button>
  </div>
</div>

<!-- エラーメッセージ -->
 <div class="alert" role="alert">
  <div class="alert__header">
    <span class="alert__icon">✕</span>
    <h2 class="alert__title">通知メッセージ</h2>
  </div>
  <div class="alert__body">
    <h4 class="alert__message">データの取得に失敗しました。</h4>
    <button class="button button--secondary button--small">
        <span class="button__text">閉じる</span>
    </button>
  </div>
</div>

<!-- トースト表示 -->
<div class="toast-container">
  <div class="alert toast" role="alert">
    <div class="alert__header">
      <span class="alert__icon">✔</span>
      <h2 class="alert__title">通知メッセージ</h2>
    </div>
    <div class="alert__body">
      <h4 class="alert__message">ユーザを登録しました</h4>
      <button class="button button--secondary button--small">
          <span class="button__text">閉じる</span>
      </button>
    </div>
  </div>
</div>
```

#### Jinja2テンプレート例

```jinja2
{# macros/alert.html #}
{% macro alert(message, type='info', closable=True) %}
<div class="alert alert--{{ type }}" role="alert">
  <span class="alert__icon">
    {% if type == 'success' %}✓
    {% elif type == 'error' %}✕
    {% elif type == 'warning' %}⚠
    {% else %}ℹ
    {% endif %}
  </span>
  <p class="alert__message">{{ message }}</p>
  {% if closable %}
  <button class="alert__close" onclick="this.parentElement.remove()" aria-label="閉じる">
    ✕
  </button>
  {% endif %}
</div>
{% endmacro %}
```

---

### フォーム要素

#### テキスト入力

**CSS定義（form.css）**

```css
/* フォームグループ */
.form-group {
  margin-bottom: var(--spacing-4);
}

/* ラベル */
.form-label {
  display: block;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-700);
  margin-bottom: var(--spacing-1);
}

.form-label__required {
  padding: var(--spacing-0) var(--spacing-1);
  font-size: var(--font-size-sm);
  background-color: var(--color-danger);
  border: none;
  border-radius: var(--border-radius-base);
  color: var(--color-white);
  margin-left: var(--spacing-1);
  vertical-align: middle;
}

/* 入力欄 */
.form-input {
  width: 100%;
  height: 40px;
  padding: var(--spacing-2) var(--spacing-3);
  font-size: var(--font-size-lg);
  color: var(--color-gray-900);
  background-color: var(--color-white);
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--border-radius-base);
  outline: none;
  transition: all var(--transition-base);
}

.form-input:hover {
  border-color: var(--color-primary);
}

.form-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-focus-shadow);
}

.form-input:disabled {
  background-color: var(--color-gray-200);
  border-color: var(--color-border);
  opacity: 0.5;
  cursor: not-allowed;
}

/* エラー状態 */
.form-input--error {
  border-color: var(--color-danger);
}

.form-input--error:hover {
  border-color: var(--color-danger);
}

.form-input--error:focus {
  border-color: var(--color-danger);
  box-shadow: 0 0 0 2px var(--color-danger-focus-shadow);
}

/* エラーメッセージ */
.form-error {
  font-size: var(--font-size-lg);
  color: var(--color-danger);
  margin-top: var(--spacing-1);
  display: flex;
  align-items: center;
}
```

**HTML例**

```html
<!-- 基本的なテキスト入力 -->
<div class="form-group">
  <label for="username" class="form-label">
    ユーザ名 <span class="form-label__required">必須</span>
  </label>
  <input
    type="text"
    id="username"
    class="form-input"
    maxlength="255"
    required
  >
</div>

<!-- エラー状態 -->
<div class="form-group">
  <label for="email" class="form-label">
    メールアドレス <span class="form-label__required">必須</span>
  </label>
  <input
    type="email"
    id="email"
    class="form-input form-input--error"
    required
    aria-invalid="true"
    aria-describedby="email-error"
  >
  <p id="email-error" class="form-error">
    有効なメールアドレスを入力してください
  </p>
</div>
```

#### セレクト（ドロップダウン）

**CSS定義**

```css
/* セレクトボックス */
.form-select {
  width: 100%;
  height: 40px;
  padding: var(--spacing-2);
  font-size: var(--font-size-base);
  color: var(--color-gray-900);
  background-color: var(--color-white);
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--border-radius-base);
  outline: none;
  cursor: pointer;
  transition: all var(--transition-base);
}

.form-select:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-focus-shadow);
}

.form-select:disabled {
  background-color: var(--color-gray-200);
  opacity: 0.5;
  cursor: not-allowed;
}

/* エラー状態 */
.form-select--error {
  border-color: var(--color-danger);
  background-color: var(--color-danger-light);
}

/* 複数選択 */
.form-select--multiple {
  height: auto;
}
```

**HTML例**

```html
<!-- 単一選択 -->
<div class="form-group">
  <label for="role" class="form-label">
    権限 <span class="form-label__required">*</span>
  </label>
  <select id="role" class="form-select" required>
    <option value="" selected>選択してください</option>
    <option value="user_admin">ユーザ管理者</option>
    <option value="user">一般ユーザ</option>
  </select>
</div>

<!-- 複数選択 -->
<div class="form-group">
  <label for="groups" class="form-label">所属グループ</label>
  <select id="groups" class="form-select form-select--multiple" multiple size="5">
    <option value="grp_001">グループA</option>
    <option value="grp_002">グループB</option>
    <option value="grp_003">グループC</option>
  </select>
  <p class="form-help">複数選択可能（Ctrl+クリック）</p>
</div>
```

#### チェックボックス

**CSS定義**

```css
/* オプショングループ */
.form-options {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

/* オプション項目 */
.form-option {
  display: flex;
  align-items: center;
}

/* ラジオボタン・チェックボックス */
.form-option__input {
  width: 16px;
  height: 16px;
  margin-right: var(--spacing-2);
  cursor: pointer;
  accent-color: var(--color-primary);
}

.form-option__label {
  font-size: var(--font-size-base);
  color: var(--color-gray-700);
  cursor: pointer;
  user-select: none;
}
```

**HTML例**

```html
<!-- チェックボックス -->
<div class="form-group">
  <div class="form-label">通知設定</div>
  <div class="form-options">
    <div class="form-option">
      <input
        type="checkbox"
        id="notifyEmail"
        class="form-option__input"
        checked
      >
      <label for="notifyEmail" class="form-option__label">メール通知を受け取る</label>
    </div>
    <div class="form-option">
      <input
        type="checkbox"
        id="notifySms"
        class="form-option__input"
      >
      <label for="notifySms" class="form-option__label">SMS通知を受け取る</label>
    </div>
  </div>
</div>
```

#### 日付ピッカー

**CSS定義**

```css
/* 日付入力（HTML5） */
.form-input[type="date"],
.form-input[type="datetime-local"] {
  /* 基本スタイルは .form-input を継承 */
}
```

**HTML例**

```html
<!-- HTML5 日付入力 -->
<div class="form-group">
  <label for="startDate" class="form-label">開始日</label>
  <input
    type="date"
    id="startDate"
    class="form-input"
    value="2025-11-11"
  >
</div>

<!-- 日時入力 -->
<div class="form-group">
  <label for="startDateTime" class="form-label">開始日時</label>
  <input
    type="datetime-local"
    id="startDateTime"
    class="form-input"
  >
</div>
```

---

### テーブル表示

#### 基本仕様

**CSS定義（table.css）**

```css
/* テーブルコンテナ */
.table-container {
  overflow-x: auto;
  box-shadow: var(--shadow-md);
  border-radius: var(--border-radius-base);
  margin-bottom: var(--spacing-4);
}

/* テーブル */
.table {
  width: 100%;
  min-width: 1200px;
  border-collapse: collapse;
  background-color: var(--color-white);
}

/* テーブルヘッダー */
.table__head {
  background-color: var(--color-table-header);
}

.table__head th {
  padding: var(--spacing-3) var(--spacing-2);
  text-align: left;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-700);
  border-bottom: var(--border-width) solid var(--color-border);
}

/* テーブルボディ */
.table__body tr {
  height: 48px;
  border-bottom: var(--border-width) solid var(--color-border);
  transition: background-color var(--transition-base);
}

/* ホバー効果 */
.table__body tr:hover {
  background-color: var(--color-table-header);
}

.table__body td {
  padding: var(--spacing-2);
  font-size: var(--font-size-base);
  color: var(--color-gray-900);
}

/* カラム幅指定 */
.table colgroup col:nth-child(1) { width: 24px; }    /* チェックボックス */
.table colgroup col:nth-child(2) { width: 80px; }    /* ID */
.table colgroup col:nth-child(3) { width: 20%; }     /* 名前 */
.table colgroup col:nth-child(4) { width: 25%; }     /* メール */
.table colgroup col:nth-child(5) { width: 15%; }     /* ステータス */
.table colgroup col:nth-child(6) { width: 120px; }   /* 日付 */
.table colgroup col:nth-child(7) { width: 150px; }   /* アクション */

/* チェックボックス */
.table__checkbox {
  text-align: center;
}

.table__checkbox-input {
  width: 16px;
  height: 16px;
  vertical-align: middle;
  cursor: pointer;
  accent-color: var(--color-primary);
}

/* バッジ */
.table__badge {
  display: inline-block;
  padding: var(--spacing-1) var(--spacing-2);
  font-size: var(--font-size-base);
  border-radius: var(--border-radius-base);
  background-color: var(--color-gray-200);
  color: var(--color-gray-700);
}

.table__badge--success {
  background-color: var(--color-success-light);
  color: var(--color-success);
}

.table__badge--danger {
  background-color: var(--color-danger-light);
  color: var(--color-danger);
}

/* アクションボタン */
.table__actions {
  display: flex;
  gap: var(--spacing-2);
}

.table__action-btn {
  background-color: var(--color-primary);
  border: none;
  border-radius: var(--border-radius-base);
  color: var(--color-white);
  font-size: var(--font-size-base);
  cursor: pointer;
  text-decoration: none;
  padding: var(--spacing-2) var(--spacing-3);
  transition: all var(--transition-base);
}

.table__action-btn:hover {
  background-color: var(--color-primary-hover);
}

/* テキストの切り詰め */
.table__truncate {
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
```

**HTML例**

```html
<div class="table-container">
  <table class="table" aria-label="ユーザ一覧">
    <colgroup>
      <col>
      <col>
      <col>
      <col>
      <col>
      <col>
      <col>
    </colgroup>
    <thead class="table__head">
      <tr>
        <th scope="col"></th>
        <th scope="col">ID</th>
        <th scope="col">ユーザ名</th>
        <th scope="col">メールアドレス</th>
        <th scope="col">ステータス</th>
        <th scope="col">最終ログイン</th>
        <th scope="col">アクション</th>
      </tr>
    </thead>
    <tbody class="table__body">
      <tr>
        <td>
          <div class="table__checkbox">
            <input type="checkbox" id="isDelete" class="table__checkbox-input" checked>
          </div>
        </td>
        <td>001</td>
        <td>
          山田太郎
        </td>
        <td>yamada@example.com</td>
        <td>
          <span class="table__badge table__badge--success">アクティブ</span>
        </td>
        <td>2025/11/01 10:30</td>
        <td>
          <div class="table__actions">
            <button class="table__action-btn">参照</button>
            <button class="table__action-btn">更新</button>
          </div>
        </td>
      </tr>
      <tr>
        <td>
          <div class="table__checkbox">
            <input type="checkbox" id="isDelete" class="table__checkbox-input">
          </div>
        </td>
        <td>002</td>
        <td>
          佐藤花子
        </td>
        <td>sato@example.com</td>
        <td>
          <span class="table__badge table__badge--danger">ロック済み</span>
        </td>
        <td>2025/10/30 15:20</td>
        <td>
          <div class="table__actions">
            <button class="table__action-btn">参照</button>
            <button class="table__action-btn">更新</button>
          </div>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

---

### ページネーション

#### UI仕様

**CSS定義（pagination.css）**

```css
/* ページネーション */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing-2);
  margin-top: var(--spacing-4);
}

/* ページボタン */
.pagination__button {
  min-width: 40px;
  height: 40px;
  padding: var(--spacing-2) var(--spacing-3);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--border-radius-base);
  background-color: var(--color-white);
  color: var(--color-gray-700);
  cursor: pointer;
  transition: all var(--transition-base);
}

.pagination__button:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.pagination__button:hover:disabled {
  cursor: not-allowed;
  color: var(--color-gray-600);
}

.pagination__button--active {
  background-color: var(--color-brand-blue);
  border-color: var(--color-primary);
}

.pagination__button--active:hover {
  background-color: var(--color-brand-blue);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.pagination__ellipsis {
  padding: var(--spacing-2) var(--spacing-3);
  color: var(--color-gray-600);
}
```

**HTML例**

```html
<!-- 基本的なページネーション -->
<nav class="pagination" aria-label="ページネーション">
  <button class="pagination__button" disabled><</button>
  <button class="pagination__button pagination__button--active" aria-current="page">1</button>
  <button class="pagination__button">2</button>
  <button class="pagination__button">3</button>
  <span class="pagination__ellipsis">...</span>
  <button class="pagination__button">10</button>
  <button class="pagination__button">></button>
</nav>
```

#### 動作仕様

**本プロジェクトの方針:**
- サーバー側でページネーション処理を実施
- APIは初回に1ページ目のデータと全件のページ数を取得
- ページ切り替え時はAPIコール必要

**1ページあたりの表示件数:**

| 画面 | デフォルト件数 | 変更可能 |
|------|--------------|----------|
| 一覧画面 | 25件 | × 固定 |
| ダッシュボード | 25件 | × 固定 |

---

### ソート

#### UI仕様

**CSS定義（sort.css）**

```css
/* ソート可能ヘッダー */
.sort-button {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-1);
  background: transparent;
  border: none;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-700);
  cursor: pointer;
  padding: var(--spacing-1);
  transition: background-color var(--transition-base);
}

.sort-button:hover {
  background-color: var(--color-gray-200);
}

.sort-icon {
  width: 16px;
  height: 16px;
  color: var(--color-gray-600);
}

.sort-icon--active {
  color: var(--color-gray-900);
}
```

**HTML例**

```html
<table class="table">
  <thead class="table__head">
    <tr>
      <th>
        <button class="sort-button" onclick="sortTable('name')">
          ユーザ名
          <span class="sort-icon">⇅</span>
        </button>
      </th>
      <th>
        <button class="sort-button" onclick="sortTable('email')">
          メールアドレス
          <span class="sort-icon sort-icon--active">↑</span>
        </button>
      </th>
      <th>
        <button class="sort-button" onclick="sortTable('lastLogin')">
          最終ログイン
          <span class="sort-icon sort-icon--active">↓</span>
        </button>
      </th>
    </tr>
  </thead>
  <tbody class="table__body">
    <!-- データ行 -->
  </tbody>
</table>
```

#### 動作仕様

**本プロジェクトの方針:**
- 全件ソートと部分ソートの2種類実装
- 全件ソートは検索フォーム内のドロップダウンでソート条件を設定
- 部分ソートはデータテーブルのヘッダーをクリックすることでソート条件を設定（ソート範囲は現在表示されているページ内）
- 全件ソートはサーバー側、部分ソートはクライアント側でソート処理を実施
- APIは初回に全件データを取得
- 部分ソートのソート順変更時はAPIコール不要

**ソート順の切り替え:**
1. 初回クリック: 昇順（↑）
2. 2回目クリック: 降順（↓）
3. 3回目クリック: ソートなし
4. 4回目クリック: 昇順に戻る

---

### モーダル・ダイアログ

#### モーダル仕様

**CSS定義（modal.css）**

```css
/* モーダルオーバーレイ */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fade-in 0.2s ease-out;
}

@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* モーダル */
.modal {
  background-color: var(--color-white);
  border-radius: var(--border-radius-base);
  box-shadow: var(--shadow-lg);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  animation: slide-up 0.3s ease-out;
}

@keyframes slide-up {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* サイズバリエーション */
.modal--small {
  max-width: 400px;
}

.modal--medium {
  max-width: 600px;
}

.modal--large {
  max-width: 800px;
}

.modal--fullscreen {
  max-width: 90%;
  width: 90%;
}

/* モーダルヘッダー */
.modal__header {
  display: flex;
  flex-direction: column;
  align-items: left;
  justify-content: space-between;
  padding: var(--spacing-5);
}

.modal__header-group {
  display: flex;
  align-items: center;
  text-align: left;
}

.modal__icon {
  width: 40x;
  height: 40px;
}

.modal__title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-900);
  margin-left: var(--spacing-4);
}

.modal__description {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-medium);
  color: var(--color-gray-900);
  margin-top: var(--spacing-4);
}

.modal__description--error {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-medium);
  color: var(--color-danger);
  margin-top: var(--spacing-4);
}

/* モーダルボディ */
.modal__body {
  padding: var(--spacing-0) var(--spacing-5);
}

/* モーダルフッター */
.modal__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--spacing-0) var(--spacing-3);
  padding: var(--spacing-5);
}
```

**HTML例**

```html
<!-- 基本的なモーダル -->
<div class="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <div class="modal">
    <div class="modal__header">
      <div class="modal__header-group">
        <!-- アイコン -->
        <img class="modal__icon" src="">
        <h2 id="modal-title" class="modal__title">ユーザ登録</h2>
      </div>
      <h4 id="modal-description" class="modal__description">ユーザ情報を登録します。以下のフォームを入力してください。</h4>

      <!-- 入力エラー時のみ表示 -->
      <h4 id="modal-description--error" class="modal__description--error">入力内容にエラーがあります。</h4>
    </div>
    <div class="modal__body">
      <form>
        <div class="form-group">
          <label for="modalEmail" class="form-label">
            メールアドレス <span class="form-label__required">*</span>
          </label>
          <input type="email" id="modalEmail" class="form-input" required>
        </div>
        <div class="form-group">
          <label for="modalName" class="form-label">
            ユーザ名 <span class="form-label__required">*</span>
          </label>
          <input type="text" id="modalName" class="form-input" required>
        </div>
      </form>
    </div>
    <div class="modal__footer">
      <button class="button button--primary">登録</button>
      <button class="button button--secondary" onclick="closeModal()">キャンセル</button>
    </div>
  </div>
</div>
```

#### 確認ダイアログ

**HTML例**

```html
<!-- 削除確認ダイアログ -->
<div class="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
  <div class="modal modal--small">
    <div class="modal__header">
      <div class="modal__header-group">
        <!-- アイコン -->
        <img class="modal__icon" src="">
        <h2 id="confirm-title" class="modal__title">確認</h2>
      </div>
    </div>
    <div class="modal__body">
      <p>このユーザを削除してもよろしいですか？</p>
    </div>
    <div class="modal__footer">
      <button class="button button--danger">削除</button>
      <button class="button button--secondary" onclick="closeModal()">キャンセル</button>
    </div>
  </div>
</div>
```

**閉じる方法:**
- キャンセルボタン: `onclick`イベント
- ESCキー: JavaScriptでキーボードイベントハンドラー追加
- 背景クリック: オーバーレイの`onclick`イベント

---

## バリデーション

### クライアント側バリデーション

登録・更新の入力フォームで以下のバリデーションを実施（検索条件の入力フォームではバリデーションを実施しない）：

#### バリデーションルール

| バリデーション種別 | HTML属性 | JavaScriptチェック |
|-------------------|----------|---------------------|
| **必須チェック** | `required` | `input.value.trim() === ''` |
| **文字数チェック** | `minlength`, `maxlength` | `input.value.length < min \|\| input.value.length > max` |
| **メール形式** | `type="email"` | `/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value)` |
| **数値範囲** | `min`, `max` | `Number(input.value) < min \|\| Number(input.value) > max` |

#### バリデーションタイミング

| タイミング | 対象 | 動作 | 実装方法 |
|-----------|------|------|---------|
| **フォーカスアウト** | すべて | エラーがあれば表示 | JavaScript `blur`イベント |
| **送信ボタン押下** | すべて | エラーがあれば送信を中断、最初のエラーフィールドにフォーカス | JavaScript `submit`イベント |

#### 実装例

詳細は [JavaScriptインタラクション](#javascriptインタラクション) セクションを参照してください。

---

## エラーメッセージ表示

### エラーの種類と表示方法

| エラー種別 | 表示方法 | BEMクラス | 自動消去 |
|-----------|---------|-----------|---------|
| **バリデーションエラー** | インライン | `.form-error` | × 手動で修正 |
| **API呼び出しエラー（400系）** | インライン or バナー | `.alert--error` | × 手動で閉じる |
| **API呼び出しエラー（500系）** | バナー | `.alert--error` | × 手動で閉じる |
| **ネットワークエラー** | バナー | `.alert--error` | × 手動で閉じる |
| **成功メッセージ** | トースト | `.toast .alert--success` | x 手動で閉じる |

### エラーメッセージの文言

**基本方針:**
- ユーザーフレンドリーな表現
- 具体的な解決策を提示
- 専門用語を避ける

**例:**
- ❌ 悪い例: 「500 Internal Server Error」
- ✅ 良い例: 「サーバーエラーが発生しました。しばらく待ってから再度お試しください」

**詳細は各画面のUI仕様書の「表示メッセージ」セクションを参照してください。**

---

## ローディング表示

### ローディングの種類

| タイプ | 用途 | BEMクラス |
|--------|------|----------|
| **フルスクリーンローディング** | 画面全体の初期読み込み | `.loading-overlay` |
| **オーバーレイローディング** | モーダル内の処理 | `.loading-overlay` |
| **インラインローディング** | テーブルの再読み込み | `.spinner` |
| **ボタンローディング** | ボタン押下後の処理 | `.button--loading` |
| **スケルトンスクリーン** | 一覧のローディング | `.skeleton` |

### スピナーデザイン

**CSS定義（spinner.css）**

```css
/* スピナー */
.spinner {
  display: inline-block;
  width: 32px;
  height: 32px;
  border: 3px solid rgba(236, 111, 120, 0.3);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spinner-rotate 0.8s linear infinite;
}

@keyframes spinner-rotate {
  to {
    transform: rotate(360deg);
  }
}

/* サイズバリエーション */
.spinner--small {
  width: 20px;
  height: 20px;
  border-width: 2px;
}

.spinner--large {
  width: 48px;
  height: 48px;
  border-width: 4px;
}

/* フルスクリーンオーバーレイ */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-overlay .spinner {
  width: 48px;
  height: 48px;
  border-width: 4px;
  border-color: rgba(255, 255, 255, 0.3);
  border-top-color: var(--color-white);
}

/* ボタンローディング */
.button--loading {
  position: relative;
  pointer-events: none;
}

.button--loading .button__text {
  opacity: 0;
}

.button--loading::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: var(--color-white);
  border-radius: 50%;
  animation: spinner-rotate 0.8s linear infinite;
}
```

**HTML例**

```html
<!-- 基本的なスピナー -->
<div class="spinner" role="status">
  <span class="sr-only">読み込み中...</span>
</div>

<!-- フルスクリーンローディング -->
<div class="loading-overlay">
  <div class="spinner spinner--large"></div>
</div>

<!-- ボタンローディング -->
<button class="button button--primary button--loading" disabled>
  <span class="button__text">処理中...</span>
</button>
```

---

## アクセシビリティ

### WCAG 2.1 レベル AA 準拠

すべての画面で以下の要件を満たしてください。

### キーボード操作

**必須対応:**
- すべてのインタラクティブ要素はキーボードで操作可能
- タブ順序は論理的（上から下、左から右）
- フォーカスインジケーターを明確に表示

**主要なキー:**

| キー | 動作 |
|------|------|
| Tab | 次の要素へフォーカス移動 |
| Shift + Tab | 前の要素へフォーカス移動 |
| Enter | ボタン押下、リンククリック |
| Space | チェックボックス/ラジオボタンの切り替え |
| Esc | モーダルを閉じる |
| ↑ / ↓ | ドロップダウンの選択肢移動 |

### スクリーンリーダー対応

**必須のaria属性:**

| 要素 | aria属性 | 実装例 |
|------|---------|--------|
| ボタン | `aria-label` | `<button aria-label="閉じる">` |
| フォーム | `role="form"`, `aria-label` | `<form aria-label="ユーザ検索">` |
| エラーメッセージ | `role="alert"`, `aria-live="assertive"` | `<div class="alert" role="alert">` |
| ローディング | `aria-busy="true"`, `aria-live="polite"` | `<div class="spinner" role="status">` |
| モーダル | `role="dialog"`, `aria-modal="true"` | `<div class="modal-overlay" role="dialog" aria-modal="true">` |
| テーブル | `aria-label` | `<table aria-label="ユーザ一覧">` |

**スクリーンリーダー専用テキスト:**

```css
/* CSS定義 */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

```html
<!-- HTML使用例 -->
<div class="spinner" role="status">
  <span class="sr-only">読み込み中...</span>
</div>
```

### 色とコントラスト

**要件:**
- テキストと背景のコントラスト比: 最低 4.5:1
- ボタンと背景のコントラスト比: 最低 3:1
- エラーメッセージ: 色だけでなくアイコンも併用
- フォーカス表示: `box-shadow: 0 0 0 2px var(--color-focus-shadow)`

### フォーカス表示

すべてのインタラクティブ要素に`:focus`スタイルを定義：

```css
/* 共通フォーカススタイル */
.button:focus,
.form-input:focus,
.form-select:focus,
.form-option__input:focus {
  outline: none;
  box-shadow: 0 0 0 2px var(--color-focus-shadow);
}
```

---

## レスポンシブデザイン

### ブレークポイント

```css
/* CSS変数定義 */
:root {
  --breakpoint-xs: 575px;
  --breakpoint-sm: 576px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 992px;
  --breakpoint-xl: 1200px;
  --breakpoint-xxl: 1400px;
}
```

| サイズ | 幅 | メディアクエリ | 対象デバイス |
|--------|-----|--------------|-------------|
| **Extra small (xs)** | 〜575px | `@media (max-width: 575px)` | スマートフォン |
| **Small (sm)** | 576px〜767px | `@media (min-width: 576px)` | 大型スマートフォン |
| **Medium (md)** | 768px〜991px | `@media (min-width: 768px)` | タブレット |
| **Large (lg)** | 992px〜1199px | `@media (min-width: 992px)` | ノートPC |
| **Extra large (xl)** | 1200px〜1399px | `@media (min-width: 1200px)` | デスクトップPC |
| **XXL** | 1400px〜 | `@media (min-width: 1400px)` | 大画面デスクトップ |

### レスポンシブ対応

**本プロジェクトの方針:**
- デスクトップファースト（主要ユーザーはデスクトップ）
- モバイル対応は必須ではないが、タブレット対応は推奨

**推奨対応:**

```css
/* テーブル: 横スクロール（モバイル）、全表示（デスクトップ） */
.table-container {
  overflow-x: auto;
}

/* フォーム: 縦並び（モバイル）、横並び（デスクトップ） */
.form-row {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

@media (min-width: 768px) {
  .form-row {
    flex-direction: row;
  }

  .form-row > * {
    flex: 1;
  }
}

/* ボタン: モバイルでフル幅、デスクトップで自動幅 */
.button {
  width: 100%;
}

@media (min-width: 768px) {
  .button {
    width: auto;
  }
}
```

---

## ブラウザサポート

### 対応ブラウザ

| ブラウザ | 最小バージョン |
|---------|--------------|
| Google Chrome | 最新版 ||

### 推奨環境

- 画面解像度: 1920×1080 以上
- JavaScript: 有効
- Cookie: 有効

---

## 画面遷移

### 遷移方法

| 遷移元 | 遷移先 | 方法 |
|--------|--------|------|
| グローバルメニュー | 各画面 | グローバルメニューをクリック |

### 状態の保持

**検索条件の保持:**
- セッションストレージに保存
- 別画面からグローバルメニューで戻る際に復元
- ブラウザバック時も復元

```javascript
// 検索条件を保存
sessionStorage.setItem('searchParams', JSON.stringify({ keyword: '山田', role: 'admin' }));

// 検索条件を復元
const searchParams = JSON.parse(sessionStorage.getItem('searchParams') || '{}');
```

### 確認ダイアログ

**未保存の変更がある場合:**
- 画面遷移時に確認ダイアログを表示
- 「変更内容が保存されていません。このページを離れてもよろしいですか?」

---

## JavaScriptインタラクション

### フォームバリデーション

**validation.js**

```javascript
// フォームバリデーション
class FormValidator {
  constructor(form) {
    this.form = form;
    this.inputs = form.querySelectorAll('input[required], select[required]');
    this.init();
  }

  init() {
    // フォーカスアウト時のバリデーション
    this.inputs.forEach(input => {
      input.addEventListener('blur', () => this.validateField(input));
    });

    // サブミット時のバリデーション
    this.form.addEventListener('submit', (e) => this.validateForm(e));
  }

  validateField(input) {
    const errorElement = document.getElementById(`${input.id}-error`);
    const error = this.getErrorMessage(input);

    if (error) {
      input.classList.add('form-input--error');
      input.classList.remove('form-input--valid');
      if (errorElement) {
        errorElement.textContent = error;
        errorElement.style.display = 'flex';
      }
      input.setAttribute('aria-invalid', 'true');
      return false;
    } else {
      input.classList.remove('form-input--error');
      input.classList.add('form-input--valid');
      if (errorElement) {
        errorElement.style.display = 'none';
      }
      input.setAttribute('aria-invalid', 'false');
      return true;
    }
  }

  getErrorMessage(input) {
    if (input.validity.valueMissing) {
      return `${input.labels[0]?.textContent || 'この項目'}を入力してください`;
    }
    if (input.validity.typeMismatch) {
      if (input.type === 'email') {
        return '有効なメールアドレスを入力してください';
      }
    }
    if (input.validity.tooShort) {
      return `${input.minLength}文字以上で入力してください`;
    }
    if (input.validity.tooLong) {
      return `${input.maxLength}文字以内で入力してください`;
    }
    if (input.validity.rangeUnderflow) {
      return `${input.min}以上の値を入力してください`;
    }
    if (input.validity.rangeOverflow) {
      return `${input.max}以下の値を入力してください`;
    }
    return '';
  }

  validateForm(e) {
    let isValid = true;
    let firstInvalid = null;

    this.inputs.forEach(input => {
      if (!this.validateField(input)) {
        isValid = false;
        if (!firstInvalid) {
          firstInvalid = input;
        }
      }
    });

    if (!isValid) {
      e.preventDefault();
      if (firstInvalid) {
        firstInvalid.focus();
      }
    }
  }
}

// 使用例
document.addEventListener('DOMContentLoaded', () => {
  const forms = document.querySelectorAll('form[data-validate]');
  forms.forEach(form => new FormValidator(form));
});
```

### モーダル操作

**modal.js**

```javascript
// モーダル管理
class Modal {
  constructor(modalId) {
    this.modal = document.getElementById(modalId);
    this.overlay = this.modal?.closest('.modal-overlay');
    this.init();
  }

  init() {
    if (!this.overlay) return;

    // 背景クリックで閉じる
    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay) {
        this.close();
      }
    });

    // ESCキーで閉じる
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen()) {
        this.close();
      }
    });

    // 閉じるボタン
    const closeButtons = this.overlay.querySelectorAll('.modal__close');
    closeButtons.forEach(btn => {
      btn.addEventListener('click', () => this.close());
    });
  }

  open() {
    this.overlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    // 最初のフォーカス可能な要素にフォーカス
    const firstInput = this.modal.querySelector('input, button, select, textarea');
    if (firstInput) {
      setTimeout(() => firstInput.focus(), 100);
    }
  }

  close() {
    this.overlay.style.display = 'none';
    document.body.style.overflow = '';
  }

  isOpen() {
    return this.overlay.style.display === 'flex';
  }
}

// 使用例
const userModal = new Modal('userModal');

// モーダルを開く
function openUserModal() {
  userModal.open();
}

// モーダルを閉じる
function closeUserModal() {
  userModal.close();
}
```

### トースト通知

**toast.js**

```javascript
// トースト通知
class Toast {
  constructor(container = 'toast-container') {
    this.container = document.getElementById(container);
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = container;
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }
  }

  show(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `alert alert--${type} toast`;
    toast.setAttribute('role', 'alert');

    const icons = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ℹ'
    };

    toast.innerHTML = `
      <span class="alert__icon">${icons[type]}</span>
      <p class="alert__message">${message}</p>
    `;

    this.container.appendChild(toast);

    // 自動削除
    setTimeout(() => {
      toast.classList.add('toast--fade-out');
      setTimeout(() => {
        toast.remove();
      }, 300);
    }, duration);
  }

  success(message, duration) {
    this.show(message, 'success', duration);
  }

  error(message, duration) {
    this.show(message, 'error', duration);
  }

  warning(message, duration) {
    this.show(message, 'warning', duration);
  }

  info(message, duration) {
    this.show(message, 'info', duration);
  }
}

// 使用例
const toast = new Toast();
toast.success('保存しました');
toast.error('エラーが発生しました');
```

### テーブルソート

**sort.js**

```javascript
// テーブルソート
class TableSort {
  constructor(tableId) {
    this.table = document.getElementById(tableId);
    this.tbody = this.table.querySelector('.table__body');
    this.sortState = {};
    this.init();
  }

  init() {
    const sortButtons = this.table.querySelectorAll('.sort-button');
    sortButtons.forEach(button => {
      button.addEventListener('click', (e) => {
        const column = button.dataset.column;
        this.sort(column);
        this.updateSortIcons(button);
      });
    });
  }

  sort(column) {
    const rows = Array.from(this.tbody.querySelectorAll('tr'));
    const currentOrder = this.sortState[column] || 'none';
    const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';

    rows.sort((a, b) => {
      const aValue = a.querySelector(`[data-column="${column}"]`)?.textContent || '';
      const bValue = b.querySelector(`[data-column="${column}"]`)?.textContent || '';

      if (newOrder === 'asc') {
        return aValue.localeCompare(bValue, 'ja');
      } else {
        return bValue.localeCompare(aValue, 'ja');
      }
    });

    // テーブルを再構築
    this.tbody.innerHTML = '';
    rows.forEach(row => this.tbody.appendChild(row));

    this.sortState[column] = newOrder;
  }

  updateSortIcons(activeButton) {
    // すべてのアイコンをリセット
    const allIcons = this.table.querySelectorAll('.sort-icon');
    allIcons.forEach(icon => {
      icon.textContent = '⇅';
      icon.classList.remove('sort-icon--active');
    });

    // アクティブなアイコンを更新
    const icon = activeButton.querySelector('.sort-icon');
    const column = activeButton.dataset.column;
    const order = this.sortState[column];

    if (order === 'asc') {
      icon.textContent = '↑';
    } else if (order === 'desc') {
      icon.textContent = '↓';
    }
    icon.classList.add('sort-icon--active');
  }
}

// 使用例
const userTable = new TableSort('userTable');
```

### ページネーション

**pagination.js**

```javascript
// ページネーション
class Pagination {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    this.currentPage = options.currentPage || 1;
    this.totalPages = options.totalPages || 1;
    this.itemsPerPage = options.itemsPerPage || 20;
    this.totalItems = options.totalItems || 0;
    this.onPageChange = options.onPageChange || (() => {});
    this.render();
  }

  render() {
    const pages = this.getPageNumbers();
    const startItem = (this.currentPage - 1) * this.itemsPerPage + 1;
    const endItem = Math.min(this.currentPage * this.itemsPerPage, this.totalItems);

    this.container.innerHTML = `
      <div class="pagination-wrapper">
        <div class="pagination-info">
          全 ${this.totalItems} 件中 ${startItem}-${endItem} 件目
        </div>
        <nav class="pagination" aria-label="ページネーション">
          <button class="pagination__button" ${this.currentPage === 1 ? 'disabled' : ''}
                  onclick="pagination.goToPage(${this.currentPage - 1})">
            前へ
          </button>
          ${pages.map(page => {
            if (page === '...') {
              return `<span class="pagination__ellipsis">...</span>`;
            }
            return `
              <button class="pagination__button ${page === this.currentPage ? 'pagination__button--active' : ''}"
                      onclick="pagination.goToPage(${page})"
                      ${page === this.currentPage ? 'aria-current="page"' : ''}>
                ${page}
              </button>
            `;
          }).join('')}
          <button class="pagination__button" ${this.currentPage === this.totalPages ? 'disabled' : ''}
                  onclick="pagination.goToPage(${this.currentPage + 1})">
            次へ
          </button>
        </nav>
      </div>
    `;
  }

  getPageNumbers() {
    const pages = [];
    const maxVisible = 5;

    if (this.totalPages <= maxVisible) {
      for (let i = 1; i <= this.totalPages; i++) {
        pages.push(i);
      }
    } else {
      pages.push(1);
      if (this.currentPage > 3) pages.push('...');

      const start = Math.max(2, this.currentPage - 1);
      const end = Math.min(this.totalPages - 1, this.currentPage + 1);

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      if (this.currentPage < this.totalPages - 2) pages.push('...');
      pages.push(this.totalPages);
    }

    return pages;
  }

  goToPage(page) {
    if (page < 1 || page > this.totalPages || page === this.currentPage) return;
    this.currentPage = page;
    this.render();
    this.onPageChange(page);
  }

  update(options) {
    Object.assign(this, options);
    this.render();
  }
}

// 使用例
const pagination = new Pagination('paginationContainer', {
  currentPage: 1,
  totalPages: 10,
  totalItems: 200,
  itemsPerPage: 20,
  onPageChange: (page) => {
    console.log('Page changed to:', page);
    // データを取得して表示を更新
  }
});
```

---

## 関連ドキュメント

### 機能設計・仕様

- [共通仕様書](./common-specification.md) - HTTPステータスコード、エラーコード、トランザクション管理、セキュリティ等
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
- [データベース設計](../../01-architecture/database.md) - OLTP DB/Unity Catalog設計
- [インフラストラクチャ設計](../../01-architecture/infrastructure.md)

### データベース

- [データベース設計書](../../01-architecture/database.md) - テーブル定義、インデックス設計、データスコープ制限

### テスト仕様

- [テスト仕様書](../../06-testing/) - 単体テスト・結合テスト・E2Eテスト

### 外部リソース

- [MDN Web Docs - HTML](https://developer.mozilla.org/ja/docs/Web/HTML)
- [MDN Web Docs - CSS](https://developer.mozilla.org/ja/docs/Web/CSS)
- [BEM Methodology](https://en.bem.info/methodology/)
- [WCAG 2.1 ガイドライン](https://www.w3.org/WAI/WCAG21/quickref/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)

---

**このUI共通仕様（HTML + CSS版）は、すべての画面で適用してください。**
