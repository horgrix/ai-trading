import sqlite3

from config import DB_PATH
from dao import hkex_dao, hkma_dao, stocks_dao
from contextlib import contextmanager
from logger import logger


# ---- 连接管理 ---- 
def _get_connection() -> sqlite3.Connection:
    """获取一个新的同步 SQLite 连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = 10000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA mmap_size = 268435456")
    return conn

@contextmanager
def connection():
    """
    同步连接上下文管理器，自动关闭连接
    """
    conn = _get_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection = None):
    """
    初始化数据库，创建所有必要的表结构
    
    参数:
        conn: 可选的数据库连接，如果不提供则自动创建并关闭
    """
    auto_close = False
    if conn is None:
        conn = _get_connection()
        auto_close = True
    
    try:
        # 市场卖空汇总表
        conn.execute(hkex_dao.MARKET_SHORT_SELLING_SCHEMA_SQL)
        conn.execute(hkex_dao.INDEX_MARKET_SS_DATE)
        # 个股卖空数据表
        conn.execute(hkex_dao.STOCK_SHORT_SELLING_SCHEMA_SQL)
        conn.execute(hkex_dao.INDEX_STOCK_SS_STOCK_CODE_DATE)
        # 香港流动性数据表
        conn.execute(hkma_dao.SCHEMA_SQL)
        conn.execute(hkma_dao.INDEX_HKMA_DATE)
        # 股票交易数据表
        conn.execute(stocks_dao.SCHEMA_SQL)
        conn.execute(stocks_dao.INDEX_SYMBOL_TYPE)
        conn.execute(stocks_dao.INDEX_SYMBOL_TYPE_DATE)
        
        conn.commit()
        logger.info(f"[DAO Manager] 数据库初始化完成: {str(DB_PATH)}")
    finally:
        if auto_close:
            conn.close()

init_db()