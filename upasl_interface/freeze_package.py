"""
Freeze Package 格式 - XRAG → UPASL 交換標準
符合 Alex 的 Cold XRAG 規範：離線生成、人為審查、凍結部署、不可變更
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import json
import uuid

@dataclass
class FreezePackage:
    """
    XRAG 生成的凍結包，供 UPASL 運行時使用
    """
    
    # 1. 模型形式 (Model Form)
    model_id: str = field(default_factory=lambda: f"xrag_{uuid.uuid4().hex[:8]}")
    model_name: str = ""
    model_type: str = ""  # e.g., 'wavelet', 'fourier', 'exponential'
    model_form: str = ""  # 數學表達式
    
    # 2. 參數集 (Parameter Set)
    parameters: Dict[str, float] = field(default_factory=dict)
    parameter_bounds: Dict[str, List[float]] = field(default_factory=dict)  # 參數邊界
    
    # 3. 不確定性 (Uncertainty)
    confidence_interval: float = 0.95  # 0-1
    sensitivity: Dict[str, float] = field(default_factory=dict)  # 參數敏感度
    
    # 4. 約束報告 (Constraint Report)
    invariants_checked: List[str] = field(default_factory=list)
    constraints_passed: List[str] = field(default_factory=list)
    
    # 5. 反事實 (Counterfactuals)
    alternatives: List[Dict] = field(default_factory=list)  # 其他競爭候選
    
    # 6. 審計包 (Audit Bundle)
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: str = "xrag_system"
    human_reviewer: str = "pending"
    hash: str = ""
    
    def __post_init__(self):
        """自動計算審計哈希"""
        self.hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """計算完整性哈希"""
        content = (
            f"{self.model_id}{self.model_form}"
            f"{json.dumps(self.parameters, sort_keys=True)}"
            f"{self.created_at}"
        )
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def validate(self) -> bool:
        """驗證凍結包完整性"""
        return self.hash == self._compute_hash()
    
    def to_json(self) -> str:
        """序列化為 JSON"""
        return json.dumps(self.__dict__, indent=2, ensure_ascii=False)
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return self.__dict__.copy()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'FreezePackage':
        """從 JSON 反序列化"""
        data = json.loads(json_str)
        return cls(**data)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FreezePackage':
        """從字典創建"""
        return cls(**data)
    
    def summary(self) -> str:
        """簡要摘要"""
        return (
            f"📦 FreezePackage: {self.model_name}\n"
            f"  ├─ Type: {self.model_type}\n"
            f"  ├─ Form: {self.model_form[:50]}...\n"
            f"  ├─ Confidence: {self.confidence_interval:.2%}\n"
            f"  ├─ Params: {len(self.parameters)}\n"
            f"  ├─ Reviewer: {self.human_reviewer}\n"
            f"  └─ Hash: {self.hash[:16]}..."
        )
