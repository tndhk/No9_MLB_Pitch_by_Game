"""
Baseball Savant (Statcast) APIとの連携を担当するクライアント
"""
import requests
import pandas as pd
import io
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Union
import logging

from src.domain.entities import Pitcher, Game
from src.infrastructure.mlb_stats_client import MLBStatsClient


class BaseballSavantClient:
    """
    Baseball Savant (Statcast)からデータを取得するクライアント
    外部APIとの通信を担当する
    """
    
    BASE_URL = "https://baseballsavant.mlb.com/statcast_search/csv"
    
    def __init__(self, rate_limit_interval: float = 2.0):
        """
        Parameters:
        -----------
        rate_limit_interval : float
            API呼び出し間の最小待機時間（秒）
        """
        self.session = requests.Session()
        # ユーザーエージェントを設定してブロックを回避
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.rate_limit_interval = rate_limit_interval
        self.last_request_time = 0.0
        self.logger = logging.getLogger(__name__)
        
        # MLB StatsAPIクライアントを内部で保持
        self.mlb_stats_client = MLBStatsClient()
    
    def _wait_for_rate_limit(self) -> None:
        """APIレート制限を遵守するための待機処理"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.rate_limit_interval:
            wait_time = self.rate_limit_interval - elapsed
            self.logger.debug(f"レート制限のため {wait_time:.2f} 秒待機します")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()

    def get_pitcher_games(self, pitcher_id: str, season: int) -> List[Game]:
        self.logger.info(f"投手ID {pitcher_id}の{season}シーズンの試合リストを取得します")
        
        season_data = self.get_pitch_data(pitcher_id, None, season=str(season))
        
        if season_data is None or season_data.empty:
            self.logger.warning(f"投手ID {pitcher_id}の{season}シーズンデータが取得できませんでした")
            return []

        if 'game_date' not in season_data.columns or 'game_pk' not in season_data.columns:
            self.logger.warning("データに試合日または試合ID (game_pk) 情報がありません")
            return []

        games = []

        # ★★★★★ ここが重要 ★★★★★
        # pitcher_id & game_pk ごとの投球数集計
        game_groups = season_data.groupby(['game_pk', 'game_date'])

        for (game_pk, game_date), game_data in game_groups:
            # 試合で実際に投げてない場合を除外
            if len(game_data) == 0:
                continue
            
            # opponent, stadium, home_away はそのまま処理
            opponent = None
            stadium = None
            home_away = None
            
            if 'pitcher_team' in game_data.columns and 'home_team' in game_data.columns and 'away_team' in game_data.columns:
                pitcher_team = game_data['pitcher_team'].iloc[0]
                home_team = game_data['home_team'].iloc[0]
                away_team = game_data['away_team'].iloc[0]
                
                if pitcher_team == home_team:
                    opponent = away_team
                    home_away = 'home'
                else:
                    opponent = home_team
                    home_away = 'away'
            
            if 'stadium' in game_data.columns:
                stadium = game_data['stadium'].iloc[0]
            
            iso_date = pd.to_datetime(game_date).strftime('%Y-%m-%d')
            
            game = Game(
                date=iso_date,
                pitcher_id=pitcher_id,
                game_pk=int(game_pk),
                opponent=opponent,
                stadium=stadium,
                home_away=home_away
            )
            games.append(game)
        
        games.sort(key=lambda g: g.date, reverse=True)
        self.logger.info(f"{len(games)}試合のデータを取得しました（投球データが存在する試合のみ）")
        return games

    def get_pitch_data(self, 
                    pitcher_id: str, 
                    game_date: Optional[str] = None,
                    game_pk: Optional[int] = None,
                    season: str = "2023",
                    team: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        特定投手の投球データを取得（game_pk優先）
        """

        # ----- 共通パラメータ -----
        params = {
            'all': 'true',
            'hfGT': 'R|',  # レギュラーシーズンのみ
            'player_type': 'pitcher',
            'pitchers_lookup[]': str(pitcher_id),
            'team': team or '',
            'min_pitches': '0',
            'min_results': '0',
            'group_by': 'name',
            'sort_col': 'pitches',
            'player_event_sort': 'pitch_number',
            'sort_order': 'desc',
            'min_pas': '0',
            'type': 'details'
        }

        # ----- クエリ条件を決定 -----
        if game_pk:
            params['game_pk'] = str(game_pk)
            self.logger.info(f"Baseball Savantからデータ取得: 投手ID {pitcher_id}, game_pk {game_pk}")
        elif game_date:
            try:
                datetime.strptime(game_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("日付は'YYYY-MM-DD'形式で指定してください")
            params['game_date_gt'] = game_date
            params['game_date_lt'] = game_date
            self.logger.info(f"Baseball Savantからデータ取得: 投手ID {pitcher_id}, 試合日 {game_date}")
        else:
            params['hfSea'] = f'{season}|'
            self.logger.info(f"Baseball Savantからデータ取得: 投手ID {pitcher_id}, {season}シーズン全体")

        # ----- レート制限考慮 -----
        self._wait_for_rate_limit()

        # ----- API Request -----
        try:
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()
            df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))

            if df.empty:
                self.logger.warning(f"投手ID {pitcher_id} - データが見つかりませんでした")
                return None

            self.logger.info(f"取得成功: {len(df)}行のデータ取得")
            return df

        except requests.exceptions.RequestException as e:
            self.logger.error(f"APIエラー: {str(e)}")
            raise

        except pd.errors.ParserError:
            self.logger.error("CSVパースエラー")
            raise

    
    def search_pitcher(self, name: str) -> List[Pitcher]:
        """
        投手名から投手を検索
        
        Parameters:
        -----------
        name : str
            投手名（部分一致で検索）
            
        Returns:
        --------
        List[Pitcher]
            検索結果の投手エンティティリスト
        """
        self.logger.info(f"投手名 '{name}' で検索しています")
        
        # MLB StatsAPIを使用して投手を検索
        pitchers_data = self.mlb_stats_client.search_pitcher(name)
        
        # 検索結果をPitcherエンティティのリストに変換
        pitchers = []
        for pitcher_data in pitchers_data:
            # 投球腕情報を取得（可能であれば）
            pitcher_details = self.mlb_stats_client.get_player_details(pitcher_data['id'])
            throws = pitcher_details.get('pitchHand', {}).get('code') if pitcher_details else None
            
            pitcher = Pitcher(
                id=str(pitcher_data['id']),
                name=pitcher_data['name'],
                team=pitcher_data['team_name'],
                throws=throws
            )
            pitchers.append(pitcher)
        
        if not pitchers:
            self.logger.warning(f"警告: '{name}'に一致する投手が見つかりませんでした")
        else:
            self.logger.info(f"{len(pitchers)}人の投手が見つかりました")
        
        return pitchers