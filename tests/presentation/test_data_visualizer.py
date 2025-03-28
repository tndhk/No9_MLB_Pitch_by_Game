class TestDataVisualizer:
    """DataVisualizerクラスのテスト"""
    
    @pytest.fixture
    def visualizer(self):
        """DataVisualizerのインスタンスを提供するフィクスチャ"""
        return DataVisualizer()
    
    @pytest.fixture
    def sample_inning_data(self):
        """イニング分析データのサンプル"""
        return {
            'innings': [1, 2, 3],
            'velocity': {
                '1': {'mean': 95.0, 'max': 97.0, 'min': 93.0, 'std': 1.0},
                '2': {'mean': 94.5, 'max': 96.5, 'min': 92.5, 'std': 1.2},
                '3': {'mean': 94.0, 'max': 96.0, 'min': 92.0, 'std': 1.1}
            },
            'pitch_count': {
                '1': 15,
                '2': 18,
                '3': 12
            },
            'strike_percentage': {
                '1': 60.0,
                '2': 65.0,
                '3': 58.0
            }
        }
    
    @pytest.fixture
    def sample_pitch_type_data(self):
        """球種分析データのサンプル"""
        return {
            'pitch_types': ['FF', 'SL', 'CH'],
            'usage': {
                'FF': {'count': 25, 'percentage': 55.6},
                'SL': {'count': 15, 'percentage': 33.3},
                'CH': {'count': 5, 'percentage': 11.1}
            },
            'velocity': {
                'FF': {'mean': 95.0, 'max': 97.0, 'min': 93.0, 'std': 1.0},
                'SL': {'mean': 88.0, 'max': 90.0, 'min': 86.0, 'std': 1.2},
                'CH': {'mean': 85.0, 'max': 87.0, 'min': 83.0, 'std': 1.1}
            },
            'effectiveness': {
                'FF': {'strike_percentage': 65.0, 'swinging_strike_percentage': 12.0, 'hit_percentage': 8.0},
                'SL': {'strike_percentage': 70.0, 'swinging_strike_percentage': 18.0, 'hit_percentage': 5.0},
                'CH': {'strike_percentage': 60.0, 'swinging_strike_percentage': 15.0, 'hit_percentage': 10.0}
            }
        }
    
    @pytest.fixture
    def sample_batted_ball_data(self):
        """被打球データのサンプル"""
        return pd.DataFrame({
            'pitch_type': ['FF', 'SL', 'FF'],
            'launch_speed': [95.2, 88.4, 102.7],
            'launch_angle': [25.3, 12.8, 32.5],
            'hit_distance_sc': [350, 220, 410],
            'hit_type': ['fly_ball', 'ground_ball', 'fly_ball'],
            'hit_result': ['single', 'out', 'home_run'],
            'hc_x': [120, 80, 150],
            'hc_y': [180, 120, 210]
        })
    
    @pytest.fixture
    def sample_performance_summary(self):
        """パフォーマンスサマリーデータのサンプル"""
        return {
            'total_pitches': 45,
            'pitch_type_counts': {
                'FF': 25,
                'SL': 15,
                'CH': 5
            },
            'velocity': {
                'average': 93.5,
                'max': 97.0,
                'min': 83.0,
                'std': 3.5
            },
            'outcomes': {
                'called_strikes': 15,
                'swinging_strikes': 10,
                'fouls': 8,
                'balls': 9,
                'hits': 3,
                'strike_percentage': 73.3,
                'ball_percentage': 20.0
            },
            'innings_pitched': 6,
            'batters_faced': 18
        }
    
    def test_create_velocity_chart(self, visualizer, sample_inning_data):
        """球速チャート生成のテスト"""
        fig = visualizer.create_velocity_chart(sample_inning_data)
        assert isinstance(fig, plt.Figure)
    
    def test_create_pitch_distribution_chart(self, visualizer, sample_inning_data):
        """投球分布チャート生成のテスト"""
        fig = visualizer.create_pitch_distribution_chart(sample_inning_data)
        assert isinstance(fig, plt.Figure)
    
    def test_create_pitch_type_chart(self, visualizer, sample_pitch_type_data):
        """球種使用率チャート生成のテスト"""
        fig = visualizer.create_pitch_type_chart(sample_pitch_type_data)
        assert isinstance(fig, plt.Figure)
    
    def test_create_pitch_effectiveness_chart(self, visualizer, sample_pitch_type_data):
        """球種有効性チャート生成のテスト"""
        fig = visualizer.create_pitch_effectiveness_chart(sample_pitch_type_data)
        assert isinstance(fig, plt.Figure)
    
    def test_create_batted_ball_chart(self, visualizer, sample_batted_ball_data):
        """被打球チャート生成のテスト"""
        fig = visualizer.create_batted_ball_chart(sample_batted_ball_data)
        assert isinstance(fig, plt.Figure)
    
    def test_create_performance_summary_chart(self, visualizer, sample_performance_summary):
        """パフォーマンスサマリーチャート生成のテスト"""
        fig = visualizer.create_performance_summary_chart(sample_performance_summary)
        assert isinstance(fig, plt.Figure)
    
    def test_figure_to_base64(self, visualizer):
        """図のBase64変換テスト"""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])
        
        base64_str = visualizer.figure_to_base64(fig)
        
        assert isinstance(base64_str, str)
        assert base64_str.startswith("iVBORw0")  # Base64エンコードされた画像の一般的な開始文字