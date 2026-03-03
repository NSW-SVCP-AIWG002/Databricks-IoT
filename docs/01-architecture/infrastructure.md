# インフラストラクチャアーキテクチャ

## 概要

Databricks IoTシステムのインフラストラクチャは、**Azure環境内に統合されたDatabricks PlatformとAzure IoT Services**を中心に、MySQL互換データベース、Flaskアプリケーションを統合した構成です。IoTデバイスからのデータをリアルタイムで収集・処理し、分析・可視化する包括的なプラットフォームを提供します。

**重要**: Azure IoT Hubs、Event Hubs、ADLS、Databricks Platformは、すべて**同一のAzure環境内**にデプロイされます。Private Linkによる閉域接続により、低レイテンシーかつ高セキュリティなデータ連携を実現しています。

**インフラストラクチャ構成図**

```
┌─────────────────────────────────────────────────────────────────┐
│                         IoT Device Layer                        │
│  各種IoTデバイス・センサー (MQTT通信)                             │
└─────────────────────────────────────────────────────────────────┘
                               │ MQTT
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Azure                                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐                                               │
│  │ Entra ID     │                                               │
│  │ - ユーザ認証  │                                               │
│  │ - トークン発行 │                                              │
│  └──────────────┘                                               │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Resource Group                                           │  │
│  │                                                           │  │
│  │  ┌──────────────┐    ┌──────────────┐                     │  │
│  │  │ IoT Hub      │───▶│ Event Hub    │                     │  │
│  │  │ - MQTT受信   │    │ - Kafka配信    │                    │  │
│  │  │- デバイス管理 │    │ - Capture→ADLS│                    │  │
│  │  └──────────────┘    └──────────────┘                     │  │
│  │                                                           │  │
│  │  ┌────────────┐  ┌────────────┐                           │  │
│  │  │ ADLS       │  │ Azure DNS  │                           │  │
│  │  │ (Unity     │  │ (Private   │                           │  │
│  │  │ Catalog)   │  │ Zones)     │                           │  │
│  │  └────────────┘  └────────────┘                           │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  VNet                                               │  │  │
│  │  │                                                     │  │  │
│  │  │  ┌───────────────────────────────────────────────┐  │  │  │
│  │  │  │ パブリック/プライベートサブネット                │  │  │  │
│  │  │  │  - クラシックコンピュートプレーン (VMSS)         │  │  │  │
│  │  │  └───────────────────────────────────────────────┘  │  │  │
│  │  │                                                     │  │  │
│  │  │  ┌───────────────────────────────────────────────┐  │  │  │
│  │  │  │ DBサブネット                                   │  │  │  │
│  │  │  │  - Private Link (MySQL)                       │  │  │  │
│  │  │  │  - MySQL DB                                   │  │  │  │
│  │  │  └───────────────────────────────────────────────┘  │  │  │
│  │  │                                                     │  │  │
│  │  │  ┌───────────────────────────────────────────────┐  │  │  │
│  │  │  │ プライベートエンドポイントサブネット             │  │  │  │
│  │  │  │  - Private Link (databricks_ui_api)           │  │  │  │
│  │  │  │  - Private Link (dfs)                         │  │  │  │
│  │  │  │  - Private Link (EventHub)                    │  │  │  │
│  │  │  └───────────────────────────────────────────────┘  │  │  │
│  │  │                                                     │  │  │
│  │  │  ┌───────────────────────────────────────────────┐  │  │  │
│  │  │  │ 踏み台サブネット                               │  │  │  │
│  │  │  │  - 踏み台サーバ (VM)                           │  │  │  │
│  │  │  └───────────────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Databricks (Databricks社管理NW)                          │  │
│  │  ┌───────────────────────────────────────────────────┐    │  │
│  │  │ コントロールプレーン                                │    │  │
│  │  │  - ワークスペースUI/API認証                         │    │  │
│  │  └───────────────────────────────────────────────────┘    │  │
│  │  ┌───────────────────────────────────────────────────┐    │  │
│  │  │ サーバレスコンピューティングプレーン                 │    │  │
│  │  │  - LDP パイプライン (ストリーミング)                │    │  │
│  │  └───────────────────────────────────────────────────┘    │  │
│  │  ┌───────────────────────────────────────────────────┐    │  │
│  │  │ Unity Catalog                                     │    │  │
│  │  │  - ADLS上のDelta Lakeストレージ                    │    │  │
│  │  │  - ブロンズ/シルバー/ゴールド層                     │    │  │
│  │  └───────────────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## ネットワーク通信経路

### フロント経路（ユーザ／管理アクセス）
- インターネット → Entra ID（ユーザ認証・トークン発行）
- インターネット → Databricks ワークスペース（認証、※アクセス元IP制限実施）
- インターネット ↔ IoT Hub（デバイス双方向通信）
- インターネット → Azure App service（公開フロント、※アクセス元IP制限実施）

### データフロー（インジェスト～保管）
- IoT Hub → Event Hub（テレメトリ転送）
- サーバレス/クラシックコンピューティングプレーン → Event Hub（Private Link経由ストリーミング）
- Event Hub → ADLS（Capture機能でRAWデータ出力）
- サーバレス/クラシックコンピューティングプレーン → ADLS（Private Link経由読み書き）

### OLTP DBアクセス
- サーバレス/クラシックコンピューティングプレーン → MySQL DB（Private Link経由）
- 踏み台VM → MySQL DB（メンテナンス経路）

### ユーザ管理
- Azure App Service → Entra ID（ユーザアカウント制御）
- Azure App service → Databricks コントロールプレーン

## 主要コンポーネント

### 1. Databricks Platform (Premium ライセンス)

**役割**: データ処理・分析・アプリケーション実行の中核プラットフォーム

**構成要素**:
- **Lakeflow 宣言型パイプライン (LDP)**: Python/SQLでのストリーミングデータ処理
- **App Compute (サーバレスコンピューティングプレーン)**: Flask Webアプリケーションの実行環境
- **クラシックコンピューティングプレーン (VMSS)**: 顧客VNet内のCompute Cluster
- **Unity Catalog**: ADLS (Azure Data Lake Storage) 上のDelta Lakeによるデータ管理
- **SQL Warehouse**: データアクセス用のSQLエンドポイント
- **認証基盤**: 共通モジュール化により、Azure/AWS/オンプレミス環境に対応。OAuth トークン フェデレーションによるデータスコープ制御
- **システムテーブル**: 監査ログの保存

**技術仕様**:
- **データ処理**: メダリオンアーキテクチャ (ブロンズ/シルバー/ゴールド)
- **アクセス方式**: SQL Warehouse経由、@databricks/sql ドライバー使用

### 2. Azure IoT Services

**役割**: IoTデバイスとの通信ハブおよびストリーミングデータ配信

**構成要素**:
- **Azure IoT Hubs**:
  - IoTデバイスとの双方向通信
  - MQTTプロトコル受信
  - 下り電文送信 (デバイスへのコマンド)
  - デバイス管理
- **Event Hubs**:
  - Kafkaエンドポイント提供
  - ストリーミングデータ配信
  - Databricks LDPへのデータソース
  - **Event Hubs Capture**: ADLSにRAWデータを継続的に出力

**通信プロトコル**:
- **上り**: MQTT (デバイス → IoT Hubs)
- **下り**: MQTT (IoT Hubs → デバイス)
- **配信**: Kafka Stream (Event Hubs → Databricks)
- **Capture**: Event Hubs → ADLS (RAWデータ保存)
- **REST変換**: 必要に応じてMQTT → REST変換を実施

**データフロー（インジェスト経路）**:
1. IoTデバイス → IoT Hub (MQTT)
2. IoT Hub → Event Hub (テレメトリ転送)
3. Event Hub → ADLS (Capture機能でRAWデータ保存)
4. Event Hub → Databricks LDP (Kafka経由でストリーミング処理)

### 3. MySQL互換データベース (OLTP)

**役割**: オンライン性能が必要なデータの高速アクセス

**技術仕様**:
- **互換性**: SingleStore互換
- **格納データ**:
  - マスタデータ (デバイス情報、ユーザー情報など)
  - デバイスステータス
  - 設定情報
- **アクセス方式**:
  - Flask AppからPython MySQLドライバー経由
  - **Private Link経由**: サーバレス/クラシックコンピューティングプレーンからPrivate Link経由で接続
- **ネットワーク配置**: プライベートネットワーク内に配置

**メンテナンスアクセス**:
- **踏み台サーバ (Bastion VM)**:
  - プライベートネットワーク配置のMySQL DBへのメンテナンスアクセス用
  - インターネット → 踏み台VM → MySQL DB
  - DBメンテナンス、運用作業に使用

**使い分け基準**:
- **OLTP DB使用**: マスタデータ、デバイスステータス
- **Unity Catalog使用**: センサーデータ

### 4. Flask Application (App Compute)

**役割**: Webアプリケーション・管理画面

**実行環境**:
- **プラットフォーム**: Databricks App Compute
- **フレームワーク**: Flask (Python)
- **パッケージ管理**: pip (requirements.txt)
- **デプロイ方式**: GitリポジトリPull or アセット圧縮ファイルアップロード

**機能**:
- 管理画面 
- ダッシュボード (Databricksダッシュボードiframe埋め込み)
- REST API (フロントエンド・外部連携)

**制約事項**:
- 1ファイル10MB以下
- コンテナ再起動時にログが消失 (対策: 外部ログアダプター使用)
- シングルトン保証について要調査 (懸念事項)

### 5. 環境構成

本システムは、3つの環境で構成されます。Azure環境は検証・本番の2つのインスタンスが存在します。

#### 環境一覧

| 環境                 | 構成                          | Azure環境                     | 用途                                           |
| -------------------- | ----------------------------- | ----------------------------- | ---------------------------------------------- |
| **ローカル開発環境** | Flask Webアプリケーションのみ | 不要                          | 開発者のローカルマシンでのアプリケーション開発 |
| **検証環境**         | Azure環境全体                 | Azure（検証用Resource Group） | 結合テスト、E2Eテスト                          |
| **本番環境**         | Azure環境全体                 | Azure（本番用Resource Group） | 本番運用                                       |

#### 環境別コンポーネント配置

| コンポーネント             | ローカル開発       | 検証環境               | 本番環境                   |
| -------------------------- | ------------------ | ---------------------- | -------------------------- |
| Flask Webアプリケーション  | ○ (localhost:5000) | ○ (Azure Apps Service) | ○ (Azure App Serivce Apps) |
| Azure IoT Hubs             | ×                  | ○                      | ○                          |
| Event Hubs (Kafka)         | ×                  | ○                      | ○                          |
| Event Hubs Capture         | ×                  | ○                      | ○                          |
| ADLS Gen2                  | ×                  | ○                      | ○                          |
| Databricks Platform        | ×                  | ○                      | ○                          |
| Lakeflow パイプライン      | ×                  | ○                      | ○                          |
| Unity Catalog (Delta Lake) | ×                  | ○                      | ○                          |
| SQL Warehouse              | ×                  | ○                      | ○                          |
| Databricks Dashboard       | ×                  | ○                      | ○                          |
| MySQL互換データベース      | ○ (開発用DB)       | ○ (検証用DB)           | ○ (本番用DB)               |
| Entra ID認証               | × (モックヘッダ)   | ○                      | ○                          |
| Private Link               | ×                  | ○                      | ○                          |
| Azure DNS                  | ×                  | ○                      | ○                          |

#### ローカル開発環境 (開発者PC)ｋ

**範囲**: Flask Webアプリケーションの開発のみ

**構成**:
- **Flask App**: ローカル開発サーバー (localhost)
- **起動方法**: `python app.py` または `flask run`
- **アクセスURL**: `http://localhost:5000`
- **データベース**: 開発用MySQL互換データベース（ローカルまたは開発用リモートDB）
- **認証**: リバースプロキシヘッダのモック（開発用の固定ヘッダ値、ブラウザ拡張機能でヘッダ偽装）
- **IoTデータ**: サンプルデータまたはモックデータを使用
- **テスト範囲**: 単体テスト、簡易的な機能テスト

