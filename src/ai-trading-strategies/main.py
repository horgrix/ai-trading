import pandas as pd
import pandas_ta as ta
from pandas import DataFrame

from dao import get_dao_manager
from database.ai_trading_db import connection

from indicators.statistics_indicators import std, mad, skew, kurtosis, zscore
from indicators.trend_indicators import adx, aroon, chop, psar, vortex
from indicators.volume_indicators import ad, aobv, cmf, mfi, obv
from indicators.volatility_indicators import atr, bbands, kc, donchian
from indicators.overlap_Indicators import ema, sma, hma, wma, kama
from indicators.mtm_indicators import roc, rsi, macd, mom, stoch, willr, ao, cci

df = pd.DataFrame()
manager = get_dao_manager()
with connection() as conn:
    df = manager.stocks.load_stock_data(conn, symbol='02400', type='daily', start_date='2019-01-01', end_date='2026-07-01')


df = roc(df)
df = rsi(df)
# df = macd(df)
# df = mom(df)
# df = stoch(df)
# df = willr(df)
# df = ao(df)
# df = cci(df)
print(df.tail(10))
# 3. 查看添加了指标列的数据
