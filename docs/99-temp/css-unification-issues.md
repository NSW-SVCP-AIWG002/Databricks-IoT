# CSS共通化 課題一覧（一時資料）

> 作成日: 2026-04-10  
> 対象ブランチ: feature/css-unification  
> ステータス: 調査中

---

## UI共通設計書との照合結果

> 設計書: `docs/03-features/common/ui-common-specification.md`

### 設計書にあり・実装と不一致（要修正）⚠️

| 項目 | 設計書 | 実装 | ファイル |
|-----|--------|------|---------|
| ページネーションボタンサイズ | 40px | 20px | pagination.css |
| ページネーション上マージン | spacing-4 (16px) | spacing-2 (8px) | pagination.css |
| ページネーションのpadding | spacing変数 | 直書き `4px 6px` | pagination.css |
| モーダルタイトルフォントサイズ | font-size-2xl (24px) | font-size-lg (16px) | modal.css |
| トースト成功通知の色 | CSS変数想定 | ハードコード `#d4edda` など | toast.css |

### 設計書にあり・実装なし（未実装）❌

| 項目 | 対応ファイル |
|-----|------------|
| `--border-radius-sm` CSS変数（pagination.cssで参照中） | variables.css に追加が必要 |
| スケルトンスクリーン（`.skeleton`） | skeleton.css 新規作成 |
| モーダル確認ボタンクラス（`.modal__button--confirm/cancel`） | modal.css に追加 |

### 設計書の更新が必要なもの（実装が正しい）🔧

| 項目 | 状況 |
|-----|------|
| ~~モーダルヘッダーの背景色（プライマリカラー）~~ | ✅ モノトーン化済み（白背景＋ボーダー＋gray-900テキストに変更） |
| モーダル表示制御（JS側 `style.display` 方式） | 実装済み方式を設計書に明記すべき |
| チャット・業種別ダッシュボード等のCSS | 実装はあるが設計書に未記載 |

---

## 空CSSファイル

なし（全ファイルに内容あり）

---

## 課題一覧

### 優先度：高

---

#### [H-1] ハードコードカラー → CSS変数未使用

**✅ 完了（2026-04-13）** ※固有色（chat.css・spinner.css）は意図的放置

以下を CSS変数に置換済み：
- `#fff` → `--color-white`（modal.css, error.css, chat.css, common.css, belt/bar/timeline/circle_chart.css）
- `#2272B4` → `--color-primary`（chat.css）
- `#F44336` → `--color-danger`（chat.css）
- `#d4edda` / `#155724` → `--color-success-light` / `--color-success-dark`（toast.css, common.css）
- `#f8d7da` / `#721c24` → `--color-danger-light` / `--color-danger-dark`（common.css）
- `#e9ecef` → `--color-gray-200`（common.css）
- `#6c757d` → `--color-secondary`（common.css）
- `#ddd` / `#ccc` / `#eee`（ボーダー） → `--color-border`（common.css, modal.css, chat.css, belt/bar/timeline/circle_chart.css）
- テキスト色: `#333`→`--color-gray-800`、`#555`→`--color-gray-700`、`#666`→`--color-secondary`、`#aaa`/`#999`→`--color-gray-500`（common.css, error.css）
- toast: alert.css の設計に統一（`toast--error` を薄い背景＋フルカラーボーダーに変更、`toast--success` のボーダーを `--color-success` に変更）
- `.flash-messages` / `.flash--success` / `.flash--error` を削除（未使用コード）、対応テンプレートのブロックも削除

**残存：未定義カラー（変数化が必要）**

| ハードコード値 | 用途 | 主な出現ファイル |
|---|---|---|
| ~~`#f5f5f5`~~ | ~~薄いグレー背景~~ | ✅ `--color-gray-100` に置換済み（common.css, error.css） |
| ~~`#f0f0f0`~~ | ~~テーブルヘッダー背景等~~ | ✅ `--color-table-header` / `--color-gray-100` に置換済み（common.css） |
| ~~`#e8f0f8`~~ | ~~グループヘッダー背景（薄い青）~~ | ✅ `--color-brand-blue` に置換済み（common.css） |
| ~~`#e67e22`~~ | ~~編集モード用オレンジ~~ | ✅ `--color-warning` / `--color-warning-dark` に変更（バナーのみ、ツールバー背景変更は廃止） |
| ~~`#fdecea`~~ | ~~危険系薄い背景~~ | ✅ `--color-danger-light` に置換済み |
| ~~`#f9f9f9`~~ | ~~テーブル行ホバー~~ | ✅ `--color-gray-50` に置換済み |
| ~~chat.css置換済み~~ | ~~`#757575`→`--color-secondary`、`#F5F5F5`→`--color-gray-100`、`#212121`→`--color-gray-900`、`#e8e8e8`→`--color-gray-200`、`#BDBDBD`/`#E0E0E0`→`--color-border`~~ | ✅ 置換済み（chat.css） |
| chat.css固有色（放置） | `#E3EEF8`（テーブルヘッダー青）、`#F9FBFD`（偶数行薄青）、`#FFF9E6`/`#FFD54F`（HITL amber）、`#FFEBEE`/`#B71C1C`/`#EF9A9A`（エラー吹き出し）、`rgba(34,114,180,0.2)`（フォーカス） | chat.css — 変数と別値、放置 |
| ~~sidebar.css固有色~~ | ~~`#ecf0f1`, `#bdc3c7`~~ | ✅ `--color-gray-200` / `--color-gray-400` に置換済み（sidebar.css） |
| spinner.css固有色（放置） | `rgba(236,111,120,0.3)` 等 | spinner.css — 変数なし、放置 |

