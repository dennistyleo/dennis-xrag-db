"""
測試 XRAG-UPASL 協調器
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from upasl_interface.candidate_axiom import CandidateAxiom
from xrag_upasl_coordinator import XRAGUPASLCoordinator

def test_coordinator():
    print("="*60)
    print("🧪 測試 XRAG-UPASL 協調器")
    print("="*60)
    
    # 初始化協調器
    coordinator = XRAGUPASLCoordinator()
    
    # 案例 1: 可直接部署的公理
    print("\n📌 案例 1: 可直接部署")
    candidate1 = CandidateAxiom(
        name="軸承磨損預測",
        domain="aging",
        mathematical_form={
            "type": "exponential_decay",
            "formula": "L = L0 * exp(-Ea/(k*T))"
        },
        parameters={
            "L0": {"value": 100000, "unit": "hours", "range": [80000, 120000]},
            "Ea": {"value": 0.85, "unit": "eV", "range": [0.7, 1.0]}
        },
        confidence=0.95,
        requires_expert=False
    )
    
    result1 = coordinator.submit_candidate(candidate1)
    
    # 案例 2: 需要專家審查的公理
    print("\n📌 案例 2: 需要專家審查")
    candidate2 = CandidateAxiom(
        name="量子效應修正",
        domain="quantum",
        mathematical_form={
            "type": "quantum_correction",
            "formula": "E = E0 + h*f * exp(-t/τ)"
        },
        parameters={
            "E0": {"value": 1.6e-19, "unit": "J"},
            "τ": {"value": 1e-12, "unit": "s", "range": [0.5e-12, 2e-12]}
        },
        confidence=0.82,
        requires_expert=True,
        expert_reason="量子效應需要物理專家確認"
    )
    
    result2 = coordinator.submit_candidate(candidate2)
    
    # 查看待審清單
    print("\n📋 待審清單:")
    pending = coordinator.get_pending_reviews()
    for p in pending:
        print(f"  • {p['name']} (信心: {p['confidence']:.0%})")
    
    # 專家審查
    print("\n👥 執行專家審查:")
    if pending:
        review = coordinator.expert_review(
            candidate_id=pending[0]['candidate_id'],
            reviewer="Dr. Alex Struver",
            approved=True,
            notes="量子效應參數經實驗驗證，同意部署"
        )
    
    # 查看凍結公理
    print("\n📦 已凍結公理:")
    frozen = coordinator.get_frozen_axioms()
    for fid, fax in frozen.items():
        print(f"  • {fid}: {fax['axiom']['name']}")
        print(f"    審查者: {fax['axiom']['reviewed_by']}")
    
    print("\n" + "="*60)
    print("✅ 測試完成")
    print("="*60)

if __name__ == "__main__":
    test_coordinator()
