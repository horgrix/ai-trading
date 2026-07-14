import pandas as pd
import pandas_ta as ta
import vectorbt as vbt

from typing import Callable

from strategies.MTMStrategy import RSIDivergenceStrategy, RSIOverboughtOversoldStrategy, MACDCrossStrategy, AOCrossStrategy, MOMDivergenceStrategy
from strategies.TrendStrategy import DualMovingAverageCrossStrategy, PsarCrossStrategy, ADXDmpDmnCrossStrategy
from strategies.VolatilityStrategy import DonchianBreakThroughStrategy, BBandsVolatilityExpandSqueezeStrategy
from strategies.VolumeStrategy import OBVDivergenceStrategy, CMFStrategy


FAST_PERIODS = [5, 10, 20, 30]
PERIODS = [5, 10, 20, 30, 60, 120, 250]

INIT_CASH: int=100000
FEES: float=0.001
FREQ: str='D'

def create_holding_strategy(df: pd.DataFrame, ) -> dict[str, vbt.Portfolio]:
    strategies = {}
    portfolio: vbt.Portfolio  = vbt.Portfolio.from_holding(df['close'], init_cash=INIT_CASH, fees=FEES, freq=FREQ)
    strategies['Holding'] = portfolio
    return strategies

def create_rsi_overboughtoversold_strategy(df: pd.DataFrame, periods: list = PERIODS, oversold: int=25, overbought:int=75) -> dict[str, vbt.Portfolio]:
    strategies = {}
    for period in periods:
        strategy = RSIOverboughtOversoldStrategy(period=period, oversold=oversold, overbought=overbought)
        entries, exits, _ = strategy.generate_signals(df=df)
        portfolio: vbt.Portfolio  = vbt.Portfolio.from_signals(df['close'], entries=entries, exits=exits, init_cash=INIT_CASH, fees=FEES, freq=FREQ)
        strategies[strategy.get_name()] = portfolio
    return strategies
    
def create_rsi_divergence_strategy(df: pd.DataFrame, periods: list = PERIODS) -> dict[str, vbt.Portfolio]:
    strategies = {}
    for period in periods:
        strategy = RSIDivergenceStrategy(period=period)
        entries, exits, _  = strategy.generate_signals(df=df)
        portfolio: vbt.Portfolio  = vbt.Portfolio.from_signals(df['close'], entries=entries, exits=exits, init_cash=INIT_CASH, fees=FEES, freq=FREQ)
        strategies[strategy.get_name()] = portfolio
    return strategies

def create_macd_cross_strategy(df: pd.DataFrame, fast_periods: list=[10, 12], slow_periods: list=[20, 26], signals: list=[7, 9]) -> dict[str, vbt.Portfolio]:
    strategies = {}
    for fast in fast_periods:
        for slow in slow_periods:
            if fast >= slow:
                continue
            for signal in signals:
                strategy = MACDCrossStrategy(fast=fast, slow=slow, signal=signal)
                entries, exits, _ = strategy.generate_signals(df=df)
                portfolio: vbt.Portfolio  = vbt.Portfolio.from_signals(df['close'], entries=entries, exits=exits, init_cash=INIT_CASH, fees=FEES, freq=FREQ)
                strategies[strategy.get_name()] = portfolio
    return strategies

def create_ao_cross_strategy(df: pd.DataFrame, fast_periods: list=[5], slow_periods: list=[13, 21, 34]) -> dict[str, vbt.Portfolio]:
    strategies = {}
    for fast in fast_periods:
        for slow in slow_periods:
            if fast >= slow:
                continue
            strategy = AOCrossStrategy(fast=fast, slow=slow)
            entries, exits, _ = strategy.generate_signals(df=df)
            portfolio: vbt.Portfolio  = vbt.Portfolio.from_signals(df['close'], entries=entries, exits=exits, init_cash=INIT_CASH, fees=FEES, freq=FREQ)
            strategies[strategy.get_name()] = portfolio
    return strategies

def create_mom_divergence_strategy(df: pd.DataFrame, periods: list=[5, 10, 20], windows: list=[20, 30, 60, 120]) -> dict[str, vbt.Portfolio]:
    strategies = {}
    for period in periods:
        for window in windows:
            if period >= window:
                continue
            strategy = MOMDivergenceStrategy(period=period, windows=window)
            entries, exits, _ = strategy.generate_signals(df=df)
            portfolio: vbt.Portfolio  = vbt.Portfolio.from_signals(df['close'], entries=entries, exits=exits, init_cash=INIT_CASH, fees=FEES, freq=FREQ)
            strategies[strategy.get_name()] = portfolio
    return strategies

