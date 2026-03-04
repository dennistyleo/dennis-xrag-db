"""
圖卷積層 - 用於GNN的卷積操作
"""

import numpy as np
from typing import Optional, Tuple, Callable, Union

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️ PyTorch not available - using numpy fallback")

if TORCH_AVAILABLE:
    class PyTorchGeometricConvLayer(nn.Module):
        """
        PyTorch版本的幾何圖卷積層
        """
        
        def __init__(self, 
                     in_features: int,
                     out_features: int,
                     activation: str = 'relu',
                     use_bias: bool = True):
            super().__init__()
            self.in_features = in_features
            self.out_features = out_features
            self.activation = activation
            self.use_bias = use_bias
            
            self.linear = nn.Linear(in_features, out_features, bias=use_bias)
            
            if activation == 'relu':
                self.act = nn.ReLU()
            elif activation == 'tanh':
                self.act = nn.Tanh()
            elif activation == 'sigmoid':
                self.act = nn.Sigmoid()
            else:
                self.act = nn.Identity()
        
        def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
            """
            PyTorch前向傳播
            
            Args:
                x: 節點特徵 [n_nodes, in_features]
                adj: 鄰接矩陣 [n_nodes, n_nodes]
                
            Returns:
                更新後的節點特徵 [n_nodes, out_features]
            """
            # 線性變換
            support = self.linear(x)  # [n_nodes, out_features]
            
            # 圖卷積: A @ XW
            output = torch.mm(adj, support)  # [n_nodes, out_features]
            
            # 激活
            output = self.act(output)
            
            return output

class GeometricConvLayer:
    """
    幾何圖卷積層 - 通用接口，自動選擇PyTorch或NumPy實現
    """
    
    def __init__(self, 
                 in_features: int,
                 out_features: int,
                 activation: str = 'relu',
                 use_bias: bool = True):
        """
        初始化卷積層
        
        Args:
            in_features: 輸入特徵維度
            out_features: 輸出特徵維度
            activation: 激活函數
            use_bias: 是否使用偏置
        """
        self.in_features = in_features
        self.out_features = out_features
        self.activation = activation
        self.use_bias = use_bias
        
        if TORCH_AVAILABLE:
            self.impl = PyTorchGeometricConvLayer(in_features, out_features, activation, use_bias)
        else:
            self._init_numpy()
    
    def _init_numpy(self):
        """使用NumPy初始化（簡化版本）"""
        self.W = np.random.randn(self.in_features, self.out_features) * 0.01
        if self.use_bias:
            self.b = np.zeros(self.out_features)
    
    def forward_numpy(self, 
                     x: np.ndarray,
                     adj: np.ndarray) -> np.ndarray:
        """
        NumPy前向傳播
        
        Args:
            x: 節點特徵 [n_nodes, in_features]
            adj: 鄰接矩陣 [n_nodes, n_nodes]
            
        Returns:
            更新後的節點特徵 [n_nodes, out_features]
        """
        # 圖卷積: AXW
        support = x @ self.W  # [n_nodes, out_features]
        output = adj @ support  # [n_nodes, out_features]
        
        if self.use_bias:
            output = output + self.b
        
        # 激活函數
        if self.activation == 'relu':
            output = np.maximum(output, 0)
        elif self.activation == 'tanh':
            output = np.tanh(output)
        elif self.activation == 'sigmoid':
            output = 1 / (1 + np.exp(-output))
        
        return output
    
    def forward(self, x, adj):
        """統一的前向接口"""
        if TORCH_AVAILABLE and hasattr(x, 'dim'):  # 檢查是否為 torch.Tensor
            return self.impl(x, adj)
        else:
            return self.forward_numpy(x, adj)
    
    def __call__(self, x, adj):
        return self.forward(x, adj)


class ChebyshevConvLayer:
    """
    Chebyshev圖卷積層 (Defferard et al.) - NumPy版本
    """
    
    def __init__(self, 
                 in_features: int,
                 out_features: int,
                 K: int = 3,
                 activation: str = 'relu'):
        """
        初始化Chebyshev卷積層
        
        Args:
            in_features: 輸入特徵維度
            out_features: 輸出特徵維度
            K: Chebyshev多項式階數
            activation: 激活函數
        """
        self.in_features = in_features
        self.out_features = out_features
        self.K = K
        self.activation = activation
        
        # Chebyshev係數
        self.thetas = [np.random.randn(in_features, out_features) * 0.01 
                      for _ in range(K)]
    
    def _compute_chebyshev(self, 
                          x: np.ndarray,
                          L: np.ndarray) -> np.ndarray:
        """
        計算Chebyshev多項式
        
        Args:
            x: 節點特徵
            L: 標準化拉普拉斯矩陣
            
        Returns:
            Chebyshev卷積結果
        """
        # 初始化
        T_0 = x  # T_0(L) x
        T_1 = L @ x  # T_1(L) x = Lx
        
        # 卷積結果
        output = T_0 @ self.thetas[0] + T_1 @ self.thetas[1]
        
        # 高階項
        for k in range(2, self.K):
            T_k = 2 * L @ T_1 - T_0
            output += T_k @ self.thetas[k]
            T_0, T_1 = T_1, T_k
        
        return output
    
    def forward(self, x, L):
        """前向傳播"""
        output = self._compute_chebyshev(x, L)
        
        if self.activation == 'relu':
            output = np.maximum(output, 0)
        elif self.activation == 'tanh':
            output = np.tanh(output)
        
        return output
    
    def __call__(self, x, L):
        return self.forward(x, L)


__all__ = ['GeometricConvLayer', 'ChebyshevConvLayer']
