import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt

from typing import Any
from strategies.BaseStrategy import BaseStrategy


class OBVDivergenceStrategy(BaseStrategy):
    """OBV 突破 策略"""

    def __init__(self, period: int=10):
        """
        参数:
            period: N日

        """
        self.period = period
        self.name = f'OBV_Divergence_{self.period}'

    def get_name(self) -> str:
        return self.name
    
    def get_plot_settings(self) -> dict[str, Any]:
        return {
            self.PLOT_SETTINGS_KEY_CNT: 2, 
            self.PLOT_SETTINGS_KEY_POSITION: "down",
            self.PLOT_SETTINGS_KEY_AX_TITLE: f"OBV_Divergence_{self.period}",
            self.PLOT_SETTINGS_KEY_AX_XLABAL: '统计日期',
            self.PLOT_SETTINGS_KEY_AX_YLABAL: '指标值',
            self.PLOT_SETTINGS_KEY_COLS: [
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'OBV',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#97c786',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                }
            ]
        }

    def generate_signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series|pd.DataFrame]:
        """生成交易信号"""

        close = df['close']
        volume = df['volume']
        obv = ta.obv(close=close, volume=volume).rename("OBV")

        # 检测OBV与价格的背离（简化版）
        # 价格创20日新高但OBV未创新高 → 顶背离预警
        max_close = close.rolling(self.period).max()
        max_obv = obv.rolling(self.period).max()
        entries = (close == max_obv) & (obv < max_close.shift(1))
        # 价格创20日新低但OBV未创新低 → 底背离预警
        min_close = close.rolling(self.period).min()
        min_obv = obv.rolling(self.period).min()
        exits = (close == min_close) & (obv > min_obv.shift(1))

        return entries, exits, obv
    

class CMFStrategy(BaseStrategy):
    """查肯资金流 策略"""

    def __init__(self, period: int=20, cashin: float = 0.2, cashout: float=-0.2):
        """
        参数:
            period: N日EMA
        """
        self.period = period
        self.cashin = cashin
        self.cashout = cashout
        self.name = f'CMF_FlowStreth_{self.period}_{self.cashin}_{self.cashout}'

    def get_name(self) -> str:
        return self.name
    
    def get_plot_settings(self) -> dict[str, Any]:
        return {
            self.PLOT_SETTINGS_KEY_CNT: 2, 
            self.PLOT_SETTINGS_KEY_POSITION: "down",
            self.PLOT_SETTINGS_KEY_AX_TITLE: f"CMF_FlowStreth_{self.period}_{self.cashin}_{self.cashout}",
            self.PLOT_SETTINGS_KEY_AX_XLABAL: '统计日期',
            self.PLOT_SETTINGS_KEY_AX_YLABAL: '指标值',
            self.PLOT_SETTINGS_KEY_COLS: [
                {
                    self.PLOT_SETTINGS_KEY_COL_NAME: 'CMF',
                    self.PLOT_SETTINGS_KEY_COL_FUNC: plt.plot,
                    self.PLOT_SETTINGS_KEY_COL_COLOR: '#97c786',
                    self.PLOT_SETTINGS_KEY_COL_TIP: 1
                }
            ]
        }
    
    def generate_signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series|pd.DataFrame]:
        """生成交易信号"""

        low = df['low']
        high = df['high']
        close = df['close']
        volume = df['volume']
        cmf = ta.cmf(high=high, low=low, close=close, volume=volume, length=self.period).rename('CMF')

        entries = cmf > self.cashin
        exits = cmf < self.cashout
        return entries, exits , cmf      
