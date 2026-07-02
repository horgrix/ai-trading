"""
项目配置模块
"""

from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 根目录
ROOT_DIR = Path(__file__).parent.parent.parent

# 项目目录
PROJECT_DIR = Path(__file__).parent

# 数据目录
DATA_DIR = ROOT_DIR / "data"

# 日志目录
LOG_DIR = PROJECT_DIR / "logs"

# 数据库文件路径
DB_PATH = DATA_DIR / "ai_trading_db.sqlite"

# 创建必要的目录
for directory in [DATA_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)