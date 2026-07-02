"""
AI Trading Crawler - 数据采集定时调度器主入口

使用 APScheduler 实现定时任务调度：
- 从 SQLite 读取定时任务配置
- 按计划执行数据采集任务
- 将执行日志和状态回写到 SQLite

运行方式:
    cd ai-trading
    python src/ai-trading-crawler/main.py
"""

import sys
from pathlib import Path

# 将 ai-trading-crawler 目录自身加入 sys.path，使所有模块可通过绝对路径互相导入
_PACKAGE_DIR = Path(__file__).resolve().parent  # ai-trading-crawler/
sys.path.insert(0, str(_PACKAGE_DIR))

from logger import logger
from tasks import hkma_task, stocks_task


# ---- 获取历史香港市场流动性数据 ----
def excute_fetch_his_hkma_data(target_date=None, day_delta=90):
    try:
        logger.info("定时任务[抓取历史香港市场流动性数据]执行中...")
        hkma_task.excute_hkma(target_date=target_date, day_delta=day_delta)
        logger.info("定时任务[抓取历史香港市场流动性数据]执行完毕!")
    except Exception as e:
        logger.error(f"定时任务[抓取历史香港市场流动性数据]执行失败! {e}")

# ---- 获取历史香港股票交易数据 ----
def excute_fetch_his_stocks_data(symbol='02400'):
    try:
        logger.info("定时任务[抓取历史香港股票交易数据]执行中...")
        stocks_task.excute_his_stocks(symbol=symbol)
        logger.info("定时任务[抓取历史香港股票交易数据]执行完毕!")
    except Exception as e:
        logger.error(f"定时任务[历史香港股票交易数据]执行失败! {e}")

# excute_fetch_his_hkma_data()
# excute_fetch_his_stocks_data()