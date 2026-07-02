import sqlite3

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


def query_stocks_short_selling(conn: sqlite3.Connection, 
    stock_code: str = None,
    start_date: str = None,
    end_date: str = None,
) -> list:
    """
    查询个股卖空数据

    参数:
        stock_code: 股票代码，可选
        start_date: 起始日期 (YYYY-MM-DD)，可选
        end_date: 结束日期 (YYYY-MM-DD)，可选

    返回:
        字典列表，每个字典包含一条记录
    """
    conn.row_factory = sqlite3.Row
    query_str = "SELECT * FROM stocks_short_selling WHERE 1=1"
    params = []

    if stock_code:
        query_str += " AND stock_code = ?"
        params.append(stock_code)
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