**特性**:
- Azure環境不要（Flask Appのみ）
- Databricks Platform不使用
- リバースプロキシがないため、ヘッダ偽装で開発

#### 検証環境 (Azure全体)

**範囲**: Azure環境全体（Azure IoT Services + Databricks Platform）

**構成**:
- **Flask App**: Azure App Service上で実行
- **デプロイ先**: Azure Resource Group（検証用）
- **実行環境**: Azure App Service
- **アクセスURL**: `https://[workspace-url]/apps/[app-name]`
- **データベース**: Unity Catalog (検証環境) + OLTP DB (検証用DB)
- **認証**: 共通認証モジュール（Azure環境: Easy Auth）、OAuth トークン フェデレーション有効、リバースプロキシ有効
- **ネットワーク**: Private Link + Azure DNS による閉域接続
- **デプロイ**: GitリポジトリからPull
- **監視**: Databricks システムテーブル、外部ログアダプター

**特性**:
- Azure環境全体が必要（IoT Hub、Event Hub、ADLS、Databricks、MySQL、認証基盤）
- 結合テスト、E2Eテスト、パフォーマンステスト実施
- 本番環境と同等の構成（Resource Groupが分離）

#### 本番環境 (Azure全体)

**範囲**: Azure環境全体（Azure IoT Services + Databricks Platform）

