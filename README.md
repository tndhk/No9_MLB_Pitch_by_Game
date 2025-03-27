# MLB投手1試合分析ツール

Baseball Savant (Statcast) APIを使用して、MLB投手の1試合分の投球データを取得・分析・可視化するツールです。

## 機能

- 投手名からの検索
- シーズン内の試合一覧表示
- 選択した試合の詳細分析
  - イニング別投球分析
  - 球種別分析
  - 被打球分析
  - 総合パフォーマンス指標

## アーキテクチャ

クリーンアーキテクチャを採用し、以下の層構造で設計しています：

- **ドメイン層**: ビジネスロジック、エンティティ、値オブジェクト
- **アプリケーション層**: ユースケースの実装
- **インフラストラクチャ層**: 外部サービス連携、データアクセス
- **プレゼンテーション層**: ユーザーインターフェース、データ可視化

## 設定ファイル

アプリケーションは `config.yml` ファイルから設定を読み込みます。設定は環境変数で上書きすることも可能です。

### 設定ファイルの場所

設定ファイルは以下の順序で検索されます：

1. `--config` コマンドライン引数で指定されたパス
2. カレントディレクトリの `config.yml` または `config.yaml`
3. `./config` ディレクトリ内の `config.yml` または `config.yaml`
4. 親ディレクトリの `config.yml` または `config.yaml`

### 環境変数による設定

以下の環境変数を使用して設定を上書きできます：

- `MLB_APP_DEBUG`: デバッグモードの有効/無効 (true/false)
- `MLB_LOG_LEVEL`: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `MLB_LOG_DIR`: ログディレクトリのパス
- `MLB_CACHE_DIR`: キャッシュディレクトリのパス
- `MLB_DB_PATH`: SQLiteデータベースのパス
- `MLB_CACHE_EXPIRY_DAYS`: キャッシュの有効期限（日数）
- `MLB_API_RATE_LIMIT`: API呼び出しの最小間隔（秒）
- `MLB_API_MAX_RETRIES`: API呼び出し失敗時のリトライ回数
- `MLB_API_TIMEOUT`: APIリクエストのタイムアウト（秒）
- `MLB_API_USE_PROXY`: プロキシの使用 (true/false)
- `MLB_API_USER_AGENT`: APIリクエストのUser-Agent

## Docker を使った実行

### 前提条件

- Docker
- Docker Compose

### インストールと実行

1. リポジトリをクローン
```bash
git clone https://github.com/yourusername/mlb-pitcher-analyzer.git
cd mlb-pitcher-analyzer
```

2. 設定ファイルのカスタマイズ（オプション）
```bash
cp config.yml.example config.yml
# config.ymlを編集
```

3. Dockerイメージのビルドと起動
```bash
# makeコマンドがある場合
make build
make run

# または、直接Docker Composeを使用
docker-compose build
docker-compose up -d
```

4. アプリケーションにアクセス

ブラウザで `http://localhost:8501` にアクセスするとアプリケーションが表示されます。

### 便利なコマンド

```bash
# アプリケーションの停止
make stop

# ログの表示
make logs

# コンテナのシェルにアクセス
make shell

# テストの実行
make test

# クリーンアップ
make clean
```

## 従来の開発環境のセットアップ（Dockerなし）

### 前提条件

- Python 3.8以上
- pipまたはconda

### インストール手順

1. プロジェクト構造のセットアップ

```bash
# makeコマンドがある場合
make setup

# または手動で
mkdir -p src/{domain,application,infrastructure,presentation}
mkdir -p tests/{domain,application,infrastructure,presentation}
mkdir -p data logs
# 以下省略...
```

2. 仮想環境を作成（オプション）
```bash
# Pythonの仮想環境を作成
python -m venv venv

# 仮想環境を有効化
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

3. 依存パッケージをインストール
```bash
pip install -r requirements.txt
```

## アプリケーションのローカル実行

### Streamlitアプリとして実行

```bash
# makeコマンドがある場合
make dev-run

# または直接実行
streamlit run app.py
```

これにより、Webブラウザでアプリケーションが起動します。デフォルトでは http://localhost:8501 でアクセスできます。

### コマンドラインからの実行

```bash
python -m src.main --config ./config.yml
```

## API接続について

### BaseballSavantClientの使用方法

BaseballSavantClientクラスは、Baseball Savant APIとの連携を担当します。以下の機能を提供します：

- **投手検索**: 投手名でMLB投手を検索
- **投球データ取得**: 特定投手の特定試合/シーズンの投球データを取得
- **投手詳細情報取得**: 投手の詳細情報（チーム、投球腕など）を取得
- **試合リスト取得**: 投手の特定シーズンの出場試合リストを取得

### エラーハンドリングとリトライ

API接続にはリトライメカニズムが実装されており、接続に失敗した場合は自動的にリトライします。
リトライの回数と間隔は設定ファイルまたは環境変数で調整できます。

### レート制限

Baseball Savant APIの使用にはレート制限があります。
アプリケーションは自動的に適切な待機時間を設定し、APIへの過度な負荷を防ぎます。

### キャッシュ

パフォーマンス向上と外部サービスへの負荷軽減のため、取得したデータはローカルにキャッシュされます。
キャッシュの有効期間は設定ファイルで指定できます。

## テストの実行

```bash
# makeコマンドがある場合
make dev-test

# または直接実行
pytest

# 特定のテストを実行
pytest tests/infrastructure/test_baseball_savant_client.py
```

## プロジェクト構造

```
mlb-pitcher-analyzer/
├── src/
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities.py
│   │   └── pitch_analyzer.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── usecases.py
│   │   └── analysis_result.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── baseball_savant_client.py
│   │   └── data_repository.py
│   ├── presentation/
│   │   ├── __init__.py
│   │   ├── data_visualizer.py
│   │   └── streamlit_app.py
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   └── service_factory.py
├── tests/
│   ├── domain/
│   │   └── test_pitch_analyzer.py
│   ├── application/
│   │   └── test_usecases.py
│   ├── infrastructure/
│   │   ├── test_baseball_savant_client.py
│   │   └── test_data_repository.py
│   ├── presentation/
│   │   └── test_data_visualizer.py
│   └── test_config.py
├── data/
│   └── db.sqlite
├── logs/
├── app.py
├── config.yml
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── Makefile
├── requirements.txt
└── README.md
```

## 注意事項

このツールはBaseball Savant APIを利用しています。過度なリクエストはAPIサーバーに負荷をかける可能性があるため、適切なレート制限（デフォルト: 2秒）を設定しています。