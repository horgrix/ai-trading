import sqlite3
import pandas as pd

def load_stock_data(conn: sqlite3.Connection, symbol: str, type: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    从 SQLite 数据库中加载股票数据

    参数:
        symbol: 股票代码
        type: 时间类型
        start_date: 起始日期 (YYYY-MM-DD)，可选
        end_date: 结束日期 (YYYY-MM-DD)，可选

    返回:
        DataFrame（index 为日期）
    """
    query = "SELECT date, open, high, low, close, volume FROM stocks WHERE symbol = ? AND type = ?"
    params = [symbol, type]

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date ASC"

    df = pd.read_sql_query(query, conn, params=params)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

    print(f"[DB] 从数据库加载 {len(df)} 条数据: symbol={symbol}")
    return df


def get_available_symbols(conn: sqlite3.Connection) -> list:
    """
    获取数据库中所有可用的股票代码列表

    返回:
        股票代码列表
    """
    cursor = conn.execute("SELECT DISTINCT symbol FROM stocks ORDER BY symbol")
    symbols = [row[0] for row in cursor.fetchall()]
    return symbols


def get_date_range(conn: sqlite3.Connection, symbol: str) -> tuple:
    """
    获取某只股票在数据库中的日期范围

    参数:
        symbol: 股票代码

    返回:
        (最早日期, 最晚日期) 元组，如果无数据则返回 (None, None)
    """
    cursor = conn.execute(
        "SELECT MIN(date), MAX(date) FROM stocks WHERE symbol = ?",
        (symbol,)
    )
    row = cursor.fetchone()
    if row and row[0]:
        return row[0], row[1]
    return None, None
