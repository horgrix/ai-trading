"""
最坏情况分析
核心概念
不只看平均表现，还要看极端情况下的生存能力。一个年化收益30%的策略，如果在某个环境下跌了50%，依然不可用。

目的：找到策略的"阿喀琉斯之踵"

关键问题：最惨的时候亏多少？持续多久？能扛过去吗？
"""

import pandas as pd
import numpy as np

import vectorbt as vbt

class WorstCasePerformanceCalculator:

    def _calculate_drawdowns_matrix(self, strategy_rets: pd.Series):
        """
        不只是看最大回撤，还要看：
        - 回撤持续时间
        - 恢复时间
        - 回撤频率
        """
        cumulative = (1 + strategy_rets).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        # 找到所有回撤事件
        # 回撤开始：drawdown从0变为负
        # 回撤结束：drawdown从负回到0
        
        is_in_dd = drawdown < 0
        dd_start = is_in_dd & ~is_in_dd.shift(1).fillna(False)
        dd_end = (~is_in_dd) & is_in_dd.shift(1).fillna(False)
        
        dd_starts = dd_start[dd_start].index
        dd_ends = dd_end[dd_end].index
        
        # 分析每次回撤
        dd_events = []
        for start in dd_starts:
            # 找到 start 之后的第一个终点
            future_ends = [e for e in dd_ends if e > start]
            
            if future_ends:
                end = future_ends[0]
            else:
                end = is_in_dd.index[-1]  # 还没结束，用最后一天暂代
            
            duration = (end - start).days
            depth = drawdown.loc[start:end].min()
            recovery = (end - drawdown.loc[start:end].idxmin()).days if depth < 0 else 0
            
            dd_events.append({
                '开始': start,
                '结束': end,
                '持续天数': duration,
                '最大跌幅': depth,
                '是否已恢复': end in dd_ends,  # 标记这次回撤是否真的结束了
                '恢复天数': recovery
            })
        
        dd_df = pd.DataFrame(dd_events)
        
        summary = {
            '最大回撤': dd_df['最大跌幅'].min() if len(dd_df) > 0 else 0,
            '平均回撤': dd_df['最大跌幅'].mean() if len(dd_df) > 0 else 0,
            '最长持续(天)': dd_df['持续天数'].max() if len(dd_df) > 0 else 0,
            '平均持续(天)': dd_df['持续天数'].mean() if len(dd_df) > 0 else 0,
            '回撤次数': len(dd_df)
        }
        
        return summary, dd_df

    def _calculate_var_matrix(self, strategy_rets: pd.Series, confidence=0.95):
        """
        VaR：在给定置信水平下的最大可能亏损
        
        95% VaR = -2% 意味着：
        有95%的把握，单日亏损不会超过2%
        有5%的概率，亏损会超过2%
        """
        var_matrix = {}

        var = np.percentile(strategy_rets, (1 - confidence) * 100)
        var_matrix['var'] = var
        # 取所有小于VaR的收益，计算均值
        tail_returns = strategy_rets[strategy_rets <= var]
        cvar = tail_returns.mean() if len(tail_returns) > 0 else var
        var_matrix['cvar'] = cvar

        return var

    def _calculate_worst_rolling_window_matrix(self, strategy_rets: pd.Series, windows=[1, 5, 20, 60, 252]):
        """
        找出不同时间窗口下的最差表现
        
        最差5日 = -15% 意味着：
        历史上曾经连续5天亏了15%
        """
        worst_performances = {}
        
        for window in windows:
            # rolling_sum = returns.rolling(window).sum()
            # 方法1：复合收益（推荐）
            rolling_compound = (1 + strategy_rets).rolling(window).apply(
                lambda x: x.prod() - 1, raw=False
            )
            worst = rolling_compound.min()
            worst_performances[f'{window}日'] = worst
        
        return pd.Series(worst_performances)

    def cal_crisis_stress(self, strategy: vbt.Portfolio, crisis_periods: dict[str, tuple[str, str]]):
        """
        测试策略在历史重大危机中的表现
        
        crisis_periods: {'危机名': (开始日期, 结束日期)}

        crises = {
            '2018年末暴跌': ('2018-10-01', '2018-12-31'),
            '2020年疫情': ('2020-02-19', '2020-03-23'),
            '2022年加息': ('2022-01-03', '2022-10-12'),
        }
        """
        crisis_results = {}
        strategy_returns = strategy.returns()
        for name, (start, end) in crisis_periods.items():
            period_returns = strategy_returns[start:end]
            
            if len(period_returns) == 0:
                continue
            
            total_return = (1 + period_returns).prod() - 1
            cumulative = (1 + period_returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_dd = drawdown.loc[start:end].min()
            
            crisis_results[name] = {
                '总收益': total_return,
                '最大回撤': max_dd,
                '持续天数': len(period_returns),
                '正收益天数': (period_returns > 0).sum(),
                '负收益天数': (period_returns < 0).sum()
            }
        
        return pd.DataFrame(crisis_results).T

    def cal_worst_case(self, df: pd.DataFrame, strategies: dict[str, vbt.Portfolio], markets: dict[str, pd.Series]):
        """
        找出每个策略的最坏环境，并分析多重不利叠加
        """
        worst_cases = pd.DataFrame()
        
        for market_name, market_mask in markets.items():
            for strat_name, portfolio in strategies.items():
                strategy_rets = portfolio.returns()
                
                # 对齐
                common_idx = df['close'].pct_change().index.intersection(market_mask.index)
                mask = market_mask.loc[common_idx]
                rets = strategy_rets.loc[common_idx]
                market_rets = rets[mask].dropna()
                
                if len(market_rets) < 20:
                    continue
                
                # 计算该环境下的各项指标
                ann_ret = (1 + market_rets.mean()) ** 252 - 1

                # 最大回撤
                drawdowns_matrix, _ = self._calculate_drawdowns_matrix(market_rets)
                max_dd = drawdowns_matrix['最大回撤']
                avg_dd = drawdowns_matrix['平均回撤']
                max_dur_dd = drawdowns_matrix['最长持续(天)']
                avg_dur_dd = drawdowns_matrix['平均持续(天)']
                cnt_dd = drawdowns_matrix['回撤次数']

                # 不同时间窗口下的最差表现
                worst_rolling_window_matrix = self._calculate_worst_rolling_window_matrix(market_rets, windows=[1, 5, 20, 60])
                worst_day = worst_rolling_window_matrix['1日']
                worst_5d = worst_rolling_window_matrix['5日']
                worst_20d = worst_rolling_window_matrix['20日']
                worst_60d = worst_rolling_window_matrix['60日']

                # 
                var_matrix = self._calculate_var_matrix(market_rets, confidence=0.95)
                
                label = f'{strat_name} | {market_name}'
                worst_cases.loc[label, '年化收益'] = ann_ret
                worst_cases.loc[label, '95% var'] = var_matrix
                worst_cases.loc[label, '最大回撤'] = max_dd
                worst_cases.loc[label, '平均回撤'] = avg_dd
                worst_cases.loc[label, '最长持续(天)'] = max_dur_dd
                worst_cases.loc[label, '平均持续(天)'] = avg_dur_dd
                worst_cases.loc[label, '回撤次数'] = cnt_dd
                worst_cases.loc[label, '最差单日'] = worst_day
                worst_cases.loc[label, '最差5日'] = worst_5d
                worst_cases.loc[label, '最差20日'] = worst_20d
                worst_cases.loc[label, '最差60日'] = worst_60d
                worst_cases.loc[label, '样本天数'] = len(market_rets)
        
        return worst_cases