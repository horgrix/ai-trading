"""
数据获取模块 - 从各种数据源获取市场数据
数据保存到 SQLite 数据库（stocks.db）中
"""

import akshare as ak
import pandas as pd
from logger import logger


def fetch_hk_stock_data_by_akshare(symbol):
    """
    获取港股日线数据，从 AKShare 拉取并

    参数:
        symbol: 股票代码，如 "00700"

    返回:
        DataFrame（index 为日期）或 None
    """

    # 从 AKShare 获取数据
    print(f"[FETCH] 从 AKShare 获取数据: symbol={symbol}")
    try:
        df = ak.stock_hk_daily(symbol=symbol, adjust="")

        if df is None or df.empty:
            logger.warning(f"[FETCH] AKShare 返回空数据: symbol={symbol}")
            return None

        # 对数据进行必要的清洗和索引设置
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')

        logger.info(f"抓取数据成功：{df.tail(5)}")
        return df

    except Exception as e:
        logger.error(f"[ERROR] 数据获取失败: {e}")
        return None