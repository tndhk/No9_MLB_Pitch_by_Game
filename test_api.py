#!/usr/bin/env python3
"""
MLB StatsAPIとBaseball Savant APIの連携をテストするスクリプト
"""
import logging
import sys
import os

# パスの追加（パッケージとして実行していない場合でも動作するように）
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.infrastructure.mlb_stats_client import MLBStatsClient
from src.infrastructure.baseball_savant_client import BaseballSavantClient


def setup_logging():
    """ロギングの設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )


def test_mlb_stats_api():
    """MLB StatsAPIのテスト"""
    client = MLBStatsClient()
    
    print("\n===== MLB StatsAPI テスト =====")
    
    # 投手名の入力
    pitcher_name = input("検索する投手名を入力してください: ")
    
    # 投手検索
    pitchers = client.search_pitcher(pitcher_name)
    
    if not pitchers:
        print(f"投手名 '{pitcher_name}' に一致する投手が見つかりませんでした。")
        return
    
    # 検索結果の表示
    print(f"\n{len(pitchers)}人の投手が見つかりました：")
    for i, pitcher in enumerate(pitchers):
        print(f"{i+1}. {pitcher['name']} (ID: {pitcher['id']}, チーム: {pitcher['team_name']})")
    
    # 選択された投手の詳細情報を表示
    if len(pitchers) > 0:
        selection = 0
        if len(pitchers) > 1:
            selection = int(input(f"\n詳細を確認する投手の番号を入力してください (1-{len(pitchers)}): ")) - 1
        
        # 範囲チェック
        if selection < 0 or selection >= len(pitchers):
            print("無効な選択です。")
            return
        
        selected_pitcher = pitchers[selection]
        
        # 詳細情報の取得
        details = client.get_player_details(selected_pitcher['id'])
        
        print("\n===== 投手詳細情報 =====")
        print(f"名前: {details.get('fullName', '不明')}")
        print(f"ポジション: {details.get('primaryPosition', {}).get('name', '不明')}")
        print(f"チーム: {selected_pitcher['team_name']}")
        print(f"背番号: {details.get('primaryNumber', '不明')}")
        print(f"生年月日: {details.get('birthDate', '不明')}")
        print(f"投球腕: {details.get('pitchHand', {}).get('description', '不明')}")
        print(f"打席: {details.get('batSide', {}).get('description', '不明')}")
        if 'height' in details and 'weight' in details:
            print(f"身長/体重: {details['height']} / {details['weight']}lbs")
        
        return selected_pitcher


def test_baseball_savant_api(pitcher_id=None):
    """Baseball Savant APIのテスト"""
    client = BaseballSavantClient()
    
    print("\n===== Baseball Savant API テスト =====")
    
    # 投手IDの入力/検証
    if pitcher_id is None:
        pitcher_id = input("投手IDを入力してください: ")
    else:
        pitcher_id = str(pitcher_id)
        print(f"投手ID: {pitcher_id}")
    
    # シーズンの入力
    season = input("シーズンを入力してください (デフォルト: 2023): ") or "2023"
    
    # 試合リストの取得
    print(f"\n{season}シーズンの試合リストを取得中...")
    games = client.get_pitcher_games(pitcher_id, int(season))
    
    if not games:
        print(f"投手ID {pitcher_id}の{season}シーズンの試合が見つかりませんでした。")
        return
    
    # 試合リストの表示
    print(f"\n{len(games)}試合が見つかりました：")
    for i, game in enumerate(games[:10]):  # 最新の10試合のみ表示
        opponent_info = f"vs {game.opponent}" if game.opponent else ""
        stadium_info = f"at {game.stadium}" if game.stadium else ""
        print(f"{i+1}. {game.date} {opponent_info} {stadium_info}")
    
    # 選択された試合の詳細を取得
    if len(games) > 0:
        selection = 0
        if len(games) > 1:
            selection = int(input(f"\n詳細を確認する試合の番号を入力してください (1-{min(10, len(games))}): ")) - 1
        
        # 範囲チェック
        if selection < 0 or selection >= min(10, len(games)):
            print("無効な選択です。")
            return
        
        selected_game = games[selection]
        
        # 投球データの取得
        print(f"\n{selected_game.date}の投球データを取得中...")
        pitch_data = client.get_pitch_data(pitcher_id, selected_game.date, game_pk=selected_game.game_pk)
        
        if pitch_data is None or pitch_data.empty:
            print("投球データが見つかりませんでした。")
            return
        
        # データサマリー
        print(f"\n===== 投球データサマリー ({selected_game.date}) =====")
        print(f"投球数: {len(pitch_data)}")
        
        # 球種ごとの集計
        if 'pitch_type' in pitch_data.columns:
            pitch_type_counts = pitch_data['pitch_type'].value_counts()
            print("\n球種別投球数:")
            for pitch_type, count in pitch_type_counts.items():
                print(f"{pitch_type}: {count}球")
        
        # 球速統計
        if 'release_speed' in pitch_data.columns:
            speed_stats = pitch_data['release_speed'].describe()
            print("\n球速統計:")
            print(f"平均: {speed_stats['mean']:.1f} mph")
            print(f"最高: {speed_stats['max']:.1f} mph")
            print(f"最低: {speed_stats['min']:.1f} mph")
        
        # イニングごとの投球数
        if 'inning' in pitch_data.columns:
            inning_counts = pitch_data['inning'].value_counts().sort_index()
            print("\nイニング別投球数:")
            for inning, count in inning_counts.items():
                print(f"{inning}回: {count}球")
        
        # データの先頭行を表示
        print("\nデータサンプル (最初の5行):")
        print(pitch_data.head().to_string())


def main():
    """メイン関数"""
    setup_logging()
    
    while True:
        print("\n===== API連携テストメニュー =====")
        print("1. MLB StatsAPIテスト (投手検索)")
        print("2. Baseball Savant APIテスト (投球データ取得)")
        print("3. 連続テスト (1→2)")
        print("0. 終了")
        
        choice = input("\n選択してください (0-3): ")
        
        if choice == '0':
            break
        elif choice == '1':
            test_mlb_stats_api()
        elif choice == '2':
            test_baseball_savant_api()
        elif choice == '3':
            selected_pitcher = test_mlb_stats_api()
            if selected_pitcher:
                test_baseball_savant_api(selected_pitcher['id'])
        else:
            print("無効な選択です。再度入力してください。")
    
    print("テストを終了します。")


if __name__ == "__main__":
    main()