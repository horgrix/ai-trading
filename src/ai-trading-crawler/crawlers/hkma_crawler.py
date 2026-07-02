import requests
import json
from logger import logger

def fetch_interbank_liquidity_data(from_date='2026-01-01', to_date='2026-04-01'):
    """
    从香港金融管理局API获取银行同业流动性数据
    
    Args:
        from_date: 开始日期 (格式: YYYY-MM-DD)
        to_date: 结束日期 (格式: YYYY-MM-DD)
    
    Returns:
        pandas.DataFrame: 包含9个字段的数据表
    """
    
    # API URL
    url = 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity'
    
    # 请求参数
    params = {
        'from': from_date,
        'to': to_date
    }
    
    # 请求头
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # 发送GET请求
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        
        # 解析JSON数据
        data = response.json()
        
        # 提取记录
        if 'result' in data and 'records' in data['result']:
            records = data['result']['records']
            
            # 需要提取的字段
            target_fields = [
                'end_of_date',
                'cu_weakside',
                'cu_strongside',
                'disc_win_base_rate',
                'hibor_overnight',
                'hibor_fixing_1m',
                'twi',
                'opening_balance',
                'closing_balance'
            ]
            
            # 提取指定字段
            extracted_data = []
            for record in records:
                extracted_record = {}
                for field in target_fields:
                    extracted_record[field] = record.get(field, None)
                extracted_data.append(extracted_record)
            
            logger.info(f"抓取数据成功：{extracted_data[1]}")
            return extracted_data
        else:
            logger.error("API返回数据格式异常")
            logger.error("完整响应:", json.dumps(data, indent=2, ensure_ascii=False)[:500])
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        logger.error("响应内容:", response.text[:500])
        return None