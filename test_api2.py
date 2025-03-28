import logging
import sys
import os
import pandas as pd

# ロギング設定
logging.basicConfig(level=logging.INFO)

# モジュールのパスを追加
sys.path.append('.')

from src.infrastructure.baseball_savant_client import BaseballSavantClient
from src.infrastructure.data_repository import DataRepository
from src.domain.pitch_analyzer import PitchAnalyzer
from src.application.usecases import PitcherGameAnalysisUseCase

# コンポーネントの初期化
client = BaseballSavantClient()
repository = DataRepository(cache_dir='./data', db_path='./data/db.sqlite')
analyzer = PitchAnalyzer()

# ユースケースの初期化
usecase = PitcherGameAnalysisUseCase(client, repository, analyzer)

# 投手検索
pitchers = usecase.search_pitchers("Ohtani")
if pitchers:
    print(f"検索結果: {len(pitchers)}人の投手が見つかりました")
    for i, p in enumerate(pitchers):
        print(f"{i+1}. {p.name} (ID: {p.id})")
    
    # 大谷翔平選手のIDをテストに使用
    pitcher_id = pitchers[0].id
    
    # 試合一覧を取得
    games = usecase.get_pitcher_games(pitcher_id, 2023)
    print(f"\n2023年シーズンの試合: {len(games)}試合")
    for i, g in enumerate(games[:5]):  # 最初の5試合のみ表示
        print(f"{i+1}. {g.date} vs {g.opponent or '不明'}")
    
    if games:
        # 最初の試合の分析を実行
        game_date = games[0].date
        print(f"\n{game_date}の試合を分析します...")
        result = usecase.analyze_game(pitcher_id, game_date)
        
        if result.error:
            print(f"エラー: {result.error}")
        else:
            print("\n分析結果:")
            
            # パフォーマンスサマリーのデータを表示
            if result.performance_summary:
                print("\nパフォーマンスサマリー:")
                print(f"総投球数: {result.performance_summary.get('total_pitches')}球")
                
                if 'velocity' in result.performance_summary:
                    velocity = result.performance_summary['velocity']
                    print(f"平均球速: {velocity.get('average', 0):.1f} mph")
                    print(f"最高球速: {velocity.get('max', 0):.1f} mph")
                
                if 'outcomes' in result.performance_summary:
                    outcomes = result.performance_summary['outcomes']
                    print(f"ストライク率: {outcomes.get('strike_percentage', 0):.1f}%")