**構成**:
- **Flask App**: Azure App Service (本番インスタンス)
- **デプロイ先**: Azure Resource Group（本番用）
- **実行環境**: Azure App Service
- **アクセスURL**: `https://[workspace-url]/apps/[app-name]`
- **データベース**: Unity Catalog (本番) + OLTP DB (本番用DB)
- **認証**: 共通認証モジュール（Azure環境: Easy Auth）、OAuth トークン フェデレーション有効、リバースプロキシ有効
- **ネットワーク**: Private Link + Azure DNS による閉域接続
- **デプロイ**: Databricks CLI or Gitリポジトリ連携
- **監視**: App Compute URL死活監視 (503 Service Unavailable)、Databricks システムテーブル、外部ログアダプター

**特性**:
- Azure環境全体が必要（IoT Hub、Event Hub、ADLS、Databricks、MySQL、認証基盤）
- 実IoTデバイスからのデータ処理
- 検証環境と同等の構成（Resource Groupが分離）

## セキュリティ

### 1. 認証・認可

**認証基盤**:
- **認証共通モジュール**: 「Azure環境(Easy Auth)」、「AWS環境(ALB＋cognito)」、「オンプレミス環境(自前認証)」の三パターンに対応可能
- **Databricks接続**: OAuth トークン フェデレーションによるユーザー単位認証
  - データスコープ制御を実現
  - インターネット → IdP でユーザ認証・トークン発行
  - アプリケーション → Databricks (Unity Catalog) へのOAuth Token Exchange
