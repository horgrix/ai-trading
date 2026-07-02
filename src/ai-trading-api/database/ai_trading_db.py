import sqlite3

from config import DB_PATH
from contextlib import contextmanager

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