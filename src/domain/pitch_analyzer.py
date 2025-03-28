class PitchAnalyzer:
    """投球データの分析を担当するクラス"""

    def analyze_by_inning(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        イニング別の分析を実行
        
        Parameters:
        -----------
        data : pd.DataFrame
            Baseball Savantから取得した投球データ
            
        Returns:
        --------
        Dict[str, Any]
            イニング別分析結果を含む辞書
            {
                'innings': [1, 2, 3, ...],
                'velocity': {
                    '1': {'mean': 95.2, 'max': 97.1, 'min': 93.4, 'std': 1.2},
                    '2': {...},
                    ...
                },
                'pitch_count': {'1': 15, '2': 12, ...},
                'strike_percentage': {'1': 63.4, '2': 58.3, ...},
                'whiff_percentage': {'1': 25.0, '2': 20.0, ...},
                'pitch_type_distribution': {'1': {'FF': 10, 'SL': 5, ...}, ...}
            }
        """
        if data.empty or 'inning' not in data.columns:
            return {'error': 'データが無効または必要なカラムがありません'}
        
        # イニング別にグループ化
        grouped = data.groupby('inning')
        
        # 結果を格納する辞書
        results = {
            'innings': [],
            'velocity': {},
            'pitch_count': {},
            'strike_percentage': {},
            'whiff_percentage': {},
            'pitch_type_distribution': {}
        }
        
        # 各イニングの分析
        for inning, group in grouped:
            results['innings'].append(int(inning))
            
            # 球速の分析
            if 'release_speed' in group.columns:
                results['velocity'][inning] = {
                    'mean': group['release_speed'].mean(),
                    'max': group['release_speed'].max(),
                    'min': group['release_speed'].min(),
                    'std': group['release_speed'].std()
                }
            
            # 投球数
            results['pitch_count'][inning] = len(group)
            
            # ストライク率
            if 'type' in group.columns:
                strikes = group[group['type'].isin(['S', 'X'])].shape[0]  # S=swinging, X=called strike
                results['strike_percentage'][inning] = strikes / len(group) * 100 if len(group) > 0 else 0
            
            # 空振り率
            if 'description' in group.columns:
                swings = group[group['description'].str.contains('swing', case=False, na=False)].shape[0]
                whiffs = group[group['description'].str.contains('swinging_strike', case=False, na=False)].shape[0]
                results['whiff_percentage'][inning] = whiffs / swings * 100 if swings > 0 else 0
            
            # 球種分布
            if 'pitch_type' in group.columns:
                pitch_types = group['pitch_type'].value_counts().to_dict()
                results['pitch_type_distribution'][inning] = pitch_types
        
        return results

    def analyze_by_pitch_type(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        球種別の分析を実行
        
        Parameters:
        -----------
        data : pd.DataFrame
            Baseball Savantから取得した投球データ
            
        Returns:
        --------
        Dict[str, Any]
            球種別分析結果を含む辞書
            {
                'pitch_types': ['FF', 'SL', 'CH', ...],
                'usage': {
                    'FF': {'count': 45, 'percentage': 56.3},
                    'SL': {...},
                    ...
                },
                'velocity': {...},
                'effectiveness': {
                    'FF': {'strike_percentage': 65.0, 'swinging_strike_percentage': 12.0, ...},
                    ...
                },
                'location': {...},
                'movement': {...}
            }
        """
        if data.empty or 'pitch_type' not in data.columns:
            return {'error': 'データが無効または必要なカラムがありません'}
        
        # 球種でグループ化
        grouped = data.groupby('pitch_type')
        
        # 結果を格納する辞書
        results = {
            'pitch_types': [],
            'usage': {},
            'velocity': {},
            'effectiveness': {},
            'location': {},
            'movement': {}
        }
        
        total_pitches = len(data)
        
        # 各球種の分析
        for pitch_type, group in grouped:
            # 球種が不明な場合はスキップ
            if pd.isna(pitch_type) or pitch_type == '':
                continue
                
            results['pitch_types'].append(pitch_type)
            
            # 使用率
            count = len(group)
            results['usage'][pitch_type] = {
                'count': count,
                'percentage': (count / total_pitches * 100) if total_pitches > 0 else 0
            }
            
            # 球速
            if 'release_speed' in group.columns:
                results['velocity'][pitch_type] = {
                    'mean': group['release_speed'].mean(),
                    'max': group['release_speed'].max(),
                    'min': group['release_speed'].min(),
                    'std': group['release_speed'].std()
                }
            
            # 有効性（結果ベース）
            if 'description' in group.columns:
                # ストライク（見逃し、空振り、ファウル）
                called_strikes = group[group['description'].str.contains('called_strike', case=False, na=False)].shape[0]
                swinging_strikes = group[group['description'].str.contains('swinging_strike', case=False, na=False)].shape[0]
                fouls = group[group['description'].str.contains('foul', case=False, na=False)].shape[0]
                
                # ボール
                balls = group[group['description'].str.contains('ball', case=False, na=False)].shape[0]
                
                # ヒット
                hits = group[group['description'].str.contains('hit', case=False, na=False)].shape[0]
                
                results['effectiveness'][pitch_type] = {
                    'strike_percentage': ((called_strikes + swinging_strikes + fouls) / count * 100) if count > 0 else 0,
                    'swinging_strike_percentage': (swinging_strikes / count * 100) if count > 0 else 0,
                    'ball_percentage': (balls / count * 100) if count > 0 else 0,
                    'hit_percentage': (hits / count * 100) if count > 0 else 0
                }
            
            # 投球位置
            if all(col in group.columns for col in ['plate_x', 'plate_z']):
                results['location'][pitch_type] = {
                    'mean_x': group['plate_x'].mean(),
                    'mean_z': group['plate_z'].mean(),
                    'std_x': group['plate_x'].std(),
                    'std_z': group['plate_z'].std()
                }
            
            # ボールの動き
            if all(col in group.columns for col in ['pfx_x', 'pfx_z']):
                results['movement'][pitch_type] = {
                    'horizontal': group['pfx_x'].mean(),
                    'vertical': group['pfx_z'].mean()
                }
        
        return results

    def analyze_batted_balls(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        被打球の分析を実行
        
        Parameters:
        -----------
        data : pd.DataFrame
            Baseball Savantから取得した投球データ
            
        Returns:
        --------
        pd.DataFrame
            被打球データを含むデータフレーム
            カラム: [pitch_type, launch_speed, launch_angle, hit_distance_sc, hit_type, hit_result, ...]
        """
        if data.empty:
            return pd.DataFrame()
        
        # 打球結果がある行のみを抽出
        is_batted_ball = data['description'].str.contains('hit', case=False, na=False)
        batted_balls = data[is_batted_ball].copy()
        
        if batted_balls.empty:
            return pd.DataFrame()
        
        # 必要なカラムが存在するか確認
        required_columns = ['launch_speed', 'launch_angle', 'hit_distance_sc', 
                           'hit_location', 'hc_x', 'hc_y']
        
        # 存在するカラムのみを処理
        for col in required_columns:
            if col not in batted_balls.columns:
                batted_balls[col] = np.nan
        
        # 打球の種類を追加（あれば）
        if 'bb_type' in batted_balls.columns:
            batted_balls['hit_type'] = batted_balls['bb_type']
        else:
            # 簡易的な打球分類（launch_angleに基づく）
            batted_balls['hit_type'] = batted_balls['launch_angle'].apply(
                lambda angle: 'ground_ball' if pd.notna(angle) and angle < 10 else 
                             ('line_drive' if pd.notna(angle) and angle < 25 else 
                             ('fly_ball' if pd.notna(angle) and angle < 50 else 'pop_up'))
            )
        
        # 打球結果を追加
        if 'events' in batted_balls.columns:
            batted_balls['hit_result'] = batted_balls['events']
        else:
            batted_balls['hit_result'] = 'unknown'
        
        return batted_balls

    def get_performance_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        全体パフォーマンスのサマリーを作成
        
        Parameters:
        -----------
        data : pd.DataFrame
            Baseball Savantから取得した投球データ
            
        Returns:
        --------
        Dict[str, Any]
            パフォーマンスサマリーを含む辞書
            {
                'total_pitches': 80,
                'pitch_type_counts': {'FF': 45, 'SL': 25, ...},
                'velocity': {'average': 94.2, 'max': 97.1, 'min': 92.3, 'std': 1.4},
                'outcomes': {'called_strikes': 20, 'swinging_strikes': 15, ...},
                'innings_pitched': 6,
                'batters_faced': 24
            }
        """
        if data.empty:
            return {'error': 'データがありません'}
        
        summary = {
            'total_pitches': len(data),
            'pitch_type_counts': {},
            'velocity': {},
            'outcomes': {},
            'innings_pitched': 0,
            'batters_faced': 0
        }
        
        # 球種別集計
        if 'pitch_type' in data.columns:
            summary['pitch_type_counts'] = data['pitch_type'].value_counts().to_dict()
        
        # 球速統計
        if 'release_speed' in data.columns:
            speed_stats = data['release_speed'].describe()
            summary['velocity'] = {
                'average': speed_stats['mean'],
                'max': speed_stats['max'],
                'min': speed_stats['min'],
                'std': speed_stats['std']
            }
        
        # 結果の集計
        if 'description' in data.columns:
            # 各種結果のカウント
            called_strikes = data[data['description'].str.contains('called_strike', case=False, na=False)].shape[0]
            swinging_strikes = data[data['description'].str.contains('swinging_strike', case=False, na=False)].shape[0]
            fouls = data[data['description'].str.contains('foul', case=False, na=False)].shape[0]
            balls = data[data['description'].str.contains('ball', case=False, na=False)].shape[0]
            hits = data[data['description'].str.contains('hit', case=False, na=False)].shape[0]
            
            summary['outcomes'] = {
                'called_strikes': called_strikes,
                'swinging_strikes': swinging_strikes,
                'fouls': fouls,
                'balls': balls,
                'hits': hits,
                'strike_percentage': ((called_strikes + swinging_strikes + fouls) / len(data) * 100) if len(data) > 0 else 0,
                'ball_percentage': (balls / len(data) * 100) if len(data) > 0 else 0
            }
        
        # 投球イニング数
        if 'inning' in data.columns:
            summary['innings_pitched'] = data['inning'].max()
        
        # 対戦打者数
        if 'at_bat_number' in data.columns:
            summary['batters_faced'] = data['at_bat_number'].nunique()
        
        return summary