import re
import requests
from datetime import date, datetime
from logger import logger


def fetch_short_selling_data():
    """
    解析港交所卖空数据HTML，提取关键信息

    Returns:
        dict: 包含解析结果的字典，失败返回 None
    """

    url='https://www.hkex.com.hk/chi/stat/smstat/ssturnover/ncms/ashtmain_c.htm'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        result = {}

        # 发送GET请求
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        response.encoding = 'big5'  # 港交所网页使用big5编码
        html_content = response.text

        # 1. 提取市场总成交（只需要一次，因为三处都是同一个值）
        market_total_pattern = r'市場總成交[^\d]*HKD\s*([\d,]+)'
        market_match = re.search(market_total_pattern, html_content)
        if market_match:
            result['市场总成交(HKD)'] = market_match.group(1)
        
        # 2. 提取三个百分比
        percentages = {}
        patterns = {
            '卖空所有指定证券占市场总成交的百分比': r'賣空所有指定證券佔市場總成交的百分比[^\d]*(\d+%)',
            '卖空指定证券(不包括交易所买卖产品)占市场总成交的百分比': r'賣空指定證券（不包括交易所買賣產品）佔市場總成交的百分比[^\d]*(\d+%)',
            '卖空指定证券(仅限交易所买卖产品)占市场总成交的百分比': r'賣空指定證券（僅限交易所買賣產品）佔市場總成交的百分比[^\d]*(\d+%)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, html_content)
            if match:
                percentages[key] = match.group(1)
        
        result['百分比'] = percentages
        
        # 3. 提取心动公司(2400)的数据
        # 在HTML中搜索 "2400" 前后文
        xindong_pattern = r'(\d{3,4})\s+心動公司[^\d]*([\d,]+)\s+([\d,]+)'
        xindong_match = re.search(xindong_pattern, html_content)
        if xindong_match:
            result['心动公司'] = {
                '代码': xindong_match.group(1),
                '成交量(股数)': xindong_match.group(2),
                '成交金额(HKD)': xindong_match.group(3)
            }
        
        logger.info(f"数据抓取成功: {result}")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        return None