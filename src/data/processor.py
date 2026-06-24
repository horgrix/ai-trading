"""
数据处理模块 - 数据清洗、特征工程、技术指标计算
"""

import pandas as pd
import numpy as np
from typing import Optional


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    清洗数据：处理缺失值、异常值

    Args:
        df: 原始数据 DataFrame

    Returns:
        清洗后的 DataFrame
    """
    df = df.copy()

    # 前向填充缺失值
    df.fillna(method="ffill", inplace=True)

    # 删除仍存在的缺失值
    df.dropna(inplace=True)

    return df


def calculate_returns(df: pd.DataFrame, column: str = "Close") -> pd.DataFrame:
    """
    计算收益率

    Args:
        df: 数据 DataFrame
        column: 用于计算收益率的列名

    Returns:
        添加了收益率列的 DataFrame
    """
    df = df.copy()
    df["returns"] = df[column].pct_change()
    df["log_returns"] = np.log(df[column] / df[column].shift(1))
    return df


def calculate_sma(df: pd.DataFrame, column: str = "Close", window: int = 20) -> pd.Series:
    """
    计算简单移动平均线 (SMA)

    Args:
        df: 数据 DataFrame
        column: 目标列名
        window: 窗口大小

    Returns:
        SMA 值的 Series
    """
    return df[column].rolling(window=window).mean()


def calculate_ema(df: pd.DataFrame, column: str = "Close", span: int = 20) -> pd.Series:
    """
    计算指数移动平均线 (EMA)

    Args:
        df: 数据 DataFrame
        column: 目标列名
        span: 跨度

    Returns:
        EMA 值的 Series
    """
    return df[column].ewm(span=span, adjust=False).mean()


def calculate_rsi(df: pd.DataFrame, column: str = "Close", period: int = 14) -> pd.Series:
    """
    计算相对强弱指标 (RSI)

    Args:
        df: 数据 DataFrame
        column: 目标列名
        period: 周期

    Returns:
        RSI 值的 Series
    """
    delta = df[column].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(
    df: pd.DataFrame,
    column: str = "Close",
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """
    计算 MACD 指标

    Args:
        df: 数据 DataFrame
        column: 目标列名
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期

    Returns:
        包含 MACD 列 (MACD, Signal, Histogram) 的 DataFrame
    """
    df = df.copy()
    df["ema_fast"] = df[column].ewm(span=fast, adjust=False).mean()
    df["ema_slow"] = df[column].ewm(span=slow, adjust=False).mean()
    df["MACD"] = df["ema_fast"] - df["ema_slow"]
    df["Signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    df["Histogram"] = df["MACD"] - df["Signal"]
    return df.drop(["ema_fast", "ema_slow"], axis=1)


def calculate_bollinger_bands(
    df: pd.DataFrame, column: str = "Close", window: int = 20, num_std: float = 2.0
) -> pd.DataFrame:
    """
    计算布林带

    Args:
        df: 数据 DataFrame
        column: 目标列名
        window: 窗口大小
        num_std: 标准差倍数

    Returns:
        包含布林带列的 DataFrame
    """
    df = df.copy()
    df["BB_Middle"] = df[column].rolling(window=window).mean()
    bb_std = df[column].rolling(window=window).std()
    df["BB_Upper"] = df["BB_Middle"] + (bb_std * num_std)
    df["BB_Lower"] = df["BB_Middle"] - (bb_std * num_std)
    return df


def add_all_indicators(df: pd.DataFrame, column: str = "Close") -> pd.DataFrame:
    """
    一键添加所有常用技术指标

    Args:
        df: 数据 DataFrame
        column: 目标列名

    Returns:
        添加了所有技术指标的 DataFrame
    """
    df = df.copy()
    df = clean_data(df)
    df = calculate_returns(df, column)
    df["SMA_20"] = calculate_sma(df, column, 20)
    df["SMA_50"] = calculate_sma(df, column, 50)
    df["EMA_20"] = calculate_ema(df, column, 20)
    df["RSI_14"] = calculate_rsi(df, column, 14)
    df = calculate_macd(df, column)
    df = calculate_bollinger_bands(df, column)
    return df