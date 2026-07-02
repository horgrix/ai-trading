import backtrader as bt

class DynamicPositionStrategy(bt.Strategy):
    """
    双均线 + DMI 趋势跟踪策略
    动态仓位管理：
    - 仓位 0~50%：每次加仓 25%
    - 仓位 50%~90%：每次加仓 15%
    - 仓位 ≥ 90%：不再加仓
    """
    params = (
        ('fast', 10),
        ('slow', 30),
        ('ma_type', 'SMA'),
        ('dmi_period', 14),
        ('adx_threshold', 25),
        # 仓位管理参数
        ('max_position_ratio', 0.95),      # 满仓阈值 90%
        ('aggressive_ratio', 0.25),        # 低仓位时加仓比例 25%
        ('conservative_ratio', 0.15),      # 高仓位时加仓比例 15%
        ('position_threshold', 0.50),      # 区分高低仓位的阈值 50%
    )

    def __init__(self):
        # 均线
        if self.params.ma_type == 'SMA':
            self.ma_fast = bt.indicators.SMA(self.data.close, period=self.params.fast)
            self.ma_slow = bt.indicators.SMA(self.data.close, period=self.params.slow)
        else:
            self.ma_fast = bt.indicators.EMA(self.data.close, period=self.params.fast)
            self.ma_slow = bt.indicators.EMA(self.data.close, period=self.params.slow)

        self.crossover = bt.indicators.CrossOver(self.ma_fast, self.ma_slow)

        # 均线斜率
        self.fast_slope = self.ma_fast - self.ma_fast(-1)
        self.slow_slope = self.ma_slow - self.ma_slow(-1)

        # DMI
        self.dmi = bt.indicators.DMI(self.data, period=self.params.dmi_period)
        self.adx = self.dmi.adx
        self.plus_di = self.dmi.plusDI
        self.minus_di = self.dmi.minusDI

        self.order = None

    def get_slope_state(self, slope_val, threshold=0.01):
        if slope_val > threshold:
            return 'up'
        elif slope_val < -threshold:
            return 'down'
        else:
            return 'flat'

    def get_current_position_ratio(self):
        """计算当前持仓占总资产的比例"""
        if self.position.size == 0:
            return 0.0
        position_value = abs(self.position.size) * self.data.close[0]
        total_value = self.broker.get_value()
        return position_value / total_value if total_value > 0 else 0.0

    def calculate_add_size(self, price, total_value):
        """
        根据当前仓位计算加仓数量
        返回: (加仓数量, 加仓比例)
        """
        current_ratio = self.get_current_position_ratio()
        
        # 满仓检查
        if current_ratio >= self.params.max_position_ratio:
            print(f"  ⚠️ 当前仓位 {current_ratio:.1%} ≥ {self.params.max_position_ratio:.0%}，已满仓，不再加仓")
            return 0, 0.0

        # 计算本次加仓比例
        if current_ratio < self.params.position_threshold:
            add_ratio = self.params.aggressive_ratio  # 25%
            level = "积极"
        else:
            add_ratio = self.params.conservative_ratio  # 15%
            level = "保守"

        # 检查加仓后是否超过满仓阈值
        target_ratio = min(current_ratio + add_ratio, self.params.max_position_ratio)
        actual_add_ratio = target_ratio - current_ratio
        
        # 计算股数
        add_value = total_value * actual_add_ratio
        size = int(add_value / price)
        
        return size, actual_add_ratio

    def get_ma_status(self):
        fast_val = self.ma_fast[0]
        slow_val = self.ma_slow[0]
        fast_prev = self.ma_fast[-1]
        slow_prev = self.ma_slow[-1]

        fast_state = self.get_slope_state(fast_val - fast_prev)
        slow_state = self.get_slope_state(slow_val - slow_prev)

        return {
            'fast_state': fast_state,
            'slow_state': slow_state,
            'is_above': fast_val > slow_val,
            'cross': self.crossover[0],
            'spread': fast_val - slow_val,
            'fast_val': fast_val,
            'slow_val': slow_val,
        }

    def next(self):
        if self.order:
            return

        # 获取市场状态
        status = self.get_ma_status()
        fast_state = status['fast_state']
        slow_state = status['slow_state']
        cross = status['cross']
        spread = status['spread']

        # DMI
        adx_val = self.adx[0]
        plus_di_val = self.plus_di[0]
        minus_di_val = self.minus_di[0]
        trend_strong = adx_val > self.params.adx_threshold
        is_bullish = plus_di_val > minus_di_val
        is_bearish = minus_di_val > plus_di_val

        price = self.data.close[0]
        total_value = self.broker.get_value()
        current_ratio = self.get_current_position_ratio()

        # === 空仓 → 入场 ===
        if not self.position:
            entry_signal = None

            # 多头入场条件
            if cross > 0 and trend_strong and is_bullish:
                entry_signal = 'buy'
            elif (fast_state == 'up' and slow_state == 'up' and 
                  not status['is_above'] and spread > -0.5 and trend_strong and is_bullish):
                entry_signal = 'buy'

            # 空头入场条件
            if cross < 0 and trend_strong and is_bearish:
                entry_signal = 'sell'
            elif (fast_state == 'down' and slow_state == 'down' and 
                  status['is_above'] and spread < 0.5 and trend_strong and is_bearish):
                entry_signal = 'sell'

            if entry_signal == 'buy':
                size, add_ratio = self.calculate_add_size(price, total_value)
                if size > 0:
                    self.order = self.buy(size=size)
                    print(f"{self.data.datetime.date(0)} 🟢 多头入场 | "
                          f"仓位:{current_ratio:.1%} → +{add_ratio:.1%} | "
                          f"买入 {size} 股 @ {price:.2f} | "
                          f"ADX:{adx_val:.2f}")

            elif entry_signal == 'sell':
                size, add_ratio = self.calculate_add_size(price, total_value)
                if size > 0:
                    self.order = self.sell(size=size)
                    print(f"{self.data.datetime.date(0)} 🔴 空头入场 | "
                          f"仓位:{current_ratio:.1%} → +{add_ratio:.1%} | "
                          f"卖出 {size} 股 @ {price:.2f} | "
                          f"ADX:{adx_val:.2f}")

        # === 有持仓 → 加仓或平仓 ===
        else:
            current_size = self.position.size

            # --- 平仓条件 ---
            close_signal = False
            close_reason = ""

            if current_size > 0:  # 多头持仓
                if cross < 0:
                    close_signal = True
                    close_reason = "死叉"
                elif fast_state in ['flat', 'down'] and slow_state in ['flat', 'down'] and spread < 0:
                    close_signal = True
                    close_reason = "趋势转弱"
                elif not is_bullish:
                    close_signal = True
                    close_reason = "DI转空"

            elif current_size < 0:  # 空头持仓
                if cross > 0:
                    close_signal = True
                    close_reason = "金叉"
                elif fast_state in ['flat', 'up'] and slow_state in ['flat', 'up'] and spread > 0:
                    close_signal = True
                    close_reason = "趋势转强"
                elif is_bullish:
                    close_signal = True
                    close_reason = "DI转多"

            if close_signal:
                self.order = self.close()
                print(f"{self.data.datetime.date(0)} 🔵 平仓 | 原因:{close_reason} | "
                      f"仓位:{current_ratio:.1%} → 0% | "
                      f"价格:{price:.2f}")
                return

            # --- 加仓条件（信号持续且未满仓） ---
            if current_ratio < self.params.max_position_ratio:
                add_signal = False
                add_direction = None

                if current_size > 0:  # 多头持仓
                    # 趋势延续且多头方向不变 → 加仓
                    if (trend_strong and is_bullish and 
                        fast_state == 'up' and slow_state == 'up' and 
                        status['is_above'] and spread > 0):
                        add_signal = True
                        add_direction = 'buy'

                elif current_size < 0:  # 空头持仓
                    if (trend_strong and is_bearish and 
                        fast_state == 'down' and slow_state == 'down' and 
                        not status['is_above'] and spread < 0):
                        add_signal = True
                        add_direction = 'sell'

                if add_signal:
                    size, add_ratio = self.calculate_add_size(price, total_value)
                    if size > 0:
                        if add_direction == 'buy':
                            self.order = self.buy(size=size)
                        else:
                            self.order = self.sell(size=size)
                        print(f"{self.data.datetime.date(0)} 📈 加仓 | "
                              f"方向:{'多头' if add_direction=='buy' else '空头'} | "
                              f"仓位:{current_ratio:.1%} → +{add_ratio:.1%} | "
                              f"加仓 {size} 股 @ {price:.2f}")

    def notify_order(self, order):
        if order.status == order.Completed:
            self.order = None
            print(f"  ✅ 成交 | 数量:{order.executed.size} 价格:{order.executed.price:.2f}")
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.order = None
            print(f"  ❌ 订单失败")


# ============ 运行主程序 ============
if __name__ == '__main__':
    import akshare as ak
    import pandas as pd

    def get_hk_data(symbol="02400", start_date="2022-01-01", end_date="2023-12-31"):
        df = ak.stock_hk_daily(symbol=symbol, adjust="")
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        df.columns = [col.lower() for col in df.columns]
        return df

    df = get_hk_data()
    data = bt.feeds.PandasData(dataname=df)

    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(DynamicPositionStrategy)
    cerebro.broker.setcash(1000000.0)
    cerebro.broker.setcommission(commission=0.0005)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    print(f'初始资金: {cerebro.broker.getvalue():.2f}')
    results = cerebro.run()
    print(f'最终资金: {cerebro.broker.getvalue():.2f}')

    strat = results[0]
    print('\n📊 绩效指标:')
    print(f'  夏普比率: {strat.analyzers.sharpe.get_analysis().get("sharperatio", "N/A")}')
    dd = strat.analyzers.drawdown.get_analysis()
    print(f'  最大回撤: {dd.get("max", {}).get("drawdown", "N/A")}')
    print(f'  总收益率: {strat.analyzers.returns.get_analysis().get("rtot", "N/A"):.2f}%')

    cerebro.plot(style='candlestick')