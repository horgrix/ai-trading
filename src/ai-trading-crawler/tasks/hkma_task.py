from datetime import datetime
from dateutil.relativedelta import relativedelta
from crawlers import hkma_crawler
from dao import get_dao_manager
from database import ai_trading_db

def excute_hkma(target_date: str = None, day_delta: int = 90):

    try:
        now = datetime.now().strptime(target_date, "%Y-%m-%d")
        if target_date is not None:
            now = datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(
            f"起始日期 '{target_date}' 格式错误，应为[%Y-%m-%d]"
        ) from e

    from_date = (now - relativedelta(days=day_delta)).strftime("%Y-%m-%d")
    to_date = now.strftime("%Y-%m-%d")

    datas = hkma_crawler.fetch_interbank_liquidity_data(from_date=from_date, to_date=to_date)

    manager = get_dao_manager()
    with ai_trading_db.connection() as conn:
        manager.hkma.save_hkma_data(conn=conn, datas=datas)


