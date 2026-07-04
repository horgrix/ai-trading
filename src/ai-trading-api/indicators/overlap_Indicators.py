import pandas_ta as ta
from pandas import DataFrame


def sma(df_sorted: DataFrame):
    # ===== 1. SMA (简单移动平均线) =====
    sma_20 = ta.sma(close=df_sorted['close'], length=20)
    sma_50 = ta.sma(close=df_sorted['close'], length=50)
    sma_200 = ta.sma(close=df_sorted['close'], length=200)
    with_sma_20 = df_sorted.join(sma_20)
    with_sma_50 = with_sma_20.join(sma_50)
    with_sma_200 = with_sma_50.join(sma_200)

    # ===== 1. SMA 信号 =====
    # 双均线交叉（黄金交叉/死亡交叉）
    with_sma_200['SMA_Cross'] = 0
    # 金叉：SMA20 上穿 SMA50（买入）
    with_sma_200.loc[
        (with_sma_200['SMA_20'] > with_sma_200['SMA_50']) & 
        (with_sma_200['SMA_20'].shift(1) <= with_sma_200['SMA_50'].shift(1)),
        'SMA_Cross'
    ] = 1
    # 死叉：SMA20 下穿 SMA50（卖出）
    with_sma_200.loc[
        (with_sma_200['SMA_20'] < with_sma_200['SMA_50']) & 
        (with_sma_200['SMA_20'].shift(1) >= with_sma_200['SMA_50'].shift(1)),
        'SMA_Cross'
    ] = -1

    # 价格与SMA位置关系
    with_sma_200['SMA_Trend'] = 0
    with_sma_200.loc[with_sma_200['close'] > with_sma_200['SMA_20'], 'SMA_Trend'] = 1    # 价格在MA之上，上升趋势
    with_sma_200.loc[with_sma_200['close'] < with_sma_200['SMA_20'], 'SMA_Trend'] = -1   # 价格在MA之下，下降趋势

    # 长期牛熊判断（MA200）
    with_sma_200['Long_Trend'] = 0
    with_sma_200.loc[with_sma_200['close'] > with_sma_200['SMA_200'], 'Long_Trend'] = 1   # 牛市
    with_sma_200.loc[with_sma_200['close'] < with_sma_200['SMA_200'], 'Long_Trend'] = -1  # 熊市

    return with_sma_200

def ema(df_sorted: DataFrame):
    # ===== 2. EMA (指数移动平均线) =====
    ema_12 = ta.ema(close=df_sorted['close'], length=12)
    ema_26 = ta.ema(close=df_sorted['close'], length=26)
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
    with_ema_26['EMA_Trend'] = 0
    with_ema_26.loc[with_ema_26['close'] > with_ema_26['EMA_12'], 'EMA_Trend'] = 1
    with_ema_26.loc[with_ema_26['close'] < with_ema_26['EMA_12'], 'EMA_Trend'] = -1

    return with_ema_26

def wma(df_sorted: DataFrame):
    # ===== 3. WMA (加权移动平均线) =====
    wma_20 = ta.wma(close=df_sorted['close'], length=20)
    with_wma_20 = df_sorted.join(wma_20)

    # ===== 3. WMA 信号 =====
    with_wma_20['WMA_Signal'] = 0
    with_wma_20.loc[with_wma_20['close'] > with_wma_20['WMA_20'], 'WMA_Signal'] = 1
    with_wma_20.loc[with_wma_20['close'] < with_wma_20['WMA_20'], 'WMA_Signal'] = -1

    return with_wma_20

def hma(df_sorted: DataFrame):
    # ===== 4. HMA (哈尔移动平均线) =====
    hma_20 = ta.hma(close=df_sorted['close'], length=20)
    with_hma_20 = df_sorted.join(hma_20)

    # ===== 4. HMA 信号 =====
    # HMA转向信号（极低滞后，适合短线）
    with_hma_20['HMA_Direction'] = 0
    with_hma_20.loc[with_hma_20['HMA_20'] > with_hma_20['HMA_20'].shift(1), 'HMA_Direction'] = 1   # 上升
    with_hma_20.loc[with_hma_20['HMA_20'] < with_hma_20['HMA_20'].shift(1), 'HMA_Direction'] = -1  # 下降

    # HMA与价格交叉信号
    with_hma_20['HMA_Cross'] = 0
    with_hma_20.loc[
        (with_hma_20['close'] > with_hma_20['HMA_20']) & 
        (with_hma_20['close'].shift(1) <= with_hma_20['HMA_20'].shift(1)),
        'HMA_Cross'
    ] = 1
    with_hma_20.loc[
        (with_hma_20['close'] < with_hma_20['HMA_20']) & 
        (with_hma_20['close'].shift(1) >= with_hma_20['HMA_20'].shift(1)),
        'HMA_Cross'
    ] = -1

    return with_hma_20

def kama(df_sorted: DataFrame):
    # ===== 6. KAMA (卡夫曼自适应移动平均线) =====
    kama_20 = ta.kama(close=df_sorted['close'], length=20).rename('KAMA_20')
    with_kama_20 = df_sorted.join(kama_20)

    # ===== 6. KAMA 信号 =====
    with_kama_20['KAMA_Signal'] = 0
    with_kama_20.loc[with_kama_20['close'] > with_kama_20['KAMA_20'], 'KAMA_Signal'] = 1    # 价格在KAMA之上，多头
    with_kama_20.loc[with_kama_20['close'] < with_kama_20['KAMA_20'], 'KAMA_Signal'] = -1   # 价格在KAMA之下，空头

    # KAMA方向变化（自适应趋势捕捉）
    with_kama_20['KAMA_Direction'] = 0
    with_kama_20.loc[with_kama_20['KAMA_20'] > with_kama_20['KAMA_20'].shift(1), 'KAMA_Direction'] = 1
    with_kama_20.loc[with_kama_20['KAMA_20'] < with_kama_20['KAMA_20'].shift(1), 'KAMA_Direction'] = -1

    return with_kama_20