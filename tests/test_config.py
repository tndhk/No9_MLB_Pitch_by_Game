"""
ConfigManagerクラスのテスト
"""
import os
import tempfile
import pytest
import yaml
from pathlib import Path

from src.config import ConfigManager, get_config


@pytest.fixture
def sample_config_file():
    """テスト用の設定ファイルを作成"""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.yml', delete=False) as f:
        yaml.dump({
            'app': {
                'name': 'テスト用アプリ',
                'debug': True
            },
            'logging': {
                'level': 'DEBUG'
            },
            'api': {
                'baseball_savant': {
                    'rate_limit': 5.0
                }
            }
        }, f)
        config_path = f.name
    
    yield config_path
    
    # テスト後にファイルを削除
    os.unlink(config_path)


class TestConfigManager:
    """ConfigManagerクラスのテスト"""
    
    def test_init_with_default_values(self):
        """デフォルト値での初期化テスト"""
        config = ConfigManager()
        
        # デフォルト値の検証
        assert config.get('app', 'name') == "MLB投手分析ツール"
        assert config.get('logging', 'level') == "INFO"
        assert config.get('api', 'baseball_savant', 'rate_limit') == 2.0
    
    def test_load_from_file(self, sample_config_file):
        """設定ファイルの読み込みテスト"""
        config = ConfigManager(sample_config_file)
        
        # ファイルから読み込んだ値の検証
        assert config.get('app', 'name') == "テスト用アプリ"
        assert config.get('app', 'debug') is True
        assert config.get('logging', 'level') == "DEBUG"
        assert config.get('api', 'baseball_savant', 'rate_limit') == 5.0
        
        # ファイルにない値はデフォルト値を使用
        assert config.get('storage', 'cache_dir') == "./data"
    
    def test_load_from_env(self, sample_config_file, monkeypatch):
        """環境変数からの設定読み込みテスト"""
        # 環境変数の設定
        monkeypatch.setenv('MLB_LOG_LEVEL', 'ERROR')
        monkeypatch.setenv('MLB_API_RATE_LIMIT', '10.0')
        monkeypatch.setenv('MLB_CACHE_DIR', '/tmp/test-cache')
        
        config = ConfigManager(sample_config_file)
        
        # 環境変数から上書きされた値の検証
        assert config.get('logging', 'level') == "ERROR"  # 環境変数が優先
        assert config.get('api', 'baseball_savant', 'rate_limit') == 10.0  # 環境変数が優先
        assert config.get('storage', 'cache_dir') == "/tmp/test-cache"  # 環境変数が優先
        
        # 環境変数で上書きされていない値は設定ファイルの値を使用
        assert config.get('app', 'name') == "テスト用アプリ"
    
    def test_get_with_default(self):
        """get()メソッドのデフォルト値テスト"""
        config = ConfigManager()
        
        # 存在しない設定のデフォルト値
        assert config.get('nonexistent', 'key', default='default_value') == 'default_value'
        assert config.get('app', 'nonexistent', default=123) == 123
    
    def test_get_all(self, sample_config_file):
        """get_all()メソッドのテスト"""
        config = ConfigManager(sample_config_file)
        all_config = config.get_all()
        
        # 全設定の取得を検証
        assert isinstance(all_config, dict)
        assert 'app' in all_config
        assert 'logging' in all_config
        assert 'api' in all_config
        
        # 元の設定が変更されないことを確認
        all_config['app']['name'] = 'Modified'
        assert config.get('app', 'name') == "テスト用アプリ"  # 変更されない


class TestGetConfig:
    """get_config()関数のテスト"""
    
    def test_singleton(self, sample_config_file):
        """シングルトンパターンのテスト"""
        # 最初の呼び出し
        config1 = get_config(sample_config_file)
        
        # 2回目の呼び出し（同じインスタンスを返す）
        config2 = get_config()
        
        # 同じインスタンスであることを検証
        assert config1 is config2
        
        # 設定値も同じであることを検証
        assert config1.get('app', 'name') == "テスト用アプリ"
        assert config2.get('app', 'name') == "テスト用アプリ"