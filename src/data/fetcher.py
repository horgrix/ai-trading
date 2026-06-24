"""
数据获取模块 - 从各种数据源获取市场数据
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List

from ..config import DEFAULT_LOOKBACK_DAYS


def fetch_stock_data(
    symbol: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    interval: str = "1d",
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> pd.DataFrame:
    """
    获取股票历史数据

    Args:
        symbol: 股票代码 (如 'AAPL', '600519.SS')
        start: 开始日期 'YYYY-MM-DD'，None 则自动计算
        end: 结束日期 'YYYY-MM-DD'，None 则为今天
        interval: 数据间隔 (1m, 5m, 15m, 1h, 1d, 1wk, 1mo)
        lookback_days: 回溯天数（当 start 为 None 时使用）

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume, etc.
    """
    if end is None:
        end = datetime.now().strftime("%Y-%m-%d")
    if start is None:
        start = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end, interval=interval)

    if df.empty:
        raise ValueError(f"未获取到 {symbol} 在 {start} 至 {end} 期间的数据")

    return df


def fetch_multiple_stocks(
    symbols: List[str],
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """
    批量获取多只股票数据

    Args:
        symbols: 股票代码列表
        start: 开始日期
        end: 结束日期

    Returns:
        包含多只股票数据的 DataFrame
    """
    if end is None:
        end = datetime.now().strftime("%Y-%m-%d")
    if start is None:
        start = (datetime.now() - timedelta(days=DEFAULT_LOOKBACK_DAYS)).strftime(
            "%Y-%m-%d"
        )

    data = yf.download(symbols, start=start, end=end, group_by="ticker")

    return data


def get_stock_info(symbol: str) -> dict:
    """
    获取股票基本信息

    Args:
        symbol: 股票代码

    Returns:
        包含股票基本信息的字典
    """
    ticker = yf.Ticker(symbol)
    info = ticker.info
    return info