class TestPitcherGameAnalysisUseCase:
    """PitcherGameAnalysisUseCaseクラスのテスト"""
    
    @pytest.fixture
    def mock_client(self):
        """BaseballSavantClientのモック"""
        return MagicMock(spec=BaseballSavantClient)
    
    @pytest.fixture
    def mock_repository(self):
        """DataRepositoryのモック"""
        return MagicMock(spec=DataRepository)
    
    @pytest.fixture
    def mock_analyzer(self):
        """PitchAnalyzerのモック"""
        return MagicMock(spec=PitchAnalyzer)
    
    @pytest.fixture
    def use_case(self, mock_client, mock_repository, mock_analyzer):
        """テスト用のユースケースインスタンス"""
        return PitcherGameAnalysisUseCase(
            client=mock_client,
            repository=mock_repository,
            analyzer=mock_analyzer
        )
    
    def test_search_pitchers(self, use_case, mock_client, mock_repository):
        """投手検索のテスト"""
        # モックの設定
        test_pitchers = [
            Pitcher(id="123", name="Test Pitcher 1"),
            Pitcher(id="456", name="Test Pitcher 2")
        ]
        mock_client.search_pitcher.return_value = test_pitchers
        
        # 検索を実行
        result = use_case.search_pitchers("Test")
        
        # 検証
        mock_client.search_pitcher.assert_called_once_with("Test")
        assert mock_repository.save_pitcher_info.call_count == 2
        assert result == test_pitchers
    
    def test_get_pitcher_games_from_cache(self, use_case, mock_client, mock_repository):
        """キャッシュからの試合取得テスト"""
        # モックの設定
        test_games = [
            Game(date="2023-04-01", pitcher_id="123"),
            Game(date="2023-04-06", pitcher_id="123")
        ]
        mock_repository.get_games_by_pitcher.return_value = test_games
        
        # 試合リストを取得
        result = use_case.get_pitcher_games("123", 2023)
        
        # 検証
        mock_repository.get_games_by_pitcher.assert_called_once_with("123")
        mock_client.get_pitcher_games.assert_not_called()  # キャッシュから取得できるのでAPIは呼ばない
        assert result == test_games
    
    def test_get_pitcher_games_from_api(self, use_case, mock_client, mock_repository):
        """APIからの試合取得テスト"""
        # モックの設定
        mock_repository.get_games_by_pitcher.return_value = []  # キャッシュは空
        
        test_games = [
            Game(date="2023-04-01", pitcher_id="123"),
            Game(date="2023-04-06", pitcher_id="123")
        ]
        mock_client.get_pitcher_games.return_value = test_games
        
        # 試合リストを取得
        result = use_case.get_pitcher_games("123", 2023)
        
        # 検証
        mock_repository.get_games_by_pitcher.assert_called_once_with("123")
        mock_client.get_pitcher_games.assert_called_once_with("123", 2023)
        assert mock_repository.save_game_info.call_count == 2
        assert result == test_games
    
    def test_analyze_game_cached_data(self, use_case, mock_client, mock_repository, mock_analyzer):
        """キャッシュデータを使った試合分析テスト"""
        # モックの設定
        pitcher = Pitcher(id="123", name="Test Pitcher")
        mock_repository.get_pitcher_info.return_value = pitcher
        
        test_data = pd.DataFrame({
            'pitch_type': ['FF', 'SL'],
            'release_speed': [95.0, 88.0]
        })
        mock_repository.get_cached_pitch_data.return_value = test_data
        
        # モック分析結果
        mock_analyzer.analyze_by_inning.return_value = {'innings': [1, 2]}
        mock_analyzer.analyze_by_pitch_type.return_value = {'pitch_types': ['FF', 'SL']}
        mock_analyzer.analyze_batted_balls.return_value = pd.DataFrame()
        mock_analyzer.get_performance_summary.return_value = {'total_pitches': 2}
        
        # 試合分析を実行
        result = use_case.analyze_game("123", "2023-04-01")
        
        # 検証
        mock_repository.get_pitcher_info.assert_called_once_with("123")
        mock_repository.get_cached_pitch_data.assert_called_once_with("123", "2023-04-01")
        mock_client.get_pitch_data.assert_not_called()  # キャッシュがあるのでAPI呼び出しなし
        
        assert isinstance(result, AnalysisResult)
        assert result.pitcher_id == "123"
        assert result.pitcher_name == "Test Pitcher"
        assert result.game_date == "2023-04-01"
        assert result.inning_analysis == {'innings': [1, 2]}
        assert result.pitch_type_analysis == {'pitch_types': ['FF', 'SL']}
        assert result.performance_summary == {'total_pitches': 2}
    
    def test_analyze_game_api_data(self, use_case, mock_client, mock_repository, mock_analyzer):
        """APIデータを使った試合分析テスト"""
        # モックの設定
        pitcher = Pitcher(id="123", name="Test Pitcher")
        mock_repository.get_pitcher_info.return_value = pitcher
        mock_repository.get_cached_pitch_data.return_value = None  # キャッシュなし
        
        test_data = pd.DataFrame({
            'pitch_type': ['FF', 'SL'],
            'release_speed': [95.0, 88.0]
        })
        mock_client.get_pitch_data.return_value = test_data
        
        # モック分析結果
        mock_analyzer.analyze_by_inning.return_value = {'innings': [1, 2]}
        mock_analyzer.analyze_by_pitch_type.return_value = {'pitch_types': ['FF', 'SL']}
        mock_analyzer.analyze_batted_balls.return_value = pd.DataFrame()
        mock_analyzer.get_performance_summary.return_value = {'total_pitches': 2}
        
        # 試合分析を実行
        result = use_case.analyze_game("123", "2023-04-01")
        
        # 検証
        mock_repository.get_pitcher_info.assert_called_once_with("123")
        mock_repository.get_cached_pitch_data.assert_called_once_with("123", "2023-04-01")
        mock_client.get_pitch_data.assert_called_once_with("123", "2023-04-01")
        mock_repository.save_pitch_data.assert_called_once_with("123", "2023-04-01", test_data)
        
        assert isinstance(result, AnalysisResult)
        assert result.pitcher_id == "123"
        assert result.pitcher_name == "Test Pitcher"
        assert result.game_date == "2023-04-01"
        assert result.inning_analysis == {'innings': [1, 2]}
        assert result.pitch_type_analysis == {'pitch_types': ['FF', 'SL']}
        assert result.performance_summary == {'total_pitches': 2}