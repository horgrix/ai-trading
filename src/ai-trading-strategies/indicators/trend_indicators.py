import pandas as pd
import pandas_ta as ta
from pandas import DataFrame

def psar(df: DataFrame):
    """
    PSAR (抛物线停损反转指标)

    作用：确定趋势方向与动态止损位。指标会在价格图表上以一系列小点的形式呈现，价格在小点之上为上升趋势，之下为下降趋势。

    核心用法：最经典的用法是当价格从下方穿越 PSAR 点时，作为趋势反转和出场（止损或止盈）的信号。它提供的止损位会随着趋势发展而动态上移/下移。

    PSARl_0.02_0.2	PSAR Long	                多头（做多）停损点。在上升趋势中，该值位于价格下方并随趋势动态上移，作为多单的动态止损参考。
    PSARs_0.02_0.2	PSAR Short	                空头（做空）停损点。在下跌趋势中，该值位于价格上方并随趋势动态下移，作为空单的动态止损参考。
    PSARaf_0.02_0.2	PSAR Acceleration Factor	当前使用的加速因子。记录了每个时刻实际应用的加速因子值（在 0.02 到 0.2 之间动态变化）。
    PSARr_0.02_0.2	PSAR Reversal	            反转信号标记。通常用 1（或类似值）表示趋势在此处发生了反转，是识别趋势改变的参考辅助列。

    做多时：关注 PSARl 列。只要价格在它上方，就继续持有多单；一旦价格跌破它，可能就是趋势反转或止盈止损的时机。

    做空时：关注 PSARs 列。只要价格在它下方，就继续持有空单。

    调试与理解：PSARaf 和 PSARr 列主要用于调试或深入理解指标的计算过程，在常规交易信号生成中，直接使用前两列即可。

    参数调整：参数 0.02/0.2 是经典默认值。若想信号更灵敏（更早出场），可以调大起始值，比如 af=0.03；若想信号更迟钝（持仓更久），可以调小起始值，比如 af=0.015。

    这正是PSAR指标的正常工作方式：

    PSAR_Long_Stop（多单止损）：只在上升趋势中有值，表示多单的止损参考位。

    PSAR_Short_Stop（空单止损）：只在下跌趋势中有值，表示空单的止损参考位。

    当价格处于下跌趋势时，PSAR的"小点"会出现在价格上方（即 PSAR_Short_Stop），而 PSAR_Long_Stop 自然就为 NaN。这不是错误，而是指标设计如此。

    📈 完整的趋势判断矩阵
    场景	                PSAR_Long_Stop	PSAR_Short_Stop	趋势判断
    close > PSAR_Long_Stop	有值（在价格下方）	NaN	上升趋势，持有多单
    close < PSAR_Short_Stop	NaN	有值（在价格上方）	下跌趋势，持有空单
    刚反转，两者都有值	    有值	有值	趋势转换期，观望
    """
    psar_df = ta.psar(high=df['high'], low=df['low'], close=df['close'], af=0.02, max_af=0.2, append=True)
    df_with_psar = df.join(psar_df[['PSARl_0.02_0.2', 'PSARs_0.02_0.2']]).rename(columns={
        'PSARl_0.02_0.2': 'PSAR_Long_Stop',
        'PSARs_0.02_0.2': 'PSAR_Short_Stop'
    })

    # PSAR 趋势状态
    df_with_psar['PSAR_State'] = 0
    df_with_psar.loc[df_with_psar['close'] > df_with_psar['PSAR_Long_Stop'], 'PSAR_State'] = 1   # 上升趋势
    df_with_psar.loc[df_with_psar['close'] < df_with_psar['PSAR_Short_Stop'], 'PSAR_State'] = -1 # 下降趋势


    """根据PSAR生成交易信号"""
    df_with_psar['PSAR_Signal'] = 0
    # 买入信号：价格上穿PSAR_Long_Stop（由空转多）
    buy_condition = (
        (df_with_psar['PSAR_Long_Stop'].notna()) & 
        (df_with_psar['close'] > df_with_psar['PSAR_Long_Stop']) &
        (df_with_psar['close'].shift(1) <= df_with_psar['PSAR_Long_Stop'].shift(1))
    )
    
    # 卖出信号：价格下穿PSAR_Short_Stop（由多转空）
    sell_condition = (
        (df_with_psar['PSAR_Short_Stop'].notna()) & 
        (df_with_psar['close'] < df_with_psar['PSAR_Short_Stop']) &
        (df_with_psar['close'].shift(1) >= df_with_psar['PSAR_Short_Stop'].shift(1))
    )
    
    df_with_psar.loc[buy_condition, 'PSAR_Signal'] = 1
    df_with_psar.loc[sell_condition, 'PSAR_Signal'] = -1

    return df_with_psar

