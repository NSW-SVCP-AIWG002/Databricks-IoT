from enum import IntEnum


class UserType(IntEnum):
    """ユーザータイプID（user_type_master.user_type_id と対応）"""
    SYSTEM_ADMIN     = 1  # システム保守者
    MANAGEMENT_ADMIN = 2  # 管理者
    SALES_COMPANY    = 3  # 販社ユーザー
    SERVICE_USER     = 4  # サービス利用者


# ソート順ドロップダウン固定値（設定ファイル管理対象外）
# sort_order_id: -1=指定なし, 1=昇順(ASC), 2=降順(DESC)
SORT_ORDER = [
    {'sort_order_id': -1, 'sort_order_name': ''},
    {'sort_order_id':  1, 'sort_order_name': '昇順'},
    {'sort_order_id':  2, 'sort_order_name': '降順'},
]
