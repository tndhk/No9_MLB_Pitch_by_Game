"""
BaseballSavantClientクラスのテスト
"""
import pytest
import pandas as pd
import requests
from unittest.mock import MagicMock, patch

from src.infrastructure.baseball_savant_client import BaseballSavantClient
from src.domain.entities import Pitcher


@pytest.fixture
def mock_session():
    """リクエストセッションのモック"""
    session = MagicMock()
    response = MagicMock()
    
    # CSVデータの例
    csv_content = """pitch_type,game_date,release_speed,batter,pitcher,events,description,spin_rate
FF,2023-04-01,95.2,12345,543037,single,hit_into_play,2400
SL,2023-04-01,88.3,12345,543037,out,swinging_strike,2600
"""
    
    response.content = csv_content.encode('utf-8')
    response.raise_for_status = MagicMock()
    session.get.return_value = response
    
    return session


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
    
    def test_get_pitch_data_with_mock_session(self, mock_session):
        """get_pitch_dataメソッドのテスト（モックセッション使用）"""
        client = BaseballSavantClient()
        client.session = mock_session
        
        # 最終リクエスト時刻を初期化
        client.last_request_time = 0
        
        # 投球データの取得
        df = client.get_pitch_data('543037', '2023-04-01')
        
        # リクエストが行われたことを検証
        mock_session.get.assert_called_once()
        
        # DataFrameが返されたことを検証
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert 'pitch_type' in df.columns
        assert 'release_speed' in df.columns
    
    def test_search_pitcher(self):
        """search_pitcherメソッドのテスト"""
        client = BaseballSavantClient()
        
        # 検索実行
        results = client.search_pitcher('Ohtani')
        
        # 結果の検証
        assert isinstance(results, list)
        assert all(isinstance(p, Pitcher) for p in results)
        assert any(p.name == 'Shohei Ohtani' for p in results)
    
    @patch('src.infrastructure.baseball_savant_client.BaseballSavantClient.get_pitch_data')
    def test_get_pitcher_games(self, mock_get_pitch_data):
        """get_pitcher_gamesメソッドのテスト"""
        # モックの設定
        mock_df = pd.DataFrame({
            'game_date': ['2023-04-01', '2023-04-01', '2023-04-06', '2023-04-06'],
            'home_team': ['NYY', 'NYY', 'LAD', 'LAD'],
            'away_team': ['BOS', 'BOS', 'SF', 'SF'],
            'pitcher_team': ['NYY', 'NYY', 'LAD', 'LAD'],
            'stadium': ['Yankee Stadium', 'Yankee Stadium', 'Dodger Stadium', 'Dodger Stadium']
        })
        mock_get_pitch_data.return_value = mock_df
        
        client = BaseballSavantClient()
        
        # 試合リストの取得
        games = client.get_pitcher_games('543037', 2023)
        
        # 結果の検証
        assert isinstance(games, list)
        assert len(games) == 2  # ユニークな試合日は2日分
        assert games[0].date == '2023-04-06'  # 日付降順
        assert games[1].date == '2023-04-01'