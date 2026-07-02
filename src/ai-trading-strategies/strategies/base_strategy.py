"""
交易策略基类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import pandas as pd


class Signal:
    """交易信号"""

    BUY = 1
    SELL = -1
    HOLD = 0

    @staticmethod
    def to_string(signal: int) -> str:
        if signal == Signal.BUY:
            return "BUY"
        elif signal == Signal.SELL:
            return "SELL"
        return "HOLD"


class BaseStrategy(ABC):
    """所有交易策略的抽象基类"""

    def __init__(self, name: str = "base_strategy"):
        self.name = name
        self.positions: List[Dict] = []
        self.current_position: int = 0  # 0=空仓, 1=持仓

    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> int:
        """
        根据数据生成交易信号

        Args:
            data: 市场数据 DataFrame

        Returns:
            交易信号: Signal.BUY(1), Signal.SELL(-1), Signal.HOLD(0)
        """
        pass

    def execute(self, data: pd.DataFrame, capital: float) -> pd.DataFrame:
        """
        执行策略回测

        Args:
            data: 市场数据
            capital: 初始资金

        Returns:
            包含回测结果的 DataFrame
        """
        df = data.copy()
        df["signal"] = Signal.HOLD
        df["position"] = 0
        df["portfolio_value"] = capital

        for i in range(len(df)):
            current_data = df.iloc[: i + 1]
            signal = self.generate_signal(current_data)
            if i < len(df) - 1:
                df.iloc[i + 1, df.columns.get_loc("signal")] = signal

        return df

    def calculate_metrics(self, results: pd.DataFrame) -> dict:
        """
        计算策略绩效指标

        Args:
            results: 回测结果 DataFrame

        Returns:
            包含绩效指标的字典
        """
        if "returns" not in results.columns:
            results["returns"] = results["Close"].pct_change()

        total_return = (results["Close"].iloc[-1] / results["Close"].iloc[0]) - 1
        sharpe = (
            results["returns"].mean() / results["returns"].std() * (252**0.5)
            if results["returns"].std() > 0
            else 0
        )

        return {
            "strategy": self.name,
            "total_return": f"{total_return:.2%}",
            "sharpe_ratio": f"{sharpe:.2f}",
            "max_drawdown": self._calculate_max_drawdown(results),
        }

    def _calculate_max_drawdown(self, results: pd.DataFrame) -> str:
        """计算最大回撤"""
        cumulative = (1 + results["returns"].fillna(0)).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return f"{drawdown.min():.2%}"