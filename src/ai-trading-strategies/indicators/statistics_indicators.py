import pandas_ta as ta
import pandas as pd
import numpy as np
from pandas import DataFrame


def std(df_sorted: DataFrame):
    # ===== 1. STDEV (标准差) =====
    # 计算20日滚动标准差
    std = df_sorted['close'].rolling(window=20).std().rename('STDEV_20')
    with_std = df_sorted.join(std)

    # ===== 1. STDEV 信号 =====
    # 波动率状态（相对于历史）
    with_std['STDEV_MA100'] = with_std['STDEV_20'].rolling(100).mean()
    with_std['Vol_State'] = 'normal'
    with_std.loc[with_std['STDEV_20'] > with_std['STDEV_MA100'] * 1.5, 'Vol_State'] = 'high'   # 高波动
    with_std.loc[with_std['STDEV_20'] < with_std['STDEV_MA100'] * 0.5, 'Vol_State'] = 'low'    # 低波动

    # 波动率变化方向
    with_std['STDEV_Direction'] = 0
    with_std.loc[with_std['STDEV_20'] > with_std['STDEV_20'].shift(1), 'STDEV_Direction'] = 1   # 波动率上升
    with_std.loc[with_std['STDEV_20'] < with_std['STDEV_20'].shift(1), 'STDEV_Direction'] = -1  # 波动率下降

    # 波动率突破信号（短期波动率突破长期均值）
    with_std['STDEV_Breakout'] = 0
    with_std.loc[with_std['STDEV_20'] > with_std['STDEV_MA100'] * 1.5, 'STDEV_Breakout'] = 1
    with_std.loc[with_std['STDEV_20'] < with_std['STDEV_MA100'] * 0.5, 'STDEV_Breakout'] = -1

    return with_std

def mad(df_sorted: DataFrame):
    # ===== 2. MAD (平均绝对偏差) =====
    # 使用 pandas_ta 的 mad 函数
    mad = ta.mad(close=df_sorted['close'], length=20)
    with_mad = df_sorted.join(mad)

    # ===== 2. MAD 信号 =====
    # MAD 替代波动率通道（上下轨）
    with_mad['MA_20'] = with_mad['close'].rolling(20).mean()
    with_mad['MAD_Upper'] = with_mad['MA_20'] + with_mad['MAD_20'] * 2
    with_mad['MAD_Lower'] = with_mad['MA_20'] - with_mad['MAD_20'] * 2

    # 价格与MAD通道位置
    with_mad['MAD_Position'] = 0
    with_mad.loc[with_mad['close'] > with_mad['MAD_Upper'], 'MAD_Position'] = 1    # 突破上轨，超买
    with_mad.loc[with_mad['close'] < with_mad['MAD_Lower'], 'MAD_Position'] = -1   # 跌破下轨，超卖

    # MAD 方向变化
    with_mad['MAD_Direction'] = 0
    with_mad.loc[with_mad['MAD_20'] > with_mad['MAD_20'].shift(1), 'MAD_Direction'] = 1
    with_mad.loc[with_mad['MAD_20'] < with_mad['MAD_20'].shift(1), 'MAD_Direction'] = -1

    return with_mad

def skew(df_sorted: DataFrame):
    # ===== 3. SKEW (偏斜度) =====
    # 计算50日滚动偏斜度
    skew = df_sorted['close'].rolling(window=50).apply(lambda x: pd.Series(x).skew(), raw=True).rename('SKEW_50')
    with_skew = df_sorted.join(skew)

    # ===== 3. SKEW 信号 =====
    # 偏斜度状态判断
    with_skew['SKEW_Signal'] = 0
    with_skew.loc[with_skew['SKEW_50'] > 0.5, 'SKEW_Signal'] = 1    # 正偏，可能有大涨风险
    with_skew.loc[with_skew['SKEW_50'] < -0.5, 'SKEW_Signal'] = -1   # 负偏，可能有大跌风险

    # 偏斜度变化方向
    with_skew['SKEW_Direction'] = 0
    with_skew.loc[with_skew['SKEW_50'] > with_skew['SKEW_50'].shift(1), 'SKEW_Direction'] = 1   # 偏斜度增大
    with_skew.loc[with_skew['SKEW_50'] < with_skew['SKEW_50'].shift(1), 'SKEW_Direction'] = -1  # 偏斜度减小

    # 极端偏斜度信号（出现潜在极端行情）
    with_skew.loc[with_skew['SKEW_50'] > 1.0, 'SKEW_Signal'] = 2     # 强正偏，大涨风险高
    with_skew.loc[with_skew['SKEW_50'] < -1.0, 'SKEW_Signal'] = -2   # 强负偏，大跌风险高

    return with_skew

