"""
候選公理格式 - XRAG 提交給 UPASL 的標準格式
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import hashlib
import uuid

@dataclass
class CandidateAxiom:
    """XRAG 生成的候選公理"""
    
    # 基本資訊
    axiom_id: str = field(default_factory=lambda: f"xrag_{uuid.uuid4().hex[:8]}")
    name: str = ""
    domain: str = ""
    version: str = "1.0"
    
    # 數學形式
    mathematical_form: Dict[str, Any] = field(default_factory=dict)
    
    # 參數與信心
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.95
    validation_metrics: Dict[str, float] = field(default_factory=dict)
    
    # 約束條件
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    # 元數據
    generated_by: str = "xrag"
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    training_data_hash: str = ""
    
    # XRAG 建議
    requires_expert: bool = False
    expert_reason: str = ""
    
    def to_json(self) -> str:
        """轉換為 JSON"""
        return json.dumps({
            "message_type": "candidate_axiom",
            "xrag_version": "1.0",
            "candidate": {
                "axiom_id": self.axiom_id,
                "name": self.name,
                "domain": self.domain,
                "version": self.version,
                "mathematical_form": self.mathematical_form,
                "parameters": self.parameters,
                "confidence": self.confidence,
                "validation_metrics": self.validation_metrics,
                "constraints": self.constraints,
                "generated_by": self.generated_by,
                "generated_at": self.generated_at,
                "training_data_hash": self.training_data_hash
            },
            "requires_expert": self.requires_expert,
            "expert_reason": self.expert_reason,
            "timestamp": datetime.now().isoformat()
        }, indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'CandidateAxiom':
        """從 JSON 載入"""
        data = json.loads(json_str)
        cand = data.get('candidate', {})
        return cls(
            axiom_id=cand.get('axiom_id', ''),
            name=cand.get('name', ''),
            domain=cand.get('domain', ''),
            version=cand.get('version', '1.0'),
            mathematical_form=cand.get('mathematical_form', {}),
            parameters=cand.get('parameters', {}),
            confidence=cand.get('confidence', 0.95),
            validation_metrics=cand.get('validation_metrics', {}),
            constraints=cand.get('constraints', {}),
            generated_by=cand.get('generated_by', 'xrag'),
            generated_at=cand.get('generated_at', ''),
            training_data_hash=cand.get('training_data_hash', ''),
            requires_expert=data.get('requires_expert', False),
            expert_reason=data.get('expert_reason', '')
        )
    
    def summary(self) -> str:
        """簡要摘要"""
        return (
            f"📦 候選公理: {self.name}\n"
            f"  ├─ ID: {self.axiom_id}\n"
            f"  ├─ 領域: {self.domain}\n"
            f"  ├─ 信心: {self.confidence:.1%}\n"
            f"  ├─ 參數數: {len(self.parameters)}\n"
            f"  └─ 需專家: {'✅' if self.requires_expert else '❌'}"
        )
