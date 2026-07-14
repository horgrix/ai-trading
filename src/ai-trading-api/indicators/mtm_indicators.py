"""
动量指标模块 - 包含 RSI, MACD, STOCH, MOM, ROC, CCI, WILLR, AO 等动量类技术指标
"""
import pandas_ta as ta
from pandas import DataFrame


def rsi(df_sorted: DataFrame, close: str='close', length: int=14):

    # ===== 1. RSI (相对强弱指数) =====

    df_sorted = df_sorted.copy()

    required_cols = [close]
    missing = [col for col in required_cols if col not in df_sorted.columns]
    if missing:
        raise ValueError(f"DataFrame 缺少必需列: {missing}")

    rsi = ta.rsi(close=df_sorted['close'], length=length)
    if rsi is None:
        return df_sorted
    with_rsi = df_sorted.join(rsi)
    with_rsi = with_rsi.rename(columns={
        f'RSI_{length}': 'RSI'
    })

    # ===== 1. RSI 信号 =====
    with_rsi['RSI_OBOS_Signal'] = 0
    with_rsi.loc[with_rsi['RSI'] < 25, 'RSI_OBOS_Signal'] = 1  # 超卖，潜在买入
    with_rsi.loc[with_rsi['RSI'] > 75, 'RSI_OBOS_Signal'] =-1  # 超买，潜在卖出

    # RSI背离检测（简化版：价格创新高但RSI未创新高）
    with_rsi['RSI_Div_Signal'] = 0
    with_rsi.loc[(with_rsi['close'] == with_rsi['close'].rolling(20).max()) & (with_rsi['RSI'] < with_rsi['RSI'].rolling(20).max().shift(1)), 'RSI_Div_Signal'] =-1 # 顶背离
    with_rsi.loc[(with_rsi['close'] == with_rsi['close'].rolling(20).min()) & (with_rsi['RSI'] > with_rsi['RSI'].rolling(20).min().shift(1)), 'RSI_Div_Signal'] = 1 # 底背离

    return with_rsi

def stoch(df_sorted: DataFrame, high: str='high', low: str='low', close: str='close', k: int=14, d: int=3, smooth_k: int=1):

    # ===== 3. STOCH (随机振荡器) =====

    df_sorted = df_sorted.copy()

    required_cols = [high, low, close]
    missing = [col for col in required_cols if col not in df_sorted.columns]
    if missing:
        raise ValueError(f"DataFrame 缺少必需列: {missing}")
    
    stoch = ta.stoch(high=df_sorted[high], low=df_sorted[low], close=df_sorted[close], k=k, d=d, smooth_k=smooth_k)
    if stoch is None:
        return df_sorted
    with_stoch = df_sorted.join(stoch)
    with_stoch = with_stoch.rename(columns={
        f'STOCHk_{k}_{d}_{smooth_k}' : 'STOCH_K',
        f'STOCHd_{k}_{d}_{smooth_k}' : 'STOCH_D',
    })
    # 列名: STOCHk_14_3_1 (%K线), STOCHd_14_3_1 (%D线)

    # ===== 3. STOCH 信号 =====
    with_stoch['STOCH_Signal'] = 0
    # 买入：%K上穿%D线，且处于超卖区（<20）
    with_stoch.loc[
        (with_stoch['STOCH_K'] > with_stoch['STOCH_D']) & 
        (with_stoch['STOCH_K'].shift(1) <= with_stoch['STOCH_D'].shift(1)) &
        (with_stoch['STOCH_K'] < 20),
        'STOCH_Signal'
    ] = 1
    # 卖出：%K下穿%D线，且处于超买区（>80）
    with_stoch.loc[
        (with_stoch['STOCH_K'] < with_stoch['STOCH_D']) & 
        (with_stoch['STOCH_K'].shift(1) >= with_stoch['STOCH_D'].shift(1)) &
        (with_stoch['STOCH_K'] > 80),
        'STOCH_Signal'
    ] = -1

    return with_stoch

def mom(df_sorted: DataFrame, close: str='close', length: int=10):
    # ===== 4. MOM (动量指标) =====
    """
    趋势确认：做多要求 MOM > 0，做空要求 MOM < 0，确保方向与动量一致。

    动量衰竭：价格创新高但 MOM 未创新高，说明上涨速度放缓，可能出现回调。

    突破质量：唐奇安突破时，MOM 数值越大（相对历史），突破的"爆发力"越强。
    """
    df_sorted = df_sorted.copy()

    required_cols = [close]
    missing = [col for col in required_cols if col not in df_sorted.columns]
    if missing:
        raise ValueError(f"DataFrame 缺少必需列: {missing}")

    mom = ta.mom(close=df_sorted[close], length=length)
    if mom is None:
        return df_sorted
    with_mom = df_sorted.join(mom)
    with_mom = with_mom.rename(columns={
        f'MOM_{length}' : 'MOM'
    })

    # ===== 4. MOM 信号 =====
    with_mom['MOM_Signal'] = 0
    with_mom.loc[with_mom['MOM'] > 0, 'MOM_Signal'] = 1   # 正向动量
    with_mom.loc[with_mom['MOM'] < 0, 'MOM_Signal'] = -1  # 负向动量

    # MOM加速/减速信号
    with_mom['MOM_Accel'] = with_mom['MOM'] - with_mom['MOM'].shift(1)
    with_mom['MOM_Accel_Signal'] = 0
    with_mom.loc[with_mom['MOM_Accel'] > 0, 'MOM_Accel_Signal'] = 1   # 动量加速
    with_mom.loc[with_mom['MOM_Accel'] < 0, 'MOM_Accel_Signal'] = -1  # 动量减速

    # 能量背离
    with_mom['MOM_Div_Signal'] = 0
    with_mom.loc[(with_mom['close'] == with_mom['close'].rolling(20).max()) & (with_mom['MOM'] < with_mom['MOM'].rolling(20).max().shift(1)), 'MOM_Div_Signal'] =-1 # 顶背离
    with_mom.loc[(with_mom['close'] == with_mom['close'].rolling(20).min()) & (with_mom['MOM'] > with_mom['MOM'].rolling(20).min().shift(1)), 'MOM_Div_Signal'] = 1 # 底背离

    return with_mom

