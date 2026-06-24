"""
项目配置模块
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

# 数据目录
DATA_DIR = ROOT_DIR / "data"

# 日志目录
LOG_DIR = ROOT_DIR / "logs"

# 配置目录
CONFIG_DIR = ROOT_DIR / "config"

# 创建必要的目录
for directory in [DATA_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# API 配置 (从环境变量读取)
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
TRADING_API_KEY = os.getenv("TRADING_API_KEY", "")
TRADING_API_SECRET = os.getenv("TRADING_API_SECRET", "")

# 交易配置
INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", "100000"))
MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "0.1"))  # 10%

# 数据配置
DEFAULT_TIMEFRAME = "1d"  # 1d, 1h, 15m, 5m, 1m
DEFAULT_LOOKBACK_DAYS = 365

# 模型配置
MODEL_DIR = ROOT_DIR / "models_saved"
MODEL_DIR.mkdir(parents=True, exist_ok=True)