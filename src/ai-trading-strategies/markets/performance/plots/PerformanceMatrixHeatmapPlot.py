import numpy as np
import pandas as pd
import random

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.axis import Axis

import mplcursors

from markets.performance.StrategyPerformanceCalculator import StrategyPerformanceCalculator
from markets.performance.ConsistencyPerformanceCalculator import ConsistencyPerformanceCalculator
from markets.performance.DependencyPerformanceCalculator import DependencyPerformanceCalculator

import vectorbt as vbt

class PerformanceMatrixHeatmapPlot:


    def _print_value(self, performance_matrix: pd.DataFrame, ax):
        # 添加数值标注
        for row_index in range(len(performance_matrix.index)):
            for col_index in range(len(performance_matrix.columns)):
                value = performance_matrix.iloc[row_index, col_index]
                if not np.isnan(value):
                    text_color = 'white' if abs(value) < 0 else 'black'
                    ax.text(col_index, row_index, f'{value:.2}', ha='center', va='center', 
                                color=text_color, fontsize=9)

    def plot_market_strategy_heatmap(self, df: pd.DataFrame, 
                                     strategies: dict[str, vbt.Portfolio], 
                                     markets: dict[str, pd.Series], 
                                     performance: int=StrategyPerformanceCalculator.PERFORMANCE_TOTAL_RETURN):

        plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
        plt.rcParams['axes.unicode_minus'] = False    # 解决负号 '-' 显示为方块的问题

        # 收益率热力图
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # 定义边界和对应的颜色
        bounds = np.linspace(-1, 2, 11)
        colors = ['#831A21','#A13D3B','#C16D58','#ECD0B4', '#F2EBE5', '#C8D6E7', '#9EBCDB', '#7091C7', '#4E70AF', '#375093']
        # 创建离散颜色映射
        cmap = mcolors.ListedColormap(colors)
        norm = mcolors.BoundaryNorm(bounds, cmap.N)


        # 绘制每个热力图
        strategyPerformanceCalculator = StrategyPerformanceCalculator()
        performance_matrix = strategyPerformanceCalculator.cal_performance_matrix(df=df, 
                                                                                  strategies=strategies, 
                                                                                  markets=markets, 
                                                                                  performance=performance)
        # 定义边界和对应的颜色
        bounds = np.linspace(-1, 2, 11)
        # 创建离散颜色映射
        cmap = mcolors.ListedColormap(colors)
        norm = mcolors.BoundaryNorm(bounds, cmap.N)
        im1 = axes[0, 0].imshow(performance_matrix, cmap=cmap, norm=norm, aspect='auto')
        axes[0, 0].set_title('不同策略在不同环境下的年化收益率')
        axes[0, 0].set_xticks(range(len(performance_matrix.columns)), labels=performance_matrix.columns, rotation=45, rotation_mode="xtick")
        axes[0, 0].set_yticks(range(len(performance_matrix.index)), labels=performance_matrix.index)
        self._print_value(performance_matrix, axes[0, 0])
        # 每个子图单独添加 colorbar
        cbar1 = fig.colorbar(im1, ax=axes[0, 0], shrink=0.6)
        cbar1.set_label('Value')

        time_in_market = pd.Series({
            market_name: market_mask.sum() / len(market_mask) for market_name, market_mask in markets.items()
        })
        market_matrix = time_in_market.to_frame('时长占比')
        # 定义边界和对应的颜色
        bounds = np.linspace(0, 1, 11)
        # 创建离散颜色映射
        cmap = mcolors.ListedColormap(colors)
        norm = mcolors.BoundaryNorm(bounds, cmap.N)
        im2 = axes[0, 1].imshow(market_matrix, cmap=cmap, norm=norm, aspect='auto')
        axes[0, 1].set_title('环境时长与总时长占比')
        axes[0, 1].set_xticks(range(len(market_matrix.columns)), labels=market_matrix.columns, rotation=45, rotation_mode="xtick")
        axes[0, 1].set_yticks(range(len(market_matrix.index)), labels=market_matrix.index)
        self._print_value(market_matrix, axes[0, 1])
        # 每个子图单独添加 colorbar
        cbar2 = fig.colorbar(im2, ax=axes[0, 1], shrink=0.6)
        cbar2.set_label('Value')

        consistencyPerformanceCalculator = ConsistencyPerformanceCalculator()
        consistency_performance_matrix = consistencyPerformanceCalculator.cal_consistency(performance_matrix=performance_matrix, 
                                                                                          consistency=ConsistencyPerformanceCalculator.PERFORMANCE_CV)
        # 定义边界和对应的颜色
        bounds = np.linspace(0, 1, 11)
        # 创建离散颜色映射
        cmap = mcolors.ListedColormap(colors)
        norm = mcolors.BoundaryNorm(bounds, cmap.N)
        im3 = axes[1, 0].imshow(consistency_performance_matrix, cmap=cmap, norm=norm, aspect='auto')
        axes[1, 0].set_title('同一策略在不同环境下一致性')
        axes[1, 0].set_xticks(range(len(consistency_performance_matrix.columns)), labels=consistency_performance_matrix.columns, rotation=45, rotation_mode="xtick")
        axes[1, 0].set_yticks(range(len(consistency_performance_matrix.index)), labels=consistency_performance_matrix.index)
        self._print_value(consistency_performance_matrix, axes[1, 0])
        # 每个子图单独添加 colorbar
        cbar3 = fig.colorbar(im3, ax=axes[1, 0], shrink=0.6)
        cbar3.set_label('Value')

        dependencyPerformanceCalculator = DependencyPerformanceCalculator()
        dependency_performance_matrix = dependencyPerformanceCalculator.cal_dependency(performance_matrix=performance_matrix)
        # 定义边界和对应的颜色
        bounds = np.linspace(0, 1, 11)
        # 创建离散颜色映射
        cmap = mcolors.ListedColormap(colors)
        norm = mcolors.BoundaryNorm(bounds, cmap.N)
        im4 = axes[1, 1].imshow(dependency_performance_matrix, cmap=cmap, norm=norm, aspect='auto')
        axes[1, 1].set_title('同一策略环境依赖性')
        axes[1, 1].set_xticks(range(len(dependency_performance_matrix.columns)), labels=dependency_performance_matrix.columns, rotation=45, rotation_mode="xtick")
        axes[1, 1].set_yticks(range(len(dependency_performance_matrix.index)), labels=dependency_performance_matrix.index)
        self._print_value(dependency_performance_matrix, axes[1, 1])
        # 每个子图单独添加 colorbar
        cbar4 = fig.colorbar(im4, ax=axes[1, 1], shrink=0.6)
        cbar4.set_label('Value')
        
        plt.tight_layout()
        plt.show()

    def plot_market_strategy_radar(self, df: pd.DataFrame, strategies: dict[str, vbt.Portfolio], 
               markets: dict[str, pd.Series], performance: int=StrategyPerformanceCalculator.PERFORMANCE_TOTAL_RETURN):
        """为每个策略画环境适应雷达图（负值范围固定为 -1.2）"""
        
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        strategyPerformanceCalculator = StrategyPerformanceCalculator()
        performance_matrix = strategyPerformanceCalculator.cal_performance_matrix(
            df=df, strategies=strategies, markets=markets, performance=performance
        )
        print(performance_matrix)
        
        n_strategies = len(strategies)
        n_cols = min(4, n_strategies)
        n_rows = (n_strategies + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 5 * n_rows), 
                                subplot_kw=dict(projection='polar'))
        
        if n_strategies == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        market_names = performance_matrix.index.tolist()
        angles = np.linspace(0, 2*np.pi, len(market_names), endpoint=False).tolist()
        angles += angles[:1]

        for idx, (strat_name, _) in enumerate(strategies.items()):
            ax = axes[idx]

            values = performance_matrix[strat_name].tolist()
            values_closed = values + values[:1]
            
            strategy_max = max(values)
            
            # ✅ 固定负值下限，上限根据最大值动态调整
            y_min = -1  # 固定下限
            y_max = max(strategy_max * 1.3, 0.5)  # 上限动态
            
            # 颜色
            is_all_positive = all(v > 0 for v in values)
            is_all_negative = all(v < 0 for v in values)
            
            if is_all_positive:
                color = '#2E8B57'
                fill_color = 'green'
                linestyle = '-'
            elif is_all_negative:
                color = '#DC143C'
                fill_color = 'red'
                linestyle = '--'
            else:
                color = '#FF8C00'
                fill_color = 'orange'
                linestyle = '-.'
            
            # 绘制
            ax.fill(angles, values_closed, alpha=0.2, color=fill_color)
            ax.plot(angles, values_closed, linewidth=2.5, color=color, 
                    linestyle=linestyle, marker='o', markersize=5)
            
            # 零线
            zero_circle = np.linspace(0, 2*np.pi, 100)
            ax.plot(zero_circle, [0]*100, 'k--', linewidth=0.6, alpha=0.5)
            
            # 设置 y 轴
            ax.set_ylim(y_min, y_max)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(market_names, size=8)
            ax.yaxis.set_tick_params(labelsize=6)
            ax.grid(True, alpha=0.3)
            
            # 统计信息
            mean_return = np.mean(values)
            positive_count = sum(1 for v in values if v > 0)
            negative_count = len(values) - positive_count
            
            ax.set_title(f'{strat_name}\n均值: {mean_return:.1%} | 正：{positive_count} 负：{negative_count}', 
                        size=9, pad=20)
        
        # 隐藏多余的子图
        for idx in range(len(strategies), len(axes)):
            axes[idx].set_visible(False)

        plt.tight_layout()
        plt.show()

    def plot_market_strategy_line(self, df: pd.DataFrame, strategies: dict[str, vbt.Portfolio], markets: dict[str, pd.Series], markets_colors: dict[str, str]):
        
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        # ===== 带环境标注的净值曲线 =====
        fig, axes = plt.subplots(3, 1, figsize=(15, 10), 
                                gridspec_kw={'height_ratios': [3, 1, 1]})

        # 子图1：所有策略净值曲线（带环境背景色）
        ax1 = axes[0]
        for name, portfolio in strategies.items():
            (portfolio.value() / portfolio.value().iloc[0]).plot(ax=ax1, label=name, linewidth=1)

        market_durations = {}
        for idx, (market_name, market_mask) in enumerate(markets.items()):
            # 找到连续的环境区间
            market_changes = market_mask.astype(int).diff()
            market_starts = market_mask.index[market_changes == 1]
            market_ends = market_mask.index[market_changes == -1]
            
            for start, end in zip(market_starts, market_ends):
                ax1.axvspan(start, end, alpha=0.15, color=markets_colors[market_name], 
                        label=market_name if start == market_ends[0] else '')
                    
            market_durations[market_name] = market_mask.astype(int) * (idx + 1)

        ax1.set_title('策略净值曲线（带市场环境标注）')
        ax1.legend(loc='upper left', fontsize=8)

        # 子图2：市场环境指示器
        ax2 = axes[1]
        market_indicators = pd.DataFrame(market_durations)
        for market_name in market_indicators.columns:
            index = market_indicators.index[market_indicators[market_name] > 0]
            ax2.scatter(index, market_indicators.loc[index, market_name], 
                        marker='o', label=market_name, s=1, alpha=0.5, color=markets_colors[market_name])
        
        ax2.set_ylim(0, len(markets) + 1)
        ax2.set_yticks([n for n in range(1, len(market_indicators.columns) + 1)])
        ax2.set_yticklabels(markets.keys())
        ax2.set_title('市场环境状态')
        ax2.legend(fontsize=8)

        # 子图3：滚动60日收益率（显示市场节奏）
        ax3 = axes[2]
        rolling_60d = df['close'].pct_change(60)
        rolling_60d.plot(ax=ax3, color='gray', alpha=0.7)
        ax3.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
        ax3.fill_between(rolling_60d.index, 0, rolling_60d, 
                        where=rolling_60d > 0, color='green', alpha=0.3)
        ax3.fill_between(rolling_60d.index, 0, rolling_60d, 
                        where=rolling_60d < 0, color='red', alpha=0.3)
        ax3.set_title('市场滚动60日收益率')
        ax3.set_ylabel('收益率')

        plt.tight_layout()
        plt.show()