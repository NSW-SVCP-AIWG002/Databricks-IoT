# テスト項目書：alert_history_service

**対象ファイル：** `src/iot_app/services/alert_history_service.py`
**テストコード：** `tests/unit/services/test_alert_history_service.py`
**テスト件数：** 68件

---

## get_default_search_params

**概要：** アラート履歴一覧検索のデフォルト検索パラメータを生成して返す。初期表示時に使用し、期間は現在日から過去7日間、ソート項目はアラート発生日時（sort_item_id=1）、ソート順は降順（sort_order_id=2）を初期値とする。

| No | 観点 | 手順 | 想定結果 |
|---|---|---|---|
| 1 | 戻り値の型 | `get_default_search_params()` を呼び出す | `dict` 型が返される |
| 2 | 必須キーの存在 | `get_default_search_params()` を呼び出す | `page`, `per_page`, `sort_item_id`, `sort_order_id`, `start_datetime`, `end_datetime`, `device_name`, `device_location`, `alert_name`, `alert_level_id`, `alert_status_id` がすべて含まれる |
| 3 | 開始日時の初期値 | `get_default_search_params()` を呼び出す | `start_datetime` が現在日から7日前の `00:00` である |
| 4 | 終了日時の初期値 | `get_default_search_params()` を呼び出す | `end_datetime` が当日の `23:59` である |
| 5 | ソート項目の初期値 | `get_default_search_params()` を呼び出す | `sort_item_id` が `1`（アラート発生日時）である |
| 6 | ソート順の初期値 | `get_default_search_params()` を呼び出す | `sort_order_id` が `2`（降順）である |
| 7 | アラートレベルの初期値 | `get_default_search_params()` を呼び出す | `alert_level_id` が `None`（すべて）である |
| 8 | ステータスの初期値 | `get_default_search_params()` を呼び出す | `alert_status_id` が `None`（すべて）である |
| 9 | 1ページ表示件数の初期値 | `get_default_search_params()` を呼び出す | `per_page` が `25` である |
| 10 | ページ番号の初期値 | `get_default_search_params()` を呼び出す | `page` が `1` である |
| 11 | テキスト検索項目の初期値 | `get_default_search_params()` を呼び出す | `device_name`, `device_location`, `alert_name` がすべて空文字 `''` である |

---

## search_alert_histories — データスコープ制御

**概要：** アラート履歴一覧を検索し、`(alert_histories, total)` のタプルを返す。`v_alert_history_by_user` VIEW に `user_id` を渡すことでデータスコープを制限する。VIEW 内部で `organization_closure` を参照するため、アプリ側では `user_id` フィルタと `delete_flag=False` フィルタのみ適用する。各種検索条件・ソート・ページネーションに対応する。

| No | 観点 | 手順 | 想定結果 |
|---|---|---|---|
| 12 | user_id フィルタの適用 | `user_id=10` でデフォルト検索条件を使い `search_alert_histories()` を呼び出す | `db.session.query().filter()` が呼ばれ、user_id によるスコープ制限が適用される |
| 13 | 論理削除レコードの除外 | デフォルト検索条件で `search_alert_histories()` を呼び出す | `delete_flag=False` フィルタが適用される（`filter()` が1回以上呼ばれる） |
| 14 | スコープ外ユーザーの場合 | `user_id=99`（スコープ外）、件数0件をモックして検索する | 戻り値が `([], 0)` である |
| 15 | 問い合わせ先VIEWの確認 | デフォルト検索条件で `search_alert_histories()` を呼び出す | `db.session.query()` の呼び出し先が `AlertHistoryByUser`（VIEW）のみである |

---

## search_alert_histories — 検索条件の適用

