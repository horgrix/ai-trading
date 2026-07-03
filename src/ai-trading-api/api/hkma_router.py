"""
金管局流动性数据 API 路由

提供 hkma 表的查询接口：
- 查询金管局流动性数据
- 获取日期范围
"""

from typing import Optional

from fastapi import APIRouter, Query

from dao.hkma_dao import get_date_range as dao_get_date_range
from dao.hkma_dao import load_hkma_data
from database.ai_trading_db import connection

router = APIRouter(prefix="/api/v2/market/hkma", tags=["hkma"])


@router.get("/data")
def get_hkma_data(
    start_date: Optional[str] = Query(None, description="起始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
):
    """
    查询金管局流动性数据

    - **start_date**: 可选，起始日期
    - **end_date**: 可选，结束日期
    """
    with connection() as conn:
        df = load_hkma_data(conn, start_date, end_date)

    if df.empty:
        return {"count": 0, "data": []}

    df = df.reset_index()
    # 使用 end_of_date 作为日期列名（与 hkma 表结构一致）
    date_col = "end_of_date" if "end_of_date" in df.columns else "date"
    df[date_col] = df[date_col].astype(str)
    records = df.to_dict(orient="records")
    return {"count": len(records), "data": records}


@router.get("/date-range")
def get_hkma_date_range():
    """获取 hkma 表在数据库中的日期范围"""
    with connection() as conn:
        min_date, max_date = dao_get_date_range(conn, "")
    return {
        "min_date": min_date,
        "max_date": max_date,
    }