"""
港交所卖空数据 API 路由

提供 market_short_selling 和 stocks_short_selling 表的查询接口：
- 市场卖空汇总数据查询
- 个股卖空数据查询
- 最大日期查询
"""

from typing import Optional

from fastapi import APIRouter, Query

from dao.hkex_dao import get_max_date as dao_get_max_date
from dao.hkex_dao import load_market_short_selling
from dao.hkex_dao import query_stocks_short_selling
from database.ai_trading_db import connection

router = APIRouter(prefix="/api/v2/market/hkex", tags=["hkex"])


@router.get("/market-short-selling")
def get_market_short_selling(
    start_date: Optional[str] = Query(None, description="起始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
):
    """
    查询市场卖空汇总数据

    - **start_date**: 可选，起始日期
    - **end_date**: 可选，结束日期
    """
    with connection() as conn:
        rows = load_market_short_selling(conn, start_date, end_date)
    return {"count": len(rows), "data": rows}


@router.get("/stocks-short-selling")
def get_stocks_short_selling(
    stock_code: Optional[str] = Query(None, description="股票代码"),
    start_date: Optional[str] = Query(None, description="起始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
):
    """
    查询个股卖空数据

    - **stock_code**: 可选，股票代码
    - **start_date**: 可选，起始日期
    - **end_date**: 可选，结束日期
    """
    with connection() as conn:
        rows = query_stocks_short_selling(conn, stock_code, start_date, end_date)
    return {"count": len(rows), "data": rows}


@router.get("/max-date")
def get_hkex_max_date():
    """获取 market_short_selling 表的最大日期"""
    with connection() as conn:
        max_date = dao_get_max_date(conn)
    return {"max_date": max_date}