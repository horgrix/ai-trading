import pandas as pd
import pandas_ta as ta

import matplotlib.pyplot as plt

from typing import Any
from strategies.BaseStrategy import BaseStrategy


class RSIOverboughtOversoldStrategy(BaseStrategy):
    """RSI 超买超卖 策略"""

    def __init__(self, period: int=10, oversold: int=25, overbought: int=75):
        """
        参数:
            oversold: 超卖
            overbought: 超买
        """
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.name = f'RSI_OverboughtOversold_({self.period})'

    def get_name(self) -> str:
        return self.name
    
    def get_plot_settings(self) -> dict[str, Any]:
        return {
            self.PLOT_SETTINGS_KEY_CNT: 2, 
            self.PLOT_SETTINGS_KEY_POSITION: "down",
            self.PLOT_SETTINGS_KEY_AX_TITLE: f"RSI({self.period})",
            self.PLOT_SETTINGS_KEY_AX_XLABAL: '统计日期',
            self.PLOT_SETTINGS_KEY_AX_YLABAL: '指标值',
            self.PLOT_SETTINGS_KEY_COLS: [
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: f'RSI_{self.period}',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#7dc3ea',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                }
            ]
        }

    def generate_signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series|pd.DataFrame]:
        """生成交易信号"""

        close = df['close']

        rsi = ta.rsi(close=close, length=self.period)
        entries = rsi < self.oversold
        exits = rsi > self.overbought
        return entries, exits, rsi
    
class RSIDivergenceStrategy(BaseStrategy):
    """RSI 背离 策略"""
    
    VALID_FUNCS = [ta.sma, ta.ema, ta.wma]

    def __init__(self, period: int=10):
        """
        参数:
            oversold: 超卖
            overbought: 超买
        """
        self.period = period
        self.name = f'RSI_Divergence_({self.period})'

    def get_name(self) -> str:
        return self.name
    
    def get_plot_settings(self) -> dict[str, Any]:
        return {
            self.PLOT_SETTINGS_KEY_CNT: 2, 
            self.PLOT_SETTINGS_KEY_POSITION: "down",
            self.PLOT_SETTINGS_KEY_AX_TITLE: f"RSI({self.period})",
            self.PLOT_SETTINGS_KEY_AX_XLABAL: '统计日期',
            self.PLOT_SETTINGS_KEY_AX_YLABAL: '指标值',
            self.PLOT_SETTINGS_KEY_COLS: [
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: f'RSI_{self.period}',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#7dc3ea',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                }
            ]
        }

    def generate_signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series|pd.DataFrame]:
        """生成交易信号"""

        close = df['close']

        rsi = ta.rsi(close=close, length=self.period).rename(f'RSI_{self.period}')
        
        # RSI底背离检测（简化版：价格创新低但RSI未创新低）
        entries = (close == close.rolling(self.period).min()) & (rsi > rsi.rolling(self.period).min().shift(1))
        # RSI顶背离检测（简化版：价格创新高但RSI未创新高）
        exits = (close == close.rolling(self.period).max()) & (rsi < rsi.rolling(self.period).max().shift(1))

        return entries, exits, rsi
    
