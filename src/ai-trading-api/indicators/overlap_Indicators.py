import pandas_ta as ta
from pandas import DataFrame


def sma(df_sorted: DataFrame, close: str='close', length=20):
    # ===== 1. SMA (简单移动平均线) =====
    df_sorted = df_sorted.copy()

    required_cols = [close]
    missing = [col for col in required_cols if col not in df_sorted.columns]
    if missing:
        raise ValueError(f"DataFrame 缺少必需列: {missing}")

    sma = ta.sma(close=df_sorted[close], length=length)
    if sma is None:
        return df_sorted
    
    with_sma = df_sorted.join(sma).rename(columns={
        f"SMA_{length}": 'SMA'
    })

    return with_sma

def ema(df_sorted: DataFrame, fast_length=12, slow_length=26):
    # ===== 2. EMA (指数移动平均线) =====
    ema_12 = ta.ema(close=df_sorted['close'], length=fast_length)
    ema_26 = ta.ema(close=df_sorted['close'], length=slow_length)
    if ema_12 is None or ema_26 is None:
        return df_sorted
    with_ema_12 = df_sorted.join(ema_12)
    with_ema_26 = with_ema_12.join(ema_26)

    # ===== 2. EMA 信号 =====
    # MACD核心组件：EMA12 与 EMA26 的交叉
    with_ema_26['EMA_Cross'] = 0
    with_ema_26.loc[
        (with_ema_26['EMA_12'] > with_ema_26['EMA_26']) & 
        (with_ema_26['EMA_12'].shift(1) <= with_ema_26['EMA_26'].shift(1)),
        'EMA_Cross'
    ] = 1
    with_ema_26.loc[
        (with_ema_26['EMA_12'] < with_ema_26['EMA_26']) & 
        (with_ema_26['EMA_12'].shift(1) >= with_ema_26['EMA_26'].shift(1)),
        'EMA_Cross'
    ] = -1

    # 价格与EMA位置关系（更灵敏的趋势判断）
    with_ema_26['EMA_Pos'] = 0
    with_ema_26.loc[with_ema_26['close'] > with_ema_26['EMA_12'], 'EMA_Pos'] = 1
    with_ema_26.loc[with_ema_26['close'] < with_ema_26['EMA_12'], 'EMA_Pos'] =-1

    with_ema_26['EMA_Fast_Trend'] = 0
    with_ema_26.loc[with_ema_26['EMA_12'].shift(1) < with_ema_26['EMA_12'], 'EMA_Fast_Trend'] = 1
    with_ema_26.loc[with_ema_26['EMA_12'].shift(1) > with_ema_26['EMA_12'], 'EMA_Fast_Trend'] =-1

    with_ema_26['EMA_Slow_Trend'] = 0
    with_ema_26.loc[with_ema_26['EMA_26'].shift(1) < with_ema_26['EMA_26'], 'EMA_Slow_Trend'] = 1
    with_ema_26.loc[with_ema_26['EMA_26'].shift(1) > with_ema_26['EMA_26'], 'EMA_Slow_Trend'] =-1

    return with_ema_26