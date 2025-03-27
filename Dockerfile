FROM python:3.10-slim

WORKDIR /app

# 依存関係をコピーしてインストール
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libsqlite3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# アプリケーションコードをコピー
COPY . .

# 設定ファイルの配置
COPY config.yml /app/config.yml

# データとログディレクトリを作成
RUN mkdir -p data logs

# 非rootユーザーを作成
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Streamlitの設定
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_ENABLE_CORS=false

# アプリケーション設定
ENV MLB_APP_DEBUG=false
ENV MLB_LOG_LEVEL=INFO
ENV MLB_CACHE_DIR=/app/data
ENV MLB_DB_PATH=/app/data/db.sqlite
ENV MLB_LOG_DIR=/app/logs

# アプリ起動
CMD ["streamlit", "run", "app.py", "--", "--config", "/app/config.yml"]