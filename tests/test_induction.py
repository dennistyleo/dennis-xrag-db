import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src.db_config import XRAGDatabase
from src.db_interface import XRAGInterface
from src.induction_engine import InductionEngine

def test_induction():
    print("🔍 測試自我歸納引擎...")
    
    db = XRAGDatabase('data/xrag_complete.db')
    interface = XRAGInterface(db)
    engine = InductionEngine(interface)
    
    # 測試數據 1：線性關係 y = 2x + 1
    x1 = np.linspace(0, 10, 20)
    y1 = 2 * x1 + 1 + np.random.normal(0, 0.5, 20)  # 加入一些噪聲
    
    data1 = {
        'x': x1.tolist(),
        'y': y1.tolist(),
        'var_names': ['x', 'y'],
        'description': '線性關係測試數據'
    }
    
    print("\n📈 測試線性數據:")
    results1 = engine.induce(data1)
    for r in results1:
        print(f"  - {r['method']}: {r['candidate']['form']}")
        print(f"    可信度: {r['confidence']:.3f}")
    
    # 測試數據 2：指數關係 y = 3·e^(0.5x)
    x2 = np.linspace(0, 5, 20)
    y2 = 3 * np.exp(0.5 * x2) + np.random.normal(0, 0.5, 20)
    
    data2 = {
        'x': x2.tolist(),
        'y': y2.tolist(),
        'var_names': ['x', 'y'],
        'description': '指數關係測試數據'
    }
    
    print("\n📈 測試指數數據:")
    results2 = engine.induce(data2)
    for r in results2:
        print(f"  - {r['method']}: {r['candidate']['form']}")
        print(f"    可信度: {r['confidence']:.3f}")

if __name__ == "__main__":
    test_induction()
