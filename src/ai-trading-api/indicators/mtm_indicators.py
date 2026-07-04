"""
动量指标模块 - 包含 RSI, MACD, STOCH, MOM, ROC, CCI, WILLR, AO 等动量类技术指标
"""
import pandas_ta as ta
from pandas import DataFrame


def rsi(df_sorted: DataFrame):

    # ===== 1. RSI (相对强弱指数) =====
    rsi = ta.rsi(close=df_sorted['close'], length=14)
    if rsi is None:
        return df_sorted
    with_rsi = df_sorted.join(rsi)

    # ===== 1. RSI 信号 =====
    with_rsi['RSI_Signal'] = 0
    with_rsi.loc[with_rsi['RSI_14'] < 30, 'RSI_Signal'] = 1      # 超卖，潜在买入
    with_rsi.loc[with_rsi['RSI_14'] > 70, 'RSI_Signal'] = -1     # 超买，潜在卖出

    # 加强版：更严格的超买超卖
    with_rsi['RSI_Strict_Signal'] = 0
    with_rsi.loc[with_rsi['RSI_14'] < 20, 'RSI_Strict_Signal'] = 1
    with_rsi.loc[with_rsi['RSI_14'] > 80, 'RSI_Strict_Signal'] = -1

    # RSI背离检测（简化版：价格创新高但RSI未创新高）
    with_rsi['RSI_Bearish_Div'] = (
        (with_rsi['close'] == with_rsi['close'].rolling(20).max()) &
        (with_rsi['RSI_14'] < with_rsi['RSI_14'].rolling(20).max().shift(1))
    )
    with_rsi['RSI_Bullish_Div'] = (
        (with_rsi['close'] == with_rsi['close'].rolling(20).min()) &
        (with_rsi['RSI_14'] > with_rsi['RSI_14'].rolling(20).min().shift(1))
    )

    return with_rsi

def macd(df_sorted: DataFrame):

    # ===== 2. MACD (移动平均收敛发散) =====
    macd = ta.macd(close=df_sorted['close'], fast=12, slow=26, signal=9)
    if macd is None:
        return df_sorted
    with_macd = df_sorted.join(macd)
    # 列名: MACD_12_26_9 (快线), MACDh_12_26_9 (柱状线), MACDs_12_26_9 (慢线/信号线)

    # ===== 2. MACD 信号 =====
    with_macd['MACD_Signal'] = 0
    # 金叉（买入）：快线上穿慢线
    with_macd.loc[
        (with_macd['MACD_12_26_9'] > with_macd['MACDs_12_26_9']) & 
        (with_macd['MACD_12_26_9'].shift(1) <= with_macd['MACDs_12_26_9'].shift(1)),
        'MACD_Signal'
    ] = 1
    # 死叉（卖出）：快线下穿慢线
    with_macd.loc[
        (with_macd['MACD_12_26_9'] < with_macd['MACDs_12_26_9']) & 
        (with_macd['MACD_12_26_9'].shift(1) >= with_macd['MACDs_12_26_9'].shift(1)),
        'MACD_Signal'
    ] = -1

    # MACD柱状线转正/转负信号
    with_macd['MACD_Hist_Signal'] = 0
    with_macd.loc[
        (with_macd['MACDh_12_26_9'] > 0) & 
        (with_macd['MACDh_12_26_9'].shift(1) <= 0),
        'MACD_Hist_Signal'
    ] = 1  # 柱状线由负转正，动能转强
    with_macd.loc[
        (with_macd['MACDh_12_26_9'] < 0) & 
        (with_macd['MACDh_12_26_9'].shift(1) >= 0),
        'MACD_Hist_Signal'
    ] = -1  # 柱状线由正转负，动能转弱

    return with_macd

def stoch(df_sorted: DataFrame):

    # ===== 3. STOCH (随机振荡器) =====
    stoch = ta.stoch(high=df_sorted['high'], low=df_sorted['low'], close=df_sorted['close'], k=14, d=3, smooth_k=1)
    if stoch is None:
        return df_sorted
    with_stoch = df_sorted.join(stoch)
    # 列名: STOCHk_14_3_1 (%K线), STOCHd_14_3_1 (%D线)

    # ===== 3. STOCH 信号 =====
    with_stoch['STOCH_Signal'] = 0
    # 买入：%K上穿%D线，且处于超卖区（<20）
    with_stoch.loc[
        (with_stoch['STOCHk_14_3_1'] > with_stoch['STOCHd_14_3_1']) & 
        (with_stoch['STOCHk_14_3_1'].shift(1) <= with_stoch['STOCHd_14_3_1'].shift(1)) &
        (with_stoch['STOCHd_14_3_1'] < 20),
        'STOCH_Signal'
    ] = 1
    # 卖出：%K下穿%D线，且处于超买区（>80）
    with_stoch.loc[
        (with_stoch['STOCHk_14_3_1'] < with_stoch['STOCHd_14_3_1']) & 
        (with_stoch['STOCHk_14_3_1'].shift(1) >= with_stoch['STOCHd_14_3_1'].shift(1)) &
        (with_stoch['STOCHd_14_3_1'] > 80),
        'STOCH_Signal'
    ] = -1

    return with_stoch

