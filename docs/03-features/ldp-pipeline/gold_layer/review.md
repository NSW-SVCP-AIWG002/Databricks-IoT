# ゴールド層LDPパイプライン ドキュメントレビュー

- **レビュー対象:** `README.md` / `ldp-pipeline-specification.md`
- **レビュー日:** 2026-03-11
- **レビュアー:** Claude Code

---

## サマリ

| 重要度 | 件数 |
| ------ | ---- |
| 高     | 4    |
| 中     | 3    |
| 低     | 2    |
| **計** | **9** |

---

## 指摘一覧

### [HIGH-001] 機能ID `FR-002-2` がシルバー層で誤用されていた → 修正済み

**対象ファイル（修正済み）:** `silver-layer/README.md` L23 / `silver-layer/ldp-pipeline-specification.md` L116

**経緯:**

要件定義書（`functional-requirements.md` L915-934）での定義は以下の通り：

| 機能ID | 定義 | 正しい対応層 |
| --- | --- | --- |
| FR-002-1 | 構造化データ変換・保存処理（Event Hubs → シルバー層） | シルバー層 |
| FR-002-2 | 表示用データ変換・保存処理（シルバー層 → ゴールド層） | ゴールド層 |

ゴールド層の `FR-002-2` は要件定義書と一致しており正しい。誤りはシルバー層側にあった。

**修正内容:**

- `silver-layer/README.md`: `FR-002-2` → `FR-002-1`
- `silver-layer/ldp-pipeline-specification.md`: `FR-002-2` → `FR-002-1`

**ステータス:** 修正済み

---

### [HIGH-002] `dlt.read()` と通常 Spark ジョブの混在による実行環境の矛盾 → 修正済み

**対象ファイル（修正済み）:** `ldp-pipeline-specification.md` L690, L1111-1141, L1143-1219, L1291-1305

**修正内容:**
実行環境を**通常のDatabricksジョブ（Spark）** に統一した。

| 変更前 | 変更後 |
| --- | --- |
| `dlt.read("silver_sensor_data")` | `spark.table("iot_catalog.silver.silver_sensor_data")` |
| `import dlt` | 削除 |
| `@dlt.table(...)` デコレータ | 削除（通常の関数定義に変更） |
| `@dlt.expect_all(...)` デコレータ | 削除（Pythonフィルタによるバリデーションに変更） |
| `@dlt.table` 関数の戻り値として DataFrame を返す | `merge_to_gold()` を直接呼び出す形に変更 |
| 関数名 `gold_sensor_data_daily_summary()` | `run_daily_aggregation()` に変更 |

**ステータス:** 修正済み

---

### [HIGH-003] バリデーションフィルタ内で存在しないカラム `collection_date` を参照 → 修正済み

**対象ファイル（修正済み）:** `ldp-pipeline-specification.md`（HIGH-002対応時に同時解消）

**経緯:**
HIGH-002の修正（「例外処理実装例」セクションの書き直し）の際に、バリデーションフィルタを以下の通り修正した。

| 変更前 | 変更後 |
| --- | --- |
| `"AND collection_date IS NOT NULL "` | `"AND event_date IS NOT NULL"` |
| `"AND summary_item BETWEEN 1 AND 22"` | 削除（集計前のDataFrameに存在しないカラムのため除外） |

**ステータス:** 修正済み（HIGH-002対応時に同時解消）

---

### [HIGH-004] `schema` 変数が未定義のまま参照されている → 修正済み

**対象ファイル（修正済み）:** `ldp-pipeline-specification.md`（HIGH-002対応時に同時解消）

**経緯:**
HIGH-002の修正（`@dlt.table` デコレータ除去・関数をvoid型に変更）により、データなし時の処理が `return spark.createDataFrame([], schema)` から単純な `return` に変更された。通常のDatabricksジョブ（Spark）では関数がDataFrameを返す必要がないため、未定義の `schema` 変数を参照する箇所が消滅した。

**ステータス:** 修正済み（HIGH-002対応時に同時解消）

---

### [MED-001] 関数名の不統一（`perform_daily_aggregation` vs `aggregate_sensor_data`） → 修正済み

**対象ファイル（修正済み）:** `ldp-pipeline-specification.md`（HIGH-002対応時に同時解消）

**経緯:**
HIGH-002の修正（実装例セクションの書き直し）の際に、すべての呼び出し箇所を `aggregate_sensor_data(silver_df, config)` に統一した。`perform_daily_aggregation()` の記述は仕様書内に残存しない。

**ステータス:** 修正済み（HIGH-002対応時に同時解消）

---

### [MED-002] パフォーマンス要件「1分間隔」がゴールド層（日次バッチ）に不適切 → 修正済み

**対象ファイル（修正済み）:** `README.md` L238

**問題点:**
「1分間隔」はストリーミング処理（シルバー層）の送信頻度であり、ゴールド層の日次バッチ処理のスループット指標としては意味をなさない。シルバー層の値をそのまま転記したと考えられる。

**修正内容:**

| 変更前 | 変更後 |
| --- | --- |
| `10,000デバイス × 1分間隔` | `70,000デバイス分の日次データを1時間以内に集計完了` |
| `水平スケーリング、最適クラスタ構成` | `インクリメンタル処理、Liquid Clustering` |

**ステータス:** 修正済み

---

### [MED-003] `summary_value` のNULL制約とバリデーション記述が矛盾 → 修正済み

**対象ファイル（修正済み）:** `README.md` L54（日次）、L67（月次）、L80（年次）

**修正内容:**
センサー故障等でNULL値が発生し得る設計方針に統一し、3テーブルすべての `summary_value` を `NOT NULL` → `NULL` に変更した。

**ステータス:** 修正済み

---

### [LOW-001] 月次・年次の処理フロー図にバリデーションステップがない → 修正済み

**対象ファイル（修正済み）:** `ldp-pipeline-specification.md` 月次フロー図直後・年次フロー図直後

**修正内容:**
月次・年次の処理フロー図の直後に以下の注記を追加した。

> **注記:** バリデーション処理（device_id・organization_id・event_date の NOT NULL チェック）は共通集計処理内で日次と共通して実施します。

**ステータス:** 修正済み

---

### [LOW-002] `logger` の定義が `run_aggregation()` のコードブロック内に存在しない → 修正済み

**対象ファイル（修正済み）:** `ldp-pipeline-specification.md` 「集計処理の実行」セクション

**修正内容:**
`run_aggregation()` の定義直前に以下を追加した。

```python
import logging
logger = logging.getLogger(__name__)
```

**ステータス:** 修正済み

---

## 総評

ゴールド層パイプラインの仕様として、集計ロジックの共通化設計（`aggregate_sensor_data()`）やマスタテーブルによる集約方法の動的制御など、設計方針は適切である。

全9件の指摘事項について修正が完了した。
