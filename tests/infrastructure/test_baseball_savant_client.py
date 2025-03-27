"""
BaseballSavantClientクラスのテスト
"""
import pytest
import pandas as pd
import requests
from unittest.mock import MagicMock, patch, ANY

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
    session.request.return_value = response
    
    return session


@pytest.fixture
def mock_search_response():
    """検索結果のモック"""
    response = MagicMock()
    
    # HTML検索結果の例
    html_content = """
    <div class="search-results">
        <a href="/savant-player/playerid=543037" class="player-name-link">Gerrit Cole</a>
        <a href="/savant-player/playerid=660271" class="player-name-link">Shohei Ohtani</a>
    </div>
    """
    
    response.text = html_content
    response.raise_for_status = MagicMock()
    
    return response


@pytest.fixture
def mock_pitcher_details_response():
    """投手詳細情報のモック"""
    response = MagicMock()
    
    # HTML検索結果の例
    html_content = """
    <div class="player-header">
        <h1 class="player-name">Gerrit Cole</h1>
        <span class="player-team">New York Yankees</span>
        <span class="player-throws">Throws: R</span>
    </div>
    """
    
    response.text = html_content
    response.raise_for_status = MagicMock()
    
    return response


class TestBaseballSavantClient:
    """BaseballSavantClientクラスのテスト"""
    
    @patch('src.infrastructure.baseball_savant_client.requests.Session')
    def test_init(self, mock_session_class):
        """初期化のテスト"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        client = BaseballSavantClient()
        
        # セッションヘッダーの設定を検証
        assert mock_session.headers.update.called
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
        mock_session.request.assert_called_once()
        
        # DataFrameが返されたことを検証
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert 'pitch_type' in df.columns
        assert 'release_speed' in df.columns
    
    @patch('src.infrastructure.baseball_savant_client.BaseballSavantClient._make_request')
    def test_search_pitcher(self, mock_make_request, mock_search_response):
        """search_pitcherメソッドのテスト"""
        client = BaseballSavantClient()
        
        # 検索レスポンスをモック
        mock_make_request.return_value = mock_search_response
        
        # 検索実行
        results = client.search_pitcher('Cole')
        
        # _make_requestが呼ばれたことを検証
        mock_make_request.assert_called_once()
        
        # 結果の検証
        assert isinstance(results, list)
        assert all(isinstance(p, Pitcher) for p in results)
        # "Gerrit Cole"が検索結果に含まれることを確認
        assert any(p.id == '543037' for p in results)
    
    @patch('src.infrastructure.baseball_savant_client.BaseballSavantClient._make_request')
    def test_get_pitcher_details(self, mock_make_request, mock_pitcher_details_response):
        """get_pitcher_detailsメソッドのテスト"""
        client = BaseballSavantClient()
        
        # 詳細情報レスポンスをモック
        mock_make_request.return_value = mock_pitcher_details_response
        
        # 詳細情報の取得
        pitcher = client.get_pitcher_details('543037')
        
        # _make_requestが呼ばれたことを検証
        mock_make_request.assert_called_once()
        
        # 結果の検証
        assert isinstance(pitcher, Pitcher)
        assert pitcher.id == '543037'
        assert pitcher.name == 'Gerrit Cole'
        assert pitcher.team == 'New York Yankees'
        assert pitcher.throws == 'R'
    
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
    
    @patch('requests.Session.request')
    @patch('time.sleep')
    def test_make_request_with_retry(self, mock_sleep, mock_request):
        """_make_requestメソッドのリトライ機能テスト"""
        # 最初の2回は例外を発生させ、3回目は成功させる
        mock_response = MagicMock()
        mock_request.side_effect = [
            requests.exceptions.ConnectionError("Connection error"),
            requests.exceptions.Timeout("Timeout error"),
            mock_response
        ]
        
        client = BaseballSavantClient()
        client.max_retries = 3  # リトライ回数を設定
        
        # リクエスト実行
        response = client._make_request('GET', 'https://example.com')
        
        # リクエストが3回呼ばれたことを検証
        assert mock_request.call_count == 3
        
        # sleepが2回呼ばれたことを検証（リトライごとに1回）
        assert mock_sleep.call_count == 2
        
        # 正常なレスポンスが返されたことを検証
        assert response == mock_response