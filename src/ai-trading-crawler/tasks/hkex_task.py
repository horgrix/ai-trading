from datetime import datetime
from crawlers import hkex_crawler
from dao import get_dao_manager
from database.ai_trading_db import connection

def excute_hkex():

    today = datetime.now().strftime("%Y-%m-%d")
    data = hkex_crawler.fetch_short_selling_data()

    manager = get_dao_manager()
    with connection() as conn:
        data_date = today
        total_turnover_hkd = data.get("市场总成交(HKD)")
        ss_percentage_data = data.get("百分比")
        all_ss_percentage = ss_percentage_data.get("卖空所有指定证券占市场总成交的百分比")
        ex_exchange_traded_products_ss_percentage = ss_percentage_data.get("卖空指定证券(不包括交易所买卖产品)占市场总成交的百分比")
        exchange_traded_products_only_ss_percentage = ss_percentage_data.get("卖空指定证券(仅限交易所买卖产品)占市场总成交的百分比")
        manager.hkex.save_market_short_selling(conn=conn, data_date=data_date,
                                               total_turnover_hkd=total_turnover_hkd, 
                                               all_ss_percentage=all_ss_percentage, 
                                               ex_exchange_traded_products_ss_percentage=ex_exchange_traded_products_ss_percentage,
                                               exchange_traded_products_only_ss_percentage=exchange_traded_products_only_ss_percentage)
        
        xd_data = data.get("心动公司")
        stock_code = xd_data.get("代码")
        stock_name = "心动公司"
        short_sell_volume = xd_data.get("成交量(股数)")
        short_sell_turnover_hkd = xd_data.get("成交金额(HKD)")
        manager.hkex.save_stock_short_selling(conn=conn, data_date=today, 
                                              stock_code=stock_code, stock_name=stock_name,
                                              short_sell_volume=short_sell_volume, short_sell_turnover_hkd=short_sell_turnover_hkd)

