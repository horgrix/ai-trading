"""
AI Trading - 主入口文件
"""

import sys
from pathlib import Path

# 将 src 目录添加到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src import config


def main():
    """主函数"""
    print("=" * 50)
    print("  AI Trading - 量化交易系统")
    print("=" * 50)
    print(f"  Python 版本: {sys.version.split()[0]}")
    print(f"  项目路径: {Path(__file__).parent}")
    print("=" * 50)

    # TODO: 在此添加主要逻辑
    print("\n项目初始化完成！请开始编写交易策略和模型。")


if __name__ == "__main__":
    main()