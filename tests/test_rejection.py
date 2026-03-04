import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db_config import XRAGDatabase
from src.db_interface import XRAGInterface
from src.matcher_advanced import AdvancedMatcher
from src.rejection_handler import RejectionHandler

def test_rejection():
    print("🔍 測試被拒處理器...")
    
    db = XRAGDatabase('data/xrag_complete.db')
    interface = XRAGInterface(db)
    matcher = AdvancedMatcher(interface)
    handler = RejectionHandler(interface, matcher)
    
    # 測試應該會被拒的公理
    candidate = {
        'name': '未知量子公式',
        'domain': 'quantum',
        'computational_core': {'form': 'ψ = e^(i·k·x - ω·t)'},
        'xr_variables': 'ψ,k,x,ω,t'
    }
    
    # 先正常匹配
    matches = matcher.match(candidate)
    print(f"\n⚛️ 正常匹配: {len(matches)} 個")
    
    # 被拒處理
    result = handler.handle(candidate, matches)
    print(f"\n🔄 被拒處理結果:")
    print(f"  策略嘗試: {len(result['search_path'])} 個")
    for path in result['search_path']:
        print(f"    - {path['strategy']}: 找到 {path['matches']} 個")
    
    if result['final_match']:
        print(f"\n✅ 最終匹配: {result['final_match']['name']} (相似度 {result['final_match']['score']})")
        print(f"   使用策略: {result['strategy_used']}")
    else:
        print(f"\n⚠️ {result['message']}")
        if result.get('unknown_id'):
            print(f"   未知通道 ID: {result['unknown_id']}")

if __name__ == "__main__":
    test_rejection()