**ボーダー変数の照合結果：**

| 変数 | 定義値 | 実際の使用状況 |
|---|---|---|
| `--color-border: #CED4DA` | 定義済み | ✅ 置換完了（旧: `#ddd`/`#ccc`/`#eee` 直書き） |
| `--border-width: 1px` | 定義済み | ✅ 置換完了（H-2と同時対応、全対象ファイルの `1px solid var(--color-border)` を置換） |
| `--border-width-thick: 2px` | 定義済み | 使用実績ゼロ（定義のみ、放置） |
| `--border-radius-base: 4px` | 定義済み | ✅ 置換完了 → H-2 参照 |

---

#### [H-2] `border-radius: 4px` 直書き（24箇所）

**✅ 完了（2026-04-13）**

- `border-radius: 4px` → `var(--border-radius-base)`（common.css, modal.css, chat.css, belt/bar/timeline/circle_chart.css）
- `border-radius: 8px` → `var(--border-radius-lg)`（error.css, chat.css）
- `1px solid var(--color-border)` → `var(--border-width) solid var(--color-border)`（全対象ファイル）
- belt_chart.css の `1px solid #eee` 漏れも同時修正
- industry-dashboard.css の `1px solid var(--color-gray-300, #ccc)` も修正
- `border-radius: 2px`（棒グラフ先端）等、対応変数なしの値は放置

---

#### [H-3] ボタン・フォームの重複定義

**ボタン: ✅ 完了（2026-04-13）**

- `customer_dashboard/common.css` のボタン重複定義（旧行471-512）を削除
- `button.css` に以下を追加・修正して全体に適用：
  - `.button` に `white-space: nowrap` を追加
  - `.button--primary:hover` → `.button--primary:hover:not(:disabled)` に修正
- `font-family` は body から継承されるため不要と判断
- disabled の色指定（`#99c0e0`）は opacity: 0.5 で代替できるため不要と判断

**フォーム: ✅ 完了（2026-04-13）**

- `customer_dashboard/common.css` の `form__*` 定義ブロック全削除（9定義）
- `form.css` に `box-sizing: border-box` 追加（`form-input`）
- `bar_chart.css`, `timeline.css` の `form__*` セレクター → `form-*` 一括置換
- `belt_chart.css` の `.form__row--top` → `.form-row--top`
- テンプレート 12ファイルで `form__*` → `form-*` 一括置換
- 必須マーク: `form__label--required::after` 方式 → `<span class="form-label__required">必須</span>` バッジ方式に変更（全22箇所）
- エラー表示: `<ul class="form__errors"><li>` リスト構造 → `<span class="form-error">` 単一要素に変更（5テンプレート）

---

### 優先度：中

---

#### [M-1] BEM命名の不一致（ハイフン vs ダブルアンダースコア混在）

**✅ 完了（2026-04-13）** H-3フォーム統一作業で解消

- `.form-input`, `.form-label`, `.form-error`（ハイフン・設計書正）に統一済み
- `form__*`（アンダースコア）は全12テンプレート・3CSSファイルから削除済み

---

#### [M-2] インラインスタイルのクラス化漏れ

**対応不要（2026-04-13 クローズ）**

Jinja2条件分岐と一体・テーブル特定列幅など文脈が明確なため、クラス化による恩恵より複雑化のコストが上回ると判断。多様性として受け入れる。

---

#### [M-3] ボックスシャドウのハードコード

**✅ 完了（2026-04-13）**

- `modal.css` → `var(--shadow-lg)`（設計書準拠）
- `industry-dashboard.css` → 既に `var(--shadow-md)` 対応済み
- `sidebar.css` → 横方向シャドウで既存変数と別物のため放置

---

### 優先度：低

---

#### [L-1] CSS変数の定義不足（variables.css）

**✅ 完了（2026-04-13）**

- `--border-radius-sm` → `pagination.css` を設計書準拠の `--border-radius-base` に修正（変数追加不要）
- `--color-success-light` / `--color-success-dark` → `variables.css` 定義済み・`toast.css` も変数参照済みで問題なし
- `--shadow-md` / `--shadow-lg` → M-3 で対応済み
- `--color-link-hover` → どこからも参照なし・課題削除

---

#### [L-2] ボーダースタイルの不統一

**✅ 完了（2026-04-13）** H-1・H-2 で対応済み

- `1px solid #ddd` / `#ccc` / `#eee` → `var(--border-width) solid var(--color-border)` に全置換済み
- `chat.css` の `1px solid #FFD54F` / `#EF9A9A` は固有色につき意図的放置

---

## ファイル規模一覧（参考）

| 行数 | ファイル |
|-----|---------|
| 22 | main.css |
| 30 | components/sort.css |
| 44 | components/toast.css |
| 50 | components/error.css |
| 52 | components/spinner.css |
| 61 | components/alert.css |
| 69 | components/pagination.css |
| 101 | base.css |
| 123 | variables.css |
| 130 | components/button.css |
| 137 | components/sidebar.css |
| 138 | components/customer_dashboard/circle_chart.css |
| 138 | components/table.css |
| 200 | components/modal.css |
| 236 | components/form.css |
| 237 | components/customer_dashboard/belt_chart.css |
| 299 | components/chat.css |
| 328 | components/customer_dashboard/bar_chart.css |
| 389 | components/industry-dashboard.css |

---

## 対応方針メモ（未確定）

- `form-*` vs `form__*` の統一方針を決める（どちらに合わせるか）
- `variables.css` に不足変数を先に追加してから各CSSを修正する順序が安全
- インラインスタイルのクラス化は対応範囲をどこまでやるか要確認
