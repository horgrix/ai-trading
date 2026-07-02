"""
AI 模型基类
"""

import joblib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional
import pandas as pd


class BaseModel(ABC):
    """所有 AI 模型的抽象基类"""

    def __init__(self, name: str = "base_model"):
        self.name = name
        self.model: Any = None
        self.is_trained: bool = False

    @abstractmethod
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> None:
        """训练模型"""
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> pd.Series:
        """使用模型进行预测"""
        pass

    def save(self, path: Optional[Path] = None) -> None:
        """保存模型到文件"""
        if not self.is_trained:
            raise ValueError("模型未训练，无法保存")
        if path is None:
            path = Path(f"{self.name}.joblib")
        joblib.dump(self.model, path)

    def load(self, path: Path) -> None:
        """从文件加载模型"""
        self.model = joblib.load(path)
        self.is_trained = True

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """评估模型性能（子类可覆盖）"""
        predictions = self.predict(X)
        return {
            "model": self.name,
            "samples": len(y),
        }