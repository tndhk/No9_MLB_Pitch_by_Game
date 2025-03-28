@dataclass
class Pitcher:
    """投手エンティティ"""
    id: str  # MLB IDなど一意の識別子
    name: str  # 投手の名前
    team: Optional[str] = None  # 所属チーム（任意）
    throws: Optional[str] = None  # 投球腕（'R':右、'L':左）

@dataclass
class Game:
    """試合エンティティ"""
    date: str  # 試合日（YYYY-MM-DD形式）
    pitcher_id: str  # 投手ID
    opponent: Optional[str] = None  # 対戦相手チーム
    stadium: Optional[str] = None  # スタジアム
    home_away: Optional[str] = None  # ホーム/アウェイ

@dataclass
class Pitch:
    """投球値オブジェクト"""
    pitch_type: str  # 球種（FF:フォーシーム、SL:スライダーなど）
    velocity: float  # 球速（mph）
    spin_rate: Optional[float] = None  # 回転数（rpm）
    result: Optional[str] = None  # 結果（ストライク、ボールなど）
    coordinates: Optional[Tuple[float, float]] = None  # 座標(x,y)
    inning: Optional[int] = None  # イニング
    pitch_number: Optional[int] = None  # 投球番号

@dataclass
class PitchingPerformance:
    """投球パフォーマンスの集計値オブジェクト"""
    pitch_count: int  # 投球数
    strike_count: int  # ストライク数
    ball_count: int  # ボール数
    swing_count: int  # スイング数
    whiff_count: int  # 空振り数
    foul_count: int  # ファウル数
    hit_count: int  # 安打数
    average_velocity: float  # 平均球速
    max_velocity: float  # 最高球速

@dataclass
class BattedBallResult:
    """打球結果値オブジェクト"""
    exit_velocity: Optional[float]  # 打球速度
    launch_angle: Optional[float]  # 打球角度
    distance: Optional[float]  # 飛距離
    hit_type: str  # 打球種類（fly, grounder, linerなど）
    hit_result: str  # 結果（single, double, triple, home_run, outなど）
    coordinates: Optional[Tuple[float, float]] = None  # 着地座標