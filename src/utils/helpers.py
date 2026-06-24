"""
通用工具函数
"""

import time
from functools import wraps
from typing import Callable, Any
import pandas as pd
import numpy as np


def timer(func: Callable) -> Callable:
    """装饰器：计算函数执行时间"""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[TIMER] {func.__name__} 执行耗时: {elapsed:.4f} 秒")
        return result

    return wrapper


def train_test_split_by_date(
    df: pd.DataFrame, split_ratio: float = 0.8
) -> tuple:
    """
    按时间顺序划分训练集和测试集

    Args:
        df: 按时间排序的 DataFrame
        split_ratio: 训练集比例

    Returns:
        (train_df, test_df)
    """
    split_idx = int(len(df) * split_ratio)
    return df.iloc[:split_idx], df.iloc[split_idx:]


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Min-Max 归一化

    Args:
        df: 数据 DataFrame

    Returns:
        归一化后的 DataFrame
    """
    return (df - df.min()) / (df.max() - df.min())


def standardize_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Z-Score 标准化

    Args:
        df: 数据 DataFrame

    Returns:
        标准化后的 DataFrame
    """
    return (df - df.mean()) / df.std()