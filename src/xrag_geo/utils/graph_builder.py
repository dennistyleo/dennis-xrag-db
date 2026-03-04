"""
圖構建器 - 將信號轉換為圖結構
"""

import numpy as np
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from scipy.spatial import distance_matrix
from sklearn.neighbors import kneighbors_graph
from sklearn.metrics.pairwise import rbf_kernel

@dataclass
class ProximityGraph:
    """鄰近圖結構"""
    nodes: List[int]
    edges: List[Tuple[int, int, float]]  # (source, target, weight)
    node_features: np.ndarray
    edge_features: np.ndarray
    adjacency_matrix: np.ndarray
    graph: nx.Graph
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            'n_nodes': len(self.nodes),
            'n_edges': len(self.edges),
            'node_features_shape': self.node_features.shape,
            'edge_features_shape': self.edge_features.shape,
            'graph_density': nx.density(self.graph)
        }

@dataclass
class KnowledgeGraph:
    """知識圖 - 包含公式之間的關係"""
    formula_nodes: List[str]  # 公式名稱
    formula_families: List[str]  # 公式家族
    similarity_edges: List[Tuple[str, str, float]]  # 相似性邊
    hierarchical_edges: List[Tuple[str, str, str]]  # 層級關係 (parent, child, relation)
    graph: nx.DiGraph  # 有向圖
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            'n_formulas': len(self.formula_nodes),
            'n_families': len(set(self.formula_families)),
            'n_similarity_edges': len(self.similarity_edges),
            'n_hierarchical_edges': len(self.hierarchical_edges)
        }