- **アクセス元IP制限**:
  - Databricks ワークスペースへのアクセス元IP制限を実施
  - 公開フロントへのアクセス元IP制限を実施

**認証フロー（Azure環境の例）**:
1. ユーザーがインターネット経由でEntra IDに認証リクエスト
2. Entra IDでユーザ認証・トークン発行
3. アプリケーション層でOAuth Token Exchangeを実行（Databricks Unity Catalog接続用）
4. リバースプロキシがリクエストヘッダにユーザ識別子・アクセストークンを付与
5. Flask Appへリクエストを転送
6. Unity Catalog接続時、OAuth トークン フェデレーションによりユーザー単位のデータスコープ制御を実現

**ユーザー権限管理**:
- サービスプリンシパル権限: App Compute処理の実行権限
- ユーザー認可API: 組織階層に基づいたデータアクセス範囲制御
  - `organization_closure` テーブルを活用した下位組織の取得
  - ロールは動線制御（UI要素の表示/非表示）のみに使用
- 動的ビュー: 組織階層（organization_closure）に基づいたデータフィルタリング
  - `current_user_organization_id()` 関数で現在のユーザーの組織IDを取得
  - 閉包テーブルで下位組織をフィルタリング

**ユーザ管理**:
- Azure App Service → Entra ID: Entra IDでのユーザアカウント制御
- Azure App Service → Databricks コントロールプレーン: DBXアカウント制御（SCIM API）

### 2. データアクセス制御

**Unity Catalogセキュリティ**:
- テーブル・ビューレベルのアクセス制御
- 行レベル・列レベルセキュリティ
- 動的ビューによる組織階層ベースのデータ範囲制限
  - 全ユーザーに対して統一的なフィルタリングロジックを適用
  - ロールによる条件分岐なし

**OLTP DBセキュリティ**:
- データベース接続認証
- テーブルアクセス権限管理
- SQL Injection対策 (パラメータ化クエリ)

### 3. ネットワークセキュリティ

