from functools import wraps


def require_auth(f):
    """権限チェックデコレータ（TODOにつき素通し、後々本実装に置き換え）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function