def mom(df_sorted: DataFrame):
    # ===== 4. MOM (动量指标) =====
    mom = ta.mom(close=df_sorted['close'], length=10)
    if mom is None:
        return df_sorted
    with_mom = df_sorted.join(mom)

    # ===== 4. MOM 信号 =====
    with_mom['MOM_Signal'] = 0
    with_mom.loc[with_mom['MOM_10'] > 0, 'MOM_Signal'] = 1   # 正向动量
    with_mom.loc[with_mom['MOM_10'] < 0, 'MOM_Signal'] = -1  # 负向动量

    # MOM加速/减速信号
    with_mom['MOM_Accel'] = with_mom['MOM_10'] - with_mom['MOM_10'].shift(1)
    with_mom['MOM_Accel_Signal'] = 0
    with_mom.loc[with_mom['MOM_Accel'] > 0, 'MOM_Accel_Signal'] = 1   # 动量加速
    with_mom.loc[with_mom['MOM_Accel'] < 0, 'MOM_Accel_Signal'] = -1  # 动量减速

    return with_mom

def roc(df_sorted: DataFrame):
    # ===== 5. ROC (变化率) =====
    roc = ta.roc(close=df_sorted['close'], length=10)
    if roc is None:
        return df_sorted
    with_roc = df_sorted.join(roc)

    # ===== 5. ROC 信号 =====
    with_roc['ROC_Signal'] = 0
    with_roc.loc[with_roc['ROC_10'] > 0, 'ROC_Signal'] = 1
    with_roc.loc[with_roc['ROC_10'] < 0, 'ROC_Signal'] = -1

    # ROC极端值信号
    with_roc['ROC_Extreme'] = 0
    with_roc.loc[with_roc['ROC_10'] > with_roc['ROC_10'].rolling(100).mean() + 2 * with_roc['ROC_10'].rolling(100).std(), 'ROC_Extreme'] = -1
    with_roc.loc[with_roc['ROC_10'] < with_roc['ROC_10'].rolling(100).mean() - 2 * with_roc['ROC_10'].rolling(100).std(), 'ROC_Extreme'] = 1

    return with_roc

def cci(df_sorted: DataFrame):
    # ===== 6. CCI (商品通道指数) =====
    cci = ta.cci(high=df_sorted['high'], low=df_sorted['low'], 
                            close=df_sorted['close'], length=14)
    if cci is None:
        return df_sorted
    cci = cci.rename('CCI_14')
    with_cci = df_sorted.join(cci)

    # ===== 6. CCI 信号 =====
    with_cci['CCI_Signal'] = 0
    with_cci.loc[with_cci['CCI_14'] < -100, 'CCI_Signal'] = 1    # 超卖
    with_cci.loc[with_cci['CCI_14'] > 100, 'CCI_Signal'] = -1    # 超买

    # CCI极端信号（±200）
    with_cci.loc[with_cci['CCI_14'] < -200, 'CCI_Signal'] = 2    # 极强买入信号
    with_cci.loc[with_cci['CCI_14'] > 200, 'CCI_Signal'] = -2    # 极强卖出信号

    return with_cci

def willr(df_sorted: DataFrame):
    # ===== 7. WILLR (威廉姆斯 %R) =====
    willr = ta.willr(high=df_sorted['high'], low=df_sorted['low'], 
                                close=df_sorted['close'], length=14)
    if willr is None:
        return df_sorted
    with_willr = df_sorted.join(willr)

    # ===== 7. WILLR 信号 =====
    with_willr['WILLR_Signal'] = 0
    with_willr.loc[with_willr['WILLR_14'] < -80, 'WILLR_Signal'] = 1   # 超卖
    with_willr.loc[with_willr['WILLR_14'] > -20, 'WILLR_Signal'] = -1  # 超买

    return with_willr

def ao(df_sorted: DataFrame):
    # ===== 8. AO (优势振荡器) =====
    ao = ta.ao(high=df_sorted['high'], low=df_sorted['low'])
    if ao is None:
        return df_sorted
    ao = ao.rename('AO')
    with_ao = df_sorted.join(ao)

    # ===== 8. AO 信号 =====
    with_ao['AO_Signal'] = 0
    with_ao.loc[with_ao['AO'] > 0, 'AO_Signal'] = 1    # 正向动量
    with_ao.loc[with_ao['AO'] < 0, 'AO_Signal'] = -1   # 负向动量

    # AO穿越零轴信号
    with_ao['AO_Cross'] = 0
    with_ao.loc[
        (with_ao['AO'] > 0) & (with_ao['AO'].shift(1) <= 0),
        'AO_Cross'
    ] = 1  # 由负转正，买入
    with_ao.loc[
        (with_ao['AO'] < 0) & (with_ao['AO'].shift(1) >= 0),
        'AO_Cross'
    ] = -1  # 由正转负，卖出

    return with_ao