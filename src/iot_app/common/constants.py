from enum import IntEnum

# ページネーション最大件数
ITEM_PER_PAGE = 25

# Databricks ワークスペースグループID（要設定）
DATABRICKS_WORKSPACE_GROUP_ID = ""


class UserType(IntEnum):
    """ユーザータイプID（user_type_master.user_type_id と対応）"""
    SYSTEM_ADMIN     = 1  # システム保守者
    MANAGEMENT_ADMIN = 2  # 管理者
    SALES_COMPANY    = 3  # 販社ユーザー
    SERVICE_USER     = 4  # サービス利用者
