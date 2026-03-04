"""
XRAG 與 XR-BUS 整合
"""

from typing import List, Dict, Any, Optional
from src.xrbus import XRModule, ModuleID, OpCode, XRFrame
from src.matcher_advanced import AdvancedMatcher
from src.rejection_handler import RejectionHandler
from src.induction_engine import InductionEngine
import json

class XRAGBusModule(XRModule):
    """XRAG 的 XR-BUS 模組"""
    
    def __init__(self, bus, db_interface):
        super().__init__(ModuleID.XRAG, bus)
        self.db = db_interface
        self.matcher = AdvancedMatcher(db_interface)
        self.rejection = RejectionHandler(db_interface, self.matcher)
        self.induction = InductionEngine(db_interface)
        self.pending_requests = {}
        
        print(f"✅ XRAG module initialized on XR-BUS")
    
    def receive(self, frame: XRFrame):
        """處理收到的 XR-BUS 幀"""
        
        if frame.op_code == OpCode.AXIOM_QUERY:
            self._handle_query(frame)
        elif frame.op_code == OpCode.AXIOM_MATCH:
            self._handle_match(frame)
        elif frame.op_code == OpCode.AXIOM_INDUCE:
            self._handle_induce(frame)
        else:
            print(f"⚠️ Unknown opcode: {frame.op_code}")
    
    def _handle_query(self, frame: XRFrame):
        """處理公理查詢"""
        domain = frame.payload.get('domain')
        results = self.db.search_axioms({'domain': domain})
        
        response = XRFrame(
            module_id=self.module_id,
            boundary_id=frame.boundary_id,
            op_code=OpCode.DIAG_RESPONSE,
            trace_id=frame.trace_id,
            parent_id=frame.checksum,
            payload={
                'query': frame.payload,
                'results': results[:10],
                'count': len(results)
            }
        )
        self.send(response, frame.module_id)
    
    def _handle_match(self, frame: XRFrame):
        """處理匹配請求"""
        candidate = frame.payload.get('candidate')
        threshold = frame.payload.get('threshold', 0.5)
        
        matches = self.matcher.match(candidate, threshold=threshold)
        
        response = XRFrame(
            module_id=self.module_id,
            boundary_id=frame.boundary_id,
            op_code=OpCode.DIAG_RESPONSE,
            trace_id=frame.trace_id,
            parent_id=frame.checksum,
            payload={
                'matches': matches,
                'count': len(matches)
            }
        )
        self.send(response, frame.module_id)
    
    def _handle_induce(self, frame: XRFrame):
        """處理歸納請求"""
        data = frame.payload.get('data')
        context = frame.payload.get('context', {})
        
        results = self.induction.induce(data, context)
        
        response = XRFrame(
            module_id=self.module_id,
            boundary_id=frame.boundary_id,
            op_code=OpCode.DIAG_RESPONSE,
            trace_id=frame.trace_id,
            parent_id=frame.checksum,
            payload={
                'results': results,
                'count': len(results)
            }
        )
        self.send(response, frame.module_id)
    
    def query_axioms(self, domain: str = None) -> List[Dict]:
        """發送公理查詢"""
        frame = XRFrame(
            module_id=self.module_id,
            boundary_id="local",
            op_code=OpCode.AXIOM_QUERY,
            payload={'domain': domain}
        )
        self.send(frame, ModuleID.XRAG)
        return []
    
    def match_axiom(self, candidate: dict, threshold: float = 0.5) -> List[Dict]:
        """發送匹配請求"""
        frame = XRFrame(
            module_id=self.module_id,
            boundary_id="local",
            op_code=OpCode.AXIOM_MATCH,
            payload={
                'candidate': candidate,
                'threshold': threshold
            }
        )
        self.send(frame, ModuleID.XRAG)
        return []
