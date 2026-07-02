"""
日志模块
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

from config import LOG_DIR


def setup_logger(
    name: str = "ai_trading_crawler",
    level: int = logging.INFO,
    log_to_file: bool = True,
) -> logging.Logger:
    """
    设置日志器

    Args:
        name: 日志器名称
        level: 日志级别
        log_to_file: 是否写入文件

    Returns:
        配置好的 Logger 对象
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 格式
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件 handler
    if log_to_file:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / f"{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 默认日志器
logger = setup_logger()