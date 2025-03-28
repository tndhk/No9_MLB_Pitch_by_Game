def parse_args() -> Dict[str, Any]:
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(description='MLB投手1試合分析ツール')
    
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='ログレベルを設定')
    
    parser.add_argument('--cache-dir', default='./data',
                        help='キャッシュディレクトリのパス')
    
    parser.add_argument('--db-path', default='./data/db.sqlite',
                        help='SQLiteデータベースのパス')
    
    parser.add_argument('--api-rate-limit', type=float, default=2.0,
                        help='API呼び出しの最小間隔（秒）')
    
    args = parser.parse_args()
    
    # 設定辞書を作成
    config = {
        'log_level': args.log_level,
        'cache_dir': args.cache_dir,
        'db_path': args.db_path,
        'api_rate_limit': args.api_rate_limit,
        'log_dir': 'logs'
    }
    
    return config

def main() -> None:
    """メイン関数"""
    # コマンドライン引数の解析
    config = parse_args()
    
    try:
        # サービスファクトリの初期化
        factory = ServiceFactory(config)
        logger = logging.getLogger(__name__)
        logger.info("アプリケーションを起動します")
        
        # Streamlitアプリの作成と実行
        app = factory.create_streamlit_app()
        app.run()
        
    except Exception as e:
        logging.error(f"アプリケーション実行中にエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()