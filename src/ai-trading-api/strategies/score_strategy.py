import pandas_ta as ta
import pandas as pd

from indicators.statistics_indicators import skew, kurtosis, zscore, std
from indicators.trend_indicators import adx, aroon, chop, psar, vortex
from indicators.volume_indicators import cmf, obv, mfi, ad, aobv
from indicators.volatility_indicators import atr, bbands, kc, donchian
from indicators.overlap_Indicators import ema, sma
from indicators.mtm_indicators import rsi, macd, stoch, mom, cci, willr

"""
五维度综合分析框架
维度	核心指标	            作用	              信号类型
趋势    PSAR,ADX,CHOP   判断方向、强度、市场状态	 趋势过滤器
动量    RSI,MACD,STOCH  衡量动能、超买超卖	        入场/出场信号
成交量  OBV,CMF         确认资金流向	           信号确认器
波动率  ATR,BBANDS      风险管理、止损设置	        仓位/止损管理器
统计    ZSCORE,SKEW     识别极端值、评估风险	    预警过滤器
"""

def calculate_trend_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算趋势得分（-3 ~ +3）
    得分 > 0 表示上升趋势，得分 < 0 表示下降趋势
    绝对值越大，趋势越强
    """
    
    # ============================================================
    # 基础趋势得分（-2 ~ +2）
    # ============================================================
    df['trend_score'] = 0.0
    
    # 1. PSAR方向（核心趋势判断）
    # 上升：价格在PSAR_Long_Stop之上；下降：价格在PSAR_Short之下
    df = psar(df)
    df.loc[df['PSAR_State'] == 1, 'trend_score'] += 1.0
    df.loc[df['PSAR_State'] == -1, 'trend_score'] -= 1.0
    
    # 2. 价格与均线位置
    # 使用EMA20和SMA50判断中期趋势
    df = ema(df)
    # df['trend_score'] += (df['EMA_Trend']).astype(float) * 0.5
    # df['trend_score'] -= (df['EMA_Trend']).astype(float) * 0.5
    df = sma(df)
    # df['trend_score'] += (df['close'] > df['SMA_20']).astype(float) * 0.3
    # df['trend_score'] -= (df['close'] < df['SMA_20']).astype(float) * 0.3
    
    # 3. 均线排列（多头排列 vs 空头排列）
    # EMA12 > EMA26 > SMA50 为多头排列
    df.loc[(df['EMA_12'] > df['EMA_26']) & (df['EMA_26'] > df['SMA_50']), 'trend_score'] += 0.5
    df.loc[(df['EMA_12'] < df['EMA_26']) & (df['EMA_26'] < df['SMA_50']), 'trend_score'] -= 0.5
    
    # ============================================================
    # 趋势强度加成（ADX）
    # ============================================================
    # ADX > 25 时，趋势得分权重加大
    df = adx(df)
    df.loc[(df['ADX_14'] > 25) & (df['trend_score'] > 0), 'trend_score'] += 0.5
    df.loc[(df['ADX_14'] > 25) & (df['trend_score'] < 0), 'trend_score'] -= 0.5
    
    # ADX > 50 时，趋势极强，额外加成
    df.loc[(df['ADX_14'] > 50) & (df['trend_score'] > 0), 'trend_score'] += 0.3
    df.loc[(df['ADX_14'] > 50) & (df['trend_score'] < 0), 'trend_score'] -= 0.3
    
    # ============================================================
    # 趋势方向确认（AROON）
    # ============================================================
    # AROON_UP > 70 确认上升，AROON_DOWN > 70 确认下降
    df = aroon(df)
    df.loc[(df['AROONU_14'] > 70) & (df['trend_score'] > 0), 'trend_score'] += 0.3
    df.loc[(df['AROOND_14'] > 70) & (df['trend_score'] < 0), 'trend_score'] -= 0.3
    
    # AROON交叉信号
    df.loc[(df['AROONU_14'] > df['AROOND_14']) & (df['trend_score'] > 0), 'trend_score'] += 0.2
    df.loc[(df['AROONU_14'] < df['AROOND_14']) & (df['trend_score'] < 0), 'trend_score'] -= 0.2
    
    # ============================================================
    # 趋势动量确认（VORTEX）
    # ============================================================
    # VTX_Pos > VTX_Neg 确认上升动量
    df = vortex(df)
    df.loc[df['VTXP_14'] > df['VTXM_14'], 'trend_score'] += 0.2
    df.loc[df['VTXP_14'] < df['VTXM_14'], 'trend_score'] -= 0.2
    
    # 漩涡强度 > 1.0 时额外加成
    df.loc[(df['VTXP_14'] > 1.0) & (df['VTXP_14'] > df['VTXM_14']), 'trend_score'] += 0.2
    df.loc[(df['VTXM_14'] > 1.0) & (df['VTXP_14'] < df['VTXM_14']), 'trend_score'] -= 0.2
    
    # ============================================================
    # 市场状态调整（CHOP）
    # ============================================================
    # 震荡市中，趋势得分权重减半
    df = chop(df)
    df.loc[df['CHOP_14'] > 61.8, 'trend_score'] = df['trend_score'] * 0.5
    
    # 趋势市中，趋势得分保持不变
    # CHOP < 38.2 时，趋势得分可以适当放大
    df.loc[df['CHOP_14'] < 38.2, 'trend_score'] = df['trend_score'] * 1.1
    
    # ============================================================
    # 截断到合理范围
    # ============================================================
    df['trend_score'] = df['trend_score'].clip(-3, 3)
    
    # ============================================================
    # 趋势得分等级
    # ============================================================
    df['trend_level'] = 'neutral'
    df.loc[df['trend_score'] > 1.5, 'trend_level'] = 'strong_bullish'   # 强多头
    df.loc[(df['trend_score'] > 0.5) & (df['trend_score'] <= 1.5), 'trend_level'] = 'bullish'  # 多头
    df.loc[(df['trend_score'] >= -0.5) & (df['trend_score'] <= 0.5), 'trend_level'] = 'neutral' # 中性
    df.loc[(df['trend_score'] < -0.5) & (df['trend_score'] >= -1.5), 'trend_level'] = 'bearish' # 空头
    df.loc[df['trend_score'] < -1.5, 'trend_level'] = 'strong_bearish'  # 强空头
    
    return df

def calculate_momentum_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算动量得分（-3 ~ +3）
    得分 > 0 表示正向动量，得分 < 0 表示负向动量
    绝对值越大，动量越强
    """
    
    # ============================================================
    # 基础动量得分（-2 ~ +2）
    # ============================================================
    df['momentum_score'] = 0.0
    
    # ----- 1. RSI（相对强弱指数）-----
    df = rsi(df)
    # RSI > 50 为正向动量，< 50 为负向动量
    df['momentum_score'] += ((df['RSI_14'] - 50) / 25).clip(-1, 1) * 0.8
    
    # RSI极端值加分（超买超卖的反向信号）
    # 超买（>70）可能预示动量衰竭，减分
    df.loc[df['RSI_14'] > 75, 'momentum_score'] -= 0.3
    # 超卖（<30）可能预示动量反转，加分
    df.loc[df['RSI_14'] < 25, 'momentum_score'] += 0.3
    
    # ----- 2. MACD（移动平均收敛发散）-----
    df = macd(df)
    # MACD柱状线方向（正为正向动量，负为负向动量）
    df.loc[df['MACDh_12_26_9'] > 0, 'momentum_score'] += 0.5
    df.loc[df['MACDh_12_26_9'] < 0, 'momentum_score'] -= 0.5
    
    # MACD柱状线加速（柱状线变化率）
    df['macd_hist_accel'] = df['MACDh_12_26_9'] - df['MACDh_12_26_9'].shift(1)
    df.loc[df['macd_hist_accel'] > 0, 'momentum_score'] += 0.2
    df.loc[df['macd_hist_accel'] < 0, 'momentum_score'] -= 0.2
    
    # MACD交叉状态
    # 金叉（快线上穿慢线）加分
    df.loc[
        (df['MACD_12_26_9'] > df['MACDs_12_26_9']) & 
        (df['MACD_12_26_9'].shift(1) <= df['MACDs_12_26_9'].shift(1)),
        'momentum_score'
    ] += 0.5
    
    # 死叉（快线下穿慢线）减分
    df.loc[
        (df['MACD_12_26_9'] < df['MACDs_12_26_9']) & 
        (df['MACD_12_26_9'].shift(1) >= df['MACDs_12_26_9'].shift(1)),
        'momentum_score'
    ] -= 0.5
    
    # ----- 3. STOCH（随机振荡器）-----
    df = stoch(df)
    # %K线位置（50为分界线）
    df.loc[df['STOCHk_14_3_1'] > 50, 'momentum_score'] += 0.3
    df.loc[df['STOCHk_14_3_1'] < 50, 'momentum_score'] -= 0.3
    
    # %K与%D交叉
    df.loc[
        (df['STOCHk_14_3_1'] > df['STOCHd_14_3_1']) & 
        (df['STOCHk_14_3_1'].shift(1) <= df['STOCHd_14_3_1'].shift(1)),
        'momentum_score'
    ] += 0.3
    
    df.loc[
        (df['STOCHk_14_3_1'] < df['STOCHd_14_3_1']) & 
        (df['STOCHk_14_3_1'].shift(1) >= df['STOCHd_14_3_1'].shift(1)),
        'momentum_score'
    ] -= 0.3
    
    # 超买超卖区域（反向信号）
    df.loc[(df['STOCHk_14_3_1'] > 80) & (df['momentum_score'] > 0), 'momentum_score'] -= 0.2
    df.loc[(df['STOCHk_14_3_1'] < 20) & (df['momentum_score'] < 0), 'momentum_score'] += 0.2
    
    # ----- 4. MOM（动量指标）-----
    df = mom(df)
    # MOM > 0 为正向动量
    df.loc[df['MOM_10'] > 0, 'momentum_score'] += 0.3
    df.loc[df['MOM_10'] < 0, 'momentum_score'] -= 0.3
    
    # MOM加速（MOM变化率）
    df['mom_accel'] = df['MOM_10'] - df['MOM_10'].shift(1)
    df.loc[df['mom_accel'] > 0, 'momentum_score'] += 0.2
    df.loc[df['mom_accel'] < 0, 'momentum_score'] -= 0.2
    
    # ----- 5. CCI（商品通道指数）-----
    df = cci(df)
    # CCI > 100 为强势，< -100 为弱势
    df.loc[df['CCI_14'] > 100, 'momentum_score'] += 0.2
    df.loc[df['CCI_14'] < -100, 'momentum_score'] -= 0.2
    
    # CCI从极端值回归（动量反转信号）
    df.loc[
        (df['CCI_14'] < 100) & 
        (df['CCI_14'].shift(1) > 100),
        'momentum_score'
    ] -= 0.3  # 从超买回归，动量减弱
    
    df.loc[
        (df['CCI_14'] > -100) & 
        (df['CCI_14'].shift(1) < -100),
        'momentum_score'
    ] += 0.3  # 从超卖回归，动量增强
    
    # ----- 6. 威廉姆斯 %R -----
    df = willr(df)
    # %R > -20 为超买，< -80 为超卖
    df.loc[df['WILLR_14'] > -20, 'momentum_score'] -= 0.2  # 超买，动量可能衰竭
    df.loc[df['WILLR_14'] < -80, 'momentum_score'] += 0.2  # 超卖，动量可能反转
    
    # ============================================================
    # 动量一致性检查（多个动量指标方向一致时加分）
    # ============================================================
    # 计算方向一致的数量
    momentum_directions = pd.DataFrame({
        'rsi': (df['RSI_14'] > 50).astype(int),
        'macd': (df['MACDh_12_26_9'] > 0).astype(int),
        'stoch': (df['STOCHk_14_3_1'] > 50).astype(int),
        'mom': (df['MOM_10'] > 0).astype(int),
        'cci': (df['CCI_14'] > 0).astype(int)
    })
    
    df['momentum_consensus'] = momentum_directions.sum(axis=1)
    
    # 如果多数指标方向一致，额外加减分
    df.loc[(df['momentum_consensus'] >= 4) & (df['momentum_score'] > 0), 'momentum_score'] += 0.3
    df.loc[(df['momentum_consensus'] >= 4) & (df['momentum_score'] < 0), 'momentum_score'] -= 0.3
    
    # ============================================================
    # 动量衰竭检测（背离信号）
    # ============================================================
    # 价格新高但RSI未新高（顶背离）→ 动量衰竭预警
    df['rsi_bearish_div'] = False
    df.loc[
        (df['close'] > df['close'].rolling(20).max().shift(1)) &
        (df['RSI_14'] < df['RSI_14'].rolling(20).max().shift(1)),
        'rsi_bearish_div'
    ] = True
    df.loc[df['rsi_bearish_div'], 'momentum_score'] -= 0.5
    
    # 价格新低但RSI未新低（底背离）→ 动量反转信号
    df['rsi_bullish_div'] = False
    df.loc[
        (df['close'] < df['close'].rolling(20).min().shift(1)) &
        (df['RSI_14'] > df['RSI_14'].rolling(20).min().shift(1)),
        'rsi_bullish_div'
    ] = True
    df.loc[df['rsi_bullish_div'], 'momentum_score'] += 0.5
    
    # ============================================================
    # 动量得分截断
    # ============================================================
    df['momentum_score'] = df['momentum_score'].clip(-3, 3)
    
    # ============================================================
    # 动量得分等级
    # ============================================================
    df['momentum_level'] = 'neutral'
    df.loc[df['momentum_score'] > 1.5, 'momentum_level'] = 'strong_positive'   # 强正向动量
    df.loc[(df['momentum_score'] > 0.5) & (df['momentum_score'] <= 1.5), 'momentum_level'] = 'positive'  # 正向动量
    df.loc[(df['momentum_score'] >= -0.5) & (df['momentum_score'] <= 0.5), 'momentum_level'] = 'neutral'  # 中性
    df.loc[(df['momentum_score'] < -0.5) & (df['momentum_score'] >= -1.5), 'momentum_level'] = 'negative'  # 负向动量
    df.loc[df['momentum_score'] < -1.5, 'momentum_level'] = 'strong_negative'  # 强负向动量
    
    return df