def kurtosis(df_sorted: DataFrame):
    # ===== 4. KURTOSIS (峰态度) =====
    # 计算50日滚动峰态度（使用pandas的kurtosis方法，默认是皮尔逊峰度，正态分布为0）
    kurtosis = df_sorted['close'].rolling(window=50).apply(lambda x: pd.Series(x).kurtosis(), raw=True).rename('KURT_50')
    with_kurtosis = df_sorted.join(kurtosis)

    # ===== 4. KURTOSIS 信号 =====
    # 峰态状态判断（正态分布峰度为0）
    with_kurtosis['KURT_Signal'] = 0
    with_kurtosis.loc[with_kurtosis['KURT_50'] > 2, 'KURT_Signal'] = 1     # 高峰度，极端值风险高
    with_kurtosis.loc[with_kurtosis['KURT_50'] < -0.5, 'KURT_Signal'] = -1  # 低峰度，分布平缓

    # 峰态变化方向
    with_kurtosis['KURT_Direction'] = 0
    with_kurtosis.loc[with_kurtosis['KURT_50'] > with_kurtosis['KURT_50'].shift(1), 'KURT_Direction'] = 1   # 峰度上升
    with_kurtosis.loc[with_kurtosis['KURT_50'] < with_kurtosis['KURT_50'].shift(1), 'KURT_Direction'] = -1  # 峰度下降

    # 极端峰度预警（>5 或 <-1 为极值）
    with_kurtosis.loc[with_kurtosis['KURT_50'] > 5, 'KURT_Signal'] = 2      # 极高峰度，黑天鹅风险极高
    with_kurtosis.loc[with_kurtosis['KURT_50'] < -1, 'KURT_Signal'] = -2    # 极低峰度，价格分布异常平坦

    return with_kurtosis

def zscore(df_sorted: DataFrame):
    # ===== 5. ZSCORE (Z分数) =====
    # 方法一：使用 pandas_ta 的 zscore 函数
    zscore = ta.zscore(close=df_sorted['close'], length=20).rename('ZSCORE_20')
    with_zscore = df_sorted.join(zscore)

    # 方法二：手动计算（验证用）
    # with_zscore['ZSCORE_20_manual'] = (with_zscore['close'] - with_zscore['close'].rolling(20).mean()) / with_zscore['close'].rolling(20).std()

    # ===== 5. ZSCORE 信号 =====
    # Z分数位置判断
    with_zscore['ZSCORE_Signal'] = 0
    with_zscore.loc[with_zscore['ZSCORE_20'] > 2, 'ZSCORE_Signal'] = -1   # 价格过高，看跌（均值回归）
    with_zscore.loc[with_zscore['ZSCORE_20'] < -2, 'ZSCORE_Signal'] = 1    # 价格过低，看涨（均值回归）

    # 极端Z分数信号（3倍标准差）
    with_zscore.loc[with_zscore['ZSCORE_20'] > 3, 'ZSCORE_Signal'] = -2   # 极端超买
    with_zscore.loc[with_zscore['ZSCORE_20'] < -3, 'ZSCORE_Signal'] = 2    # 极端超卖

    # Z分数变化方向
    with_zscore['ZSCORE_Direction'] = 0
    with_zscore.loc[with_zscore['ZSCORE_20'] > with_zscore['ZSCORE_20'].shift(1), 'ZSCORE_Direction'] = 1   # 向超买移动
    with_zscore.loc[with_zscore['ZSCORE_20'] < with_zscore['ZSCORE_20'].shift(1), 'ZSCORE_Direction'] = -1  # 向超卖移动

    # Z分数回归信号（从极端值回归到均值附近）
    with_zscore['ZSCORE_Reversion'] = 0
    # 从超买回归（ZSCORE > 2 变为 < 1.5）
    with_zscore.loc[
        (with_zscore['ZSCORE_20'] < 1.5) & 
        (with_zscore['ZSCORE_20'].shift(1) > 2),
        'ZSCORE_Reversion'
    ] = -1
    # 从超卖回归（ZSCORE < -2 变为 > -1.5）
    with_zscore.loc[
        (with_zscore['ZSCORE_20'] > -1.5) & 
        (with_zscore['ZSCORE_20'].shift(1) < -2),
        'ZSCORE_Reversion'
    ] = 1

    return with_zscore