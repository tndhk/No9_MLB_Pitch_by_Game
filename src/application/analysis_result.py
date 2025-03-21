"""
分析結果を格納するクラス
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import pandas as pd


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
               self.performance_summary