def calculate_volume_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算成交量得分（-2 ~ +2）
    得分 > 0 表示资金净流入，得分 < 0 表示资金净流出
    绝对值越大，资金流向越明确
    """
    
    # ============================================================
    # 基础成交量得分（-1.5 ~ +1.5）
    # ============================================================
    df['volume_score'] = 0.0
    
    # ----- 1. OBV（平衡成交量）-----
    df = obv(df)
    # OBV相对于20日均线的位置
    if 'OBV_MA20' not in df.columns:
        df['OBV_MA20'] = df['OBV'].rolling(20).mean()
    
    # OBV在均线之上：资金流入；之下：资金流出
    df.loc[df['OBV'] > df['OBV_MA20'], 'volume_score'] += 1.0
    df.loc[df['OBV'] < df['OBV_MA20'], 'volume_score'] -= 1.0
    
    # OBV偏离程度（距离均线的相对距离）
    df['obv_deviation'] = (df['OBV'] - df['OBV_MA20']) / df['OBV_MA20'].abs()
    df.loc[df['obv_deviation'] > 0.05, 'volume_score'] += 0.3   # 显著高于均线
    df.loc[df['obv_deviation'] < -0.05, 'volume_score'] -= 0.3  # 显著低于均线
    
    # OBV趋势方向（OBV本身在上升还是下降）
    df.loc[df['OBV'] > df['OBV'].shift(1), 'volume_score'] += 0.3
    df.loc[df['OBV'] < df['OBV'].shift(1), 'volume_score'] -= 0.3
    
    # ----- 2. CMF（查肯资金流）-----
    df = cmf(df)
    # CMF > 0 为资金净流入，< 0 为净流出
    df.loc[df['CMF_20'] > 0, 'volume_score'] += 0.5
    df.loc[df['CMF_20'] < 0, 'volume_score'] -= 0.5
    
    # CMF强度分级
    df.loc[df['CMF_20'] > 0.1, 'volume_score'] += 0.3   # 强流入
    df.loc[df['CMF_20'] < -0.1, 'volume_score'] -= 0.3  # 强流出
    df.loc[df['CMF_20'] > 0.2, 'volume_score'] += 0.2   # 极强流入
    df.loc[df['CMF_20'] < -0.2, 'volume_score'] -= 0.2  # 极强流出
    
    # CMF趋势方向
    df.loc[df['CMF_20'] > df['CMF_20'].shift(1), 'volume_score'] += 0.2
    df.loc[df['CMF_20'] < df['CMF_20'].shift(1), 'volume_score'] -= 0.2
    
    # ----- 3. MFI（资金流量指数）-----
    df = mfi(df)
    # MFI > 50 为资金流入，< 50 为资金流出
    df.loc[df['MFI_14'] > 50, 'volume_score'] += 0.3
    df.loc[df['MFI_14'] < 50, 'volume_score'] -= 0.3
    
    # MFI超买超卖（反向信号）
    df.loc[df['MFI_14'] > 80, 'volume_score'] -= 0.2   # 超买，资金可能流出
    df.loc[df['MFI_14'] < 20, 'volume_score'] += 0.2   # 超卖，资金可能流入
    
    # MFI与价格背离
    # 价格新高但MFI未新高 → 顶背离，资金流出预警
    df['mfi_bearish_div'] = False
    df.loc[
        (df['close'] > df['close'].rolling(20).max().shift(1)) &
        (df['MFI_14'] < df['MFI_14'].rolling(20).max().shift(1)),
        'mfi_bearish_div'
    ] = True
    df.loc[df['mfi_bearish_div'], 'volume_score'] -= 0.5
    
    # 价格新低但MFI未新低 → 底背离，资金流入信号
    df['mfi_bullish_div'] = False
    df.loc[
        (df['close'] < df['close'].rolling(20).min().shift(1)) &
        (df['MFI_14'] > df['MFI_14'].rolling(20).min().shift(1)),
        'mfi_bullish_div'
    ] = True
    df.loc[df['mfi_bullish_div'], 'volume_score'] += 0.5
    
    # ----- 4. AD（积聚/分配指数）-----
    df = ad(df)
    if 'AD' in df.columns:
        # AD相对于20日均线的位置
        if 'AD_MA20' not in df.columns:
            df['AD_MA20'] = df['AD'].rolling(20).mean()
        
        df.loc[df['AD'] > df['AD_MA20'], 'volume_score'] += 0.3
        df.loc[df['AD'] < df['AD_MA20'], 'volume_score'] -= 0.3
        
        # AD趋势方向
        df.loc[df['AD'] > df['AD'].shift(1), 'volume_score'] += 0.2
        df.loc[df['AD'] < df['AD'].shift(1), 'volume_score'] -= 0.2
    
    # ----- 5. AOBV（阿彻平衡成交量）-----
    df = aobv(df)
    if 'AOBV' in df.columns:
        if 'AOBV_MA20' not in df.columns:
            df['AOBV_MA20'] = df['AOBV'].rolling(20).mean()
        
        df.loc[df['AOBV'] > df['AOBV_MA20'], 'volume_score'] += 0.2
        df.loc[df['AOBV'] < df['AOBV_MA20'], 'volume_score'] -= 0.2
    
    # ============================================================
    # 量价配合分析（核心逻辑）
    # ============================================================
    # 价格上涨 + 成交量放大 = 健康上涨
    df['price_up'] = df['close'] > df['close'].shift(1)
    df['volume_up'] = df['volume'] > df['volume'].rolling(20).mean()
    
    # 量价齐升（强势信号）
    df.loc[df['price_up'] & df['volume_up'] & (df['volume_score'] > 0), 'volume_score'] += 0.3
    
    # 量价背离：价格上涨但成交量萎缩（弱势信号）
    df.loc[df['price_up'] & ~df['volume_up'] & (df['volume_score'] > 0), 'volume_score'] -= 0.3
    
    # 价格下跌 + 成交量放大 = 健康下跌
    df['price_down'] = df['close'] < df['close'].shift(1)
    df.loc[df['price_down'] & df['volume_up'] & (df['volume_score'] < 0), 'volume_score'] -= 0.3
    
    # 放量滞涨：价格不涨但成交量放大（可能出货）
    df['price_flat'] = (df['close'] - df['close'].shift(1)).abs() / df['close'].shift(1) < 0.01
    df.loc[df['price_flat'] & df['volume_up'] & (df['volume_score'] > 0), 'volume_score'] -= 0.2
    
    # ============================================================
    # 成交量一致性检查（多个成交量指标方向一致时加分）
    # ============================================================
    # 计算方向一致的数量
    volume_directions = pd.DataFrame({
        'obv': (df['OBV'] > df['OBV_MA20']).astype(int) if 'OBV_MA20' in df.columns else 0,
        'cmf': (df['CMF_20'] > 0).astype(int),
        'mfi': (df['MFI_14'] > 50).astype(int)
    })
    
    # 如果有AD列则加入
    if 'AD' in df.columns and 'AD_MA20' in df.columns:
        volume_directions['ad'] = (df['AD'] > df['AD_MA20']).astype(int)
    
    df['volume_consensus'] = volume_directions.sum(axis=1)
    
    # 如果多数指标方向一致，额外加减分
    df.loc[(df['volume_consensus'] >= 3) & (df['volume_score'] > 0), 'volume_score'] += 0.2
    df.loc[(df['volume_consensus'] >= 3) & (df['volume_score'] < 0), 'volume_score'] -= 0.2
    
    # ============================================================
    # 成交量得分截断
    # ============================================================
    df['volume_score'] = df['volume_score'].clip(-2, 2)
    
    # ============================================================
    # 成交量得分等级
    # ============================================================
    df['volume_level'] = 'neutral'
    df.loc[df['volume_score'] > 1.0, 'volume_level'] = 'strong_inflow'    # 强资金流入
    df.loc[(df['volume_score'] > 0.3) & (df['volume_score'] <= 1.0), 'volume_level'] = 'inflow'  # 资金流入
    df.loc[(df['volume_score'] >= -0.3) & (df['volume_score'] <= 0.3), 'volume_level'] = 'neutral'  # 中性
    df.loc[(df['volume_score'] < -0.3) & (df['volume_score'] >= -1.0), 'volume_level'] = 'outflow'  # 资金流出
    df.loc[df['volume_score'] < -1.0, 'volume_level'] = 'strong_outflow'  # 强资金流出
    
    return df

def calculate_volatility_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算波动率得分（-2 ~ +2）
    得分 > 0 表示波动率较低/稳定，适合持仓
    得分 < 0 表示波动率较高/风险增加，需谨慎
    绝对值越大，波动率特征越明显
    """
    
    # ============================================================
    # 基础波动率得分（-1.5 ~ +1.5）
    # ============================================================
    df['volatility_score'] = 0.0
    
    # ----- 1. ATR（平均真实波幅）-----
    df = atr(df)
    if 'ATR_MA100' not in df.columns:
        df['ATR_MA100'] = df['ATR_14'].rolling(100).mean()
    
    # ATR相对于历史均值的位置
    # 低波动：ATR < 0.5倍均值 → 加分（稳定）
    df.loc[df['ATR_14'] < df['ATR_MA100'] * 0.5, 'volatility_score'] += 1.0
    
    # 正常波动：ATR在0.5~1.5倍均值之间 → 中性
    df.loc[(df['ATR_14'] >= df['ATR_MA100'] * 0.5) & 
           (df['ATR_14'] <= df['ATR_MA100'] * 1.5), 'volatility_score'] += 0.0
    
    # 高波动：ATR > 1.5倍均值 → 减分（风险增加）
    df.loc[df['ATR_14'] > df['ATR_MA100'] * 1.5, 'volatility_score'] -= 0.8
    df.loc[df['ATR_14'] > df['ATR_MA100'] * 2.0, 'volatility_score'] -= 0.5  # 极高波动，额外减分
    
    # ATR方向变化（波动率加速/减速）
    df['atr_change'] = df['ATR_14'] - df['ATR_14'].shift(1)
    # 波动率上升 → 风险增加，减分
    df.loc[df['atr_change'] > 0, 'volatility_score'] -= 0.2
    # 波动率下降 → 风险降低，加分
    df.loc[df['atr_change'] < 0, 'volatility_score'] += 0.2
    
    # 波动率急剧变化（单日ATR变化超过20%）
    df['atr_spike'] = df['atr_change'].abs() / df['ATR_14'].shift(1) > 0.2
    df.loc[df['atr_spike'] & (df['atr_change'] > 0), 'volatility_score'] -= 0.3  # 波动率飙升
    df.loc[df['atr_spike'] & (df['atr_change'] < 0), 'volatility_score'] += 0.2  # 波动率骤降
    
    # ----- 2. 布林带（BBANDS）-----
    df = bbands(df)
    # 布林带宽度（波动率指标）
    if 'BB_Width' not in df.columns:
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
    if 'BB_Width_MA20' not in df.columns:
        df['BB_Width_MA20'] = df['BB_Width'].rolling(20).mean()
    
    # 布林带宽度相对位置
    # 带宽收缩（挤压）→ 变盘前兆，中性偏谨慎
    df['bb_squeeze'] = df['BB_Width'] < df['BB_Width_MA20'] * 0.7
    df.loc[df['bb_squeeze'], 'volatility_score'] -= 0.1  # 轻微减分，等待方向
    
    # 带宽扩张 → 波动率放大
    df.loc[df['BB_Width'] > df['BB_Width_MA20'] * 1.5, 'volatility_score'] -= 0.3
    
    # 价格在布林带中的位置（超买超卖）
    # 触及上轨 → 超买，可能回调
    df.loc[df['close'] > df['BB_Upper'], 'volatility_score'] -= 0.3
    # 触及下轨 → 超卖，可能反弹
    df.loc[df['close'] < df['BB_Lower'], 'volatility_score'] += 0.3
    
    # 价格与中轨的距离（偏离程度）
    df['bb_deviation'] = (df['close'] - df['BB_Middle']) / (df['BB_Upper'] - df['BB_Lower'])
    # 偏离过大 → 回归概率高
    df.loc[df['bb_deviation'] > 0.5, 'volatility_score'] -= 0.2
    df.loc[df['bb_deviation'] < -0.5, 'volatility_score'] += 0.2
    
    # ----- 3. 凯尔顿通道（KC）-----
    df = kc(df)
    if 'KC_Width' not in df.columns:
        df['KC_Width'] = (df['KC_Upper'] - df['KC_Lower']) / df['KC_Middle']
    
    # KC宽度（ATR-based波动率）
    df['kc_ma'] = df['KC_Width'].rolling(20).mean()
    df.loc[df['KC_Width'] > df['kc_ma'] * 1.5, 'volatility_score'] -= 0.3
    df.loc[df['KC_Width'] < df['kc_ma'] * 0.5, 'volatility_score'] += 0.3
    
    # 价格突破KC通道
    df.loc[df['close'] > df['KC_Upper'], 'volatility_score'] -= 0.2
    df.loc[df['close'] < df['KC_Lower'], 'volatility_score'] += 0.2
    
    # ----- 4. 唐奇安通道（DONCHIAN）-----
    df = donchian(df)
    if 'DC_Width' not in df.columns:
        df['DC_Width'] = (df['DC_Upper'] - df['DC_Lower']) / df['DC_Middle']
    
    # DC宽度（价格区间波动率）
    df['dc_ma'] = df['DC_Width'].rolling(20).mean()
    df.loc[df['DC_Width'] > df['dc_ma'] * 1.5, 'volatility_score'] -= 0.2
    df.loc[df['DC_Width'] < df['dc_ma'] * 0.5, 'volatility_score'] += 0.2
    
    # 价格突破DC通道（趋势信号，非波动率信号）
    # 突破本身意味着波动率放大，减分
    df.loc[(df['close'] > df['DC_Upper']) | (df['close'] < df['DC_Lower']), 'volatility_score'] -= 0.1
    
    # ============================================================
    # 波动率一致性检查
    # ============================================================
    # 多个波动率指标方向一致时，加减分
    vol_directions = pd.DataFrame({
        'atr_low': (df['ATR_14'] < df['ATR_MA100'] * 0.5).astype(int),
        'bb_narrow': (df['BB_Width'] < df['BB_Width_MA20'] * 0.7).astype(int),
        'kc_narrow': (df['KC_Width'] < df['kc_ma'] * 0.5).astype(int) if 'kc_ma' in df.columns else 0
    })
    
    df['vol_consensus'] = vol_directions.sum(axis=1)
    
    # 如果多数指标显示低波动，额外加分
    df.loc[df['vol_consensus'] >= 2, 'volatility_score'] += 0.3
    
    # ============================================================
    # 波动率得分截断
    # ============================================================
    df['volatility_score'] = df['volatility_score'].clip(-2, 2)
    
    # ============================================================
    # 波动率得分等级
    # ============================================================
    df['volatility_level'] = 'normal'
    df.loc[df['volatility_score'] > 1.0, 'volatility_level'] = 'very_stable'   # 极低波动，非常稳定
    df.loc[(df['volatility_score'] > 0.3) & (df['volatility_score'] <= 1.0), 'volatility_level'] = 'stable'  # 低波动
    df.loc[(df['volatility_score'] >= -0.3) & (df['volatility_score'] <= 0.3), 'volatility_level'] = 'normal'  # 正常波动
    df.loc[(df['volatility_score'] < -0.3) & (df['volatility_score'] >= -1.0), 'volatility_level'] = 'volatile'  # 高波动
    df.loc[df['volatility_score'] < -1.0, 'volatility_level'] = 'very_volatile'  # 极高波动
    
    # ============================================================
    # 波动率特殊状态标记
    # ============================================================
    # 布林带挤压（变盘前兆）
    df['bb_squeeze'] = df['BB_Width'] < df['BB_Width_MA20'] * 0.7
    
    # 波动率爆发（ATR突然放大）
    df['volatility_eruption'] = (
        (df['atr_change'] > df['atr_change'].rolling(10).std() * 2) &
        (df['ATR_14'] > df['ATR_MA100'] * 1.2)
    )
    
    # 波动率收缩（可能横盘）
    df['volatility_contraction'] = (
        (df['atr_change'] < 0) &
        (df['ATR_14'] < df['ATR_MA100'] * 0.8) &
        (df['bb_squeeze'])
    )
    
    return df

