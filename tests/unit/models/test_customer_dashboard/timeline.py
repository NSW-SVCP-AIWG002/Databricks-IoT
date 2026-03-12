"""
時系列グラフガジェット モデル層 単体テスト

対象モジュール: iot_app.models.dashboard
参照設計書:
  - docs/03-features/flask-app/customer-dashboard/timeline/workflow-specification.md
参照観点表: docs/06-testing/unit-test/unit-test-perspectives.md

【注意】
  モデルファイル (src/iot_app/models/dashboard.py) は未作成のため、
  本テストコードはワークフロー仕様書のテーブル定義に基づいて
  期待仕様を先行定義するTDDアプローチで作成しています。

  モデル実装時は以下のカラム定義を参照してください:
    dashboard_gadget_master:
      gadget_id (PK, INT, AUTO), gadget_uuid (VARCHAR 36, UNIQUE),
      gadget_name (VARCHAR 100), gadget_type_id (FK → gadget_type_master),
      dashboard_group_id (INT), chart_config (TEXT),
      data_source_config (TEXT), position_x (INT, default=0),
      position_y (INT, default=0), gadget_size (VARCHAR 10),
      display_order (INT, default=0), create_date (DATETIME),
      creator (INT), update_date (DATETIME), modifier (INT),
      delete_flag (BOOLEAN, default=False)

    gadget_type_master:
      gadget_type_id (PK, INT, AUTO), gadget_type_name (VARCHAR 100),
      delete_flag (BOOLEAN, default=False)
"""

import json

import pytest


# ============================================================
# TestDashboardGadgetMaster
# 観点: 2.1 正常系処理、2.3 副作用チェック
# ============================================================

