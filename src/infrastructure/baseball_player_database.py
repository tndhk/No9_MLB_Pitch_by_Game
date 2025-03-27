"""
MLBの選手データベース - API障害時のフォールバック用
"""
from typing import List, Dict, Optional, Any
import re
import logging
from src.domain.entities import Pitcher


class BaseballPlayerDatabase:
    """
    MLBの選手データベース - API障害時のフォールバック用
    実際の本番APIが使用できない場合に使用する主要選手のデータを提供
    """
    
    def __init__(self):
        """選手データベースの初期化"""
        self.logger = logging.getLogger(__name__)
        
        # 主要な投手のデータ
        self.pitchers: Dict[str, Dict[str, Any]] = {
            '660271': {
                'name': 'Shohei Ohtani',
                'team': 'Los Angeles Dodgers',
                'throws': 'R',
                'keywords': ['ohtani', 'shohei', 'angels', 'dodgers', 'japan', 'japanese', 'two-way']
            },
            '543037': {
                'name': 'Gerrit Cole',
                'team': 'New York Yankees',
                'throws': 'R',
                'keywords': ['cole', 'gerrit', 'yankees', 'pirates', 'astros']
            },
            '453286': {
                'name': 'Max Scherzer',
                'team': 'Texas Rangers',
                'throws': 'R',
                'keywords': ['scherzer', 'max', 'mets', 'nationals', 'tigers', 'dodgers', 'rangers']
            },
            '594798': {
                'name': 'Jacob deGrom',
                'team': 'Texas Rangers',
                'throws': 'R',
                'keywords': ['degrom', 'jacob', 'mets', 'rangers']
            },
            '506433': {
                'name': 'Yu Darvish',
                'team': 'San Diego Padres',
                'throws': 'R',
                'keywords': ['darvish', 'yu', 'japan', 'japanese', 'padres', 'cubs', 'rangers', 'dodgers']
            },
            '669011': {
                'name': 'Kodai Senga',
                'team': 'New York Mets', 
                'throws': 'R',
                'keywords': ['senga', 'kodai', 'japan', 'japanese', 'mets']
            },
            '993772': {
                'name': 'Yoshinobu Yamamoto',
                'team': 'Los Angeles Dodgers',
                'throws': 'R',
                'keywords': ['yamamoto', 'yoshinobu', 'japan', 'japanese', 'dodgers']
            },
            '682397': {
                'name': 'Shota Imanaga',
                'team': 'Chicago Cubs',
                'throws': 'L',
                'keywords': ['imanaga', 'shota', 'japan', 'japanese', 'cubs']
            },
            '676265': {
                'name': 'Roki Sasaki',
                'team': 'Chiba Lotte Marines',
                'throws': 'R',
                'keywords': ['sasaki', 'roki', 'japan', 'japanese', 'marines', 'lotte']
            },
            '605483': {
                'name': 'Blake Snell',
                'team': 'San Francisco Giants',
                'throws': 'L',
                'keywords': ['snell', 'blake', 'rays', 'padres', 'giants']
            },
            '608566': {
                'name': 'Aaron Nola',
                'team': 'Philadelphia Phillies',
                'throws': 'R',
                'keywords': ['nola', 'aaron', 'phillies']
            },
            '519242': {
                'name': 'Clayton Kershaw',
                'team': 'Los Angeles Dodgers',
                'throws': 'L',
                'keywords': ['kershaw', 'clayton', 'dodgers']
            },
            '425844': {
                'name': 'Justin Verlander',
                'team': 'Houston Astros',
                'throws': 'R',
                'keywords': ['verlander', 'justin', 'astros', 'tigers', 'mets']
            },
            '592789': {
                'name': 'Marcus Stroman',
                'team': 'New York Yankees',
                'throws': 'R',
                'keywords': ['stroman', 'marcus', 'yankees', 'cubs', 'mets', 'blue jays']
            }
        }
    
    def search_pitcher(self, name: str) -> List[Pitcher]:
        """
        名前に基づいて投手を検索
        
        Parameters:
        -----------
        name : str
            検索する投手名または部分文字列
            
        Returns:
        --------
        List[Pitcher]
            マッチした投手のリスト
        """
        self.logger.info(f"フォールバックデータベースから '{name}' の検索を実行中")
        
        results = []
        name_lower = name.lower()
        
        # 部分一致でキーワード検索
        for pitcher_id, data in self.pitchers.items():
            # 名前に直接含まれているか確認
            if name_lower in data['name'].lower():
                results.append(
                    Pitcher(
                        id=pitcher_id,
                        name=data['name'],
                        team=data['team'],
                        throws=data['throws']
                    )
                )
                continue
            
            # キーワードに含まれているか確認
            for keyword in data['keywords']:
                if name_lower in keyword or keyword in name_lower:
                    results.append(
                        Pitcher(
                            id=pitcher_id,
                            name=data['name'],
                            team=data['team'],
                            throws=data['throws']
                        )
                    )
                    break
        
        self.logger.info(f"フォールバックデータベースから {len(results)}件の結果が見つかりました")
        return results
    
    def get_pitcher_by_id(self, pitcher_id: str) -> Optional[Pitcher]:
        """
        IDによって投手を取得
        
        Parameters:
        -----------
        pitcher_id : str
            投手ID
            
        Returns:
        --------
        Optional[Pitcher]
            マッチした投手。見つからない場合はNone
        """
        if pitcher_id in self.pitchers:
            data = self.pitchers[pitcher_id]
            return Pitcher(
                id=pitcher_id,
                name=data['name'],
                team=data['team'],
                throws=data['throws']
            )
        return None