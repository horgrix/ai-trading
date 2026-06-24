"""
数据获取模块 - 从各种数据源获取市场数据
"""

import akshare as ak
import pandas as pd
import os
from datetime import datetime, timedelta


def get_hk_stock_data_with_cache(symbol, start_date, end_date, cache_dir="./stock_cache"):
    """
    带本地缓存的港股数据获取函数
    """
    # 1. 准备缓存文件路径
    os.makedirs(cache_dir, exist_ok=True)
    # 用股票代码和日期范围生成文件名，方便管理
    cache_file = os.path.join(cache_dir, f"{symbol}_{start_date}_{end_date}.csv")

    # 2. 检查本地缓存是否存在且有效
    if os.path.exists(cache_file):
        # 可以添加一个简单的过期检查，比如缓存超过1天就重新获取
        file_modified_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - file_modified_time < timedelta(days=1):
            print(f"[CACHE] 从缓存加载数据: {cache_file}")
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            return df
        else:
            print(f"[CACHE] 缓存已过期，重新获取...")

    # 3. 缓存不存在或已过期，从网络获取
    print(f"[FETCH] 从 AKShare 获取数据...")
    # 注意：stock_hk_daily 可能不支持 start_date/end_date 参数，这里仅作示例
    # 根据你的情况，可以先获取全量再在本地筛选
    try:
        # 示例：获取港股所有历史数据
        df = ak.stock_hk_daily(symbol=symbol, adjust="")
        # 如果接口支持日期参数，可以在这里传入
        # df = ak.stock_hk_daily(symbol=symbol, start_date=start_date, end_date=end_date, adjust="")
        
        # 对数据进行必要的清洗和索引设置
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
        
        # 按日期范围筛选
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        
        # 4. 保存到本地缓存
        df.to_csv(cache_file)
        print(f"[CACHE] 数据已缓存到: {cache_file}")
        return df
    except Exception as e:
        print(f"[ERROR] 数据获取失败: {e}")
        return None