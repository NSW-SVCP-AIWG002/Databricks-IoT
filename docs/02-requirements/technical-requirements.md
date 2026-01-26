# Databricks IoTシステム 技術要件定義書

## 1. 概要

Databricks IoTシステムの開発プロジェクトにおける技術要件を定義します。本ドキュメントは、システムを「どう作るか」を規定し、使用する技術スタック、開発環境、テスト戦略、デプロイメント方法などを明確にします。

---

## 2. アーキテクチャ概要

本システムのインフラストラクチャ構成、ネットワーク構成、主要コンポーネントの詳細については、以下のドキュメントを参照してください。

**参照ドキュメント**: [`01-architecture/infrastructure.md`](../01-architecture/infrastructure.md)

**概要**:
- Azure環境内にDatabricks Platform、Azure IoT Services、OLTP DBを統合
- Private Linkによる閉域接続でセキュアな通信を実現
- メダリオンアーキテクチャ（ブロンズ/シルバー/ゴールド層）によるデータ処理
- Event Hubs Captureがブロンズ層を担当、LDPがシルバー/ゴールド層を処理

---

## 3. Databricks Platform技術スタック

### TR-DB-001: Databricks Platform (Premium ライセンス)

**決定理由**: データ処理・分析・アプリケーション実行を統合的に行うため

#### Lakeflow 宣言型パイプライン (LDP)
- **実装言語**: Python / SQL
- **処理方式**: ストリーミングデータ処理
- **アーキテクチャ**: メダリオンアーキテクチャ
  - シルバー層: データ構造化・変換、異常データ検出
  - ゴールド層: ダッシュボード表示用データ生成
- **LDP処理範囲**: シルバー層・ゴールド層のみ
  - ブロンズ層の生データ保存はEvent Hubs Captureが担当
- **データソース**: Event Hubs (Kafka Endpoint)

#### App Compute
- **Webフレームワーク**: Flask 3.0+
- **テンプレートエンジン**: Jinja2
- **実行環境**: Databricks App Compute
- **制約事項**:
  - 1ファイル10MB以下
  - コンテナ再起動時にログが消失
  - シングルトン保証について要調査

#### Unity Catalog
- **ストレージ**: Delta Lake
- **用途**: センサーデータ、表示用データ
- **アクセス方式**: SQL Warehouse経由
- **接続ドライバー**: databricks-sql-connector (Python)

#### Databricks User認証 + Entra ID
- **認証基盤**: Entra ID (Azure Active Directory) によるユーザ認証・トークン発行
- **認証方式**: Databricks標準ログイン画面（Entra ID連携）
  - **重要**: ログイン認証はDatabricks標準機能であり、Flaskアプリでは実装しない
- **Flaskアプリの役割**: リバースプロキシが付与するヘッダ情報からユーザーを識別
- **ヘッダ付与**: リバースプロキシによるユーザ識別子・アクセストークン
- **権限管理**: サービスプリンシパル権限 + ユーザー認可API
- **ユーザ管理**: Entra ID + Databricks SCIM API 間の同期

---

### TR-DB-002: データベース技術スタック

**決定理由**: データストアの適材適所使用によるパフォーマンス最適化

#### Unity Catalog (ADLS上のDelta Lake)
- **用途**: センサーデータ、分析用途
- **ストレージ**: ADLS (Azure Data Lake Store)
- **アクセス**: Private Link経由でADLSに接続
- **特徴**:
  - ACID トランザクション保証
  - タイムトラベル機能
  - スキーマ進化対応
  - Z-Orderingによる最適化
- **データ保持期間**:
  - ブロンズ層: 7日
  - シルバー層: 1年
  - ゴールド層: 5年

#### MySQL互換データベース (OLTP)
- **用途**: マスタデータ、デバイスステータス
- **互換性**: SingleStoreと置き換え可能
- **接続ライブラリ**: PyMySQL
- **特徴**:
  - 低レイテンシ
  - 高頻度更新対応
  - ACID準拠

---

## 4. Azure IoT Services技術スタック

### TR-AZURE-001: Azure IoT Hubs

**決定理由**: IoTデバイスとの通信ハブとして実績のあるサービス

#### 機能
- **プロトコル**: MQTT
- **双方向通信**: 上り（デバイス → クラウド）、下り（クラウド → デバイス）
- **デバイス管理**: Azure管理画面から事前に設定（Databricks Appsからの操作は行わない）

#### 接続方法
- Python SDK: `azure-iot-hub`
- デバイス認証: 共有アクセス署名 (SAS) またはX.509証明書

---

### TR-AZURE-002: Event Hubs

**決定理由**: Kafkaエンドポイント提供によるDatabricks連携

#### 機能
- **プロトコル**: Kafka
- **データ配信**: IoT Hubs → Event Hubs → Databricks LDP
- **スループット**: スループットユニットによるスケーリング
- **Event Hubs Capture**: ADLSにRAWデータを継続的に出力（ブロンズ層）

#### ネットワーク接続
- **Private Link経由**: サーバレス/クラシックコンピューティングプレーンからPrivate Link経由で接続
- **セキュリティ**: パブリックインターネットを経由しないセキュアな通信

---

## 5. フロントエンド技術スタック

### TR-FE-001: Flask Application

**決定理由**: シンプルで保守性の高いサーバーサイドレンダリング

#### コアフレームワーク
- **Flask**: 3.0+
  - Blueprint によるモジュール化
  - Jinja2 テンプレートエンジン
  - WSGI サーバー対応

#### テンプレートエンジン
- **Jinja2**: 2.11+
  - テンプレート継承
  - マクロ機能
  - 自動エスケープ (XSS対策)
  - フィルター・テスト機能

