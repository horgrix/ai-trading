"""
环境切换的应对能力
核心概念
策略在市场环境转换时的表现。很多策略在稳定环境里赚钱，但在牛转熊、熊转牛的切换期大幅回撤。

好的策略：切换期回撤可控，能快速适应新环境

差的策略：切换期严重亏损，迟迟无法调整
"""
import pandas as pd
import numpy as np

import vectorbt as vbt

class TransitionsPerformanceCalculator:

    def _find_market_transitions(self, market: pd.Series):
        """
        找到环境切换点
        
        切换分为两种：
        - 进入该环境（0→1）
        - 退出该环境（1→0）
        """
        # 环境状态变化
        env_changes = market.astype(int).diff()
        
        entry_points = market.index[env_changes == 1]   # 进入
        exit_points = market.index[env_changes == -1]   # 退出
        
        return entry_points, exit_points

    def cal_transition(self, strategy: vbt.Portfolio, market: pd.Series, window: int=20):
        """
        切换后分析严格限定在当前环境周期内
        
        进入点 → 只看从进入到退出的区间
        退出点 → 只看从退出到进入的区间
        """
        entry_points, exit_points = self._find_market_transitions(market)
        # 净值
        strategy_returns = strategy.returns()
        cumulative = (1 + strategy_returns).cumprod()
        
        results = []
        
        # 分析进入点
        for entry_date in entry_points:
            if entry_date not in strategy_returns.index:
                continue
            
            idx = strategy_returns.index.get_loc(entry_date)
            
            # 找到对应的退出点
            future_exits = exit_points[exit_points > entry_date]
            if len(future_exits) == 0:
                continue  # 还没有退出，跳过
            
            exit_date = future_exits[0]
            exit_idx = strategy_returns.index.get_loc(exit_date)
            
            # 切换后：最多取 window 天，但不能超过退出点
            actual_window = min(window, exit_idx - idx)
            post_end = idx + actual_window
            
            if actual_window < 5:
                continue

            # 前window天
            pre_start = max(0, idx - window)
            pre_ret = (1 + strategy_returns.iloc[pre_start:idx]).prod() - 1
            
            # 后actual_window天
            post_ret = (1 + strategy_returns.iloc[idx:post_end]).prod() - 1

            # 维度3：切换时的绝对回撤
            current_value = cumulative.iloc[idx]
            historical_max = cumulative.iloc[:idx+1].max()
            drawdown_at_switch = current_value / historical_max - 1

            # 维度4：切换后的净值变化（相对切换点）
            post_value_start = cumulative.iloc[idx]
            post_value_end = cumulative.iloc[post_end - 1] if post_end > idx else post_value_start
            post_value_change = post_value_end / post_value_start - 1

            # 维度5：整个环境周期表现
            cycle_return = cumulative.iloc[exit_idx - 1] / cumulative.iloc[idx] - 1
            
            results.append({
                '类型': '进入',
                '日期': entry_date,
                '前收益': pre_ret,
                '后收益': post_ret,
                '切换时回撤': drawdown_at_switch,
                '切换时净值': current_value,
                '历史最高净值': historical_max,
                '后净值变化': post_value_change,
                '后净值': post_value_end,
                '环境周期收益': cycle_return,
                '实际窗口': actual_window,
                '环境持续天数': exit_idx - idx
            })
    
        # 分析退出点（同理）
        for exit_date in exit_points:
            if exit_date not in strategy_returns.index:
                continue
            
            idx = strategy_returns.index.get_loc(exit_date)
            
            # 找到下一个进入点
            future_entries = entry_points[entry_points > exit_date]
            if len(future_entries) == 0:
                # 没有后续进入，可以取满window
                actual_window = min(window, len(strategy_returns) - idx)
            else:
                next_entry = future_entries[0]
                next_idx = strategy_returns.index.get_loc(next_entry)
                actual_window = min(window, next_idx - idx)
            
            if actual_window < 5:
                continue

            post_end = idx + actual_window
            
            pre_start = max(0, idx - window)
            pre_ret = (1 + strategy_returns.iloc[pre_start:idx]).prod() - 1
            post_ret = (1 + strategy_returns.iloc[idx:post_end]).prod() - 1

            # 切换时的绝对回撤
            current_value = cumulative.iloc[idx]
            historical_max = cumulative.iloc[:idx+1].max()
            drawdown_at_switch = current_value / historical_max - 1
            
            # 切换后的净值变化
            post_value_start = cumulative.iloc[idx]
            post_value_end = cumulative.iloc[post_end - 1] if post_end > idx else post_value_start
            post_value_change = post_value_end / post_value_start - 1
            
            results.append({
                '类型': '退出',
                '日期': exit_date,
                '前收益': pre_ret,
                '后收益': post_ret,
                '切换时回撤': drawdown_at_switch,
                '切换时净值': current_value,
                '历史最高净值': historical_max,
                '后净值变化': post_value_change,
                '后净值': post_value_end,
                '环境周期收益': np.nan,  # 退出点没有完整周期
                '实际窗口': actual_window,
                '环境持续天数': np.nan
            })
        
        return pd.DataFrame(results)
