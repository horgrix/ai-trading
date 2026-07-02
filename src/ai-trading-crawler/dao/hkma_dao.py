import sqlite3
import pandas as pd
from typing import Any, Dict

# 股票明细表
SCHEMA_SQL="""
CREATE TABLE IF NOT EXISTS hkma (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    end_of_date TEXT NOT NULL,
    cu_weakside REAL,
    cu_strongside REAL,
    disc_win_base_rate REAL,
    hibor_overnight REAL,
    hibor_fixing_1m REAL,
    twi REAL,
    opening_balance REAL,
    closing_balance REAL,
    UNIQUE(end_of_date)
)
"""

# 时间
INDEX_HKMA_DATE="""
CREATE INDEX IF NOT EXISTS idx_hkma_end_of_date ON hkma(end_of_date)
"""

def save_hkma_data(conn: sqlite3.Connection, datas: list[Dict[str, Any]]) -> int:
    """
    将股票数据保存到 SQLite 数据库中

    参数:
        symbol: 股票代码
        df: 包含 OHLCV 数据的 DataFrame（index 为日期）

    返回:
        插入的行数
    """
    if datas is None or len(datas) == 0:
        print(f"[DB] 无数据需要保存")
        return 0

    rows_inserted = 0
    for row in datas:
        date_str = row.get('end_of_date')
        try:
            conn.execute("""
                INSERT OR REPLACE INTO hkma (end_of_date, cu_weakside, cu_strongside, 
                         disc_win_base_rate, hibor_overnight, hibor_fixing_1m, twi, opening_balance, closing_balance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                date_str,
                row.get('cu_weakside'),
                row.get('cu_strongside'),
                row.get('disc_win_base_rate'),
                row.get('hibor_overnight'),
                row.get('hibor_fixing_1m'),
                row.get('twi'),
                row.get('opening_balance'),
                row.get('closing_balance')
            ))
            rows_inserted += 1
        except Exception:
            continue

    conn.commit()
    print(f"[DB] 已保存 {rows_inserted} 条数据")
    return rows_inserted