# Databricks notebook source
import os
# STEP 2 でアップロードしたパスに合わせて変更
os.chdir("/Workspace/Users/kei.sugiyama@nsw.co.jp/ai_orchestrator")
print(os.getcwd())
print(os.listdir("."))

# COMMAND ----------

# MAGIC %pip install "mlflow[databricks]==3.6.0" databricks-sdk==0.73.0 "typing_extensions>=4.13.0" -r requirements.txt

# COMMAND ----------

# DBTITLE 1,Restart Python
dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Model logging
import os
import sys
os.chdir("/Workspace/Users/kei.sugiyama@nsw.co.jp/ai_orchestrator")
sys.path.insert(0, "/Workspace/Users/kei.sugiyama@nsw.co.jp/ai_orchestrator")

import mlflow
import pandas as pd
from mlflow.models.signature import infer_signature
from model.pyfunc_model import LangGraphServingModel
from src.agent.builder import build_agent

input_example = {
  "prompt": "こんにちは",
  "access_token": "1111",
  "thread_id": "100"
}
output_example = {"status":"ok","message":"...", "df": None, "fig_data": None}
signature = infer_signature(
    model_input=pd.DataFrame([input_example]),
    model_output=pd.DataFrame([output_example])
)

with mlflow.start_run():
    mlflow.pyfunc.log_model(
        artifact_path="model",
        python_model=LangGraphServingModel(),
        pip_requirements=[
            "langgraph==1.0.2",
            "plotly==6.3.0",
            "databricks-sql-connector==3.1.0",
            "tiktoken==0.11.0",
            "databricks-langchain==0.9.0",
            ],
        input_example=input_example,
        signature=signature,
        #code_paths or code_path
        code_paths=["model", "src", "conf", "db"]
    )
    run_id = mlflow.active_run().info.run_id

registered_model_name = "iot_catalog.ai.ai_orchestrator"
result = mlflow.register_model(model_uri=f"runs:/{run_id}/model", name=registered_model_name)
print("Registered:", result.name, result.version)