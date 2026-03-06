import base64
import json

from typing import Any, Dict, List, Optional, Tuple
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from conf.settings import CheckpointConfig
from conf.logging_config import log_message
from db.connection import get_db_connection
from src.utils.common import trim_messages

class DatabricksSerializer:
    """
    JsonPlusSerializerのラッパー。
    DatabricksのSTRINGカラムに保存できるよう、バイナリをHex文字列化したJSONとして扱います。
    """
    def __init__(self):
        self.inner = JsonPlusSerializer()

    def dumps(self, obj: Any) -> str:
        """オブジェクトをシリアライズし、JSON文字列として返す"""
        # dumps_typed は (type_name, bytes_data) を返す
        type_, data_bytes = self.inner.dumps_typed(obj)
        
        # DBに保存するために JSON 文字列化 (bytes は hex 文字列に変換)
        # Base64エンコード（Hexより約33%サイズ削減）
        return json.dumps({
            "t": type_,
            "b": base64.b64encode(data_bytes).decode('ascii')
        }, ensure_ascii=False)

    def loads(self, data: str) -> Any:
        """JSON文字列からオブジェクトを復元する"""
        if not data:
            return None
        
        try:
            raw = json.loads(data)
            type_ = raw["t"]

            # Base64デコード
            data_bytes = base64.b64decode(raw["b"])
            
            # loads_typed に (type_name, bytes_data) を渡す
            return self.inner.loads_typed((type_, data_bytes))
        except Exception as e:
            log_message(f"Deserialization error: {e}")
            return None

    def dumps_typed(self, obj: Any) -> Tuple[str, bytes]:
        """互換性のために inner のメソッドも公開"""
        return self.inner.dumps_typed(obj)

class DatabricksUnityCatalogCheckpointer(BaseCheckpointSaver):
    _table_checked = False

    def __init__(self):
        # LangGraph標準のシリアライザを利用
        super().__init__()
        self.serde=DatabricksSerializer()

    def _get_conn_from_config(self, config: Dict[str, Any]):
        """DB接続を確立する"""
        configurable = config.get("configurable", {})
        access_token = configurable.get("access_token")
        return get_db_connection(access_token)
    
    def _ensure_table_exists(self, cursor):
        """
        テーブルが存在しない場合に作成する内部メソッド
        CREATE TABLE IF NOT EXISTS を使用するため、存在する場合は何もしません。
        パフォーマンスのため、インスタンスごとに初回のみ実行します。
        """
        if DatabricksUnityCatalogCheckpointer._table_checked:
            return

        log_message("Checking/Creating tables if not exists...")

        # 1. メインのチェックポイントテーブル
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {CheckpointConfig.table_name} (
            thread_id STRING,
            checkpoint STRING,
            metadata STRING,
            ts STRING,
            parent_ts STRING
        ) USING DELTA
        """)
        DatabricksUnityCatalogCheckpointer._table_checked = True

    def get_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id") 

        conn = self._get_conn_from_config(config)
        cursor = conn.cursor()
        try:
            self._ensure_table_exists(cursor)
            if checkpoint_id:
                cursor.execute(
                    f"SELECT checkpoint, metadata, parent_ts FROM {CheckpointConfig.table_name} WHERE thread_id = ? AND ts = ?",
                    (thread_id, checkpoint_id),
                    )
            else:
                cursor.execute(
                    f"SELECT checkpoint, metadata, parent_ts FROM {CheckpointConfig.table_name} WHERE thread_id = ? ORDER BY ts DESC LIMIT 1",
                    (thread_id,),
                )
            
            row = cursor.fetchone()
            if not row:
                return None

            # DBから取り出したデータを復元
            # self.serde.loads を使うと Checkpoint オブジェクトへの復元
            checkpoint = self.serde.loads(row.checkpoint)
            metadata = self.serde.loads(row.metadata)
            parent_ts = row.parent_ts

            # 親の設定を作成
            parent_config = None
            if parent_ts:
                parent_config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_id": parent_ts,
                    }
                }

            return CheckpointTuple(
                config=config,
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=parent_config,
            )
        finally:
            cursor.close()

    def list(self, config: Dict[str, Any]) -> List[CheckpointTuple]:
        """一覧取得（N+1問題を解消した版）"""
        thread_id = config["configurable"]["thread_id"]
        
        conn = self._get_conn_from_config(config)
        cursor = conn.cursor()
        try:
            self._ensure_table_exists(cursor)
            cursor.execute(
                f"SELECT ts, checkpoint, metadata, parent_ts FROM {CheckpointConfig.table_name} WHERE thread_id = ? ORDER BY ts DESC",
                (thread_id,),
            )
            rows = cursor.fetchall()

            tuples = []
            for row in rows:
                tuples.append(CheckpointTuple(
                    config={"configurable": {"thread_id": thread_id, "checkpoint_id": row.ts}},
                    checkpoint=self.serde.loads(row.checkpoint),
                    metadata=self.serde.loads(row.metadata),
                    parent_config={"configurable": {"thread_id": thread_id, "checkpoint_id": row.parent_ts}} if row.parent_ts else None,
                ))
            return tuples
        finally:
            cursor.close()
    
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Dict[str, Any],
    ) -> Dict[str, Any]:
        thread_id = config["configurable"]["thread_id"]

        # checkpoint をコピー
        ckpt = checkpoint.copy()
        channel_values = ckpt.get("channel_values", {}).copy()

        messages = channel_values.get("messages")

        if isinstance(messages, list):
            channel_values["messages"] = trim_messages(
                messages,
                max_turns=CheckpointConfig.MAX_TURNS,
                max_size_bytes=CheckpointConfig.MAX_SIZE_BYTES
            )

        # 2. dataframe 系チャネルはすべて None にする
        df_like_keys = [
            "dataframe",
            "fig_data",
        ]
        for k in df_like_keys:
            if k in channel_values:
                channel_values[k] = None

        # channel_values を上書き
        ckpt["channel_values"] = channel_values

        # シリアライズして保存 (filtered_checkpoint を使用)
        serialized_checkpoint = self.serde.dumps(ckpt)
        serialized_metadata = self.serde.dumps(metadata)
        
        # ★デバッグ用 (フィルタリング後のサイズが表示されます)
        data_size_checkpoint = len(serialized_checkpoint) / (1024 * 1024)
        data_size_metadata = len(serialized_metadata) / (1024 * 1024)
        log_message(f"DEBUG: size={data_size_checkpoint:.2f} MB (Filtered)")
        log_message(f"DEBUG: metadata_size={data_size_metadata:.2f} MB")

        conn = self._get_conn_from_config(config)
        cursor = conn.cursor()
        try:
            self._ensure_table_exists(cursor)
            cursor.execute(
                f"""
                INSERT INTO {CheckpointConfig.table_name}
                (thread_id, checkpoint, metadata, ts, parent_ts)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    serialized_checkpoint,
                    serialized_metadata,
                    checkpoint["id"],
                    config["configurable"].get("checkpoint_id"),
                ),
            )
        finally:
            cursor.close()

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint["id"],
            }
        }

    def put_writes(
        self,
        config: Dict[str, Any],
        writes: List[Any],
        task_id: str,
    ) -> None:
        pass