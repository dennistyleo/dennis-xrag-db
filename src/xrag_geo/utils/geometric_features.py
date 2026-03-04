"""
幾何特徵提取器 - 從數據中提取幾何特徵
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from scipy.spatial import ConvexHull, Delaunay
from scipy.spatial.distance import pdist, squareform
from sklearn.decomposition import PCA
import networkx as nx

class GeometricFeatureExtractor:
    """
    幾何特徵提取器 - 用於GNN的幾何特徵
    """
    
    def __init__(self):
        self.name = "XRAG-Geo-FeatureExtractor"
        self.version = "1.0.0"
    
    def extract_node_features(self, 
                             data: np.ndarray,
                             graph: nx.Graph) -> np.ndarray:
        """
        提取節點特徵
        
        Args:
            data: 原始數據
            graph: NetworkX圖對象
            
        Returns:
            節點特徵矩陣 (n_nodes, n_features)
        """
        n_nodes = len(graph.nodes)
        features = []
        
        for node in graph.nodes:
            node_features = []
            
            # 1. 節點自身的值
            if node < len(data):
                node_features.append(data[node])
            
            # 2. 度中心性
            node_features.append(graph.degree(node))
            
            # 3. 聚集係數
            try:
                clustering = nx.clustering(graph, node)
                node_features.append(clustering)
            except:
                node_features.append(0)
            
            # 4. 鄰居的平均值
            neighbors = list(graph.neighbors(node))
            if neighbors and node < len(data):
                neighbor_vals = [data[n] for n in neighbors if n < len(data)]
                if neighbor_vals:
                    node_features.append(np.mean(neighbor_vals))
                    node_features.append(np.std(neighbor_vals))
                else:
                    node_features.extend([0, 0])
            else:
                node_features.extend([0, 0])
            
            # 5. PageRank
            try:
                pagerank = nx.pagerank(graph)[node]
                node_features.append(pagerank)
            except:
                node_features.append(0)
            
            features.append(node_features)
        
        return np.array(features, dtype=np.float32)
    
    def extract_edge_features(self, 
                             graph: nx.Graph,
                             node_features: Optional[np.ndarray] = None) -> np.ndarray:
        """
        提取邊特徵
        
        Args:
            graph: NetworkX圖對象
            node_features: 節點特徵矩陣
            
        Returns:
            邊特徵矩陣 (n_edges, n_features)
        """
        edges = list(graph.edges(data=True))
        features = []
        
        for u, v, data in edges:
            edge_features = []
            
            # 1. 邊權重
            weight = data.get('weight', 1.0)
            edge_features.append(weight)
            
            # 2. 關係類型
            relation = data.get('relation', 'unknown')
            if relation == 'similar':
                edge_features.append(1.0)
            elif relation == 'temporal':
                edge_features.append(2.0)
            elif relation == 'belongs_to':
                edge_features.append(3.0)
            else:
                edge_features.append(0.0)
            
            # 3. 基於節點特徵的差異
            if node_features is not None and u < len(node_features) and v < len(node_features):
                diff = np.linalg.norm(node_features[u] - node_features[v])
                edge_features.append(diff)
            
            # 4. 共同鄰居數量
            common_neighbors = len(set(graph.neighbors(u)) & set(graph.neighbors(v)))
            edge_features.append(common_neighbors)
            
            features.append(edge_features)
        
        return np.array(features, dtype=np.float32)
    
    def extract_global_features(self, 
                               graph: nx.Graph,
                               data: np.ndarray) -> Dict[str, float]:
        """
        提取全局圖特徵
        
        Args:
            graph: NetworkX圖對象
            data: 原始數據
            
        Returns:
            全局特徵字典
        """
        features = {}
        
        # 圖統計
        features['n_nodes'] = len(graph.nodes)
        features['n_edges'] = len(graph.edges)
        features['density'] = nx.density(graph)
        
        # 連通性
        if nx.is_connected(graph) if not graph.is_directed() else nx.is_weakly_connected(graph):
            features['diameter'] = nx.diameter(graph.to_undirected())
            features['avg_shortest_path'] = nx.average_shortest_path_length(graph.to_undirected())
        else:
            features['diameter'] = -1
            features['avg_shortest_path'] = -1
        
        # 聚集係數
        features['avg_clustering'] = nx.average_clustering(graph)
        
        # 度分佈
        degrees = [d for n, d in graph.degree()]
        features['avg_degree'] = np.mean(degrees)
        features['max_degree'] = max(degrees)
        features['degree_std'] = np.std(degrees)
        
        # 基於數據的幾何特徵
        if len(data) > 0:
            # PCA
            if data.ndim == 1:
                data_2d = data.reshape(-1, 1)
            else:
                data_2d = data
            
            try:
                pca = PCA(n_components=min(2, data_2d.shape[1]))
                pca.fit(data_2d)
                features['pca_explained_var_ratio'] = pca.explained_variance_ratio_[0]
            except:
                pass
        
        return features
    
    def compute_curvature(self, 
                         points: np.ndarray,
                         graph: nx.Graph) -> np.ndarray:
        """
        計算圖的曲率 (Ollivier-Ricci curvature)
        
        Args:
            points: 節點坐標
            graph: NetworkX圖對象
            
        Returns:
            每條邊的曲率
        """
        from scipy.spatial.distance import cdist
        
        curvatures = []
        
        for u, v in graph.edges():
            # 獲取鄰居
            neighbors_u = set(graph.neighbors(u))
            neighbors_v = set(graph.neighbors(v))
            
            # 計算 Wasserstein 距離的近似
            if len(neighbors_u) > 0 and len(neighbors_v) > 0:
                # 獲取鄰居坐標
                coords_u = points[list(neighbors_u)] if len(neighbors_u) > 0 else points[u].reshape(1, -1)
                coords_v = points[list(neighbors_v)] if len(neighbors_v) > 0 else points[v].reshape(1, -1)
                
                # 計算質心
                centroid_u = np.mean(coords_u, axis=0)
                centroid_v = np.mean(coords_v, axis=0)
                
                # 計算距離
                dist_uv = np.linalg.norm(points[u] - points[v])
                dist_centroid = np.linalg.norm(centroid_u - centroid_v)
                
                # 近似曲率
                curvature = 1 - dist_centroid / (dist_uv + 1e-8)
            else:
                curvature = 0
            
            curvatures.append(curvature)
        
        return np.array(curvatures)
    
    def compute_spectral_features(self, graph: nx.Graph) -> Dict[str, Any]:
        """
        計算圖的譜特徵
        
        Args:
            graph: NetworkX圖對象
            
        Returns:
            譜特徵字典
        """
        features = {}
        
        try:
            # 拉普拉斯矩陣
            L = nx.laplacian_matrix(graph).toarray()
            
            # 特徵值
            eigenvalues = np.linalg.eigvalsh(L)
            eigenvalues = np.sort(eigenvalues)
            
            features['lambda_1'] = float(eigenvalues[0]) if len(eigenvalues) > 0 else 0
            features['lambda_2'] = float(eigenvalues[1]) if len(eigenvalues) > 1 else 0
            features['lambda_max'] = float(eigenvalues[-1]) if len(eigenvalues) > 0 else 0
            features['spectral_gap'] = float(eigenvalues[1] - eigenvalues[0]) if len(eigenvalues) > 1 else 0
            
            # 特徵熵
            if np.sum(eigenvalues) > 0:
                probs = eigenvalues / np.sum(eigenvalues)
                features['spectral_entropy'] = float(-np.sum(probs * np.log(probs + 1e-10)))
            else:
                features['spectral_entropy'] = 0
            
        except Exception as e:
            features['error'] = str(e)
        
        return features