#### スタイリング
- **HTML5**: セマンティックHTML
- **CSS3**: カスタムCSS
  - CSS変数によるデザイントークン
  - メディアクエリによるレスポンシブ対応
  - Flexbox/Grid Layout

#### JavaScript
- **最小限の使用**: フォーム検証、UI補助のみ
- **ライブラリ**: 必要に応じて軽量ライブラリ使用検討

---

### TR-FE-002: フォーム管理

**決定理由**: セキュリティとユーザビリティの向上

#### CSRF対策
- **Flask-WTF**: 4.1+
  - CSRFトークン生成・検証
  - フォームクラス定義
  - バリデーション機能

#### バリデーション
- **サーバーサイド検証**: 必須
  - 入力値の型チェック
  - 範囲チェック
  - 形式チェック
- **クライアントサイド検証**: 補助的に使用
  - HTML5バリデーション属性
  - JavaScriptによる即時フィードバック

---

## 6. バックエンド技術スタック

### TR-BE-001: Python技術スタック

**決定理由**: Databricks環境とFlask開発の統一

#### Pythonバージョン
- **Python**: 3.11
  - Type Hints活用
  - Dataclasses使用
  - F-strings使用

#### 必須パッケージ
```
Flask==3.0.0
Jinja2==3.1.0
databricks-sql-connector==2.9.0
PyMySQL==1.1.0
python-dotenv==1.0.0
Flask-WTF==1.2.0
```

#### 推奨パッケージ
```
# テスト
pytest==7.4.0
pytest-flask==1.3.0

# コード品質
pylint==3.0.0
flake8==6.1.0
black==23.12.0

# セキュリティ
cryptography==41.0.0
```

---

### TR-BE-002: データベース接続

**決定理由**: 効率的なデータベースアクセスとリソース管理

#### Databricks接続
```python
from databricks import sql

# 接続プール設定
connection = sql.connect(
    server_hostname=os.getenv('DATABRICKS_SERVER_HOSTNAME'),
    http_path=os.getenv('DATABRICKS_HTTP_PATH'),
    access_token=os.getenv('DATABRICKS_TOKEN')
)
```

#### MySQL接続
```python
import pymysql.cursors
from pymysql.pooling import ConnectionPool

# 接続プール設定
mysql_pool = ConnectionPool(
    pool_size=5,
    host=os.getenv('MYSQL_HOST'),
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    database=os.getenv('MYSQL_DATABASE'),
    cursorclass=pymysql.cursors.DictCursor
)
```

---

### TR-BE-003: アラート処理

**決定理由**: 多様な通知チャネルへの対応
- LDPシルバー層で処理内で実施

#### 通知ライブラリ
- **メール**: `smtplib` (標準ライブラリ)


---

### TR-BE-004: CSVインポート/エクスポート機能 (FR-004-8)

**決定理由**: マスタデータの一括操作（ユーザー、組織、デバイス等）を効率的に行うため

#### 必須ライブラリ
```python
# requirements.txt
pandas==2.0+  # CSV処理
chardet==5.0+  # 文字コード検出
```

#### CSVエクスポート実装

**実装方式**: 各マスタの一覧画面にエクスポートボタンを配置し、一覧取得APIに `export=csv` パラメータを追加することでCSVレスポンスを返却

**エンドポイント例**:
- `GET /api/admin/devices?export=csv` - デバイス一覧のCSVエクスポート
- `GET /api/admin/users?export=csv` - ユーザー一覧のCSVエクスポート
- `GET /api/admin/organizations?export=csv` - 組織一覧のCSVエクスポート

**権限チェック**: 各マスタのC/U権限に従う（一覧APIと同じ権限チェックロジック）

```python
# services/csv_export_service.py
import pandas as pd
from flask import make_response, request
from datetime import datetime

def export_to_csv(data, columns, filename_prefix):
    """
    データをCSVファイルとしてエクスポート

    Args:
        data: エクスポート対象データ（list of dict）
        columns: カラム名とヘッダー名のマッピング
        filename_prefix: ファイル名プレフィックス

    Returns:
        Flask Response object
    """
    df = pd.DataFrame(data)
    df = df.rename(columns=columns)
    csv_data = df.to_csv(index=False, encoding='utf-8-sig')

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{filename_prefix}_{timestamp}.csv"

    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

# 使用例（一覧APIに統合）
@admin_bp.route('/devices', methods=['GET'])
@require_permission('device', ['create', 'update'])  # C/U権限チェック
def list_devices():
    """デバイス一覧取得/エクスポート"""
    devices = get_devices_filtered()  # スコープ制限適用済み（絞り込み条件含む）

    # CSVエクスポートリクエストの場合
    if request.args.get('export') == 'csv':
        columns = {'device_id': 'デバイスID', 'device_name': 'デバイス名', ...}
        return export_to_csv(devices, columns, 'devices')

    # 通常のJSON応答
    return jsonify({'data': devices})

    columns = {
        'device_id': 'デバイスID',
        'device_name': 'デバイス名',
        'organization_id': '組織ID',
        'sales_company_id': '販社ID',
        'status': 'ステータス',
        'last_communication_time': '最終通信日時'
    }

    return export_to_csv(devices, columns, 'devices')
```

