"""
双均线 + DMI 趋势策略 - 基于 backtrader 实现

策略规格：
每次操作前要检查目前仓位水位，若已经满仓则不进行操作

| 模块     | 条件                                                                                     | 投入仓位 |
|----------|------------------------------------------------------------------------------------------|----------|
| 多头入场 | ADX > 25 且 +DI > -DI 且 快均线上穿慢均线（金叉）                                        | 60%      |
| 多头追加 | ADX > 40 且 +DI > -DI 且 快均线在慢均线之上 且 快均线和慢均线均为上升趋势                | 35%      |
| 空头入场 | ADX > 25 且 -DI > +DI 且 快均线下穿慢均线（死叉）                                        | 60%      |
| 多头平仓 | +DI < -DI（多头转弱）或 死叉出现 或 (ADX >= 55 且 快均线和慢均线其中一个为下降趋势)      | -        |
| 空头平仓 | -DI < +DI（空头转弱）或 金叉出现                                                         | -        |

注意：入场 + 追加累计最大 95%，不满仓，留 5% 缓冲。
"""

import backtrader as bt
from typing import Optional


class SmaWithDmiTrendStrategy(bt.Strategy):
    """
    双均线与 DMI 趋势策略

    结合 SMA 双均线交叉信号与 DMI(ADX/±DI) 趋势强度过滤，
    在趋势明确且方向一致时入场，趋势衰竭或反转时平仓。
    """

    params = (
        # 均线参数
        ('fast', 10),           # 快均线周期
        ('slow', 30),           # 慢均线周期
        # DMI 参数
        ('dmi_period', 14),     # DMI 计算周期
        ('adx_trend', 25),      # ADX 趋势阈值（入场最低要求）
        ('adx_strong', 40),     # ADX 强趋势阈值（追加条件）
        ('adx_extreme', 55),    # ADX 极端阈值（潜在反转平仓）
        # 仓位比例
        ('entry_ratio', 0.60),  # 入场仓位比例（多头/空头）
        ('add_ratio', 0.35),    # 多头追加仓位比例（累计最大 95%，留 5% 缓冲）
        ('max_ratio', 0.95),    # 满仓阈值（总仓位占比），超过视为满仓不操作
        # 风险控制
        ('trailing_stop', 0.0), # （预留）追踪止损比例，0 表示不启用
    )

    def __init__(self):
        # ========== 均线系统 ==========
        self.sma_fast = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.fast
        )
        self.sma_slow = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.slow
        )
        self.crossover = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)

        # ========== DMI 系统 ==========
        self.dmi = bt.indicators.DMI(self.data, period=self.params.dmi_period)
        self.plus_di = self.dmi.plusDI    # +DI
        self.minus_di = self.dmi.minusDI  # -DI
        self.adx = self.dmi.adx           # ADX

        # ========== 状态跟踪 ==========
        self.entry_bar = 0                # 入场 K 线索引，用于避免同一根K线重复入场

    # ======================== 辅助判断方法 ========================

    def _adx_valid(self) -> bool:
        """ADX 是否已计算出有效值（排除 NaN）"""
        return not (self.adx[0] != self.adx[0])  # NaN != NaN 为 True

    def _sma_fast_rising(self) -> bool:
        """快均线是否处于上升趋势（当前值 > 前一周期值）"""
        return (len(self.sma_fast) >= 2
                and self.sma_fast[0] > self.sma_fast[-1])

    def _sma_slow_rising(self) -> bool:
        """慢均线是否处于上升趋势（当前值 > 前一周期值）"""
        return (len(self.sma_slow) >= 2
                and self.sma_slow[0] > self.sma_slow[-1])

    def _sma_fast_falling(self) -> bool:
        """快均线是否处于下降趋势（当前值 < 前一周期值）"""
        return (len(self.sma_fast) >= 2
                and self.sma_fast[0] < self.sma_fast[-1])

    def _sma_slow_falling(self) -> bool:
        """慢均线是否处于下降趋势（当前值 < 前一周期值）"""
        return (len(self.sma_slow) >= 2
                and self.sma_slow[0] < self.sma_slow[-1])

    # ======================== 仓位计算 ========================

    def _get_target_value(self, ratio: float) -> float:
        """计算目标市值"""
        return self.broker.get_value() * ratio

    def _is_full_position(self) -> bool:
        """
        检查是否已满仓（超过 max_ratio 阈值）
        满仓定义：当前持仓市值 >= 总资产 * max_ratio
        """
        if not self.position:
            return False
        current_exposure = abs(self.position.size) * self.data.close[0]
        total_value = self.broker.get_value()
        return current_exposure >= total_value * self.params.max_ratio

    # ======================== 主逻辑 ========================

    def next(self):
        # 跳过指标尚未就绪的阶段
        if not self._adx_valid():
            return

        # 获取当前指标值
        adx_val = self.adx[0]
        plus_di_val = self.plus_di[0]
        minus_di_val = self.minus_di[0]
        cross_val = self.crossover[0]
        sma_fast_above_slow = self.sma_fast[0] > self.sma_slow[0]

        # ---- 趋势强度判断 ----
        is_trend = adx_val > self.params.adx_trend      # ADX > 25
        trend_strong = adx_val > self.params.adx_strong  # ADX > 40
        trend_extreme = adx_val >= self.params.adx_extreme  # ADX >= 55

        # ---- 多空方向判断 ----
        is_bullish = plus_di_val > minus_di_val   # +DI > -DI → 多头占优
        is_bearish = minus_di_val > plus_di_val   # -DI > +DI → 空头占优

        # ---- 交叉信号 ----
        golden_cross = cross_val > 0   # 金叉（快线上穿慢线）
        dead_cross = cross_val < 0     # 死叉（快线下穿慢线）

        # ---- 均线趋势 ----
        both_sma_rising = self._sma_fast_rising() and self._sma_slow_rising()
        sma_falling = self._sma_fast_falling() or self._sma_slow_falling()

        # ==================== 持仓状态处理 ====================
        if self.position:
            if self.position.size > 0:
                # ===== 多头持仓 =====
                # 多头平仓条件：
                #   1. +DI < -DI（多头转弱）
                #   2. 死叉出现
                #   3. ADX >= 55 且 快/慢均线其中一个下降
                should_close_long = (
                    not is_bullish          # +DI < -DI
                    or dead_cross           # 死叉
                    or (trend_extreme and sma_falling)  # ADX极端 + 均线下降
                )
                if should_close_long:
                    self.close()
                    self.log(
                        f"多头平仓 | Price={self.data.close[0]:.2f} "
                        f"ADX={adx_val:.1f} +DI={plus_di_val:.1f} -DI={minus_di_val:.1f} "
                        f"Cross={cross_val} FastRise={self._sma_fast_rising()} SlowRise={self._sma_slow_rising()}"
                    )
                else:
                    # 多头追加：ADX > 40 且 +DI > -DI 且 SMA快在SMA慢之上 且 双均线上升
                    # 满仓检查：若已满仓则不追加
                    if self._is_full_position():
                        pass  # 满仓，跳过追加
                    elif trend_strong and is_bullish and sma_fast_above_slow and both_sma_rising:
                        # 目标仓位 = 入场60% + 追加35% = 95%
                        full_target_ratio = self.params.entry_ratio + self.params.add_ratio
                        target_value = self._get_target_value(full_target_ratio)
                        if target_value > self.position.size * self.data.close[0]:
                            self.order_target_value(target=target_value)
                            self.log(
                                f"多头追加@{full_target_ratio:.0%} | Price={self.data.close[0]:.2f} "
                                f"ADX={adx_val:.1f} +DI={plus_di_val:.1f} -DI={minus_di_val:.1f}"
                            )

            elif self.position.size < 0:
                # ===== 空头持仓 =====
                # 空头平仓条件：
                #   1. -DI < +DI（空头转弱）
                #   2. 金叉出现
                should_close_short = (
                    not is_bearish    # -DI < +DI
                    or golden_cross   # 金叉
                )
                if should_close_short:
                    self.close()
                    self.log(
                        f"空头平仓 | Price={self.data.close[0]:.2f} "
                        f"ADX={adx_val:.1f} +DI={plus_di_val:.1f} -DI={minus_di_val:.1f} "
                        f"Cross={cross_val}"
                    )

        else:
            # ==================== 空仓 → 寻找入场信号 ====================
            # 避免同一根K线多个信号导致重复触发
            if len(self) == self.entry_bar:
                return

            # ---- 多头入场：ADX > 25 且 +DI > -DI 且 金叉 ----
            if is_trend and is_bullish and golden_cross:
                target_value = self._get_target_value(self.params.entry_ratio)
                self.order_target_value(target=target_value)
                self.entry_bar = len(self)
                self.log(
                    f"多头入场@{self.params.entry_ratio:.0%} | Price={self.data.close[0]:.2f} "
                    f"ADX={adx_val:.1f} +DI={plus_di_val:.1f} -DI={minus_di_val:.1f} Cross={cross_val}"
                )

            # ---- 空头入场：ADX > 25 且 -DI > +DI 且 死叉 ----
            elif is_trend and is_bearish and dead_cross:
                target_value = self._get_target_value(self.params.entry_ratio)
                self.order_target_value(target=target_value)
                self.entry_bar = len(self)
                self.log(
                    f"空头入场@{self.params.entry_ratio:.0%} | Price={self.data.close[0]:.2f} "
                    f"ADX={adx_val:.1f} +DI={plus_di_val:.1f} -DI={minus_di_val:.1f} Cross={cross_val}"
                )

    # ======================== 通知与日志 ========================

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                action = '买入' if order.size > 0 else '卖出(空头平仓)'
            else:
                action = '卖出' if order.size > 0 else '买入(空头开仓)'
            self.log(
                f'订单成交 | {action} Size={order.executed.size:.0f} '
                f'Price={order.executed.price:.2f} Comm={order.executed.comm:.2f}'
            )

    def log(self, txt: str):
        """输出带时间戳的日志"""
        dt = self.datas[0].datetime.date(0).isoformat()
        print(f'[{dt}] {txt}')

