"""
AI Trading - 主入口文件
双均线 + DMI 趋势策略回测应用

数据: 港股 02400 (心动公司) | 2019-01-01 ~ 2039-01-01
初始资金: 100,000
"""

import sys
from pathlib import Path

# 将 src 目录添加到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

import backtrader as bt

from src.data.fetcher import get_hk_stock_data_with_cache
from src.strategies.trend_strategy import SmaWithDmiTrendStrategy


def main():
    """主函数：运行回测"""
    print("=" * 60)
    print("  AI Trading - 双均线 + DMI 趋势策略回测")
    print("=" * 60)

    # 1. 获取数据
    symbol = "02400"
    start_date = "2019-01-01"
    end_date = "2039-01-01"

    print(f"\n[INFO] 获取港股数据: {symbol} ({start_date} ~ {end_date})")
    data_df = get_hk_stock_data_with_cache(
        symbol=symbol, start_date=start_date, end_date=end_date
    )

    if data_df is None or data_df.empty:
        print(f"[ERROR] 无法获取 {symbol} 的数据，回测终止。")
        return

    print(f"   数据量: {len(data_df)} 条")
    print(f"   日期范围: {data_df.index[0].date()} ~ {data_df.index[-1].date()}")

    # 2. 构建 Backtrader 数据源
    data_feed = bt.feeds.PandasData(
        dataname=data_df,
        datetime=None,          # 使用 DataFrame 的索引作为日期
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        openinterest=-1,
    )

    # 3. 初始化 Cerebro 引擎
    cerebro = bt.Cerebro()

    # 添加数据
    cerebro.adddata(data_feed)

    # 添加策略
    cerebro.addstrategy(SmaWithDmiTrendStrategy)

    # 设置初始资金与佣金
    initial_cash = 100000.0
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=0.001)

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe',
                         timeframe=bt.TimeFrame.Days, annualize=True)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual_return')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    # 4. 运行回测
    print(f"\n[INFO] 初始资金: {initial_cash:,.2f}")
    print("-" * 60)
    print("  回测运行中...")
    print("-" * 60)

    results = cerebro.run()

    # 5. 输出绩效
    final_value = cerebro.broker.get_value()
    total_return = (final_value - initial_cash) / initial_cash

    print(f"\n{'=' * 60}")
    print(f"  回测完成")
    print(f"{'=' * 60}")
    print(f"  最终资金:   {final_value:,.2f}")
    print(f"  总收益率:   {total_return:+.2%}")
    print(f"  绝对收益:   {final_value - initial_cash:+,.2f}")
    print(f"{'=' * 60}")

    # 分析器结果
    strat = results[0]

    # 夏普比率
    sharpe_analysis = strat.analyzers.sharpe.get_analysis()
    sharpe_ratio = sharpe_analysis.get('sharperatio', None)
    print(f"  夏普比率:   {sharpe_ratio:.4f}" if sharpe_ratio else "  夏普比率:   N/A")

    # 最大回撤
    drawdown_analysis = strat.analyzers.drawdown.get_analysis()
    max_dd = drawdown_analysis.get('max', {}).get('drawdown', 0)
    print(f"  最大回撤:   {max_dd:+.2%}")

    # 年化收益率
    annual_analysis = strat.analyzers.annual_return.get_analysis()
    if annual_analysis:
        avg_annual = sum(annual_analysis.values()) / len(annual_analysis)
        print(f"  平均年化:   {avg_annual:+.2%}")

    # 交易统计
    trade_analysis = strat.analyzers.trades.get_analysis()
    total_trades = trade_analysis.get('total', {}).get('total', 0)
    won_trades = trade_analysis.get('won', {}).get('total', 0)
    lost_trades = trade_analysis.get('lost', {}).get('total', 0)
    win_rate = won_trades / total_trades if total_trades > 0 else 0

    print(f"  总交易数:   {total_trades}")
    print(f"  盈利次数:   {won_trades}")
    print(f"  亏损次数:   {lost_trades}")
    print(f"  胜率:       {win_rate:.2%}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()