"""
XR-BUS 完整實現測試
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from src.xrbus import (
    XRBUS, XRModule, XRFrame, ModuleID, OpCode,
    BoundaryContract, BoundaryType
)
from src.db_config import XRAGDatabase
from src.db_interface import XRAGInterface
from src.xrag_xrbus import XRAGBusModule

class MonitorModule(XRModule):
    """監控模組（用於測試）"""
    
    def __init__(self, bus):
        super().__init__(ModuleID.UNKNOWN, bus)
        self.received_frames = []
    
    def receive(self, frame: XRFrame):
        self.received_frames.append(frame)
        print(f"📡 Monitor received: {frame.op_code} from {frame.module_id.value}")

def test_xrbus_implementation():
    print("🚀 測試 XR-BUS 完整實現...")
    
    # 1. 初始化 XR-BUS
    bus = XRBUS("test-bus-1")
    
    # 2. 註冊邊界
    boundary = BoundaryContract(
        boundary_id="test-boundary",
        boundary_type=BoundaryType.DOMAIN,
        owner="test",
        governance_policies=["audit", "trace"],
        allowed_modules=[ModuleID.XRAG, ModuleID.XRAD]
    )
    bus.register_boundary(boundary)
    
    # 3. 初始化資料庫
    db = XRAGDatabase('data/xrag_complete.db')
    interface = XRAGInterface(db)
    
    # 4. 註冊 XRAG 模組
    xrag = XRAGBusModule(bus, interface)
    
    # 5. 註冊監控模組
    monitor = MonitorModule(bus)
    
    # 6. 添加監聽器
    def frame_listener(frame, dest):
        print(f"  🔍 Frame: {frame.module_id.value} -> {dest.value} | trace: {frame.trace_id[:8]}")
    bus.add_listener(frame_listener)
    
    # 7. 測試發送幀
    print("\n📨 測試 1: 發送公理查詢幀")
    frame1 = XRFrame(
        module_id=ModuleID.XRAD,
        boundary_id="test-boundary",
        op_code=OpCode.AXIOM_QUERY,
        payload={"domain": "thermal"}
    )
    bus.send(frame1, ModuleID.XRAG)
    
    time.sleep(0.1)
    
    # 8. 測試匹配請求
    print("\n📨 測試 2: 發送匹配請求幀")
    frame2 = XRFrame(
        module_id=ModuleID.XENOS,
        boundary_id="test-boundary",
        op_code=OpCode.AXIOM_MATCH,
        payload={
            "candidate": {
                "domain": "thermal",
                "computational_core": {"form": "Q = k·A·ΔT/d"}
            }
        }
    )
    bus.send(frame2, ModuleID.XRAG)
    
    time.sleep(0.1)
    
    # 9. 查看因果鏈
    print(f"\n🔗 因果鏈數量: {len(bus.causal_chains)}")
    for trace_id, chain in list(bus.causal_chains.items())[:2]:
        print(f"  Trace {trace_id[:8]}: {len(chain)} frames")
    
    # 10. 查看統計
    print(f"\n📊 XR-BUS 統計:")
    stats = bus.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    test_xrbus_implementation()