#### CSVインポート実装
```python
# services/csv_import_service.py
import pandas as pd
import chardet
from werkzeug.exceptions import BadRequest

def detect_encoding(file_content):
    """CSVファイルの文字コードを検出"""
    result = chardet.detect(file_content)
    return result['encoding']

# マスタ種別ごとの設定
MASTER_CONFIGS = {
    'devices': {
        'name': 'デバイス',
        'required_columns': ['デバイスID', 'デバイス名', '組織ID', '販社ID'],
        'permission': 'device'
    },
    'users': {
        'name': 'ユーザー',
        'required_columns': ['ユーザーID', 'ユーザー名', 'メールアドレス', 'ロール'],
        'permission': 'user'
    },
    'organizations': {
        'name': '組織',
        'required_columns': ['組織ID', '組織名', '販社ID'],
        'permission': 'organization'
    },
    # ... その他のマスタ設定
}

def get_available_masters(user):
    """ユーザーがインポート可能なマスタのリストを取得（プルダウン表示用）"""
    available = []
    for master_type, config in MASTER_CONFIGS.items():
        if user.has_permission(config['permission'], ['create', 'update']):
            available.append({
                'type': master_type,
                'name': config['name']
            })
    return available

def import_from_csv(file, master_type):
    """
    CSVファイルからマスタデータをインポート

    Args:
        file: アップロードされたファイルオブジェクト
        master_type: マスタ種別 ('devices', 'users', 'organizations', etc.)

    Returns:
        dict: {'success': bool, 'imported_count': int, 'errors': list}
    """
    if master_type not in MASTER_CONFIGS:
        raise BadRequest(f'不正なマスタ種別: {master_type}')

    config = MASTER_CONFIGS[master_type]

    # ファイルサイズチェック（10MB制限）
    file.seek(0, 2)
    if file.tell() > 10 * 1024 * 1024:
        raise BadRequest('ファイルサイズが10MBを超えています')
    file.seek(0)

    # 文字コード検出・CSV読み込み
    file_content = file.read()
    encoding = detect_encoding(file_content)
    file.seek(0)

    try:
        df = pd.read_csv(file, encoding=encoding)

        # 必須カラムチェック
        missing = set(config['required_columns']) - set(df.columns)
        if missing:
            raise BadRequest(f'必須カラムが不足: {", ".join(missing)}')

        # マスタ種別ごとの処理を実行
        errors = validate_and_import(df, master_type)

        if errors:
            return {'success': False, 'imported_count': 0, 'errors': errors}

        return {'success': True, 'imported_count': len(df), 'errors': []}

    except pd.errors.EmptyDataError:
        raise BadRequest('CSVファイルが空です')
    except pd.errors.ParserError as e:
        raise BadRequest(f'CSV解析エラー: {str(e)}')
```

#### ルーティング実装
```python
# blueprints/transfer.py
from flask import Blueprint, request, jsonify, render_template
from decorators.auth import role_required
from models.role import Role
from services.csv_import_service import import_from_csv, get_available_masters

transfer_bp = Blueprint('transfer', __name__, url_prefix='/transfer')

@transfer_bp.route('/csv-import', methods=['GET'])
@role_required(Role.SYSTEM_ADMIN, Role.ADMIN, Role.SALES_USER)  # サービス利用者は除外
def csv_import_page():
    """CSVインポート画面（TRF-001）"""
    # ユーザーがインポート可能なマスタのリストを取得
    available_masters = get_available_masters(current_user)
    return render_template('transfer/csv-import.html', masters=available_masters)

@transfer_bp.route('/api/import', methods=['POST'])
@role_required(Role.SYSTEM_ADMIN, Role.ADMIN, Role.SALES_USER)  # サービス利用者は除外
def import_csv():
    """CSVインポートAPI（マスタ種別をパラメータで受け取る）"""
    if 'file' not in request.files:
        return jsonify({'error': 'ファイルが指定されていません'}), 400

    if 'master_type' not in request.form:
        return jsonify({'error': 'マスタ種別が指定されていません'}), 400

    file = request.files['file']
    master_type = request.form['master_type']

    if file.filename == '':
        return jsonify({'error': 'ファイルが選択されていません'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'CSVファイルを選択してください'}), 400

    try:
        result = import_from_csv(file, master_type)
        return jsonify(result)
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400

# グローバルメニュー表示制御（サービス利用者には非表示）
# app/templates/base.html のテンプレート内で以下のように制御:
# {% if current_user.role in ['SYSTEM_ADMIN', 'ADMIN', 'SALES_USER'] %}
#   <a href="{{ url_for('transfer.csv_import_page') }}">CSVインポート</a>
# {% endif %}
```

**CSVエクスポート**: 個別のエンドポイントは不要。各マスタの一覧APIに `?export=csv` パラメータを追加することで実現（CSVエクスポート実装セクション参照）。

#### 制約事項
- **ファイルサイズ制限**: 10MB以下（App Compute制約）
- **対応文字コード**: UTF-8（BOM付き/なし）、Shift-JIS、EUC-JP（自動検出）
- **CSV形式**: カンマ区切り、ヘッダー行必須
- **スコープ制限**: インポート/エクスポートともにロール別データスコープを適用

---

## 7. テスト要件

### TR-TEST-001: ユニットテスト

**決定理由**: コード品質の保証と回帰防止

#### テストフレームワーク
- **Pytest**: 7.4+
  - Fixture機能
  - パラメータ化テスト
  - モック機能

#### テストカバレッジ
- **目標**: 80%以上
- **ツール**: pytest-cov
- **対象**: ビジネスロジック、ビュー関数、モデル

#### テスト例
```python
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        yield client

def test_device_list(client):
    response = client.get('/admin/devices')
    assert response.status_code == 200
```

---

### TR-TEST-002: 結合テスト

**決定理由**: システム全体の動作確認

#### テストツール
- **Flask Test Client**: Flaskアプリケーションのテスト
- **モックオブジェクト**: `unittest.mock`

#### テスト対象
- エンドポイントのリクエスト/レスポンス
- データベース接続
- 認証フロー

---

### TR-TEST-003: e2eテスト