| No | 観点 | 手順 | 想定結果 |
|---|---|---|---|
| 16 | 期間検索（BETWEEN） | `start_datetime='2026/01/01 00:00'`, `end_datetime='2026/01/07 23:59'` を指定して検索する | BETWEEN フィルタが適用される（`filter()` が呼ばれる） |
| 17 | 期間未指定の場合 | `start_datetime=None`, `end_datetime=None` で検索する | BETWEEN フィルタが追加されない（期間指定ありより `filter()` 呼び出し回数が少ない） |
| 17-1 | 片方のみの期間指定でBETWEENフィルタ非適用 | `start_datetime` のみ指定・`end_datetime` のみ指定・両方指定・両方 None の4パターンで検索する | 片方のみ指定の場合は BETWEEN フィルタが追加されず、両方 None と同じ `filter()` 呼び出し回数である |
| 18 | デバイス名の部分一致 | `device_name='センサー'` を指定して検索する | device_name 部分一致フィルタが適用される |
| 19 | 設置場所の部分一致 | `device_location='東京'` を指定して検索する | device_location 部分一致フィルタが適用される |
| 20 | アラート名の部分一致 | `alert_name='温度'` を指定して検索する | alert_name 部分一致フィルタが適用される |
| 21 | アラートレベルの完全一致 | `alert_level_id=2` を指定して検索する | alert_level_id 完全一致フィルタが適用される |
| 22 | ステータスの完全一致 | `alert_status_id=1` を指定して検索する | alert_status_id 完全一致フィルタが適用される |
| 23 | 複数条件のAND結合 | `device_name`, `alert_level_id`, `alert_status_id` を同時に指定して検索する | 条件なしより `filter()` 呼び出し回数が多い（AND 結合で複数フィルタが追加される） |
| 24 | OR条件の不使用 | `device_name`, `alert_name` を指定して検索する | `sqlalchemy.or_` が呼ばれない |
| 25 | アラートレベル「すべて」の検索結果 | `alert_level_id=None` で検索し、Critical/Warning/Info の3件をモックする | 全レベル（Critical, Warning, Info）のアラートが返される |
| 26 | アラートレベルNoneのフィルタ数 | `alert_level_id=None` と `alert_level_id=2` でそれぞれ検索する | None の場合は具体値指定よりフィルタ呼び出し回数が少ない |
| 27 | ステータス「すべて」の検索結果 | `alert_status_id=None` で検索し、発生中/復旧済みの2件をモックする | 全ステータス（発生中、復旧済み）のアラートが返される |
| 28 | ステータスNoneのフィルタ数 | `alert_status_id=None` と `alert_status_id=1` でそれぞれ検索する | None の場合は具体値指定よりフィルタ呼び出し回数が少ない |
| 29 | 全条件未指定（全件相当） | 全検索条件を None に設定して検索した場合と条件指定ありで検索した場合を比較する | 全条件 None の場合は条件指定ありより `filter()` 呼び出し回数が少ない（基底フィルタのみ） |
| 30 | 空文字テキストフィールドのフィルタ非適用 | `device_name=''` / `device_name=None` / `device_name='センサー'` でそれぞれ検索する | 空文字と None は同じフィルタ呼び出し回数（フィルタ非適用）、具体値指定の場合はフィルタが追加される |

---

## search_alert_histories — ソート

| No | 観点 | 手順 | 想定結果 |
|---|---|---|---|
| 31 | 降順ソート | `sort_item_id=1, sort_order_id=2`（降順）で検索する | `order_by()` が呼ばれる |
| 32 | 昇順ソート | `sort_item_id=1, sort_order_id=1`（昇順）で検索する | `order_by()` が呼ばれる |
| 32-1 | sort_order_id=-1（指定なし）の場合 | `sort_item_id=1, sort_order_id=-1` で検索する | `order_by()` が呼ばれない（ORDER BY が適用されない） |
| 33-1 | ソート項目：sort_item_id=2（device_name） | `sort_item_id=2` で検索する | `order_by()` が呼ばれる |
| 33-2 | ソート項目：sort_item_id=3（device_location） | `sort_item_id=3` で検索する | `order_by()` が呼ばれる |
| 33-3 | ソート項目：sort_item_id=4（alert_name） | `sort_item_id=4` で検索する | `order_by()` が呼ばれる |
| 33-4 | ソート項目：sort_item_id=5（alert_level_id） | `sort_item_id=5` で検索する | `order_by()` が呼ばれる |
| 33-5 | ソート項目：sort_item_id=6（alert_status_id） | `sort_item_id=6` で検索する | `order_by()` が呼ばれる |
| 34-1 | ソート組み合わせ（sort_item_id=2/昇順） | `sort_item_id=2, sort_order_id=1` で検索する | `order_by()` が呼ばれ、`(list, int)` のタプルが返される |
| 34-2 | ソート組み合わせ（sort_item_id=2/降順） | `sort_item_id=2, sort_order_id=2` で検索する | `order_by()` が呼ばれ、`(list, int)` のタプルが返される |
| 34-3 | ソート組み合わせ（sort_item_id=3/昇順） | `sort_item_id=3, sort_order_id=1` で検索する | `order_by()` が呼ばれ、`(list, int)` のタプルが返される |
| 34-4 | ソート組み合わせ（sort_item_id=3/降順） | `sort_item_id=3, sort_order_id=2` で検索する | `order_by()` が呼ばれ、`(list, int)` のタプルが返される |
| 34-5 | ソート組み合わせ（sort_item_id=4/昇順） | `sort_item_id=4, sort_order_id=1` で検索する | `order_by()` が呼ばれ、`(list, int)` のタプルが返される |
| 34-6 | ソート組み合わせ（sort_item_id=1/昇順） | `sort_item_id=1, sort_order_id=1` で検索する | `order_by()` が呼ばれ、`(list, int)` のタプルが返される |
| 34-7 | ソート組み合わせ（sort_item_id=1/降順） | `sort_item_id=1, sort_order_id=2` で検索する | `order_by()` が呼ばれ、`(list, int)` のタプルが返される |
| 35 | 第二ソートキーの適用 | `sort_item_id=1, sort_order_id=2` で検索する | `order_by()` が主ソートキーと `alert_history_id` の2引数以上で呼ばれる |

