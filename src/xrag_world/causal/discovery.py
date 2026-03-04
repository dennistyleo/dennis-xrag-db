"""
因果發現算法 - 從數據中學習因果結構
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from scipy import stats
from sklearn.feature_selection import mutual_info_regression
import itertools

from ..models.causal_graph import CausalGraph, EdgeType

class CausalDiscovery:
    """
    因果發現基類
    """
    
    def __init__(self, alpha: float = 0.05):
        """
        Args:
            alpha: 顯著性水平
        """
        self.alpha = alpha
        self.variable_names = None
        self.n_variables = None
        
    def discover(self, data: np.ndarray, variable_names: Optional[List[str]] = None) -> CausalGraph:
        """
        從數據中發現因果結構
        
        Args:
            data: 數據矩陣 (n_samples, n_variables)
            variable_names: 變量名稱列表
            
        Returns:
            學習到的因果圖
        """
        raise NotImplementedError

class PCAlgorithm(CausalDiscovery):
    """
    PC算法 (Peter-Clark)
    基於條件獨立性測試的因果發現算法
    """
    
    def __init__(self, 
                 alpha: float = 0.05,
                 independence_test: str = 'pearson',
                 max_condition_size: int = 3):
        super().__init__(alpha)
        self.independence_test = independence_test
        self.max_condition_size = max_condition_size
        self.separation_sets = {}  # 記錄分離集
        
    def discover(self, data: np.ndarray, variable_names: Optional[List[str]] = None) -> CausalGraph:
        """
        PC算法的三個階段:
        1. 構建無向骨架圖
        2. 確定邊的方向
        3. 傳播方向約束
        """
        n_samples, n_vars = data.shape
        self.n_variables = n_vars
        
        if variable_names is None:
            variable_names = [f'X{i}' for i in range(n_vars)]
        self.variable_names = variable_names
        
        print(f"\n🔍 Running PC Algorithm on {n_vars} variables...")
        
        # === 階段1: 構建無向骨架圖 ===
        print("   Phase 1: Building skeleton...")
        skeleton = self._build_skeleton(data)
        
        # === 階段2: 確定v-structures ===
        print("   Phase 2: Identifying v-structures...")
        directed_edges = self._orient_v_structures(skeleton, data)
        
        # === 階段3: 傳播方向約束 ===
        print("   Phase 3: Propagating directions...")
        final_graph = self._propagate_directions(skeleton, directed_edges)
        
        # 創建因果圖
        causal_graph = CausalGraph(name="PC_Discovered")
        for i, var in enumerate(variable_names):
            causal_graph.add_variable(var)
        
        for (i, j), directed in directed_edges.items():
            if directed == 1:  # i -> j
                causal_graph.add_cause(variable_names[i], variable_names[j])
            elif directed == -1:  # j -> i
                causal_graph.add_cause(variable_names[j], variable_names[i])
        
        return causal_graph
    
    def _build_skeleton(self, data: np.ndarray) -> np.ndarray:
        """構建無向骨架圖"""
        n_vars = self.n_variables
        adj_matrix = np.ones((n_vars, n_vars)) - np.eye(n_vars)  # 初始完全連接
        
        # 逐步增加條件集大小
        for k in range(self.max_condition_size + 1):
            print(f"      Testing with |condition set| = {k}")
            
            for i in range(n_vars):
                for j in range(i+1, n_vars):
                    if adj_matrix[i, j] == 0:
                        continue
                    
                    # 獲取可能的條件集
                    candidates = [v for v in range(n_vars) if v != i and v != j and adj_matrix[i, v] == 1]
                    
                    if len(candidates) < k:
                        continue
                    
                    # 測試所有大小為k的條件集
                    for cond_set in itertools.combinations(candidates, k):
                        p_value = self._test_conditional_independence(
                            data[:, i], data[:, j], data[:, list(cond_set)]
                        )
                        
                        if p_value > self.alpha:
                            # 條件獨立，移除邊
                            adj_matrix[i, j] = adj_matrix[j, i] = 0
                            self.separation_sets[(i, j)] = set(cond_set)
                            self.separation_sets[(j, i)] = set(cond_set)
                            break
        
        return adj_matrix
    
    def _test_conditional_independence(self, 
                                      x: np.ndarray, 
                                      y: np.ndarray, 
                                      z: np.ndarray) -> float:
        """測試條件獨立性 x ⟂ y | z"""
        
        if self.independence_test == 'pearson':
            # 使用偏相關
            if z.size == 0:
                # 無條件
                corr, p_value = stats.pearsonr(x, y)
                return p_value
            else:
                # 計算偏相關
                from sklearn.linear_model import LinearRegression
                
                # 回歸x on z
                model_x = LinearRegression().fit(z, x)
                resid_x = x - model_x.predict(z)
                
                # 回歸y on z
                model_y = LinearRegression().fit(z, y)
                resid_y = y - model_y.predict(z)
                
                # 計算殘差相關
                corr, p_value = stats.pearsonr(resid_x, resid_y)
                return p_value
                
        elif self.independence_test == 'mutual_info':
            # 使用條件互信息
            if z.size == 0:
                mi = mutual_info_regression(x.reshape(-1, 1), y)[0]
            else:
                # 近似條件互信息
                mi = mutual_info_regression(np.column_stack([x.reshape(-1, 1), z]), y)[0]
            
            # 轉換為p值（近似）
            n = len(x)
            test_stat = 2 * n * mi
            p_value = 1 - stats.chi2.cdf(test_stat, df=1)
            return p_value
        
        else:
            return 1.0
    
    def _orient_v_structures(self, 
                            skeleton: np.ndarray, 
                            data: np.ndarray) -> Dict[Tuple[int, int], int]:
        """識別v-structures (colliders)"""
        n_vars = self.n_variables
        directed = {}
        
        for i in range(n_vars):
            for j in range(i+1, n_vars):
                if skeleton[i, j] == 0:
                    continue
                
                # 尋找共同鄰居
                common_neighbors = []
                for k in range(n_vars):
                    if k != i and k != j and skeleton[i, k] == 1 and skeleton[j, k] == 1:
                        common_neighbors.append(k)
                
                for k in common_neighbors:
                    # 檢查k是否不在分離集中
                    sep_set = self.separation_sets.get((i, j), set())
                    if k not in sep_set:
                        # 這是v-structure: i -> k <- j
                        directed[(i, k)] = 1  # i -> k
                        directed[(j, k)] = 1  # j -> k
        
        return directed
    
    def _propagate_directions(self, 
                             skeleton: np.ndarray,
                             directed_edges: Dict[Tuple[int, int], int]) -> nx.DiGraph:
        """傳播方向約束（避免形成環）"""
        n_vars = self.n_variables
        
        # 創建有向圖
        G = nx.DiGraph()
        G.add_nodes_from(range(n_vars))
        
        # 添加已知方向
        for (i, j), d in directed_edges.items():
            if d == 1:
                G.add_edge(i, j)
        
        # 應用方向傳播規則
        changed = True
        while changed:
            changed = False
            
            for i in range(n_vars):
                for j in range(n_vars):
                    if i == j or skeleton[i, j] == 0:
                        continue
                    
                    # 規則1: 如果 i -> j 且 j - k 無向，且 i 和 k 不相鄰，則 j -> k
                    if G.has_edge(i, j):
                        for k in range(n_vars):
                            if (k != i and k != j and skeleton[j, k] == 1 and 
                                not G.has_edge(j, k) and not G.has_edge(k, j) and
                                skeleton[i, k] == 0):
                                G.add_edge(j, k)
                                changed = True
                    
                    # 規則2: 如果 i -> j 且 i - k 無向，且 j 和 k 不相鄰，則 i -> k
                    if G.has_edge(i, j):
                        for k in range(n_vars):
                            if (k != i and k != j and skeleton[i, k] == 1 and
                                not G.has_edge(i, k) and not G.has_edge(k, i) and
                                skeleton[j, k] == 0):
                                G.add_edge(i, k)
                                changed = True
        
        return G


class FCIAlgorithm(CausalDiscovery):
    """
    FCI算法 (Fast Causal Inference)
    處理潛在混雜變量和選擇偏差
    """
    
    def discover(self, data: np.ndarray, variable_names: Optional[List[str]] = None) -> CausalGraph:
        """
        FCI算法可以發現部分有向的因果圖（PAG）
        """
        # 簡化實現 - 實際FCI更複雜
        pc = PCAlgorithm(alpha=self.alpha)
        causal_graph = pc.discover(data, variable_names)
        
        # 添加可能的混雜因子
        causal_graph.name = "FCI_Discovered"
        
        return causal_graph
