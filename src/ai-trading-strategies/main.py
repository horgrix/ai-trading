import pandas as pd
import pandas_ta as ta

import vectorbt as vbt

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from dao import get_dao_manager
from database.ai_trading_db import connection

import strategies.factory.StrategyFactory as sf

from markets.MarketDefinition import MarketDefinition
from markets.performance.StrategyPerformanceCalculator import StrategyPerformanceCalculator
from markets.performance.ConsistencyPerformanceCalculator import ConsistencyPerformanceCalculator
from markets.performance.DependencyPerformanceCalculator import DependencyPerformanceCalculator
from markets.performance.TransitionsPerformanceCalculator import TransitionsPerformanceCalculator
from markets.performance.WorstCasePerformanceCalculator import WorstCasePerformanceCalculator
from markets.performance.plots.PerformanceMatrixHeatmapPlot import PerformanceMatrixHeatmapPlot

from models.FindBestStrategy4Market import FindBestStrategy4Market

df = pd.DataFrame()
manager = get_dao_manager()
with connection() as conn:
    df = manager.stocks.load_stock_data(conn, symbol='02400', type='daily', start_date='2019-01-01', end_date='2026-07-10')
market_returns = df['close'].pct_change()

collections = {
    "最高价": df['high'], 
    "收盘价": df['close'], 
    "最低价": df['low']
}

# 策略：买入持有
holding_strategies: dict[str ,vbt.Portfolio] = sf.create_holding_strategy(df=df)
# # 策略：RSI 超买超卖
# ris_obos_strategies: dict[str ,vbt.Portfolio]  = sf.create_rsi_overboughtoversold_strategy(df=df, periods=[5, 10, 15])
# 策略：RSI 背离策略
ris_div_strategies: dict[str ,vbt.Portfolio]  = sf.create_rsi_divergence_strategy(df=df, periods=[5, 10, 15])
# # 策略：SMA 双均线交叉策略
# sma_cross_strategies: dict[str ,vbt.Portfolio]  = sf.create_dualmovingaverage_cross_strategy(df=df)
# # 策略：PASR 交叉策略
# pasr_cross_strategies: dict[str ,vbt.Portfolio]  = sf.create_psar_cross_strategy(df=df)
# # 策略：donchian 突破策略
# donchian_breakthrough_strategies: dict[str ,vbt.Portfolio]  = sf.create_donchian_breakthrough_strategy(df=df)

# 选择策略
choice_strategies = holding_strategies | ris_div_strategies

# 市场
market_definition = MarketDefinition()
markets: dict[str, pd.Series] = market_definition.market_definition(df=df)
# ===== 使用示例 =====
# 定义环境
choice_markets = {
    '牛市': markets['牛市'],
    '熊市': markets['熊市'],
    '高波动': markets['高波动'],
    '低波动': markets['低波动']
}

markets_colors = {
    '牛市': '#4DBBD5',
    '熊市': '#8A8A8A',
    '高波动': '#FF7F0E',
    '低波动': '#E0E0E0'
}


# adaptive_rets, adaptive_cumulative, market_weights, actual_weights_history = FindBestStrategy4Market().find_best_by_weights(df=df, strategies=ris_div_strategies, markets=choice_markets)
# print(market_weights)
# print()
# 计算性能表现
# basePerformanceCalculator = StrategyPerformanceCalculator()
# base_performance_matrix = basePerformanceCalculator.cal_performance_matrix(df=df, 
#                                                                            strategies=choice_strategies, 
#                                                                            markets=choice_markets, 
#                                                                            performance=StrategyPerformanceCalculator.PERFORMANCE_ANN_RETURN)
# print(base_performance_matrix)
# consistencyPerformanceCalculator = ConsistencyPerformanceCalculator()
# consistency_performance_matrix = consistencyPerformanceCalculator.cal_consistency(performance_matrix=base_performance_matrix, 
#                                                                                   consistency=ConsistencyPerformanceCalculator.PERFORMANCE_CV)
# print(consistency_performance_matrix)
# dependencyPerformanceCalculator = DependencyPerformanceCalculator()
# dependency_performance_matrix = dependencyPerformanceCalculator.cal_dependency(performance_matrix=base_performance_matrix)
# print(dependency_performance_matrix)

# transitionsPerformanceCalculator = TransitionsPerformanceCalculator()
# transitions_performance_matrix = transitionsPerformanceCalculator.cal_transition(strategy=choice_strategies['Holding'], market=choice_markets['牛市'])
# print(transitions_performance_matrix)

# 定义历史危机
# crises = {
#     '2018年末暴跌': ('2018-10-01', '2018-12-31'),
#     '2020年疫情': ('2020-02-19', '2020-03-23'),
#     '2022年加息': ('2022-01-03', '2022-10-12'),
# }
# worstcasePerformanceCalculator = WorstCasePerformanceCalculator()
# worstcase_performance_matrix = worstcasePerformanceCalculator.cal_worst_case(df=df, strategies=choice_strategies, markets=choice_markets)
# print(worstcase_performance_matrix)
PerformanceMatrixHeatmapPlot().plot_ts(df=df,strategies=choice_strategies, markets=choice_markets, markets_colors=markets_colors)
