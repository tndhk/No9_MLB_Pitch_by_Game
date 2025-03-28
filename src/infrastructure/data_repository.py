"""
データの永続化とキャッシュを担当するリポジトリ
"""
import os
import sqlite3
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union

from src.domain.entities import Pitcher, Game


class DataRepository:
    """
    データの永続化とキャッシュを担当
    """
    
    def __init__(self, cache_dir: str = './data', db_path: str = './data/db.sqlite'):
        """
        Parameters:
        -----------
        cache_dir : str
            キャッシュディレクトリのパス
        db_path : str
            SQLiteデータベースファイルのパス
        """
        self.cache_dir = cache_dir
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # キャッシュディレクトリが存在しない場合は作成
        os.makedirs(cache_dir, exist_ok=True)
        
        # データベース接続の初期化
        self._init_db()
    
    def _init_db(self) -> None:
        """データベーススキーマの初期化"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 投手テーブルの作成
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS pitchers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                team TEXT,
                throws TEXT,
                updated_at TEXT
            )
            ''')
            
            # 試合テーブルの作成
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                pitcher_id TEXT NOT NULL,
                opponent TEXT,
                stadium TEXT,
                home_away TEXT,
                FOREIGN KEY (pitcher_id) REFERENCES pitchers (id)
            )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("データベーススキーマを初期化しました")
            
        except sqlite3.Error as e:
            self.logger.error(f"データベース初期化中にエラーが発生しました: {e}")
            raise
    
    def save_pitch_data(self, pitcher_id: str, game_date: str, data: pd.DataFrame) -> None:
        """
        投球データをキャッシュとして保存
        
        Parameters:
        -----------
        pitcher_id : str
            投手ID
        game_date : str
            試合日（YYYY-MM-DD形式）
        data : pd.DataFrame
            保存する投球データ
        """
        if data.empty:
            self.logger.warning("空のデータフレームは保存しません")
            return
        
        try:
            # キャッシュファイルパスの作成
            file_name = f"pitch_data_{pitcher_id}_{game_date}.pkl"
            file_path = os.path.join(self.cache_dir, file_name)
            
            # データを保存
            data.to_pickle(file_path)
            
            # メタデータの保存
            meta_file = f"pitch_data_{pitcher_id}_{game_date}.meta.json"
            meta_path = os.path.join(self.cache_dir, meta_file)
            
            meta_data = {
                'pitcher_id': pitcher_id,
                'game_date': game_date,
                'cached_at': datetime.now().isoformat(),
                'rows': len(data),
                'columns': list(data.columns)
            }
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"投球データをキャッシュに保存しました: {file_path}")
            
        except Exception as e:
            self.logger.error(f"投球データの保存中にエラーが発生しました: {e}")
            raise
    
    def get_cached_pitch_data(self, pitcher_id: str, game_date: str, max_age_days: int = 7) -> Optional[pd.DataFrame]:
        """
        キャッシュされた投球データを取得
        
        Parameters:
        -----------
        pitcher_id : str
            投手ID
        game_date : str
            試合日（YYYY-MM-DD形式）
        max_age_days : int
            キャッシュの最大有効期間（日数）
            
        Returns:
        --------
        Optional[pd.DataFrame]
            キャッシュされたデータ。キャッシュがない場合はNone
        """
        # キャッシュファイルパスの作成
        file_name = f"pitch_data_{pitcher_id}_{game_date}.pkl"
        file_path = os.path.join(self.cache_dir, file_name)
        
        # メタデータファイルパス
        meta_file = f"pitch_data_{pitcher_id}_{game_date}.meta.json"
        meta_path = os.path.join(self.cache_dir, meta_file)
        
        # ファイルが存在するか確認
        if not os.path.exists(file_path) or not os.path.exists(meta_path):
            self.logger.debug(f"キャッシュが見つかりませんでした: {file_path}")
            return None
        
        try:
            # メタデータを読み込み
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
            
            # キャッシュの有効期限をチェック
            cached_at = datetime.fromisoformat(meta_data['cached_at'])
            now = datetime.now()
            age = now - cached_at
            
            if age > timedelta(days=max_age_days):
                self.logger.debug(f"キャッシュが古すぎます（{age.days}日）: {file_path}")
                return None
            
            # データを読み込み
            data = pd.read_pickle(file_path)
            
            self.logger.info(f"キャッシュからデータを読み込みました: {file_path}")
            return data
            
        except Exception as e:
            self.logger.error(f"キャッシュデータの読み込み中にエラーが発生しました: {e}")
            return None
    
    def save_pitcher_info(self, pitcher: Pitcher) -> None:
        """
        投手情報をデータベースに保存
        
        Parameters:
        -----------
        pitcher : Pitcher
            保存する投手エンティティ
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 現在の日時
            now = datetime.now().isoformat()
            
            # 投手情報を挿入または更新
            cursor.execute('''
            INSERT OR REPLACE INTO pitchers (id, name, team, throws, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (pitcher.id, pitcher.name, pitcher.team, pitcher.throws, now))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"投手情報を保存しました: {pitcher.name} (ID: {pitcher.id})")
            
        except sqlite3.Error as e:
            self.logger.error(f"投手情報の保存中にエラーが発生しました: {e}")
            raise
    
    def get_pitcher_info(self, pitcher_id: str) -> Optional[Pitcher]:
        """
        投手情報をデータベースから取得
        
        Parameters:
        -----------
        pitcher_id : str
            投手ID
            
        Returns:
        --------
        Optional[Pitcher]
            投手エンティティ。見つからない場合はNone
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 投手情報を検索
            cursor.execute('''
            SELECT id, name, team, throws
            FROM pitchers
            WHERE id = ?
            ''', (pitcher_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row is None:
                self.logger.debug(f"投手ID {pitcher_id} は見つかりませんでした")
                return None
            
            # Pitcherエンティティを作成
            pitcher = Pitcher(
                id=row[0],
                name=row[1],
                team=row[2],
                throws=row[3]
            )
            
            self.logger.info(f"投手情報を取得しました: {pitcher.name} (ID: {pitcher.id})")
            return pitcher
            
        except sqlite3.Error as e:
            self.logger.error(f"投手情報の取得中にエラーが発生しました: {e}")
            return None
    
    def save_game_info(self, game: Game) -> None:
        """
        試合情報をデータベースに保存
        
        Parameters:
        -----------
        game : Game
            保存する試合エンティティ
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ゲームIDの生成 (pitcher_id + date)
            game_id = f"{game.pitcher_id}_{game.date}"
            
            # 試合情報を挿入または更新
            cursor.execute('''
            INSERT OR REPLACE INTO games (id, date, pitcher_id, opponent, stadium, home_away)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (game_id, game.date, game.pitcher_id, game.opponent, game.stadium, game.home_away))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"試合情報を保存しました: {game.date} (投手ID: {game.pitcher_id})")
            
        except sqlite3.Error as e:
            self.logger.error(f"試合情報の保存中にエラーが発生しました: {e}")
            raise
    
    def get_games_by_pitcher(self, pitcher_id: str) -> List[Game]:
        """
        投手IDに基づいて試合情報を取得
        
        Parameters:
        -----------
        pitcher_id : str
            投手ID
            
        Returns:
        --------
        List[Game]
            試合エンティティのリスト
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 試合情報を検索
            cursor.execute('''
            SELECT id, date, pitcher_id, opponent, stadium, home_away
            FROM games
            WHERE pitcher_id = ?
            ORDER BY date DESC
            ''', (pitcher_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            games = []
            for row in rows:
                game = Game(
                    date=row[1],
                    pitcher_id=row[2],
                    opponent=row[3],
                    stadium=row[4],
                    home_away=row[5]
                )
                games.append(game)
            
            self.logger.info(f"投手ID {pitcher_id} の{len(games)}試合分の情報を取得しました")
            return games
            
        except sqlite3.Error as e:
            self.logger.error(f"試合情報の取得中にエラーが発生しました: {e}")
            return []