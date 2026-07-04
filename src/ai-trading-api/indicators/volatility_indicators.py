import pandas_ta as ta
from pandas import DataFrame


def atr(df_sorted: DataFrame):
    # ===== 1. ATR (平均真实波幅) =====
    atr = ta.atr(high=df_sorted['high'], low=df_sorted['low'], 
                            close=df_sorted['close'], length=14).rename('ATR_14')
    with_atr = df_sorted.join(atr)
    
    # ===== 1. ATR 信号 =====
    # ATR动态止损和止盈
    with_atr['ATR_Stop_Loss'] = with_atr['ATR_14'] * 2      # 2倍ATR止损
    with_atr['ATR_Take_Profit'] = with_atr['ATR_14'] * 4    # 4倍ATR止盈

    # 波动率状态判断
    with_atr['ATR_MA100'] = with_atr['ATR_14'].rolling(100).mean()
    with_atr['Volatility_State'] = 'normal'
    with_atr.loc[with_atr['ATR_14'] > with_atr['ATR_MA100'] * 1.5, 'Volatility_State'] = 'high'
    with_atr.loc[with_atr['ATR_14'] < with_atr['ATR_MA100'] * 0.5, 'Volatility_State'] = 'low'

    # ATR方向变化信号（波动率加速/减速）
    with_atr['ATR_Accel'] = with_atr['ATR_14'] - with_atr['ATR_14'].shift(1)
    with_atr['ATR_Accel_Signal'] = 0
    with_atr.loc[with_atr['ATR_Accel'] > with_atr['ATR_Accel'].rolling(5).mean(), 'ATR_Accel_Signal'] = 1   # 波动率上升
    with_atr.loc[with_atr['ATR_Accel'] < with_atr['ATR_Accel'].rolling(5).mean(), 'ATR_Accel_Signal'] = -1  # 波动率下降

    return with_atr
    
def bbands(df_sorted: DataFrame):
    # ===== 5. BBANDS (布林带) =====
    bbands = ta.bbands(close=df_sorted['close'], length=20, std=2)
    with_bbands = df_sorted.join(bbands)
    # 列名: BBU_20_2.0 (上轨), BBM_20_2.0 (中轨), BBL_20_2.0 (下轨), BBB_20_2.0 (带宽百分比)
    # 重命名为更简洁的名称
    with_bbands.rename(columns={
        'BBU_20_2.0_2.0': 'BB_Upper',
        'BBM_20_2.0_2.0': 'BB_Middle',
        'BBL_20_2.0_2.0': 'BB_Lower'
    }, inplace=True)

    # ===== 5. BBANDS 信号 =====
    # 布林带经典策略：触及上下轨
    with_bbands['BB_Signal'] = 0
    with_bbands.loc[with_bbands['close'] <= with_bbands['BB_Lower'], 'BB_Signal'] = 1    # 触及下轨，超卖，潜在买入
    with_bbands.loc[with_bbands['close'] >= with_bbands['BB_Upper'], 'BB_Signal'] = -1   # 触及上轨，超买，潜在卖出

    # 布林带宽度（波动率指标）
    with_bbands['BB_Width'] = (with_bbands['BB_Upper'] - with_bbands['BB_Lower']) / with_bbands['BB_Middle']
    # 带宽收缩预示变盘（带宽低于过去20日均值*0.8）
    with_bbands['BB_Width_MA'] = with_bbands['BB_Width'].rolling(20).mean()
    with_bbands['BB_Squeeze'] = with_bbands['BB_Width'] < (with_bbands['BB_Width_MA'] * 0.8)
    # 布林带扩张（趋势加速）
    with_bbands['BB_Expansion'] = with_bbands['BB_Width'] > (with_bbands['BB_Width_MA'] * 1.2)

    # 中轨方向
    with_bbands['BB_Middle_Direction'] = 0
    with_bbands.loc[with_bbands['BB_Middle'] > with_bbands['BB_Middle'].shift(1), 'BB_Middle_Direction'] = 1
    with_bbands.loc[with_bbands['BB_Middle'] < with_bbands['BB_Middle'].shift(1), 'BB_Middle_Direction'] = -1

    return with_bbands

def kc(df_sorted: DataFrame):
    # ===== 3. KC (凯尔顿通道) =====
    kc = ta.kc(high=df_sorted['high'], low=df_sorted['low'], close=df_sorted['close'], length=20, scalar=2)
    with_kc = df_sorted.join(kc)
    
    with_kc.rename(columns={
        'KCUe_20_2': 'KC_Upper',
        'KCBe_20_2': 'KC_Middle',
        'KCLe_20_2': 'KC_Lower'
    }, inplace=True)

    # ===== 3. KC 信号 =====
    # 凯尔顿通道突破
    with_kc['KC_Breakout'] = 0
    with_kc.loc[with_kc['close'] > with_kc['KC_Upper'], 'KC_Breakout'] = 1      # 突破上轨，强势
    with_kc.loc[with_kc['close'] < with_kc['KC_Lower'], 'KC_Breakout'] = -1     # 跌破下轨，弱势

    # KC宽度（波动率）
    with_kc['KC_Width'] = (with_kc['KC_Upper'] - with_kc['KC_Lower']) / with_kc['KC_Middle']

    # KC方向
    with_kc['KC_Direction'] = 0
    with_kc.loc[with_kc['KC_Middle'] > with_kc['KC_Middle'].shift(1), 'KC_Direction'] = 1
    with_kc.loc[with_kc['KC_Middle'] < with_kc['KC_Middle'].shift(1), 'KC_Direction'] = -1

    return with_kc

def donchian(df_sorted: DataFrame):
    # ===== 4. DONCHIAN (唐奇安通道) =====
    donchian = ta.donchian(high=df_sorted['high'], low=df_sorted['low'], length=20)
    with_donchian = df_sorted.join(donchian)
    
    with_donchian.rename(columns={
        'DCU_20_20': 'DC_Upper',
        'DCM_20_20': 'DC_Middle',
        'DCL_20_20': 'DC_Lower'
    }, inplace=True)

    # ===== 4. DONCHIAN 信号 =====
    # 唐奇安通道突破（海龟交易法核心）
    with_donchian['DC_Breakout'] = 0
    with_donchian.loc[with_donchian['close'] > with_donchian['DC_Upper'], 'DC_Breakout'] = 1      # 创20日新高，买入信号
    with_donchian.loc[with_donchian['close'] < with_donchian['DC_Lower'], 'DC_Breakout'] = -1     # 创20日新低，卖出信号

    # 通道宽度
    with_donchian['DC_Width'] = (with_donchian['DC_Upper'] - with_donchian['DC_Lower']) / with_donchian['DC_Middle']

    # 通道方向
    with_donchian['DC_Direction'] = 0
    with_donchian.loc[with_donchian['DC_Middle'] > with_donchian['DC_Middle'].shift(1), 'DC_Direction'] = 1
    with_donchian.loc[with_donchian['DC_Middle'] < with_donchian['DC_Middle'].shift(1), 'DC_Direction'] = -1

    return with_donchian