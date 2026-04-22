from databricks.connect import DatabricksSession

spark = DatabricksSession.builder.serverless(True).getOrCreate()

print(spark.range(5).collect())