import pandas_ta as ta
from pandas import DataFrame


def atr(df_sorted: DataFrame, high: str='high', low: str='low', close: str='close', length: int=14):
    # ===== 1. ATR (平均真实波幅) =====
    # ATR值越高，代表市场波动越剧烈；ATR值越低，则市场越低迷。但ATR本身不提供买卖信号，只描述波动状态
    df_sorted = df_sorted.copy()

    required_cols = [high, low, close]
    missing = [col for col in required_cols if col not in df_sorted.columns]
    if missing:
        raise ValueError(f"DataFrame 缺少必需列: {missing}")
    
    atr = ta.atr(high=df_sorted[high], low=df_sorted[low], close=df_sorted[close], length=length)
    if atr is None:
        return df_sorted
    
    with_atr = df_sorted.join(atr).rename(columns={
        f'ATRr_{length}': 'ATR'
    })
    
    # ===== 1. ATR 信号 =====
    # ATR动态止损和止盈
    with_atr['ATR_SL_STOP'] = with_atr['ATR'] * 2    # 2倍ATR止损
    with_atr['ATR_TP_STOP'] = with_atr['ATR'] * 4    # 4倍ATR止盈

    return with_atr
    
def bbands(df_sorted: DataFrame, close: str='close', length: int=20, std: int=2):
    # ===== 5. BBANDS (布林带) =====

    df_sorted = df_sorted.copy()
    required_cols = [close]
    missing = [col for col in required_cols if col not in df_sorted.columns]
    if missing:
        raise ValueError(f"DataFrame 缺少必需列: {missing}")
    
    bbands = ta.bbands(close=df_sorted[close], length=length, std=std)
    if bbands is None:
        return df_sorted
    
    indicator_upper  = f'BBU_{length}_{std}.0_{std}.0'
    indicator_middle = f'BBM_{length}_{std}.0_{std}.0'
    indicator_lower  = f'BBL_{length}_{std}.0_{std}.0'

    with_bbands = df_sorted.join(bbands)
    # 列名: BBU_20_2.0 (上轨), BBM_20_2.0 (中轨), BBL_20_2.0 (下轨), BBB_20_2.0 (带宽百分比)
    # 重命名为更简洁的名称
    with_bbands = with_bbands.rename(columns={
        indicator_upper:  'BB_Upper',
        indicator_middle: 'BB_Middle',
        indicator_lower:  'BB_Lower'
    })

    # ===== 5. BBANDS 信号 =====
    # 布林带经典策略：触及上下轨
    with_bbands['BB_Trade_Signal'] = 0
    with_bbands.loc[with_bbands['close'] <= with_bbands['BB_Lower'], 'BB_Trade_Signal'] = 1    # 触及下轨，超卖，潜在买入
    with_bbands.loc[with_bbands['close'] >= with_bbands['BB_Upper'], 'BB_Trade_Signal'] = -1   # 触及上轨，超买，潜在卖出

    # 布林带宽度（波动率指标）
    with_bbands['BB_Width'] = (with_bbands['BB_Upper'] - with_bbands['BB_Lower']) / with_bbands['BB_Middle']
    with_bbands['BB_Width_MA'] = with_bbands['BB_Width'].rolling(20).mean()
    with_bbands['BB_State'] = 0
    with_bbands.loc[with_bbands['BB_Width'] < (with_bbands['BB_Width_MA'] * 0.8), 'BB_State'] =-1 # 带宽收缩预示变盘（带宽低于过去20日均值*0.8）
    with_bbands.loc[with_bbands['BB_Width'] > (with_bbands['BB_Width_MA'] * 1.2), 'BB_State'] = 1 # 布林带扩张（趋势加速）

    # 中轨方向
    with_bbands['BB_Middle_Direction'] = 0
    with_bbands.loc[with_bbands['BB_Middle'] > with_bbands['BB_Middle'].shift(1), 'BB_Middle_Direction'] = 1
    with_bbands.loc[with_bbands['BB_Middle'] < with_bbands['BB_Middle'].shift(1), 'BB_Middle_Direction'] =-1

    return with_bbands

def donchian(df_sorted: DataFrame, high: str='high', low: str='low', length: int=20):
    # ===== 4. DONCHIAN (唐奇安通道) =====
    """
    上轨 (Upper Band)：过去N个周期的最高价（即 N日最高价的最高值）。
    下轨 (Lower Band)：过去N个周期的最低价（即 N日最低价的最低值）。
    中轨 (Middle Band)：上轨和下轨的平均值（即 (上轨 + 下轨) / 2）。
    它的核心就是看价格是否突破了前期的重要高点或低点。默认参数通常为 N=20。
    """
    df_sorted = df_sorted.copy()

    required_cols = [high, low]
    missing = [col for col in required_cols if col not in df_sorted.columns]
    if missing:
        raise ValueError(f"DataFrame 缺少必需列: {missing}")
    
    donchian = ta.donchian(high=df_sorted[high], low=df_sorted[low], length=length)
    if donchian is None:
        return df_sorted
    with_donchian = df_sorted.join(donchian)
    indicator_upper  = f'DCU_{length}_{length}'
    indicator_middle = f'DCM_{length}_{length}'
    indicator_lower  = f'DCL_{length}_{length}'
    with_donchian = with_donchian.rename(columns={
        indicator_upper : 'DC_Upper',
        indicator_middle: 'DC_Middle',
        indicator_lower : 'DC_Lower'
    })

    # ===== 4. DONCHIAN 信号 =====
    # 唐奇安通道突破（海龟交易法核心）
    with_donchian['DC_Breakout'] = 0
    with_donchian.loc[with_donchian['close'] > with_donchian['DC_Upper'].shift(1), 'DC_Breakout'] = 1  # 创20日新高，买入信号
    with_donchian.loc[with_donchian['close'] < with_donchian['DC_Lower'].shift(1), 'DC_Breakout'] =-1  # 创20日新低，卖出信号

    return with_donchian