**決定理由**: UI/UXの確認とクロスブラウザ対応

#### テスト内容
- ブラウザでのUI確認
- レスポンシブデザイン確認
- クロスブラウザテスト (Chrome, Edge, Firefox, Safari)

---

## 8. ビルド・デプロイ要件

### TR-DEPLOY-001: App Computeデプロイ

**決定理由**: Databricks統合環境でのシンプルなデプロイ

#### デプロイ方式
- **方法A**: 外部GitリポジトリからPull
  - GitHub / GitLab Private Repository
  - 自動または手動Pull
- **方法B**: ファイル同期
  - Databricks CLIによるDatabricks統合環境へのファイル同期

#### パッケージ管理
- **requirements.txt**: pipによる自動インストール
- バージョン固定推奨

#### デプロイフロー
```
開発 → Git Push → GitHub
              ↓
         Databricks Pull または ファイル同期
              ↓
         App Compute配置
              ↓
         パッケージインストール (pip)
              ↓
         アプリケーション再起動
```
#### 備考
- 1ファイル辺り10MB以下の制約あり

---

### TR-DEPLOY-002: Databricks リソースデプロイ

#### Databricks CLI
- **バージョン**: 最新
- **認証**: Personal Access Token
- **用途**: パイプライン、クラスター、ジョブ定義のデプロイ

#### Databricks アセット バンドル
- **定義ファイル**: YAML形式
- **対象リソース**:
  - Lakeflow 宣言型パイプライン
  - Compute Cluster設定
  - ジョブ定義
  - Unity Catalogオブジェクト

#### デプロイコマンド
```bash
databricks bundle deploy --target production
```

---

### TR-DEPLOY-003: 環境管理

**決定理由**: 環境別の設定分離とセキュリティ

#### 環境構成

本システムは、3つの環境で構成されます。Azure環境は検証・本番の2つのインスタンスが存在します。

| 環境 | 構成 | Azure環境 | 用途 |
|------|------|-----------|------|
| **ローカル開発環境** | Flask Webアプリケーションのみ | 不要 | 開発者のローカルマシンでのアプリケーション開発 |
| **検証環境** | Azure環境全体 | Azure（検証用Resource Group） | 結合テスト、E2Eテスト |
| **本番環境** | Azure環境全体 | Azure（本番用Resource Group） | 本番運用 |

#### 環境変数
- **ローカル開発環境**: `.env` ファイル
- **検証環境**: Databricks環境変数設定（検証用）
- **本番環境**: Databricks環境変数設定（本番用）

#### 環境別設定
```python
# config.py
import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    DATABRICKS_SERVER_HOSTNAME = os.getenv('DATABRICKS_SERVER_HOSTNAME')
    MYSQL_HOST = os.getenv('MYSQL_HOST')

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'

class TestingConfig(Config):
    DEBUG = True
    ENV = 'testing'

class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'
```

---

## 9. 開発環境要件

### TR-DEV-001: 必須ツール

**決定理由**: 効率的な開発とチーム協業

#### エディタ/IDE
- **Visual Studio Code**: 推奨
  - Python拡張機能
  - Pylance (型チェック)
  - Black Formatter
  - Flake8 Linter

#### バージョン管理
- **Git**: 2.40+
- **GitHub**: プライベートリポジトリ

#### Python環境
- **Python**: 3.11
  - **Databricks Apps側の動作環境と合わせるため3.11必須**
- **venv**: 仮想環境管理
- **pip**: パッケージ管理

---

### TR-DEV-002: コード品質ツール

**決定理由**: コード品質の維持と統一

#### リンター
- **Pylint**: Pythonコード品質チェック
- **Flake8**: PEP 8準拠チェック

#### フォーマッター
- **Black**: コード自動フォーマット
- **設定**: 行長88文字

#### 型チェック
- **MyPy**: 静的型チェック (オプション)

---

### TR-DEV-003: ローカル開発環境

**重要**: ローカル開発環境は**Flask Webアプリケーションの開発のみ**を対象とします。Azure IoT Services、Databricks Platform、Unity Catalog等のAzure環境コンポーネントは使用しません。

#### 構成
- **範囲**: Flask Webアプリケーションのみ
- **実行環境**: 開発者のローカルマシン（Windows）
- **Flask開発サーバー**: `localhost:5000`
- **データベース**: 開発用MySQL互換DB（ローカルまたは開発用リモートDB）
- **認証**: ブラウザ拡張機能でヘッダ偽装（リバースプロキシ未使用）
- **IoTデータ**: サンプルデータまたはモックデータを使用
- **Azure環境**: 不要（検証・本番環境でのみ必要）

#### セットアップ
```bash
# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# パッケージインストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .env を編集

# アプリケーション起動
flask run
```

---

### TR-DEV-004: Docker開発環境（推奨）

**決定理由**:
- 開発環境の再現性向上
- 依存関係の統一管理
- チーム内での環境差異を最小化
- Databricks Apps (App Compute) の実行環境に近い構成を実現

**重要**: Docker環境は**ローカル開発のみ**を対象とします。検証・本番環境ではDatabricks App Computeを使用します。

#### 前提条件
- **Docker Desktop for Windows**: 20.10以上
- **Docker Compose**: 2.0以上
- **WSL2**: Windows環境で推奨

#### 構成

**コンテナ構成**:
```yaml
services:
  flask-app:
    - Python 3.11 (Databricks Apps互換)
    - Flask 3.0+
    - ポート: 5000

  mysql-db:
    - MySQL互換データベース (開発用OLTP DB)
    - ポート: 3306
```

**ボリューム**:
- アプリケーションコード: ホストとコンテナでマウント（ホットリロード対応）
- データベースデータ: 永続化ボリューム