**Private Link によるセキュアな通信**:
すべての内部通信はPrivate Link経由で行い、パブリックインターネットを経由しない構成。

- **Event Hub用Private Link**:
  - サーバレスコンピューティングプレーン（パイプライン）→ Event Hub
  - クラシックコンピューティングプレーン（VMSS）→ Event Hub
- **ADLS用Private Link (dfs)**:
  - サーバレスコンピューティングプレーン → ADLS（読み書き）
  - クラシックコンピューティングプレーン → ADLS（読み書き）
- **MySQL用Private Link**:
  - サーバレスコンピューティングプレーン → MySQL DB
  - クラシックコンピューティングプレーン → MySQL DB
- **Databricks UI/API用Private Link**:
  - クラシックコンピューティングプレーン（VMSS）→ コントロールプレーン

**Azure DNS**:
- Private Link用の名前解決にAzure DNSを使用
- プライベートDNSゾーンでの名前解決

**外部通信制限**:
- セキュリティポリシーによる外部向け通信の制御
- 必要な外部サービスのみホワイトリスト化
- フロント経路のみインターネット公開（IP制限付き）

**HTTPS通信**:
- 全ての通信でHTTPS強制
- Databricks App ComputeのHTTPS対応

**コンピュートプレーン構成**:
- **サーバレスコンピューティングプレーン**: Databricks社管理NW内、パイプライン実行
- **クラシックコンピューティングプレーン (VMSS)**: 顧客VNet内、Private Link経由で各サービスに接続

### 4. 環境変数管理

**機密情報の保護**:
```python
# 環境変数による接続情報管理
DATABASE_URL = os.getenv('DATABASE_URL')
DATABRICKS_SQL_WAREHOUSE_ID = os.getenv('DATABRICKS_SQL_WAREHOUSE_ID')
DATABRICKS_TOKEN = os.getenv('DATABRICKS_TOKEN')
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
```

**環境別設定**:
- 開発環境: `.env`ファイル使用
- 結合テスト・本番: Databricks環境変数設定

## 監視・ログ

### 1. Databricks監視

**システムテーブル**:
- 監査ログの自動出力
- ユーザーアクティビティの記録
- アクセスログの保存

**パフォーマンス監視**:
- SQL Warehouse実行メトリクス
- LDPパイプライン処理状況
- App Computeリソース使用状況

### 2. アプリケーションログ

**App Computeログ管理**:
- **課題**: コンテナ内部ログは再起動時に消失
- **対策**: Unity Catalogまたは外部ログアダプターへの出力

**ログ出力先**:
```python
# Unity Catalogへのログ出力
import logging
logger = logging.getLogger(__name__)
# Unity Catalogテーブルへ書き込み

# または外部ログアダプター (例: Azure Log Analytics)
# 外部サービスへHTTP送信
```

**ログレベル**:
- ERROR: エラー・例外発生時
- WARNING: 警告事項
- INFO: 主要な処理フロー
- DEBUG: 開発時のデバッグ情報

### 3. 死活監視

**App Compute死活監視**:
- App Compute URLへの外部監視ツールからのアクセス
- 正常時: 200 OK
- Stop時: 503 Service Unavailable
- 認証の問題でヘルスチェックエンドポイント実装は難しい

**データベース監視**:
- Unity Catalog: Databricks標準監視
- OLTP DB: データベース管理ツールによる監視

### 4. アラート監視

**異常検知アラート**:
- LDPパイプライン内でのアラート判定
- Python処理による外部通知 (メール、Slack等)
- アラート履歴の記録

## デプロイメントフロー

### 1. App Computeデプロイフロー

```
開発 → Git Push → GitHub/GitLab (Private Repository)
                        │
                        ├─→ Databricks Pull (手動/自動)
                        │   └─→ App Compute配置
                        │
                        └─→ CI/CD Pipeline (将来)
                            └─→ Databricks CLI Deploy
```

**デプロイ手順**:
1. **開発者がGitリポジトリにプッシュ**
2. **Databricksコンソールから操作**:
   - 方法A: 外部GitリポジトリからPull
   - 方法B: アセット圧縮ファイルをアップロード (1ファイル10MB以下)
3. **App Compute側でフォルダ指定してコード配置**
4. **パッケージ管理システムが自動実行** (pip/npm)
5. **アプリケーション再起動**

