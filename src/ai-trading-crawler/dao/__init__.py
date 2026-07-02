"""
DAO 管理对象 - 统一管理所有数据访问操作

提供 DAOManager 类，封装：
- 数据库连接管理（连接池）
- 表结构初始化
- 股票数据 CRUD
- 港交所卖空数据 CRUD  
- 金管局流动性数据 CRUD
"""

from typing import Optional

from dao import stocks_dao, hkex_dao, hkma_dao


class DAOManager:
    """
    DAO 管理对象，统一管理所有数据访问层操作。
    
    用法：
        # 同步模式
        manager = DAOManager(db_path)
        manager.init_db()
        manager.stocks.save_stock_data(conn, symbol, type, df)
        
        # 异步模式（推荐与 aiosqlite 连接池配合使用）
        async with manager.get_connection() as conn:
            manager.stocks.save_stock_data(conn, symbol, type, df)
    """
    
    def __init__(self, db_path: str = None):
        """
        初始化 DAO 管理器
        
        参数:
            db_path: 数据库文件路径，默认使用 ai_trading_db.DB_PATH
        """
        if db_path is None:
            from database.ai_trading_db import DB_PATH
            db_path = str(DB_PATH)
        self._db_path = db_path
    
    # ---- 子模块访问器（提供命名空间隔离） ----
    
    @property
    def stocks(self):
        """股票交易数据 DAO"""
        return stocks_dao
    
    @property
    def hkex(self):
        """港交所卖空数据 DAO"""
        return hkex_dao
    
    @property
    def hkma(self):
        """金管局流动性数据 DAO"""
        return hkma_dao


# 创建全局默认 DAO 管理器实例
_dao_manager: Optional[DAOManager] = None


def get_dao_manager(db_path: str = None) -> DAOManager:
    """
    获取 DAO 管理器单例
    
    参数:
        db_path: 数据库路径，默认使用配置的路径
    
    返回:
        DAOManager 实例
    """
    global _dao_manager
    if _dao_manager is None:
        _dao_manager = DAOManager(db_path)
    return _dao_manager


def reset_dao_manager():
    """重置 DAO 管理器（主要用于测试）"""
    global _dao_manager
    _dao_manager = None