def calculate_stat_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算统计得分（-2 ~ +2）
    得分 > 0 表示价格处于相对低位或分布偏态有利，存在潜在机会
    得分 < 0 表示价格处于相对高位或分布偏态不利，存在潜在风险
    """
    
    # ============================================================
    # 基础统计得分（-1.5 ~ +1.5）
    # ============================================================
    df['stat_score'] = 0.0
    
    # ----- 1. ZSCORE（Z分数，最核心的统计工具）-----
    df = zscore(df)
    # ZSCORE > 2 表示价格极度偏高（均值回归向下压力大）
    df.loc[df['ZSCORE_20'] > 2.0, 'stat_score'] -= 1.0
    df.loc[df['ZSCORE_20'] > 3.0, 'stat_score'] -= 0.5  # 极端偏离，额外减分
    
    # ZSCORE < -2 表示价格极度偏低（均值回归向上动力强）
    df.loc[df['ZSCORE_20'] < -2.0, 'stat_score'] += 1.0
    df.loc[df['ZSCORE_20'] < -3.0, 'stat_score'] += 0.5  # 极端偏离，额外加分
    
    # ZSCORE在-0.5~0.5之间表示价格接近均值（中性）
    df.loc[(df['ZSCORE_20'] >= -0.5) & (df['ZSCORE_20'] <= 0.5), 'stat_score'] += 0.0
    
    # ZSCORE方向变化（回归/偏离）
    # 从极端值回归 → 加分（均值回归正在发生）
    df['zscore_reversion_buy'] = (df['ZSCORE_20'].shift(1) < -2) & (df['ZSCORE_20'] > -1.5)
    df['zscore_reversion_sell'] = (df['ZSCORE_20'].shift(1) > 2) & (df['ZSCORE_20'] < 1.5)
    df.loc[df['zscore_reversion_buy'], 'stat_score'] += 0.5
    df.loc[df['zscore_reversion_sell'], 'stat_score'] -= 0.5
    
    # 向极端值移动 → 趋势加强信号
    df['zscore_trend_buy'] = (df['ZSCORE_20'] < -1.5) & (df['ZSCORE_20'] < df['ZSCORE_20'].shift(1))
    df['zscore_trend_sell'] = (df['ZSCORE_20'] > 1.5) & (df['ZSCORE_20'] > df['ZSCORE_20'].shift(1))
    df.loc[df['zscore_trend_buy'], 'stat_score'] += 0.3
    df.loc[df['zscore_trend_sell'], 'stat_score'] -= 0.3
    
    # ----- 2. SKEW（偏斜度）-----
    df = skew(df)
    # 正偏（>0.5）：右侧尾巴长，可能有大的上涨，但也可能突然下跌
    df.loc[df['SKEW_50'] > 0.5, 'stat_score'] += 0.4
    df.loc[df['SKEW_50'] > 1.0, 'stat_score'] += 0.2  # 强正偏，额外加分
    
    # 负偏（<-0.5）：左侧尾巴长，可能有大的下跌，但也可能突然上涨
    df.loc[df['SKEW_50'] < -0.5, 'stat_score'] -= 0.4
    df.loc[df['SKEW_50'] < -1.0, 'stat_score'] -= 0.2  # 强负偏，额外减分
    
    # 偏斜度变化方向
    df['skew_direction'] = df['SKEW_50'] - df['SKEW_50'].shift(1)
    df.loc[(df['skew_direction'] > 0) & (df['SKEW_50'] < 0), 'stat_score'] += 0.2  # 负偏转正，机会增加
    df.loc[(df['skew_direction'] < 0) & (df['SKEW_50'] > 0), 'stat_score'] -= 0.2  # 正偏转负，风险增加
    
    # ----- 3. KURTOSIS（峰态度）-----
    df = kurtosis(df)
    # 高峰度（>2）：极端值出现概率高，风险较大
    df.loc[df['KURT_50'] > 2.0, 'stat_score'] -= 0.3
    df.loc[df['KURT_50'] > 4.0, 'stat_score'] -= 0.3  # 极高峰度，额外减分
    
    # 低峰度（<0）：分布平缓，极端值概率低，相对安全
    df.loc[df['KURT_50'] < 0, 'stat_score'] += 0.2
    
    # 峰度变化方向
    df.loc[(df['KURT_50'] > df['KURT_50'].shift(1)) & (df['KURT_50'] > 2), 'stat_score'] -= 0.2  # 峰度上升，风险增加
    df.loc[(df['KURT_50'] < df['KURT_50'].shift(1)) & (df['KURT_50'] < 2), 'stat_score'] += 0.2  # 峰度下降，风险降低
    
    # ----- 4. ENTROPY（混沌度/熵）-----
    # if 'ENTROPY' in df.columns:
    #     # 熵值高 → 市场随机性强，难以预测
    #     df['entropy_ma'] = df['ENTROPY'].rolling(20).mean()
    #     df.loc[df['ENTROPY'] > df['entropy_ma'] * 1.2, 'stat_score'] -= 0.2
    #     df.loc[df['ENTROPY'] < df['entropy_ma'] * 0.8, 'stat_score'] += 0.2
    
    # ----- 5. STDEV（标准差）-----
    df = std(df)
    # 标准差相对于历史位置（已在波动率中计算，这里作为补充）
    if 'STDEV_20' in df.columns and 'STDEV_MA100' in df.columns:
        # 标准差极低 → 价格压缩，可能变盘
        df.loc[df['STDEV_20'] < df['STDEV_MA100'] * 0.3, 'stat_score'] += 0.2
        # 标准差极高 → 风险增加
        df.loc[df['STDEV_20'] > df['STDEV_MA100'] * 2.0, 'stat_score'] -= 0.2
    
    # ============================================================
    # 统计一致性检查
    # ============================================================
    # 多个统计指标方向一致时，加减分
    stat_directions = pd.DataFrame({
        'zscore_low': (df['ZSCORE_20'] < -1.5).astype(int),
        'skew_pos': (df['SKEW_50'] > 0.5).astype(int),
        'kurt_low': (df['KURT_50'] < 0).astype(int)
    })
    
    df['stat_consensus'] = stat_directions.sum(axis=1)
    
    # 如果多数统计指标显示机会（ZSCORE低 + SKEW正 + KURT低）
    df.loc[(df['stat_consensus'] >= 2) & (df['stat_score'] > 0), 'stat_score'] += 0.2
    
    # 如果多数统计指标显示风险（ZSCORE高 + SKEW负 + KURT高）
    df.loc[(df['stat_consensus'] <= 0) & (df['stat_score'] < 0), 'stat_score'] -= 0.2
    
    # ============================================================
    # 特殊统计模式识别
    # ============================================================
    # 1. "均值回归黄金信号"：ZSCORE < -2 + SKEW > 0（价格低且偏向上涨）
    df['stat_golden_buy'] = (df['ZSCORE_20'] < -2) & (df['SKEW_50'] > 0.5)
    df.loc[df['stat_golden_buy'], 'stat_score'] += 0.5
    
    # 2. "极端风险信号"：ZSCORE > 2 + KURT > 3（价格高且极端值概率大）
    df['stat_extreme_risk'] = (df['ZSCORE_20'] > 2) & (df['KURT_50'] > 3)
    df.loc[df['stat_extreme_risk'], 'stat_score'] -= 0.5
    
    # 3. "底部确认信号"：ZSCORE < -2 + 波动率收缩（价格低且市场稳定）
    df['stat_bottom_confirm'] = (df['ZSCORE_20'] < -2) & (df['bb_squeeze'])
    df.loc[df['stat_bottom_confirm'], 'stat_score'] += 0.3
    
    # 4. "顶部预警信号"：ZSCORE > 2 + 波动率扩张（价格高且市场不稳定）
    df['stat_top_warning'] = (df['ZSCORE_20'] > 2) & (df['volatility_eruption'])
    df.loc[df['stat_top_warning'], 'stat_score'] -= 0.3
    
    # ============================================================
    # 统计得分截断
    # ============================================================
    df['stat_score'] = df['stat_score'].clip(-2, 2)
    
    # ============================================================
    # 统计得分等级
    # ============================================================
    df['stat_level'] = 'neutral'
    df.loc[df['stat_score'] > 1.0, 'stat_level'] = 'strong_opportunity'   # 强机会（价格低、分布有利）
    df.loc[(df['stat_score'] > 0.3) & (df['stat_score'] <= 1.0), 'stat_level'] = 'opportunity'  # 有机会
    df.loc[(df['stat_score'] >= -0.3) & (df['stat_score'] <= 0.3), 'stat_level'] = 'neutral'  # 中性
    df.loc[(df['stat_score'] < -0.3) & (df['stat_score'] >= -1.0), 'stat_level'] = 'risk'  # 有风险
    df.loc[df['stat_score'] < -1.0, 'stat_level'] = 'strong_risk'  # 强风险（价格高、分布不利）
    
    return df

def calculate_all_scores(df: pd.DataFrame) -> pd.DataFrame:
        
    """
    计算所有维度的得分（趋势、动量、成交量、波动率、统计）
    """
    
    # ============================================================
    # 1. 趋势得分
    # ============================================================
    df = calculate_trend_score(df)
    
    # ============================================================
    # 2. 动量得分
    # ============================================================
    df = calculate_momentum_score(df)
    
    # ============================================================
    # 3. 成交量得分
    # ============================================================
    df = calculate_volume_score(df)
    
    # ============================================================
    # 4. 波动率得分
    # ============================================================
    df = calculate_volatility_score(df)
    
    # ============================================================
    # 5. 统计得分
    # ============================================================
    df = calculate_stat_score(df)
    
    # ============================================================
    # 6. 综合得分
    # ============================================================
    df['total_score'] = (
        df['trend_score'] + 
        df['momentum_score'] + 
        df['volume_score'] + 
        df['volatility_score'] + 
        df['stat_score']
    )
    df['total_score'] = df['total_score'].clip(-3, 3)
    
    # ============================================================
    # 7. 综合信号
    # ============================================================
    df['final_signal'] = 0
    df.loc[df['total_score'] > 1.5, 'final_signal'] = 2
    df.loc[df['total_score'] > 0.5, 'final_signal'] = 1
    df.loc[df['total_score'] < -1.5, 'final_signal'] = -2
    df.loc[df['total_score'] < -0.5, 'final_signal'] = -1
    
    return df

def generate_bullish_entry_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    生成多头入场信号（多维度综合判断）
    返回包含入场信号等级和入场条件的DataFrame
    """
    # ============================================================
    # 确保所有得分已计算
    # ============================================================
    required_cols = ['trend_score', 'momentum_score', 'volume_score', 
                     'volatility_score', 'stat_score', 'total_score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"⚠️ 缺少列: {missing_cols}，请先运行 calculate_all_scores()")
        return df
    
    # ============================================================
    # 多头入场条件（金字塔结构）
    # ============================================================
    
    # ----- 条件1：趋势方向（必须满足）-----
    trend_bullish = (
        (df['trend_score'] > 0.3) &                         # 趋势得分为正
        (df['PSAR_State'] == 1) &                           # PSAR上升
        (df['close'] > df['EMA_12']) &                      # 价格在EMA12之上
        (df['close'] > df['SMA_20'])                        # 价格在SMA20之上
    )
    
    # ----- 条件2：动量确认（必须满足）-----
    momentum_bullish = (
        (df['momentum_score'] > 0.3) &                      # 动量得分为正
        (df['RSI_14'] > 50) &                               # RSI强势
        (df['MACDh_12_26_9'] > 0)                           # MACD柱状线为正
    )
    
    # ----- 条件3：成交量确认（建议满足）-----
    volume_bullish = (
        (df['volume_score'] > 0.3) &                        # 成交量得分为正
        (df['CMF_20'] > 0) &                                # 资金净流入
        (df['OBV'] > df['OBV_MA20'])                        # OBV在均线之上
    )
    
    # ----- 条件4：波动率环境（建议满足）-----
    volatility_bullish = (
        (df['volatility_score'] > -0.5) &                   # 非高波动状态
        (df['Volatility_State'] != 'high') &                # 非高波动
        (df['close'] < df['BB_Upper'])                      # 未严重超买
    )
    
    # ----- 条件5：统计支持（加分项）-----
    stat_bullish = (
        (df['stat_score'] > -0.3) |                         # 非强风险状态
        (df['stat_golden_buy'] == True)                     # 统计黄金买入信号
    )
    
    # ============================================================
    # 入场信号等级
    # ============================================================
    
    # 1. 强烈入场（所有核心条件都满足）
    df['entry_strong'] = (
        trend_bullish &
        momentum_bullish &
        volume_bullish &
        volatility_bullish &
        stat_bullish &
        (df['total_score'] > 1.0) &
        (df['ADX_14'] > 25)                                 # 强趋势确认
    )
    
    # 2. 中等入场（趋势+动量+成交量）
    df['entry_medium'] = (
        trend_bullish &
        momentum_bullish &
        volume_bullish &
        (df['total_score'] > 0.5)
    )
    
    # 3. 基础入场（趋势+动量）
    df['entry_basic'] = (
        trend_bullish &
        momentum_bullish &
        (df['total_score'] > 0.3)
    )
    
    # 4. 提前入场（统计机会+趋势启动）
    df['entry_early'] = (
        (df['stat_score'] > 0.5) &                          # 统计显示机会
        (df['trend_score'] > 0) &                           # 趋势刚转正
        (df['momentum_score'] > 0) &                        # 动量刚转正
        (df['ADX_14'] < 25) &                               # 趋势尚未形成（提前布局）
        (df['stat_golden_buy'] == True)                     # 统计黄金买入
    )
    
    # 5. 回调入场（趋势中回调买入）
    df['entry_pullback'] = (
        (df['trend_score'] > 0.5) &                         # 上升趋势
        (df['momentum_score'] < -0.3) &                     # 动量回调
        (df['close'] < df['SMA_20']) &                      # 价格在均线之下（回调）
        (df['close'] > df['SMA_50']) &                      # 但仍在长期均线之上
        (df['volume_score'] > 0) &                          # 资金仍在流入
        (df['RSI_14'] > 40)                                 # RSI未过度超卖
    )
    
    # 6. 突破入场（价格突破关键位）
    df['entry_breakout'] = (
        (df['close'] > df['DC_Upper']) &                    # 突破唐奇安上轨
        (df['volume'] > df['volume'].rolling(20).mean()) &  # 放量
        (df['ADX_14'] > 25) &                               # 趋势确认
        (df['momentum_score'] > 0.5) &                      # 动量强劲
        (df['CHOP_14'] < 38.2)                              # 趋势市
    )
    
    # ============================================================
    # 综合入场信号
    # ============================================================
    df['entry_signal'] = 0.0
    df['entry_level'] = 'none'
    
    # 最高优先级：强烈入场
    df.loc[df['entry_strong'], 'entry_signal'] = 3
    df.loc[df['entry_strong'], 'entry_level'] = 'strong'
    
    # 次高优先级：突破入场
    df.loc[df['entry_breakout'] & (df['entry_signal'] == 0), 'entry_signal'] = 2
    df.loc[df['entry_breakout'] & (df['entry_signal'] == 0), 'entry_level'] = 'breakout'
    
    # 中等优先级：中等入场
    df.loc[df['entry_medium'] & (df['entry_signal'] == 0), 'entry_signal'] = 2
    df.loc[df['entry_medium'] & (df['entry_signal'] == 0), 'entry_level'] = 'medium'
    
    # 回调入场
    df.loc[df['entry_pullback'] & (df['entry_signal'] == 0), 'entry_signal'] = 2
    df.loc[df['entry_pullback'] & (df['entry_signal'] == 0), 'entry_level'] = 'pullback'
    
    # 基础入场
    df.loc[df['entry_basic'] & (df['entry_signal'] == 0), 'entry_signal'] = 1
    df.loc[df['entry_basic'] & (df['entry_signal'] == 0), 'entry_level'] = 'basic'
    
    # 提前入场（最低优先级）
    df.loc[df['entry_early'] & (df['entry_signal'] == 0), 'entry_signal'] = 1
    df.loc[df['entry_early'] & (df['entry_signal'] == 0), 'entry_level'] = 'early'
    
    # ============================================================
    # 入场确认（额外过滤条件）
    # ============================================================
    # 排除震荡市中的假信号（CHOP过滤）
    df.loc[df['CHOP_14'] > 61.8, 'entry_signal'] = 0
    df.loc[df['CHOP_14'] > 61.8, 'entry_level'] = 'filtered_choppy'
    
    # 排除高波动环境（风险控制）
    df.loc[(df['Volatility_State'] == 'high') & (df['entry_signal'] > 0), 'entry_signal'] *= 0.5
    df.loc[(df['Volatility_State'] == 'high') & (df['entry_level'] != 'none'), 'entry_level'] += '_cautious'
    
    return df[['date', 'close', 'entry_signal', 'entry_level']]

def generate_bullish_take_profit_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    生成多头止盈信号（多维度综合判断）
    返回包含止盈信号等级和止盈策略的DataFrame
    """
    # ============================================================
    # 确保所有得分已计算
    # ============================================================
    required_cols = ['trend_score', 'momentum_score', 'volume_score', 
                     'volatility_score', 'stat_score', 'total_score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"⚠️ 缺少列: {missing_cols}，请先运行 calculate_all_scores()")
        return df
    
    # ============================================================
    # 止盈条件（金字塔结构，从轻微到紧急）
    # ============================================================
    
    # ----- 1. 趋势转弱止盈（早期预警）-----
    df['tp_trend_weakening'] = (
        (df['trend_score'] < 0.5) &                           # 趋势得分下降
        (df['trend_score'] < df['trend_score'].shift(1)) &    # 趋势正在减弱
        (df['ADX_14'] < df['ADX_14'].shift(1))               # ADX也在下降
    )
    
    # ----- 2. 动量衰竭止盈（中期信号）-----
    df['tp_momentum_fading'] = (
        (df['momentum_score'] < 0.3) |                        # 动量得分偏低
        ((df['momentum_score'] < df['momentum_score'].shift(1)) & 
         (df['momentum_score'] > 0)) |                        # 动量从高位回落
        (df['MACDh_12_26_9'] < df['MACDh_12_26_9'].shift(1)) # MACD柱状线缩短
    )
    
    # ----- 3. 资金流出止盈（重要信号）-----
    df['tp_volume_deterioration'] = (
        (df['volume_score'] < -0.3) |                         # 成交量得分转负
        (df['CMF_20'] < 0) |                                  # 资金净流出
        (df['OBV'] < df['OBV_MA20']) |                        # OBV跌破均线
        ((df['volume_score'] < df['volume_score'].shift(1)) & 
         (df['volume_score'] > 0))                            # 资金从流入转流出
    )
    
    # ----- 4. 波动率异常止盈（风险预警）-----
    df['tp_volatility_risk'] = (
        (df['volatility_score'] < -0.5) |                     # 波动率得分转负
        (df['Volatility_State'] == 'high') |                         # 高波动状态
        (df['volatility_eruption']) |                         # 波动率爆发
        (df['close'] > df['BB_Upper'])                        # 触及布林带上轨
    )
    
    # ----- 5. 统计异常止盈（极端信号）-----
    df['tp_stat_extreme'] = (
        (df['stat_score'] < -0.5) |                           # 统计得分转负
        (df['ZSCORE_20'] > 2.5) |                             # 价格极度偏高
        (df['stat_extreme_risk']) |                           # 统计极端风险
        (df['SKEW_50'] < -0.5)                                # 分布偏态不利
    )
    
    # ----- 6. PSAR反转（紧急信号）-----
    df['tp_psar_reversal'] = (
        (df['PSAR_Long_Stop'].notna()) & 
        (df['close'] < df['PSAR_Long_Stop']) &                     # 价格跌破PSAR
        (df['close'].shift(1) >= df['PSAR_Long_Stop'].shift(1))    # 刚刚跌破
    )
    
    # ----- 7. 关键支撑破位（紧急信号）-----
    df['tp_key_level_break'] = (
        (df['close'] < df['SMA_20']) &                        # 跌破20日均线
        (df['close'] < df['EMA_12']) &                        # 跌破12日均线
        (df['close'] < df['BB_Middle'])                       # 跌破布林中轨
    )
    
    # ----- 8. 顶背离（强烈信号）-----
    df['tp_divergence'] = (
        (df['rsi_bearish_div']) |                             # RSI顶背离
        (df['mfi_bearish_div'])                               # MFI顶背离
    )
    
    # ============================================================
    # 止盈信号等级
    # ============================================================
    
    # 计算触发的止盈条件数量
    tp_conditions = ['tp_trend_weakening', 'tp_momentum_fading', 'tp_volume_deterioration',
                     'tp_volatility_risk', 'tp_stat_extreme', 'tp_psar_reversal',
                     'tp_key_level_break', 'tp_divergence']
    
    df['tp_count'] = df[tp_conditions].sum(axis=1)
    
    # ----- 1. 强烈止盈（3个以上信号或紧急信号）-----
    df['tp_strong'] = (
        (df['tp_count'] >= 3) |
        df['tp_psar_reversal'] |
        (df['tp_divergence'] & (df['tp_count'] >= 2))
    )
    
    # ----- 2. 中等止盈（2个信号）-----
    df['tp_medium'] = (
        (df['tp_count'] == 2) &
        (~df['tp_strong'])
    )
    
    # ----- 3. 轻度止盈（1个信号）-----
    df['tp_light'] = (
        (df['tp_count'] == 1) &
        (~df['tp_strong']) &
        (~df['tp_medium'])
    )
    
    # ----- 4. 分批止盈信号（价格达到目标位）-----
    # 动态止盈位：3倍ATR 和 5倍ATR
    if 'ATR_14' in df.columns:
        # 假设入场价（用最近20日最低价近似）
        df['entry_price'] = df['low'].rolling(20).min()
        df['tp_target_1'] = df['entry_price'] + 3 * df['ATR_14']   # 第一目标
        df['tp_target_2'] = df['entry_price'] + 5 * df['ATR_14']   # 第二目标
        df['tp_target_3'] = df['entry_price'] + 7 * df['ATR_14']   # 第三目标
        
        df['tp_hit_target_1'] = df['close'] >= df['tp_target_1']
        df['tp_hit_target_2'] = df['close'] >= df['tp_target_2']
        df['tp_hit_target_3'] = df['close'] >= df['tp_target_3']
    
    # ----- 5. 移动止盈（追踪止盈）-----
    # 使用PSAR作为追踪止损
    df['tp_trailing'] = (
        (df['PSAR_Long_Stop'].notna()) & 
        (df['close'] - df['PSAR_Long_Stop'] < df['ATR_14'] * 0.5) &   # 价格距离PSAR不足0.5倍ATR
        (df['close'] > df['PSAR_Long_Stop'])                          # 但仍在PSAR之上
    )
    
    # ============================================================
    # 综合止盈信号
    # ============================================================
    df['tp_signal'] = 0
    df['tp_level'] = 'hold'
    
    # 最高优先级：强烈止盈
    df.loc[df['tp_strong'], 'tp_signal'] = 3
    df.loc[df['tp_strong'], 'tp_level'] = 'strong_sell'
    
    # 中等止盈
    df.loc[df['tp_medium'] & (df['tp_signal'] == 0), 'tp_signal'] = 2
    df.loc[df['tp_medium'] & (df['tp_signal'] == 0), 'tp_level'] = 'sell'
    
    # 轻度止盈
    df.loc[df['tp_light'] & (df['tp_signal'] == 0), 'tp_signal'] = 1
    df.loc[df['tp_light'] & (df['tp_signal'] == 0), 'tp_level'] = 'reduce'
    
    # 目标位止盈（独立于信号计数）
    if 'tp_hit_target_1' in df.columns:
        df.loc[df['tp_hit_target_1'] & (df['tp_signal'] == 0), 'tp_level'] = 'target_1'
        df.loc[df['tp_hit_target_2'] & (df['tp_signal'] <= 1), 'tp_level'] = 'target_2'
        df.loc[df['tp_hit_target_3'] & (df['tp_signal'] <= 2), 'tp_level'] = 'target_3'
    
    # 追踪止盈预警
    df.loc[df['tp_trailing'] & (df['tp_signal'] <= 1), 'tp_level'] = 'trailing_warning'
    
    # ============================================================
    # 综合得分判断（辅助）
    # ============================================================
    # 如果综合得分转负，立即止盈
    df.loc[(df['total_score'] < -0.5) & (df['tp_signal'] <= 1), 'tp_level'] = 'score_sell'
    
    return df[['date', 'close', 'tp_signal', 'tp_level']]