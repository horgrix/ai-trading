"""
股票交易数据 API 路由

提供 stocks 表的查询接口：
- 获取可用股票代码列表
- 获取股票数据（按代码、类型、日期范围查询）
- 获取股票日期范围
"""

from typing import Optional

from fastapi import APIRouter, Query

from dao.stocks_dao import get_available_symbols as dao_get_symbols
from dao.stocks_dao import get_date_range as dao_get_date_range
from dao.stocks_dao import load_stock_data
from database.ai_trading_db import connection

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/symbols")
def get_available_symbols():
    """获取数据库中所有可用的股票代码列表"""
    with connection() as conn:
        symbols = dao_get_symbols(conn)
    return {"count": len(symbols), "data": symbols}


@router.get("/data")
def get_stock_data(
    symbol: str = Query(..., description="股票代码"),
    type: str = Query(..., description="时间类型"),
    start_date: Optional[str] = Query(None, description="起始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
):
    """
    查询股票交易数据

    - **symbol**: 股票代码
    - **type**: 时间类型
    - **start_date**: 可选，起始日期
    - **end_date**: 可选，结束日期
    """
    with connection() as conn:
        df = load_stock_data(conn, symbol, type, start_date, end_date)

    if df.empty:
        return {"count": 0, "data": []}

    df = df.reset_index()
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    records = df.to_dict(orient="records")
    return {"count": len(records), "data": records}


@router.get("/date-range")
def get_stock_date_range(
    symbol: str = Query(..., description="股票代码"),
):
    """获取指定股票在数据库中的日期范围"""
    with connection() as conn:
        min_date, max_date = dao_get_date_range(conn, symbol)
    return {
        "symbol": symbol,
        "min_date": min_date,
        "max_date": max_date,
    }