#### セットアップ手順

**1. Docker環境の準備**
```bash
# Docker Desktopがインストールされていることを確認
docker --version
docker-compose --version
```

**2. プロジェクトのセットアップ**
```bash
# リポジトリをクローン
git clone <repository-url>
cd <project-directory>

# 環境変数ファイルを作成
cp .env.example .env
# .env を編集（DB接続情報など）
```

**3. Docker環境の起動**
```bash
# コンテナをビルド・起動
docker-compose up -d

# ログ確認
docker-compose logs -f flask-app

# アプリケーションアクセス
# http://localhost:5000
```

**4. 開発作業**
```bash
# コンテナ内でコマンド実行
docker-compose exec flask-app bash

# パッケージ追加時
docker-compose exec flask-app pip install <package>
docker-compose exec flask-app pip freeze > requirements.txt

# データベース操作
docker-compose exec mysql-db mysql -u root -p
```

**5. 環境の停止・削除**
```bash
# 停止
docker-compose stop

# 停止・削除
docker-compose down

# データベース含めて完全削除
docker-compose down -v
```

#### docker-compose.yml 例

```yaml
version: '3.8'

services:
  flask-app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    volumes:
      - .:/app
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
      - DATABASE_URL=mysql://user:password@mysql-db:3306/iot_db
    depends_on:
      - mysql-db
    command: flask run --host=0.0.0.0

  mysql-db:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=iot_db
      - MYSQL_USER=user
      - MYSQL_PASSWORD=password
    volumes:
      - mysql-data:/var/lib/mysql

volumes:
  mysql-data:
```

#### Dockerfile 例

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# システム依存パッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Pythonパッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# Flask実行
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]
```

#### .dockerignore 例

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
.env
.git
.gitignore
.vscode
*.md
docs/
```

#### 注意事項

**対象範囲**:
- Flask Webアプリケーション
- MySQL互換データベース (OLTP DB)

**開発時の留意点**:
- コンテナ内のPython 3.11はDatabricks Apps互換
- リバースプロキシ未使用のため、ブラウザ拡張機能でヘッダ偽装が必要
- サンプルデータまたはモックデータを使用
- 本番デプロイ時はDatabricks CLIまたはGitリポジトリ連携を使用

**トラブルシューティング**:
- ポート競合時: `docker-compose.yml` のポート番号を変更
- ボリュームマウントエラー: Docker Desktopの共有設定を確認
- データベース接続エラー: `.env` の接続情報を確認

---

## 10. セキュリティ要件

### TR-SEC-001: 認証・認可

**重要**: ログイン認証はDatabricks標準機能であり、Flaskアプリでは実装しない。アプリではリバースプロキシが付与するヘッダ情報からユーザーを識別する。

#### 実装
```python
from flask import request

def get_current_user():
    """リバースプロキシヘッダからユーザー情報取得

    注意: 認証はDatabricks標準機能で行われる。
    この関数は認証済みユーザーの識別のみを行う。
    """
    user_id = request.headers.get('X-Databricks-User-Id')
    access_token = request.headers.get('X-Databricks-Access-Token')
    if not user_id or not access_token:
        raise Unauthorized('Authentication required')
    return user_id
```

#### Databricks API認証戦略

**決定理由**: Databricks Groups APIは管理者権限が必要なため、操作内容によって認証情報を使い分ける必要がある

**認証情報の使い分け**:
- **Databricks Groups API呼び出し**: サービスプリンシパルの認証情報を使用
  - 対象: ユーザー、組織管理のCUD操作時のグループ作成/更新/削除
  - 理由: Databricksワークスペースのグループ制御には管理者ロールが必須
  - サービスプリンシパルには管理者ロールを割り当てる
- **OLTP DBへのマスタCRUD操作**: 共通のDBアカウントを使用
  - 対象: 組織、ユーザー、デバイスなどのマスタデータ操作
  - 理由: OLTP DBはアプリケーション専用のデータストアであり、ユーザー認証情報は不要
  - データスコープ制限はアプリケーション層で実装
- **Unity Catalogアクセス**: ログインユーザーの認証情報を使用
  - 対象: センサーデータ取得、分析データアクセス
  - 理由: 動的ビューの `is_member()` によるスコープ制限を適用するため

**実装例**:
```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.iam import Group

# 組織登録処理
@admin_bp.route('/api/admin/organizations', methods=['POST'])
@role_required(Role.SYSTEM_ADMIN, Role.ADMIN, Role.SALES_USER)
def create_organization():
    """組織登録（OLTP DB + Databricks Group連携）"""

    # 1. OLTP DBへの組織登録（共通アカウントで接続、データスコープはアプリケーション層で制御）
    cursor.execute(
        "INSERT INTO organizations (name, type, ...) VALUES (%s, %s, ...)",
        (org_name, org_type, ...)
    )
    organization_id = cursor.lastrowid

    # 2. Databricks Groups API呼び出し（サービスプリンシパルの権限で実行）
    group_id = create_databricks_group(organization_id, org_name)

    # 3. グループIDをOLTP DBに保存
    cursor.execute(
        "UPDATE organizations SET databricks_group_id = %s WHERE id = %s",
        (group_id, organization_id)
    )

    return jsonify({'success': True, 'organization_id': organization_id})

def create_databricks_group(organization_id, organization_name):
    """Databricksグループを作成（管理者権限が必要）"""
    # サービスプリンシパル認証（管理者ロール）
    w = WorkspaceClient(
        host=os.getenv('DATABRICKS_HOST'),
        token=os.getenv('DATABRICKS_SERVICE_PRINCIPAL_TOKEN')  # 管理者権限
    )

    group = w.groups.create(
        display_name=f"organization_{organization_id}"
    )
    return group.id

# Unity Catalogアクセス処理
def get_devices_from_unity_catalog():
    """デバイスデータをUnity Catalogから取得（ユーザー権限でアクセス）"""
    # ログインユーザーの認証情報（データスコープ制限が適用される）
    w = WorkspaceClient(
        host=os.getenv('DATABRICKS_HOST'),
        token=request.headers.get('X-Databricks-Access-Token')  # ユーザー権限
    )

    # Unity Catalogの動的ビュー（is_member()でスコープ制限が適用される）
    result = w.sql.execute_statement(
        warehouse_id=os.getenv('SQL_WAREHOUSE_ID'),
        statement="SELECT * FROM devices_view"
    )
    return result
```

