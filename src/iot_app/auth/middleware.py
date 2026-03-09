from flask import g


class _MockUser:
    """ローカル開発用モックユーザー"""
    def __init__(self, organization_id=1):
        self.organization_id = organization_id


def set_mock_current_user():
    """before_request フック: g.current_user にモックユーザーをセットする"""
    g.current_user = _MockUser(organization_id=1)
