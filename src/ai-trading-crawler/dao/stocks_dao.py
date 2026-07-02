import sqlite3
import pandas as pd

# 股票明细表
SCHEMA_SQL="""
CREATE TABLE IF NOT EXISTS stocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    type TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    UNIQUE(symbol, type, date)
)
"""

# 股票 + 时间粒度
INDEX_SYMBOL_TYPE="""
CREATE INDEX IF NOT EXISTS idx_stock_daily_symbol ON stocks(symbol, type)
"""

# 股票 + 时间粒度 + 时间
INDEX_SYMBOL_TYPE_DATE="""
CREATE INDEX IF NOT EXISTS idx_stock_daily_symbol ON stocks(symbol, type, date)
"""

def save_stock_data(conn: sqlite3.Connection, symbol: str, type: str, df: pd.DataFrame) -> int:
    """
    将股票数据保存到 SQLite 数据库中

    参数:
        symbol: 股票代码
        df: 包含 OHLCV 数据的 DataFrame（index 为日期）

    返回:
        插入的行数
    """
    if df is None or df.empty:
        print(f"[DB] 无数据需要保存: {symbol}")
        return 0

    rows_inserted = 0
    for idx, row in df.iterrows():
        date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, 'strftime') else str(idx)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO stocks (symbol, type, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                type,
                date_str,
                float(row.get('open', 0)) if pd.notna(row.get('open')) else None,
                float(row.get('high', 0)) if pd.notna(row.get('high')) else None,
                float(row.get('low', 0)) if pd.notna(row.get('low')) else None,
                float(row.get('close', 0)) if pd.notna(row.get('close')) else None,
                float(row.get('volume', 0)) if pd.notna(row.get('volume')) else None,
            ))
            rows_inserted += 1
        except Exception:
            continue

    conn.commit()
    print(f"[DB] 已保存 {rows_inserted} 条数据: symbol={symbol}")
    return rows_inserted