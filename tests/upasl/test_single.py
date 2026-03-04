import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import time
import json
import numpy as np
from src.xrbus import XRBUS, ModuleID
from src.db_config import XRAGDatabase
from src.db_interface import XRAGInterface
from xrag_upasl_integration import XRAGUPASLModule
from upasl_interface.upasl_receiver import UPASLRuntimeCore
from upasl_interface.freeze_package import FreezePackage

class SimpleTest:
    def __init__(self):
        self.bus = XRBUS("test-bus")
        self.db = XRAGDatabase('data/xrag_complete.db')
        self.interface = XRAGInterface(self.db)
        self.xrag = XRAGUPASLModule(self.bus, self.interface)
        self.upasl_core = UPASLRuntimeCore("UPASL-Test")
        
        # 手動註冊 UPASL 模組到 XR-BUS
        class UPASLModule:
            def __init__(self, core):
                self.core = core
            def receive(self, frame):
                if frame.payload.get('action') == 'deploy_freeze_package':
                    package = frame.payload.get('package', {})
                    result = self.core.receive_freeze_package(json.dumps(package))
                    
                    from src.xrbus import XRFrame
                    response = XRFrame(
                        module_id=ModuleID.UNKNOWN,
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
                    from src.xrbus import XRBUS
                    XRBUS().send(response, ModuleID.XRAG)
        
        self.bus.register_module(ModuleID.UNKNOWN, UPASLModule(self.upasl_core))
    
    def test_thermal(self):
        """測試熱學案例"""
        print("\n" + "="*60)
        print("🔥 測試熱學案例")
        print("="*60)
        
        # 高品質數據
        x = np.linspace(0, 100, 50)
        kA_d = 2.5
        y = kA_d * x + np.random.normal(0, 0.1, 50)  # 低噪聲
        
        data = {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 40
        }
        
        context = {
            'domain': 'thermal',
            'application': 'test'
        }
        
        package = self.xrag.generate_freeze_package(
            data=data,
            context=context,
            human_reviewer="Dr. Test"
        )
        
        print(f"\n📦 生成的公理: {package.model_name}")
        print(f"  公式: {package.model_form}")
        print(f"  信心: {package.confidence_interval:.0%}")
        
        success = self.xrag.send_to_upasl(package.model_id)
        time.sleep(0.5)
        
        print(f"\n📊 結果: {'✅ 成功' if success else '❌ 失敗'}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    test = SimpleTest()
    test.test_thermal()
