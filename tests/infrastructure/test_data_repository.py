class TestDataRepository:
    """DataRepositoryクラスのテスト"""
    
    @pytest.fixture
    def tmp_db_path(self, tmp_path):
        """一時的なDBパスを提供するフィクスチャ"""
        return tmp_path / "test.db"
    
    @pytest.fixture
    def tmp_cache_dir(self, tmp_path):
        """一時的なキャッシュディレクトリを提供するフィクスチャ"""
        return tmp_path / "cache"
    
    def test_init(self, tmp_db_path, tmp_cache_dir):
        """初期化のテスト"""
        repo = DataRepository(cache_dir=str(tmp_cache_dir), db_path=str(tmp_db_path))
        
        # ディレクトリとデータベースの作成を検証
        assert tmp_cache_dir.exists()
        assert tmp_db_path.exists()
    
    def test_save_and_get_pitcher_info(self, tmp_db_path, tmp_cache_dir):
        """投手情報の保存と取得のテスト"""
        repo = DataRepository(cache_dir=str(tmp_cache_dir), db_path=str(tmp_db_path))
        
        # テスト用の投手オブジェクト
        pitcher = Pitcher(id="123", name="Test Pitcher", team="Test Team", throws="R")
        
        # 保存
        repo.save_pitcher_info(pitcher)
        
        # 取得して検証
        retrieved = repo.get_pitcher_info("123")
        
        assert retrieved is not None
        assert retrieved.id == "123"
        assert retrieved.name == "Test Pitcher"
        assert retrieved.team == "Test Team"
        assert retrieved.throws == "R"
    
    def test_save_and_get_game_info(self, tmp_db_path, tmp_cache_dir):
        """試合情報の保存と取得のテスト"""
        repo = DataRepository(cache_dir=str(tmp_cache_dir), db_path=str(tmp_db_path))
        
        # テスト用の投手オブジェクト（外部キー参照のため）
        pitcher = Pitcher(id="123", name="Test Pitcher", team="Test Team", throws="R")
        repo.save_pitcher_info(pitcher)
        
        # テスト用の試合オブジェクト
        game = Game(
            date="2023-04-01", 
            pitcher_id="123", 
            opponent="Opponent Team", 
            stadium="Test Stadium", 
            home_away="home"
        )
        
        # 保存
        repo.save_game_info(game)
        
        # 取得して検証
        retrieved_games = repo.get_games_by_pitcher("123")
        
        assert len(retrieved_games) == 1
        assert retrieved_games[0].date == "2023-04-01"
        assert retrieved_games[0].opponent == "Opponent Team"
        assert retrieved_games[0].stadium == "Test Stadium"
    
    def test_save_and_get_pitch_data(self, tmp_db_path, tmp_cache_dir):
        """投球データの保存と取得のテスト"""
        repo = DataRepository(cache_dir=str(tmp_cache_dir), db_path=str(tmp_db_path))
        
        # テスト用のデータフレーム
        data = pd.DataFrame({
            'pitch_type': ['FF', 'SL'],
            'release_speed': [95.2, 88.3],
            'description': ['hit_into_play', 'swinging_strike']
        })
        
        # 保存
        repo.save_pitch_data("123", "2023-04-01", data)
        
        # ファイルの存在を検証
        pkl_path = tmp_cache_dir / "pitch_data_123_2023-04-01.pkl"
        meta_path = tmp_cache_dir / "pitch_data_123_2023-04-01.meta.json"
        
        assert pkl_path.exists()
        assert meta_path.exists()
        
        # 取得して検証
        retrieved_data = repo.get_cached_pitch_data("123", "2023-04-01")
        
        assert retrieved_data is not None
        assert len(retrieved_data) == 2
        assert retrieved_data['pitch_type'][0] == 'FF'
        assert retrieved_data['release_speed'][1] == 88.3