### 2. Databricks リソースデプロイフロー

```
開発 → Databricks アセット バンドル作成
         │
         └─→ Databricks CLI実行
              └─→ パイプライン、クラスター定義のデプロイ
```

**デプロイ対象**:
- Lakeflow 宣言型パイプライン (LDP)
- Compute Cluster設定
- ジョブ定義
- Unity Catalogオブジェクト

**デプロイコマンド例**:
```bash
# Databricks CLI使用
databricks bundle deploy --target production
```

### 3. 環境別デプロイ戦略

**開発環境**:
- ローカルでの開発・単体テスト
- 頻繁なコード変更
- Databricks外部で実行

**検証環境**:
- GitリポジトリからDatabricksへPull
- 結合テスト実施
- App Compute + 実データベース接続

**本番環境**:
- GitリポジトリからDatabricksへPull
- Databricks CLIによる自動デプロイ検討
- デプロイ前の承認フロー

## スケーラビリティ

### Databricks スケーラビリティ

**自動スケーリング**:
- **Compute Cluster**: ワークロードに応じた自動スケール
- **SQL Warehouse**: クエリ負荷に応じたスケーリング
- **Delta Lake**: ペタバイト規模のデータ処理に対応

### データストア スケーラビリティ

**Unity Catalog (Delta Lake)**:
- 水平スケーリング対応
- センサーデータの効率的な保存
- パーティション戦略による性能最適化

**OLTP データベース**:
- MySQL互換DBのスケーリング機能活用
- 読み取りレプリカの検討
- シャーディング戦略 (必要に応じて)

### IoT データ取込みスケーラビリティ

**Event Hubs**:
- スループットユニットによるスケーリング
- パーティション数の調整
- 大量デバイスからの同時接続に対応

**Lakeflow パイプライン**:
- ストリーミング処理の並列化
- ブロンズ層データの短期保持によるストレージ最適化

### 将来のスケーリング戦略

- **App Computeの水平スケール**: 複数インスタンス構成の検討
- **キャッシュ層導入**: 頻繁なクエリ結果のキャッシュ
- **CDN活用**: 静的リソース配信の最適化
- **マイクロサービス化**: 機能分割による独立スケール

---

# インフラストラクチャコーディング制約

## 必須遵守事項

### 1. デプロイメント制約

**App Computeファイルサイズ制約**:
```python
# ✅ 推奨
# 1ファイル10MB以下に保つ
# 大きなファイルは分割または外部ストレージ使用

# ❌ 禁止
# 10MBを超えるファイルのアップロード
# 大容量の静的アセットをアプリに含める
```

**パッケージ管理**:
```python
# ✅ 推奨: requirements.txt
Flask==3.0.0
databricks-sql-connector==2.9.0
python-dotenv==1.0.0
pymysql==1.1.0

# ❌ 禁止: バージョン指定なし
Flask
databricks-sql-connector
```

**環境変数の命名**:
```python
# ✅ 推奨
DATABRICKS_SQL_WAREHOUSE_ID  # Databricks接続用
DATABRICKS_TOKEN             # 認証トークン
MYSQL_HOST                   # OLTP DB接続
MYSQL_DATABASE               # DB名

# ❌ 禁止
DB_ID                        # 不明確な命名
TOKEN                        # 汎用的すぎる命名
```

### 2. セキュリティ制約

**認証ヘッダ処理**:
```python
# ✅ 推奨: リバースプロキシヘッダの利用
from flask import request

def get_current_user():
    user_id = request.headers.get('X-Databricks-User-Id')
    access_token = request.headers.get('X-Databricks-Access-Token')
    if not user_id or not access_token:
        raise Unauthorized('Authentication required')
    return user_id

# ❌ 禁止: 独自認証実装
# 共通認証モジュールを使わずに独自実装
```

**SQL Injection対策**:
```python
# ✅ 推奨: パラメータ化クエリ
cursor.execute(
    "SELECT * FROM devices WHERE device_id = %s",
    (device_id,)
)

# ❌ 禁止: 文字列連結
query = f"SELECT * FROM devices WHERE device_id = '{device_id}'"
cursor.execute(query)  # SQLインジェクションリスク
```

