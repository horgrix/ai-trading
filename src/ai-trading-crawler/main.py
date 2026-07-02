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
import time
from pathlib import Path

# 将 ai-trading-crawler 目录自身加入 sys.path，使所有模块可通过绝对路径互相导入
_PACKAGE_DIR = Path(__file__).resolve().parent  # ai-trading-crawler/
sys.path.insert(0, str(_PACKAGE_DIR))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from logger import logger
from tasks import hkma_task, hkex_task, stocks_task

def _on_job_event(event):
    """APScheduler 任务事件回调"""
    if event.exception:
        logger.error(f"[APScheduler] 任务异常: job_id={event.job_id}, exception={event.exception}")
    else:
        logger.info(f"[APScheduler] 任务完成: job_id={event.job_id}")

# ============================================================
# 任务函数定义
# ============================================================

# ---- 获取每日香港市场流动性数据 ----
def excute_fetch_daily_hkma_data():
    try:
        logger.info("定时任务[抓取每日香港市场流动性数据]执行中...")
        hkma_task.excute_hkma(day_delta=7)
        logger.info("定时任务[抓取每日香港市场流动性数据]执行完毕!")
    except Exception as e:
        logger.error(f"定时任务[抓取每日香港市场流动性数据]执行失败! {e}")

# ---- 获取历史香港市场流动性数据 ----
def excute_fetch_his_hkma_data():
    try:
        logger.info("定时任务[抓取历史香港市场流动性数据]执行中...")
        hkma_task.excute_hkma(day_delta=90)
        logger.info("定时任务[抓取历史香港市场流动性数据]执行完毕!")
    except Exception as e:
        logger.error(f"定时任务[抓取历史香港市场流动性数据]执行失败! {e}")

# ---- 获取每日香港股市做空数据 ----
def excute_fetch_daily_hkex_data():
    try:
        logger.info("定时任务[抓取每日香港股市做空数据]执行中...")
        hkex_task.excute_hkex()
        logger.info("定时任务[抓取每日香港股市做空数据]执行完毕!")
    except Exception as e:
        logger.error(f"定时任务[抓取每日香港股市做空数据]执行失败! {e}")

# ---- 获取每日香港股票交易数据 ----
def excute_fetch_daily_stocks_data():
    try:
        logger.info("定时任务[抓取每日香港股票交易数据]执行中...")
        stocks_task.excute_new_stocks(symbol='02400')
        logger.info("定时任务[抓取每日香港股票交易数据]执行完毕!")
    except Exception as e:
        logger.error(f"定时任务[每日香港股票交易数据]执行失败! {e}")

# ---- 获取历史香港股票交易数据 ----
def excute_fetch_his_stocks_data():
    try:
        logger.info("定时任务[抓取历史香港股票交易数据]执行中...")
        stocks_task.excute_his_stocks(symbol='02400')
        logger.info("定时任务[抓取历史香港股票交易数据]执行完毕!")
    except Exception as e:
        logger.error(f"定时任务[历史香港股票交易数据]执行失败! {e}")

# ============================================================
# 调度器配置
# ============================================================
jobstores = {
    'default': SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")
}
executors = {
    'default': ThreadPoolExecutor(max_workers=10)
}
job_defaults = {
    'coalesce': True,
    'max_instances': 4,
}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='UTC',
)

# 注册事件监听
scheduler.add_listener(_on_job_event, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

# ---- 注册定时任务 ----
# 抓取每日香港市场流动性数据：每天20:00执行
scheduler.add_job(
    excute_fetch_daily_hkma_data,
    trigger=CronTrigger(hour=20),
    id='fetch_daily_hkma_data',
    replace_existing=True,
    name='抓取每日香港市场流动性数据：每天20:00执行',
)

# 抓取历史香港市场流动性数据：每月第1天01:00执行
scheduler.add_job(
    excute_fetch_his_hkma_data,
    trigger=CronTrigger(day=1, hour=1),
    id='fetch_his_hkma_data',
    replace_existing=True,
    name='抓取历史香港市场流动性数据：每月第1天01:00执行',
)

# 获取每日香港股市做空数据：每天21:00执行
scheduler.add_job(
    excute_fetch_daily_hkex_data,
    trigger=CronTrigger(hour=21),
    id='fetch_daily_hkex_data',
    replace_existing=True,
    name='获取每日香港股市做空数据：每天21:00执行',
)

# 获取每日香港股票交易数据：每天22:00执行
scheduler.add_job(
    excute_fetch_daily_stocks_data,
    trigger=CronTrigger(hour=22),
    id='fetch_daily_stocks_data',
    replace_existing=True,
    name='获取每日香港股票交易数据：每天22:00执行',
)

# 获取历史香港股票交易数据：每月第1天04:00执行
scheduler.add_job(
    excute_fetch_his_stocks_data,
    trigger=CronTrigger(day=1, hour=4),
    id='fetch_his_stocks_data',
    replace_existing=True,
    name='获取历史香港股票交易数据：每月第1天04:00执行',
)

# ============================================================
# 启动
# ============================================================
"""
启动定时调度器（阻塞运行，使用 APScheduler）
"""
logger.info("=" * 60)
logger.info("  AI Trading Crawler - 定时数据采集调度器 (APScheduler)")
logger.info("=" * 60)
scheduler.start()
logger.info("[Scheduler] APScheduler 已启动，等待任务执行...")
logger.info("[Scheduler] 按 Ctrl+C 停止调度器")

try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    logger.info("收到终止信号，正在关闭调度器...")
    scheduler.shutdown()