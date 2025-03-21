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

2. Dockerイメージのビルドと起動
```bash
# makeコマンドがある場合
make build
make run

# または、直接Docker Composeを使用
docker-compose build
docker-compose up -d
```

3. アプリケーションにアクセス

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
python -m src.main
```

コマンドラインオプション：
- `--log-level`: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- `--cache-dir`: キャッシュディレクトリのパス
- `--db-path`: SQLiteデータベースのパス
- `--api-rate-limit`: API呼び出しの最小間隔（秒）

例：
```bash
python -m src.main --log-level DEBUG --api-rate-limit 3.0
```

## テストの実行

```bash
# makeコマンドがある場合
make dev-test

# または直接実行
pytest

# 特定のテストを実行
pytest tests/domain/test_pitch_analyzer.py
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
│   └── presentation/
│       └── test_data_visualizer.py
├── data/
│   └── db.sqlite
├── logs/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── Makefile
├── requirements.txt
└── README.md
```

## 貢献方法

1. Forkして自分のリポジトリにコピー
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. リモートブランチにプッシュ (`git push origin feature/amazing-feature`)
5. Pull Requestを作成

## 注意事項

このツールはBaseball Savant APIを利用しています。過度なリクエストはAPIサーバーに負荷をかける可能性があるため、適切なレート制限（デフォルト: 2秒）を設定しています。