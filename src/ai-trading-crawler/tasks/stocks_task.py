
from crawlers import stocks_crawler
from database import ai_trading_db
from dao import get_dao_manager
from logger import logger

def excute_his_stocks(symbol: str):

    datas = stocks_crawler.fetch_hk_stock_data_by_akshare(symbol)

    manager = get_dao_manager()
    with ai_trading_db.connection() as conn:
        manager.stocks.save_stock_data(conn=conn, symbol=symbol, type='daily', df=datas)


def excute_new_stocks(symbol: str):

    datas = stocks_crawler.fetch_hk_stock_data_by_akshare(symbol)
    last_row = datas.tail(1)

    manager = get_dao_manager()
    with ai_trading_db.connection() as conn:
        manager.stocks.save_stock_data(conn=conn, symbol=symbol, type='daily', df=last_row)