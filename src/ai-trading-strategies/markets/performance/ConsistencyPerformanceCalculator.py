import pandas as pd
import numpy as np


class ConsistencyPerformanceCalculator:

    # CV
    PERFORMANCE_CV : int = 1
    # IR
    PERFORMANCE_IR : int = 2
    # RANK
    PERFORMANCE_RANK : int = 3
    # MIX
    PERFORMANCE_MIX : int = 4

    def _consistency_cv(self, performance_matrix: pd.DataFrame):
        """
        变异系数 = 标准差 / |均值|
        一致性 = 1 / (1 + CV)
        
        得分在0-1之间，越高越稳定
        """
        scores = {}
        
        for strategy_name in performance_matrix.columns:
            values = performance_matrix[strategy_name].dropna()
            
            if len(values) < 2:
                scores[strategy_name] = np.nan
                continue
                
            mean_val = values.mean()
            std_val = values.std()
            
            if abs(mean_val) < 0.0001:  # 均值接近0
                cv = np.inf
            else:
                cv = std_val / abs(mean_val)
            
            scores[strategy_name] = 1 / (1 + cv)
        
        return pd.Series(scores)

    def _consistency_ir(self, performance_matrix: pd.DataFrame):
        """
        信息比率 = 均值 / 标准差
        衡量单位风险的超额收益稳定性
        """
        scores = {}
        
        for strategy_name in performance_matrix.columns:
            values = performance_matrix[strategy_name].dropna()
            
            if len(values) < 2:
                scores[strategy_name] = np.nan
                continue
            
            mean_val = values.mean()
            std_val = values.std()
            
            if std_val < 0.0001:
                scores[strategy_name] = np.inf if mean_val > 0 else -np.inf
            else:
                scores[strategy_name] = mean_val / std_val
        
        return pd.Series(scores)

    def _consistency_rank(self, perf_matrix):
        """
        计算策略在各环境中的排名标准差
        排名越稳定 = 一致性越高
        """
        # 每个环境下对策略排名
        rank_df = perf_matrix.rank(axis=1, ascending=False)
        
        scores = {}
        for strategy_name in rank_df.columns:
            rank_std = rank_df[strategy_name].std()
            # 排名标准差越小，一致性越高
            scores[strategy_name] = 1 / (1 + rank_std)
        
        return pd.Series(scores)

    def cal_consistency(self, performance_matrix: pd.DataFrame, consistency: int = PERFORMANCE_CV):
        """
        结合变异系数和排名稳定性
        """
        cv_scores = self._consistency_cv(performance_matrix)
        ir_scores = self._consistency_ir(performance_matrix)
        rank_scores = self._consistency_rank(performance_matrix)

        # 归一化后等权组合
        cv_norm = (cv_scores - cv_scores.min()) / (cv_scores.max() - cv_scores.min())
        rank_norm = (rank_scores - rank_scores.min()) / (rank_scores.max() - rank_scores.min())
        composite = 0.5 * cv_norm + 0.5 * rank_norm
        
        result = pd.DataFrame({
            'CV': cv_scores,
            'IR': ir_scores,
            'RANK': rank_scores,
            'MIX_CV_RANK': composite
        })

        return result