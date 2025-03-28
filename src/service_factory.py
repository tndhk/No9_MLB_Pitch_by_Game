class ServiceFactory:
    """
    サービスファクトリクラス
    アプリケーション全体の依存性を管理し、必要なオブジェクトを提供する
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Parameters:
        -----------
        config : Dict[str, Any], optional
            アプリケーション設定
        """
        self.config = config or {}
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("サービスファクトリを初期化しています")
        
        # 内部でインスタンスをキャッシュ
        self._instances = {}
    
    def _setup_logging(self) -> None:
        """ロギングの設定"""
        log_level = self.config.get('log_level', 'INFO')
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # ログディレクトリの作成
        log_dir = self.config.get('log_dir', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # ロガーの設定
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format,
            handlers=[
                logging.StreamHandler(),  # コンソール出力
                logging.FileHandler(os.path.join(log_dir, 'app.log'))  # ファイル出力
            ]
        )
    
    def create_baseball_savant_client(self) -> BaseballSavantClient:
        """BaseballSavantClientのインスタンスを作成/取得"""
        if 'baseball_savant_client' not in self._instances:
            rate_limit = self.config.get('api_rate_limit', 2.0)
            self._instances['baseball_savant_client'] = BaseballSavantClient(rate_limit_interval=rate_limit)
            self.logger.info("BaseballSavantClientを作成しました")
        
        return self._instances['baseball_savant_client']
    
    def create_data_repository(self) -> DataRepository:
        """DataRepositoryのインスタンスを作成/取得"""
        if 'data_repository' not in self._instances:
            cache_dir = self.config.get('cache_dir', './data')
            db_path = self.config.get('db_path', './data/db.sqlite')
            
            # キャッシュディレクトリの作成
            os.makedirs(cache_dir, exist_ok=True)
            
            self._instances['data_repository'] = DataRepository(cache_dir=cache_dir, db_path=db_path)
            self.logger.info(f"DataRepositoryを作成しました (cache_dir: {cache_dir}, db_path: {db_path})")
        
        return self._instances['data_repository']
    
    def create_pitch_analyzer(self) -> PitchAnalyzer:
        """PitchAnalyzerのインスタンスを作成/取得"""
        if 'pitch_analyzer' not in self._instances:
            self._instances['pitch_analyzer'] = PitchAnalyzer()
            self.logger.info("PitchAnalyzerを作成しました")
        
        return self._instances['pitch_analyzer']
    
    def create_data_visualizer(self) -> DataVisualizer:
        """DataVisualizerのインスタンスを作成/取得"""
        if 'data_visualizer' not in self._instances:
            self._instances['data_visualizer'] = DataVisualizer()
            self.logger.info("DataVisualizerを作成しました")
        
        return self._instances['data_visualizer']
    
    def create_pitcher_game_analysis_use_case(self) -> PitcherGameAnalysisUseCase:
        """PitcherGameAnalysisUseCaseのインスタンスを作成/取得"""
        if 'pitcher_game_analysis_use_case' not in self._instances:
            client = self.create_baseball_savant_client()
            repository = self.create_data_repository()
            analyzer = self.create_pitch_analyzer()
            
            self._instances['pitcher_game_analysis_use_case'] = PitcherGameAnalysisUseCase(
                client=client,
                repository=repository,
                analyzer=analyzer
            )
            self.logger.info("PitcherGameAnalysisUseCaseを作成しました")
        
        return self._instances['pitcher_game_analysis_use_case']
    
    def create_streamlit_app(self) -> StreamlitApp:
        """StreamlitAppのインスタンスを作成/取得"""
        if 'streamlit_app' not in self._instances:
            use_case = self.create_pitcher_game_analysis_use_case()
            visualizer = self.create_data_visualizer()
            
            self._instances['streamlit_app'] = StreamlitApp(
                use_case=use_case,
                visualizer=visualizer
            )
            self.logger.info("StreamlitAppを作成しました")
        
        return self._instances['streamlit_app']