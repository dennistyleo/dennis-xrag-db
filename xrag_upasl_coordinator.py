"""
XRAG-UPASL 協調器 - 管理整個流程
"""

from typing import Dict, List, Optional
from datetime import datetime
import json

from upasl_interface.candidate_axiom import CandidateAxiom
from upasl_interface.upasl_validator import UPASLValidator, ValidationResult

class XRAGUPASLCoordinator:
    """XRAG-UPASL 協調器"""
    
    def __init__(self, xrag_instance=None, upasl_instance=None):
        self.xrag = xrag_instance
        self.upasl = upasl_instance or UPASLValidator()
        self.pending_reviews = []
        self.frozen_axioms = {}
        self.validation_history = []
        print("✅ XRAG-UPASL 協調器初始化完成")
    
    def submit_candidate(self, candidate: CandidateAxiom) -> Dict:
        """
        步驟 1: XRAG 提交候選公理
        """
        print("\n" + "="*60)
        print("📤 XRAG 提交候選公理")
        print("="*60)
        print(candidate.summary())
        
        # UPASL 驗證
        validation = self.upasl.validate(candidate)
        self.validation_history.append(validation)
        
        # 決定下一步
        next_step = self._determine_next_step(validation, candidate)
        
        result = {
            "candidate_id": candidate.axiom_id,
            "candidate_name": candidate.name,
            "validation": {
                "consistency": validation.consistency_check['status'],
                "invariant": validation.invariant_check['status'],
                "runtime": validation.runtime_check['status']
            },
            "recommendation": validation.recommendation,
            "next_step": next_step,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\n📊 驗證結果:")
        print(f"  ├─ 一致性: {validation.consistency_check['status']}")
        print(f"  ├─ 不變量: {validation.invariant_check['status']}")
        print(f"  ├─ 運行時: {validation.runtime_check['status']}")
        print(f"  └─ 建議: {validation.recommendation['action']}")
        
        # 如果需要專家審查，加入待審列表
        if next_step == "expert_review":
            self.pending_reviews.append({
                "candidate": candidate,
                "validation": validation,
                "submitted_at": datetime.now().isoformat()
            })
            print(f"\n👥 已加入專家待審清單")
        
        return result
    
    def _determine_next_step(self, validation: ValidationResult, 
                            candidate: CandidateAxiom) -> str:
        """決定下一步"""
        
        # 如果候選要求專家審查
        if candidate.requires_expert:
            return "expert_review"
        
        # 根據 UPASL 建議
        action = validation.recommendation.get('action')
        
        if action == "deploy":
            return "deploy"
        elif action == "expert_review":
            return "expert_review"
        else:
            return "reject"
    
    def expert_review(self, candidate_id: str, reviewer: str, 
                      approved: bool, notes: str) -> Optional[Dict]:
        """
        步驟 2: 專家審查
        """
        print("\n" + "="*60)
        print("👥 專家審查")
        print("="*60)
        
        # 找到待審的公理
        pending = next(
            (p for p in self.pending_reviews if p['candidate'].axiom_id == candidate_id),
            None
        )
        
        if not pending:
            print(f"❌ 找不到待審公理: {candidate_id}")
            return None
        
        candidate = pending['candidate']
        validation = pending['validation']
        
        print(f"📋 審查公理: {candidate.name}")
        print(f"📝 審查者: {reviewer}")
        
        if approved:
            # 專家批准，產生凍結包
            frozen = self._create_frozen_axiom(
                candidate=candidate,
                validation=validation,
                reviewer=reviewer,
                notes=notes
            )
            
            self.frozen_axioms[frozen['axiom']['axiom_id']] = frozen
            
            print(f"\n✅ 專家批准，產生凍結包")
            print(f"  凍結包 ID: {frozen['axiom']['axiom_id']}")
            
            return frozen
        else:
            # 專家拒絕
            result = {
                "status": "rejected",
                "candidate_id": candidate_id,
                "candidate_name": candidate.name,
                "reviewer": reviewer,
                "notes": notes,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"\n❌ 專家拒絕")
            print(f"  原因: {notes}")
            
            return result
    
    def _create_frozen_axiom(self, candidate: CandidateAxiom,
                               validation: ValidationResult,
                               reviewer: str, notes: str) -> Dict:
        """產生最終凍結包"""
        
        frozen_id = f"{candidate.axiom_id}_frozen"
        
        frozen = {
            "message_type": "frozen_axiom",
            "xrag_version": "1.0",
            "upasl_version": "1.0",
            "axiom": {
                "axiom_id": frozen_id,
                "original_id": candidate.axiom_id,
                "name": candidate.name,
                "domain": candidate.domain,
                "version": "1.0",
                "status": "deployed",
                "freeze_date": datetime.now().isoformat(),
                "reviewed_by": reviewer,
                "review_notes": notes,
                "mathematical_form": candidate.mathematical_form,
                "parameters": candidate.parameters,
                "constraints": candidate.constraints,
                "validation_summary": {
                    "consistency": validation.consistency_check['status'],
                    "invariant": validation.invariant_check['status'],
                    "runtime": validation.runtime_check['status']
                }
            }
        }
        
        return frozen
    
    def get_pending_reviews(self) -> List[Dict]:
        """取得待審清單"""
        return [{
            "candidate_id": p['candidate'].axiom_id,
            "name": p['candidate'].name,
            "domain": p['candidate'].domain,
            "confidence": p['candidate'].confidence,
            "submitted_at": p['submitted_at']
        } for p in self.pending_reviews]
    
    def get_frozen_axioms(self) -> Dict:
        """取得已凍結公理"""
        return self.frozen_axioms
    
    def get_validation_history(self) -> List:
        """取得驗證歷史"""
        return self.validation_history
