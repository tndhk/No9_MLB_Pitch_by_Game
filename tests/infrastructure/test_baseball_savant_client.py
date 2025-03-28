class TestBaseballSavantClient:
    """BaseballSavantClientクラスのテスト"""
    
    @patch('src.infrastructure.baseball_savant_client.requests.Session')
    def test_init(self, mock_session_class):
        """初期化のテスト"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        client = BaseballSavantClient()
        
        # セッションヘッダーの設定を検証
        assert 'User-Agent' in mock_session.headers.update.call_args[0][0]
    
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_rate_limit(self, mock_time, mock_sleep):
        """レート制限待機のテスト"""
        # 現在時刻を設定
        mock_time.side_effect = [100.0, 101.0]
        
        client = BaseballSavantClient(rate_limit_interval=2.0)
        client.last_request_time = 99.0  # 前回のリクエストは1秒前
        
        # 待機処理を実行
        client._wait_for_rate_limit()
        
        # 追加で1秒待機したことを検証
        mock_sleep.assert_called_once_with(1.0)
        assert client.last_request_time == 101.0
    
    @patch('src.infrastructure.baseball_savant_client.requests.Session.get')
    def test_get_pitch_data(self, mock_get):
        """get_pitch_dataメソッドのテスト"""
        # モックレスポンスの設定
        mock_response = MagicMock()
        csv_content = """pitch_type,game_date,release_speed,batter,pitcher,events,description,spin_rate
FF,2023-04-01,95.2,12345,543037,single,hit_into_play,2400
SL,2023-04-01,88.3,12345,543037,out,swinging_strike,2600
"""
        mock_response.content = csv_content.encode('utf-8')
        mock_get.return_value = mock_response
        
        client = BaseballSavantClient()
        client.last_request_time = 0  # レート制限をリセット
        
        # 投球データの取得
        df = client.get_pitch_data('543037', '2023-04-01')
        
        # リクエストが行われたことを検証
        mock_get.assert_called_once()
        assert mock_get.call_args[1]['params']['pitchers_lookup[]'] == '543037'
        
        # 結果を検証
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert df['pitch_type'][0] == 'FF'
    
    @patch('src.infrastructure.mlb_stats_client.MLBStatsClient.search_pitcher')
    def test_search_pitcher(self, mock_search_pitcher):
        """search_pitcherメソッドのテスト"""
        # モックデータの設定
        mock_search_pitcher.return_value = [
            {'id': 123, 'name': 'John Pitcher', 'team_name': 'Team A', 'position': 'P'},
            {'id': 456, 'name': 'Mike Pitcher', 'team_name': 'Team B', 'position': 'P'}
        ]
        
        client = BaseballSavantClient()
        
        # 検索実行
        results = client.search_pitcher('Pitcher')
        
        # 結果の検証
        assert len(results) == 2
        assert all(isinstance(p, Pitcher) for p in results)
        assert results[0].name == 'John Pitcher'
        assert results[1].team == 'Team B'