class ValidationError(Exception):
    """バリデーションエラー"""
    pass


class NotFoundError(Exception):
    """リソース未検出エラー"""
    pass