class MACDCrossStrategy(BaseStrategy):

    def __init__(self, fast: int=12, slow: int=26, signal: int=9):
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.name = f'MACD_Cross_({self.fast},{self.slow},{self.signal})'
        
    def get_name(self):
        return self.name
    
    def get_plot_settings(self) -> dict[str, Any]:
        return {
            self.PLOT_SETTINGS_KEY_CNT: 2, 
            self.PLOT_SETTINGS_KEY_POSITION: "down",
            self.PLOT_SETTINGS_KEY_AX_TITLE: f"MACD({self.fast},{self.slow},{self.signal})",
            self.PLOT_SETTINGS_KEY_AX_XLABAL: '统计日期',
            self.PLOT_SETTINGS_KEY_AX_YLABAL: '指标值',
            self.PLOT_SETTINGS_KEY_COLS: [
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'MACD_F',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#7dc3ea',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                },{
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'MACD_S',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#ffa600',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                },{
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'MACD_H',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.bar,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#f46a64',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 0
                }
            ]
        }

    def generate_signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series|pd.DataFrame]:
        close = df['close']
        macd = ta.macd(close=close, fast=self.fast, slow=self.slow, signal=self.signal).rename(columns={
            f'MACD_{self.fast}_{self.slow}_{self.signal}'  : 'MACD_F',
            f'MACDs_{self.fast}_{self.slow}_{self.signal}' : 'MACD_S',
            f'MACDh_{self.fast}_{self.slow}_{self.signal}' : 'MACD_H'
        })

        entries = (macd['MACD_F'] > macd['MACD_S']) & (macd['MACD_F'].shift(1) <= macd['MACD_S'].shift(1))
        exits = (macd['MACD_F'] < macd['MACD_S']) & (macd['MACD_F'].shift(1) >= macd['MACD_S'].shift(1))
        
        return entries, exits, macd
    
class AOCrossStrategy(BaseStrategy):

    def __init__(self, fast: int=5, slow: int=30):
        self.fast = fast
        self.slow = slow
        self.name = f'AO_Cross_({self.fast},{self.slow})'

    def get_name(self) -> str:
        return self.name
    
    def get_plot_settings(self) -> dict[str, Any]:
        return {
            self.PLOT_SETTINGS_KEY_CNT: 2, 
            self.PLOT_SETTINGS_KEY_POSITION: "down",
            self.PLOT_SETTINGS_KEY_AX_TITLE: f"AO({self.fast},{self.slow})",
            self.PLOT_SETTINGS_KEY_AX_XLABAL: '统计日期',
            self.PLOT_SETTINGS_KEY_AX_YLABAL: '指标值',
            self.PLOT_SETTINGS_KEY_COLS: [
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: f"AO({self.fast},{self.slow})",
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#7dc3ea',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                }
            ]
        }

    def generate_signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series|pd.DataFrame]:
        low = df['low']
        high = df['high']
        ao = ta.ao(high=high, low=low, fast=self.fast, slow=self.slow).rename('AO')
        # AO穿越零轴信号
        # 由负转正，买入
        entries = (ao > 0) & (ao.shift(1) <= 0)
        # 由正转负，卖出
        exits = (ao < 0) & (ao.shift(1) >= 0)

        return entries, exits, ao
    
class MOMDivergenceStrategy(BaseStrategy):

    def __init__(self, period: int=10, windows: int=20):
        self.period = period
        self.windows = windows
        self.name = f'MOM_Divergence_({self.period},{self.windows})'

    def get_name(self) -> str:
        return self.name
    
    def get_plot_settings(self) -> dict[str, Any]:
        return {
            self.PLOT_SETTINGS_KEY_CNT: 2, 
            self.PLOT_SETTINGS_KEY_POSITION: "down",
            self.PLOT_SETTINGS_KEY_AX_TITLE: f"MOM({self.period},{self.windows})",
            self.PLOT_SETTINGS_KEY_AX_XLABAL: '统计日期',
            self.PLOT_SETTINGS_KEY_AX_YLABAL: '指标值',
            self.PLOT_SETTINGS_KEY_COLS: [
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: f"MOM({self.period},{self.windows})",
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#7dc3ea',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                }
            ]
        }

    def generate_signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series|pd.DataFrame]:
        close = df['close']
        mom = ta.mom(close=close, length=self.period).rename('MOM')
        # 能量背离
        # 底背离
        entries = (close == close.rolling(self.windows).min()) & (mom > mom.rolling(self.windows).min().shift(1))
        # 顶背离
        exits = (close == close.rolling(self.windows).max()) & (mom < mom.rolling(self.windows).max().shift(1))
        return entries, exits, mom
