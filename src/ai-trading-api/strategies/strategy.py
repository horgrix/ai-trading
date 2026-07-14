import pandas as pd

from indicators.trend_indicators import adx, chop
from indicators.volatility_indicators import donchian, atr
from indicators.mtm_indicators import rsi, roc

class BaseStrategy:

    def __init__(self, df: pd.DataFrame):
        df = df.copy()

        # ATR 用于动态控制仓位
        df = atr(df)
        # 用于判断趋势强度
        df = adx(df)
        # 用于判断市场是趋势市、振荡市还是中性市场
        df = chop(df)
        # donchian 用于查看突破信号
        df = donchian(df)
        # 用于判断突破时动能强度
        df = rsi(df)
        # 用于判断突破时速度
        df = roc(df)

        self.df = df

    def get_close(self, close: str='close') -> pd.DataFrame:

        required_cols = [close]
        missing = [col for col in required_cols if col not in self.df.columns]
        if missing:
            raise ValueError(f"DataFrame 缺少必需列: {missing}")
        
        return self.df[close]
    
    def get_data(self) -> pd.DataFrame:
        return self.df


    def get_entries(self, level: int = 1) -> pd.DataFrame:
        pass

    def get_exits(self, level: int = 1) -> pd.DataFrame:
        pass

    def get_size(self)-> pd.DataFrame:
        pass

class BreakThroughStrategy(BaseStrategy):

    def get_entries(self, level: int = 1) -> pd.DataFrame:
        
        df = self.df

        # 向上突破
        # 突破必须大于 ATR * 2
        donchian_filter = (df['DC_Breakout'] == 1 & ((df['close'] - df['DC_Upper'].shift(1)) >= df['ATR_SL_STOP']))
        # 突破的幅度是否高于5%
        roc_filter = df['ROC'] > df['ATR_SL_STOP'] / df['close'].shift(1)
        # 健康的突破成交量要放大
        volume_filter = (df['volume'] > (df['volume'].rolling(20).mean() * 200))
        # 突破时在强势区间，但不能超买
        rsi_filter = ((df['RSI'] > 50) & (df['RSI'] < 75))
        # 在趋势内突破
        trend_filter = (((df['ADX_Signal'] == 1) & (df['ADX_Direction'] == 1)) | ((df['Market_State'] == 'trending') & (df['CHOP_Direction'] == -1)))

        # 最严格
        filter_up_strict = (
            donchian_filter & 
            # roc_filter &
            volume_filter & 
            rsi_filter &
            trend_filter
        )

        # 最平衡
        filter_up_balanced = (
            volume_filter &
            (roc_filter | rsi_filter | trend_filter)
        )

        # 最便捷
        filter_up_simple = (
            donchian_filter &
            volume_filter
        )

        if level == 1:
            return filter_up_simple
        elif level == 2:
            return filter_up_balanced
        else:
            return filter_up_strict
        
    def get_exits(self, level: int = 1) -> pd.DataFrame:

        df = self.df

        # 向下突破
        donchian_filter = (df['DC_Breakout'] == -1 & ((df['DC_Lower'].shift(1) - df['close']) >= df['ATR_SL_STOP']))
        # 突破的幅度是否大于5%
        roc_filter = df['ROC'] < -10
        # 健康的突破成交量要放大
        volume_filter = df['volume'] > df['volume'].rolling(20).mean() * 1
        # 突破时在强势区间，但不能超卖
        rsi_filter = ((df['RSI'] > 25) & (df['RSI'] < 50))
        # 在趋势内突破
        trend_filter = (((df['ADX_Signal'] == -1) & (df['ADX_Direction'] == 1)) | ((df['Market_State'] == 'trending') & (df['CHOP_Direction'] == -1)))

        # 最严格
        filter_down_strict = (
            donchian_filter & 
            # roc_filter &
            volume_filter & 
            rsi_filter &
            trend_filter
        )

        # 最平衡
        filter_down_balanced = (
            volume_filter &
            (roc_filter | rsi_filter | trend_filter)
        )

        # 最便捷
        filter_down_simple = (
            donchian_filter &
            volume_filter
        )

        if level == 1:
            return filter_down_simple
        elif level == 2:
            return filter_down_balanced
        else:
            return filter_down_strict

    def get_size(self)-> pd.DataFrame:
        pass