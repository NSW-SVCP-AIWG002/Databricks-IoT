import io
from io import StringIO

import chardet
import pandas as pd

from iot_app import db
from iot_app.common.logger import get_logger
from iot_app.models.organization import OrganizationClosure

logger = get_logger(__name__)

# マスタ種別ごとの必須カラム定義（表示名ベース）
_REQUIRED_COLUMNS: dict[int, list[str]] = {
    1: ['デバイスID', 'デバイス名', 'デバイス種別', 'モデル情報', '所属組織ID'],
    2: ['ユーザーID', 'ユーザー名', 'メールアドレス', 'ユーザー種別', '所属組織ID',
        '地域', '住所', 'ステータス', 'アラート通知メール受信設定', 'システム通知メール受信設定'],
    3: ['組織ID', '組織名', '組織種別', '所属組織ID', '住所', '電話番号',
        '担当者名', '契約状態', '契約開始日', '契約終了日'],
    4: ['アラートID', 'アラート名', 'デバイスID',
        'アラート発生条件_測定項目名', 'アラート発生条件_比較演算子', 'アラート発生条件_閾値',
        'アラート復旧条件_測定項目名', 'アラート復旧条件_比較演算子', 'アラート復旧条件_閾値',
        '判定時間', 'アラートレベル', 'アラート通知', 'メール送信'],
    5: ['デバイスID', 'デバイス名', 'デバイス種別', 'モデル情報', 'MACアドレス',
        '所属組織ID', '在庫状況', '購入日', 'メーカー保証終了日', '在庫場所'],
}


def detect_encoding(file_content: bytes) -> str:
    """BOM付きなら 'utf-8-sig'、それ以外は chardet 検出結果（未検出時は 'utf-8'）を返す。"""
    if file_content.startswith(b'\xef\xbb\xbf'):
        return 'utf-8-sig'
    detected = chardet.detect(file_content)
    return detected.get('encoding') or 'utf-8'


def read_csv(file_content: bytes, encoding: str) -> pd.DataFrame:
    """バイト列のCSVをDataFrameで返す。空行スキップ、NA変換無効。"""
    csv_content = file_content.decode(encoding)
    return pd.read_csv(StringIO(csv_content), keep_default_na=False, skip_blank_lines=True)


def validate_csv_format(df: pd.DataFrame, master_type_id: int, user) -> list:
    """CSVのフォーマット・データスコープを検証し、エラー辞書リストを返す。"""
    errors: list[dict] = []

    accessible_org_ids = {
        str(org_id)
        for (org_id,) in db.session.query(
            OrganizationClosure.subsidiary_organization_id
        ).filter(
            OrganizationClosure.parent_organization_id == user.organization_id
        ).all()
    }

    required_columns = _REQUIRED_COLUMNS.get(master_type_id, [])

    for col in required_columns:
        if col not in df.columns:
            errors.append({'row': 1, 'column': col, 'message': '必須列が存在しません'})

    for index, row in df.iterrows():
        row_num = index + 2

        for col in required_columns:
            if col in row.index and (pd.isna(row[col]) or str(row[col]).strip() == ''):
                errors.append({'row': row_num, 'column': col, 'message': '必須項目です'})

        org_id_col = '組織ID' if '組織ID' in row.index else '所属組織ID'
        if org_id_col in row.index:
            try:
                row_org_id = str(int(float(row[org_id_col])))
            except (ValueError, TypeError):
                row_org_id = str(row[org_id_col])
            if row_org_id not in accessible_org_ids:
                errors.append({
                    'row': row_num,
                    'column': org_id_col,
                    'message': 'アクセス権限のない組織のデータは登録できません',
                })

    return errors


def apply_data_scope_filter(query, user):
    """organization_closure を参照してクエリにデータスコープ制限を適用する。"""
    accessible_org_ids = [
        org_id
        for (org_id,) in db.session.query(
            OrganizationClosure.subsidiary_organization_id
        ).filter(
            OrganizationClosure.parent_organization_id == user.organization_id
        ).all()
    ]
    return query.filter(OrganizationClosure.subsidiary_organization_id.in_(accessible_org_ids))


def generate_csv(rows: list) -> bytes:
    """rows (list of dict) から UTF-8 BOM 付き CSV バイト列を生成する。"""
    if not rows:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(rows).fillna('')

    buf = io.BytesIO()
    df.to_csv(buf, index=False, encoding='utf-8-sig')
    return buf.getvalue()
