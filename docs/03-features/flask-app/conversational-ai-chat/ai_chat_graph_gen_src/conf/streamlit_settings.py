import json
import configparser
from pathlib import Path

_parser = configparser.ConfigParser()
# streamlit_settings.py と同じディレクトリの streamlit_config.ini を参照
_parser.read(Path(__file__).with_name("streamlit_config.ini"), encoding="utf-8")

class AgentAPI:
    endpoint = _parser.get("agent", "endpoint")

class ServicePrincipalConfig:
    WORKSPACE_URL = _parser.get("service_principal", "workspace_url")
    DATABRICKS_CLIENT_ID = _parser.get("service_principal", "databricks_client_id")
    DATABRICKS_CLIENT_SECRET = _parser.get("service_principal", "databricks_client_secret")
