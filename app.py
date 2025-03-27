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
    
    # サブコマンドライン引数がある場合は、それだけをパースする
    if len(sys.argv) > 1 and sys.argv[1] == '--':
        args = parser.parse_args(sys.argv[2:])
    else:
        args = parser.parse_args()
    
    # デバッグログ
    logging.basicConfig(level=logging.INFO)
    logging.info(f"設定ファイルパス: {args.config}")
    
    return args


def main() -> None:
    """Streamlitアプリケーションのメイン関数"""
    # コマンドライン引数の解析
    args = parse_args()
    
    # ファイルの存在確認
    config_path = args.config
    if not os.path.exists(config_path):
        logging.error(f"設定ファイルが見つかりません: {config_path}")
        print(f"エラー: 設定ファイルが見つかりません: {config_path}")
        print(f"現在の作業ディレクトリ: {os.getcwd()}")
        print(f"ディレクトリ内容: {os.listdir('.')}")
        if os.path.dirname(config_path):
            parent_dir = os.path.dirname(config_path)
            if os.path.exists(parent_dir):
                print(f"{parent_dir}の内容: {os.listdir(parent_dir)}")
    else:
        logging.info(f"設定ファイルが見つかりました: {config_path}")
    
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