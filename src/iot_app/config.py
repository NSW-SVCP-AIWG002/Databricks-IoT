import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    AUTH_TYPE = os.getenv("AUTH_TYPE")  # 必須設定: 'azure' / 'aws' / 'local'

    # Flask Server Configuration
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", 5000))

    # Databricks Configuration
    DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "")
    DATABRICKS_SERVICE_PRINCIPAL_TOKEN = os.getenv("DATABRICKS_SERVICE_PRINCIPAL_TOKEN", "")
    DATABRICKS_SERVING_ENDPOINT_NAME = os.getenv(
        "DATABRICKS_SERVING_ENDPOINT_NAME", "ai_orchestrator"
    )

    # MySQL Configuration
    MYSQL_HOST = os.getenv("MYSQL_HOST", "db")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT") or 3306)
    MYSQL_USER = os.getenv("MYSQL_USER", "user")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "databricks_iot")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    AUTH_TYPE = 'dev'
    MYSQL_TEST_DATABASE = os.getenv("MYSQL_TEST_DATABASE", "databricks_iot_test")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        f"mysql+pymysql://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{MYSQL_TEST_DATABASE}"
    )
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}
