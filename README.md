# AI Trading

基于 Python 的 AI 量化交易项目。

## 项目结构

```
ai-trading/
├── src/                # 源代码
│   ├── __init__.py
│   ├── data/           # 数据获取与处理
│   ├── models/         # AI 模型
│   ├── strategies/     # 交易策略
│   └── utils/          # 工具函数
├── tests/              # 测试
├── config/             # 配置文件
├── notebooks/          # Jupyter Notebook
├── main.py             # 入口文件
├── requirements.txt    # 依赖
└── README.md
```

## 快速开始

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

## 开发

```bash
# 运行测试
pytest

# 代码格式化
black .

# 代码检查
flake8 src/