def create_dualmovingaverage_cross_strategy(df: pd.DataFrame, func: Callable = ta.sma,  fast_periods: list = FAST_PERIODS, slow_periods: list = PERIODS) -> dict[str, vbt.Portfolio]:
    strategies = {}
    for fast in fast_periods:
        for slow in slow_periods:
            if slow < fast:
                continue
            strategy = DualMovingAverageCrossStrategy(func=func, fast=fast, slow=slow)
            entries, exits, _ = strategy.generate_signals(df=df)
            portfolio: vbt.Portfolio  = vbt.Portfolio.from_signals(df['close'], entries=entries, exits=exits, init_cash=INIT_CASH, fees=FEES, freq=FREQ)
            strategies[f'{func.__name__}({fast},{slow})'] = portfolio
    return strategies

def create_psar_cross_strategy(df: pd.DataFrame, afs: list = [0.02], max_afs: list = [0.2]) -> dict[str, vbt.Portfolio]:
    strategies = {}
    for af in afs:
        for max_af in max_afs:
            strategy = PsarCrossStrategy(af=af, max_af=max_af)
            entries, exits, _ = strategy.generate_signals(df=df)
            portfolio: vbt.Portfolio  = vbt.Portfolio.from_signals(df['close'], entries=entries, exits=exits, init_cash=INIT_CASH, fees=FEES, freq=FREQ)
            strategies[f'PSAR({af},{max_af})'] = portfolio
    return strategies

def create_adx_dmpdmn_cross_strategy(df: pd.DataFrame, periods: list = FAST_PERIODS) -> dict[str, vbt.Portfolio]:
    strategies = {}
    for period in periods:
        strategy = ADXDmpDmnCrossStrategy(period=period)
        entries, exits, _ = strategy.generate_signals(df=df)
        portfolio: vbt.Portfolio  = vbt.Portfolio.from_signals(df['close'], entries=entries, exits=exits, init_cash=INIT_CASH, fees=FEES, freq=FREQ)
        strategies[f'ADX_CROSS({period})'] = portfolio
    return strategies

def create_donchian_breakthrough_strategy(df: pd.DataFrame, upper_periods: list = FAST_PERIODS, lower_periods: list = PERIODS) -> dict[str, vbt.Portfolio]:
    strategies = {}
    for upper_period in upper_periods:
        for lower_period in lower_periods:
            strategy = DonchianBreakThroughStrategy(upper_period=upper_period, lower_period=lower_period)
            entries, exits, _ = strategy.generate_signals(df=df)
            portfolio: vbt.Portfolio  = vbt.Portfolio.from_signals(df['close'], entries=entries, exits=exits, init_cash=INIT_CASH, fees=FEES, freq=FREQ)
            strategies[f'DONCHIAN({upper_period},{lower_period})'] = portfolio
    return strategies

def create_bbands_volatilityexpandsqueeze_strategy(df: pd.DataFrame, periods: list = FAST_PERIODS, stds: list=[2]) -> dict[str, vbt.Portfolio]:
    strategies = {}
    for period in periods:
        for std in stds:
            strategy = BBandsVolatilityExpandSqueezeStrategy(period=period, std=std)
            entries, exits, _ = strategy.generate_signals(df=df)
            portfolio: vbt.Portfolio  = vbt.Portfolio.from_signals(df['close'], entries=entries, exits=exits, init_cash=INIT_CASH, fees=FEES, freq=FREQ)
            strategies[f'BBANDS({period},{std})'] = portfolio
    return strategies

def create_obv_divergence_strategy(df: pd.DataFrame, periods: list = FAST_PERIODS) -> dict[str, vbt.Portfolio]:
    strategies = {}
    for period in periods:
        strategy = OBVDivergenceStrategy(period=period)
        entries, exits, _ = strategy.generate_signals(df=df)
        portfolio: vbt.Portfolio  = vbt.Portfolio.from_signals(df['close'], entries=entries, exits=exits, init_cash=INIT_CASH, fees=FEES, freq=FREQ)
        strategies[f'OBV_DIV({period})'] = portfolio
    return strategies

def create_cmf_strategy(df: pd.DataFrame, periods: list = FAST_PERIODS, cashin: float=0.2, cashout: float=-0.2) -> dict[str, vbt.Portfolio]:
    strategies = {}
    for period in periods:
        strategy = CMFStrategy(period=period, cashin=cashin, cashout=cashout)
        entries, exits, _ = strategy.generate_signals(df=df)
        portfolio: vbt.Portfolio  = vbt.Portfolio.from_signals(df['close'], entries=entries, exits=exits, init_cash=INIT_CASH, fees=FEES, freq=FREQ)
        strategies[f'CMF({period})'] = portfolio
    return strategies