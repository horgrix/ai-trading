"""
市场环境模型
包含：
1. 市场环境：
    牛市
    熊市
2. 波动率：
    高
    低
    收缩
    扩大
3. 市场各类收益率
"""
import pandas as pd
import pandas_ta as ta
import numpy as np

class MarketDefinition:
        
    def market_trend_definition(self, df: pd.DataFrame, bbline_period: int=200, relative_period: int=60) -> pd.Series:

        # 牛熊线
        sma_bbline = ta.sma(df['close'], length=bbline_period)
        # 今日对比N日之前的涨跌幅
        ret_relative = df['close'].pct_change(relative_period)

        market = pd.Series('unknown', index=df['close'].index)
        # 优先级：明确的趋势 > 震荡
        market[(df['close'] > sma_bbline) & (ret_relative > 0.05)]  = 'bull'  # 价格在均线上方且正收益
        market[(df['close'] < sma_bbline) & (ret_relative < -0.05)] = 'bear'  # 价格在均线下方且负收益
        market[market == 'unknown'] = 'neutral'                               # 其余为震荡
        
        return market

    def market_volatility_definition(self, df: pd.DataFrame, period: int=20) -> pd.Series:
        """
        综合判定波动率状态
        返回：'high', 'low', 'normal', 'expanding', 'contracting'
        """
        returns = df['close'].pct_change().dropna()
        vol = returns.rolling(period).std() * np.sqrt(252)
        
        # 绝对水平判定
        vol_high = vol.rolling(252).quantile(0.8)
        vol_low = vol.rolling(252).quantile(0.2)
        
        # 相对变化判定
        vol_short_ma = vol.rolling(int(period / 2)).mean()
        vol_long_ma = vol.rolling(period * 3).mean()
        
        market = pd.Series('normal', index=returns.index)
        market[vol > vol_high] = 'high'
        market[vol < vol_low] = 'low'
        
        # 优先级：绝对水平 > 相对变化
        # 在normal状态下进一步区分扩张/收缩
        normal_mask = market == 'normal'
        market[normal_mask & (vol_short_ma > vol_long_ma * 1.5)] = 'expanding'
        market[normal_mask & (vol_short_ma < vol_long_ma * 0.5)] = 'contracting'
        
        return market
    
    def market_volume_definition(self, df: pd.DataFrame, period: int=20) -> pd.Series:
        """
        expanding, contracting
        """

        volume = df['volume']
        volume_ma = volume.rolling(period).mean()

        market = pd.Series('normal', index=volume.index)
        market[volume > volume_ma * 1.5] = 'expanding'
        market[volume < volume_ma * 0.5] = 'contracting'

        return market   
    
    def market_chop_definition(self, df: pd.DataFrame, period: int=14) -> pd.Series:
        """
        expanding, contracting
        """

        low = df['low']
        high = df['high']
        close= df['close']

        chop = ta.chop(high=high, low=low, close=close, length=period)

        market = pd.Series('neutral', index=close.index)
        market[chop > 61.8] = 'choppy'
        market[chop < 38.2] = 'trending'

        # 优先级：绝对水平 > 相对变化
        # 在neutral状态下进一步区分扩张/收缩
        normal_mask = market == 'neutral'
        market[normal_mask & (chop > chop.shift(1))] = 'trend_weaken'
        market[normal_mask & (chop < chop.shift(1))] = 'trend_enhance'

        return market 
    
    def market_adx_definition(self, df: pd.DataFrame, period: int=14) -> pd.Series:
        """
        expanding, contracting
        """

        low = df['low']
        high = df['high']
        close= df['close']
        adx = ta.adx(high=high, low=low, close=close, length=period).rename(columns={
            f'ADX_{period}' : 'ADX',
            f'DMP_{period}' : 'DMP',
            f'DMN_{period}' : 'DMN'
        })

        market = pd.Series('normal', index=close.index)
        market[(adx['ADX'] > 25) & (adx['DMP'] > adx['DMN'])] = 'strong_up'
        market[(adx['ADX'] > 25) & (adx['DMP'] < adx['DMN'])] = 'strong_down'

        return market 

    # ===== 定义完整的市场环境 =====
    def market_definition(self, df: pd.DataFrame) ->  dict[str, pd.Series]:
        """定义多种市场环境"""
        markets: dict[str, pd.Series] = {}
        
        # 1. 趋势环境
        market_trend = self.market_trend_definition(df)
        markets['牛市'] = market_trend == 'bull'
        markets['熊市'] = market_trend == 'bear'
        markets['振荡市'] = market_trend == 'neutral'
        
        # 2. 波动率环境
        market_vol = self.market_volatility_definition(df)
        markets['高波动'] = market_vol == 'high'
        markets['波动扩张'] = market_vol == 'expanding'
        markets['波动收缩'] = market_vol == 'contracting'
        markets['低波动'] = market_vol == 'low'
        
        # 3. 市场强度（趋势+波动组合）
        markets['牛+高波'] = markets['牛市'] & markets['高波动']
        markets['牛+低波'] = markets['牛市'] & markets['低波动']
        markets['熊+高波'] = markets['熊市'] & markets['高波动']
        markets['熊+低波'] = markets['熊市'] & markets['低波动']
        
        # 4. 回撤环境（市场是否在回撤中）
        drawdown = df['close'] / df['close'].expanding().max() - 1
        markets['市场回撤中'] = drawdown < -0.20  # 从高点跌超10%
        markets['市场创新高'] = drawdown > -0.03  # 接近历史高点
        
        
        return markets
