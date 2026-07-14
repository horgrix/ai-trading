"""
股票交易数据 API 路由

提供 stocks 表的查询接口：
- 获取可用股票代码列表
- 获取股票数据（按代码、类型、日期范围查询）
- 获取股票日期范围
"""

from typing import Optional
import numpy as np

from fastapi import APIRouter, Query

from dao.stocks_dao import get_available_symbols as dao_get_symbols
from dao.stocks_dao import get_date_range as dao_get_date_range
from dao.stocks_dao import load_stock_data
from database.ai_trading_db import connection

from indicators.statistics_indicators import skew, kurtosis, zscore
from indicators.trend_indicators import adx, aroon, chop, psar
from indicators.volume_indicators import cmf, mfi, obv
from indicators.volatility_indicators import atr, bbands, donchian
from indicators.overlap_Indicators import ema, sma
from indicators.mtm_indicators import roc, rsi, macd, mom, stoch, ao

from strategies.strategy import BreakThroughStrategy

# 函数映射表
FUNCTION_MAP = {
    # mtm_indicators
    'roc': roc, 
    'rsi': rsi, 
    'macd': macd, 
    'mom': mom, 
    'stoch': stoch, 
    'ao': ao, 
    # overlap_Indicators
    'ema': ema, 
    'sma': sma, 
    # volatility_indicators
    'atr': atr, 
    'bbands': bbands, 
    'donchian': donchian,
    # volume_indicators
    'cmf': cmf, 
    'mfi': mfi, 
    'obv': obv,
    # trend_indicators
    'adx': adx, 
    'aroon': aroon, 
    'chop': chop, 
    'psar': psar, 
    # statistics_indicators
    'skew': skew, 
    'kurtosis': kurtosis, 
    'zscore': zscore
}

router = APIRouter(prefix="/api/v2/market/stocks", tags=["stocks"])


@router.get("/symbols")
def get_available_symbols():
    """获取数据库中所有可用的股票代码列表"""
    with connection() as conn:
        symbols = dao_get_symbols(conn)
    return {"count": len(symbols), "data": symbols}

def _query_data(symbol: str, type: str, start_date: str, end_date: str):

    with connection() as conn:
        df = load_stock_data(conn, symbol, type, start_date, end_date)

    if df.empty:
        return {"count": 0, "data": []}
    
    df = df.reset_index()
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    return df;

@router.get("/strategy_1")
def get_trading_strategies_buy(
    symbol: str = Query(..., description="股票代码"),
    type: str = Query(..., description="时间类型"),
    start_date: Optional[str] = Query(None, description="起始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)")
):
    
    df = _query_data(symbol=symbol, type=type, start_date=start_date, end_date=end_date)

    strategy = BreakThroughStrategy(df)
    df = strategy.get_data()
    df['signals'] = 0
    df.loc[strategy.get_entries(), 'signals'] = 1
    df.loc[strategy.get_exits(), 'signals'] = -1
    df = df[['date', 'close', 'RSI', 'RSI_Div_Signal', 'DC_Upper', 'DC_Lower', 'DC_Middle', 'ROC', 'CHOP', 'ADX', 'DMP', 'DMN', 'ATR', 'signals']]
    # 将 NaN 替换为 None，确保 JSON 序列化兼容
    df = df.replace({np.nan: None})
    records = df.to_dict(orient="records")
    return {"count": len(records), "data": records}

@router.get("/data")
def get_stock_data(
    symbol: str = Query(..., description="股票代码"),
    type: str = Query(..., description="时间类型"),
    start_date: Optional[str] = Query(None, description="起始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    indicators: Optional[str]= Query(None, description="指标rsi,macd"),
):
    """
    查询股票交易数据

    - **symbol**: 股票代码
    - **type**: 时间类型
    - **start_date**: 可选，起始日期
    - **end_date**: 可选，结束日期
    """
    df = _query_data(symbol=symbol, type=type, start_date=start_date, end_date=end_date)

    if indicators:
        indicator_list: list[str] = indicators.split(",")
        for indicator in indicator_list:
            if indicator not in FUNCTION_MAP:
                continue
            df = FUNCTION_MAP[indicator](df)

    # 将 NaN 替换为 None，确保 JSON 序列化兼容
    df = df.replace({np.nan: None})
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