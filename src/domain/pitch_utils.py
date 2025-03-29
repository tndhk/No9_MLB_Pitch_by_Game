"""
投球データに関するユーティリティ関数を提供するモジュール
"""
from typing import Dict, Any, List, Optional
import pandas as pd


# 球種コードと日本語名のマッピング
PITCH_TYPE_MAPPING: Dict[str, str] = {
    'FF': 'フォーシーム',
    'FT': 'ツーシーム',
    'SI': 'シンカー',
    'FC': 'カッター',
    'SL': 'スライダー',
    'CH': 'チェンジアップ',
    'CU': 'カーブ',
    'KC': 'ナックルカーブ',
    'EP': 'エフェクティブ',
    'FS': 'スプリット',
    'KN': 'ナックル',
    'SC': 'スクリュー',
    'GY': 'ジャイロ',
    'ST': 'スイーパー',
    'FO': 'フォーク',
    'PO': 'ポイントフォーク',
    'IN': 'インフォーシング',
    'KC': 'キャッチャーズカーブ',
    # 必要に応じて他の球種も追加可能
}


def get_pitch_name_ja(pitch_code: str) -> str:
    """
    球種コードから日本語名を取得
    
    Parameters:
    -----------
    pitch_code : str
        球種コード（例: FF, SL, CH など）
        
    Returns:
    --------
    str
        日本語名（マッピングにない場合はコードをそのまま返す）
    """
    return PITCH_TYPE_MAPPING.get(pitch_code, pitch_code)


def translate_pitch_types_in_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析データ内の球種コードを日本語名に変換
    
    Parameters:
    -----------
    data : Dict[str, Any]
        球種分析データなどの辞書
        
    Returns:
    --------
    Dict[str, Any]
        球種コードが日本語名に変換されたデータ
    """
    if not data or not isinstance(data, dict):
        return data
    
    # 元のデータ構造を変更しないよう新しい辞書を作成
    result = {}
    
    # 各キーについて処理
    for key, value in data.items():
        # pitch_typesキーは球種のリスト
        if key == 'pitch_types' and isinstance(value, list):
            result[key] = [get_pitch_name_ja(pt) for pt in value]
        
        # usageなどの球種をキーとする辞書
        elif key in ['usage', 'velocity', 'effectiveness', 'location', 'movement', 'pitch_type_counts'] and isinstance(value, dict):
            result[key] = {}
            for pitch_code, data_value in value.items():
                pitch_name = get_pitch_name_ja(pitch_code)
                result[key][pitch_name] = data_value
        
        # イニング別の球種分布など、二重の辞書
        elif key == 'pitch_type_distribution' and isinstance(value, dict):
            result[key] = {}
            for inning, distribution in value.items():
                if isinstance(distribution, dict):
                    result[key][inning] = {}
                    for pitch_code, count in distribution.items():
                        pitch_name = get_pitch_name_ja(pitch_code)
                        result[key][inning][pitch_name] = count
                else:
                    result[key][inning] = distribution
        
        # その他の値はそのままコピー
        else:
            result[key] = value
    
    return result


def translate_pitch_types_in_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrameの'pitch_type'カラムの球種コードを日本語名に変換
    
    Parameters:
    -----------
    df : pd.DataFrame
        'pitch_type'カラムを含むDataFrame
        
    Returns:
    --------
    pd.DataFrame
        'pitch_type'カラムが日本語名に変換されたDataFrame
    """
    if df is None or df.empty or 'pitch_type' not in df.columns:
        return df
    
    # コピーを作成して元のデータを変更しない
    result = df.copy()
    
    # 'pitch_type'カラムを変換
    result['pitch_type'] = result['pitch_type'].apply(lambda x: get_pitch_name_ja(x) if pd.notna(x) else x)
    
    return result