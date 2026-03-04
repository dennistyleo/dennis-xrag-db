"""
XRAG-UPASL 完整整合測試
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import time
import json
import numpy as np
from datetime import datetime

from src.xrbus import XRBUS, ModuleID, XRModule, XRFrame
from src.db_config import XRAGDatabase
from src.db_interface import XRAGInterface
from xrag_upasl_integration import XRAGUPASLModule
from upasl_interface.upasl_receiver import UPASLRuntimeCore

class UPASLXRModule(XRModule):
    """UPASL 的 XR-BUS 模組包裝"""
    
    def __init__(self, bus, upasl_core):
        super().__init__(ModuleID.UNKNOWN, bus)
        self.upasl = upasl_core
    
    def receive(self, frame: XRFrame):
        """處理收到的幀"""
        if frame.payload.get('action') == 'deploy_freeze_package':
            package = frame.payload.get('package', {})
            result = self.upasl.receive_freeze_package(json.dumps(package))
            
            # 回應
            response = XRFrame(
                module_id=self.module_id,
                boundary_id=frame.boundary_id,
                op_code=frame.op_code,
                trace_id=frame.trace_id,
                parent_id=frame.checksum,
                payload={
                    'status': result['status'],
                    'package_id': package.get('model_id'),
                    'message': result.get('message', '')
                }
            )
            self.send(response, frame.module_id)

def test_complete_integration():
    """完整整合測試"""
    print("=" * 60)
    print("🔄 XRAG-UPASL 完整整合測試")
    print("=" * 60)
    
    # 1. 初始化 XR-BUS
    bus = XRBUS("xrbus-main")
    print("\n✅ XR-BUS 初始化完成")
    
    # 2. 初始化 XRAG 端
    db = XRAGDatabase('data/xrag_complete.db')
    interface = XRAGInterface(db)
    xrag = XRAGUPASLModule(bus, interface)
    
    # 3. 初始化 UPASL 端
    upasl_core = UPASLRuntimeCore("UPASL-Test")
    upasl = UPASLXRModule(bus, upasl_core)
    
    # 4. 測試數據 1：線性數據
    print("\n" + "-" * 40)
    print("📊 測試案例 1：線性關係數據")
    print("-" * 40)
    
    x1 = np.linspace(0, 10, 50)
    y1 = 2.5 * x1 + 1.0 + np.random.normal(0, 0.2, 50)
    
    data1 = {
        'x': x1.tolist(),
        'y': y1.tolist(),
        'snr': 25
    }
    
    context1 = {
        'domain': 'thermal',
        'application': 'temperature_sensor'
    }
    
    # 生成凍結包
    package1 = xrag.generate_freeze_package(
        data=data1,
        context=context1,
        human_reviewer="Dr. Alex Struver"
    )
    
    # 發送給 UPASL
    xrag.send_to_upasl(package1.model_id)
    time.sleep(0.5)
    
    # 5. 測試數據 2：指數數據
    print("\n" + "-" * 40)
    print("📊 測試案例 2：指數關係數據")
    print("-" * 40)
    
    x2 = np.linspace(0, 5, 40)
    y2 = 3.0 * np.exp(0.5 * x2) + np.random.normal(0, 0.1, 40)
    
    data2 = {
        'x': x2.tolist(),
        'y': y2.tolist(),
        'snr': 30
    }
    
    context2 = {
        'domain': 'radioactive_decay',
        'application': 'particle_counter'
    }
    
    # 生成凍結包
    package2 = xrag.generate_freeze_package(
        data=data2,
        context=context2,
        human_reviewer="Dr. Elena Chen"
    )
    
    # 發送給 UPASL
    xrag.send_to_upasl(package2.model_id)
    time.sleep(0.5)
    
    # 6. 查看部署歷史
    print("\n" + "-" * 40)
    print("📋 部署歷史")
    print("-" * 40)
    
    for i, dep in enumerate(xrag.deployment_history):
        package_id = dep.get('package_id', 'unknown')
        status = dep.get('status', 'unknown')
        timestamp = dep.get('received_at', dep.get('sent_at', 'unknown'))
        print(f"  {i+1}. {package_id}: {status} @ {timestamp[:19] if timestamp != 'unknown' else timestamp}")
    
    # 7. XR-BUS 統計
    print("\n" + "-" * 40)
    print("📊 XR-BUS 統計")
    print("-" * 40)
    
    stats = bus.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    # 8. UPASL 狀態
    print("\n" + "-" * 40)
    print("🛡️ UPASL 狀態")
    print("-" * 40)
    
    upasl_status = upasl_core.get_status()
    print(f"  已部署公理: {upasl_status['deployed_axioms']}")
    for dep in upasl_status['recent_deployments']:
        print(f"    - {dep['axiom_id']}: {dep['package']} @ {dep['deployed_at'][:19]}")
    
    # 9. 因果鏈驗證
    print("\n" + "-" * 40)
    print("🔗 因果鏈追蹤")
    print("-" * 40)
    
    for trace_id in list(bus.causal_chains.keys())[:2]:
        chain = bus.get_causal_chain(trace_id)
        print(f"  Trace {trace_id[:8]}: {len(chain)} 個幀")
    
    print("\n" + "=" * 60)
    print("✅ 整合測試完成")
    print("=" * 60)

if __name__ == "__main__":
    test_complete_integration()