class GraphBuilder:
    """
    圖構建器 - 將各種數據轉換為圖結構
    """
    
    def __init__(self):
        self.name = "XRAG-Geo-Builder"
        self.version = "1.0.0"
    
    def build_proximity_graph(self, 
                             data: np.ndarray,
                             method: str = 'knn',
                             k: int = 5,
                             threshold: float = 0.5,
                             metric: str = 'euclidean') -> ProximityGraph:
        """
        從數據構建鄰近圖
        
        Args:
            data: 輸入數據 (n_samples, n_features)
            method: 'knn', 'radius', 'fully_connected', 'adaptive'
            k: KNN的鄰居數
            threshold: 半徑閾值
            metric: 距離度量
        
        Returns:
            ProximityGraph 對象
        """
        n_samples = data.shape[0]
        
        # 確保k不超過樣本數
        if k >= n_samples:
            k = max(1, n_samples - 1)
            print(f"   Warning: Reduced k to {k} (n_samples={n_samples})")
        
        # 構建鄰接矩陣
        if method == 'knn':
            if n_samples <= k + 1:
                # 樣本太少，使用全連接
                adjacency = np.ones((n_samples, n_samples)) - np.eye(n_samples)
            else:
                adjacency = kneighbors_graph(data, k, mode='distance', metric=metric)
                adjacency = adjacency.toarray()
                # 轉換距離為相似度
                adjacency = 1.0 / (1.0 + adjacency)
                adjacency[adjacency < 0.1] = 0
            
        elif method == 'radius':
            dist_matrix = distance_matrix(data, data)
            adjacency = (dist_matrix < threshold).astype(float)
            np.fill_diagonal(adjacency, 0)
            
        elif method == 'fully_connected':
            # 使用RBF核
            adjacency = rbf_kernel(data, data)
            np.fill_diagonal(adjacency, 0)
            
        elif method == 'adaptive':
            if n_samples <= 3:
                # 樣本太少，使用全連接
                adjacency = np.ones((n_samples, n_samples)) - np.eye(n_samples)
            else:
                # 自適應KNN - 根據局部密度調整K
                dist_matrix = distance_matrix(data, data)
                # 估計局部密度
                local_density = 1.0 / (np.mean(np.sort(dist_matrix, axis=1)[:, 1:min(6, n_samples)], axis=1) + 1e-8)
                # 根據密度調整K，但確保不超過樣本數
                adaptive_k = np.maximum(2, np.minimum(k, (local_density / np.mean(local_density) * k).astype(int)))
                adaptive_k = np.minimum(adaptive_k, n_samples - 1)  # 確保不超過樣本數
                
                adjacency = np.zeros((n_samples, n_samples))
                for i in range(n_samples):
                    k_i = adaptive_k[i]
                    if k_i >= n_samples:
                        k_i = n_samples - 1
                    if k_i > 0:
                        neighbors = np.argsort(dist_matrix[i])[1:k_i+1]
                        for j in neighbors:
                            # 高斯核權重
                            sigma = np.std(dist_matrix[i, neighbors]) + 1e-8
                            weight = np.exp(-dist_matrix[i, j]**2 / (2 * sigma**2))
                            adjacency[i, j] = weight
        else:
            raise ValueError(f"未知方法: {method}")
        
        # 創建 NetworkX 圖
        G = nx.Graph()
        G.add_nodes_from(range(n_samples))
        
        edges = []
        edge_features = []
        
        for i in range(n_samples):
            for j in range(i+1, n_samples):
                if adjacency[i, j] > 0:
                    G.add_edge(i, j, weight=adjacency[i, j])
                    edges.append((i, j, adjacency[i, j]))
                    edge_features.append([adjacency[i, j]])
        
        edge_features = np.array(edge_features) if edge_features else np.array([])
        
        return ProximityGraph(
            nodes=list(range(n_samples)),
            edges=edges,
            node_features=data,
            edge_features=edge_features,
            adjacency_matrix=adjacency,
            graph=G
        )
    
    def build_knowledge_graph(self, hypotheses: List) -> KnowledgeGraph:
        """
        從假設列表構建知識圖
        
        Args:
            hypotheses: Hypothesis對象列表
            
        Returns:
            KnowledgeGraph 對象
        """
        G = nx.DiGraph()
        
        formula_nodes = []
        formula_families = []
        similarity_edges = []
        hierarchical_edges = []
        
        # 添加公式節點
        for h in hypotheses:
            G.add_node(h.name, 
                      family=h.family.value if hasattr(h.family, 'value') else str(h.family),
                      complexity=h.complexity,
                      formulation=h.formulation)
            formula_nodes.append(h.name)
            formula_families.append(h.family.value if hasattr(h.family, 'value') else str(h.family))
        
        # 構建家族層級結構
        families = {}
        for h in hypotheses:
            family = h.family.value if hasattr(h.family, 'value') else str(h.family)
            if family not in families:
                families[family] = []
            families[family].append(h.name)
        
        # 添加家族節點和邊
        for family, members in families.items():
            G.add_node(f"family_{family}", type='family', name=family)
            for member in members:
                G.add_edge(f"family_{family}", member, relation='belongs_to')
                hierarchical_edges.append((f"family_{family}", member, 'belongs_to'))
        
        # 構建相似性邊 (基於複雜度、參數數量等)
        for i, h1 in enumerate(hypotheses):
            for j, h2 in enumerate(hypotheses[i+1:], i+1):
                # 計算相似性分數
                similarity = 0
                
                # 相同家族
                if h1.family == h2.family:
                    similarity += 0.3
                
                # 複雜度相似
                complexity_diff = 1.0 - abs(h1.complexity - h2.complexity) / 10.0
                similarity += 0.2 * complexity_diff
                
                # 參數數量相似
                n_params1 = len(h1.parameter_names)
                n_params2 = len(h2.parameter_names)
                param_sim = 1.0 - abs(n_params1 - n_params2) / max(n_params1, n_params2, 1)
                similarity += 0.2 * param_sim
                
                # 共同標籤
                if hasattr(h1, 'tags') and hasattr(h2, 'tags'):
                    common_tags = len(set(h1.tags) & set(h2.tags))
                    if common_tags > 0:
                        similarity += 0.3 * common_tags / max(len(h1.tags), len(h2.tags), 1)
                
                if similarity > 0.3:
                    G.add_edge(h1.name, h2.name, weight=similarity, relation='similar')
                    similarity_edges.append((h1.name, h2.name, similarity))
        
        return KnowledgeGraph(
            formula_nodes=formula_nodes,
            formula_families=formula_families,
            similarity_edges=similarity_edges,
            hierarchical_edges=hierarchical_edges,
            graph=G
        )
    
    def build_temporal_graph(self, 
                           time_series: np.ndarray,
                           window_size: int = 10,
                           stride: int = 1) -> ProximityGraph:
        """
        從時間序列構建時序圖
        
        Args:
            time_series: 時間序列數據 (n_timesteps, n_features)
            window_size: 滑動窗口大小
            stride: 步長
            
        Returns:
            ProximityGraph 對象
        """
        n_timesteps = len(time_series)
        n_windows = (n_timesteps - window_size) // stride + 1
        
        # 創建窗口特徵
        windows = []
        for i in range(0, n_timesteps - window_size + 1, stride):
            windows.append(time_series[i:i+window_size].flatten())
        
        windows = np.array(windows)
        
        # 構建時間鄰近圖
        G = nx.DiGraph()
        
        for i in range(n_windows):
            G.add_node(i, window_start=i*stride, window_end=i*stride+window_size)
            
            # 連接前後的窗口
            if i > 0:
                G.add_edge(i-1, i, relation='temporal', weight=1.0)
        
        # 構建鄰接矩陣
        adjacency = np.zeros((n_windows, n_windows))
        for i in range(n_windows):
            if i > 0:
                adjacency[i-1, i] = 1.0
        
        return ProximityGraph(
            nodes=list(range(n_windows)),
            edges=[(i-1, i, 1.0) for i in range(1, n_windows)],
            node_features=windows,
            edge_features=np.array([[1.0] for _ in range(1, n_windows)]),
            adjacency_matrix=adjacency,
            graph=G
        )