def aroon(df: DataFrame):
    """
    作用：判断新趋势是否萌芽。它通过计算自近期最高价和最低价以来的时间周期数，来衡量当前趋势的“新旧”程度。

    核心用法：AROON_UP（上阿龙）接近 100 表明上升趋势强劲；AROON_DOWN（下阿龙）接近 100 表明下跌趋势强劲。当上阿龙上穿下阿龙时，通常是新上升趋势开始的信号。

    上阿龙 > 70 表示上升趋势强劲，> 50 表示上升趋势尚在

    下阿龙 > 70 表示下跌趋势强劲

    阿龙振荡器（AROONOSC）> 0 为上升趋势，< 0 为下跌趋势
    """
    # 基础用法：默认周期14
    aroon_df = ta.aroon(high=df['high'], low=df['low'], length=14)

    # 合并结果（列名：AROOND_14, AROONU_14, AROONOSC_14）
    df_with_aroon = df.join(aroon_df)

    # ===== 3. AROON 信号 =====
    # AROON 交叉信号（上阿龙穿下阿龙）
    df_with_aroon['AROON_Cross'] = 0
    df_with_aroon.loc[(df_with_aroon['AROONU_14'] > df_with_aroon['AROOND_14']) & 
                (df_with_aroon['AROONU_14'].shift(1) <= df_with_aroon['AROOND_14'].shift(1)), 'AROON_Cross'] = 1
    df_with_aroon.loc[(df_with_aroon['AROONU_14'] < df_with_aroon['AROOND_14']) & 
                (df_with_aroon['AROONU_14'].shift(1) >= df_with_aroon['AROOND_14'].shift(1)), 'AROON_Cross'] = -1

    # AROON 强度等级
    df_with_aroon['AROON_Strength'] = 'neutral'
    df_with_aroon.loc[(df_with_aroon['AROONU_14'] > 70) & (df_with_aroon['AROONU_14'] > df_with_aroon['AROOND_14']), 'AROON_Strength'] = 'strong_up'
    df_with_aroon.loc[(df_with_aroon['AROOND_14'] > 70) & (df_with_aroon['AROONU_14'] < df_with_aroon['AROOND_14']), 'AROON_Strength'] = 'strong_down'

    return df_with_aroon

def vortex(df: DataFrame):
    """
    作用：识别趋势的启动与反转。它通过衡量价格在正向和负向的移动轨迹，来判断趋势的强度和方向。

    核心用法：VTXP_14（正漩涡）和 VTXM_14（负漩涡）两条线。当 VTXP_14 上穿 VTXM_14 时视为买入信号，下穿时视为卖出信号，常用于捕捉趋势的早期变化。

    VTXP_14 是正漩涡（买盘力量），VTXM_14 是负漩涡（卖盘力量），两者交叉是核心信号
    """
    # 基础用法：默认周期14
    vortex_df = ta.vortex(high=df['high'], low=df['low'], close=df['close'], length=14)

    df_with_vortex = df.join(vortex_df)
    # 列名：VTXP_14 (正漩涡), VTXM_14 (负漩涡)

    # ===== 4. VORTEX 信号 =====
    # 生成交易信号：正漩涡上穿负漩涡时买入
    df_with_vortex['VORTEX_Signal'] = 0
    df_with_vortex.loc[(df_with_vortex['VTXP_14'] > df_with_vortex['VTXM_14']) & 
        (df_with_vortex['VTXP_14'].shift(1) <= df_with_vortex['VTXM_14'].shift(1)), 'VORTEX_Signal'] = 1
    df_with_vortex.loc[(df_with_vortex['VTXP_14'] < df_with_vortex['VTXM_14']) & 
        (df_with_vortex['VTXP_14'].shift(1) >= df_with_vortex['VTXM_14'].shift(1)), 'VORTEX_Signal'] = -1

    return df_with_vortex