def roc(df_sorted: DataFrame, close: str='close', length: int=10):
    # ===== 5. ROC (变化率) =====

    df_sorted = df_sorted.copy()

    required_cols = [close]
    missing = [col for col in required_cols if col not in df_sorted.columns]
    if missing:
        raise ValueError(f"DataFrame 缺少必需列: {missing}")
    
    roc = ta.roc(close=df_sorted['close'], length=length)
    if roc is None:
        return df_sorted
    with_roc = df_sorted.join(roc)
    with_roc = with_roc.rename(columns={
        f'ROC_{length}' : 'ROC'
    })

    # ===== 5. ROC 信号 =====
    with_roc['ROC_Signal'] = 0
    with_roc.loc[with_roc['ROC'] > 0, 'ROC_Signal'] = 1
    with_roc.loc[with_roc['ROC'] < 0, 'ROC_Signal'] = -1

    with_roc['ROC_Cross'] = 0
    with_roc.loc[(with_roc['ROC'] > 0) & (with_roc['ROC'].shift(1) < 0), 'ROC_Cross'] =  1
    with_roc.loc[(with_roc['ROC'] < 0) & (with_roc['ROC'].shift(1) > 0), 'ROC_Cross'] = -1

    # ROC极端值信号
    with_roc['ROC_Extreme'] = 0
    with_roc.loc[with_roc['ROC'] > with_roc['ROC'].rolling(100).mean() + 2 * with_roc['ROC'].rolling(100).std(), 'ROC_Extreme'] = -1
    with_roc.loc[with_roc['ROC'] < with_roc['ROC'].rolling(100).mean() - 2 * with_roc['ROC'].rolling(100).std(), 'ROC_Extreme'] = 1

    return with_roc

def macd(df_sorted: DataFrame, close: str='close', fast=12, slow=26, signal=9):
    # ===== 2. MACD (移动平均收敛发散) =====
    df_sorted = df_sorted.copy()

    required_cols = [close]
    missing = [col for col in required_cols if col not in df_sorted.columns]
    if missing:
        raise ValueError(f"DataFrame 缺少必需列: {missing}")
    
    macd = ta.macd(close=df_sorted[close], fast=fast, slow=slow, signal=signal)
    if macd is None:
        return df_sorted
    with_macd = df_sorted.join(macd)
    with_macd = with_macd.rename(columns={
        f'MACD_{fast}_{slow}_{signal}'  : 'MACD_F',
        f'MACDs_{fast}_{slow}_{signal}' : 'MACD_S',
        f'MACDh_{fast}_{slow}_{signal}' : 'MACD_H'
    })
    # 列名: MACD_12_26_9 (快线), MACDh_12_26_9 (柱状线), MACDs_12_26_9 (慢线/信号线)

    # ===== 2. MACD 信号 =====
    with_macd['MACD_Signal'] = 0
    # 金叉（买入）：快线上穿慢线
    with_macd.loc[
        (with_macd['MACD_F'] > with_macd['MACD_S']) & 
        (with_macd['MACD_F'].shift(1) <= with_macd['MACD_S'].shift(1)),
        'MACD_Signal'
    ] = 1
    # 死叉（卖出）：快线下穿慢线
    with_macd.loc[
        (with_macd['MACD_F'] < with_macd['MACD_S']) & 
        (with_macd['MACD_F'].shift(1) >= with_macd['MACD_S'].shift(1)),
        'MACD_Signal'
    ] = -1

    # MACD柱状线转正/转负信号
    with_macd['MACD_Hist_Signal'] = 0
    with_macd.loc[
        (with_macd['MACD_H'] > 0) & 
        (with_macd['MACD_H'].shift(1) <= 0),
        'MACD_Hist_Signal'
    ] = 1  # 柱状线由负转正，动能转强
    with_macd.loc[
        (with_macd['MACD_H'] < 0) & 
        (with_macd['MACD_H'].shift(1) >= 0),
        'MACD_Hist_Signal'
    ] = -1  # 柱状线由正转负，动能转弱

    return with_macd

def ao(df_sorted: DataFrame, high: str='high', low: str='low', fast=5, slow=34):
    # ===== 8. AO (优势振荡器) =====
    """
    趋势确认：做多要求 AO > 0，做空要求 AO < 0。
    零轴穿越：AO 从下向上穿越零轴，视为趋势由空转多的关键信号。
    双峰形态：AO 在零轴下方形成两个依次抬高的峰（Twin Peaks Bullish），是强反转信号。
    """
    df_sorted = df_sorted.copy()

    required_cols = [high, low]
    missing = [col for col in required_cols if col not in df_sorted.columns]
    if missing:
        raise ValueError(f"DataFrame 缺少必需列: {missing}")
    
    ao = ta.ao(high=df_sorted[high], low=df_sorted[low], fast=fast, slow=slow)
    if ao is None:
        return df_sorted
    with_ao = df_sorted.join(ao)
    with_ao = with_ao.rename(columns={
        f"AO_{fast}_{slow}" : 'AO'
    })

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