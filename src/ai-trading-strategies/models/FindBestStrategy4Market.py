import pandas as pd

import vectorbt as vbt

from markets.performance.StrategyPerformanceCalculator import StrategyPerformanceCalculator

class FindBestStrategy4Market:

    def __init__(self):
        self.calculator = StrategyPerformanceCalculator()

    def find_best(self, df: pd.DataFrame, strategies: dict[str, vbt.Portfolio], markets: dict[str, pd.Series]) -> tuple[pd.Series, pd.Series, dict[str, str]]:
        performance_matrix = self.calculator.cal_performance_matrix(df=df, 
                                                                    strategies=strategies, 
                                                                    markets=markets, 
                                                                    performance=StrategyPerformanceCalculator.PERFORMANCE_TOTAL_RETURN)
        # ===== 第一步：计算各环境下的策略表现矩阵 =====
        # 找出每种环境的最佳策略
        best_strategy_per_market = {}
        for market in performance_matrix.index:
            best_strategy_per_market[market] = performance_matrix.loc[market].idxmax()

        # ===== 第二步：实时环境判断 =====
        # 当天属于哪个环境
        current_market = pd.Series('unknown', index=df.index)
        for market_name, market_mask in markets.items():
            aligned_mask = market_mask.reindex(current_market.index, fill_value=False)
            current_market[aligned_mask] = market_name

        # ===== 第三步：根据环境选择策略收益 =====
        strategy_rets_dict = {
            name: portfolio.returns() for name, portfolio in strategies.items()
        }
        
        adaptive_rets = pd.Series(0.0, index=df.index)
        for date in adaptive_rets.index:
            env = current_market.loc[date]
            
            if env in best_strategy_per_market:
                best_strategy = best_strategy_per_market[env]
                
                if (date in strategy_rets_dict[best_strategy].index and 
                    not pd.isna(strategy_rets_dict[best_strategy].loc[date])):
                    adaptive_rets.loc[date] = strategy_rets_dict[best_strategy].loc[date]

        # 计算自适应组合净值
        adaptive_cumulative = (1 + adaptive_rets).cumprod()
        
        return adaptive_rets, adaptive_cumulative, best_strategy_per_market
    
    def find_best_by_weights(self, df: pd.DataFrame, strategies: dict[str, vbt.Portfolio], markets: dict[str, pd.Series]):
        """
        根据各策略在各环境下的历史表现动态分配权重
        
        权重逻辑：
        - 表现越好权重越高
        - 负收益策略不参与
        - 全负则等权
        """
        # ===== 第一步：计算各环境下各策略的表现 =====
        performance_matrix = self.calculator.cal_performance_matrix(df=df, 
                                                            strategies=strategies, 
                                                            markets=markets, 
                                                            performance=StrategyPerformanceCalculator.PERFORMANCE_TOTAL_RETURN)
        
        # ===== 第二步：计算每种环境下的策略权重 =====
        def calculate_env_weights(market_performance: pd.Series):
            """表现越好权重越高，负收益策略权重为0"""
            weights = market_performance.copy()
            weights[weights < 0] = 0
            if weights.sum() > 0:
                weights = weights / weights.sum()
            else:
                weights[:] = 1 / len(weights)
            return weights
        
        market_weights = {}
        for market in performance_matrix.index:
            market_weights[market] = calculate_env_weights(performance_matrix.loc[market])
        
        # ===== 第三步：直接复用 environments 判断当天环境 =====
        current_market = pd.Series('unknown', index=df.index)
        for market_name, market_mask in markets.items():
            aligned_mask = market_mask.reindex(current_market.index, fill_value=False)
            current_market[aligned_mask] = market_name
        
        # ===== 第四步：每日按权重合成收益 =====
        strategy_rets_dict = {
            name: portfolio.returns() for name, portfolio in strategies.items()
        }

        strategy_names = list(strategies.keys())
        adaptive_rets = pd.Series(0.0, index=df.index)
        actual_weights_history = {}  # 记录每天实际使用的权重
        
        for date in adaptive_rets.index:
            market = current_market.loc[date]
            
            if market not in market_weights:
                continue
            
            weights = market_weights[market]
            daily_return = 0.0
            weight_sum = 0.0
            active_strategies = {}
            
            for strategy_name in strategy_names:
                if (date in strategy_rets_dict[strategy_name].index and not pd.isna(strategy_rets_dict[strategy_name].loc[date])):
                    w = weights[strategy_name]
                    daily_return += w * strategy_rets_dict[strategy_name].loc[date]
                    weight_sum += w
                    active_strategies[strategy_name] = w
            
            if weight_sum > 0:
                adaptive_rets.loc[date] = daily_return / weight_sum
                actual_weights_history[date] = {
                    k: v/weight_sum for k, v in active_strategies.items()
                }
        
        adaptive_cumulative = (1 + adaptive_rets).cumprod()
        
        return adaptive_rets, adaptive_cumulative, market_weights, actual_weights_history

