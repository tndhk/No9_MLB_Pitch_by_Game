"""
アプリケーション設定の管理
環境変数とYAML設定ファイルを組み合わせて設定を提供する
"""
import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """
    アプリケーション設定の管理クラス
    環境変数とYAML設定ファイルを統合して設定を提供する
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Parameters:
        -----------
        config_path : Optional[str]
            設定ファイルのパス。Noneの場合はデフォルトのパスを使用
        """
        self.logger = logging.getLogger(__name__)
        
        # デフォルト設定
        self.config = {
            'app': {
                'name': "MLB投手分析ツール",
                'version': "1.0.0",
                'debug': False,
            },
            'logging': {
                'level': "INFO",
                'format': "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                'dir': "logs",
            },
            'storage': {
                'cache_dir': "./data",
                'db_path': "./data/db.sqlite",
                'cache_expiry_days': 7,
            },
            'api': {
                'baseball_savant': {
                    'base_url': "https://baseballsavant.mlb.com",
                    'search_url': "https://baseballsavant.mlb.com/player-search",
                    'stats_url': "https://baseballsavant.mlb.com/statcast_search/csv",
                    'player_url': "https://baseballsavant.mlb.com/savant-player",
                    'rate_limit': 2.0,
                    'max_retries': 3,
                    'timeout': 30,
                    'use_proxy': False,
                    'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                },
            },
        }
        
        # 設定ファイルのパス
        self.config_path = config_path or self._find_config_file()
        
        # 設定ファイルの読み込み
        self._load_config_file()
        
        # 環境変数から設定を上書き
        self._load_from_env()
        
        self.logger.debug("設定の初期化が完了しました")
    
    def _find_config_file(self) -> str:
        """
        設定ファイルのパスを探す
        
        Returns:
        --------
        str
            設定ファイルのパス
        """
        # 設定ファイルの候補パス
        paths = [
            Path("./config.yml"),
            Path("./config.yaml"),
            Path("./config/config.yml"),
            Path("./config/config.yaml"),
            Path("../config.yml"),
            Path("../config.yaml"),
        ]
        
        # 存在する最初のファイルを返す
        for path in paths:
            if path.exists():
                return str(path)
        
        # デフォルトパス
        return "./config.yml"
    
    def _load_config_file(self) -> None:
        """設定ファイルを読み込む"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f)
                
                if yaml_config:
                    # 設定をマージ
                    self._merge_config(self.config, yaml_config)
                    self.logger.info(f"設定ファイル {self.config_path} を読み込みました")
            else:
                self.logger.warning(f"設定ファイル {self.config_path} が見つかりませんでした。デフォルト設定を使用します")
        
        except Exception as e:
            self.logger.error(f"設定ファイルの読み込み中にエラーが発生しました: {e}")
    
    def _merge_config(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        2つの設定辞書を再帰的にマージする
        
        Parameters:
        -----------
        target : Dict[str, Any]
            マージ先の辞書
        source : Dict[str, Any]
            マージ元の辞書
        """
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                # 両方が辞書の場合は再帰的にマージ
                self._merge_config(target[key], value)
            else:
                # それ以外の場合は上書き
                target[key] = value
    
    def _load_from_env(self) -> None:
        """環境変数から設定を読み込む"""
        env_mappings = {
            'MLB_APP_DEBUG': ('app', 'debug', lambda x: x.lower() == 'true'),
            'MLB_LOG_LEVEL': ('logging', 'level', str),
            'MLB_LOG_DIR': ('logging', 'dir', str),
            'MLB_CACHE_DIR': ('storage', 'cache_dir', str),
            'MLB_DB_PATH': ('storage', 'db_path', str),
            'MLB_CACHE_EXPIRY_DAYS': ('storage', 'cache_expiry_days', int),
            'MLB_API_RATE_LIMIT': ('api', 'baseball_savant', 'rate_limit', float),
            'MLB_API_MAX_RETRIES': ('api', 'baseball_savant', 'max_retries', int),
            'MLB_API_TIMEOUT': ('api', 'baseball_savant', 'timeout', int),
            'MLB_API_USE_PROXY': ('api', 'baseball_savant', 'use_proxy', lambda x: x.lower() == 'true'),
            'MLB_API_USER_AGENT': ('api', 'baseball_savant', 'user_agent', str),
        }
        
        for env_name, config_path in env_mappings.items():
            env_value = os.environ.get(env_name)
            if env_value is not None:
                # 型変換関数
                converter = config_path[-1]
                # 設定パス
                keys = config_path[:-1] if callable(config_path[-1]) else config_path
                
                # 設定値を更新
                target = self.config
                for key in keys[:-1]:
                    target = target.setdefault(key, {})
                
                try:
                    target[keys[-1]] = converter(env_value)
                    self.logger.debug(f"環境変数 {env_name} から設定を上書きしました: {keys} = {target[keys[-1]]}")
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"環境変数 {env_name} の変換に失敗しました: {e}")
    
    def get(self, *keys, default=None) -> Any:
        """
        設定値を取得する
        
        Parameters:
        -----------
        *keys
            設定キーのパス
        default
            設定が存在しない場合のデフォルト値
            
        Returns:
        --------
        Any
            設定値
        """
        result = self.config
        try:
            for key in keys:
                result = result[key]
            return result
        except (KeyError, TypeError):
            return default

    def get_all(self) -> Dict[str, Any]:
        """
        すべての設定を取得する
        
        Returns:
        --------
        Dict[str, Any]
            すべての設定
        """
        return self.config.copy()


# シングルトンインスタンス
_config_instance = None


def get_config(config_path: Optional[str] = None) -> ConfigManager:
    """
    設定マネージャーのシングルトンインスタンスを取得
    
    Parameters:
    -----------
    config_path : Optional[str]
        設定ファイルのパス。Noneの場合はデフォルトのパスを使用
        
    Returns:
    --------
    ConfigManager
        設定マネージャーのインスタンス
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager(config_path)
    return _config_instance