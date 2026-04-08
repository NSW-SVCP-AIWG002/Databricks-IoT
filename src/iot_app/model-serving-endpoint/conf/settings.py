import json
import configparser
from pathlib import Path

_parser = configparser.ConfigParser()
<<<<<<< HEAD
# settings.py と同じディレクトリの config.ini を参照
_parser.read(Path(__file__).with_name("config.ini"), encoding="utf-8")

endpoint = _parser.get("model", "endpoint")

class FileStoreConfig:
    DATABRICKS_HOST = _parser.get("filestore", "databricks_host")
    CSV_FILE_NAME = _parser.get("filestore", "csv_file_name")

class GenieConfig:
    DATABRICKS_HOST = _parser.get("genie", "databricks_host")
    GENIE_START_CONVERSATION_API = _parser.get("genie", "genie_start_conversation_api")
    GENIE_GET_MESSAGE_API = _parser.get("genie", "genie_get_message_api")
    GENIE_POST_MESSAGE_API = _parser.get("genie", "genie_post_message_api")
    STATEMENT_API = _parser.get("genie", "statement_api")
    DATABRICKS_GENIE_SPACES = {}
=======
_config_path = Path(__file__).with_name("config.ini")
_found = _parser.read(_config_path, encoding="utf-8")

# Serving Endpoint コンテナログで config.ini の読み込み状況を確認できるようにする
print(f"[settings] config.ini path: {_config_path}, loaded: {bool(_found)}, sections: {_parser.sections()}")


def _get(section: str, key: str, fallback: str = "") -> str:
    try:
        return _parser.get(section, key)
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        print(f"[settings] WARNING: {e} — fallback='{fallback}'")
        return fallback


endpoint = _get("model", "endpoint")


class FileStoreConfig:
    DATABRICKS_HOST = _get("filestore", "databricks_host")
    CSV_FILE_NAME   = _get("filestore", "csv_file_name")


class GenieConfig:
    DATABRICKS_HOST              = _get("genie", "databricks_host")
    GENIE_START_CONVERSATION_API = _get("genie", "genie_start_conversation_api")
    GENIE_GET_MESSAGE_API        = _get("genie", "genie_get_message_api")
    GENIE_POST_MESSAGE_API       = _get("genie", "genie_post_message_api")
    STATEMENT_API                = _get("genie", "statement_api")
    DATABRICKS_GENIE_SPACES: dict = {}
>>>>>>> origin/main

for section in _parser.sections():
    if section.startswith("genie_spaces."):
        space_name = section.split(".", 1)[1]
        sec = _parser[section]
        GenieConfig.DATABRICKS_GENIE_SPACES[space_name] = {
<<<<<<< HEAD
            "id": sec.get("id"),
            "description": sec.get("description"),
            "keywords": json.loads(sec.get("keywords")),
            "examples": json.loads(sec.get("examples")),
        }

class SQLConfig:
    SQL_SERVER_HOST_NAME = _parser.get("sql", "sql_server_host_name")
    SQL_HTTP_PATH = _parser.get("sql", "sql_http_path")

class CheckpointConfig:
    table_name = _parser.get("checkpoint", "table_name")
    MAX_TURNS = _parser.getint("checkpoint", "max_turns")
    MAX_SIZE_BYTES = _parser.getint("checkpoint", "max_size_bytes")
=======
            "id":          sec.get("id"),
            "description": sec.get("description"),
            "keywords":    json.loads(sec.get("keywords", "[]")),
            "examples":    json.loads(sec.get("examples", "[]")),
        }


class SQLConfig:
    SQL_SERVER_HOST_NAME = _get("sql", "sql_server_host_name")
    SQL_HTTP_PATH        = _get("sql", "sql_http_path")


class CheckpointConfig:
    table_name     = _get("checkpoint", "table_name")
    MAX_TURNS      = int(_get("checkpoint", "max_turns",      "15"))
    MAX_SIZE_BYTES = int(_get("checkpoint", "max_size_bytes", "524288"))

>>>>>>> origin/main

class TokenContextClass:
    def __init__(self):
        self._data = {}
<<<<<<< HEAD
    def set(self, key: str, value):
        self._data[key] = value
    def get(self, key: str, default=None):
        return self._data.get(key, default)

TokenContext = TokenContextClass()
=======

    def set(self, key: str, value):
        self._data[key] = value

    def get(self, key: str, default=None):
        return self._data.get(key, default)


TokenContext = TokenContextClass()
>>>>>>> origin/main