@pytest.mark.unit
class TestDashboardGadgetMaster:
    """DashboardGadgetMaster モデルの単体テスト
    観点: 2.1 正常系処理、2.3 副作用チェック
    仕様: workflow-specification.md > ガジェット登録 > 処理詳細③
    """

    def _make_gadget(self, **overrides):
        """DashboardGadgetMaster インスタンスを生成するヘルパー"""
        from iot_app.models.dashboard import DashboardGadgetMaster
        defaults = dict(
            gadget_uuid='aaaaaaaa-0000-0000-0000-000000000001',
            gadget_name='時系列テスト',
            gadget_type_id=1,
            dashboard_group_id=1,
            chart_config=json.dumps({
                'left_item_id': 1,
                'right_item_id': 2,
                'left_min_value': None,
                'left_max_value': None,
                'right_min_value': None,
                'right_max_value': None,
            }),
            data_source_config=json.dumps({'device_id': 12345}),
            gadget_size='2x2',
            creator=1,
            modifier=1,
        )
        defaults.update(overrides)
        return DashboardGadgetMaster(**defaults)

    # ---- 正常系: インスタンス生成 (2.1.1) ----

    def test_instantiation_with_valid_params(self):
        """2.1.1: 有効なパラメータで DashboardGadgetMaster インスタンスが生成できる"""
        # Arrange / Act
        gadget = self._make_gadget()

        # Assert
        assert gadget.gadget_uuid        == 'aaaaaaaa-0000-0000-0000-000000000001'
        assert gadget.gadget_name        == '時系列テスト'
        assert gadget.gadget_type_id     == 1
        assert gadget.dashboard_group_id == 1

    # ---- delete_flag デフォルト値 (2.3.1) ----

    def test_delete_flag_default_is_false(self):
        """2.3.1: delete_flag のデフォルト値が False である
        仕様: dashboard_gadget_master.delete_flag = FALSE（INSERT時）"""
        # Arrange / Act
        gadget = self._make_gadget()

        # Assert
        assert gadget.delete_flag is False

    # ---- デフォルト値チェック (2.3.1) ----

    def test_position_x_default_is_zero(self):
        """2.3.1: position_x のデフォルト値が 0 である
        仕様: workflow-specification.md > ガジェット登録③ position_x=0"""
        # Arrange / Act（position_x を明示しない）
        gadget = self._make_gadget()

        # Assert
        # TODO: 実装時に要確認 — SQLAlchemy の Column(Integer, default=0) は
        #       DB INSERT 時のデフォルトであり、Python オブジェクト生成時点では
        #       None になる実装もある。モデル実装後に挙動を確認してテストを調整すること。
        assert gadget.position_x == 0

    def test_position_y_default_is_zero(self):
        """2.3.1: position_y のデフォルト値が 0 である
        仕様: dashboard_gadget_master.position_y default=0"""
        # Arrange / Act（position_y を明示しない）
        gadget = self._make_gadget()

        # Assert
        # TODO: 実装時に要確認 — SQLAlchemy の Column(Integer, default=0) は
        #       DB INSERT 時のデフォルトであり、Python オブジェクト生成時点では
        #       None になる実装もある。モデル実装後に挙動を確認してテストを調整すること。
        assert gadget.position_y == 0

    def test_display_order_default_is_zero(self):
        """2.3.1: display_order のデフォルト値が 0 である
        仕様: dashboard_gadget_master.display_order default=0"""
        # Arrange / Act（display_order を明示しない）
        gadget = self._make_gadget()

        # Assert
        # TODO: 実装時に要確認 — SQLAlchemy の Column(Integer, default=0) は
        #       DB INSERT 時のデフォルトであり、Python オブジェクト生成時点では
        #       None になる実装もある。モデル実装後に挙動を確認してテストを調整すること。
        assert gadget.display_order == 0

    # ---- chart_config JSON スキーマ (2.1.1) ----

    def test_chart_config_stores_left_right_item_ids(self):
        """2.1.1: chart_config に left_item_id / right_item_id が正しく格納される
        仕様: workflow-specification.md > chart_config JSONスキーマ"""
        # Arrange
        chart_config = {
            'left_item_id':  1,
            'right_item_id': 2,
            'left_min_value':  0.0,
            'left_max_value':  100.0,
            'right_min_value': 10.0,
            'right_max_value': 110.0,
        }
        gadget = self._make_gadget(chart_config=json.dumps(chart_config))

        # Act
        parsed = json.loads(gadget.chart_config)

        # Assert
        assert parsed['left_item_id']    == 1
        assert parsed['right_item_id']   == 2
        assert parsed['left_min_value']  == 0.0
        assert parsed['left_max_value']  == 100.0
        assert parsed['right_min_value'] == 10.0
        assert parsed['right_max_value'] == 110.0

    def test_chart_config_min_max_none_when_not_set(self):
        """2.1.2: min/max 未設定時は chart_config の各値が None になる
        仕様: ui-specification.md > 最小値/最大値（未入力時は自動スケール）"""
        # Arrange
        chart_config = {
            'left_item_id':    1,
            'right_item_id':   2,
            'left_min_value':  None,
            'left_max_value':  None,
            'right_min_value': None,
            'right_max_value': None,
        }
        gadget = self._make_gadget(chart_config=json.dumps(chart_config))

        # Act
        parsed = json.loads(gadget.chart_config)

        # Assert
        assert parsed['left_min_value']  is None
        assert parsed['left_max_value']  is None
        assert parsed['right_min_value'] is None
        assert parsed['right_max_value'] is None

    # ---- data_source_config JSON スキーマ (2.1.1) ----

    def test_data_source_config_fixed_mode_stores_device_id(self):
        """2.1.1: デバイス固定モード時、data_source_config に device_id が格納される
        仕様: workflow-specification.md > data_source_config（デバイス固定モード）"""
        # Arrange
        data_source_config = {'device_id': 12345}
        gadget = self._make_gadget(data_source_config=json.dumps(data_source_config))

        # Act
        parsed = json.loads(gadget.data_source_config)

        # Assert
        assert parsed['device_id'] == 12345

    def test_data_source_config_variable_mode_device_id_is_null(self):
        """2.1.1: デバイス可変モード時、data_source_config の device_id が null になる
        仕様: workflow-specification.md > data_source_config（デバイス可変モード）"""
        # Arrange
        data_source_config = {'device_id': None}
        gadget = self._make_gadget(data_source_config=json.dumps(data_source_config))

        # Act
        parsed = json.loads(gadget.data_source_config)

        # Assert
        assert parsed['device_id'] is None

    # ---- gadget_size 許容値 (1.1.6) ----

    def test_gadget_size_2x2_is_stored(self):
        """1.6.1: gadget_size に '2x2' が格納できる
        仕様: ui-specification.md > 部品サイズ 選択肢"""
        # Arrange / Act
        gadget = self._make_gadget(gadget_size='2x2')

        # Assert
        assert gadget.gadget_size == '2x2'

    def test_gadget_size_2x4_is_stored(self):
        """1.6.1: gadget_size に '2x4' が格納できる
        仕様: ui-specification.md > 部品サイズ 選択肢"""
        # Arrange / Act
        gadget = self._make_gadget(gadget_size='2x4')

        # Assert
        assert gadget.gadget_size == '2x4'

    # ---- gadget_uuid の一意性 ----

    def test_gadget_uuid_is_stored_as_string(self):
        """2.1.1: gadget_uuid が文字列として格納される
        仕様: workflow-specification.md > ガジェット登録③ gadget_uuid=str(uuid.uuid4())"""
        # Arrange
        import uuid
        expected_uuid = str(uuid.uuid4())
        gadget = self._make_gadget(gadget_uuid=expected_uuid)

        # Assert
        assert gadget.gadget_uuid == expected_uuid
        assert isinstance(gadget.gadget_uuid, str)

    # ---- tablename ----

    def test_tablename(self):
        """モデルのテーブル名が dashboard_gadget_master である
        仕様: workflow-specification.md > ガジェット登録③ INSERT INTO dashboard_gadget_master"""
        from iot_app.models.dashboard import DashboardGadgetMaster

        # Assert
        assert DashboardGadgetMaster.__tablename__ == 'dashboard_gadget_master'


