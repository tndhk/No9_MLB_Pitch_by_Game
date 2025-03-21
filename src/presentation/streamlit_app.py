"""
Streamlitアプリケーションのメインクラス
"""
import streamlit as st
import pandas as pd
import logging
from typing import Optional, Tuple, List, Dict, Any
import matplotlib.pyplot as plt
import time

from src.application.usecases import PitcherGameAnalysisUseCase
from src.presentation.data_visualizer import DataVisualizer
from src.application.analysis_result import AnalysisResult
from src.domain.entities import Pitcher, Game


class StreamlitApp:
    """Streamlitアプリケーションのメインクラス"""
    
    def __init__(self, use_case: PitcherGameAnalysisUseCase, visualizer: DataVisualizer):
        """
        Parameters:
        -----------
        use_case : PitcherGameAnalysisUseCase
            投手分析ユースケース
        visualizer : DataVisualizer
            データ可視化ツール
        """
        self.use_case = use_case
        self.visualizer = visualizer
        self.logger = logging.getLogger(__name__)
    
    def run(self) -> None:
        """アプリケーションの実行"""
        self.logger.info("アプリケーションを起動します")
        
        # アプリケーションのタイトル設定
        st.set_page_config(
            page_title="MLB投手1試合分析ツール",
            page_icon="⚾",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.title("MLB投手1試合分析ツール")
        st.markdown("---")
        
        # サイドバーに検索インターフェースを配置
        pitcher_id, game_date = self.render_search_interface()
        
        # 投手と試合が選択されていれば分析を実行
        if pitcher_id and game_date:
            with st.spinner('分析を実行中...'):
                # 分析の実行
                result = self.use_case.analyze_game(pitcher_id, game_date)
                
                # 結果の表示
                self.render_results(result)
    
    def render_search_interface(self) -> Tuple[Optional[str], Optional[str]]:
        """
        検索インターフェースの表示
        
        Returns:
        --------
        Tuple[Optional[str], Optional[str]]
            選択された投手IDと試合日のタプル
        """
        st.sidebar.header("投手・試合選択")
        
        # セッション状態の初期化
        # 修正後 - 新しいセッション変数を追加
        if 'pitcher_search_history' not in st.session_state:
            st.session_state.pitcher_search_history = []
        if 'selected_pitcher' not in st.session_state:
            st.session_state.selected_pitcher = None
        if 'selected_pitcher_id' not in st.session_state:  # 追加
            st.session_state.selected_pitcher_id = None    # 追加
        if 'selected_season' not in st.session_state:      # 追加
            st.session_state.selected_season = None        # 追加
        if 'pitcher_games' not in st.session_state:
            st.session_state.pitcher_games = []
        if 'selected_game' not in st.session_state:
            st.session_state.selected_game = None
        if 'need_load_games' not in st.session_state:      # 追加：試合データ読み込みフラグ
            st.session_state.need_load_games = False       # 追加
        if 'search_results' not in st.session_state:       # 追加：検索結果の保存
            st.session_state.search_results = []           # 追加
                
        # 投手検索フォーム
        with st.sidebar.form("pitcher_search_form"):
            pitcher_name = st.text_input("投手名を入力", help="投手名の一部を入力してください（例: Ohtani, Cole など）")
            season = st.selectbox("シーズン", [2024, 2023, 2022, 2021, 2020, 2019], index=1)
            search_submitted = st.form_submit_button("検索")
        
        # 検索履歴の表示（最大5件）
        if st.session_state.pitcher_search_history:
            st.sidebar.markdown("### 検索履歴")
            # 修正後 - 履歴ボタンにもユニークキーとフラグ設定
            for pitcher in st.session_state.pitcher_search_history[-5:]:
                history_key = f"history_{pitcher.id}_{int(time.time())}"
                if st.sidebar.button(f"{pitcher.name}", key=history_key):
                    st.session_state.selected_pitcher = pitcher
                    st.session_state.selected_pitcher_id = pitcher.id
                    st.session_state.selected_season = season
                    st.session_state.need_load_games = True
                    st.experimental_rerun()  # 画面を再描画
        
        # 検索が実行された場合
        if search_submitted and pitcher_name:
            self.logger.info(f"投手名「{pitcher_name}」で検索を実行")
            
            # 検索中メッセージを表示
            search_status = st.sidebar.empty()
            search_status.info("投手を検索中...")
            
            try:
                # 投手検索
                pitchers = self.use_case.search_pitchers(pitcher_name)
                
                if not pitchers:
                    search_status.error(f"「{pitcher_name}」に一致する投手が見つかりませんでした")
                else:
                    # 検索結果の表示
                    search_status.success(f"{len(pitchers)}人の投手が見つかりました")
                    
                    # 修正後 - ユニークなキーとデータ読み込みのフラグ設定
                    # 検索結果をセッション状態に保存
                    st.session_state.search_results = pitchers

                    st.sidebar.markdown("### 検索結果")

                    # 検索結果ごとにキーを生成（タイムスタンプ付きで毎回異なるキーを使用）
                    for i, pitcher in enumerate(pitchers):
                        button_key = f"search_{pitcher.id}_{int(time.time())}"
                        if st.sidebar.button(f"{pitcher.name}", key=button_key):
                            st.session_state.selected_pitcher = pitcher
                            st.session_state.selected_pitcher_id = pitcher.id  # 追加
                            st.session_state.selected_season = season          # 追加
                            
                            # 重複を避けて検索履歴に追加
                            if pitcher not in st.session_state.pitcher_search_history:
                                st.session_state.pitcher_search_history.append(pitcher)
                            
                            # 試合データ取得のフラグを設定（直接取得せずフラグだけ設定）
                            st.session_state.need_load_games = True
                            st.experimental_rerun()  # 画面を再描画（重要な追加）
            except Exception as e:
                search_status.error(f"検索中にエラーが発生しました: {str(e)}")
        
            # 修正後 - 試合データ読み込みのトリガー追加
            # 選択された投手の表示
            if st.session_state.selected_pitcher:
                pitcher = st.session_state.selected_pitcher
                st.sidebar.markdown(f"### 選択中: {pitcher.name}")
                
                # 試合データの取得が必要な場合（新しく追加したコード）
                if st.session_state.need_load_games:
                    self._load_pitcher_games(st.session_state.selected_pitcher_id, st.session_state.selected_season)
                    st.session_state.need_load_games = False
                
                # 試合選択インターフェース
                if st.session_state.pitcher_games:
                    st.sidebar.markdown("### 試合選択")
                
                games = st.session_state.pitcher_games
                game_options = [f"{game.date} vs {game.opponent or '不明'}" for game in games]
                
                # デフォルト選択
                default_index = 0 if st.session_state.selected_game is None else \
                                next((i for i, g in enumerate(games) if g.date == st.session_state.selected_game.date), 0)
                
                selected_game_idx = st.sidebar.selectbox(
                    "試合を選択", 
                    range(len(game_options)),
                    format_func=lambda i: game_options[i],
                    index=default_index
                )
                
                st.session_state.selected_game = games[selected_game_idx]
            else:
                st.sidebar.warning(f"{season}シーズンの試合データがありません")
                st.session_state.selected_game = None
        
        # 選択された投手IDと試合日を返す
        pitcher_id = st.session_state.selected_pitcher.id if st.session_state.selected_pitcher else None
        game_date = st.session_state.selected_game.date if st.session_state.selected_game else None
        
        return pitcher_id, game_date
    
    def render_results(self, result: AnalysisResult) -> None:
        """
        分析結果の表示
        
        Parameters:
        -----------
        result : AnalysisResult
            分析結果
        """
        # エラーがある場合は表示して終了
        if result.error:
            st.error(f"分析エラー: {result.error}")
            return
        
        # ヘッダー情報の表示
        st.header(f"{result.pitcher_name} - {result.game_date}の投球分析")
        
        # タブで分析結果を分類
        tab1, tab2, tab3, tab4 = st.tabs(["概要", "イニング分析", "球種分析", "被打球分析"])
        
        # タブ1: 概要
        with tab1:
            self._render_summary_tab(result)
        
        # タブ2: イニング分析
        with tab2:
            self._render_inning_analysis_tab(result.inning_analysis)
        
        # タブ3: 球種分析
        with tab3:
            self._render_pitch_type_analysis_tab(result.pitch_type_analysis)
        
        # タブ4: 被打球分析
        with tab4:
            self._render_batted_ball_analysis_tab(result.batted_ball_analysis)
    
    def _render_summary_tab(self, result: AnalysisResult) -> None:
        """
        概要タブの表示
        
        Parameters:
        -----------
        result : AnalysisResult
            分析結果
        """
        # 2列レイアウト
        col1, col2 = st.columns(2)
        
        # 投球サマリー
        with col1:
            st.subheader("投球サマリー")
            
            if result.performance_summary:
                # 主要な数値を取得
                total_pitches = result.performance_summary.get('total_pitches', 0)
                innings_pitched = result.performance_summary.get('innings_pitched', 0)
                
                # 球速情報
                velocity_info = result.performance_summary.get('velocity', {})
                avg_velo = velocity_info.get('average', 0)
                max_velo = velocity_info.get('max', 0)
                
                # 結果情報
                outcomes = result.performance_summary.get('outcomes', {})
                strike_pct = outcomes.get('strike_percentage', 0)
                swing_miss_pct = outcomes.get('swinging_strikes', 0) / total_pitches * 100 if total_pitches > 0 else 0
                
                # メトリクス表示
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                metrics_col1.metric("総投球数", f"{total_pitches}球")
                metrics_col2.metric("イニング", f"{innings_pitched}")
                metrics_col3.metric("打者数", f"{result.performance_summary.get('batters_faced', 0)}人")
                
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                metrics_col1.metric("平均球速", f"{avg_velo:.1f} mph")
                metrics_col2.metric("最高球速", f"{max_velo:.1f} mph")
                metrics_col3.metric("ストライク率", f"{strike_pct:.1f}%")
                
                # パフォーマンスサマリーグラフ
                summary_fig = self.visualizer.create_performance_summary_chart(result.performance_summary)
                st.pyplot(summary_fig)
            else:
                st.info("パフォーマンスサマリーデータがありません")
        
        # 球種分布
        with col2:
            st.subheader("球種分布")
            
            if result.pitch_type_analysis and 'usage' in result.pitch_type_analysis:
                # 球種使用率グラフ
                pitch_type_fig = self.visualizer.create_pitch_type_chart(result.pitch_type_analysis)
                st.pyplot(pitch_type_fig)
                
                # 球種効果グラフ
                effectiveness_fig = self.visualizer.create_pitch_effectiveness_chart(result.pitch_type_analysis)
                st.pyplot(effectiveness_fig)
            else:
                st.info("球種分析データがありません")
    
    def _render_inning_analysis_tab(self, inning_analysis: Dict[str, Any]) -> None:
        """
        イニング分析タブの表示
        
        Parameters:
        -----------
        inning_analysis : Dict[str, Any]
            イニング別分析結果
        """
        if not inning_analysis or 'error' in inning_analysis:
            st.info("イニング分析データがありません")
            return
        
        st.subheader("イニング別分析")
        
        # 2列レイアウト
        col1, col2 = st.columns(2)
        
        # 球速推移グラフ
        with col1:
            st.markdown("#### 球速推移")
            velocity_fig = self.visualizer.create_velocity_chart(inning_analysis)
            st.pyplot(velocity_fig)
        
        # 投球数グラフ
        with col2:
            st.markdown("#### 投球数")
            pitch_count_fig = self.visualizer.create_pitch_distribution_chart(inning_analysis)
            st.pyplot(pitch_count_fig)
        
        # イニング別詳細データ
        st.markdown("#### イニング別詳細")
        
        if 'innings' in inning_analysis and inning_analysis['innings']:
            # データフレームの作成
            innings = sorted(inning_analysis['innings'])
            
            data = []
            for inning in innings:
                inning_str = str(inning)
                
                # 各イニングのデータを収集
                row = {'イニング': inning}
                
                # 投球数
                if 'pitch_count' in inning_analysis and inning_str in inning_analysis['pitch_count']:
                    row['投球数'] = inning_analysis['pitch_count'][inning_str]
                
                # 球速
                if 'velocity' in inning_analysis and inning_str in inning_analysis['velocity']:
                    velo = inning_analysis['velocity'][inning_str]
                    row['平均球速'] = f"{velo['mean']:.1f} mph"
                    row['最高球速'] = f"{velo['max']:.1f} mph"
                
                # ストライク率
                if 'strike_percentage' in inning_analysis and inning_str in inning_analysis['strike_percentage']:
                    row['ストライク率'] = f"{inning_analysis['strike_percentage'][inning_str]:.1f}%"
                
                # 空振り率
                if 'whiff_percentage' in inning_analysis and inning_str in inning_analysis['whiff_percentage']:
                    row['空振り率'] = f"{inning_analysis['whiff_percentage'][inning_str]:.1f}%"
                
                data.append(row)
            
            # データフレーム表示
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("イニング別詳細データがありません")
        else:
            st.info("イニング別データがありません")
    
    def _render_pitch_type_analysis_tab(self, pitch_type_analysis: Dict[str, Any]) -> None:
        """
        球種分析タブの表示
        
        Parameters:
        -----------
        pitch_type_analysis : Dict[str, Any]
            球種別分析結果
        """
        if not pitch_type_analysis or 'error' in pitch_type_analysis:
            st.info("球種分析データがありません")
            return
        
        st.subheader("球種別分析")
        
        # 球種のデータがあるか確認
        if 'pitch_types' not in pitch_type_analysis or not pitch_type_analysis['pitch_types']:
            st.info("球種データがありません")
            return
        
        # 球種データの準備
        pitch_types = pitch_type_analysis['pitch_types']
        
        # 球種詳細データ
        st.markdown("#### 球種詳細データ")
        
        # データフレームの作成
        data = []
        for pt in pitch_types:
            row = {'球種': pt}
            
            # 使用率
            if 'usage' in pitch_type_analysis and pt in pitch_type_analysis['usage']:
                usage = pitch_type_analysis['usage'][pt]
                row['投球数'] = usage['count']
                row['使用率'] = f"{usage['percentage']:.1f}%"
            
            # 球速
            if 'velocity' in pitch_type_analysis and pt in pitch_type_analysis['velocity']:
                velo = pitch_type_analysis['velocity'][pt]
                row['平均球速'] = f"{velo['mean']:.1f} mph"
                row['最高球速'] = f"{velo['max']:.1f} mph"
            
            # 有効性
            if 'effectiveness' in pitch_type_analysis and pt in pitch_type_analysis['effectiveness']:
                effect = pitch_type_analysis['effectiveness'][pt]
                row['ストライク率'] = f"{effect['strike_percentage']:.1f}%"
                row['空振り率'] = f"{effect['swinging_strike_percentage']:.1f}%"
                row['被安打率'] = f"{effect['hit_percentage']:.1f}%"
            
            # ボールの動き
            if 'movement' in pitch_type_analysis and pt in pitch_type_analysis['movement']:
                move = pitch_type_analysis['movement'][pt]
                row['横の動き'] = f"{move['horizontal']:.1f} inch"
                row['縦の動き'] = f"{move['vertical']:.1f} inch"
            
            data.append(row)
        
        # データフレーム表示
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("球種詳細データがありません")
        
        # グラフ表示
        st.markdown("#### 球種使用率と効果")
        
        col1, col2 = st.columns(2)
        
        # 球種使用率グラフ
        with col1:
            pitch_type_fig = self.visualizer.create_pitch_type_chart(pitch_type_analysis)
            st.pyplot(pitch_type_fig)
        
        # 球種効果グラフ
        with col2:
            effectiveness_fig = self.visualizer.create_pitch_effectiveness_chart(pitch_type_analysis)
            st.pyplot(effectiveness_fig)
    
    def _render_batted_ball_analysis_tab(self, batted_ball_analysis: Optional[pd.DataFrame]) -> None:
        """
        被打球分析タブの表示
        
        Parameters:
        -----------
        batted_ball_analysis : Optional[pd.DataFrame]
            被打球分析結果
        """
        if batted_ball_analysis is None or batted_ball_analysis.empty:
            st.info("被打球データがありません")
            return
        
        st.subheader("被打球分析")
        
        # 被打球分布図
        st.markdown("#### 被打球分布")
        batted_ball_fig = self.visualizer.create_batted_ball_chart(batted_ball_analysis)
        st.pyplot(batted_ball_fig)
        
        # 被打球詳細データ
        st.markdown("#### 被打球詳細")
        
        # 表示するカラムを選択
        display_columns = []
        
        # 基本情報
        if 'pitch_type' in batted_ball_analysis.columns:
            display_columns.append('pitch_type')
        
        # 打球情報
        if 'launch_speed' in batted_ball_analysis.columns:
            display_columns.append('launch_speed')
        if 'launch_angle' in batted_ball_analysis.columns:
            display_columns.append('launch_angle')
        if 'hit_distance_sc' in batted_ball_analysis.columns:
            display_columns.append('hit_distance_sc')
        
        # 結果情報
        if 'hit_type' in batted_ball_analysis.columns:
            display_columns.append('hit_type')
        if 'hit_result' in batted_ball_analysis.columns:
            display_columns.append('hit_result')
        
        # イニング情報
        if 'inning' in batted_ball_analysis.columns:
            display_columns.append('inning')
        
        # カウント情報
        if 'balls' in batted_ball_analysis.columns and 'strikes' in batted_ball_analysis.columns:
            # カウント列を作成
            batted_ball_analysis['count'] = batted_ball_analysis.apply(
                lambda row: f"{int(row['balls'])}-{int(row['strikes'])}" if pd.notna(row['balls']) and pd.notna(row['strikes']) else "",
                axis=1
            )
            display_columns.append('count')
        
        # データフレーム表示
        if display_columns:
            st.dataframe(batted_ball_analysis[display_columns], use_container_width=True)
        else:
            st.info("被打球詳細データを表示できるカラムがありません")
        
        # 打球タイプや結果の集計
        st.markdown("#### 打球タイプと結果")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'hit_type' in batted_ball_analysis.columns:
                st.markdown("##### 打球タイプ")
                hit_type_counts = batted_ball_analysis['hit_type'].value_counts()
                st.bar_chart(hit_type_counts)
            else:
                st.info("打球タイプデータがありません")
        
        with col2:
            if 'hit_result' in batted_ball_analysis.columns:
                st.markdown("##### 打球結果")
                hit_result_counts = batted_ball_analysis['hit_result'].value_counts()
                st.bar_chart(hit_result_counts)
            else:
                st.info("打球結果データがありません")
    
    def _load_pitcher_games(self, pitcher_id: str, season: int) -> None:
        """
        投手の試合データを読み込む
        
        Parameters:
        -----------
        pitcher_id : str
            投手ID
        season : int
            シーズン年
        """
        # ステータスプレースホルダを作成
        status = st.sidebar.empty()
        status.info(f"{season}シーズンの試合データを取得中...")
        
        try:
            st.session_state.pitcher_games = self.use_case.get_pitcher_games(pitcher_id, season)
            
            if not st.session_state.pitcher_games:
                status.warning(f"{season}シーズンの試合データが見つかりませんでした")
            else:
                status.success(f"{len(st.session_state.pitcher_games)}試合分のデータを取得しました")
                # 最新の試合を選択
                st.session_state.selected_game = st.session_state.pitcher_games[0]
        except Exception as e:
            status.error(f"データ取得中にエラーが発生しました: {str(e)}")