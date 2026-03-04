#!/usr/bin/env python3
"""
XRAG Geo 模塊測試 - 修復版本
"""

import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.xrag_geo import (
    XRAG_GNN, GraphAxiomGenerator,
    Signal2GraphEncoder, GraphBuilder,
    GeometricFeatureExtractor
)
from src.xrag_core import XRAGEngine

def example_1_basic_gnn():
    """示例1: 基本GNN分析"""
    print("\n" + "="*60)
    print("示例1: 基本GNN分析")
    print("="*60)
    
    # 創建GNN
    gnn = XRAG_GNN(node_features=32)
    
    # 生成信號
    t = np.linspace(0, 10, 300)
    signal = 10 * np.exp(-0.5 * t) + 0.1 * np.random.randn(300)
    
    # 分析
    axiom = gnn.analyze_signal(signal, t)
    
    print(f"📊 信號: 指數衰減")
    print(f"📈 圖公理: {axiom.name}")
    print(f"   節點數: {axiom.node_features}")
    print(f"   全局特徵: {axiom.global_features}")
    print(f"   預測: {axiom.prediction}")
    print(f"   置信度: {axiom.confidence:.4f}")

def example_2_different_signals():
    """示例2: 比較不同信號的圖結構"""
    print("\n" + "="*60)
    print("示例2: 比較不同信號的圖結構")
    print("="*60)
    
    encoder = Signal2GraphEncoder()
    t = np.linspace(0, 10, 300)
    
    signals = {
        '指數衰減': 10 * np.exp(-0.5 * t),
        '正弦波': 5 * np.sin(2 * np.pi * 2 * t),
        '線性': 2 * t + 10,
        '隨機噪聲': np.random.randn(300)
    }
    
    for name, signal in signals.items():
        # 編碼為圖
        graph = encoder.encode_time_series(signal, t, method='adaptive')
        
        # 圖統計
        print(f"\n📊 {name}:")
        print(f"   節點數: {len(graph.nodes)}")
        print(f"   邊數: {len(graph.edges)}")
        print(f"   圖密度: {nx.density(graph.graph):.4f}")
        print(f"   平均聚集係數: {nx.average_clustering(graph.graph):.4f}")

def example_3_integration_with_xrag():
    """示例3: 與XRAG核心集成"""
    print("\n" + "="*60)
    print("示例3: 與XRAG核心集成")
    print("="*60)
    
    # 初始化
    gnn = XRAG_GNN()
    xrag = XRAGEngine(verbose=False)
    
    # 測試不同信號
    t = np.linspace(0, 10, 300)
    
    test_cases = [
        ('指數衰減', 10 * np.exp(-0.5 * t) + 0.1 * np.random.randn(300)),
        ('正弦波', 5 * np.sin(2 * np.pi * 2 * t) + 0.2 * np.random.randn(300)),
        ('線性', 2 * t + 10 + np.random.randn(300))
    ]
    
    for name, signal in test_cases:
        print(f"\n📈 測試: {name}")
        
        # 集成分析
        result = gnn.integrate_with_xrag(xrag, signal, t)
        
        print(f"   XRAG: {result['xrag']['best_model']} (R²={result['xrag']['r2']:.3f})")
        print(f"   GNN置信度: {result['gnn']['confidence']:.3f}")
        print(f"   組合分數: {result['integration']['combined_score']:.3f}")

def example_4_visualize_graph():
    """示例4: 可視化圖結構"""
    print("\n" + "="*60)
    print("示例4: 可視化圖結構")
    print("="*60)
    
    try:
        import matplotlib.pyplot as plt
        
        encoder = Signal2GraphEncoder()
        t = np.linspace(0, 10, 50)  # 減少點數以便可視化
        signal = 10 * np.exp(-0.5 * t)
        
        # 編碼為圖
        graph = encoder.encode_time_series(signal, t, method='knn')
        
        # 繪製
        plt.figure(figsize=(12, 4))
        
        # 原始信號
        plt.subplot(1, 3, 1)
        plt.plot(t, signal, 'b-')
        plt.title('原始信號')
        plt.xlabel('時間')
        plt.ylabel('幅度')
        
        # 圖結構
        plt.subplot(1, 3, 2)
        pos = nx.spring_layout(graph.graph)
        nx.draw(graph.graph, pos, node_color='lightblue', 
                node_size=100, with_labels=False, alpha=0.7)
        plt.title(f'圖結構 ({len(graph.nodes)}節點)')
        
        # 鄰接矩陣
        plt.subplot(1, 3, 3)
        plt.imshow(graph.adjacency_matrix, cmap='viridis', aspect='auto')
        plt.colorbar(label='權重')
        plt.title('鄰接矩陣')
        
        plt.tight_layout()
        plt.savefig('gnn_graph_visualization.png', dpi=150)
        print("   ✓ 圖表已保存: gnn_graph_visualization.png")
        
    except Exception as e:
        print(f"   ⚠️ 無法繪製圖表: {e}")

