"""
Baseball Savant (Statcast) APIとの連携を担当するクライアント
"""
import requests
import pandas as pd
import io
import time
import json
import re
from datetime import datetime
from typing import List, Dict, Optional, Any, Union, Tuple
import logging
from bs4 import BeautifulSoup
import urllib.parse

from src.domain.entities import Pitcher, Game
from src.config import get_config

class BaseballSavantClient:
    """
    Baseball Savant (Statcast)からデータを取得するクライアント
    外部APIとの通信を担当する
    """
    
    def __init__(self, rate_limit_interval: Optional[float] = None):
        """
        Parameters:
        -----------
        rate_limit_interval : float, optional
            API呼び出し間の最小待機時間（秒）
            指定しない場合は設定ファイルから読み込む
        """
        # 設定の取得
        config = get_config()
        
        # ベースURL
        self.BASE_URL = config.get('api', 'baseball_savant', 'base_url')
        self.SEARCH_URL = config.get('api', 'baseball_savant', 'search_url')
        self.STATS_URL = config.get('api', 'baseball_savant', 'stats_url')
        self.PLAYER_URL = config.get('api', 'baseball_savant', 'player_url')
        
        # APIリクエスト設定
        self.rate_limit_interval = rate_limit_interval or config.get('api', 'baseball_savant', 'rate_limit')
        self.max_retries = config.get('api', 'baseball_savant', 'max_retries', default=3)
        self.timeout = config.get('api', 'baseball_savant', 'timeout', default=30)
        self.use_proxy = config.get('api', 'baseball_savant', 'use_proxy', default=False)
        
        # セッションの初期化
        self.session = requests.Session()
        
        # ユーザーエージェントを設定してブロックを回避
        user_agent = config.get('api', 'baseball_savant', 'user_agent')
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.last_request_time = 0.0
        self.logger = logging.getLogger(__name__)
        
        # 主要な投手のフォールバックデータ
        self.fallback_pitchers = {
            'Shohei Ohtani': {'id': '660271', 'team': 'Los Angeles Dodgers', 'throws': 'R'},
            'Gerrit Cole': {'id': '543037', 'team': 'New York Yankees', 'throws': 'R'},
            'Max Scherzer': {'id': '453286', 'team': 'Texas Rangers', 'throws': 'R'},
            'Jacob deGrom': {'id': '594798', 'team': 'Texas Rangers', 'throws': 'R'},
            'Yu Darvish': {'id': '506433', 'team': 'San Diego Padres', 'throws': 'R'},
            'Kodai Senga': {'id': '669011', 'team': 'New York Mets', 'throws': 'R'},
            'Yoshinobu Yamamoto': {'id': '993772', 'team': 'Los Angeles Dodgers', 'throws': 'R'},
            'Shota Imanaga': {'id': '682397', 'team': 'Chicago Cubs', 'throws': 'L'},
        }
        
        # プロキシ設定
        if self.use_proxy:
            # 環境変数からプロキシを取得するか、明示的に設定する
            # 例: self.session.proxies = {'http': 'http://proxy:port', 'https': 'https://proxy:port'}
            pass
    
    def _wait_for_rate_limit(self) -> None:
        """APIレート制限を遵守するための待機処理"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.rate_limit_interval:
            wait_time = self.rate_limit_interval - elapsed
            self.logger.debug(f"レート制限のため {wait_time:.2f} 秒待機します")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, method: str, url: str, params: Optional[Dict[str, Any]] = None,
                     data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None,
                     retry_count: int = 0) -> requests.Response:
        """
        API リクエストを実行（エラーハンドリングとリトライロジック付き）
        
        Parameters:
        -----------
        method : str
            HTTPメソッド ('GET', 'POST' など)
        url : str
            リクエストURL
        params : Dict[str, Any], optional
            クエリパラメータ
        data : Dict[str, Any], optional
            リクエストボディ
        headers : Dict[str, str], optional
            追加のHTTPヘッダー
        retry_count : int
            現在のリトライ回数
            
        Returns:
        --------
        requests.Response
            レスポンスオブジェクト
            
        Raises:
        -------
        requests.exceptions.RequestException
            リクエストに失敗し、リトライも失敗した場合
        """
        # レート制限の適用
        self._wait_for_rate_limit()
        
        try:
            # リクエストの実行
            self.logger.debug(f"{method} リクエスト: {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=headers,
                timeout=self.timeout
            )
            
            # ステータスコードのチェック
            response.raise_for_status()
            
            return response
            
        except requests.exceptions.RequestException as e:
            # エラーログ
            self.logger.warning(f"リクエスト失敗 ({retry_count+1}/{self.max_retries}): {url} - {str(e)}")
            
            # リトライ
            if retry_count < self.max_retries - 1:
                # バックオフ時間（指数関数的に増加: 2秒, 4秒, 8秒, ...）
                backoff = 2 ** retry_count
                self.logger.info(f"{backoff}秒後にリトライします...")
                time.sleep(backoff)
                
                # 再帰的にリトライ
                return self._make_request(method, url, params, data, headers, retry_count + 1)
            else:
                # リトライ上限に達した場合は例外を再発生
                self.logger.error(f"リトライ上限に達しました: {url}")
                raise
    
    def search_pitcher(self, name: str) -> List[Pitcher]:
        """
        投手名から投手を検索（実装）
        
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
        
        try:
            # Baseball Savantの検索APIリクエストの構築
            # 2025年時点での正確なAPIエンドポイント
            search_params = {
                'search': name,  # 検索キーワード
                'player_pool': 'All',  # すべての選手から検索
                'position': 'P',  # 投手のみ検索
                'type': 'player',
                'sort': 'relevance'
            }
            
            url = f"{self.SEARCH_URL}"
            response = self._make_request('GET', url, params=search_params)
            
            # JSONデータの解析
            search_results = []
            
            try:
                # Baseball Savantの検索結果はJSON形式で返される
                json_data = response.json()
                self.logger.debug(f"検索レスポンス: {json_data}")
                
                # 結果のパース（実際のJSON構造に合わせて調整）
                if 'results' in json_data:
                    players = json_data['results']
                    for player in players:
                        if player.get('position') in ['P', 'SP', 'RP']:  # 投手のみを抽出
                            player_id = str(player.get('player_id'))
                            player_name = player.get('player_name', '').strip()
                            team = player.get('team')
                            
                            # 投手の場合だけ追加
                            search_results.append(
                                Pitcher(
                                    id=player_id,
                                    name=player_name,
                                    team=team,  # チーム情報
                                    throws=None  # 投球腕は後で取得
                                )
                            )
            except ValueError as e:
                # JSONパースエラー - レスポンスがHTML形式の可能性がある
                self.logger.warning(f"JSONパースエラー: {e}")
                # HTML形式の場合はBeautifulSoupで解析を試みる
                try:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 選手リンクの抽出（実際のHTMLパターンに応じて調整）
                    player_links = soup.select('a.player-name-link, div.search-item a')
                    
                    for link in player_links:
                        player_name = link.text.strip()
                        
                        # playerid=XXXXのパターンを探す
                        href = link.get('href', '')
                        player_id_match = re.search(r'playerid=(\d+)', href)
                        
                        if player_id_match:
                            player_id = player_id_match.group(1)
                            
                            # 投手の場合だけ追加
                            search_results.append(
                                Pitcher(
                                    id=player_id,
                                    name=player_name,
                                    team=None,
                                    throws=None
                                )
                            )
                except Exception as e:
                    self.logger.error(f"HTML解析エラー: {e}")
            
            # 検索結果が空の場合はフォールバックデータを使用
            if not search_results:
                self.logger.warning(f"警告: '{name}'に一致する投手が見つかりませんでした - フォールバックデータを使用します")
                # 部分一致で名前を検索
                name_lower = name.lower()
                for pitcher_name, info in self.fallback_pitchers.items():
                    if name_lower in pitcher_name.lower():
                        search_results.append(
                            Pitcher(
                                id=info['id'],
                                name=pitcher_name,
                                team=info['team'],
                                throws=info['throws']
                            )
                        )
                
                if search_results:
                    self.logger.info(f"フォールバックデータから{len(search_results)}人の投手が見つかりました")
            else:
                self.logger.info(f"{len(search_results)}人の投手が見つかりました")
            
            # 検索結果を返す
            return search_results
            
        except Exception as e:
            self.logger.error(f"投手検索中にエラーが発生しました: {str(e)}")
            # エラー時はフォールバックデータから検索
            name_lower = name.lower()
            results = []
            for pitcher_name, info in self.fallback_pitchers.items():
                if name_lower in pitcher_name.lower():
                    results.append(
                        Pitcher(
                            id=info['id'],
                            name=pitcher_name,
                            team=info['team'],
                            throws=info['throws']
                        )
                    )
            return results
    
    def get_pitcher_details(self, pitcher_id: str) -> Optional[Pitcher]:
        """
        投手の詳細情報を取得
        
        Parameters:
        -----------
        pitcher_id : str
            投手ID
            
        Returns:
        --------
        Optional[Pitcher]
            投手の詳細情報。取得失敗時はNone
        """
        self.logger.info(f"投手ID {pitcher_id} の詳細情報を取得しています")
        
        # まずフォールバックデータを確認
        for name, info in self.fallback_pitchers.items():
            if info['id'] == pitcher_id:
                return Pitcher(
                    id=pitcher_id,
                    name=name,
                    team=info['team'],
                    throws=info['throws']
                )
        
        try:
            # 投手詳細ページのURL
            url = f"{self.PLAYER_URL}/{pitcher_id}"
            response = self._make_request('GET', url)
            
            # HTMLから必要な情報を抽出
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 名前の取得
            name_elem = soup.select_one('h1.player-name, div.player-header-name')
            name = name_elem.text.strip() if name_elem else "不明"
            
            # チーム情報の取得
            team_elem = soup.select_one('span.player-team, div.player-team')
            team = team_elem.text.strip() if team_elem else None
            
            # 投球腕の取得
            throws_elem = soup.select_one('span.player-throws, div.player-throws')
            throws = None
            if throws_elem:
                throws_text = throws_elem.text.strip()
                throws_match = re.search(r'Throws:\s+([RL])', throws_text)
                if throws_match:
                    throws = throws_match.group(1)
            
            # Pitcherエンティティを作成
            pitcher = Pitcher(
                id=pitcher_id,
                name=name,
                team=team,
                throws=throws
            )
            
            self.logger.info(f"投手詳細情報を取得しました: {name} (Team: {team}, Throws: {throws})")
            return pitcher
            
        except Exception as e:
            self.logger.error(f"投手詳細情報の取得中にエラーが発生しました: {str(e)}")
            return None
    
    def get_pitcher_games(self, pitcher_id: str, season: int) -> List[Game]:
        """
        指定した投手の特定シーズンの試合リストを取得
        
        Parameters:
        -----------
        pitcher_id : str
            投手のMLB ID
        season : int
            シーズン年
            
        Returns:
        --------
        List[Game]
            試合エンティティのリスト
        """
        self.logger.info(f"投手ID {pitcher_id}の{season}シーズンの試合リストを取得します")
        
        # シーズンデータを取得
        season_data = self.get_pitch_data(pitcher_id, None, season=str(season))
        
        if season_data is None or season_data.empty:
            self.logger.warning(f"投手ID {pitcher_id}の{season}シーズンデータが取得できませんでした")
            return []
        
        # game_dateカラムが存在するか確認
        if 'game_date' not in season_data.columns:
            self.logger.warning("データに試合日情報がありません")
            return []
        
        # game_pkカラムが存在するか確認（試合ID）
        has_game_pk = 'game_pk' in season_data.columns
        
        # teamカラムが存在するか確認
        has_team = 'home_team' in season_data.columns and 'away_team' in season_data.columns
        
        # ユニークな試合をグループ化
        games = []
        unique_game_dates = season_data['game_date'].unique()
        
        for game_date in unique_game_dates:
            # そのゲームのデータだけ抽出
            game_data = season_data[season_data['game_date'] == game_date]
            
            # ゲーム情報の抽出
            opponent = None
            stadium = None
            home_away = None
            
            if has_team:
                pitcher_team = game_data['pitcher_team'].iloc[0] if 'pitcher_team' in game_data.columns else None
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
            
            # ISO形式に変換
            try:
                date_obj = pd.to_datetime(game_date)
                iso_date = date_obj.strftime('%Y-%m-%d')
            except:
                iso_date = str(game_date)
            
            # Gameエンティティ作成
            game = Game(
                date=iso_date,
                pitcher_id=pitcher_id,
                opponent=opponent,
                stadium=stadium,
                home_away=home_away
            )
            
            games.append(game)
        
        # 日付でソート
        games.sort(key=lambda g: g.date, reverse=True)
        
        self.logger.info(f"{len(games)}試合のデータを取得しました")
        return games
    
    def get_pitch_data(self, 
                      pitcher_id: str, 
                      game_date: Optional[str] = None, 
                      season: str = "2023",
                      team: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        特定投手の投球データを取得
        
        Parameters:
        -----------
        pitcher_id : str
            投手のMLB ID
        game_date : str, optional
            試合日（YYYY-MM-DD形式）。Noneの場合は日付指定なし（シーズン全体）
        season : str, optional
            シーズン年（デフォルト: "2023"）
        team : str, optional
            チーム略称（例: 'NYY', 'LAD'）
            
        Returns:
        --------
        Optional[pd.DataFrame]
            投手の投球データ。取得失敗時はNone
        """
        # 日付形式の検証（指定がある場合）
        if game_date:
            try:
                datetime.strptime(game_date, '%Y-%m-%d')
            except ValueError:
                self.logger.error("日付は'YYYY-MM-DD'形式で指定してください")
                raise ValueError("日付は'YYYY-MM-DD'形式で指定してください")
        
        # リクエストパラメータの設定
        params = {
            'all': 'true',
            'hfPT': '',
            'hfAB': '',
            'hfGT': 'R|',  # レギュラーシーズンのみ
            'hfPR': '',
            'hfZ': '',
            'stadium': '',
            'hfBBL': '',
            'hfNewZones': '',
            'hfPull': '',
            'hfC': '',
            'hfSea': f'{season}|',  # シーズン（年）
            'hfSit': '',
            'player_type': 'pitcher',
            'hfOuts': '',
            'pitcher_throws': '',
            'batter_stands': '',
            'hfSA': '',
            'pitchers_lookup[]': str(pitcher_id),
            'team': team if team else '',
            'position': '',
            'hfRO': '',
            'home_road': '',
            'hfFlag': '',
            'metric_1': '',
            'hfInn': '',
            'min_pitches': '0',
            'min_results': '0',
            'group_by': 'name',
            'sort_col': 'pitches',
            'player_event_sort': 'pitch_number',
            'sort_order': 'desc',
            'min_pas': '0',
            'type': 'details'
        }
        
        # 特定の試合日が指定されている場合
        if game_date:
            params['game_date_gt'] = game_date
            params['game_date_lt'] = game_date
            self.logger.info(f"Baseball Savantからデータを取得中: 投手ID {pitcher_id}, 試合日 {game_date}")
        else:
            self.logger.info(f"Baseball Savantからデータを取得中: 投手ID {pitcher_id}, {season}シーズン全体")
        
        try:
            # CSVデータのリクエスト
            response = self._make_request('GET', self.STATS_URL, params=params)
            
            # CSVデータの解析
            csv_data = response.content.decode('utf-8')
            df = pd.read_csv(io.StringIO(csv_data))
            
            # データが空でないか確認
            if df.empty:
                self.logger.warning(f"警告: 投手ID {pitcher_id}のデータが見つかりませんでした")
                return None
                
            self.logger.info(f"取得成功: {len(df)}行のデータを取得しました")
            return df
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"エラー: データ取得中にエラーが発生しました - {str(e)}")
            raise
        except pd.errors.ParserError:
            self.logger.error("エラー: CSVデータの解析に失敗しました")
            raise