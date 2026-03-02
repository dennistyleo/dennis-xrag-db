"""
UPASL 端接收 XRAG 凍結包的介面
（這部分 Alex 需要實作，這裡提供模擬版本）
"""

from typing import Dict, Any, List, Optional
import json
import hashlib
from datetime import datetime
import random

class UPASLRuntimeCore:
    """UPASL 運行時演繹核心 - 模擬版本"""
    
    def __init__(self, name: str = "UPASL-Core"):
        self.name = name
        self.deployed_axioms: Dict[str, Dict] = {}
        self.deployment_log: List[Dict] = []
        self.invariant_enforcer = InvariantEnforcer()
        # 設定一致性檢查的成功率（調高到 100% 用於測試）
        self.consistency_success_rate = 1.0
        print(f"✅ {self.name} 初始化完成")
    
    def receive_freeze_package(self, package_json: str) -> Dict:
        """
        接收 XRAG 的凍結包
        
        Args:
            package_json: FreezePackage 的 JSON 字串
            
        Returns:
            部署結果
        """
        print(f"\n🛡️ UPASL: 收到凍結包")
        
        try:
            package = json.loads(package_json)
        except:
            return {'status': 'error', 'reason': 'invalid_json'}
        
        # 1. 驗證凍結包完整性
        if not self._verify_package(package):
            return {'status': 'rejected', 'reason': 'integrity_check_failed'}
        print(f"  ✅ 完整性驗證通過")
        
        # 2. 檢查與現有公理的一致性
        if not self._check_consistency(package):
            return {'status': 'rejected', 'reason': 'consistency_check_failed'}
        print(f"  ✅ 一致性檢查通過")
        
        # 3. 部署到運行時
        axiom_id = self._deploy_to_runtime(package)
        print(f"  ✅ 部署成功: {axiom_id}")
        
        # 4. 通知 XRAG 部署成功
        return {
            'status': 'deployed',
            'axiom_id': axiom_id,
            'package_id': package.get('model_id'),
            'timestamp': package.get('created_at'),
            'message': f'已部署到 {self.name}'
        }
    
    def _verify_package(self, package: Dict) -> bool:
        """驗證凍結包完整性"""
        expected_hash = self._compute_hash(package)
        actual_hash = package.get('hash', '')
        return expected_hash == actual_hash
    
    def _compute_hash(self, package: Dict) -> str:
        """計算哈希"""
        content = (
            f"{package.get('model_id', '')}"
            f"{package.get('model_form', '')}"
            f"{json.dumps(package.get('parameters', {}), sort_keys=True)}"
            f"{package.get('created_at', '')}"
        )
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def _check_consistency(self, package: Dict) -> bool:
        """檢查與現有公理的一致性"""
        # 調高成功率
        return random.random() < self.consistency_success_rate
    
    def _deploy_to_runtime(self, package: Dict) -> str:
        """部署到運行時"""
        axiom_id = f"upasl_{package.get('model_id', 'unknown')}"
        self.deployed_axioms[axiom_id] = package
        self.deployment_log.append({
            'axiom_id': axiom_id,
            'deployed_at': datetime.now().isoformat(),
            'package': package.get('model_name', 'unknown')
        })
        self.invariant_enforcer.add_axiom(axiom_id, package)
        return axiom_id
    
    def get_status(self) -> Dict:
        """獲取 UPASL 狀態"""
        return {
            'name': self.name,
            'deployed_axioms': len(self.deployed_axioms),
            'recent_deployments': self.deployment_log[-5:]
        }


class InvariantEnforcer:
    """UPASL 的不變量執行器（模擬）"""
    
    def __init__(self):
        self.active_axioms = []
    
    def add_axiom(self, axiom_id: str, package: Dict):
        """添加新公理到執行器"""
        self.active_axioms.append({
            'id': axiom_id,
            'name': package.get('model_name', ''),
            'added_at': datetime.now().isoformat()
        })
        print(f"  🔒 不變量執行器: 已加入 {axiom_id}")
    
    def check_invariants(self, data: Dict) -> bool:
        """檢查不變量（模擬）"""
        return True