# ============================================================
# TestGadgetTypeMaster
# 観点: 2.1 正常系処理、2.3 副作用チェック
# ============================================================

@pytest.mark.unit
class TestGadgetTypeMaster:
    """GadgetTypeMaster モデルの単体テスト
    観点: 2.1 正常系処理、2.3 副作用チェック
    仕様: workflow-specification.md > ガジェット登録④（gadget_type_id 取得）
    """

    def _make_gadget_type(self, **overrides):
        """GadgetTypeMaster インスタンスを生成するヘルパー"""
        from iot_app.models.dashboard import GadgetTypeMaster
        defaults = dict(gadget_type_name='時系列グラフ')
        defaults.update(overrides)
        return GadgetTypeMaster(**defaults)

    # ---- 正常系: インスタンス生成 (2.1.1) ----

    def test_instantiation_with_valid_name(self):
        """2.1.1: 有効な gadget_type_name で GadgetTypeMaster インスタンスが生成できる"""
        # Arrange / Act
        gadget_type = self._make_gadget_type(gadget_type_name='時系列グラフ')

        # Assert
        assert gadget_type.gadget_type_name == '時系列グラフ'

    # ---- delete_flag デフォルト値 (2.3.1) ----

    def test_delete_flag_default_is_false(self):
        """2.3.1: delete_flag のデフォルト値が False である"""
        # Arrange / Act
        gadget_type = self._make_gadget_type()

        # Assert
        assert gadget_type.delete_flag is False

    # ---- tablename ----

    def test_tablename(self):
        """モデルのテーブル名が gadget_type_master である"""
        from iot_app.models.dashboard import GadgetTypeMaster

        # Assert
        assert GadgetTypeMaster.__tablename__ == 'gadget_type_master'

