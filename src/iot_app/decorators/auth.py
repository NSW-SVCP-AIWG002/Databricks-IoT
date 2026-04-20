from functools import wraps

from flask import abort, g

# user_type_id → ロール名マッピング
_USER_TYPE_ROLE_MAP = {
    1: 'system_admin',
    2: 'management_admin',
    3: 'sales_company_user',
    4: 'service_company_user',
}


def require_role(*roles):
    """ロールチェックデコレータ

    Args:
        *roles: 許可するロール名
                ('system_admin', 'management_admin',
                 'sales_company_user', 'service_company_user')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = getattr(g, 'current_user', None)
            user_role = _USER_TYPE_ROLE_MAP.get(getattr(current_user, 'user_type_id', None))
            if user_role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