**環境変数検証**:
```python
# ✅ 推奨: 起動時検証
import os

required_env_vars = [
    'DATABRICKS_SQL_WAREHOUSE_ID',
    'DATABRICKS_TOKEN',
    'MYSQL_HOST',
    'MYSQL_USER',
    'MYSQL_PASSWORD'
]

for env_var in required_env_vars:
    if not os.getenv(env_var):
        raise ValueError(f'Missing required environment variable: {env_var}')

# ❌ 禁止: 未検証での使用
db_host = os.getenv('MYSQL_HOST')  # 存在チェックなし
```

**機密情報のログ出力禁止**:
```python
# ✅ 推奨
logger.info(f'Database connection established to {db_host}')

# ❌ 禁止
logger.info(f'Connecting with password: {password}')  # パスワード露出
logger.debug(f'Token: {access_token}')  # トークン露出
```

### 3. パフォーマンス制約

**データベース接続の使い分け**:
```python
# ✅ 推奨: 適切なデータストアの選択
# OLTP DB: マスタデータ、デバイスステータス
def get_device_info(device_id):
    # MySQL互換DBから取得
    return mysql_db.query("SELECT * FROM devices WHERE id = %s", (device_id,))

# Unity Catalog: 履歴データ、分析用途
def get_sensor_history(device_id, start_date):
    # SQL Warehouse経由で取得
    return databricks_sql.query(
        "SELECT * FROM sensor_data WHERE device_id = ? AND date >= ?",
        (device_id, start_date)
    )

# ❌ 禁止: 不適切なデータストア選択
# 大量履歴データをOLTP DBから取得 → パフォーマンス低下
```

**クエリ最適化**:
```python
# ✅ 推奨: 必要なカラムのみ取得
cursor.execute("SELECT device_id, status FROM devices WHERE active = 1")

# ❌ 禁止: 不要なデータ取得
cursor.execute("SELECT * FROM devices")  # 全カラム取得
```

**App Compute重い処理の制約**:
```python
# ✅ 推奨: 軽量処理のみApp Computeで実行
@app.route('/api/device/status')
def get_device_status():
    # 軽量なクエリ
    return jsonify(get_latest_status())

# ❌ 禁止: 重い処理をApp Computeで実行
@app.route('/api/analytics/heavy')
def heavy_analytics():
    # メモリ大量消費、長時間処理 → クラスターで実装すべき
    return perform_heavy_computation()
```

**接続プーリング**:
```python
# ✅ 推奨: コネクションプール使用
from databricks import sql
import pymysql.pooling

# Databricks接続プール
databricks_connection_pool = sql.connect(...)

# MySQL接続プール
mysql_pool = pymysql.pooling.ConnectionPool(
    pool_size=5,
    host=os.getenv('MYSQL_HOST'),
    ...
)

# ❌ 禁止: リクエストごとに接続生成
def query_data():
    connection = pymysql.connect(...)  # 毎回接続
    # 処理
    connection.close()
```

### 4. 監視・ログ制約

**ログレベル管理**:
```python
# ✅ 推奨: 環境別ログレベル
import logging
import os

log_level = logging.ERROR if os.getenv('ENV') == 'production' else logging.DEBUG
logging.basicConfig(level=log_level)

logger = logging.getLogger(__name__)
logger.error('Critical error: %s', error)  # ✅ 本番でも出力
logger.warning('Warning: %s', warning)     # ✅ 警告レベル
logger.info('Info: %s', info)              # ⚠️ 本番では慎重に
logger.debug('Debug: %s', debug)           # ❌ 本番では出力されない

# ❌ 禁止: 機密情報のログ出力
logger.info(f'User password: {password}')  # セキュリティリスク
logger.debug(f'API key: {api_key}')        # セキュリティリスク
```

**永続化ログ出力**:
```python
# ✅ 推奨: Unity Catalogまたは外部ログアダプターへ出力
def log_to_unity_catalog(level, message):
    # Unity Catalogテーブルへログ書き込み
    databricks_sql.execute(
        "INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)",
        (datetime.now(), level, message)
    )

# または外部ログアダプター
def log_to_external(level, message):
    # Azure Log Analyticsなどへ送信
    requests.post(external_log_endpoint, json={'level': level, 'message': message})

# ❌ 禁止: 標準出力のみ (App Compute再起動で消失)
print(f'Log: {message}')  # コンテナ再起動で消える
```