**セキュリティ上の注意**:
- サービスプリンシパルのトークンは環境変数で管理し、コードにハードコードしない
- サービスプリンシパルはDatabricks Groups APIの呼び出しのみに使用する
- Unity Catalogへのアクセスには必ずログインユーザーの認証情報を使用する
- OLTP DBへのアクセスは共通アカウントを使用し、データスコープ制限はアプリケーション層で実装する

---

### TR-SEC-002: 入力検証

**決定理由**: SQLインジェクション、XSS対策

#### パラメータ化クエリ
```python
# ✅ 推奨
cursor.execute(
    "SELECT * FROM devices WHERE device_id = %s",
    (device_id,)
)

# ❌ 禁止
query = f"SELECT * FROM devices WHERE device_id = '{device_id}'"
```

#### XSS対策
- Jinja2自動エスケープ有効化
- HTMLタグのサニタイズ

---

### TR-SEC-003: セキュアヘッダ

**決定理由**: セキュリティ強化

#### 実装
```python
from flask import Flask

app = Flask(__name__)

@app.after_request
def set_secure_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

---

### TR-SEC-004: ロールベースアクセス制御実装

**決定理由**: 4つのロール（システム保守者、管理者、販社ユーザ、サービス利用者）に応じた機能アクセス制御

#### ロール定義
```python
# models/role.py
from enum import Enum

class Role(Enum):
    SYSTEM_ADMIN = "システム保守者"
    ADMIN = "管理者"
    SALES_USER = "販社ユーザ"
    SERVICE_USER = "サービス利用者"
```

#### ユーザー情報取得ヘルパー関数
```python
# auth/helpers.py
from flask import request
from werkzeug.exceptions import Unauthorized

def get_current_user():
    """リバースプロキシヘッダからユーザーIDを取得"""
    user_id = request.headers.get('X-Databricks-User-Id')
    if not user_id:
        raise Unauthorized('Authentication required')
    return user_id

def get_user_info(user_id):
    """OLTP DBからユーザー情報を取得"""
    query = "SELECT user_id, role, sales_company_id, customer_id FROM users WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()

    if not user:
        raise Unauthorized('User not found')

    return {
        'user_id': user['user_id'],
        'role': user['role'],
        'sales_company_id': user['sales_company_id'],
        'customer_id': user['customer_id']
    }
```

#### デコレーター実装
```python
# decorators/auth.py
from functools import wraps
from flask import abort, jsonify, request
from auth.helpers import get_current_user, get_user_info