def chop(df: DataFrame):
    """
    作用：判断市场处于趋势市还是震荡市。它是评估市场状态的绝佳过滤器。

    核心用法：数值在 61.8 以上表示市场震荡，趋势策略容易失效；数值在 38.2 以下表示市场趋势明显，适合趋势跟踪策略。它不产生直接买卖信号，而是告诉你“现在该不该用趋势策略”。
    
    📈 CHOP解读：

    > 61.8：震荡/盘整，趋势策略失效概率高

    38.2 - 61.8：过渡区间，市场方向不明

    < 38.2：强趋势市，趋势策略胜率高
    """

    # 基础用法：默认周期14
    chop_df = ta.chop(high=df['high'], low=df['low'], close=df['close'], length=14).rename('CHOP_14')

    df_with_chop = df.join(chop_df)
    # 列名：CHOP_14

    # ===== 5. CHOP 信号 =====
    # CHOP 市场状态
    df_with_chop['Market_State'] = 'neutral'
    df_with_chop.loc[df_with_chop['CHOP_14'] > 61.8, 'Market_State'] = 'choppy'    # 震荡市
    df_with_chop.loc[df_with_chop['CHOP_14'] < 38.2, 'Market_State'] = 'trending'  # 趋势市

    # CHOP 方向变化
    df_with_chop['CHOP_Direction'] = 0
    df_with_chop.loc[df_with_chop['CHOP_14'] > df_with_chop['CHOP_14'].shift(1), 'CHOP_Direction'] = 1   # 震荡加剧
    df_with_chop.loc[df_with_chop['CHOP_14'] < df_with_chop['CHOP_14'].shift(1), 'CHOP_Direction'] = -1  # 趋势加强

    return df_with_chop

def adx(df: DataFrame):
    """
    作用：衡量趋势强度，而非趋势方向。数值越高（通常 >25）代表趋势越强，适合顺势策略；数值越低（<20）代表市场处于盘整，适合高抛低吸策略。

    核心用法：常与 DMP (+DI) 和 DMN (-DI) 配合。当 +DI 上穿 -DI 且 ADX 在 25 以上时，是较强的买入信号。
    """
    adx = ta.adx(high=df['high'], low=df['low'], close=df['close'], length=14, append=True)
    with_adx = df.join(adx)

    # ===== 1. ADX 信号 =====
    # ADX 趋势强度 + 方向
    with_adx['ADX_Signal'] = 0
    with_adx.loc[(with_adx['ADX_14'] > 25) & (with_adx['DMP_14'] > with_adx['DMN_14']), 'ADX_Signal'] = 1   # 强上升趋势
    with_adx.loc[(with_adx['ADX_14'] > 25) & (with_adx['DMP_14'] < with_adx['DMN_14']), 'ADX_Signal'] = -1  # 强下降趋势

    # ADX 趋势强度等级
    with_adx['ADX_Strength'] = 'weak'
    with_adx.loc[with_adx['ADX_14'] > 25, 'ADX_Strength'] = 'strong'
    with_adx.loc[with_adx['ADX_14'] > 50, 'ADX_Strength'] = 'very_strong'

    # ADX 方向变化
    with_adx['ADX_Direction'] = 0
    with_adx.loc[with_adx['ADX_14'] > with_adx['ADX_14'].shift(1), 'ADX_Direction'] = 1   # 趋势增强
    with_adx.loc[with_adx['ADX_14'] < with_adx['ADX_14'].shift(1), 'ADX_Direction'] = -1  # 趋势减弱

    # +DI 和 -DI 交叉信号
    with_adx['DI_Cross'] = 0
    with_adx.loc[(with_adx['DMP_14'] > with_adx['DMN_14']) & 
                (with_adx['DMP_14'].shift(1) <= with_adx['DMN_14'].shift(1)), 'DI_Cross'] = 1   # +DI上穿-DI，买入
    with_adx.loc[(with_adx['DMP_14'] < with_adx['DMN_14']) & 
                (with_adx['DMP_14'].shift(1) >= with_adx['DMN_14'].shift(1)), 'DI_Cross'] = -1  # -DI上穿+DI，卖出

    return with_adx