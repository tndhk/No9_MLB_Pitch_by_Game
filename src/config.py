"""
設定ファイルを読み込むためのモジュール
"""
import os
import yaml
from typing import Dict, Any, Optional


def get_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    設定ファイルを読み込む
    
    Parameters:
    -----------
    config_path : Optional[str]
        設定ファイルのパス。Noneの場合はデフォルトのパスを使用
        
    Returns:
    --------
    Dict[str, Any]
        設定値の辞書
    """
    if config_path is None:
        # デフォルトの設定ファイルパス
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yml')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        # 設定ファイルが見つからない場合はデフォルト値を返す
        return {
            'app': {
                'name': 'MLB投手分析ツール',
                'version': '1.0.0',
                'debug': False
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'dir': 'logs'
            },
            'storage': {
                'cache_dir': './data',
                'db_path': './data/db.sqlite',
                'cache_expiry_days': 7
            },
            'api': {
                'mlb_stats': {
                    'base_url': 'https://statsapi.mlb.com/api/v1',
                    'timeout': 30
                }
            }
        } 