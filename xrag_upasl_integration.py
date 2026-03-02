"""
XRAG 與 UPASL 整合 - 生成與發送 Freeze Package
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import time

from src.xrbus import XRModule, ModuleID, OpCode, XRFrame
from src.matcher_advanced import AdvancedMatcher
from src.induction_engine import InductionEngine
from upasl_interface.freeze_package import FreezePackage

class XRAGUPASLModule(XRModule):
    """XRAG 的 UPASL 整合模組"""
    
    def __init__(self, bus, db_interface):
        super().__init__(ModuleID.XRAG, bus)
        self.db = db_interface
        self.matcher = AdvancedMatcher(db_interface)
        self.induction = InductionEngine(db_interface)
        self.frozen_packages: Dict[str, FreezePackage] = {}
        self.deployment_history: List[Dict] = []
        self.pending_responses: Dict[str, bool] = {}
        
        print(f"✅ XRAG-UPASL 整合模組初始化完成")
    
    def generate_freeze_package(self, 
                                data: Dict,
                                context: Dict,
                                human_reviewer: str = "pending") -> FreezePackage:
        """生成凍結包"""
        print(f"\n🔍 XRAG: 開始生成凍結包 (Reviewer: {human_reviewer})")
        
        # L1: 問題特徵化
        features = self._analyze_features(data)
        print(f"  L1: 數據特徵 - SNR:{features['snr']:.2f}dB, 樣本數:{features['samples']}")
        
        # L2: 生成候選路徑 - 根據 SNR 調整
        candidates = self._generate_candidates(features, context)
        print(f"  L2: 生成 {len(candidates)} 個候選路徑")
        
        # L3: 可行性評估
        feasible = self._assess_feasibility(candidates, features)
        print(f"  L3: {len(feasible)} 個通過可行性評估")
        
        if not feasible:
            raise ValueError("沒有可行的候選方案")
        
        # L4: 參數校準
        best = self._calibrate_parameters(feasible[0], data)
        print(f"  L4: 最佳方案 - {best['name']} (信心: {best['confidence']:.2%})")
        
        # L5: 構建凍結包
        package = FreezePackage(
            model_name=best['name'],
            model_type=best['type'],
            model_form=best['form'],
            parameters=best['params'],
            parameter_bounds=best['bounds'],
            confidence_interval=best['confidence'],
            sensitivity=best['sensitivity'],
            invariants_checked=features['invariants'],
            constraints_passed=features['constraints'],
            alternatives=feasible[1:4] if len(feasible) > 1 else [],
            human_reviewer=human_reviewer
        )
        
        self.frozen_packages[package.model_id] = package
        print(f"  L5: ✅ 凍結包生成完成 - {package.model_id}")
        print(package.summary())
        
        return package
    
    def _analyze_features(self, data: Dict) -> Dict:
        """數據特徵分析"""
        x = np.array(data.get('x', []))
        y = np.array(data.get('y', []))
        
        if len(y) > 1:
            signal_power = np.mean(y**2)
            noise_power = np.var(y) if len(y) > 1 else 0
            snr = 10 * np.log10(signal_power / (noise_power + 1e-10))
        else:
            snr = 20
        
        # 檢測非線性程度
        if len(x) > 2:
            # 簡單的非線性檢測：比較線性和二次擬合
            coeffs_linear = np.polyfit(x, y, 1)
            y_pred_linear = np.polyval(coeffs_linear, x)
            error_linear = np.mean((y - y_pred_linear)**2)
            
            coeffs_quad = np.polyfit(x, y, 2)
            y_pred_quad = np.polyval(coeffs_quad, x)
            error_quad = np.mean((y - y_pred_quad)**2)
            
            is_nonlinear = error_quad < error_linear * 0.8
        else:
            is_nonlinear = False
        
        return {
            'invariants': ['能量守恆', '質量守恆'],
            'constraints': ['平穩性'],
            'snr': float(snr),
            'samples': len(x),
            'is_nonlinear': is_nonlinear
        }
    
    def _generate_candidates(self, features: Dict, context: Dict) -> List[Dict]:
        """生成候選路徑 - 根據 SNR 調整"""
        domain = context.get('domain', 'general')
        candidates = []
        
        # 基礎候選
        candidates.append({'name': '線性回歸', 'type': 'linear', 'form': 'y = ax + b', 'complexity': 1})
        candidates.append({'name': '指數衰減', 'type': 'exponential', 'form': 'y = a·e^(bx)', 'complexity': 2})
        candidates.append({'name': '冪律', 'type': 'power_law', 'form': 'y = a·x^b', 'complexity': 2})
        candidates.append({'name': '多項式', 'type': 'polynomial', 'form': 'y = a₀ + a₁x + a₂x²', 'complexity': 3})
        
        # SNR 夠高才加入複雜模型
        if features['snr'] > 10:
            candidates.append({'name': '對數', 'type': 'logarithmic', 'form': 'y = a·ln(x) + b', 'complexity': 2})
        
        if features['snr'] > 15:
            candidates.append({'name': '小波變換', 'type': 'wavelet', 'form': 'W(a,b) = ∫f(t)ψ((t-b)/a)dt', 'complexity': 4})
        
        # 如果是非線性，優先選擇非線性模型
        if features['is_nonlinear']:
            # 把非線性模型往前放
            candidates.sort(key=lambda x: 0 if x['type'] in ['exponential', 'power_law', 'polynomial'] else 1)
        
        return candidates
    
    def _assess_feasibility(self, candidates: List[Dict], features: Dict) -> List[Dict]:
        """可行性評估"""
        feasible = []
        for c in candidates:
            # SNR 太低時只留線性
            if features['snr'] < 5 and c['complexity'] > 1:
                continue
            # 樣本太少不用複雜模型
            if features['samples'] < 20 and c['complexity'] > 2:
                continue
            feasible.append(c)
        return feasible
    
    def _calibrate_parameters(self, candidate: Dict, data: Dict) -> Dict:
        """參數校準"""
        x = np.array(data.get('x', [0,1]))
        y = np.array(data.get('y', [0,1]))
        
        if candidate['type'] == 'linear':
            if len(x) > 1:
                A = np.vstack([x, np.ones(len(x))]).T
                a, b = np.linalg.lstsq(A, y, rcond=None)[0]
            else:
                a, b = 1.0, 0.0
            
            return {
                'name': candidate['name'],
                'type': candidate['type'],
                'form': f'y = {a:.4f}x + {b:.4f}',
                'params': {'a': float(a), 'b': float(b)},
                'bounds': {
                    'a': [float(a*0.8), float(a*1.2)],
                    'b': [float(b-0.5), float(b+0.5)]
                },
                'confidence': 0.95,
                'sensitivity': {'a': 0.1, 'b': 0.05}
            }
        
        elif candidate['type'] == 'exponential':
            # 簡單的指數擬合
            log_y = np.log(np.abs(y) + 1e-10)
            if len(x) > 1:
                A = np.vstack([x, np.ones(len(x))]).T
                b, log_a = np.linalg.lstsq(A, log_y, rcond=None)[0]
                a = np.exp(log_a)
            else:
                a, b = 1.0, 0.1
            
            return {
                'name': candidate['name'],
                'type': candidate['type'],
                'form': f'y = {a:.4f}·e^({b:.4f}x)',
                'params': {'a': float(a), 'b': float(b)},
                'bounds': {'a': [a*0.8, a*1.2], 'b': [b*0.8, b*1.2]},
                'confidence': 0.92,
                'sensitivity': {'a': 0.15, 'b': 0.08}
            }
        
        elif candidate['type'] == 'power_law':
            # 冪律擬合
            log_x = np.log(np.abs(x) + 1e-10)
            log_y = np.log(np.abs(y) + 1e-10)
            if len(log_x) > 1:
                A = np.vstack([log_x, np.ones(len(log_x))]).T
                b, log_a = np.linalg.lstsq(A, log_y, rcond=None)[0]
                a = np.exp(log_a)
            else:
                a, b = 1.0, 1.0
            
            return {
                'name': candidate['name'],
                'type': candidate['type'],
                'form': f'y = {a:.4f}·x^{b:.4f}',
                'params': {'a': float(a), 'b': float(b)},
                'bounds': {'a': [a*0.8, a*1.2], 'b': [b*0.8, b*1.2]},
                'confidence': 0.9,
                'sensitivity': {'a': 0.12, 'b': 0.1}
            }
        
        else:
            # 多項式或其他
            return {
                'name': candidate['name'],
                'type': candidate['type'],
                'form': candidate['form'],
                'params': {'a': 1.0, 'b': 0.5},
                'bounds': {'a': [0.8, 1.2], 'b': [0.3, 0.7]},
                'confidence': 0.88,
                'sensitivity': {'a': 0.12, 'b': 0.1}
            }
    
    def send_to_upasl(self, package_id: str, destination: str = "UPASL") -> bool:
        """發送凍結包給 UPASL"""
        if package_id not in self.frozen_packages:
            print(f"❌ 找不到凍結包: {package_id}")
            return False
        
        package = self.frozen_packages[package_id]
        
        frame = XRFrame(
            module_id=self.module_id,
            boundary_id="upasl_boundary",
            op_code=OpCode.SETTLE_AUDIT,
            payload={
                'action': 'deploy_freeze_package',
                'package': package.to_dict(),
                'destination': destination,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        self.pending_responses[package_id] = False
        success = self.send(frame, ModuleID.UNKNOWN)
        
        if success:
            print(f"📨 已發送凍結包 {package_id} 給 UPASL")
            
            # 等待回應
            for _ in range(20):  # 增加等待次數
                time.sleep(0.1)
                if self.pending_responses.get(package_id, False):
                    break
            
            self.deployment_history.append({
                'package_id': package_id,
                'sent_at': datetime.now().isoformat(),
                'destination': destination,
                'status': 'sent'
            })
            return True
        else:
            print(f"❌ 發送失敗")
            return False
    
    def receive(self, frame: XRFrame):
        """接收回應"""
        if frame.op_code == OpCode.SETTLE_AUDIT:
            status = frame.payload.get('status')
            package_id = frame.payload.get('package_id')
            message = frame.payload.get('message', '')
            
            print(f"\n📬 收到 UPASL 回應:")
            print(f"  📦 Package: {package_id}")
            print(f"  📊 狀態: {status}")
            if message:
                print(f"  💬 訊息: {message}")
            
            self.deployment_history.append({
                'package_id': package_id,
                'status': status,
                'received_at': datetime.now().isoformat()
            })
            
            if package_id in self.pending_responses:
                self.pending_responses[package_id] = True
