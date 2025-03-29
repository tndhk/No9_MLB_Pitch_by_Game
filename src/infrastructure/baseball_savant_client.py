"""
Baseball Savant (Statcast) APIとの連携を担当するクライアント
"""
import requests
import pandas as pd
import io
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Union

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
        """
        特定投手の特定シーズンの試合リストを取得
        
        Parameters:
        -----------
        pitcher_id : str
            投手ID
        season : int
            シーズン年
            
        Returns:
        --------
        List[Game]
            Game エンティティのリスト
        """
        self.logger.info(f"投手ID {pitcher_id}の{season}シーズンの試合リストを取得します")
        
        try:
            # シーズンデータを取得
            season_data = self.get_pitch_data(pitcher_id, None, season=str(season))
            
            if season_data is None or season_data.empty:
                self.logger.warning(f"投手ID {pitcher_id}の{season}シーズンデータが取得できませんでした")
                return []

            # 必要なカラムがあるか確認
            if 'game_date' not in season_data.columns:
                self.logger.warning("データに試合日情報がありません")
                return []
            
            # game_pkカラムの確認
            has_game_pk = 'game_pk' in season_data.columns
            
            games = []

            # ゲームの日付をユニークに抽出
            unique_dates = pd.to_datetime(season_data['game_date']).dt.date.unique()
            self.logger.info(f"{len(unique_dates)}個のユニークな試合日を特定しました")
            
            # 各試合日に対して処理
            for game_date in sorted(unique_dates, reverse=True):
                iso_date = game_date.strftime('%Y-%m-%d')
                
                # この日付のデータを抽出
                date_data = season_data[pd.to_datetime(season_data['game_date']).dt.date == game_date]
                
                # game_pkがある場合はそれを使用
                game_pk = None
                if has_game_pk and not date_data['game_pk'].empty:
                    game_pk = int(date_data['game_pk'].iloc[0])
                
                # チーム情報の取得
                opponent = None
                home_away = None
                stadium = None
                
                # Baseball Savantデータから直接チーム情報の取得を試みる
                if 'home_team' in date_data.columns and 'away_team' in date_data.columns:
                    if 'pitcher_team' in date_data.columns:
                        pitcher_team = date_data['pitcher_team'].iloc[0] if not date_data['pitcher_team'].empty else None
                        home_team = date_data['home_team'].iloc[0] if not date_data['home_team'].empty else None
                        away_team = date_data['away_team'].iloc[0] if not date_data['away_team'].empty else None
                        
                        if pitcher_team and home_team and away_team:
                            if pitcher_team == home_team:
                                opponent = away_team
                                home_away = 'home'
                            else:
                                opponent = home_team
                                home_away = 'away'
                
                # カラム名が異なる場合の対応（team_homeやteam_awayなど）
                if opponent is None:
                    possible_home_cols = ['home_team', 'team_home', 'home']
                    possible_away_cols = ['away_team', 'team_away', 'away']
                    possible_pitcher_cols = ['pitcher_team', 'team', 'player_team']
                    
                    # 存在するカラムを探す
                    home_col = next((col for col in possible_home_cols if col in date_data.columns), None)
                    away_col = next((col for col in possible_away_cols if col in date_data.columns), None)
                    pitcher_col = next((col for col in possible_pitcher_cols if col in date_data.columns), None)
                    
                    if home_col and away_col:
                        home_team = date_data[home_col].iloc[0] if not date_data[home_col].empty else None
                        away_team = date_data[away_col].iloc[0] if not date_data[away_col].empty else None
                        
                        if pitcher_col:
                            pitcher_team = date_data[pitcher_col].iloc[0] if not date_data[pitcher_col].empty else None
                            if pitcher_team and home_team and away_team:
                                if pitcher_team == home_team:
                                    opponent = away_team
                                    home_away = 'home'
                                else:
                                    opponent = home_team
                                    home_away = 'away'
                        else:
                            # 投手のチームがわからない場合はホーム・アウェイ両方表示
                            if home_team and away_team:
                                opponent = f"{away_team} @ {home_team}"
                
                # 球場情報を取得
                if 'stadium' in date_data.columns and not date_data['stadium'].empty:
                    stadium = date_data['stadium'].iloc[0]
                
                # MLB StatsAPIから情報を補完（game_pkがある場合）
                if (opponent is None or stadium is None) and game_pk:
                    self.logger.info(f"チーム情報をMLB StatsAPIから取得 (試合ID: {game_pk})")
                    game_info = self.mlb_stats_client.get_game_info(game_pk)
                    
                    if game_info:
                        # 対戦チーム情報がまだない場合は設定
                        if opponent is None and 'home_team' in game_info and 'away_team' in game_info:
                            home_team = game_info.get('home_team', '')
                            away_team = game_info.get('away_team', '')
                            opponent = f"{away_team} @ {home_team}"
                        
                        # 球場情報がまだない場合は設定
                        if stadium is None and 'venue' in game_info:
                            stadium = game_info.get('venue')

                # ゲームオブジェクトの作成
                game = Game(
                    date=iso_date,
                    pitcher_id=pitcher_id,
                    game_pk=game_pk,
                    opponent=opponent,
                    stadium=stadium,
                    home_away=home_away
                )
                
                games.append(game)
            
            self.logger.info(f"{len(games)}試合のデータを取得しました")
            return games
            
        except Exception as e:
            self.logger.error(f"試合リスト取得中にエラーが発生しました: {str(e)}", exc_info=True)
            return []

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
            
            # 空のCSVが返される場合があるので確認
            content = response.content.decode('utf-8')
            if not content.strip():
                self.logger.warning(f"投手ID {pitcher_id} - 空のレスポンスが返されました")
                return None
                
            df = pd.read_csv(io.StringIO(content))

            if df.empty:
                self.logger.warning(f"投手ID {pitcher_id} - データが見つかりませんでした")
                return None

            self.logger.info(f"取得成功: {len(df)}行のデータ取得")
            return df

        except requests.exceptions.RequestException as e:
            self.logger.error(f"APIエラー: {str(e)}")
            raise

        except pd.errors.ParserError as e:
            self.logger.error(f"CSVパースエラー: {str(e)}")
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