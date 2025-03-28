"""
シンプルな代替アプローチ：完全に書き直したStreamlitアプリ
"""
import streamlit as st
import pandas as pd
import time
import logging
from typing import Dict, Any, List, Optional

from src.domain.entities import Pitcher, Game
from src.application.usecases import PitcherGameAnalysisUseCase
from src.presentation.data_visualizer import DataVisualizer

class StreamlitApp:
    """簡素化されたStreamlitアプリケーションクラス"""
    
    def __init__(self, use_case: PitcherGameAnalysisUseCase, visualizer: DataVisualizer):
        self.use_case = use_case
        self.visualizer = visualizer
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """アプリケーションの実行"""
        self.logger.info("シンプルなアプリケーションを起動します")
        
        # アプリケーションの設定
        st.set_page_config(
            page_title="MLB投手分析ツール (シンプル版)",
            page_icon="⚾",
            layout="wide"
        )
        
        st.title("MLB投手試合分析ツール")
        st.markdown("---")
        
        # サイドバーに検索UI
        with st.sidebar:
            st.header("投手・試合選択")
            
            # 投手検索
            pitcher_name = st.text_input("投手名を入力", help="例: Ohtani, Cole, Imanaga など")
            season = st.selectbox("シーズン", [2024, 2023, 2022, 2021, 2020], index=1)
            
            if st.button("検索"):
                if pitcher_name:
                    with st.spinner("検索中..."):
                        try:
                            # 投手検索を実行
                            pitchers = self.use_case.search_pitchers(pitcher_name)
                            
                            if pitchers:
                                # 検索結果をセッション状態に保存
                                st.session_state['pitchers'] = pitchers
                                st.success(f"{len(pitchers)}人の投手が見つかりました")
                            else:
                                st.error(f"「{pitcher_name}」に一致する投手が見つかりませんでした")
                        except Exception as e:
                            st.error(f"検索エラー: {str(e)}")
                            self.logger.error(f"検索エラー: {str(e)}", exc_info=True)
                else:
                    st.warning("投手名を入力してください")
            
            # 検索結果がある場合、投手選択UIを表示
            if 'pitchers' in st.session_state and st.session_state['pitchers']:
                st.subheader("検索結果")
                
                # 投手選択用のラジオボタン
                pitcher_options = {f"{p.name} (ID: {p.id})": p for p in st.session_state['pitchers']}
                selected_pitcher_key = st.radio("投手を選択", list(pitcher_options.keys()))
                
                selected_pitcher = pitcher_options[selected_pitcher_key]
                
                if st.button(f"{selected_pitcher.name}の試合データを取得"):
                    with st.spinner(f"{season}シーズンの試合データを取得中..."):
                        try:
                            # 試合データを取得
                            games = self.use_case.get_pitcher_games(selected_pitcher.id, season)
                            
                            if games:
                                # 試合データをセッション状態に保存
                                st.session_state['selected_pitcher'] = selected_pitcher
                                st.session_state['games'] = games
                                st.success(f"{len(games)}試合のデータを取得しました")
                            else:
                                st.warning(f"{season}シーズンの試合データが見つかりませんでした")
                        except Exception as e:
                            st.error(f"データ取得エラー: {str(e)}")
                            self.logger.error(f"データ取得エラー: {str(e)}", exc_info=True)
            
            # 試合データがある場合、試合選択UIを表示
            if 'games' in st.session_state and st.session_state['games']:
                st.subheader("試合選択")
                
                # 試合選択用のセレクトボックス
                game_options = {f"{g.date} vs {g.opponent or '不明'}": g for g in st.session_state['games']}
                selected_game_key = st.selectbox("試合を選択", list(game_options.keys()))
                
                selected_game = game_options[selected_game_key]
                
                if st.button("分析を実行"):
                    # 選択した試合と投手をセッション状態に保存
                    st.session_state['selected_game'] = selected_game
                    st.session_state['analysis_requested'] = True
        
        # メインエリア：分析結果表示
        if 'analysis_requested' in st.session_state and st.session_state.get('analysis_requested'):
            pitcher = st.session_state.get('selected_pitcher')
            game = st.session_state.get('selected_game')
            
            if pitcher and game:
                with st.spinner(f"{pitcher.name}の{game.date}の試合を分析中..."):
                    try:
                        # 分析実行
                        result = self.use_case.analyze_game(pitcher.id, game.date)
                        
                        if result.error:
                            st.error(f"分析エラー: {result.error}")
                        else:
                            # 分析結果表示
                            st.header(f"{result.pitcher_name} - {result.game_date}の投球分析")
                            
                            # タブで結果表示
                            tab1, tab2, tab3, tab4 = st.tabs(["概要", "イニング分析", "球種分析", "被打球分析"])
                            
                            with tab1:
                                self._render_summary(result)
                            
                            with tab2:
                                self._render_inning_analysis(result.inning_analysis)
                            
                            with tab3:
                                self._render_pitch_type_analysis(result.pitch_type_analysis)
                            
                            with tab4:
                                self._render_batted_ball_analysis(result.batted_ball_analysis)
                    except Exception as e:
                        st.error(f"分析エラー: {str(e)}")
                        self.logger.error(f"分析エラー: {str(e)}", exc_info=True)
    
    def _render_summary(self, result):
        """概要タブの表示"""
        if result.performance_summary:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("投球サマリー")
                
                # 主要な数値を取得
                total_pitches = result.performance_summary.get('total_pitches', 0)
                innings_pitched = result.performance_summary.get('innings_pitched', 0)
                
                # メトリクス表示
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                metrics_col1.metric("総投球数", f"{total_pitches}球")
                metrics_col2.metric("イニング", f"{innings_pitched}")
                metrics_col3.metric("打者数", f"{result.performance_summary.get('batters_faced', 0)}人")
                
                # パフォーマンスサマリーグラフ
                summary_fig = self.visualizer.create_performance_summary_chart(result.performance_summary)
                st.pyplot(summary_fig)
            
            with col2:
                st.subheader("球種分布")
                
                if result.pitch_type_analysis and 'usage' in result.pitch_type_analysis:
                    # 球種使用率グラフ
                    pitch_type_fig = self.visualizer.create_pitch_type_chart(result.pitch_type_analysis)
                    st.pyplot(pitch_type_fig)
                else:
                    st.info("球種分析データがありません")
        else:
            st.warning("パフォーマンスサマリーデータがありません")
    
    def _render_inning_analysis(self, inning_analysis):
        """イニング分析タブの表示"""
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
    
    def _render_pitch_type_analysis(self, pitch_type_analysis):
        """球種分析タブの表示"""
        if not pitch_type_analysis or 'error' in pitch_type_analysis:
            st.info("球種分析データがありません")
            return
        
        st.subheader("球種別分析")
        
        if 'pitch_types' not in pitch_type_analysis or not pitch_type_analysis['pitch_types']:
            st.info("球種データがありません")
            return
        
        # 球種効果グラフ
        st.markdown("#### 球種効果")
        effectiveness_fig = self.visualizer.create_pitch_effectiveness_chart(pitch_type_analysis)
        st.pyplot(effectiveness_fig)
    
    def _render_batted_ball_analysis(self, batted_ball_analysis):
        """被打球分析タブの表示"""
        if batted_ball_analysis is None or batted_ball_analysis.empty:
            st.info("被打球データがありません")
            return
        
        st.subheader("被打球分析")
        
        # 被打球分布図
        st.markdown("#### 被打球分布")
        batted_ball_fig = self.visualizer.create_batted_ball_chart(batted_ball_analysis)
        st.pyplot(batted_ball_fig)