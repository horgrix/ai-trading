import pandas_ta as ta
import pandas as pd
from pandas import DataFrame

def skew(df_sorted: DataFrame, close: str='close', window=60):
    # ===== 3. SKEW (偏斜度) =====
    df_sorted = df_sorted.copy()

    required_cols = [close]
    missing = [col for col in required_cols if col not in df_sorted.columns]
    if missing:
        raise ValueError(f"DataFrame 缺少必需列: {missing}")

    # 计算50日滚动偏斜度
    skew = df_sorted[close].rolling(window=window).apply(lambda x: pd.Series(x).skew(), raw=True).rename('SKEW')
    with_skew = df_sorted.join(skew)

    # ===== 3. SKEW 信号 =====
    # 偏斜度状态判断
    with_skew['SKEW_Signal'] = 0
    with_skew.loc[with_skew['SKEW'] > 0.5, 'SKEW_Signal'] = 1    # 正偏，可能有大涨风险
    with_skew.loc[with_skew['SKEW'] < -0.5, 'SKEW_Signal'] = -1  # 负偏，可能有大跌风险

    # 偏斜度变化方向
    with_skew['SKEW_Direction'] = 0
    with_skew.loc[with_skew['SKEW'] > with_skew['SKEW'].shift(1), 'SKEW_Direction'] = 1   # 偏斜度增大
    with_skew.loc[with_skew['SKEW'] < with_skew['SKEW'].shift(1), 'SKEW_Direction'] = -1  # 偏斜度减小

    # 极端偏斜度信号（出现潜在极端行情）
    with_skew.loc[with_skew['SKEW'] > 1.0, 'SKEW_Signal'] = 2     # 强正偏，大涨风险高
    with_skew.loc[with_skew['SKEW'] < -1.0, 'SKEW_Signal'] = -2   # 强负偏，大跌风险高

    return with_skew

def kurtosis(df_sorted: DataFrame, close: str='close', window=60):
    # ===== 4. KURTOSIS (峰态度) =====
    """
    Kurtosis（峰度） 在量化交易中是一个衡量收益率分布尾部“厚薄”程度的统计量。简单来说，它告诉你：极端行情（暴涨暴跌）发生的概率，比正常情况高还是低？
    """
    df_sorted = df_sorted.copy()

    required_cols = [close]
    missing = [col for col in required_cols if col not in df_sorted.columns]
    if missing:
        raise ValueError(f"DataFrame 缺少必需列: {missing}")
    
    # 计算50日滚动峰态度（使用pandas的kurtosis方法，默认是皮尔逊峰度，正态分布为0）
    kurtosis = df_sorted[close].rolling(window=window).apply(lambda x: pd.Series(x).kurtosis(), raw=True).rename('KURT')
    with_kurtosis = df_sorted.join(kurtosis)

    # ===== 4. KURTOSIS 信号 =====
    # 峰态状态判断（正态分布峰度为0）
    with_kurtosis['KURT_Signal'] = 0
    with_kurtosis.loc[with_kurtosis['KURT'] > 2, 'KURT_Signal'] = 1      # 高峰度，极端值风险高
    with_kurtosis.loc[with_kurtosis['KURT'] < -0.5, 'KURT_Signal'] = -1  # 低峰度，分布平缓

    # 峰态变化方向
    with_kurtosis['KURT_Direction'] = 0
    with_kurtosis.loc[with_kurtosis['KURT'] > with_kurtosis['KURT'].shift(1), 'KURT_Direction'] = 1   # 峰度上升
    with_kurtosis.loc[with_kurtosis['KURT'] < with_kurtosis['KURT'].shift(1), 'KURT_Direction'] = -1  # 峰度下降

    # 极端峰度预警（>5 或 <-1 为极值）
    with_kurtosis.loc[with_kurtosis['KURT'] > 5, 'KURT_Signal'] = 2      # 极高峰度，黑天鹅风险极高
    with_kurtosis.loc[with_kurtosis['KURT'] < -1, 'KURT_Signal'] = -2    # 极低峰度，价格分布异常平坦

    return with_kurtosis

def zscore(df_sorted: DataFrame, close: str='close', length=20):
    # ===== 5. ZSCORE (Z分数) =====
    df_sorted = df_sorted.copy()

    required_cols = [close]
    missing = [col for col in required_cols if col not in df_sorted.columns]
    if missing:
        raise ValueError(f"DataFrame 缺少必需列: {missing}")

    # 方法一：使用 pandas_ta 的 zscore 函数
    zscore = ta.zscore(close=df_sorted[close], length=length)
    if zscore is None:
        return df_sorted

    with_zscore = df_sorted.join(zscore).rename(columns={
        f'ZS_{length}': 'ZSCORE'
    })

    # 方法二：手动计算（验证用）
    # with_zscore['ZSCORE_20_manual'] = (with_zscore['close'] - with_zscore['close'].rolling(20).mean()) / with_zscore['close'].rolling(20).std()

    # ===== 5. ZSCORE 信号 =====
    # Z分数位置判断
    with_zscore['ZSCORE_Signal'] = 0
    with_zscore.loc[with_zscore['ZSCORE'] > 2, 'ZSCORE_Signal'] = -1  # 价格过高，看跌（均值回归）
    with_zscore.loc[with_zscore['ZSCORE'] < -2, 'ZSCORE_Signal'] = 1  # 价格过低，看涨（均值回归）

    # 极端Z分数信号（3倍标准差）
    with_zscore.loc[with_zscore['ZSCORE'] > 3, 'ZSCORE_Signal'] = -2   # 极端超买
    with_zscore.loc[with_zscore['ZSCORE'] < -3, 'ZSCORE_Signal'] = 2    # 极端超卖

    # Z分数变化方向
    with_zscore['ZSCORE_Direction'] = 0
    with_zscore.loc[with_zscore['ZSCORE'] > with_zscore['ZSCORE'].shift(1), 'ZSCORE_Direction'] = 1   # 向超买移动
    with_zscore.loc[with_zscore['ZSCORE'] < with_zscore['ZSCORE'].shift(1), 'ZSCORE_Direction'] = -1  # 向超卖移动

    # Z分数回归信号（从极端值回归到均值附近）
    with_zscore['ZSCORE_Reversion'] = 0
    # 从超买回归（ZSCORE > 2 变为 < 1.5）
    with_zscore.loc[
        (with_zscore['ZSCORE'] < 1.5) & 
        (with_zscore['ZSCORE'].shift(1) > 2),
        'ZSCORE_Reversion'
    ] = -1
    # 从超卖回归（ZSCORE < -2 变为 > -1.5）
    with_zscore.loc[
        (with_zscore['ZSCORE'] > -1.5) & 
        (with_zscore['ZSCORE'].shift(1) < -2),
        'ZSCORE_Reversion'
    ] = 1

    return with_zscore