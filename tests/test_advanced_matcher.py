import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db_config import XRAGDatabase
from src.db_interface import XRAGInterface
from src.matcher_advanced import AdvancedMatcher

def test_matcher():
    print("🔍 測試進階匹配器...")
    
    # 初始化
    db = XRAGDatabase('data/xrag_complete.db')
    interface = XRAGInterface(db)
    matcher = AdvancedMatcher(interface)
    
    # 測試候選公理 1：熱學
    candidate1 = {
        'domain': 'thermal',
        'computational_core': {'form': 'Q = k·A·ΔT/d'},
        'xr_variables': 'k,A,ΔT,d,Q'
    }
    
    print("\n🔥 測試熱學公理:")
    results1 = matcher.match(candidate1)
    print(f"找到 {len(results1)} 個匹配")
    for r in results1:
        print(f"  ✅ {r['name']}: 相似度 {r['score']}")
        if 'details' in r:
            print(f"     細節: {r['details']}")
    
    # 測試候選公理 2：電學
    candidate2 = {
        'domain': 'electrical',
        'computational_core': {'form': 'V = I·R'},
        'xr_variables': 'V,I,R'
    }
    
    print("\n⚡ 測試電學公理:")
    results2 = matcher.match(candidate2)
    print(f"找到 {len(results2)} 個匹配")
    for r in results2:
        print(f"  ✅ {r['name']}: 相似度 {r['score']}")
    
    # 測試候選公理 3：未知領域（應該進入未知通道）
    candidate3 = {
        'name': '未知量子公式',
        'domain': 'quantum',
        'computational_core': {'form': 'ψ = e^(i·k·x - ω·t)'},
        'xr_variables': 'ψ,k,x,ω,t'
    }
    
    print("\n⚛️ 測試未知公理:")
    results3 = matcher.match(candidate3, threshold=0.5)
    print(f"找到 {len(results3)} 個匹配")
    if not results3:
        print("  ⚠️ 無匹配（符合預期）")

if __name__ == "__main__":
    test_matcher()
