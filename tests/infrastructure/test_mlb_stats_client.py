class TestMLBStatsClient:
    """MLBStatsClientクラスのテスト"""
    
    def test_init(self):
        """初期化のテスト"""
        client = MLBStatsClient()
        assert client.BASE_URL == "https://statsapi.mlb.com/api/v1"
        assert client.cache_ttl == 3600
    
    @patch('requests.Session.get')
    def test_get_all_teams(self, mock_get):
        """チーム取得のテスト"""
        # モックレスポンスの設定
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'teams': [
                {'id': 1, 'name': 'Team A'},
                {'id': 2, 'name': 'Team B'}
            ]
        }
        mock_get.return_value = mock_response
        
        client = MLBStatsClient()
        teams = client.get_all_teams()
        
        assert len(teams) == 2
        assert teams[0]['name'] == 'Team A'
        assert teams[1]['id'] == 2
    
    @patch('requests.Session.get')
    def test_get_team_roster(self, mock_get):
        """ロスター取得のテスト"""
        # モックレスポンスの設定
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'roster': [
                {'person': {'id': 123, 'fullName': 'Player X'}, 'position': {'abbreviation': 'P'}},
                {'person': {'id': 456, 'fullName': 'Player Y'}, 'position': {'abbreviation': 'C'}}
            ]
        }
        mock_get.return_value = mock_response
        
        client = MLBStatsClient()
        roster = client.get_team_roster(1)
        
        assert len(roster) == 2
        assert roster[0]['person']['fullName'] == 'Player X'
        assert roster[1]['position']['abbreviation'] == 'C'
    
    @patch('src.infrastructure.mlb_stats_client.MLBStatsClient.get_all_teams')
    @patch('src.infrastructure.mlb_stats_client.MLBStatsClient.get_team_roster')
    def test_search_pitcher(self, mock_get_roster, mock_get_teams):
        """投手検索のテスト"""
        # モックデータの設定
        mock_get_teams.return_value = [
            {'id': 1, 'name': 'Team A'},
            {'id': 2, 'name': 'Team B'}
        ]
        
        mock_get_roster.side_effect = [
            # Team A's roster
            [
                {'person': {'id': 123, 'fullName': 'John Pitcher'}, 'position': {'abbreviation': 'P'}},
                {'person': {'id': 456, 'fullName': 'Bob Batter'}, 'position': {'abbreviation': 'OF'}}
            ],
            # Team B's roster
            [
                {'person': {'id': 789, 'fullName': 'Mike Pitcher'}, 'position': {'abbreviation': 'P'}},
                {'person': {'id': 101, 'fullName': 'Alex Catcher'}, 'position': {'abbreviation': 'C'}}
            ]
        ]
        
        client = MLBStatsClient()
        pitchers = client.search_pitcher('Pitcher')
        
        assert len(pitchers) == 2
        assert pitchers[0]['name'] == 'John Pitcher'
        assert pitchers[1]['team_name'] == 'Team B'