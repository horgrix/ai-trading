import sqlite3
import pandas as pd

def load_hkma_data(conn: sqlite3.Connection, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    从 SQLite 数据库中加载股票数据

    参数:
        start_date: 起始日期 (YYYY-MM-DD)，可选
        end_date: 结束日期 (YYYY-MM-DD)，可选

    返回:
        DataFrame（index 为日期）
    """
    query = """SELECT end_of_date, cu_weakside, cu_strongside, disc_win_base_rate, hibor_overnight, 
                    hibor_fixing_1m, twi, opening_balance, closing_balance FROM hkma WHERE 1=1"""
    params = []
    if start_date:
        query += " AND end_of_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND end_of_date <= ?"
        params.append(end_date)
    query += " ORDER BY end_of_date ASC"

    df = pd.read_sql_query(query, conn, params=params)
    if not df.empty:
        df['date'] = pd.to_datetime(df['end_of_date'])
        df = df.set_index('end_of_date')

    print(f"[DB] 从数据库加载 {len(df)} 条数据")
    return df


def get_date_range(conn: sqlite3.Connection, symbol: str) -> tuple:
    """
    获取某只股票在数据库中的日期范围

    参数:
        symbol: 股票代码

    返回:
        (最早日期, 最晚日期) 元组，如果无数据则返回 (None, None)
    """
    cursor = conn.execute(
        "SELECT MIN(date), MAX(date) FROM hkma"
    )
    row = cursor.fetchone()
    if row and row[0]:
        return row[0], row[1]
    return None, None
