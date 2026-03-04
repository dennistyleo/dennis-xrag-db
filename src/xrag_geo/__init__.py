"""
XRAG Geo - Geometric AI Features for XRAG
圖神經網路(GNN)和幾何深度學習模塊
"""

from .models.gnn import XRAG_GNN, GraphAxiomGenerator
from .models.gnn_encoder import Signal2GraphEncoder
from .layers.graph_attention import GeometricAttentionLayer
from .layers.graph_conv import GeometricConvLayer
from .utils.graph_builder import GraphBuilder, ProximityGraph, KnowledgeGraph
from .utils.geometric_features import GeometricFeatureExtractor

__version__ = "1.0.0"
__all__ = [
    'XRAG_GNN',
    'GraphAxiomGenerator',
    'Signal2GraphEncoder',
    'GeometricAttentionLayer',
    'GeometricConvLayer',
    'GraphBuilder',
    'ProximityGraph',
    'KnowledgeGraph',
    'GeometricFeatureExtractor'
]
