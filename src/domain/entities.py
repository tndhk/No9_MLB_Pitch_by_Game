"""
ドメイン層のエンティティと値オブジェクト
"""
from dataclasses import dataclass
from typing import Tuple, List, Optional


@dataclass
class Pitcher:
    """投手エンティティ"""
    id: str
    name: str
    team: Optional[str] = None
    throws: Optional[str] = None  # 'R' or 'L'


@dataclass
class Game:
    """試合エンティティ"""
    date: str
    pitcher_id: str
    game_pk: Optional[int] = None  # ← ★追加
    opponent: Optional[str] = None
    stadium: Optional[str] = None
    home_away: Optional[str] = None



@dataclass
class Pitch:
    """投球値オブジェクト"""
    pitch_type: str
    velocity: float
    spin_rate: Optional[float] = None
    result: Optional[str] = None
    coordinates: Optional[Tuple[float, float]] = None
    inning: Optional[int] = None
    pitch_number: Optional[int] = None


@dataclass
class PitchingPerformance:
    """投球パフォーマンスの集計値オブジェクト"""
    pitch_count: int
    strike_count: int
    ball_count: int
    swing_count: int
    whiff_count: int
    foul_count: int
    hit_count: int
    average_velocity: float
    max_velocity: float


@dataclass
class BattedBallResult:
    """打球結果値オブジェクト"""
    exit_velocity: Optional[float]
    launch_angle: Optional[float]
    distance: Optional[float]
    hit_type: str  # 'fly', 'grounder', 'liner', etc.
    hit_result: str  # 'single', 'double', 'triple', 'home_run', 'out', etc.
    coordinates: Optional[Tuple[float, float]] = None