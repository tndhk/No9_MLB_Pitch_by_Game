"""
Streamlitアプリケーションのエントリーポイント
"""
import os
import sys
import logging
from typing import Dict, Any

from src.service_factory import ServiceFactory


def get_config() -> Dict[str, Any]:
    """設定を取得"""
    # 環境変数から設定を読み込む（または固定値を使用）
    config = {
        'log_level': os.environ.get('LOG_LEVEL', 'INFO'),
        'cache_dir': os.environ.get('CACHE_DIR', './data'),
        'db_path': os.environ.get('DB_PATH', './data/db.sqlite'),
        'api_rate_limit': float(os.environ.get('API_RATE_LIMIT', '2.0')),
        'log_dir': os.environ.get('LOG_DIR', 'logs')
    }
    
    return config

def main() -> None:
    """Streamlitアプリケーションのメイン関数"""
    config = get_config()
    
    try:
        # ログディレクトリの作成
        os.makedirs(config['log_dir'], exist_ok=True)
        
        # ロギングの初期化
        logging.basicConfig(
            level=getattr(logging, config['log_level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(os.path.join(config['log_dir'], 'streamlit_app.log'))
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info("Streamlitアプリケーションを起動します")
        
        # サービスファクトリの初期化
        factory = ServiceFactory(config)
        
        # Streamlitアプリの作成と実行
        app = factory.create_streamlit_app()
        app.run()
        
    except Exception as e:
        logging.error(f"アプリケーション実行中にエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)

# Streamlitのエントリーポイント
if __name__ == "__main__":
    main()