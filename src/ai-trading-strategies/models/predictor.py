"""
价格预测器 - 基于技术指标的价格涨跌预测
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple

from .base_model import BaseModel
from ..fetcher.processor import add_all_indicators


class PricePredictor(BaseModel):
    """
    价格涨跌预测器
    使用技术指标作为特征，预测未来 N 天的涨跌方向
    """

    def __init__(self, name: str = "price_predictor", lookahead: int = 5):
        super().__init__(name)
        self.lookahead = lookahead
        self.feature_columns: list = []

    def prepare_features(
        self, df: pd.DataFrame, column: str = "Close"
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        准备特征和标签

        Args:
            df: 原始 OHLCV 数据
            column: 目标列

        Returns:
            X: 特征 DataFrame, y: 标签 Series (1=涨, 0=跌)
        """
        # 添加技术指标
        df = add_all_indicators(df, column)

        # 创建标签：未来 lookahead 天后是否上涨
        future_price = df[column].shift(-self.lookahead)
        df["target"] = (future_price > df[column]).astype(int)

        # 选择特征列（排除非数值列和目标列）
        exclude_cols = ["target"]
        self.feature_columns = [
            c
            for c in df.columns
            if c not in exclude_cols and df[c].dtype in [np.float64, np.int64]
        ]

        # 删除 NaN
        df.dropna(inplace=True)

        X = df[self.feature_columns]
        y = df["target"]

        return X, y

    def train(
        self, df: pd.DataFrame, column: str = "Close", **kwargs
    ) -> None:
        """
        训练预测模型（占位实现，子类应覆盖）
        """
        X, y = self.prepare_features(df, column)
        # TODO: 实现实际的模型训练逻辑
        # 例如使用 sklearn.ensemble.RandomForestClassifier 等
        self.is_trained = True

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """
        进行预测（占位实现，子类应覆盖）
        """
        if not self.is_trained:
            raise ValueError("模型未训练")
        # TODO: 返回实际预测结果
        return pd.Series([0] * len(X), index=X.index)