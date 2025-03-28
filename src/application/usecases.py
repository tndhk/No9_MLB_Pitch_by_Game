"""
アプリケーション層のユースケースクラス
各コンポーネントを連携させ、アプリケーションのビジネスロジックを実装
"""
import logging
from typing import List, Dict, Any, Optional

from src.domain.entities import Pitcher, Game
from src.domain.pitch_analyzer import PitchAnalyzer
from src.infrastructure.baseball_savant_client import BaseballSavantClient
from src.infrastructure.data_repository import DataRepository
from src.application.analysis_result import AnalysisResult


class PitcherGameAnalysisUseCase:
    """
    投手1試合分析のユースケース
    
    アプリケーション層のユースケースクラス
    ドメイン層とインフラストラクチャ層を連携させる
    """
    
    def __init__(
        self,
        client: BaseballSavantClient,
        repository: DataRepository,
        analyzer: PitchAnalyzer
    ):
        """
        Parameters:
        -----------
        client : BaseballSavantClient
            Baseball Savantクライアント
        repository : DataRepository
            データリポジトリ
        analyzer : PitchAnalyzer
            投球分析ツール
        """
        self.client = client
        self.repository = repository
        self.analyzer = analyzer
        self.logger = logging.getLogger(__name__)
    
    def search_pitchers(self, name: str) -> List[Pitcher]:
        """
        投手名から投手を検索
        
        Parameters:
        -----------
        name : str
            投手名（部分一致で検索）
            
        Returns:
        --------
        List[Pitcher]
            検索結果の投手リスト
        """
        self.logger.info(f"投手名 '{name}' で検索します")
        
        # クライアントを使用して投手を検索
        pitchers = self.client.search_pitcher(name)
        
        # 見つかった投手をリポジトリに保存
        for pitcher in pitchers:
            self.repository.save_pitcher_info(pitcher)
        
        return pitchers
    
    def get_pitcher_games(self, pitcher_id: str, season: int = 2023) -> List[Game]:
        """
        投手IDからその年の試合一覧を取得
        
        Parameters:
        -----------
        pitcher_id : str
            投手ID
        season : int
            シーズン年（デフォルト: 2023）
            
        Returns:
        --------
        List[Game]
            試合エンティティのリスト
        """
        self.logger.info(f"投手ID {pitcher_id} の{season}シーズンの試合を取得します")
        
        # リポジトリからキャッシュされた試合一覧を取得
        cached_games = self.repository.get_games_by_pitcher(pitcher_id)
        
        # キャッシュから当該シーズンの試合だけ抽出
        season_games = [g for g in cached_games if g.date.startswith(str(season))]
        
        # キャッシュが十分でない場合、APIから取得
        if len(season_games) < 5:  # 5試合未満の場合は更新
            self.logger.info(f"キャッシュ不十分: APIから試合データを取得します")
            api_games = self.client.get_pitcher_games(pitcher_id, season)
            
            # リポジトリに保存
            for game in api_games:
                self.repository.save_game_info(game)
            
            return api_games
        
        self.logger.info(f"キャッシュから{len(season_games)}試合分のデータを取得しました")
        return season_games
    
    def analyze_game(self, pitcher_id: str, game_date: str) -> AnalysisResult:
        """
        特定試合の分析を実行
        
        Parameters:
        -----------
        pitcher_id : str
            投手ID
        game_date : str
            試合日（YYYY-MM-DD形式）
            
        Returns:
        --------
        AnalysisResult
            分析結果
        """
        self.logger.info(f"投手ID {pitcher_id} の{game_date}の試合を分析します")
        
        # 投手情報の取得
        pitcher = self.repository.get_pitcher_info(pitcher_id)
        if pitcher is None:
            error_msg = f"投手ID {pitcher_id} の情報が見つかりません"
            self.logger.error(error_msg)
            return AnalysisResult(
                pitcher_id=pitcher_id,
                pitcher_name="Unknown",
                game_date=game_date,
                inning_analysis={},
                pitch_type_analysis={},
                error=error_msg
            )
        
        # キャッシュからデータ取得を試みる
        pitch_data = self.repository.get_cached_pitch_data(pitcher_id, game_date)
        
        # キャッシュになければAPIから取得
        if pitch_data is None:
            try:
                self.logger.info(f"キャッシュにデータがないため、APIから取得します")
                pitch_data = self.client.get_pitch_data(pitcher_id, game_date)
                
                if pitch_data is None or pitch_data.empty:
                    error_msg = f"投手ID {pitcher_id} の{game_date}の試合データが取得できませんでした"
                    self.logger.error(error_msg)
                    return AnalysisResult(
                        pitcher_id=pitcher_id,
                        pitcher_name=pitcher.name,
                        game_date=game_date,
                        inning_analysis={},
                        pitch_type_analysis={},
                        error=error_msg
                    )
                
                # データをキャッシュに保存
                self.repository.save_pitch_data(pitcher_id, game_date, pitch_data)
                
            except Exception as e:
                error_msg = f"データ取得中にエラーが発生しました: {str(e)}"
                self.logger.error(error_msg)
                return AnalysisResult(
                    pitcher_id=pitcher_id,
                    pitcher_name=pitcher.name,
                    game_date=game_date,
                    inning_analysis={},
                    pitch_type_analysis={},
                    error=error_msg
                )
        
        # 各種分析を実行
        try:
            inning_analysis = self.analyzer.analyze_by_inning(pitch_data)
            pitch_type_analysis = self.analyzer.analyze_by_pitch_type(pitch_data)
            batted_ball_analysis = self.analyzer.analyze_batted_balls(pitch_data)
            performance_summary = self.analyzer.get_performance_summary(pitch_data)
            
            # 分析結果を作成
            result = AnalysisResult(
                pitcher_id=pitcher_id,
                pitcher_name=pitcher.name,
                game_date=game_date,
                inning_analysis=inning_analysis,
                pitch_type_analysis=pitch_type_analysis,
                batted_ball_analysis=batted_ball_analysis,
                performance_summary=performance_summary
            )
            
            self.logger.info(f"分析が正常に完了しました")
            return result
            
        except Exception as e:
            error_msg = f"データ分析中にエラーが発生しました: {str(e)}"
            self.logger.error(error_msg)
            return AnalysisResult(
                pitcher_id=pitcher_id,
                pitcher_name=pitcher.name,
                game_date=game_date,
                inning_analysis={},
                pitch_type_analysis={},
                error=error_msg
            )