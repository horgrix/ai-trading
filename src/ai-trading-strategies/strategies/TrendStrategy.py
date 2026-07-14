import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from typing import Any, Callable

from strategies.BaseStrategy import BaseStrategy

class DualMovingAverageCrossStrategy(BaseStrategy):
    """双均线趋势跟踪策略"""
    
    VALID_FUNCS = [ta.sma, ta.ema, ta.wma]

    def __init__(self, func: Callable, fast: int=20, slow: int=50):
        """
        参数:
            fast: 短期均线周期
            long_window: 长期均线周期
        """
        
        if func not in self.VALID_FUNCS:
            raise ValueError(f"不支持该函数: {func.__name__}")

        self.fast = fast
        self.slow = slow
        self.func = func
        self.name = f'{self.func.__name__.upper}_Cross_({self.fast},{self.slow})'

    def get_name(self) -> str:
        return self.name
    
    def get_plot_settings(self) -> dict[str, Any]:
        return {
            self.PLOT_SETTINGS_KEY_CNT: 1, 
            self.PLOT_SETTINGS_KEY_POSITION: "up",
            self.PLOT_SETTINGS_KEY_COLS: [
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: f'{self.func.__name__.upper()}_{self.fast}',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#97c786',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 0
                },
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: f'{self.func.__name__.upper()}_{self.slow}',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#f46a64',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 0
                }
            ]
        }
    
    def generate_signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series|pd.DataFrame]:
        """生成交易信号"""

        close = df['close']

        # 计算两条移动平均线
        fast_ma: pd.Series = self.func(close=close, length=self.fast).rename(f'{self.func.__name__.upper()}_{self.fast}')
        slow_ma: pd.Series = self.func(close=close, length=self.slow).rename(f'{self.func.__name__.upper()}_{self.slow}')
        ma = pd.concat([fast_ma, slow_ma], axis=1)
        entries = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
        exits = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))
        return entries, exits, ma
    

class PsarCrossStrategy(BaseStrategy):
    """PSAR (抛物线停损反转指标)策略"""
    
    VALID_FUNCS = [ta.sma, ta.ema, ta.wma]

    def __init__(self, af=0.02, max_af=0.2):
        """
        参数:
            af: 短期均线周期
            max_af: 长期均线周期
            参数调整：参数 0.02/0.2 是经典默认值。若想信号更灵敏（更早出场），可以调大起始值，比如 af=0.03；若想信号更迟钝（持仓更久），可以调小起始值，比如 af=0.015。
        """

        self.af = af
        self.max_af = max_af
        self.name = f'PSAR_Cross_({self.af},{self.max_af})'
        
    def get_name(self) -> str:
        return self.name
    
    def get_plot_settings(self) -> dict[str, Any]:
        return {
            self.PLOT_SETTINGS_KEY_CNT: 2, 
            self.PLOT_SETTINGS_KEY_POSITION: "down",
            self.PLOT_SETTINGS_KEY_AX_TITLE: f"PSAR_Cross_({self.af},{self.max_af})",
            self.PLOT_SETTINGS_KEY_AX_XLABAL: '统计日期',
            self.PLOT_SETTINGS_KEY_AX_YLABAL: '指标值',
            self.PLOT_SETTINGS_KEY_COLS: [
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'PSAR_Long_Stop',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#97c786',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                },
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'PSAR_Short_Stop',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#f46a64',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                }
            ]
        }

    def generate_signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series|pd.DataFrame]:
        """生成交易信号"""

        low   = df['low']
        high  = df['high']
        close = df['close']
        psar_df = ta.psar(high=high, low=low, close=close, af=self.af, max_af=self.max_af, append=True)
        if psar_df is None:
            return df
        psar_df = psar_df[['PSARl_0.02_0.2', 'PSARs_0.02_0.2']].rename(columns={
            f'PSARl_{self.af}_{self.max_af}': 'PSAR_Long_Stop',
            f'PSARs_{self.af}_{self.max_af}': 'PSAR_Short_Stop'
        })

        entries = (close > psar_df['PSAR_Long_Stop']) & (close.shift(1) < psar_df['PSAR_Short_Stop'].shift(1))
        exits = (close < psar_df['PSAR_Short_Stop']) & (close.shift(1) > psar_df['PSAR_Long_Stop'].shift(1))
        return entries, exits, psar_df
    
class ADXDmpDmnCrossStrategy(BaseStrategy):

    def __init__(self, period: int=14):
        self.period = period
        self.name = f'ADX_DmpDmnCross_({self.period})'

    def get_name(self) -> str:
        return self.name
    
    def get_plot_settings(self) -> dict[str, Any]:
        return {
            self.PLOT_SETTINGS_KEY_CNT: 2, 
            self.PLOT_SETTINGS_KEY_POSITION: "down",
            self.PLOT_SETTINGS_KEY_AX_TITLE: f'ADX_DmpDmnCross_({self.period})',
            self.PLOT_SETTINGS_KEY_AX_XLABAL: '统计日期',
            self.PLOT_SETTINGS_KEY_AX_YLABAL: '指标值',
            self.PLOT_SETTINGS_KEY_COLS: [
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'ADX',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#7dc3ea',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                },
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'DMP',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#97c786',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                },
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'DMN',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#f46a64',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                }
            ]
        }

    def generate_signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series|pd.DataFrame]:
        low   = df['low']
        high  = df['high']
        close = df['close']
        adx = ta.adx(high=high, low=low, close=close, length=self.period).rename(columns={
            f'ADX_{self.period}' : 'ADX',
            f'DMP_{self.period}' : 'DMP',
            f'DMN_{self.period}' : 'DMN'
        })

        # +DI 和 -DI 交叉信号
        # +DI上穿-DI，买入
        entries = (adx['DMP'] > adx['DMN']) & (adx['DMP'].shift(1) <= adx['DMN'].shift(1))
        # -DI上穿+DI，卖出
        exits = (adx['DMP'] < adx['DMN']) & (adx['DMP'].shift(1) >= adx['DMN'].shift(1))

        return entries, exits, adx
