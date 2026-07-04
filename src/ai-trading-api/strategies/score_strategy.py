import pandas_ta as ta
import pandas as pd

from indicators.statistics_indicators import skew, kurtosis, zscore
from indicators.trend_indicators import adx, aroon, chop, psar
from indicators.volume_indicators import cmf, obv
from indicators.volatility_indicators import atr, bbands
from indicators.mtm_indicators import rsi, macd, stoch

"""
五维度综合分析框架
维度	核心指标	            作用	              信号类型
趋势    PSAR,ADX,CHOP   判断方向、强度、市场状态	 趋势过滤器
动量    RSI,MACD,STOCH  衡量动能、超买超卖	        入场/出场信号
成交量  OBV,CMF         确认资金流向	           信号确认器
波动率  ATR,BBANDS      风险管理、止损设置	        仓位/止损管理器
统计    ZSCORE,SKEW     识别极端值、评估风险	    预警过滤器
"""

def composite_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    五维度综合信号生成函数
    返回包含综合评分的DataFrame
    """
    df = df.copy()
    
    # ============================================================
    # 维度1：趋势得分 (-2 ~ +2)
    # ============================================================
    # PSAR方向 (1=上升, -1=下降)
    df = psar(df)
    df['trend_score'] = 0.0
    df.loc[df['PSAR_State'] == 1, 'trend_score'] += 1
    df.loc[df['PSAR_State'] == -1, 'trend_score'] -= 1
    
    # ADX强度加成 (ADX>25时，趋势得分权重加大)
    df = adx(df)
    df.loc[df['ADX_14'] > 25, 'trend_score'] += df['trend_score'].abs() * 0.5
    
    # CHOP过滤 (震荡市时降低趋势得分权重)
    df = chop(df)
    df.loc[df['CHOP_14'] > 61.8, 'trend_score'] = df['trend_score'] * 0.5
    
    # AROON确认
    df = aroon(df)
    df.loc[(df['AROONU_14'] > 70) & (df['trend_score'] > 0), 'trend_score'] += 0.5
    df.loc[(df['AROOND_14'] > 70) & (df['trend_score'] < 0), 'trend_score'] -= 0.5
    
    # ============================================================
    # 维度2：动量得分 (-2 ~ +2)
    # ============================================================
    df['momentum_score'] = 0.0
    
    # RSI (50为分界线)
    df = rsi(df)
    df.loc[df['RSI_14'] > 50, 'momentum_score'] += 1
    df.loc[df['RSI_14'] < 50, 'momentum_score'] -= 1
    
    # MACD柱状线方向
    df = macd(df)
    df.loc[df['MACDh_12_26_9'] > 0, 'momentum_score'] += 0.5
    df.loc[df['MACDh_12_26_9'] < 0, 'momentum_score'] -= 0.5
    
    # STOCH (超买超卖)
    df = stoch(df)
    df.loc[df['STOCHk_14_3_1'] > 80, 'momentum_score'] -= 0.5  # 超买减分
    df.loc[df['STOCHk_14_3_1'] < 20, 'momentum_score'] += 0.5  # 超卖加分
    
    # ============================================================
    # 维度3：成交量得分 (-1.5 ~ +1.5)
    # ============================================================
    df['volume_score'] = 0.0
    
    # OBV方向 (相对于20日均线)
    df = obv(df)
    df.loc[df['OBV_Signal'] == 1, 'volume_score'] += 1
    df.loc[df['OBV_Signal'] == -1, 'volume_score'] -= 1
    
    # CMF资金流向
    df = cmf(df)
    df.loc[df['CMF_Signal'] == 1, 'volume_score'] += 0.5
    df.loc[df['CMF_Signal'] == -1, 'volume_score'] -= 0.5
    
    # ============================================================
    # 维度4：波动率得分 (-1 ~ +1)
    # ============================================================
    df['volatility_score'] = 0.0
    
    # 布林带位置
    df = bbands(df)
    df.loc[df['BB_Signal'] == 1, 'volatility_score'] += 0.5   # 下轨附近，超卖
    df.loc[df['BB_Signal'] == -1, 'volatility_score'] -= 0.5   # 上轨附近，超买
    
    # ATR相对位置 (高波动减分，低波动加分)
    df = atr(df)
    df.loc[df['Volatility_State'] == 'low', 'volatility_score'] += 0.5  # 低波动，趋势可能延续
    df.loc[df['Volatility_State'] == 'high', 'volatility_score'] -= 0.5  # 高波动，风险增加
    
    # ============================================================
    # 维度5：统计得分 (-1.5 ~ +1.5)
    # ============================================================
    df['stat_score'] = 0.0
    
    # ZSCORE (均值回归信号)
    df = zscore(df)
    df.loc[df['ZSCORE_Signal'] == -1, 'stat_score'] -= 1    # 价格过高，看跌
    df.loc[df['ZSCORE_Signal'] == 1, 'stat_score'] += 1   # 价格过低，看涨
    
    # SKEW偏斜度 (极端值预警)
    df = skew(df)
    df.loc[df['SKEW_Signal'] == 1, 'stat_score'] += 0.5   # 正偏，可能继续涨
    df.loc[df['SKEW_Signal'] == -1, 'stat_score'] -= 0.5  # 负偏，可能继续跌
    
    # KURTOSIS (高峰度预警)
    df = kurtosis(df)
    df.loc[df['KURT_Signal'] == 1, 'stat_score'] = df['stat_score'] * 0.8  # 降低权重，风险增加
    
    # ============================================================
    # 综合评分与信号生成
    # ============================================================
    # 总得分 = 趋势得分 + 动量得分 + 成交量得分 + 波动率得分 + 统计得分
    df['total_score'] = (
        df['trend_score'] + 
        df['momentum_score'] + 
        df['volume_score'] + 
        df['volatility_score'] + 
        df['stat_score']
    )
    
    # 标准化到 -3 ~ +3 范围
    df['total_score'] = df['total_score'].clip(-3, 3)
    
    # 综合信号
    df['final_signal'] = 0.0
    df.loc[df['total_score'] > 1.5, 'final_signal'] = 2    # 强烈看多
    df.loc[df['total_score'] > 0.5, 'final_signal'] = 1     # 温和看多
    df.loc[df['total_score'] < -1.5, 'final_signal'] = -2   # 强烈看空
    df.loc[df['total_score'] < -0.5, 'final_signal'] = -1   # 温和看空
    
    # 信号信心等级
    df['confidence'] = 'low'
    df.loc[df['total_score'].abs() > 0.5, 'confidence'] = 'medium'
    df.loc[df['total_score'].abs() > 1.5, 'confidence'] = 'high'
    
    return df

def strong_buy(df: pd.DataFrame) -> pd.DataFrame:

    df = composite_signal(df)

    # ===== 场景1：强多头信号过滤 =====
    strong_buy = df[
        (df['final_signal'] >= 1.5) &          # 综合信号强烈看多
        (df['trend_score'] > 1) &              # 趋势向上
        (df['momentum_score'] > 0.5) &         # 动量正向
        (df['volume_score'] > 0) &             # 资金流入
        (df['Volatility_State'] != 'high')     # 非高波动状态
    ]
    print(f"强多头信号数量: {len(strong_buy)}")

def oversold_opportunity(df: pd.DataFrame) -> pd.DataFrame:

    df = composite_signal(df)

    # ===== 场景2：超卖反弹机会 =====
    oversold_opportunity = df[
        (df['RSI_14'] < 30) &                  # RSI超卖
        (df['STOCHk_14_3_1'] < 20) &           # 随机指标超卖
        (df['ZSCORE_20'] < -1.5) &             # 价格低于均值
        (df['volume_score'] > 0) &             # 资金开始流入
        (df['final_signal'] > 0)               # 综合信号看多
    ]
    print(f"超卖反弹机会数量: {len(oversold_opportunity)}")

def trend_continuation(df: pd.DataFrame) -> pd.DataFrame:

    df = composite_signal(df)
    
    # ===== 场景3：趋势延续确认 =====
    trend_continuation = df[
        (df['trend_score'] > 1) &              # 趋势向上
        (df['momentum_score'] > 0.5) &         # 动量正向
        (df['volume_score'] > 0.5) &           # 资金持续流入
        (df['ADX_14'] > 25) &                  # 强趋势
        (df['CHOP_14'] < 38.2) &               # 趋势市
        (df['Volatility_State'] == 'low')      # 低波动，趋势稳定
    ]
    print(f"趋势延续确认数量: {len(trend_continuation)}")