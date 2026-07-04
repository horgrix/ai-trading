import pandas_ta as ta
from pandas import DataFrame



def obv(df_sorted: DataFrame):
    # 1. OBV (平衡成交量)
    # 核心作用：追踪主力资金流向。它通过将成交量与价格涨跌相结合，判断资金的净流入或净流出。核心逻辑是：价格变化需要成交量确认。
    # 用法：OBV 趋势与价格趋势同步，确认趋势健康；如果价格创新高但 OBV 未创新高，形成 “顶背离”，可能预示上涨动力不足，是风险信号。
    obv = ta.obv(close=df_sorted['close'], volume=df_sorted['volume'])
    if obv is None:
        return df_sorted
    with_obv = df_sorted.join(obv)
    # with_obv['OBV_ZScore'] = (with_obv['OBV'] - with_obv['OBV'].rolling(100).mean()) / with_obv['OBV'].rolling(100).std()
    
    # ----- 1. OBV 信号：趋势确认与背离 -----
    # OBV上升趋势：OBV > 其20日均线
    with_obv['OBV_MA20'] = with_obv['OBV'].rolling(20).mean()
    with_obv['OBV_Signal'] = 0
    with_obv.loc[with_obv['OBV'] > with_obv['OBV_MA20'], 'OBV_Signal'] = 1   # 资金流入
    with_obv.loc[with_obv['OBV'] < with_obv['OBV_MA20'], 'OBV_Signal'] = -1  # 资金流出

    # 检测OBV与价格的背离（简化版）
    # 价格创20日新高但OBV未创新高 → 顶背离预警
    with_obv['Price_20_High'] = with_obv['close'].rolling(20).max()
    with_obv['OBV_20_High'] = with_obv['OBV'].rolling(20).max()
    with_obv['Bearish_Divergence'] = (
        (with_obv['close'] == with_obv['Price_20_High']) & 
        (with_obv['OBV'] < with_obv['OBV_20_High'].shift(1))
    )

    return with_obv

def mfi(df_sorted: DataFrame):

    # 2. MFI (资金流量指数) - 默认周期14
    # 核心作用：判断超买超卖区域。它常被称为“成交量加权的 RSI”，同时考虑了价格和成交量，能更真实地反映市场热度。
    # 用法：数值 > 80 为超买（价格可能过高），数值 < 20 为超卖（价格可能被低估）。它比单纯的价格 RSI 更能体现资金的态度。
    mfi = ta.mfi(high=df_sorted['high'], low=df_sorted['low'], 
                            close=df_sorted['close'], volume=df_sorted['volume'], length=14)
    if mfi is None:
        return df_sorted
    with_mfi = df_sorted.join(mfi)

    # ----- 2. MFI 信号：超买超卖 -----
    with_mfi['MFI_Signal'] = 0
    with_mfi.loc[with_mfi['MFI_14'] < 20, 'MFI_Signal'] = 1    # 超卖，潜在买入机会
    with_mfi.loc[with_mfi['MFI_14'] > 80, 'MFI_Signal'] = -1   # 超买，潜在卖出风险

    return with_mfi

def cmf(df_sorted: DataFrame):
    # 3. CMF (查肯资金流) - 默认周期20
    # 核心作用：衡量特定周期内的资金流向强度。它通过计算一段时间（通常 20 或 21 天）内资金的净流入或净流出，来判断市场的主导力量。
    # 用法：CMF > 0 表示资金净流入（买方主导），CMF < 0 表示资金净流出（卖方主导）。数值的绝对值越大，说明资金流向的确定性越高。
    cmf = ta.cmf(high=df_sorted['high'], low=df_sorted['low'], 
                            close=df_sorted['close'], volume=df_sorted['volume'], length=20)
    if cmf is None:
        return df_sorted
    with_cmf = df_sorted.join(cmf)

    # ----- 3. CMF 信号：资金流向强度 -----
    with_cmf['CMF_Signal'] = 0
    with_cmf.loc[with_cmf['CMF_20'] > 0.1, 'CMF_Signal'] = 1     # 强资金流入
    with_cmf.loc[with_cmf['CMF_20'] < -0.1, 'CMF_Signal'] = -1   # 强资金流出

    return with_cmf

def ad(df_sorted: DataFrame):
    # 4. AD (积聚/分配指数)
    # 核心作用：判断资金是“积聚”（吸筹）还是“分配”（派发）。它更侧重于评估收盘价在当日价格区间的位置，结合成交量来判断资金的真实意图。
    # 用法：AD 线上涨，表明资金在积聚（吸筹），后市看涨；AD 线下跌，表明资金在分配（派发），后市看跌。它同样可用于背离分析。
    ad = ta.ad(high=df_sorted['high'], low=df_sorted['low'], 
                        close=df_sorted['close'], volume=df_sorted['volume'])
    if ad is None:
        return df_sorted
    with_ad = df_sorted.join(ad)

    # ----- 4. AD 信号：积聚/分配趋势 -----
    # AD的20日均线作为趋势判断
    with_ad['AD_MA20'] = with_ad['AD'].rolling(20).mean()
    with_ad['AD_Signal'] = 0
    with_ad.loc[with_ad['AD'] > with_ad['AD_MA20'], 'AD_Signal'] = 1   # 积聚（吸筹）
    with_ad.loc[with_ad['AD'] < with_ad['AD_MA20'], 'AD_Signal'] = -1  # 分配（派发）

    return with_ad

def aobv(df_sorted: DataFrame):
    # 5. AOBV (阿彻平衡成交量) - 需要额外参数，默认使用20日基准
    # 核心作用：OBV 的优化版本。它通过一个动态的“基准成交量”来调整 OBV，试图减少噪音，更平滑地反映长期资金趋势。
    # 用法：作用与 OBV 类似，但信号更平滑。当 AOBV 与 OBV 方向出现分歧时，可能预示着短期波动中的潜在机会或风险。
    aobv = ta.aobv(close=df_sorted['close'], volume=df_sorted['volume'], length=20)
    if aobv is None:
        return df_sorted
    aobv = aobv.rename(columns={
        'OBV': 'AOBV',
        'OBV_min_2': 'AOBV_min_2period',
        'OBV_max_2': 'AOBV_max_2period',
        'OBVe_4': 'AOBV_EMA_4',
        'OBVe_12': 'AOBV_EMA_12',
        'AOBV_LR_2': 'AOBV_LongTerm',
        'AOBV_SR_2': 'AOBV_ShortTerm'
    })['AOBV']
    with_aobv = df_sorted.join(aobv)
    
    # ----- 5. AOBV 信号：平滑版OBV趋势 -----
    with_aobv['AOBV_Signal'] = 0
    with_aobv.loc[with_aobv['AOBV'] > with_aobv['AOBV'].rolling(20).mean(), 'AOBV_Signal'] = 1
    with_aobv.loc[with_aobv['AOBV'] < with_aobv['AOBV'].rolling(20).mean(), 'AOBV_Signal'] = -1

    return with_aobv
