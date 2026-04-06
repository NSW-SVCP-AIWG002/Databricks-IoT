from iot_app.auth.exceptions import UnauthorizedError
from iot_app.models.user import User


def find_user_by_email(email: str) -> dict:
    """email でアクティブユーザーを検索し user_id と user_type_id を返す

    Args:
        email: 検索対象のメールアドレス

    Returns:
        dict: {'user_id': int, 'user_type_id': int}

    Raises:
        UnauthorizedError: ユーザーが存在しない場合
    """
    user = User.query.filter_by(email_address=email, delete_flag=False).first()
    if user is None:
        raise UnauthorizedError(f"User not found: {email}")

    return {
        'user_id': user.user_id,
        'user_type_id': user.user_type_id,
<<<<<<< HEAD
=======
        'organization_id': user.organization_id,
>>>>>>> origin/main
    }
