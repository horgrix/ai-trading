import pandas_ta as ta
from pandas import DataFrame



def obv(df_sorted: DataFrame, close: str='close', volume: str='volume', length=20):
    # 1. OBV (平衡成交量)
    # 核心作用：追踪主力资金流向。它通过将成交量与价格涨跌相结合，判断资金的净流入或净流出。核心逻辑是：价格变化需要成交量确认。
    # 用法：OBV 趋势与价格趋势同步，确认趋势健康；如果价格创新高但 OBV 未创新高，形成 “顶背离”，可能预示上涨动力不足，是风险信号。

    df_sorted = df_sorted.copy()

    required_cols = [close, volume]
    missing = [col for col in required_cols if col not in df_sorted.columns]
    if missing:
        raise ValueError(f"DataFrame 缺少必需列: {missing}")

    obv = ta.obv(close=df_sorted[close], volume=df_sorted[volume])
    if obv is None:
        return df_sorted
    with_obv = df_sorted.join(obv)
    # with_obv['OBV_ZScore'] = (with_obv['OBV'] - with_obv['OBV'].rolling(100).mean()) / with_obv['OBV'].rolling(100).std()
    
    indicator_name = f"OBV_MA{length}"

    # ----- 1. OBV 信号：趋势确认与背离 -----
    # OBV上升趋势：OBV > 其20日均线
    with_obv[indicator_name] = with_obv['OBV'].rolling(length).mean()
    with_obv['OBV_Signal'] = 0
    with_obv.loc[with_obv['OBV'] > with_obv[indicator_name], 'OBV_Signal'] = 1   # 资金流入
    with_obv.loc[with_obv['OBV'] < with_obv[indicator_name], 'OBV_Signal'] = -1  # 资金流出

    # 检测OBV与价格的背离（简化版）
    with_obv['OBV_Divergence_Signal'] = 0
    # 价格创20日新高但OBV未创新高 → 顶背离预警
    with_obv[f'Price_{length}_High'] = with_obv['close'].rolling(length).max()
    with_obv[f'OBV_{length}_High'] = with_obv['OBV'].rolling(length).max()
    with_obv.loc[(
        (with_obv['close'] == with_obv[f'Price_{length}_High']) & 
        (with_obv['OBV'] < with_obv[f'OBV_{length}_High'].shift(1))
    ), 'OBV_Divergence_Signal'] = 1

    # 价格创20日新低但OBV未创新低 → 底背离预警
    with_obv[f'Price_{length}_Low'] = with_obv['close'].rolling(length).min()
    with_obv[f'OBV_{length}_Low'] = with_obv['OBV'].rolling(length).min()
    with_obv.loc[(
        (with_obv['close'] == with_obv[f'Price_{length}_Low']) & 
        (with_obv['OBV'] > with_obv[f'OBV_{length}_Low'].shift(1))
    ), 'OBV_Divergence_Signal'] = -1

    return with_obv

def mfi(df_sorted: DataFrame, high: str='high', low: str='low', close: str='close', volume: str='volume', length=14):
    # 2. MFI (资金流量指数) - 默认周期14
    # 核心作用：判断超买超卖区域。它常被称为“成交量加权的 RSI”，同时考虑了价格和成交量，能更真实地反映市场热度。
    # 用法：数值 > 80 为超买（价格可能过高），数值 < 20 为超卖（价格可能被低估）。它比单纯的价格 RSI 更能体现资金的态度。
    df_sorted = df_sorted.copy()

    required_cols = [high, low, close, volume]
    missing = [col for col in required_cols if col not in df_sorted.columns]
    if missing:
        raise ValueError(f"DataFrame 缺少必需列: {missing}")

    mfi = ta.mfi(high=df_sorted[high], low=df_sorted[low], 
                            close=df_sorted[close], volume=df_sorted[volume], length=length)
    if mfi is None:
        return df_sorted
    with_mfi = df_sorted.join(mfi)
    with_mfi = with_mfi.rename(columns={
        f"MFI_{length}" : 'MFI'
    })


    # ----- 2. MFI 信号：超买超卖 -----
    with_mfi['MFI_Signal'] = 0
    with_mfi.loc[with_mfi['MFI'] < 20, 'MFI_Signal'] = 1    # 超卖，潜在买入机会
    with_mfi.loc[with_mfi['MFI'] > 80, 'MFI_Signal'] = -1   # 超买，潜在卖出风险

    return with_mfi

def cmf(df_sorted: DataFrame, high: str='high', low: str='low', close: str='close', volume: str='volume', length=20):
    # 3. CMF (查肯资金流) - 默认周期20
    # 核心作用：衡量特定周期内的资金流向强度。它通过计算一段时间（通常 20 或 21 天）内资金的净流入或净流出，来判断市场的主导力量。
    # 用法：CMF > 0 表示资金净流入（买方主导），CMF < 0 表示资金净流出（卖方主导）。数值的绝对值越大，说明资金流向的确定性越高。
    df_sorted = df_sorted.copy()

    cmf = ta.cmf(high=df_sorted[high], low=df_sorted[low], 
                            close=df_sorted[close], volume=df_sorted[volume], length=length)
    if cmf is None:
        return df_sorted
    with_cmf = df_sorted.join(cmf)
    with_cmf = with_cmf.rename(columns={
        f"CMF_{length}" : 'CMF'
    })


    # ----- 3. CMF 信号：资金流向强度 -----
    with_cmf['CMF_Signal'] = 0
    with_cmf.loc[with_cmf['CMF'] > 0.1, 'CMF_Signal'] = 1   # 强资金流入
    with_cmf.loc[with_cmf['CMF'] <-0.1, 'CMF_Signal'] =-1   # 强资金流出

    return with_cmf