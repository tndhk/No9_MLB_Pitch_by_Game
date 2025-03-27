"""
BaseballPlayerDatabaseクラスのテスト
"""
import pytest
from src.infrastructure.baseball_player_database import BaseballPlayerDatabase
from src.domain.entities import Pitcher


class TestBaseballPlayerDatabase:
    """BaseballPlayerDatabaseクラスのテスト"""
    
    def test_search_pitcher_exact_match(self):
        """完全一致検索のテスト"""
        db = BaseballPlayerDatabase()
        
        # 完全一致での検索
        results = db.search_pitcher("Shohei Ohtani")
        
        # 結果の検証
        assert len(results) == 1
        assert results[0].id == "660271"
        assert results[0].name == "Shohei Ohtani"
        assert results[0].team == "Los Angeles Dodgers"
    
    def test_search_pitcher_partial_match(self):
        """部分一致検索のテスト"""
        db = BaseballPlayerDatabase()
        
        # 部分一致での検索
        results = db.search_pitcher("Ohtani")
        
        # 結果の検証
        assert len(results) == 1
        assert results[0].name == "Shohei Ohtani"
    
    def test_search_pitcher_multiple_results(self):
        """複数結果検索のテスト"""
        db = BaseballPlayerDatabase()
        
        # 複数結果が返ることを確認
        results = db.search_pitcher("japan")
        
        # 結果の検証
        assert len(results) > 1
        # 日本人投手が含まれることを確認
        names = [p.name for p in results]
        assert "Shohei Ohtani" in names
        assert "Yu Darvish" in names
    
    def test_search_pitcher_no_results(self):
        """検索結果なしのテスト"""
        db = BaseballPlayerDatabase()
        
        # 存在しない名前での検索
        results = db.search_pitcher("NonExistentPitcher")
        
        # 結果の検証
        assert len(results) == 0
    
    def test_get_pitcher_by_id(self):
        """ID検索のテスト"""
        db = BaseballPlayerDatabase()
        
        # IDによる検索
        pitcher = db.get_pitcher_by_id("660271")
        
        # 結果の検証
        assert pitcher is not None
        assert pitcher.id == "660271"
        assert pitcher.name == "Shohei Ohtani"
        assert pitcher.team == "Los Angeles Dodgers"
    
    def test_get_pitcher_by_id_not_found(self):
        """ID検索結果なしのテスト"""
        db = BaseballPlayerDatabase()
        
        # 存在しないIDでの検索
        pitcher = db.get_pitcher_by_id("999999")
        
        # 結果の検証
        assert pitcher is None
    
    def test_japanese_pitcher_search(self):
        """日本人投手の検索テスト"""
        db = BaseballPlayerDatabase()
        
        # 五十音を含む名前検索
        results = db.search_pitcher("Imanaga")
        
        # 結果の検証
        assert len(results) == 1
        assert results[0].name == "Shota Imanaga"
        assert results[0].team == "Chicago Cubs"