---

## search_alert_histories — ページネーション

| No | 観点 | 手順 | 想定結果 |
|---|---|---|---|
| 36 | limit の値 | `page=1, per_page=25` で検索する | `limit(25)` が呼ばれる |
| 37 | page=1 の offset | `page=1, per_page=25` で検索する | `offset(0)` が呼ばれる |
| 38 | page=2 の offset | `page=2, per_page=25` で検索する | `offset(25)` が呼ばれる |
| 39 | page=3 の offset | `page=3, per_page=25` で検索する | `offset(50)` が呼ばれる |

---

## search_alert_histories — 戻り値

| No | 観点 | 手順 | 想定結果 |
|---|---|---|---|
| 40 | 戻り値の型 | 5件モックで `search_alert_histories()` を呼び出す | `(list, int)` のタプルが返される |
| 41 | total は全件数 | `page=2`（count=100件モック）で検索する | `total` が `100`（ページング後の件数ではなく全件数）である |
| 42 | 検索結果0件の戻り値 | count=0・results=[] のモックで検索する | `([], 0)` が返される |
| 43 | リスト内のオブジェクト | 1件モックで検索する | 戻り値リストにモックした `AlertHistoryByUser` オブジェクトが含まれ、`total=1` である |
| 44 | 最小構成の入力（2.1.2） | 全検索条件を None に設定した最小構成で `search_alert_histories()` を呼び出す | `list` と `int` のタプルが例外なく返される |
| 45 | 最大件数内の入力（2.1.3） | `per_page=25`（最大件数）で25件モックして検索する | `total=25`、リスト長が `25` である |
| 46 | 複数ページの全件数 | count=75・results=25件モック（page=1）で検索する | `total=75`、リスト長が `25` である |

---

## search_alert_histories — エラーハンドリング

| No | 観点 | 手順 | 想定結果 |
|---|---|---|---|
| 47 | DB例外の伝播 | `db.session.query()` が `SQLAlchemyError` を送出するようモックして `search_alert_histories()` を呼び出す | `SQLAlchemyError` が上位へ伝播される |

---

## get_alert_history_detail

**概要：** `alert_history_uuid` と `user_id` を条件に `v_alert_history_by_user` VIEW から1件取得する。該当なし・スコープ外・論理削除済みの場合は `None` を返す（呼び出し元で 404 ハンドリングを行う）。

| No | 観点 | 手順 | 想定結果 |
|---|---|---|---|
| 48 | UUID一致のレコード取得 | `alert_history_uuid='uuid-001'` のモックを用意して `get_alert_history_detail()` を呼び出す | 対応する `AlertHistoryByUser` オブジェクトが返される |
| 49 | user_id スコープの適用 | `user_id=10` で `get_alert_history_detail()` を呼び出す | `filter()` が呼ばれ user_id によるスコープ制限が適用される |
| 50 | 論理削除レコードの除外 | `get_alert_history_detail()` を呼び出す | `delete_flag=False` フィルタが適用される（`filter()` が1回以上呼ばれる） |
| 51 | 該当なしの場合 | 存在しない UUID で検索する（results=[] をモック） | `None` が返される |
| 52 | スコープ外ユーザーの場合 | 別ユーザーの `user_id=99` で検索する（results=[] をモック） | `None` が返される |
| 53 | 論理削除済みデータの場合 | `delete_flag=True` のレコードが除外されるよう results=[] をモックして検索する | `None` が返される |
| 54 | UUID フィルタの適用 | `alert_history_uuid='uuid-target'` で `get_alert_history_detail()` を呼び出す | `filter()` が呼ばれ UUID でフィルタされる |
| 55 | 問い合わせ先VIEWの確認 | `get_alert_history_detail()` を呼び出す | `db.session.query()` の呼び出し先が `AlertHistoryByUser`（VIEW）のみである |
| 56 | DB例外の伝播 | `db.session.query()` が `Exception("DB Timeout")` を送出するようモックして `get_alert_history_detail()` を呼び出す | `Exception("DB Timeout")` が上位へ伝播される |