def role_required(*allowed_roles):
    """
    ロールベースのアクセス制御デコレーター

    使用例:
    @role_required(Role.SYSTEM_ADMIN, Role.ADMIN)
    def admin_only_function():
        pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # リバースプロキシヘッダからユーザーIDを取得
            user_id = get_current_user()

            # OLTP DBからユーザー情報を取得
            user_info = get_user_info(user_id)
            user_role = user_info['role']

            if user_role not in [role.value for role in allowed_roles]:
                # APIの場合はJSON、画面の場合は403ページ
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({
                        "error": "Forbidden",
                        "message": "この操作を実行する権限がありません"
                    }), 403
                else:
                    abort(403)  # Forbidden

            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

#### 使用例
```python
# routes/device_inventory.py
from flask import Blueprint
from decorators.auth import role_required
from models.role import Role

device_inventory_bp = Blueprint('device_inventory', __name__)

@device_inventory_bp.route('/admin/device-inventory')
@role_required(Role.SYSTEM_ADMIN)  # システム保守者のみアクセス可能
def device_inventory_list():
    """デバイス台帳一覧（システム保守者専用）"""
    return render_template('admin/device_inventory/list.html')

@device_inventory_bp.route('/admin/alerts/settings/<int:alert_id>/delete', methods=['POST'])
@role_required(Role.SYSTEM_ADMIN, Role.ADMIN, Role.SALES_USER)  # サービス利用者は削除不可
def delete_alert_setting(alert_id):
    """アラート設定削除"""
    # 削除処理
    return jsonify({"success": True})
```

---

### TR-SEC-005: データスコープ制限実装

**決定理由**: 組織階層に基づいたデータアクセス範囲の制限（全ユーザー共通のフィルタリングロジック、ユーザーの所属組織および下位組織のデータのみアクセス可能）

#### Unity Catalog動的ビュー実装
```sql
-- devices_view.sql
-- すべてのユーザーに対して組織階層ベースのフィルタリングを適用
-- ロールによる条件分岐は一切行わない
CREATE OR REPLACE VIEW devices_view AS
SELECT
    d.device_id,
    d.device_name,
    d.organization_id,
    d.status,
    d.last_communication_time
FROM devices d
WHERE d.delete_flag = FALSE
  AND EXISTS (
    -- 組織階層によるフィルタリング（全ユーザー共通）
    SELECT 1
    FROM organization_closure oc
    WHERE oc.parent_organization_id = current_user_organization_id()
      AND oc.subsidiary_organization_id = d.organization_id
  );

-- organizations_view.sql
-- 組織マスタの動的ビュー（組織管理画面で使用）
CREATE OR REPLACE VIEW organizations_view AS
SELECT
    o.organization_id,
    o.organization_name,
    o.parent_organization_id,
    o.organization_type
FROM organizations o
WHERE o.delete_flag = FALSE
  AND EXISTS (
    -- 組織階層によるフィルタリング（全ユーザー共通）
    SELECT 1
    FROM organization_closure oc
    WHERE oc.parent_organization_id = current_user_organization_id()
      AND oc.subsidiary_organization_id = o.organization_id
  );
```

#### OLTP DBフィルタリング実装
```python
# repositories/device_repository.py
from flask import request
from models.role import Role
from auth.helpers import get_current_user, get_user_info

def get_devices_filtered():
    """組織階層に基づいてフィルタリングされたデバイス一覧を取得

    すべてのユーザーに対して同じフィルタリングロジックを適用。
    ロールによる条件分岐は一切行わない。
    """
    # リバースプロキシヘッダからユーザーIDを取得
    user_id = get_current_user()

    # OLTP DBからユーザー情報を取得
    user_info = get_user_info(user_id)
    current_user_organization_id = user_info['organization_id']

    # 組織階層ベースのフィルタリング（全ユーザー共通）
    # ロールによる条件分岐は一切行わない
    base_query = """
        SELECT * FROM devices
        WHERE organization_id IN (
            SELECT subsidiary_organization_id
            FROM organization_closure
            WHERE parent_organization_id = %s
        )
    """
    params = [current_user_organization_id]

    cursor.execute(base_query, params)
    return cursor.fetchall()

def get_device_by_id(device_id):
    """デバイス詳細取得（スコープチェック付き）"""
    # リバースプロキシヘッダからユーザーIDを取得
    user_id = get_current_user()

    # OLTP DBからユーザー情報を取得
    user_info = get_user_info(user_id)
    user_role = user_info['role']
    sales_company_id = user_info['sales_company_id']
    customer_id = user_info['customer_id']

    query = "SELECT * FROM devices WHERE device_id = %s"
    params = [device_id]

    # ロール別スコープチェック
    if user_role == Role.SALES_USER.value:
        query += " AND sales_company_id = %s"
        params.append(sales_company_id)
    elif user_role == Role.SERVICE_USER.value:
        query += " AND customer_id = %s"
        params.append(customer_id)

    cursor.execute(query, params)
    device = cursor.fetchone()

    if not device:
        # データが見つからない、またはアクセス権限がない
        raise NotFound("デバイスが見つかりません")

    return device
```

#### CSVエクスポート時のスコープ制限
```python
# services/csv_export_service.py
def export_devices_csv():
    """デバイスをCSVエクスポート（スコープ制限適用）"""
    # get_devices_filtered()は自動的にスコープ制限を適用
    devices = get_devices_filtered()

    # CSVファイル生成
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['デバイスID', 'デバイス名', '組織ID', '販社ID', 'ステータス'])

    for device in devices:
        writer.writerow([
            device['device_id'],
            device['device_name'],
            device['organization_id'],
            device['sales_company_id'],
            device['status']
        ])

    return output.getvalue()
```

---

## 11. パフォーマンス要件

### TR-PERF-001: データストア使い分け

**決定理由**: 適材適所によるパフォーマンス最適化

#### 使い分け基準
- **OLTP DB使用**: マスタデータ、デバイスステータス
- **Unity Catalog使用**: センサーデータ

---

### TR-PERF-002: 接続プーリング

**決定理由**: データベース接続オーバーヘッド削減

#### 実装
```python
# MySQL接続プール
mysql_pool = pymysql.pooling.ConnectionPool(
    pool_size=5,
    host=os.getenv('MYSQL_HOST'),
    ...
)

# 接続取得
connection = mysql_pool.get_connection()
```

---

### TR-PERF-003: キャッシュ戦略

**決定理由**: 応答時間短縮

#### 実装方針
- Jinja2テンプレートキャッシュ
- 静的ファイルのブラウザキャッシュ (Cache-Control)
- マスタデータのメモリキャッシュ検討

---

## 12. 監視・ログ要件

### TR-MON-001: ログ出力

**決定理由**: トラブルシューティングと監査証跡

#### ログ出力先
```python
import logging

# Unity Catalogへのログ出力
def log_to_unity_catalog(level, message):
    databricks_sql.execute(
        "INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)",
        (datetime.now(), level, message)
    )

# または外部ログアダプター
def log_to_external(level, message):
    requests.post(external_log_endpoint, json={
        'level': level,
        'message': message
    })
```

#### ログレベル
- ERROR: エラー・例外発生時
- WARNING: 警告事項
- INFO: 主要な処理フロー
- DEBUG: 開発時のデバッグ情報 (本番環境では無効化)

---

### TR-MON-002: 監視

**決定理由**: システム稼働状況の把握

#### 監視項目
- App Compute URL死活監視 (外部監視ツール)
- Databricks Compute Clusterメトリクス
- データベースクエリ実行時間
- API応答時間

---

## 13. アクセシビリティ要件

### TR-ACCESS-001: セマンティックHTML

**決定理由**: スクリーンリーダー対応

#### 実装
```html
<header>
  <nav>
    <ul>
      <li><a href="/dashboard">ダッシュボード </a></li>
    </ul>
  </nav>
</header>
<main>
  <section>
    <h1>デバイス管理</h1>
  </section>
</main>
```

---

### TR-ACCESS-002: フォームアクセシビリティ

**決定理由**: ユーザビリティ向上

#### 実装
```html
<form>
  <label for="device-name">デバイス名</label>
  <input id="device-name" name="device_name" type="text" required>

  <button type="submit">登録</button>
</form>
```

---

## 14. 拡張性要件

### TR-EXTEND-001: モジュール化

**決定理由**: 保守性と拡張性の向上

#### Flask Blueprint構成
```
app/
├── __init__.py
├── dashboard/          # ダッシュボード (DSH-001)
│   ├── __init__.py
│   └── views.py        # /, /dashboard - ダッシュボード表示（対話型AI含む）
├── admin/              # 管理機能 (ADM-001〜016)
│   ├── __init__.py
│   ├── devices.py      # /admin/devices/* - デバイス管理
│   ├── users.py        # /admin/users/* - ユーザー管理
│   ├── organizations.py # /admin/organizations/* - 組織管理
│   └── device_inventory.py # /admin/device-inventory/* - デバイス台帳管理
├── alert/              # アラート機能 (ALT-001〜006)
│   ├── __init__.py
│   ├── alert_settings.py # /alert/alert-settings/* - アラート設定
│   └── alert_history.py # /alert/alert-history/* - アラート履歴
├── notice/             # 通知機能 (NTC-001〜006)
│   ├── __init__.py
│   ├── mail_settings.py # /notice/mail-settings/* - メール通知設定
│   └── mail_history.py      # /notice/mail-history/* - メール通知履歴
├── account/            # アカウント (ACC-001〜002)
│   ├── __init__.py
│   └── views.py        # /account/* - 言語設定、ユーザ情報参照
├── transfer/           # インポート (TRF-001)
│   ├── __init__.py
│   └── views.py        # /transfer/* - CSVインポート
├── models/
│   ├── __init__.py
│   ├── device.py
│   ├── user.py
│   ├── organization.py
│   ├── alert.py
│   └── notification.py
└── utils/
    ├── __init__.py
    ├── databricks.py
    └── mysql.py
```

---

## 15. 受け入れ基準

以下の基準をすべて満たすこと：

### 技術スタック
- [ ] Python 3.11を使用していること
- [ ] Flask 3.0以上を使用していること
- [ ] requirements.txtでバージョンが固定されていること

### コード品質
- [ ] Pylintエラーが0件であること
- [ ] テストカバレッジが80%以上であること
- [ ] コードレビューが実施されていること

### セキュリティ
- [ ] SQLインジェクション対策が実装されていること
- [ ] XSS対策が実装されていること
- [ ] CSRF対策が実装されていること
- [ ] 機密情報がログに出力されていないこと

### パフォーマンス
- [ ] 接続プーリングが実装されていること
- [ ] データストア使い分けが適切であること
- [ ] API応答時間が500ms以内であること

### デプロイ
- [ ] Databricks App Computeにデプロイできること
- [ ] 環境変数が適切に設定されていること
- [ ] デプロイ時間が30分以内であること

### ドキュメント
- [ ] README.mdが整備されていること
- [ ] API仕様書が整備されていること
- [ ] 関数・クラスのDocstringが記述されていること

---

## 編集履歴

| 日付 | バージョン | 編集者 | 変更内容 |
|------|------------|--------|----------|
| 2025-11-14 | 1.0 | Claude | 初版作成（Databricks IoTシステムの技術要件を定義） |
| 2025-11-14 | 2.0 | Claude | 画像1・画像2の情報を反映。TR-SEC-004（ロールベースアクセス制御実装）追加、TR-SEC-005（データスコープ制限実装）追加、TR-BE-004（CSVインポート/エクスポート機能）追加 |
| 2025-11-20 | 3.0 | Claude | インフラネットワーク資料反映。ネットワーク構成セクション追加、Entra ID認証基盤、Private Link通信、Event Hubs Capture、ADLS、コンピュートプレーン構造を追加 |
| 2025-11-21 | 3.1 | Claude | functional-requirements.mdとの整合性確認: CSVインポート/エクスポート機能の機能IDをFR-006に更新、ダッシュボードがFR-006-1として分析機能内に統合された旨を反映 |
| 2025-11-25 | 3.2 | Claude | スケジュールバッチ機能削除に伴う更新: TR-BE-004のCSVインポート/エクスポート機能の機能IDをFR-006からFR-005に変更 |
| 2025-11-25 | 3.3 | Claude | 機能分類再編成: TR-BE-004のCSVインポート/エクスポート機能の機能IDをFR-005からFR-004-8（マスタ管理機能内）に変更 |
| 2025-11-25 | 3.4 | Claude | ログイン画面の整理: Databricks User認証セクションに「Flaskアプリでは実装しない」を明記、TR-SEC-001にログイン認証はDatabricks標準機能である旨を追加、get_current_user関数にコメント追加 |
| 2025-11-26 | 3.5 | Claude | Azure環境統合の明確化: システム構成にAzure環境統合を明記、TR-DEPLOY-003に3環境構成表を追加、TR-DEV-003にローカル開発環境はWebアプリのみである旨を明記 |
| 2025-11-26 | 3.6 | Claude | Flask Blueprint構成を画面カテゴリベースに更新: frontend.mdの構成に合わせて、dashboard/admin/alert/notice/account/transferの6つのBlueprintに整理、画面ID（DSH/ADM/ALT/NTC/ACC/TRF）との対応を明記 |
| 2025-12-04 | 3.7 | Claude | OLTP DB認証戦略の整理: TR-SEC-001のOLTP DBアクセス方式を「ログインユーザーの認証情報」から「共通アカウント」に変更、データスコープ制限はアプリケーション層で実装する旨を明記 |
