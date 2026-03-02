"""
XR-BUS — Internal Causal Interconnect Fabric
Version: 1.0
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union, Callable
import hashlib
import time
import uuid

# ============================================================================
# 3.1 Frame Format Layer
# ============================================================================

class ModuleID(Enum):
    """XR 模組標識符"""
    XRAD = "XRAD"
    XENOS = "XENOS"
    XENOA = "XENOA"
    XAPS = "XAPS"
    XRAS = "XRAS"
    XRST = "XRST"
    XROG = "XROG"
    XRAG = "XRAG"
    XRBUS = "XRBUS"
    UNKNOWN = "UNK"

class OpCode(Enum):
    """操作碼"""
    DIAG_QUERY = 0x01
    DIAG_RESPONSE = 0x02
    DIAG_STREAM = 0x03
    GOV_POLICY = 0x10
    GOV_BOUNDARY = 0x11
    GOV_ENFORCE = 0x12
    SEM_TRANSLATE = 0x20
    SEM_ALIGN = 0x21
    SEM_DRIFT = 0x22
    SETTLE_TOKEN = 0x30
    SETTLE_AUDIT = 0x31
    SETTLE_PROOF = 0x32
    CAUSAL_LINK = 0x40
    CAUSAL_CHAIN = 0x41
    CAUSAL_ROOT = 0x42
    AXIOM_QUERY = 0x50
    AXIOM_MATCH = 0x51
    AXIOM_INDUCE = 0x52

@dataclass
class XRFrame:
    """XR-BUS 標準幀結構"""
    
    module_id: ModuleID
    boundary_id: str
    op_code: OpCode
    frame_version: str = "1.0"
    device_timestamp: int = field(default_factory=lambda: int(time.time() * 1e9))
    fabric_timestamp: int = 0
    cloud_timestamp: int = 0
    time_zone: str = "UTC"
    jitter_window: int = 1000000
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    parent_id: Optional[str] = None
    semantic_anchor: str = ""
    causal_depth: int = 0
    payload_type: str = "json"
    payload: Union[Dict, List, str, bytes] = field(default_factory=dict)
    hash_algo: str = "sha256"
    signature: Optional[str] = None
    checksum: str = ""
    
    def __post_init__(self):
        self.checksum = self._compute_checksum()
    
    def _compute_checksum(self) -> str:
        # 直接在方法內導入
        import json
        content = f"{self.module_id.value}{self.boundary_id}{self.op_code.value}{self.trace_id}{self.device_timestamp}"
        if isinstance(self.payload, dict):
            content += json.dumps(self.payload, sort_keys=True)
        else:
            content += str(self.payload)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def validate(self) -> bool:
        return self.checksum == self._compute_checksum()
    
    def to_dict(self) -> Dict:
        return {
            'module_id': self.module_id.value,
            'boundary_id': self.boundary_id,
            'op_code': self.op_code.value,
            'frame_version': self.frame_version,
            'device_timestamp': self.device_timestamp,
            'fabric_timestamp': self.fabric_timestamp,
            'cloud_timestamp': self.cloud_timestamp,
            'trace_id': self.trace_id,
            'parent_id': self.parent_id,
            'payload': self.payload,
            'checksum': self.checksum
        }

# ============================================================================
# 3.2 Timing Contract Layer
# ============================================================================

class TimingContract:
    """時序合約"""
    
    def __init__(self, master_clock: str = "fabric"):
        self.master_clock = master_clock
        self.clock_drifts: Dict[str, int] = {}
        self.jitter_history: Dict[str, List[int]] = {}
        
    def reconcile_clocks(self, frame: XRFrame) -> XRFrame:
        now = int(time.time() * 1e9)
        frame.fabric_timestamp = now
        frame.cloud_timestamp = now
        drift = frame.fabric_timestamp - frame.device_timestamp
        self.clock_drifts[frame.module_id.value] = drift
        return frame
    
    def check_jitter(self, frame: XRFrame) -> bool:
        module = frame.module_id.value
        if module not in self.jitter_history:
            self.jitter_history[module] = [frame.device_timestamp]
            return True
        last = self.jitter_history[module][-1]
        jitter = abs(frame.device_timestamp - last)
        if jitter <= frame.jitter_window:
            self.jitter_history[module].append(frame.device_timestamp)
            return True
        return False

# ============================================================================
# 3.3 Boundary Contract Layer
# ============================================================================

class BoundaryType(Enum):
    """邊界類型"""
    RACK = "rack"
    CLUSTER = "cluster"
    DOMAIN = "domain"
    TENANT = "tenant"
    SOVEREIGN = "sovereign"
    JURISDICTION = "jurisdiction"

@dataclass
class BoundaryContract:
    """邊界合約"""
    
    boundary_id: str
    boundary_type: BoundaryType
    owner: str
    governance_policies: List[str] = field(default_factory=list)
    sovereign_constraints: List[str] = field(default_factory=list)
    allowed_modules: List[ModuleID] = field(default_factory=list)
    
    def check_permission(self, frame: XRFrame) -> bool:
        if self.allowed_modules and frame.module_id not in self.allowed_modules:
            return False
        return True

# ============================================================================
# 3.4 Integrity & Version Layer
# ============================================================================

class IntegrityManager:
    """完整性管理器"""
    
    VERSIONS = ["1.0"]
    
    def __init__(self):
        self.frame_history: Dict[str, XRFrame] = {}
        self.signing_keys: Dict[str, str] = {}
    
    def verify_frame(self, frame: XRFrame) -> bool:
        if frame.frame_version not in self.VERSIONS:
            return False
        if not frame.validate():
            return False
        if frame.checksum in self.frame_history:
            return False
        self.frame_history[frame.checksum] = frame
        return True
    
    def sign_frame(self, frame: XRFrame, key_id: str) -> XRFrame:
        if key_id in self.signing_keys:
            content = f"{frame.trace_id}{frame.checksum}{frame.module_id.value}"
            frame.signature = hashlib.sha256(content.encode()).hexdigest()
        return frame

# ============================================================================
# XR-BUS 主幹
# ============================================================================

class XRBUS:
    """XR-BUS 主幹"""
    
    def __init__(self, bus_id: str = "xrbus-1"):
        self.bus_id = bus_id
        self.modules: Dict[ModuleID, Any] = {}
        self.timing = TimingContract()
        self.boundaries: Dict[str, BoundaryContract] = {}
        self.integrity = IntegrityManager()
        self.causal_chains: Dict[str, List[str]] = {}
        self.stats = {
            "frames_sent": 0,
            "frames_received": 0,
            "errors": 0,
            "causal_chains": 0
        }
        self.listeners: List[Callable] = []
    
    def register_module(self, module_id: ModuleID, module_instance: Any) -> bool:
        if module_id in self.modules:
            return False
        self.modules[module_id] = module_instance
        print(f"✅ XR-BUS: Module {module_id.value} registered")
        return True
    
    def register_boundary(self, contract: BoundaryContract) -> bool:
        if contract.boundary_id in self.boundaries:
            return False
        self.boundaries[contract.boundary_id] = contract
        print(f"✅ XR-BUS: Boundary {contract.boundary_id} registered")
        return True
    
    def send(self, frame: XRFrame, destination: ModuleID) -> bool:
        try:
            # 時序對齊
            frame = self.timing.reconcile_clocks(frame)
            
            # 抖動檢查
            if not self.timing.check_jitter(frame):
                self.stats["errors"] += 1
                return False
            
            # 完整性驗證
            if not self.integrity.verify_frame(frame):
                self.stats["errors"] += 1
                return False
            
            # 邊界檢查
            if frame.boundary_id in self.boundaries:
                boundary = self.boundaries[frame.boundary_id]
                if not boundary.check_permission(frame):
                    self.stats["errors"] += 1
                    return False
            
            # 更新因果鏈
            if frame.trace_id not in self.causal_chains:
                self.causal_chains[frame.trace_id] = []
                self.stats["causal_chains"] += 1
            self.causal_chains[frame.trace_id].append(frame.checksum)
            
            # 發送到目標模組
            if destination in self.modules:
                self.modules[destination].receive(frame)
                self.stats["frames_sent"] += 1
                
                # 通知監聽器
                for listener in self.listeners:
                    listener(frame, destination)
                    
                return True
            
            return False
            
        except Exception as e:
            self.stats["errors"] += 1
            error_msg = str(e)
            print(f"❌ XR-BUS error: {error_msg}")
            
            # 如果是 json 錯誤，印出更多資訊
            if 'json' in error_msg:
                print(f"  錯誤類型: {type(e).__name__}")
                print(f"  發生位置: send() 方法中")
                import traceback
                traceback.print_exc()
            
            return False
    
    def broadcast(self, frame: XRFrame) -> Dict[ModuleID, bool]:
        results = {}
        for module_id in self.modules:
            results[module_id] = self.send(frame, module_id)
        return results
    
    def get_causal_chain(self, trace_id: str) -> List[str]:
        return self.causal_chains.get(trace_id, [])
    
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "modules": len(self.modules),
            "boundaries": len(self.boundaries),
            "active_chains": len(self.causal_chains)
        }
    
    def add_listener(self, callback: Callable):
        self.listeners.append(callback)

# ============================================================================
# 模組基礎介面
# ============================================================================

class XRModule:
    """所有 XR 模組的基礎介面"""
    
    def __init__(self, module_id: ModuleID, bus: XRBUS):
        self.module_id = module_id
        self.bus = bus
        bus.register_module(module_id, self)
    
    def receive(self, frame: XRFrame):
        raise NotImplementedError
    
    def send(self, frame: XRFrame, destination: ModuleID) -> bool:
        return self.bus.send(frame, destination)
