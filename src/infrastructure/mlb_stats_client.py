"""
MLB StatsAPIからデータを取得するクライアント
選手情報の検索を担当
"""
import requests
import re
import time
import logging
from typing import List, Dict, Any, Optional


class MLBStatsClient:
    """
    MLB StatsAPIからデータを取得するクライアント
    選手情報の検索を担当
    """
    
    BASE_URL = "https://statsapi.mlb.com/api/v1"
    
    def __init__(self, cache_ttl: int = 3600):
        """
        Parameters:
        -----------
        cache_ttl : int
            キャッシュの有効期間（秒）
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.logger = logging.getLogger(__name__)
        self.cache_ttl = cache_ttl
        
        # メモリ内キャッシュ
        self._teams_cache = None
        self._teams_cache_time = 0
        self._roster_cache = {}
        self._roster_cache_time = {}
    
    def get_all_teams(self) -> List[Dict[str, Any]]:
        """
        すべてのMLBチームのリストを取得
        
        Returns:
        --------
        List[Dict[str, Any]]
            チーム情報のリスト
        """
        # キャッシュチェック
        current_time = time.time()
        if self._teams_cache is not None and (current_time - self._teams_cache_time) < self.cache_ttl:
            self.logger.debug("チームリストをキャッシュから取得")
            return self._teams_cache
        
        # 新規取得
        url = f"{self.BASE_URL}/teams"
        params = {
            'sportId': 1  # MLB
        }
        
        try:
            self.logger.info("MLBチームリストをAPI経由で取得")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # 結果をキャッシュ
            self._teams_cache = data.get('teams', [])
            self._teams_cache_time = current_time
            
            return self._teams_cache
        except Exception as e:
            self.logger.error(f"チームリスト取得エラー: {str(e)}")
            return []
    
    def get_team_roster(self, team_id: int) -> List[Dict[str, Any]]:
        """
        特定チームのロスターを取得
        
        Parameters:
        -----------
        team_id : int
            チームID
            
        Returns:
        --------
        List[Dict[str, Any]]
            ロスター情報
        """
        # キャッシュチェック
        cache_key = str(team_id)
        current_time = time.time()
        if (cache_key in self._roster_cache and 
            (current_time - self._roster_cache_time.get(cache_key, 0)) < self.cache_ttl):
            self.logger.debug(f"チームID {team_id} のロスターをキャッシュから取得")
            return self._roster_cache[cache_key]
        
        # 新規取得
        url = f"{self.BASE_URL}/teams/{team_id}/roster"
        
        try:
            self.logger.info(f"チームID {team_id} のロスターをAPI経由で取得")
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            # 結果をキャッシュ
            self._roster_cache[cache_key] = data.get('roster', [])
            self._roster_cache_time[cache_key] = current_time
            
            return self._roster_cache[cache_key]
        except Exception as e:
            self.logger.error(f"ロスター取得エラー (チームID: {team_id}): {str(e)}")
            return []

    def search_player(self, name: str, position: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        選手名から選手を検索
        
        Parameters:
        -----------
        name : str
            選手名（部分一致で検索）
        position : str, optional
            ポジション略称（例: 'P' - Pitcher）
            
        Returns:
        --------
        List[Dict[str, Any]]
            検索結果の選手リスト
        """
        # 大文字小文字を区別せず、名前の一部で検索できるように正規表現パターンを用意
        name_pattern = re.compile(name, re.IGNORECASE)
        results = []
        
        # すべてのチームを取得
        teams = self.get_all_teams()
        self.logger.info(f"{len(teams)}チームのデータを検索します")
        
        for team in teams:
            team_id = team['id']
            team_name = team['name']
            
            # チームのロスターを取得
            roster = self.get_team_roster(team_id)
            
            # 名前が一致する選手を検索
            for player in roster:
                full_name = player.get('person', {}).get('fullName', '')
                player_position = player.get('position', {}).get('abbreviation', '')
                
                # 名前が一致し、ポジションも一致する（ポジション指定がある場合）
                if (name_pattern.search(full_name) and 
                    (position is None or player_position == position)):
                    # 選手情報を整形して結果に追加
                    player_info = {
                        'id': player.get('person', {}).get('id'),
                        'name': full_name,
                        'team_id': team_id,
                        'team_name': team_name,
                        'position': player_position
                    }
                    results.append(player_info)
                    self.logger.debug(f"選手が見つかりました: {full_name} (ID: {player_info['id']}, チーム: {team_name})")
        
        self.logger.info(f"'{name}'の検索結果: {len(results)}件")
        return results   
    
    def search_pitcher(self, name: str) -> List[Dict[str, Any]]:
        """
        投手名から投手を検索（ポジションがPの選手のみ）
        
        Parameters:
        -----------
        name : str
            投手名（部分一致で検索）
            
        Returns:
        --------
        List[Dict[str, Any]]
            検索結果の投手リスト
        """
        return self.search_player(name)
    
    def get_player_details(self, player_id: int) -> Dict[str, Any]:
        """
        選手IDから詳細情報を取得
        """
        url = f"https://statsapi.mlb.com/api/v1/people/{player_id}"
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('people', [{}])[0]  # 安全に取得
