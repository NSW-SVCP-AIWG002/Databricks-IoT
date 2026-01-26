# Databricks IoTシステム アーキテクチャ

このディレクトリには、Databricks IoTシステムのアーキテクチャに関する設計ドキュメントが格納されています。IoTデバイスからのデータ収集、リアルタイム処理、分析、可視化に関する包括的なアーキテクチャ設計を提供します。

## 📋 ドキュメント構成

### overview.md
システム全体のアーキテクチャ概要
- システム構成図（IoTデバイス → Azure統合環境（Azure IoT + Databricks Platform） → データストア）
- 主要コンポーネントの説明
- 技術スタックの概要
- データフロー全体図

### frontend.md
フロントエンドアーキテクチャ
- Flask + Jinja2テンプレートアーキテクチャ
- サーバーサイドレンダリング設計
- HTML + CSS クラシック構成
- Databricksダッシュボード埋め込み設計
- UI/UXアーキテクチャ

### backend.md
バックエンドアーキテクチャ
- Flask Application設計（App Compute）
- Lakeflow 宣言型パイプライン（LDP）設計
- メダリオンアーキテクチャ（Bronze/Silver/Gold）
- データベース設計（Unity Catalog + MySQL互換DB）
- アラート処理設計

### infrastructure.md
インフラストラクチャ設計
- Databricks Platform構成（Premium ライセンス）
- Azure IoT Services構成（IoT Hubs、Event Hubs、Event Hubs Capture）
- 認証基盤（Entra ID、Databricksワークスペース、アクセス元IP制限）
- ネットワーク構成（Private Link、Azure DNS）
- コンピューティングプレーン構成（サーバレス/クラシック）
- Unity Catalog設計（ADLS連携）
- MySQL互換データベース構成（踏み台VM）
- デプロイメント設計
- 監視・ログ設計

### data-models/ (TODO)
データモデル設計
- ERD（Entity Relationship Diagram）
- Unity Catalogテーブル設計
- MySQL互換DBテーブル設計
- データフロー図（メダリオンアーキテクチャ）

### decisions/ (TODO)
アーキテクチャ決定記録（ADR）
- 技術選定の理由（Databricks Platform選定理由など）
- 設計上の重要な決定事項（データストア使い分け戦略など）
- トレードオフの記録

## 🏗️ アーキテクチャの原則

### 1. **データレイクハウスアーキテクチャ**
- Unity Catalogによる統合データ管理
- メダリオンアーキテクチャ（Bronze → Silver → Gold）
- Delta Lakeによる信頼性の高いデータストレージ
- データ品質とガバナンスの確保

### 2. **リアルタイム処理とスケーラビリティ**
- Lakeflow 宣言型パイプライン（LDP）によるストリーム処理
- 大量IoTデバイスデータの効率的処理（最大100,000デバイス）
- Event Hubsを活用したスケーラブルなデータ取込み
- パフォーマンス要件（データ処理5分以内）

### 3. **ハイブリッドデータストア戦略**
- Unity Catalog: 大量データ、履歴データ、分析用途
- MySQL互換DB: マスタデータ、最新状況、OLTP用途
- 用途に応じた最適なデータストアの使い分け
- データ整合性の保証

### 4. **セキュリティとガバナンス**
- Entra ID + Databricks User認証（シングルサインオン）
- アクセス元IP制限（Databricksワークスペース、Databricks Apps）
- Private Linkによるセキュア通信（Event Hub/ADLS/MySQL/Databricks UI API）
- Unity Catalogによるアクセス制御
- データ暗号化（100%）
- 入力検証とセキュアコーディング
- 監査ログとトレーサビリティ

### 5. **シンプルで保守性の高い設計**
- Flask + Jinja2によるクラシックなWeb構成
- Python/SQLによる統一された開発言語
- モジュール化されたBlueprint構成
- テスト容易性とコード品質の維持

## 📊 主要コンポーネント

### Databricks Platform
- **Unity Catalog**: Delta Lakeベースのデータカタログ（大量データ、履歴データ管理）
- **Lakeflow 宣言型パイプライン (LDP)**: Python/SQLによるストリーム処理パイプライン
- **App Compute**: Flask Applicationホスティング環境
- **SQL Warehouse**: SQLクエリ実行環境
- **Databricks Dashboard**: データ可視化・BI機能
- **Databricks AI**: 対話型AIパネル機能

### Azure IoT Services
- **Azure IoT Hubs**: MQTTプロトコル対応IoTデバイス接続サービス
- **Event Hubs**: Kafkaエンドポイント提供、LDPへのデータストリーム配信
  - **Event Hubs Capture**: RAWデータをADLSに継続出力（長期保存・障害復旧用）
- **Private Link**: Event HubsへのPrivate Link接続

### アプリケーション層
- **Flask Application**: Python 3.10+ ベースのWebアプリケーション（App Compute）
- **Jinja2 Templates**: サーバーサイドHTMLレンダリング
- **Databricks SQL Connector**: Unity Catalogへのデータアクセス
- **PyMySQL**: MySQL互換データベースへのアクセス

### データストア層
- **Unity Catalog (Delta Lake)**: 大量IoTデータ、履歴データ、集計データ
  - **ADLS (Azure Data Lake Storage)**: ストレージバックエンド
  - **Private Link**: ADLS用Private Link (dfs)経由でのデータ読み書き
- **MySQL互換データベース**: デバイスマスタ、ユーザーマスタ、アラート設定、最新状況
  - **Private Link**: MySQL用Private Link経由でのアクセス
  - **踏み台VM**: プライベートネットワーク内のDB保守アクセス

## 🔄 更新履歴

アーキテクチャの変更は、必ず`decisions/`ディレクトリにADRとして記録してください。

| 日付 | バージョン | 編集者 | 変更内容 |
|------|------------|--------|----------|
| 2025-11-14 | 1.0 | Claude | 初版作成（Databricks IoTシステム用にアーキテクチャドキュメント構成を整備） |
| 2025-11-20 | 1.1 | Claude | インフラネットワーク構成反映: Entra ID認証基盤、Private Link、Event Hubs Capture、ADLS、コンピューティングプレーン構成、踏み台VMを追加 |
| 2025-11-26 | 1.2 | Claude | Azure環境統合の明確化: overview.mdの(TODO)を削除、システム構成図の表記を「Azure統合環境（Azure IoT + Databricks Platform）」に変更 |

## 📚 参考資料

### Databricks関連
- [Databricks Documentation](https://docs.databricks.com/)
- [Unity Catalog Documentation](https://docs.databricks.com/data-governance/unity-catalog/index.html)
- [Delta Lake Documentation](https://docs.delta.io/)
- [Databricks SQL Connector for Python](https://docs.databricks.com/dev-tools/python-sql-connector.html)
- [Databricks Apps](https://docs.databricks.com/en/dev-tools/databricks-apps/index.html)

### Azure IoT関連
- [Azure IoT Hubs Documentation](https://learn.microsoft.com/azure/iot-hub/)
- [Azure Event Hubs Documentation](https://learn.microsoft.com/azure/event-hubs/)

### アプリケーション開発関連
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [PyMySQL Documentation](https://pymysql.readthedocs.io/) 