import sqlite3
import pandas as pd
from typing import Any, Dict

# 市场卖空
MARKET_SHORT_SELLING_SCHEMA_SQL="""
CREATE TABLE IF NOT EXISTS market_short_selling (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    total_turnover_hkd TEXT,
    all_ss_percentage TEXT,
    ex_exchange_traded_products_ss_percentage TEXT,
    exchange_traded_products_only_ss_percentage TEXT
)
"""

# 时间
INDEX_MARKET_SS_DATE="""
CREATE INDEX IF NOT EXISTS idx_market_ss_date ON market_short_selling(date)
"""

# 个股卖空
STOCK_SHORT_SELLING_SCHEMA_SQL="""
CREATE TABLE IF NOT EXISTS stocks_short_selling (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    date TEXT NOT NULL,
    short_sell_volume TEXT,
    short_sell_turnover_hkd TEXT,
    UNIQUE(stock_code, date)
)
"""

# 时间
INDEX_STOCK_SS_STOCK_CODE_DATE="""
CREATE INDEX IF NOT EXISTS idx_market_ss_stock_code_date ON stocks_short_selling(stock_code, date)
"""

def save_market_short_selling(conn: sqlite3.Connection, 
    data_date: str,
    total_turnover_hkd: str,
    all_ss_percentage: str,
    ex_exchange_traded_products_ss_percentage: str,
    exchange_traded_products_only_ss_percentage: str,
) -> bool:
    """
    保存市场卖空汇总数据到 market_short_selling 表

    参数:
        data_date: 数据日期 (YYYY-MM-DD)
        total_turnover_hkd: 市场总成交(HKD)
        all_ss_percentage: 卖空所有指定证券占市场总成交的百分比
        ex_exchange_traded_products_ss_percentage: 卖空指定证券(不包括交易所买卖产品)占市场总成交的百分比
        exchange_traded_products_only_ss_percentage: 卖空指定证券(仅限交易所买卖产品)占市场总成交的百分比

    返回:
        是否保存成功
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO market_short_selling (
                date, total_turnover_hkd, all_ss_percentage,
                ex_exchange_traded_products_ss_percentage,
                exchange_traded_products_only_ss_percentage
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            data_date,
            total_turnover_hkd,
            all_ss_percentage,
            ex_exchange_traded_products_ss_percentage,
            exchange_traded_products_only_ss_percentage
        ))
        conn.commit()
        print(f"[AI-Trading DB] 已保存市场卖空数据: date={data_date}")
        return True
    except Exception as e:
        print(f"[AI-Trading DB] 保存市场卖空数据失败: {e}")
        return False


def save_stock_short_selling(conn: sqlite3.Connection, 
    data_date: str,
    stock_code: str,
    stock_name: str,
    short_sell_volume: str,
    short_sell_turnover_hkd: str,
) -> bool:
    """
    保存个股卖空数据到 stocks_short_selling 表

    参数:
        data_date: 数据日期 (YYYY-MM-DD)
        stock_code: 股票代码
        stock_name: 股票名称
        short_sell_volume: 卖空成交量(股数)
        short_sell_turnover_hkd: 卖空成交金额(HKD)

    返回:
        是否保存成功
    """
    try:
        conn.execute("""
            INSERT OR REPLACE INTO stocks_short_selling (
                date, stock_code, stock_name,
                short_sell_volume, short_sell_turnover_hkd
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            data_date,
            stock_code,
            stock_name,
            short_sell_volume,
            short_sell_turnover_hkd
        ))
        conn.commit()
        print(f"[AI-Trading DB] 已保存个股卖空数据: date={data_date}, code={stock_code}, name={stock_name}")
        return True
    except Exception as e:
        print(f"[AI-Trading DB] 保存个股卖空数据失败: {e}")
        return False

def get_max_date(conn: sqlite3.Connection) -> str | None:
    """
    获取数据库中 market_short_selling 表的最大日期

    返回:
        最大日期字符串 (YYYY-MM-DD)，无数据返回 None
    """
    cursor = conn.execute("SELECT MAX(date) FROM market_short_selling")
    row = cursor.fetchone()
    return row[0] if row and row[0] else None

def load_market_short_selling(conn: sqlite3.Connection, 
    start_date: str = None,
    end_date: str = None,
) -> list:
    """
    查询市场卖空汇总数据

    参数:
        start_date: 起始日期 (YYYY-MM-DD)，可选
        end_date: 结束日期 (YYYY-MM-DD)，可选

    返回:
        字典列表，每个字典包含一条记录
    """
    conn.row_factory = sqlite3.Row
    query_str = "SELECT * FROM market_short_selling WHERE 1=1"
    params = []

    if start_date:
        query_str += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query_str += " AND date <= ?"
        params.append(end_date)

    query_str += " ORDER BY date ASC"

    cursor = conn.execute(query_str, params)
    rows = [dict(r) for r in cursor.fetchall()]
    return rows