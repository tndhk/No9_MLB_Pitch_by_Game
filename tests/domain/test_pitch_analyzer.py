class TestPitchAnalyzer:
    """PitchAnalyzerクラスのテスト"""
    
    @pytest.fixture
    def sample_pitch_data(self):
        """テスト用の投球データを生成"""
        # テスト用のダミーデータを作成
        data = {
            'pitch_type': ['FF', 'SL', 'CH', 'FF', 'FF', 'SL', 'FF', 'CH'],
            'release_speed': [95.2, 88.4, 85.1, 94.8, 95.5, 87.9, 96.1, 84.7],
            'inning': [1, 1, 1, 2, 2, 3, 3, 3],
            'description': ['swinging_strike', 'ball', 'called_strike', 'foul', 'swinging_strike', 'hit_into_play', 'called_strike', 'swinging_strike'],
            'type': ['S', 'B', 'S', 'S', 'S', 'X', 'S', 'S'],
            'plate_x': [0.12, -0.54, 0.23, 0.05, -0.32, 0.78, 0.21, -0.15],
            'plate_z': [2.31, 1.87, 1.65, 2.45, 2.12, 1.98, 2.35, 1.72],
            'pfx_x': [3.2, -4.5, 8.7, 3.5, 3.1, -4.8, 3.3, 9.1],
            'pfx_z': [9.8, 2.3, 5.6, 10.1, 9.5, 2.1, 9.7, 6.2]
        }
        
        # DataFrameの作成
        df = pd.DataFrame(data)
        
        return df
    
    @pytest.fixture
    def sample_batted_ball_data(self):
        """テスト用の打球データを生成"""
        # テスト用のダミーデータを作成
        data = {
            'pitch_type': ['FF', 'SL', 'FF'],
            'description': ['hit_into_play', 'hit_into_play', 'hit_into_play'],
            'launch_speed': [95.2, 88.4, 102.7],
            'launch_angle': [25.3, 12.8, 32.5],
            'hit_distance_sc': [350, 220, 410],
            'hit_location': [7, 4, 9],
            'hc_x': [120, 80, 150],
            'hc_y': [180, 120, 210],
            'bb_type': ['fly_ball', 'ground_ball', 'fly_ball'],
            'events': ['single', 'out', 'home_run']
        }
        
        # DataFrameの作成
        df = pd.DataFrame(data)
        
        return df
    
    def test_analyze_by_inning(self, sample_pitch_data):
        """イニング別分析のテスト"""
        analyzer = PitchAnalyzer()
        result = analyzer.analyze_by_inning(sample_pitch_data)
        
        # 結果の検証
        assert 'innings' in result
        assert 'velocity' in result
        assert 'pitch_count' in result
        assert 'strike_percentage' in result
        
        # イニング数の検証
        assert set(result['innings']) == {1, 2, 3}
        
        # 各イニングの投球数
        assert result['pitch_count']['1'] == 3
        assert result['pitch_count']['2'] == 2
        assert result['pitch_count']['3'] == 3
        
        # 球速の検証（1イニング目）
        assert abs(result['velocity']['1']['mean'] - 89.56) < 0.1
    
    def test_analyze_by_pitch_type(self, sample_pitch_data):
        """球種別分析のテスト"""
        analyzer = PitchAnalyzer()
        result = analyzer.analyze_by_pitch_type(sample_pitch_data)
        
        # 結果の検証
        assert 'pitch_types' in result
        assert 'usage' in result
        assert 'velocity' in result
        assert 'effectiveness' in result
        
        # 球種の検証
        assert set(result['pitch_types']) == {'FF', 'SL', 'CH'}
        
        # 使用率の検証
        assert result['usage']['FF']['count'] == 4
        assert abs(result['usage']['FF']['percentage'] - 50.0) < 0.1
        
        # 球速の検証（FFの平均球速）
        assert abs(result['velocity']['FF']['mean'] - 95.4) < 0.1
    
    def test_analyze_batted_balls(self, sample_batted_ball_data):
        """被打球分析のテスト"""
        analyzer = PitchAnalyzer()
        result = analyzer.analyze_batted_balls(sample_batted_ball_data)
        
        # 結果の検証
        assert not result.empty
        assert len(result) == 3
        assert 'hit_type' in result.columns
        assert 'hit_result' in result.columns
    
    def test_get_performance_summary(self, sample_pitch_data):
        """パフォーマンスサマリーのテスト"""
        analyzer = PitchAnalyzer()
        result = analyzer.get_performance_summary(sample_pitch_data)
        
        # 結果の検証
        assert 'total_pitches' in result
        assert 'pitch_type_counts' in result
        assert 'velocity' in result
        assert 'outcomes' in result
        
        # 投球数の検証
        assert result['total_pitches'] == 8
        
        # 球種カウントの検証
        assert result['pitch_type_counts']['FF'] == 4
        assert result['pitch_type_counts']['SL'] == 2
        assert result['pitch_type_counts']['CH'] == 2
        
        # 球速の検証
        assert abs(result['velocity']['average'] - 90.96) < 0.1
        
        # 結果の検証
        assert result['outcomes']['called_strikes'] == 2
        assert result['outcomes']['swinging_strikes'] == 3