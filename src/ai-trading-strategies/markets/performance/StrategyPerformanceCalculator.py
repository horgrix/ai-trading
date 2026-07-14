import numpy as np
import pandas as pd

import vectorbt as vbt

class StrategyPerformanceCalculator:

    # 总收益率
    PERFORMANCE_TOTAL_RETURN : int = 1
    # 年化收益
    PERFORMANCE_ANN_RETURN : int = 2
    # 年化波动率
    PERFORMANCE_ANN_VOL : int = 3
    # 最大回撤
    PERFORMANCE_MAX_DD : int = 4

    def cal_performance_matrix(self, df: pd.DataFrame, strategies: dict[str, vbt.Portfolio], markets: dict[str, pd.Series], performance: int=PERFORMANCE_TOTAL_RETURN):
        """
        计算所有策略在所有环境下的表现矩阵
        
        Parameters:
        -----------
        strategies : dict - {'策略名': vbt Pportfolio对象}
        markets : dict - {'环境名': 布尔掩码 Series}
        returns : pd.Series - 基准收益率（用于提取环境）
        
        Returns:
        --------
        pd.DataFrame - 行=环境，列=策略，值为年化收益率
        """
        close_rets = df['close'].pct_change()

        performance_data = {}
        
        for market_name, market_mask in markets.items():
            market_perf = {}
            
            for strategy_name, portfolio in strategies.items():
                # 获取策略日收益率
                strategy_rets = portfolio.returns()
                
                # 确保索引对齐
                common_idx = close_rets.index.intersection(market_mask.index).intersection(strategy_rets.index)
                if len(common_idx) < 20:
                    market_perf[strategy_name] = np.nan
                    continue
                
                # 提取该环境下的策略收益
                aligned_mask = market_mask.loc[common_idx]
                aligned_rets = strategy_rets.loc[common_idx]
                market_rets = aligned_rets[aligned_mask].dropna()
                
                if len(market_rets) >= 20:
                    # 计算指标
                    if performance == self.PERFORMANCE_TOTAL_RETURN:
                        # 总收益率
                        market_perf[strategy_name] = (1 + market_rets).prod() - 1
                    elif performance == self.PERFORMANCE_ANN_RETURN:
                        # 年化收益率
                        market_perf[strategy_name] = (1 + market_rets.mean()) ** 252 - 1
                    elif performance == self.PERFORMANCE_ANN_VOL:
                        # 年化波动率
                        market_perf[strategy_name] = market_rets.std() * np.sqrt(252)
                    elif performance == self.PERFORMANCE_MAX_DD:
                        # 最大回撤
                        cumulative = (1 + market_rets).cumprod()
                        market_perf[strategy_name] = (cumulative / cumulative.expanding().max() - 1).min()
                    else:
                        # 日均回报率
                        market_perf[strategy_name] = market_rets.mean()
                else:
                    market_perf[strategy_name] = np.nan
            
            performance_data[market_name] = market_perf
        
        return pd.DataFrame(performance_data).T