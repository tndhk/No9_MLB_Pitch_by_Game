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
        
        # レート制限の対応
        self._wait_for_rate_limit()
        
        try:
            # CSVデータのリクエスト
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()  # エラーレスポンスの場合は例外を発生
            
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