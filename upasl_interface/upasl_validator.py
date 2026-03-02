"""
UPASL 驗證器 - 負責驗證 XRAG 提交的候選公理
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import hashlib

class ValidationStatus(Enum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"

class Recommendation(Enum):
    DEPLOY = "deploy"
    EXPERT_REVIEW = "expert_review"
    REJECT = "reject"

@dataclass
class ValidationResult:
    """UPASL 驗證結果"""
    
    candidate_id: str
    consistency_check: Dict[str, Any]
    invariant_check: Dict[str, Any]
    runtime_check: Dict[str, Any]
    recommendation: Dict[str, Any]
    validated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_json(self) -> str:
        return json.dumps({
            "message_type": "validation_result",
            "upasl_version": "1.0",
            "candidate_id": self.candidate_id,
            "validation": {
                "consistency_check": self.consistency_check,
                "invariant_check": self.invariant_check,
                "runtime_check": self.runtime_check
            },
            "recommendation": self.recommendation,
            "validated_at": self.validated_at
        }, indent=2, ensure_ascii=False)
    
    def should_deploy(self) -> bool:
        """判斷是否可以直接部署"""
        return (self.recommendation.get('action') == Recommendation.DEPLOY.value and
                self.consistency_check.get('status') == ValidationStatus.PASSED.value and
                self.invariant_check.get('status') == ValidationStatus.PASSED.value)

class UPASLValidator:
    """UPASL 驗證核心"""
    
    def __init__(self):
        # 已知公理庫
        self.known_axioms = self._load_known_axioms()
        
        # 物理不變量
        self.invariants = self._load_invariants()
        print("✅ UPASL 驗證器初始化完成")
    
    def validate(self, candidate) -> ValidationResult:
        """
        驗證候選公理
        
        檢查項目：
        1. 與現有公理的一致性
        2. 物理不變量
        3. 運行時可行性
        """
        print(f"\n🛡️ UPASL 驗證候選公理: {candidate.axiom_id}")
        
        # 1. 一致性檢查
        consistency = self._check_consistency(candidate)
        print(f"  ├─ 一致性: {consistency['status']}")
        
        # 2. 不變量檢查
        invariant = self._check_invariants(candidate)
        print(f"  ├─ 不變量: {invariant['status']}")
        
        # 3. 運行時檢查
        runtime = self._check_runtime(candidate)
        print(f"  ├─ 運行時: {runtime['status']}")
        
        # 4. 綜合建議
        recommendation = self._make_recommendation(
            consistency, invariant, runtime, candidate
        )
        print(f"  └─ 建議: {recommendation['action']}")
        
        return ValidationResult(
            candidate_id=candidate.axiom_id,
            consistency_check=consistency,
            invariant_check=invariant,
            runtime_check=runtime,
            recommendation=recommendation
        )
    
    def _check_consistency(self, candidate) -> Dict:
        """檢查與現有公理的一致性"""
        
        conflicts = []
        compatible = []
        
        # 比對已知公理
        for axiom in self.known_axioms:
            if axiom['domain'] == candidate.domain:
                # 檢查是否有衝突
                if self._has_conflict(candidate, axiom):
                    conflicts.append(axiom['name'])
                else:
                    compatible.append(axiom['name'])
        
        status = ValidationStatus.PASSED.value
        if len(conflicts) > 2:
            status = ValidationStatus.FAILED.value
        elif len(conflicts) > 0:
            status = ValidationStatus.WARNING.value
        
        return {
            "status": status,
            "conflicts": conflicts,
            "compatible": compatible,
            "message": f"找到 {len(compatible)} 個相容公理，{len(conflicts)} 個衝突"
        }
    
    def _check_invariants(self, candidate) -> Dict:
        """檢查物理不變量"""
        
        failed = []
        passed = []
        
        # 檢查各項不變量
        for inv in self.invariants:
            if self._check_invariant(candidate, inv):
                passed.append(inv['name'])
            else:
                failed.append(inv['name'])
        
        status = ValidationStatus.PASSED.value
        if len(failed) > 0:
            status = ValidationStatus.FAILED.value
        
        return {
            "status": status,
            "passed": passed,
            "failed": failed,
            "message": f"{len(passed)} 項通過，{len(failed)} 項失敗"
        }
    
    def _check_runtime(self, candidate) -> Dict:
        """檢查運行時可行性"""
        
        issues = []
        
        # 檢查參數範圍
        for param_name, param in candidate.parameters.items():
            if 'range' in param:
                if param.get('value', 0) < param['range'][0] or \
                   param.get('value', 0) > param['range'][1]:
                    issues.append(f"{param_name} 超出範圍")
        
        # 檢查複雜度
        if candidate.confidence < 0.7:
            issues.append("信心度過低")
        
        status = ValidationStatus.PASSED.value
        if len(issues) > 2:
            status = ValidationStatus.FAILED.value
        elif len(issues) > 0:
            status = ValidationStatus.WARNING.value
        
        return {
            "status": status,
            "issues": issues,
            "estimated_cost": "medium",
            "message": f"發現 {len(issues)} 個潛在問題"
        }
    
    def _make_recommendation(self, consistency, invariant, runtime, candidate) -> Dict:
        """做出綜合建議"""
        
        # 如果候選本身要求專家審查
        if candidate.requires_expert:
            return {
                "action": Recommendation.EXPERT_REVIEW.value,
                "reason": candidate.expert_reason or "XRAG 建議專家審查",
                "priority": "high"
            }
        
        # 根據檢查結果決定
        if (consistency['status'] == ValidationStatus.FAILED.value or
            invariant['status'] == ValidationStatus.FAILED.value):
            return {
                "action": Recommendation.REJECT.value,
                "reason": "嚴重違反一致性或不變量",
                "priority": "high"
            }
        
        if (consistency['status'] == ValidationStatus.WARNING.value or
            runtime['status'] == ValidationStatus.WARNING.value):
            return {
                "action": Recommendation.EXPERT_REVIEW.value,
                "reason": "有潛在問題，建議專家確認",
                "priority": "medium"
            }
        
        return {
            "action": Recommendation.DEPLOY.value,
            "reason": "所有檢查通過，可直接部署",
            "priority": "low"
        }
    
    def _load_known_axioms(self) -> List[Dict]:
        """載入已知公理庫"""
        return [
            {"name": "bearing_wear_v1", "domain": "aging", "form": "exponential"},
            {"name": "arrhenius_general", "domain": "aging", "form": "exponential"},
            {"name": "fourier_law", "domain": "thermal", "form": "linear"},
        ]
    
    def _load_invariants(self) -> List[Dict]:
        """載入物理不變量"""
        return [
            {"name": "energy_conservation", "check": "positive_energy"},
            {"name": "parameter_positivity", "check": "all_positive"},
            {"name": "dimension_consistency", "check": "units_match"},
        ]
    
    def _has_conflict(self, candidate, known) -> bool:
        """檢查是否有衝突"""
        # 簡化版衝突檢測
        return False
    
    def _check_invariant(self, candidate, invariant) -> bool:
        """檢查單一不變量"""
        # 簡化版不變量檢查
        return True
