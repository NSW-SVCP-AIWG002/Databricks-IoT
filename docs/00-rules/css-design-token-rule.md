---
description: CSS変数によるデザイントークン管理ルール
globs:
  - app/static/css/**/*.css
alwaysApply: true
---

# CSS デザイントークン管理ルール

## デザイントークンの参照
**必ず `app/static/css/variables.css` のCSS変数（Custom Properties）を経由して値を参照してください。**

```css
/* variables.css で定義 */
:root {
  --color-primary: #1976d2;
  --font-size-md: 16px;
  --spacing-md: 16px;
}

/* 使用例 */
.button {
  background-color: var(--color-primary);
  font-size: var(--font-size-md);
  padding: var(--spacing-md);
}
```

## 禁止事項（絶対NG）
❌ **直接値指定は一切禁止**
- `color: #1976d2;`
- `font-size: 16px;`
- `padding: 16px;`

## 使用必須のトークンカテゴリ

### 色指定
```css
color: var(--text-primary);
background-color: var(--color-primary);
border-color: var(--border-color);
```

### フォントサイズ
```css
font-size: var(--font-size-sm);  /* 14px */
font-size: var(--font-size-md);  /* 16px */
font-size: var(--font-size-lg);  /* 18px */
```

### スペーシング
```css
padding: var(--spacing-sm);      /* 8px */
margin: var(--spacing-md);       /* 16px */
gap: var(--spacing-lg);          /* 24px */
```

### 角丸・影
```css
border-radius: var(--border-radius-md);
box-shadow: var(--shadow-sm);
```

## トークン追加ルール
- 新しい値が必要になった場合は `variables.css` にトークンを追加してから使用する。
- 追加時は既存のトークン命名規則に従う（例: `--color-*`, `--spacing-*`）。
- 同じ値の重複定義を避け、既存トークンで代用できないか確認する。

## コードレビュー基準
**実装時は以下を必ずチェック:**
1. CSS内に直接値（`#hex`, `px`値など）を指定していないか
2. `var(--*)` プレフィックスでトークンを参照しているか
3. 追加したトークンが `variables.css` に定義されているか
4. 未定義のトークンを参照していないか
