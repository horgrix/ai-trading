"""
环境依赖度分析
核心概念
衡量策略的收益是否过度集中在少数环境中。依赖度越高的策略，一旦离开舒适区就容易失效。

高依赖度：策略80%的收益来自20%的环境（危险）
低依赖度：收益均匀分布在各个环境中（稳健）
"""

import pandas as pd
import numpy as np


class DependencyPerformanceCalculator:

    def _calculate_hhi_dependency(self, performance_matrix: pd.DataFrame):
        """
        HHI = Σ(各环境收益占比)²
        
        范围：[1/n, 1]，n为环境数量
        1/n = 完全均匀分布（低依赖）
        1 = 完全集中在单一环境（高依赖）

        HHI解读标准
        HHI值	依赖程度	含义
        < 0.3	低依赖	    收益来源分散，策略健壮
        0.3-0.5	中度依赖	有一定集中度，需关注
        0.5-0.7	高度依赖	收益集中在少数环境
        > 0.7	极度依赖	严重依赖特定环境，高风险
        """
        hhi_scores = {}
        
        for strategy_name in performance_matrix.columns:
            values = performance_matrix[strategy_name].dropna()
            
            if len(values) == 0 or values.sum() == 0:
                hhi_scores[strategy_name] = np.nan
                continue
            
            # 只考虑正收益（亏损环境不算依赖）
            positive_vals = values[values > 0]
            
            if len(positive_vals) == 0:
                # 全亏损，依赖度为1
                hhi_scores[strategy_name] = 1.0
                continue
            
            # 计算每个正收益环境占总正收益的比例
            shares = positive_vals / positive_vals.sum()
            
            # HHI = Σ(share²)
            hhi = (shares ** 2).sum()
            hhi_scores[strategy_name] = hhi
        
        return pd.Series(hhi_scores).sort_values(ascending=False)


    def _calculate_cr_dependency(self, performance_matrix: pd.DataFrame, n=2):
        """
        CRn = 前n个最佳环境的收益 / 总正收益
        
        CR2=80% 意味着前2个环境贡献了80%的正收益

        CRn解读
        CR2 > 80%：策略高度依赖两个最好的环境
        CR2 < 60%：收益分布相对均匀
        CR1 > 50%：单一环境主导，极度依赖
        """
        cr_scores = {}
        
        for strategy_name in performance_matrix.columns:
            values = performance_matrix[strategy_name].dropna()
            positive_vals = values[values > 0]
            
            if len(positive_vals) == 0:
                cr_scores[strategy_name] = 1.0
                continue
            
            # 排序取前n个
            top_n_sum = positive_vals.sort_values(ascending=False).head(n).sum()
            total_positive = positive_vals.sum()
            
            cr_scores[strategy_name] = top_n_sum / total_positive
        
        return pd.Series(cr_scores).sort_values(ascending=False)

    def _calculate_adaptation_width(self, performance_matrix: pd.DataFrame):
        """
        适应宽度 = 盈利环境数 / 总环境数
        
        同时也看最差环境的表现

        解读
        适应宽度 = 1.0：所有环境都盈利（理想，但警惕过拟合）
        适应宽度 = 0.6：60%的环境盈利，40%亏损
        适应宽度 < 0.3：只在极少数环境下存活
        """
        width_scores = {}
        worst_case = {}
        
        for strategy_name in performance_matrix.columns:
            values = performance_matrix[strategy_name].dropna()
            
            # 盈利环境占比
            profitable_env = (values > 0).sum()
            total_env = len(values)
            width = profitable_env / total_env
            
            width_scores[strategy_name] = width
            worst_case[strategy_name] = values.min()
        
        width_df = pd.DataFrame({
            '适应宽度': pd.Series(width_scores),
            '最差环境收益': pd.Series(worst_case),
            '环境总数': len(performance_matrix)
        })
        
        return width_df.sort_values('适应宽度', ascending=False)

    def _calculate_environment_elasticity(self, performance_matrix: pd.DataFrame, time_in_env):
        """
        弹性 = 收益波动率 / 环境时间占比波动率
        
        高弹性 = 环境变化对策略影响大
        低弹性 = 策略对环境变化不敏感
        """
        elasticity = {}
        
        for strategy_name in performance_matrix.columns:
            values = performance_matrix[strategy_name].dropna()
            
            if len(values) < 2:
                elasticity[strategy_name] = np.nan
                continue
            
            # 收益的变异系数
            ret_cv = values.std() / abs(values.mean()) if abs(values.mean()) > 0.001 else np.inf
            
            # 如果各环境时间占比差异大，说明环境本身分布不均
            # 这种情况下策略的"依赖"更可能是环境分布造成的
            if time_in_env.std() > 0.01:
                elasticity[strategy_name] = ret_cv / time_in_env.std()
            else:
                elasticity[strategy_name] = ret_cv
        
        return pd.Series(elasticity).sort_values(ascending=False)

    def cal_dependency(self, performance_matrix: pd.DataFrame):
        """
        综合HHI、CR2、适应宽度三个维度
        输出0-1之间的综合依赖度得分
        """
        # 计算各维度
        hhi = self._calculate_hhi_dependency(performance_matrix)
        cr2 = self._calculate_cr_dependency(performance_matrix, n=2)
        width = self._calculate_adaptation_width(performance_matrix)['适应宽度']
        
        # 归一化到0-1（都转换为"依赖度"方向，越高越依赖）
        hhi_norm = (hhi - 1/len(performance_matrix)) / (1 - 1/len(performance_matrix))  # HHI归一化
        cr2_norm = cr2  # CR2本身在0-1
        width_norm = 1 - width  # 适应宽度取反
        
        # 等权综合
        composite = (hhi_norm + cr2_norm + width_norm) / 3
        
        result = pd.DataFrame({
            'HHI依赖度': hhi_norm,
            'CR2集中度': cr2_norm,
            '宽度缺乏度': width_norm,
            '综合依赖度': composite
        })
        
        return result.sort_values('综合依赖度', ascending=False)
