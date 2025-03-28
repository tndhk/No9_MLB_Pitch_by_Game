class DataVisualizer:
    """データの可視化を担当するクラス"""
    
    def __init__(self):
        """
        DataVisualizer の初期化
        """
        # スタイル設定
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'tertiary': '#2ca02c',
            'quaternary': '#d62728',
            'background': '#f8f9fa',
            'text': '#212529'
        }
        
        # グラフスタイルの設定
        sns.set_style('whitegrid')
        
        self.logger = logging.getLogger(__name__)
    
    def create_velocity_chart(self, inning_data: Dict[str, Any]) -> Figure:
        """
        イニング別球速のグラフを作成
        
        Parameters:
        -----------
        inning_data : Dict[str, Any]
            イニング別分析データ
            
        Returns:
        --------
        Figure
            Matplotlibのfigure
        """
        self.logger.info("イニング別球速グラフを作成")
        
        # inningキーがない場合は空図を返す
        if 'innings' not in inning_data or not inning_data['innings']:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.text(0.5, 0.5, 'データがありません', ha='center', va='center')
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
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 最大・最小球速の範囲を表示
        if any(x is not None for x in min_speeds) and any(x is not None for x in max_speeds):
            ax.fill_between(innings, min_speeds, max_speeds, alpha=0.2, color=self.colors['primary'], label='最小-最大')
        
        # 平均球速のライン
        if any(x is not None for x in mean_speeds):
            ax.plot(innings, mean_speeds, marker='o', linestyle='-', color=self.colors['primary'], linewidth=2, label='平均球速')
        
        # グラフ設定
        ax.set_xlabel('イニング')
        ax.set_ylabel('球速 (mph)')
        ax.set_title('イニング別球速の推移')
        ax.set_xticks(innings)
        ax.set_xticklabels([str(i) for i in innings])
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        # Y軸の範囲設定（球速の一般的な範囲）
        valid_speeds = [s for s in mean_speeds if s is not None]
        if valid_speeds:
            mean_speed = np.mean(valid_speeds)
            ax.set_ylim([mean_speed - 10, mean_speed + 10])
        
        plt.tight_layout()
        
        return fig
    
    def create_pitch_distribution_chart(self, inning_data: Dict[str, Any]) -> Figure:
        """
        イニング別投球分布のグラフを作成
        
        Parameters:
        -----------
        inning_data : Dict[str, Any]
            イニング別分析データ
            
        Returns:
        --------
        Figure
            Matplotlibのfigure
        """
        self.logger.info("イニング別投球分布グラフを作成")
        
        # inningキーがない場合は空図を返す
        if 'innings' not in inning_data or not inning_data['innings']:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.text(0.5, 0.5, 'データがありません', ha='center', va='center')
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
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 棒グラフでイニング別投球数
        bars = ax.bar(innings, pitch_counts, color=self.colors['primary'], alpha=0.7)
        
        # 数値をバーの上に表示
        for bar, count in zip(bars, pitch_counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{count}', ha='center', va='bottom')
        
        # グラフ設定
        ax.set_xlabel('イニング')
        ax.set_ylabel('投球数')
        ax.set_title('イニング別投球数')
        ax.set_xticks(innings)
        ax.set_xticklabels([str(i) for i in innings])
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        
        plt.tight_layout()
        
        return fig
    
    def create_pitch_type_chart(self, pitch_type_data: Dict[str, Any]) -> Figure:
        """
        球種別分布のグラフを作成
        
        Parameters:
        -----------
        pitch_type_data : Dict[str, Any]
            球種別分析データ
            
        Returns:
        --------
        Figure
            Matplotlibのfigure
        """
        self.logger.info("球種別分布グラフを作成")
        
        # pitch_typesキーがない場合は空図を返す
        if 'pitch_types' not in pitch_type_data or not pitch_type_data['pitch_types']:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.text(0.5, 0.5, 'データがありません', ha='center', va='center')
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
        
        # グラフの作成
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 棒グラフで球種別使用率
        labels = [d['pitch_type'] for d in usage_data]
        percentages = [d['percentage'] for d in usage_data]
        counts = [d['count'] for d in usage_data]
        
        bars = ax.bar(labels, percentages, color=[self.colors['primary'] for _ in labels], alpha=0.7)
        
        # 数値をバーの上に表示
        for bar, pct, cnt in zip(bars, percentages, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{pct:.1f}%\n({cnt})', ha='center', va='bottom')
        
        # グラフ設定
        ax.set_xlabel('球種')
        ax.set_ylabel('使用率 (%)')
        ax.set_title('球種別使用率')
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        
        # y軸の範囲を0から適切な最大値に設定
        ax.set_ylim(0, max(percentages) * 1.2 if percentages else 100)
        
        plt.tight_layout()
        
        return fig
    
    def create_pitch_effectiveness_chart(self, pitch_type_data: Dict[str, Any]) -> Figure:
        """
        球種別有効性のグラフを作成
        
        Parameters:
        -----------
        pitch_type_data : Dict[str, Any]
            球種別分析データ
            
        Returns:
        --------
        Figure
            Matplotlibのfigure
        """
        self.logger.info("球種別有効性グラフを作成")
        
        # pitch_typesキーがない場合は空図を返す
        if 'pitch_types' not in pitch_type_data or not pitch_type_data['pitch_types']:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.text(0.5, 0.5, 'データがありません', ha='center', va='center')
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
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.text(0.5, 0.5, '有効性データがありません', ha='center', va='center')
            return fig
        
        # 使用率の高い順にソート（usageデータを使用）
        if 'usage' in pitch_type_data:
            # 使用頻度情報に基づいてソート
            effectiveness_data.sort(
                key=lambda x: pitch_type_data['usage'].get(x['pitch_type'], {}).get('percentage', 0), 
                reverse=True
            )
        
        # グラフの作成
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # データの準備
        labels = [d['pitch_type'] for d in effectiveness_data]
        strike_pcts = [d['strike_pct'] for d in effectiveness_data]
        swing_miss_pcts = [d['swing_miss_pct'] for d in effectiveness_data]
        hit_pcts = [d['hit_pct'] for d in effectiveness_data]
        
        # バーの位置
        x = np.arange(len(labels))
        width = 0.25
        
        # 3種類の棒グラフを表示
        ax.bar(x - width, strike_pcts, width, label='ストライク率', color=self.colors['primary'])
        ax.bar(x, swing_miss_pcts, width, label='空振り率', color=self.colors['secondary'])
        ax.bar(x + width, hit_pcts, width, label='被安打率', color=self.colors['quaternary'])
        
        # グラフ設定
        ax.set_xlabel('球種')
        ax.set_ylabel('割合 (%)')
        ax.set_title('球種別有効性指標')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        
        # y軸の範囲を0から適切な最大値に設定
        all_values = strike_pcts + swing_miss_pcts + hit_pcts
        if all_values:
            ax.set_ylim(0, max(all_values) * 1.2)
        
        plt.tight_layout()
        
        return fig
    
    def create_batted_ball_chart(self, batted_ball_data: pd.DataFrame) -> Figure:
        """
        被打球分布のグラフを作成
        
        Parameters:
        -----------
        batted_ball_data : pd.DataFrame
            被打球分析データ
            
        Returns:
        --------
        Figure
            Matplotlibのfigure
        """
        self.logger.info("被打球分布グラフを作成")
        
        if batted_ball_data is None or batted_ball_data.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.text(0.5, 0.5, '被打球データがありません', ha='center', va='center')
            return fig
        
        # 野球場の基本図を描画する関数
        def draw_baseball_field(ax):
            # 内野の描画
            infield = plt.Circle((0, 0), 95, fill=False, color='gray', linestyle='-')
            ax.add_patch(infield)
            
            # 外野の描画（半円）
            outfield = plt.Circle((0, 0), 300, fill=False, color='gray', linestyle='-')
            ax.add_patch(outfield)
            
            # ベースライン
            ax.plot([0, 90], [0, 90], color='gray', linestyle='-')  # 一塁線
            ax.plot([0, -90], [0, 90], color='gray', linestyle='-')  # 三塁線
            
            # 投手マウンド
            mound = plt.Circle((0, 60.5), 9, fill=False, color='gray', linestyle='-')
            ax.add_patch(mound)
            
            # ホームプレート
            home = plt.Rectangle((-8.5, -8.5), 17, 17, fill=False, color='gray')
            ax.add_patch(home)
            
            # 各ベース
            first_base = plt.Rectangle((90-5, 90-5), 10, 10, fill=False, color='gray')
            second_base = plt.Rectangle((0-5, 90*2-5), 10, 10, fill=False, color='gray')
            third_base = plt.Rectangle((-90-5, 90-5), 10, 10, fill=False, color='gray')
            ax.add_patch(first_base)
            ax.add_patch(second_base)
            ax.add_patch(third_base)
        
        # グラフの作成
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 野球場の描画
        draw_baseball_field(ax)
        
        # 座標データの準備
        has_coordinates = 'hc_x' in batted_ball_data.columns and 'hc_y' in batted_ball_data.columns
        
        if has_coordinates:
            # 座標のスケール調整（StatcastのX,Y座標を描画用に変換）
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
                        sizes.append(50)
                    else:
                        # 50-200の範囲でサイズを設定
                        sizes.append(50 + min(150, speed))
            else:
                sizes = [100] * len(x_coords)
            
            # 散布図描画
            scatter = ax.scatter(x_coords, y_coords, c=colors, s=sizes, alpha=0.6)
            
            # 凡例
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='black', markersize=10, label='アウト'),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10, label='シングルヒット'),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='ツーベースヒット'),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='purple', markersize=10, label='スリーベースヒット'),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='ホームラン'),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=10, label='その他/不明')
            ]
            ax.legend(handles=legend_elements, loc='upper right')
        else:
            ax.text(0, 0, '座標データがありません', ha='center', va='center')
        
        # グラフ設定
        ax.set_xlim(-330, 330)
        ax.set_ylim(-50, 400)
        ax.set_title('被打球分布')
        ax.set_aspect('equal')
        ax.grid(False)
        
        # 軸ラベルを消す
        ax.set_xticks([])
        ax.set_yticks([])
        
        plt.tight_layout()
        
        return fig
    
    def create_performance_summary_chart(self, performance_summary: Dict[str, Any]) -> Figure:
        """
        パフォーマンスサマリーのグラフを作成
        
        Parameters:
        -----------
        performance_summary : Dict[str, Any]
            パフォーマンスサマリーデータ
            
        Returns:
        --------
        Figure
            Matplotlibのfigure
        """
        self.logger.info("パフォーマンスサマリーグラフを作成")
        
        if not performance_summary or 'error' in performance_summary:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.text(0.5, 0.5, 'サマリーデータがありません', ha='center', va='center')
            return fig
        
        # グラフの作成（2x2のサブプロット）
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
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
            
            # パイチャート描画
            wedges, texts, autotexts = ax1.pie(
                filtered_counts, 
                labels=filtered_types,
                autopct='%1.1f%%',
                startangle=90,
                colors=sns.color_palette('muted', len(filtered_types))
            )
            
            # テキスト設定
            for text in texts:
                text.set_fontsize(9)
            for autotext in autotexts:
                autotext.set_fontsize(9)
                autotext.set_color('white')
            
            ax1.set_title('球種分布')
        else:
            ax1.text(0.5, 0.5, '球種データがありません', ha='center', va='center', transform=ax1.transAxes)
        
        # 2. 球速ヒストグラム
        if 'velocity' in performance_summary and performance_summary['velocity']:
            velocity_data = performance_summary['velocity']
            
            # ダミーデータ生成（実際は正規分布のデータを生成）
            mean = velocity_data.get('average', 90)
            std = velocity_data.get('std', 2)
            min_v = velocity_data.get('min', mean - 5)
            max_v = velocity_data.get('max', mean + 5)
            
            # 正規分布に従うデータポイントを生成
            velocity_points = np.random.normal(mean, std, 1000)
            velocity_points = velocity_points[(velocity_points >= min_v) & (velocity_points <= max_v)]
            
            # ヒストグラム描画
            ax2.hist(velocity_points, bins=15, alpha=0.7, color=self.colors['primary'])
            
            # 最大・最小・平均速度をプロット
            if 'max' in velocity_data:
                ax2.axvline(velocity_data['max'], color='red', linestyle='--', alpha=0.7, label=f"最高: {velocity_data['max']:.1f} mph")
            if 'average' in velocity_data:
                ax2.axvline(velocity_data['average'], color='green', linestyle='-', alpha=0.7, label=f"平均: {velocity_data['average']:.1f} mph")
            if 'min' in velocity_data:
                ax2.axvline(velocity_data['min'], color='blue', linestyle='--', alpha=0.7, label=f"最低: {velocity_data['min']:.1f} mph")
            
            ax2.set_xlabel('球速 (mph)')
            ax2.set_ylabel('頻度')
            ax2.set_title('球速分布')
            ax2.legend(fontsize=9)
        else:
            ax2.text(0.5, 0.5, '球速データがありません', ha='center', va='center', transform=ax2.transAxes)
        
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
            
            # 棒グラフ描画
            bars = ax3.bar(labels, values, color=sns.color_palette('muted', len(categories)))
            
            # 数値ラベル
            for bar, val in zip(bars, values):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{val}', ha='center', va='bottom', fontsize=9)
            
            ax3.set_ylabel('投球数')
            ax3.set_title('結果分布')
            
            # y軸の調整
            ax3.set_ylim(0, max(values) * 1.2 if values else 10)
        else:
            ax3.text(0.5, 0.5, '結果データがありません', ha='center', va='center', transform=ax3.transAxes)
        
        # 4. ストライク率のゲージ
        if 'outcomes' in performance_summary and 'strike_percentage' in performance_summary['outcomes']:
            strike_pct = performance_summary['outcomes']['strike_percentage']
            
            # ゲージの描画
            gauge_colors = ['red', 'orange', 'yellow', 'yellowgreen', 'green']
            gauge_thresholds = [45, 55, 65, 75, 100]  # ストライク率の閾値
            
            # 該当する色を判定
            gauge_color = gauge_colors[0]
            for i, threshold in enumerate(gauge_thresholds):
                if strike_pct <= threshold:
                    gauge_color = gauge_colors[i]
                    break
            
            # ゲージのプロット (半円)
            theta = np.linspace(0, np.pi, 100)
            r = 1.0
            
            # 半円のベース（グレー）
            ax4.plot(r * np.cos(theta), r * np.sin(theta), color='lightgray', linewidth=20)
            
            # ストライク率に応じたゲージ
            theta_filled = np.linspace(0, np.pi * strike_pct / 100, 100)
            ax4.plot(r * np.cos(theta_filled), r * np.sin(theta_filled), color=gauge_color, linewidth=20)
            
            # テキスト表示
            ax4.text(0, 0, f'{strike_pct:.1f}%', ha='center', va='center', fontsize=24, fontweight='bold')
            ax4.text(0, -0.3, 'ストライク率', ha='center', va='center', fontsize=12)
            
            # 軸設定
            ax4.set_xlim(-1.2, 1.2)
            ax4.set_ylim(-0.5, 1.2)
            ax4.axis('off')
            ax4.set_title('ストライク率')
        else:
            ax4.text(0.5, 0.5, 'ストライク率データがありません', ha='center', va='center', transform=ax4.transAxes)
        
        plt.tight_layout()
        fig.subplots_adjust(wspace=0.3, hspace=0.3)
        
        return fig
    
    def figure_to_base64(self, fig: Figure) -> str:
        """
        matplotlib図をbase64エンコードされた文字列に変換
        
        Parameters:
        -----------
        fig : Figure
            Matplotlibのfigure
            
        Returns:
        --------
        str
            Base64エンコードされた画像データ
        """
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close(fig)  # メモリリーク防止
        
        return img_str