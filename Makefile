.PHONY: setup build run test clean logs shell

# 初期セットアップ: ディレクトリ構造作成
setup:
	mkdir -p src/{domain,application,infrastructure,presentation}
	mkdir -p tests/{domain,application,infrastructure,presentation}
	mkdir -p data logs
	touch src/domain/__init__.py
	touch src/domain/entities.py
	touch src/domain/pitch_analyzer.py
	touch src/infrastructure/__init__.py
	touch src/infrastructure/baseball_savant_client.py
	touch src/infrastructure/data_repository.py
	touch src/application/__init__.py
	touch src/application/analysis_result.py
	touch src/application/usecases.py
	touch src/presentation/__init__.py
	touch src/presentation/data_visualizer.py
	touch src/presentation/streamlit_app.py
	touch src/__init__.py
	touch src/service_factory.py
	touch src/main.py
	touch app.py
	touch tests/__init__.py
	touch tests/domain/__init__.py
	touch tests/domain/test_pitch_analyzer.py
	touch tests/application/__init__.py
	touch tests/application/test_usecases.py
	touch tests/infrastructure/__init__.py
	touch tests/infrastructure/test_baseball_savant_client.py
	touch tests/infrastructure/test_data_repository.py
	touch tests/presentation/__init__.py
	touch tests/presentation/test_data_visualizer.py

# Dockerイメージのビルド
build:
	docker-compose build

# アプリケーションの起動
run:
	docker-compose up -d

# アプリケーションの停止
stop:
	docker-compose down

# テストの実行
test:
	docker-compose run --rm mlb-pitcher-analyzer pytest

# ログの表示
logs:
	docker-compose logs -f

# コンテナのシェルに接続
shell:
	docker-compose exec mlb-pitcher-analyzer /bin/bash

# クリーンアップ（コンテナ、イメージ、ボリューム）
clean:
	docker-compose down -v
	docker rmi mlb-pitcher-analyzer_mlb-pitcher-analyzer

# 開発用のローカル環境セットアップ
dev-setup:
	pip install -r requirements.txt

# ローカルでのアプリケーション実行
dev-run:
	streamlit run app.py

# ローカルでのテスト実行
dev-test:
	pytest