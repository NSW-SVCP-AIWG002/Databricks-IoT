import sys, os
import traceback
from pathlib import Path
import pandas as pd

from model.pyfunc_model import LangGraphServingModel

# 疑似コンテキスト（MLflow の context の代用）
class DummyContext:
    def __init__(self):
        self.artifacts = {}
        self.model_config = {}
        self._mlflow_version = None

context = DummyContext()

# インスタンス生成
model = LangGraphServingModel()

# MLflow 環境では load_context が最初に呼ばれるので、手動で呼ぶ
model.load_context(context)

def run_agent(prompt, pat_token, thread_id):

    payload_dict = {
    "prompt": prompt,
    "access_token": pat_token,
    "thread_id": thread_id
    }

    # DataFrame で試す
    df = pd.DataFrame([payload_dict])
    try:
        # 直接 predict をコール（第1引数は MLflow context 相当。None でも可）
        response = model.predict(context=None, model_input=df)
        return response
    except Exception as e:
        traceback.print_exc()
        print(f"Error: {e}")
        return e
