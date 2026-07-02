"""
项目配置模块
"""

from pathlib import Path
from dotenv import load_dotenv

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

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

class Settings(BaseSettings):
    """应用配置."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用
    app_name: str = "AI Trading Api"
    app_version: str = "0.1.0"
    debug: bool = False

    # 服务器
    host: str = "0.0.0.0"
    port: int = 8000

    # 爬虫
    request_timeout: float = 30.0
    max_retries: int = 3
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    concurrency_limit: int = 5


@lru_cache
def get_settings() -> Settings:
    """获取应用配置单例."""
    return Settings()