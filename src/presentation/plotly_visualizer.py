"""
Plotlyを使用したデータの可視化を担当するクラス
グラフやチャートの生成を行う
"""
import logging
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Optional, Tuple


class PlotlyVisualizer:
    """Plotlyを使用したデータの可視化を担当するクラス"""
    
    def __init__(self):
        """
        PlotlyVisualizer の初期化
        """
        # スタイル設定
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'tertiary': '#2ca02c',
            'quaternary': '#d62728',
            'background': '#f8f9fa',
            'text': '#212529',
            'axis': '#444444',  # 軸ラベルの色を濃く
            'title': '#000000'  # タイトルは黒に
        }
        
        # 共通レイアウト設定
        self.layout_defaults = {
            'template': 'plotly_white',
            'font': {'family': 'Arial, sans-serif', 'color': self.colors['text'], 'size': 12},
            'paper_bgcolor': self.colors['background'],
            'plot_bgcolor': self.colors['background'],
            'margin': {'t': 60, 'r': 30, 'b': 60, 'l': 30}
            # titleプロパティは個別に設定するので、ここでは指定しない
        }
        
        # 軸設定（個別に適用するため分離）
        self.axis_defaults = {
            'gridcolor': 'rgba(0, 0, 0, 0.1)',
            'showgrid': True,
            'title': {'font': {'size': 14, 'color': self.colors['axis']}},
            'tickfont': {'size': 12, 'color': self.colors['axis']},
            'linecolor': 'rgba(0, 0, 0, 0.3)',  # 軸線を濃く
            'linewidth': 1.5
        }
        
        self.logger = logging.getLogger(__name__)
    
    def create_velocity_chart(self, inning_data: Dict[str, Any]) -> go.Figure:
        """
        イニング別球速のグラフを作成
        
        Parameters:
        -----------
        inning_data : Dict[str, Any]
            イニング別分析データ
            
        Returns:
        --------
        go.Figure
            Plotlyのfigure
        """
        self.logger.info("イニング別球速グラフを作成（Plotly）")
        
        # inningキーがない場合は空図を返す
        if 'innings' not in inning_data or not inning_data['innings']:
            fig = go.Figure()
            fig.add_annotation(
                text="データがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # データの準備
        innings = sorted(inning_data['innings'])
        
        # 球速データの抽出
        mean_speeds = []
        max_speeds = []
        min_speeds = []
        
        for inning in innings:
            inning_str = str(inning)
            if inning_str in inning_data['velocity']:
                mean_speeds.append(inning_data['velocity'][inning_str]['mean'])
                max_speeds.append(inning_data['velocity'][inning_str]['max'])
                min_speeds.append(inning_data['velocity'][inning_str]['min'])
            else:
                mean_speeds.append(None)
                max_speeds.append(None)
                min_speeds.append(None)
        
        # グラフの作成
        fig = go.Figure()
        
        # 最大・最小球速の範囲を表示（まずfill areaを追加し、その後にラインを追加）
        if any(x is not None for x in min_speeds) and any(x is not None for x in max_speeds):
            # Fill area for min-max range
            fig.add_trace(go.Scatter(
                x=innings + innings[::-1],
                y=max_speeds + min_speeds[::-1],
                fill='toself',
                fillcolor='rgba(31, 119, 180, 0.2)',
                line=dict(color='rgba(255, 255, 255, 0)'),
                showlegend=True,
                name='最小-最大範囲'
            ))
        
        # 平均球速のライン
        if any(x is not None for x in mean_speeds):
            fig.add_trace(go.Scatter(
                x=innings,
                y=mean_speeds,
                mode='lines+markers',
                line=dict(color=self.colors['primary'], width=3),
                marker=dict(size=8),
                name='平均球速'
            ))
        
        # グラフ設定
        fig.update_layout(
            title='イニング別球速の推移',
            **self.layout_defaults
        )
        
        # 軸設定を別途更新
        fig.update_xaxes(
            title={'text': 'イニング', 'font': {'size': 14, 'color': self.colors['axis']}},
            tickmode='array',
            tickvals=innings,
            ticktext=[str(i) for i in innings],
            tickfont={'size': 12, 'color': self.colors['axis']},
            gridcolor='rgba(0, 0, 0, 0.1)',
            linecolor='rgba(0, 0, 0, 0.3)',
            linewidth=1.5
        )
        
        fig.update_yaxes(
            title={'text': '球速 (mph)', 'font': {'size': 14, 'color': self.colors['axis']}},
            tickfont={'size': 12, 'color': self.colors['axis']},
            gridcolor='rgba(0, 0, 0, 0.1)',
            linecolor='rgba(0, 0, 0, 0.3)',
            linewidth=1.5
        )
        
        # Y軸の範囲設定（球速の一般的な範囲）
        valid_speeds = [s for s in mean_speeds if s is not None]
        if valid_speeds:
            mean_speed = np.mean(valid_speeds)
            fig.update_yaxes(range=[mean_speed - 10, mean_speed + 10])
        
        return fig
    
    def create_pitch_distribution_chart(self, inning_data: Dict[str, Any]) -> go.Figure:
        """
        イニング別投球分布のグラフを作成
        
        Parameters:
        -----------
        inning_data : Dict[str, Any]
            イニング別分析データ
            
        Returns:
        --------
        go.Figure
            Plotlyのfigure
        """
        self.logger.info("イニング別投球分布グラフを作成（Plotly）")
        
        # inningキーがない場合は空図を返す
        if 'innings' not in inning_data or not inning_data['innings']:
            fig = go.Figure()
            fig.add_annotation(
                text="データがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # データの準備
        innings = sorted(inning_data['innings'])
        
        # 各イニングの投球数
        pitch_counts = []
        for inning in innings:
            inning_str = str(inning)
            if inning_str in inning_data['pitch_count']:
                pitch_counts.append(inning_data['pitch_count'][inning_str])
            else:
                pitch_counts.append(0)
        
        # グラフの作成
        fig = go.Figure()
        
        # 棒グラフでイニング別投球数
        fig.add_trace(go.Bar(
            x=[str(i) for i in innings],
            y=pitch_counts,
            marker_color=self.colors['primary'],
            opacity=0.8,
            text=pitch_counts,
            textposition='outside'
        ))
        
        # グラフ設定
        fig.update_layout(
            title='イニング別投球数',
            **self.layout_defaults
        )
        
        # 軸設定を別途更新
        fig.update_xaxes(
            title='イニング',
            tickmode='array',
            tickvals=[str(i) for i in innings],
            gridcolor='rgba(0, 0, 0, 0.1)'
        )
        
        fig.update_yaxes(
            title='投球数',
            gridcolor='rgba(0, 0, 0, 0.1)'
        )
        
        # Y軸の範囲設定（0から少し上まで）
        max_count = max(pitch_counts) if pitch_counts else 10
        fig.update_yaxes(range=[0, max_count * 1.2])
        
        return fig
    
    def create_pitch_type_chart(self, pitch_type_data: Dict[str, Any]) -> go.Figure:
        """
        球種別分布のグラフを作成
        
        Parameters:
        -----------
        pitch_type_data : Dict[str, Any]
            球種別分析データ
            
        Returns:
        --------
        go.Figure
            Plotlyのfigure
        """
        self.logger.info("球種別分布グラフを作成（Plotly）")
        
        # pitch_typesキーがない場合は空図を返す
        if 'pitch_types' not in pitch_type_data or not pitch_type_data['pitch_types']:
            fig = go.Figure()
            fig.add_annotation(
                text="データがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # データの準備
        pitch_types = pitch_type_data['pitch_types']
        
        # 使用率と球数の抽出
        usage_data = []
        for pt in pitch_types:
            if pt in pitch_type_data['usage']:
                usage_data.append({
                    'pitch_type': pt,
                    'count': pitch_type_data['usage'][pt]['count'],
                    'percentage': pitch_type_data['usage'][pt]['percentage']
                })
        
        # 使用率でソート
        usage_data.sort(key=lambda x: x['percentage'], reverse=True)
        
        # データの準備
        labels = [d['pitch_type'] for d in usage_data]
        percentages = [d['percentage'] for d in usage_data]
        counts = [d['count'] for d in usage_data]
        
        # グラフの作成
        fig = go.Figure()
        
        # 棒グラフで球種別使用率
        fig.add_trace(go.Bar(
            x=labels,
            y=percentages,
            marker_color=self.colors['primary'],
            opacity=0.8,
            text=[f"{pct:.1f}%<br>({cnt}球)" for pct, cnt in zip(percentages, counts)],
            textposition='outside'
        ))
        
        # グラフ設定
        fig.update_layout(
            title='球種別使用率',
            **self.layout_defaults
        )
        
        # 軸設定を別途更新
        fig.update_xaxes(
            title='球種',
            gridcolor='rgba(0, 0, 0, 0.1)'
        )
        
        fig.update_yaxes(
            title='使用率 (%)',
            gridcolor='rgba(0, 0, 0, 0.1)'
        )
        
        # Y軸の範囲を0から適切な最大値に設定
        max_pct = max(percentages) if percentages else 100
        fig.update_yaxes(range=[0, max_pct * 1.15])
        
        return fig
    
    def create_pitch_effectiveness_chart(self, pitch_type_data: Dict[str, Any]) -> go.Figure:
        """
        球種別有効性のグラフを作成
        
        Parameters:
        -----------
        pitch_type_data : Dict[str, Any]
            球種別分析データ
            
        Returns:
        --------
        go.Figure
            Plotlyのfigure
        """
        self.logger.info("球種別有効性グラフを作成（Plotly）")
        
        # pitch_typesキーがない場合は空図を返す
        if 'pitch_types' not in pitch_type_data or not pitch_type_data['pitch_types']:
            fig = go.Figure()
            fig.add_annotation(
                text="データがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # データの準備
        pitch_types = pitch_type_data['pitch_types']
        
        # 有効性データの抽出
        effectiveness_data = []
        for pt in pitch_types:
            if pt in pitch_type_data['effectiveness']:
                effectiveness_data.append({
                    'pitch_type': pt,
                    'strike_pct': pitch_type_data['effectiveness'][pt]['strike_percentage'],
                    'swing_miss_pct': pitch_type_data['effectiveness'][pt]['swinging_strike_percentage'],
                    'hit_pct': pitch_type_data['effectiveness'][pt]['hit_percentage']
                })
        
        if not effectiveness_data:
            fig = go.Figure()
            fig.add_annotation(
                text="有効性データがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # 使用率の高い順にソート（usageデータを使用）
        if 'usage' in pitch_type_data:
            # 使用頻度情報に基づいてソート
            effectiveness_data.sort(
                key=lambda x: pitch_type_data['usage'].get(x['pitch_type'], {}).get('percentage', 0), 
                reverse=True
            )
        
        # データの準備
        labels = [d['pitch_type'] for d in effectiveness_data]
        strike_pcts = [d['strike_pct'] for d in effectiveness_data]
        swing_miss_pcts = [d['swing_miss_pct'] for d in effectiveness_data]
        hit_pcts = [d['hit_pct'] for d in effectiveness_data]
        
        # グラフの作成 - グループ化されたバーチャート
        fig = go.Figure()
        
        # 3種類のバーを追加
        fig.add_trace(go.Bar(
            x=labels,
            y=strike_pcts,
            name='ストライク率',
            marker_color=self.colors['primary'],
            text=[f"{pct:.1f}%" for pct in strike_pcts],
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            x=labels,
            y=swing_miss_pcts,
            name='空振り率',
            marker_color=self.colors['secondary'],
            text=[f"{pct:.1f}%" for pct in swing_miss_pcts],
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            x=labels,
            y=hit_pcts,
            name='被安打率',
            marker_color=self.colors['quaternary'],
            text=[f"{pct:.1f}%" for pct in hit_pcts],
            textposition='auto'
        ))
        
        # グラフ設定 - グループ化
        fig.update_layout(
            title='球種別有効性指標',
            barmode='group',  # グループ化されたバーチャート
            bargap=0.15,      # グループ間のギャップ
            bargroupgap=0.1,  # バー間のギャップ
            **self.layout_defaults
        )
        
        # 軸設定を別途更新
        fig.update_xaxes(
            title='球種',
            gridcolor='rgba(0, 0, 0, 0.1)'
        )
        
        fig.update_yaxes(
            title='割合 (%)',
            gridcolor='rgba(0, 0, 0, 0.1)'
        )
        
        # Y軸の範囲を0から適切な最大値に設定
        all_values = strike_pcts + swing_miss_pcts + hit_pcts
        max_value = max(all_values) if all_values else 100
        fig.update_yaxes(range=[0, max_value * 1.15])
        
        return fig
    
    def create_batted_ball_chart(self, batted_ball_data: pd.DataFrame) -> go.Figure:
        """
        被打球分布のグラフを作成
        
        Parameters:
        -----------
        batted_ball_data : pd.DataFrame
            被打球分析データ
            
        Returns:
        --------
        go.Figure
            Plotlyのfigure
        """
        self.logger.info("被打球分布グラフを作成（Plotly）")
        
        if batted_ball_data is None or batted_ball_data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="被打球データがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # グラフの作成 - 野球場の図を作成
        fig = go.Figure()
        
        # 野球場の描画
        # 内野の円
        fig.add_shape(
            type="circle",
            xref="x", yref="y",
            x0=-95, y0=-95, x1=95, y1=95,
            line=dict(color="gray", width=1),
            fillcolor="rgba(0,0,0,0)"
        )
        
        # 外野の円
        fig.add_shape(
            type="circle",
            xref="x", yref="y",
            x0=-300, y0=-300, x1=300, y1=300,
            line=dict(color="gray", width=1),
            fillcolor="rgba(0,0,0,0)"
        )
        
        # ベースライン
        fig.add_shape(
            type="line",
            xref="x", yref="y",
            x0=0, y0=0, x1=90, y1=90,
            line=dict(color="gray", width=1)
        )
        
        fig.add_shape(
            type="line",
            xref="x", yref="y",
            x0=0, y0=0, x1=-90, y1=90,
            line=dict(color="gray", width=1)
        )
        
        # 投手マウンド
        fig.add_shape(
            type="circle",
            xref="x", yref="y",
            x0=-9, y0=51.5, x1=9, y1=69.5,
            line=dict(color="gray", width=1),
            fillcolor="rgba(0,0,0,0)"
        )
        
        # ホームプレート
        fig.add_shape(
            type="rect",
            xref="x", yref="y",
            x0=-8.5, y0=-8.5, x1=8.5, y1=8.5,
            line=dict(color="gray", width=1),
            fillcolor="rgba(0,0,0,0)"
        )
        
        # 一塁
        fig.add_shape(
            type="rect",
            xref="x", yref="y",
            x0=85, y0=85, x1=95, y1=95,
            line=dict(color="gray", width=1),
            fillcolor="rgba(0,0,0,0)"
        )
        
        # 二塁
        fig.add_shape(
            type="rect",
            xref="x", yref="y",
            x0=-5, y0=175, x1=5, y1=185,
            line=dict(color="gray", width=1),
            fillcolor="rgba(0,0,0,0)"
        )
        
        # 三塁
        fig.add_shape(
            type="rect",
            xref="x", yref="y",
            x0=-95, y0=85, x1=-85, y1=95,
            line=dict(color="gray", width=1),
            fillcolor="rgba(0,0,0,0)"
        )
        
        # 座標データの準備
        has_coordinates = 'hc_x' in batted_ball_data.columns and 'hc_y' in batted_ball_data.columns
        
        if has_coordinates:
            # 座標のスケール調整
            x_coords = batted_ball_data['hc_x'].values
            y_coords = batted_ball_data['hc_y'].values
            
            # 結果でカラー分け
            colors = []
            for result in batted_ball_data['hit_result']:
                if pd.isna(result):
                    colors.append('gray')
                elif 'single' in str(result).lower():
                    colors.append('green')
                elif 'double' in str(result).lower():
                    colors.append('blue')
                elif 'triple' in str(result).lower():
                    colors.append('purple')
                elif 'home' in str(result).lower():
                    colors.append('red')
                elif 'out' in str(result).lower():
                    colors.append('black')
                else:
                    colors.append('gray')
            
            # サイズを打球速度から決定
            sizes = []
            if 'launch_speed' in batted_ball_data.columns:
                for speed in batted_ball_data['launch_speed']:
                    if pd.isna(speed):
                        sizes.append(12)
                    else:
                        # 8-30の範囲でサイズを設定
                        sizes.append(8 + min(22, speed / 5))
            else:
                sizes = [15] * len(x_coords)
            
            # ホバー情報の準備
            hover_data = []
            for i in range(len(x_coords)):
                info = {}
                if 'pitch_type' in batted_ball_data.columns:
                    info['球種'] = batted_ball_data['pitch_type'].iloc[i] if not pd.isna(batted_ball_data['pitch_type'].iloc[i]) else '不明'
                if 'launch_speed' in batted_ball_data.columns:
                    info['打球速度'] = f"{batted_ball_data['launch_speed'].iloc[i]:.1f} mph" if not pd.isna(batted_ball_data['launch_speed'].iloc[i]) else '不明'
                if 'launch_angle' in batted_ball_data.columns:
                    info['打角'] = f"{batted_ball_data['launch_angle'].iloc[i]:.1f}°" if not pd.isna(batted_ball_data['launch_angle'].iloc[i]) else '不明'
                if 'hit_distance_sc' in batted_ball_data.columns:
                    info['飛距離'] = f"{batted_ball_data['hit_distance_sc'].iloc[i]:.1f} ft" if not pd.isna(batted_ball_data['hit_distance_sc'].iloc[i]) else '不明'
                
                # ホバーテキストの作成
                hover_text = '<br>'.join([f"{k}: {v}" for k, v in info.items()])
                hover_data.append(hover_text)
            
            # 散布図の追加
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='markers',
                marker=dict(
                    color=colors,
                    size=sizes,
                    opacity=0.7,
                    line=dict(width=1, color='gray')
                ),
                text=hover_data,
                hoverinfo='text',
                name='被打球'
            ))
            
            # 凡例の追加（カスタム）
            legend_items = [
                dict(name='アウト', color='black'),
                dict(name='シングルヒット', color='green'),
                dict(name='ツーベースヒット', color='blue'),
                dict(name='スリーベースヒット', color='purple'),
                dict(name='ホームラン', color='red'),
                dict(name='その他/不明', color='gray')
            ]
            
            # Y軸上部に離して凡例アイテムを配置
            legend_y = 410
            for item in legend_items:
                # マーカー（点）
                fig.add_trace(go.Scatter(
                    x=[300],
                    y=[legend_y],
                    mode='markers',
                    marker=dict(size=10, color=item['color']),
                    showlegend=False
                ))
                
                # テキスト
                fig.add_annotation(
                    x=310, y=legend_y,
                    text=item['name'],
                    showarrow=False,
                    xanchor='left',
                    font=dict(color=self.colors['text'])
                )
                
                legend_y -= 20
        else:
            # 座標データがない場合
            fig.add_annotation(
                text="座標データがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16)
            )
        
        # グラフ設定
        fig.update_layout(
            title='被打球分布',
            showlegend=False,
            **self.layout_defaults
        )
        
        # 軸設定を別途更新
        fig.update_xaxes(
            range=[-330, 330],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        )
        
        fig.update_yaxes(
            range=[-50, 420],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1
        )
        
        return fig
    
    def create_performance_summary_chart(self, performance_summary: Dict[str, Any]) -> go.Figure:
        """
        パフォーマンスサマリーのグラフを作成
        
        Parameters:
        -----------
        performance_summary : Dict[str, Any]
            パフォーマンスサマリーデータ
            
        Returns:
        --------
        go.Figure
            Plotlyのfigure
        """
        self.logger.info("パフォーマンスサマリーグラフを作成（Plotly）")
        
        if not performance_summary or 'error' in performance_summary:
            fig = go.Figure()
            fig.add_annotation(
                text="サマリーデータがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # 2x2のサブプロットの作成
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                '球種分布', '球速分布',
                '結果分布', 'ストライク率'
            ),
            specs=[
                [{"type": "pie"}, {"type": "histogram"}],
                [{"type": "bar"}, {"type": "indicator"}]
            ],
            column_widths=[0.5, 0.5],
            row_heights=[0.5, 0.5]
        )
        
        # 1. 球種分布パイチャート
        if 'pitch_type_counts' in performance_summary and performance_summary['pitch_type_counts']:
            pitch_types = list(performance_summary['pitch_type_counts'].keys())
            counts = list(performance_summary['pitch_type_counts'].values())
            
            # 使用頻度が少ない球種をまとめる（5%未満を「その他」に）
            total = sum(counts)
            threshold = total * 0.05
            
            other_count = 0
            filtered_types = []
            filtered_counts = []
            
            for pt, cnt in zip(pitch_types, counts):
                if cnt >= threshold:
                    filtered_types.append(pt)
                    filtered_counts.append(cnt)
                else:
                    other_count += cnt
            
            if other_count > 0:
                filtered_types.append('Other')
                filtered_counts.append(other_count)
            
            # パイチャートの追加
            # 最も使用頻度の高い球種のインデックスを特定
            max_index = filtered_counts.index(max(filtered_counts)) if filtered_counts else 0
            
            fig.add_trace(
                go.Pie(
                    labels=filtered_types,
                    values=filtered_counts,
                    textinfo='percent+label+value',
                    hole=0.4,
                    pull=[0.1 if i == max_index else 0 for i in range(len(filtered_counts))],
                    marker=dict(
                        colors=px.colors.sequential.Viridis[:len(filtered_types)],
                        line=dict(color='white', width=2)
                    ),
                    hovertemplate="<b>%{label}</b><br>球数: %{value}<br>割合: %{percent}<extra></extra>",
                    textposition='inside',
                    insidetextorientation='radial',
                    showlegend=False
                ),
                row=1, col=1
            )
        else:
            fig.add_annotation(
                text="球種データがありません",
                xref="x domain", yref="y domain",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color=self.colors['axis'], family="Arial"),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor=self.colors['axis'],
                borderwidth=1,
                borderpad=10,
                row=1, col=1
            )
        
        # 2. 球速ヒストグラム
        if 'velocity' in performance_summary and performance_summary['velocity']:
            velocity_data = performance_summary['velocity']
            
            # ダミーデータ生成（正規分布）
            mean = velocity_data.get('average', 90)
            std = velocity_data.get('std', 2)
            min_v = velocity_data.get('min', mean - 5)
            max_v = velocity_data.get('max', mean + 5)
            
            # 正規分布に従うデータポイントを生成
            velocity_points = np.random.normal(mean, std, 1000)
            velocity_points = velocity_points[(velocity_points >= min_v) & (velocity_points <= max_v)]
            
            # ヒストグラムの追加
            fig.add_trace(
                go.Histogram(
                    x=velocity_points,
                    nbinsx=15,
                    marker_color=self.colors['primary'],
                    marker_line_color='rgba(0,0,0,0.3)',
                    marker_line_width=1,
                    opacity=0.7,
                    name='球速分布',
                    hovertemplate="球速: %{x:.1f} mph<br>頻度: %{y}<extra></extra>",
                    hoverlabel=dict(
                        bgcolor='white',
                        font_size=12,
                        font_family="Arial",
                        bordercolor=self.colors['primary']
                    )
                ),
                row=1, col=2
            )
            
            # 最大・最小・平均速度の線を追加（垂直線をshapeとして追加）
            if 'max' in velocity_data:
                fig.add_shape(
                    type="line",
                    x0=velocity_data['max'], y0=0,
                    x1=velocity_data['max'], y1=1,
                    line=dict(dash="dash", color="red", width=2),
                    xref="x2", yref="paper",
                    row=1, col=2
                )
                # 注釈を追加
                fig.add_annotation(
                    x=velocity_data['max'],
                    y=0.95,
                    text=f"最高: {velocity_data['max']:.1f} mph",
                    showarrow=False,
                    xref="x2", yref="paper",
                    xanchor="left",
                    font=dict(size=12, color='red', family="Arial", weight="bold"),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="red",
                    borderwidth=1,
                    borderpad=4,
                    row=1, col=2
                )
            
            if 'average' in velocity_data:
                fig.add_shape(
                    type="line",
                    x0=velocity_data['average'], y0=0,
                    x1=velocity_data['average'], y1=1,
                    line=dict(dash="solid", color="green", width=2),
                    xref="x2", yref="paper",
                    row=1, col=2
                )
                # 注釈を追加
                fig.add_annotation(
                    x=velocity_data['average'],
                    y=0.85,
                    text=f"平均: {velocity_data['average']:.1f} mph",
                    showarrow=False,
                    xref="x2", yref="paper",
                    xanchor="left",
                    font=dict(size=12, color='green', family="Arial", weight="bold"),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="green",
                    borderwidth=1,
                    borderpad=4,
                    row=1, col=2
                )
            
            if 'min' in velocity_data:
                fig.add_shape(
                    type="line",
                    x0=velocity_data['min'], y0=0,
                    x1=velocity_data['min'], y1=1,
                    line=dict(dash="dash", color="blue", width=2),
                    xref="x2", yref="paper",
                    row=1, col=2
                )
                # 注釈を追加
                fig.add_annotation(
                    x=velocity_data['min'],
                    y=0.75,
                    text=f"最低: {velocity_data['min']:.1f} mph",
                    showarrow=False,
                    xref="x2", yref="paper",
                    xanchor="left",
                    font=dict(size=12, color='blue', family="Arial", weight="bold"),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="blue",
                    borderwidth=1,
                    borderpad=4,
                    row=1, col=2
                )
            
            # この部分は削除します - 後で一括して設定します
        else:
            fig.add_annotation(
                text="球速データがありません",
                xref="x2 domain", yref="y2 domain",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14),
                row=1, col=2
            )
        
        # 3. 結果分布の棒グラフ
        if 'outcomes' in performance_summary and performance_summary['outcomes']:
            outcomes = performance_summary['outcomes']
            
            # 結果データの抽出
            categories = ['called_strikes', 'swinging_strikes', 'fouls', 'balls', 'hits']
            values = []
            
            for cat in categories:
                if cat in outcomes:
                    values.append(outcomes[cat])
                else:
                    values.append(0)
            
            # 日本語ラベル
            labels = ['見逃し', '空振り', 'ファウル', 'ボール', 'ヒット']
            
            # 棒グラフの追加
            fig.add_trace(
                go.Bar(
                    x=labels,
                    y=values,
                    text=values,
                    textposition='outside',
                    textfont=dict(size=12, color=self.colors['axis']),
                    marker_color=px.colors.qualitative.Plotly[:len(labels)],
                    marker_line_width=1,
                    marker_line_color='rgba(0,0,0,0.3)',
                    hovertemplate="<b>%{x}</b><br>投球数: %{y}<extra></extra>",
                    hoverlabel=dict(
                        bgcolor='white',
                        font_size=12,
                        font_family="Arial"
                    ),
                    showlegend=False
                ),
                row=2, col=1
            )
            
            # 軸の設定
            fig.update_yaxes(title_text="投球数", row=2, col=1)
            
            # y軸の調整
            max_value = max(values) if values else 10
            fig.update_yaxes(range=[0, max_value * 1.2], row=2, col=1)
        else:
            fig.add_annotation(
                text="結果データがありません",
                xref="x3 domain", yref="y3 domain",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14),
                row=2, col=1
            )
        
        # 4. ストライク率のゲージ
        if 'outcomes' in performance_summary and 'strike_percentage' in performance_summary['outcomes']:
            strike_pct = performance_summary['outcomes']['strike_percentage']
            
            # ゲージの色を決定
            gauge_thresholds = [45, 55, 65, 75, 100]  # ストライク率の閾値
            gauge_colors = ['red', 'orange', 'yellow', 'yellowgreen', 'green']
            
            # 該当する色を判定
            gauge_color = gauge_colors[0]
            for i, threshold in enumerate(gauge_thresholds):
                if strike_pct <= threshold:
                    gauge_color = gauge_colors[i]
                    break
            
            # ゲージチャートの追加
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=strike_pct,
                    title={
                        'text': "ストライク率",
                        'font': {'size': 16, 'color': self.colors['title'], 'family': 'Arial'}
                    },
                    gauge={
                        'axis': {
                            'range': [0, 100],
                            'tickwidth': 1,
                            'tickfont': {'size': 12, 'color': self.colors['axis']},
                            'tickcolor': self.colors['axis']
                        },
                        'bar': {'color': gauge_color, 'thickness': 0.7},
                        'bgcolor': 'white',
                        'borderwidth': 2,
                        'bordercolor': self.colors['axis'],
                        'steps': [
                            {'range': [0, 45], 'color': 'rgba(255, 0, 0, 0.15)'},
                            {'range': [45, 55], 'color': 'rgba(255, 165, 0, 0.15)'},
                            {'range': [55, 65], 'color': 'rgba(255, 255, 0, 0.15)'},
                            {'range': [65, 75], 'color': 'rgba(154, 205, 50, 0.15)'},
                            {'range': [75, 100], 'color': 'rgba(0, 128, 0, 0.15)'}
                        ],
                        'threshold': {
                            'line': {'color': "black", 'width': 2},
                            'thickness': 0.8,
                            'value': strike_pct
                        }
                    },
                    domain={'row': 1, 'column': 1},
                    number={
                        'suffix': "%", 
                        'font': {
                            'size': 28, 
                            'color': gauge_color, 
                            'family': 'Arial',
                            'weight': 'bold'
                        }
                    }
                ),
                row=2, col=2
            )
        else:
            fig.add_annotation(
                text="ストライク率データがありません",
                xref="x4 domain", yref="y4 domain",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14),
                row=2, col=2
            )
        
        # 全体レイアウトの設定
        fig.update_layout(
            height=800,
            title=dict(
                text="パフォーマンスサマリー",
                font=dict(size=20, color=self.colors['title'], family="Arial, sans-serif", weight="bold"),
                x=0.5,
                y=0.98
            ),
            # サブプロットタイトルのフォント設定
            font=dict(
                family="Arial, sans-serif",
                size=14,
                color=self.colors['axis']
            ),
            # layout_defaultsから必要なプロパティだけを抽出
            paper_bgcolor=self.layout_defaults['paper_bgcolor'],
            plot_bgcolor=self.layout_defaults['plot_bgcolor'],
            margin=self.layout_defaults['margin'],
            template=self.layout_defaults['template']
        )
        
        # サブプロットのタイトルを強調
        for i in fig['layout']['annotations']:
            i['font'] = dict(size=16, color=self.colors['title'], family="Arial, sans-serif", weight="bold")
        
        # 各サブプロットの軸を個別に設定（パイチャート以外）
        fig.update_xaxes(
            title_text="球速 (mph)",
            title_font=dict(size=14, color=self.colors['axis']),
            tickfont=dict(size=12, color=self.colors['axis']),
            gridcolor='rgba(0, 0, 0, 0.1)',
            linecolor='rgba(0, 0, 0, 0.3)',
            linewidth=1.5,
            row=1, col=2
        )
        
        fig.update_yaxes(
            title_text="頻度",
            title_font=dict(size=14, color=self.colors['axis']),
            tickfont=dict(size=12, color=self.colors['axis']),
            gridcolor='rgba(0, 0, 0, 0.1)',
            linecolor='rgba(0, 0, 0, 0.3)',
            linewidth=1.5,
            row=1, col=2
        )
        
        fig.update_xaxes(
            title_text="結果",
            title_font=dict(size=14, color=self.colors['axis']),
            tickfont=dict(size=12, color=self.colors['axis']),
            gridcolor='rgba(0, 0, 0, 0.1)',
            linecolor='rgba(0, 0, 0, 0.3)',
            linewidth=1.5,
            row=2, col=1
        )
        
        fig.update_yaxes(
            title_text="投球数",
            title_font=dict(size=14, color=self.colors['axis']),
            tickfont=dict(size=12, color=self.colors['axis']),
            gridcolor='rgba(0, 0, 0, 0.1)',
            linecolor='rgba(0, 0, 0, 0.3)',
            linewidth=1.5,
            row=2, col=1
        )
        
        return fig