**エラーハンドリング**:
```python
# ✅ 推奨: 構造化されたエラー応答
from flask import jsonify
from datetime import datetime

@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f'Error occurred: {str(error)}')
    return jsonify({
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR',
        'timestamp': datetime.now().isoformat()
    }), 500

# ❌ 禁止: 生のエラー露出
@app.errorhandler(Exception)
def handle_error(error):
    return jsonify({'error': str(error)}), 500  # 内部情報漏洩リスク
```

### 5. 依存関係制約

**パッケージ選定基準**:
```python
# ✅ 推奨: 必要最小限のライブラリ
Flask==3.0.0                      # 軽量Webフレームワーク
databricks-sql-connector==2.9.0   # Databricks公式
pymysql==1.1.0                    # 軽量MySQL接続
python-dotenv==1.0.0              # 環境変数管理

# ❌ 禁止: 重量級・不要なライブラリ
Django                            # Flaskで十分な場合
pandas                            # 分析はDatabricks側で実施
```

**外部通信ライブラリ**:
```python
# ✅ 推奨: 必要に応じて使用、セキュリティポリシー確認
import requests  # 外部API呼び出し用

# ⚠️ 注意: 外部通信制限を確認
# セキュリティポリシーで制限されている場合は部分的な解除が必要
```

**バージョン管理**:
```python
# ✅ 推奨: requirements.txt
Flask==3.0.0                      # バージョン固定
databricks-sql-connector==2.9.0   # メジャーバージョン固定
pymysql==1.1.0
python-dotenv==1.0.0

# ❌ 禁止: バージョン未指定・不安定版
Flask                             # バージョン未指定
databricks-sql-connector>=2.0     # 範囲指定（予期せぬ更新）
some-package==0.1.0-alpha         # アルファ版は禁止
```

## チェックリスト

### デプロイ前チェック (App Compute)
- [ ] 全ての環境変数が設定されている (Databricks環境変数)
- [ ] 1ファイル10MB以下の制約を満たしている
- [ ] requirements.txtでバージョンが固定されている
- [ ] 機密情報がログに出力されていない
- [ ] エラーハンドリングが適切に実装されている
- [ ] 永続化ログ出力が実装されている (Unity Catalog/外部アダプター)
- [ ] Gitリポジトリが最新の状態になっている

### Databricks リソースデプロイ前チェック
- [ ] Databricks アセット バンドルが作成されている
- [ ] パイプライン定義が正しく記述されている
- [ ] クラスター設定が適切に定義されている
- [ ] Unity Catalogオブジェクトが定義されている

### セキュリティチェック
- [ ] 本番環境で不要なログが出力されていない
- [ ] パスワード・トークンなどが環境変数化されている
- [ ] SQLインジェクション対策がされている (パラメータ化クエリ)
- [ ] 認証ヘッダ（IdP発行トークン）を適切に処理している
- [ ] OAuth トークン フェデレーションが正しく動作している
- [ ] XSS対策がされている (Jinja2自動エスケープ)
- [ ] CSRF対策が実装されている (Flask-WTF)

### パフォーマンスチェック
- [ ] データストア使い分けが適切 (Unity Catalog vs OLTP DB)
- [ ] 接続プーリングが実装されている
- [ ] 必要なカラムのみ取得している (SELECT *)
- [ ] 重い処理をApp Computeで実装していない
- [ ] テンプレートキャッシュが有効になっている
- [ ] 静的ファイルが最適化されている

### 監視・運用チェック
- [ ] 死活監視の設定が完了している (App Compute URL監視)
- [ ] アラート通知の設定が完了している
- [ ] ログの永続化が確認されている
- [ ] システムテーブルへの監査ログ出力が確認されている

---

## 編集履歴

| 日付       | バージョン | 編集者 | 変更内容                                                                                                                                    |
| ---------- | ---------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 2025-11-25 | 1.0        | Claude | スケジュールバッチ機能削除に伴う更新: App Computeの機能から「スケジュールバッチ (バックグラウンド処理)」を削除                              |
| 2025-11-26 | 1.1        | Claude | Azure環境統合の明確化: 概要にAzure環境統合を明記、構成図タイトル変更、環境構成セクション詳細化（3環境構成、環境別コンポーネント配置表追加） |