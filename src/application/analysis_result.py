"""
分析結果を格納するデータクラス
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
import pandas as pd
import logging

# 球種名変換用のユーティリティ関数のインポート
from src.domain.pitch_utils import translate_pitch_types_in_data, translate_pitch_types_in_dataframe


@dataclass
class AnalysisResult:
    """分析結果を格納するクラス"""
    
    # 基本情報
    pitcher_id: str
    pitcher_name: str
    game_date: str
    
    # イニング別分析
    inning_analysis: Dict[str, Any]
    
    # 球種別分析
    pitch_type_analysis: Dict[str, Any]
    
    # 被打球分析
    batted_ball_analysis: Optional[pd.DataFrame] = None
    
    # 全体パフォーマンスサマリー
    performance_summary: Dict[str, Any] = None
    
    # エラー情報
    error: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """有効な分析結果かどうか"""
        return self.error is None and \
               self.inning_analysis and \
               self.pitch_type_analysis and \
               self.performance_summary is not None
    
    def ensure_pitch_types_translated(self):
        """
        球種名が日本語に変換されていることを確認
        すでに変換済みでも安全に実行できます
        """
        logger = logging.getLogger(__name__)
        
        # イニング別分析
        if self.inning_analysis:
            self.inning_analysis = translate_pitch_types_in_data(self.inning_analysis)
            logger.debug("イニング別分析の球種名を変換")
        
        # 球種別分析
        if self.pitch_type_analysis:
            self.pitch_type_analysis = translate_pitch_types_in_data(self.pitch_type_analysis)
            logger.debug("球種別分析の球種名を変換")
        
        # 被打球分析
        if self.batted_ball_analysis is not None and not self.batted_ball_analysis.empty:
            self.batted_ball_analysis = translate_pitch_types_in_dataframe(self.batted_ball_analysis)
            logger.debug("被打球分析の球種名を変換")
        
        # パフォーマンスサマリー
        if self.performance_summary:
            self.performance_summary = translate_pitch_types_in_data(self.performance_summary)
            logger.debug("パフォーマンスサマリーの球種名を変換")