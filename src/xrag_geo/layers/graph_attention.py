"""
圖注意力層 - GAT (Graph Attention Networks)
"""

import numpy as np
from typing import Optional, Union

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️ PyTorch not available - using numpy fallback")

if TORCH_AVAILABLE:
    class PyTorchGeometricAttentionLayer(nn.Module):
        """
        PyTorch版本的幾何圖注意力層
        """
        
        def __init__(self, 
                     in_features: int,
                     out_features: int,
                     n_heads: int = 4,
                     concat: bool = True,
                     dropout: float = 0.1,
                     leaky_relu_slope: float = 0.2):
            super().__init__()
            self.in_features = in_features
            self.out_features = out_features
            self.n_heads = n_heads
            self.concat = concat
            self.dropout = dropout
            self.leaky_relu_slope = leaky_relu_slope
            
            self.W = nn.Parameter(torch.zeros(n_heads, in_features, out_features))
            self.a = nn.Parameter(torch.zeros(n_heads, 2 * out_features, 1))
            
            nn.init.xavier_uniform_(self.W)
            nn.init.xavier_uniform_(self.a)
            
            self.leaky_relu = nn.LeakyReLU(leaky_relu_slope)
            self.dropout_layer = nn.Dropout(dropout)
        
        def forward(self, 
                   x: torch.Tensor,
                   adj: torch.Tensor,
                   return_attention: bool = False):
            """
            PyTorch前向傳播
            
            Args:
                x: 節點特徵 [n_nodes, in_features]
                adj: 鄰接矩陣 [n_nodes, n_nodes]
                return_attention: 是否返回注意力權重
                
            Returns:
                更新後的節點特徵
            """
            n_nodes = x.shape[0]
            
            # 線性變換
            h = torch.matmul(x, self.W)  # [n_heads, n_nodes, out_features]
            
            # 準備注意力係數
            h_repeat_i = h.unsqueeze(2).repeat(1, 1, n_nodes, 1)  # [n_heads, n_nodes, n_nodes, out_features]
            h_repeat_j = h.unsqueeze(1).repeat(1, n_nodes, 1, 1)  # [n_heads, n_nodes, n_nodes, out_features]
            
            # 拼接特徵
            h_concat = torch.cat([h_repeat_i, h_repeat_j], dim=-1)  # [n_heads, n_nodes, n_nodes, 2*out_features]
            
            # 計算注意力分數
            e = torch.matmul(h_concat, self.a.unsqueeze(1))  # [n_heads, n_nodes, n_nodes, 1]
            e = e.squeeze(-1)  # [n_heads, n_nodes, n_nodes]
            
            # LeakyReLU
            e = self.leaky_relu(e)
            
            # 掩碼 - 只保留有邊的節點對
            attention_mask = adj.unsqueeze(0).repeat(self.n_heads, 1, 1)  # [n_heads, n_nodes, n_nodes]
            e = e.masked_fill(attention_mask == 0, float('-inf'))
            
            # Softmax
            attention = F.softmax(e, dim=-1)
            attention = self.dropout_layer(attention)
            
            # 應用注意力
            h_prime = torch.matmul(attention, h)  # [n_heads, n_nodes, out_features]
            
            if self.concat:
                # 拼接多頭
                output = h_prime.permute(1, 0, 2).reshape(n_nodes, -1)  # [n_nodes, n_heads * out_features]
            else:
                # 平均多頭
                output = h_prime.mean(dim=0)  # [n_nodes, out_features]
            
            if return_attention:
                return output, attention
            return output

class GeometricAttentionLayer:
    """
    幾何圖注意力層 - 通用接口，自動選擇PyTorch或NumPy實現
    """
    
    def __init__(self, 
                 in_features: int,
                 out_features: int,
                 n_heads: int = 4,
                 concat: bool = True,
                 dropout: float = 0.1,
                 leaky_relu_slope: float = 0.2):
        """
        初始化注意力層
        
        Args:
            in_features: 輸入特徵維度
            out_features: 輸出特徵維度
            n_heads: 注意力頭數
            concat: 是否拼接多頭輸出
            dropout: Dropout概率
            leaky_relu_slope: LeakyReLU斜率
        """
        self.in_features = in_features
        self.out_features = out_features
        self.n_heads = n_heads
        self.concat = concat
        self.dropout = dropout
        self.leaky_relu_slope = leaky_relu_slope
        
        if TORCH_AVAILABLE:
            self.impl = PyTorchGeometricAttentionLayer(
                in_features, out_features, n_heads, concat, dropout, leaky_relu_slope
            )
        else:
            self._init_numpy()
    
    def _init_numpy(self):
        """NumPy初始化"""
        self.W = np.random.randn(self.n_heads, self.in_features, self.out_features) * 0.01
        self.a = np.random.randn(self.n_heads, 2 * self.out_features, 1) * 0.01
    
    def forward_numpy(self, 
                     x: np.ndarray,
                     adj: np.ndarray,
                     return_attention: bool = False):
        """
        NumPy前向傳播（簡化版本）
        
        Args:
            x: 節點特徵 [n_nodes, in_features]
            adj: 鄰接矩陣 [n_nodes, n_nodes]
            return_attention: 是否返回注意力權重
            
        Returns:
            更新後的節點特徵
        """
        n_nodes = x.shape[0]
        
        # 線性變換
        h = np.einsum('ni,hid->hnd', x, self.W)  # [n_heads, n_nodes, out_features]
        
        # 簡化的注意力機制
        attention = np.zeros((self.n_heads, n_nodes, n_nodes))
        
        for head in range(self.n_heads):
            h_head = h[head]  # [n_nodes, out_features]
            
            # 計算相似度
            for i in range(n_nodes):
                for j in range(n_nodes):
                    if adj[i, j] > 0:
                        # 簡單的點積注意力
                        sim = np.dot(h_head[i], h_head[j])
                        attention[head, i, j] = sim
            
            # Softmax
            row_sums = np.sum(attention[head], axis=1, keepdims=True) + 1e-8
            attention[head] = attention[head] / row_sums
        
        # 應用注意力
        h_prime = np.einsum('hij,hjd->hid', attention, h)  # [n_heads, n_nodes, out_features]
        
        if self.concat:
            # 拼接多頭
            output = h_prime.transpose(1, 0, 2).reshape(n_nodes, -1)
        else:
            # 平均多頭
            output = np.mean(h_prime, axis=0)
        
        if return_attention:
            return output, attention
        return output
    
    def forward(self, x, adj, return_attention=False):
        """統一的前向接口"""
        if TORCH_AVAILABLE and hasattr(x, 'dim'):
            return self.impl.forward(x, adj, return_attention)
        else:
            return self.forward_numpy(x, adj, return_attention)
    
    def __call__(self, x, adj, return_attention=False):
        return self.forward(x, adj, return_attention)


__all__ = ['GeometricAttentionLayer']
