import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src.db_config import XRAGDatabase
from src.db_interface import XRAGInterface
from src.matcher_advanced import AdvancedMatcher
from src.rejection_handler import RejectionHandler
from src.induction_engine import InductionEngine
from src.xrag_pipeline import XRAGPipeline
import json

def test_pipeline():
    print("🔍 測試完整 XRAG 推理管線...")
    
    # 初始化所有元件
    db = XRAGDatabase('data/xrag_complete.db')
    interface = XRAGInterface(db)
    matcher = AdvancedMatcher(interface)
    rejection = RejectionHandler(interface, matcher)
    induction = InductionEngine(interface)
    pipeline = XRAGPipeline(interface, matcher, rejection, induction)
    
    # 測試案例 1：直接匹配
    print("\n📌 案例 1：直接匹配")
    input1 = {
        'type': 'axiom',
        'candidate': {
            'name': '測試熱學公理',
            'domain': 'thermal',
            'computational_core': {'form': 'Q = k·A·ΔT/d'},
            'xr_variables': 'k,A,ΔT,d,Q'
        }
    }
    result1 = pipeline.process(input1)
    print(f"  結果類型: {result1['final_result']['type']}")
    print(f"  建議: {result1.get('recommendation', '')}")
    
    # 測試案例 2：需要被拒處理
    print("\n📌 案例 2：需要被拒處理")
    input2 = {
        'type': 'axiom',
        'candidate': {
            'name': '未知量子公式',
            'domain': 'quantum',
            'computational_core': {'form': 'ψ = e^(i·k·x - ω·t)'},
            'xr_variables': 'ψ,k,x,ω,t'
        }
    }
    result2 = pipeline.process(input2)
    print(f"  結果類型: {result2['final_result']['type']}")
    if result2['final_result']['type'] == 'unknown':
        print(f"  未知通道 ID: {result2['final_result']['unknown_id']}")
    
    # 測試案例 3：從數據歸納
    print("\n📌 案例 3：從數據歸納")
    x = np.linspace(0, 10, 50)
    y = 2.5 * x + 3.0 + np.random.normal(0, 0.5, 50)
    
    input3 = {
        'type': 'data',
        'data': {
            'x': x.tolist(),
            'y': y.tolist(),
            'var_names': ['x', 'y']
        },
        'context': {'domain': 'test'}
    }
    result3 = pipeline.process(input3)
    print(f"  結果類型: {result3['final_result']['type']}")
    if result3['final_result']['type'] == 'induced':
        print(f"  發現公式: {result3['final_result']['candidate']['form']}")
        print(f"  可信度: {result3['final_result']['confidence']:.3f}")
    
    # 輸出完整結果
    print("\n📊 完整結果:")
    print(json.dumps(result1, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_pipeline()