def test_graph_builder():
    """測試圖構建器"""
    print("\n📊 測試 GraphBuilder...")
    
    builder = GraphBuilder()
    
    # 生成測試數據
    data = np.random.randn(100, 3)
    
    # 構建KNN圖
    graph = builder.build_proximity_graph(data, method='knn', k=5)
    
    print(f"   ✓ KNN圖: {len(graph.nodes)}節點, {len(graph.edges)}邊")
    print(f"     密度: {nx.density(graph.graph):.4f}")
    
    # 構建時序圖
    time_series = np.random.randn(200)
    temporal_graph = builder.build_temporal_graph(time_series, window_size=10)
    
    print(f"   ✓ 時序圖: {len(temporal_graph.nodes)}窗口")
    
    return True

def test_feature_extractor():
    """測試特徵提取器"""
    print("\n🔍 測試 GeometricFeatureExtractor...")
    
    extractor = GeometricFeatureExtractor()
    builder = GraphBuilder()
    
    # 創建圖
    data = np.random.randn(50, 2)
    graph = builder.build_proximity_graph(data, method='fully_connected')
    
    # 提取節點特徵
    node_features = extractor.extract_node_features(data[:, 0], graph.graph)
    print(f"   ✓ 節點特徵: {node_features.shape}")
    
    # 提取邊特徵
    edge_features = extractor.extract_edge_features(graph.graph, node_features)
    print(f"   ✓ 邊特徵: {edge_features.shape if edge_features.size > 0 else '空'}")
    
    # 提取全局特徵
    global_features = extractor.extract_global_features(graph.graph, data[:, 0])
    print(f"   ✓ 全局特徵: {len(global_features)}項")
    
    return True

def test_gnn():
    """測試GNN模型"""
    print("\n🧠 測試 XRAG_GNN...")
    
    gnn = XRAG_GNN(node_features=32, hidden_dim=64, n_layers=2)
    
    # 生成測試信號
    t = np.linspace(0, 10, 200)
    signal = 10 * np.exp(-0.5 * t) + 0.1 * np.random.randn(200)
    
    # 分析信號
    axiom = gnn.analyze_signal(signal, t)
    
    print(f"   ✓ 生成公理: {axiom.name}")
    print(f"     置信度: {axiom.confidence:.4f}")
    print(f"     預測: {axiom.prediction}")
    
    return True

def test_integration_with_xrag():
    """測試與XRAG核心的集成"""
    print("\n🔄 測試與XRAG集成...")
    
    # 初始化
    gnn = XRAG_GNN()
    xrag = XRAGEngine(verbose=False)
    
    # 生成測試信號
    t = np.linspace(0, 10, 300)
    signal = 10 * np.exp(-0.5 * t) + 0.1 * np.random.randn(300)
    
    # 集成分析
    result = gnn.integrate_with_xrag(xrag, signal, t)
    
    print(f"   ✓ XRAG結果: {result['xrag']['best_model']} (R²={result['xrag']['r2']:.3f})")
    print(f"   ✓ GNN置信度: {result['gnn']['confidence']:.3f}")
    print(f"   ✓ 組合分數: {result['integration']['combined_score']:.3f}")
    
    return True

def test_encoder():
    """測試信號編碼器"""
    print("\n📈 測試 Signal2GraphEncoder...")
    
    encoder = Signal2GraphEncoder(embedding_dim=16)
    
    # 生成測試信號
    t = np.linspace(0, 10, 200)
    signal = np.sin(2 * np.pi * 2 * t) + 0.1 * np.random.randn(200)
    
    # 編碼
    graph = encoder.encode_time_series(signal, t, method='adaptive')
    
    # 獲取嵌入
    embeddings = encoder.get_node_embeddings(graph, use_torch=False)
    
    print(f"   ✓ 圖結構: {len(graph.nodes)}節點, {len(graph.edges)}邊")
    print(f"   ✓ 嵌入維度: {embeddings.shape}")
    
    return True

def main():
    """主函數"""
    print("="*70)
    print("🚀 XRAG Geo 模塊測試")
    print("="*70)
    
    # 檢查依賴
    try:
        import networkx as nx
        print("✅ networkx 已安裝")
    except ImportError:
        print("❌ 請安裝 networkx: pip install networkx")
        return
    
    # 運行示例
    example_1_basic_gnn()
    example_2_different_signals()
    example_3_integration_with_xrag()
    example_4_visualize_graph()
    
    # 運行測試
    tests = [
        test_graph_builder,
        test_feature_extractor,
        test_encoder,
        test_gnn,
        test_integration_with_xrag
    ]
    
    print("\n" + "="*70)
    print("🔬 運行單元測試")
    print("="*70)
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ❌ 失敗: {e}")
    
    print("\n" + "="*70)
    print(f"✅ 測試完成: {passed}/{len(tests)} 通過")
    print("="*70)

if __name__ == "__main__":
    # 導入 networkx
    import networkx as nx
    main()
