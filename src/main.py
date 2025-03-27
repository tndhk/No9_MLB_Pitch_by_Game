"""
Streamlitアプリケーションのエントリーポイント
"""
import os
import sys
import logging
import argparse
from typing import Dict, Any

# パスの追加（パッケージとして実行していない場合でも動作するように）
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.service_factory import ServiceFactory


def parse_args() -> Dict[str, Any]:
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(description='MLB投手1試合分析ツール')
    
    parser.add_argument('--config', 
                        default='./config.yml',
                        help='設定ファイルのパス')
    
    args = parser.parse_args()
    
    return args


def main() -> None:
    """Streamlitアプリケーションのメイン関数"""
    # コマンドライン引数の解析
    args = parse_args()
    
    try:
        # サービスファクトリの初期化（設定ファイルのパスを指定）
        factory = ServiceFactory(args.config)
        logger = logging.getLogger(__name__)
        logger.info("Streamlitアプリケーションを起動します")
        
        # Streamlitアプリの作成と実行
        app = factory.create_streamlit_app()
        app.run()
        
    except Exception as e:
        logging.error(f"アプリケーション実行中にエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


# Streamlitのエントリーポイント
if __name__ == "__main__":
    main()