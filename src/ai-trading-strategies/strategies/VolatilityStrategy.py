import pandas as pd
import pandas_ta as ta

from typing import Any
import matplotlib.pyplot as plt
from strategies.BaseStrategy import BaseStrategy


class DonchianBreakThroughStrategy(BaseStrategy):
    """唐奇安通道 突破 策略"""

    def __init__(self, upper_period: int=5, lower_period: int=20):
        """
        参数:
            upper_period: N日新高
            lower_period: N日新低
        """
        self.lower_period = lower_period
        self.upper_period = upper_period
        self.name = f'Donchian_BreakThrough_{self.upper_period}_{self.lower_period}'

    def get_name(self) -> str:
        return self.name
    
    def get_plot_settings(self) -> dict[str, Any]:
        return {
            self.PLOT_SETTINGS_KEY_CNT: 1, 
            self.PLOT_SETTINGS_KEY_POSITION: "up",
            self.PLOT_SETTINGS_KEY_COLS: [
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'DC_Upper',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#97c786',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                },
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'DC_Middle',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#ffa600',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 0
                },
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'DC_Lower',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#f46a64',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                }
            ]
        }

    def generate_signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series|pd.DataFrame]:
        """生成交易信号"""

        close = df['close']
        """唐奇安通道"""
        indicator_upper  = f'DCU_{self.lower_period}_{self.upper_period}'
        indicator_middle = f'DCM_{self.lower_period}_{self.upper_period}'
        indicator_lower  = f'DCL_{self.lower_period}_{self.upper_period}'
        donchian = ta.donchian(high=df['high'], low=df['low'], lower_length=self.lower_period, upper_length=self.upper_period).rename(columns={
            indicator_upper : 'DC_Upper',
            indicator_middle: 'DC_Middle',
            indicator_lower : 'DC_Lower'
        })

        entries = (close > donchian['DC_Upper'].shift(1))
        exits = (close < donchian['DC_Lower'].shift(1))
        return entries, exits, donchian
    

class BBandsVolatilityExpandSqueezeStrategy(BaseStrategy):
    """布林通道 波动率扩张收缩 策略"""

    def __init__(self, period: int=20, std: int=2):
        """
        参数:
            period: N日EMA
            std: 标准差
        """
        self.period = period
        self.std = std
        self.name = f'BBands_ExpandSqueeze_{period}_{std}'

    def get_name(self) -> str:
        return self.name
    
    def get_plot_settings(self) -> dict[str, Any]:
        return {
            self.PLOT_SETTINGS_KEY_CNT: 1, 
            self.PLOT_SETTINGS_KEY_POSITION: "up",
            self.PLOT_SETTINGS_KEY_COLS: [
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'BB_Upper',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#97c786',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                },
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'BB_Middle',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#ffa600',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 0
                },
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'BB_Lower',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#f46a64',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                }
            ]
        }

    def generate_signals(self, df: pd.DataFrame)  -> tuple[pd.Series, pd.Series, pd.Series|pd.DataFrame]:
        """生成交易信号"""

        close = df['close']
        indicator_upper  = f'BBU_{self.period}_{self.std}.0_{self.std}.0'
        indicator_middle = f'BBM_{self.period}_{self.std}.0_{self.std}.0'
        indicator_lower  = f'BBL_{self.period}_{self.std}.0_{self.std}.0'
        bbands = ta.bbands(close=close, length=self.period, std=self.std).rename(columns={
            indicator_upper:  'BB_Upper',
            indicator_middle: 'BB_Middle',
            indicator_lower:  'BB_Lower'
        })

        width = bbands['BB_Upper'] - bbands['BB_Lower']
        width_ma = width.rolling(self.period).mean()
        entries = (width <= width_ma * 0.8) & (close <= bbands['BB_Lower'])
        exits = (width >= width_ma * 1.2) & (close >= bbands['BB_Upper'])
        return entries, exits, bbands        
