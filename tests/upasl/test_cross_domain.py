"""
XRAG-UPASL 跨領域完整測試
驗證 17 大領域的公理生成與部署
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import time
import json
import numpy as np
from datetime import datetime
import random

from src.xrbus import XRBUS, ModuleID, XRModule, XRFrame
from src.db_config import XRAGDatabase
from src.db_interface import XRAGInterface
from xrag_upasl_integration import XRAGUPASLModule
from upasl_interface.upasl_receiver import UPASLRuntimeCore

class UPASLXRModule(XRModule):
    """UPASL 的 XR-BUS 模組包裝"""
    
    def __init__(self, bus, upasl_core):
        super().__init__(ModuleID.UNKNOWN, bus)
        self.upasl = upasl_core
    
    def receive(self, frame: XRFrame):
        """處理收到的幀"""
        if frame.payload.get('action') == 'deploy_freeze_package':
            package = frame.payload.get('package', {})
            result = self.upasl.receive_freeze_package(json.dumps(package))
            
            response = XRFrame(
                module_id=self.module_id,
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
            self.send(response, frame.module_id)

def generate_test_data(domain: str):
    """根據領域生成測試數據"""
    
    if domain == "electrical":
        # 電學：歐姆定律 V = I·R
        x = np.linspace(0, 10, 50)
        R = 100
        y = R * x + np.random.normal(0, 5, 50)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 30,
            'true_form': 'V = I·R',
            'true_params': {'R': R}
        }
    
    elif domain == "thermal":
        # 熱學：傅立葉定律 Q = k·A·ΔT/d
        x = np.linspace(0, 100, 50)  # ΔT
        kA_d = 2.5
        y = kA_d * x + np.random.normal(0, 2, 50)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 25,
            'true_form': 'Q = k·A·ΔT/d',
            'true_params': {'kA_d': kA_d}
        }
    
    elif domain == "emc":
        # EMC：屏蔽效能 SE = 20·log₁₀(E₁/E₂)
        x = np.linspace(1, 100, 40)  # E₁/E₂
        y = 20 * np.log10(x) + np.random.normal(0, 0.5, 40)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 35,
            'true_form': 'SE = 20·log₁₀(E₁/E₂)',
            'true_params': {'log_coeff': 20}
        }
    
    elif domain == "fluid":
        # 流體力學：白努力 P + ½ρv² + ρgh = constant
        x = np.linspace(0, 20, 40)  # v²
        rho_half = 0.5
        y = 100 - rho_half * x + np.random.normal(0, 1, 40)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 28,
            'true_form': 'P + ½ρv² = constant',
            'true_params': {'rho_half': rho_half}
        }
    
    elif domain == "mechanics":
        # 固體力學：虎克定律 σ = E·ε
        x = np.linspace(0, 0.01, 30)  # 應變 ε
        E = 200e9
        y = E * x + np.random.normal(0, 1e8, 30)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 32,
            'true_form': 'σ = E·ε',
            'true_params': {'E': E}
        }
    
    elif domain == "thermodynamics":
        # 熱力學：理想氣體 P·V = n·R·T
        x = np.linspace(300, 500, 35)  # T
        nR_V = 0.01
        y = nR_V * x + np.random.normal(0, 0.5, 35)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 30,
            'true_form': 'P = (nR/V)·T',
            'true_params': {'nR_V': nR_V}
        }
    
    elif domain == "semiconductor":
        # 半導體：二極體 I = I_s·(e^(V/(n·V_T)) - 1)
        x = np.linspace(0, 1, 40)  # V
        I_s = 1e-12
        V_T = 0.026
        n = 1.5
        y = I_s * (np.exp(x/(n*V_T)) - 1) + np.random.normal(0, 1e-13, 40)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 25,
            'true_form': 'I = I_s·(e^(V/(n·V_T)) - 1)',
            'true_params': {'I_s': I_s, 'n': n, 'V_T': V_T}
        }
    
    elif domain == "quantum":
        # 量子力學：普朗克關係 E = h·f
        x = np.linspace(1e14, 1e15, 30)  # f
        h = 6.626e-34
        y = h * x + np.random.normal(0, 1e-20, 30)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 30,
            'true_form': 'E = h·f',
            'true_params': {'h': h}
        }
    
    elif domain == "aging":
        # 老化：阿倫尼斯模型 AF = exp[(Ea/k)(1/T_use - 1/T_stress)]
        x = np.linspace(300, 400, 30)  # 1/T
        Ea_k = 5000
        y = np.exp(Ea_k * (1/300 - 1/x)) + np.random.normal(0, 0.1, 30)
        return {
            'x': (1/x).tolist(),
            'y': y.tolist(),
            'snr': 20,
            'true_form': 'AF = exp[(Ea/k)(1/T_use - 1/T_stress)]',
            'true_params': {'Ea_k': Ea_k}
        }
    
    elif domain == "causal_drift":
        # 因果漂移：CUSUM S_t = max(0, S_{t-1} + (x_t - μ) - k)
        x = np.linspace(0, 100, 50)
        drift = 0.02
        y = drift * x**2 + np.random.normal(0, 0.5, 50)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 22,
            'true_form': 'quadratic drift',
            'true_params': {'drift': drift}
        }
    
    elif domain == "statistics":
        # 統計指標：MACD (EMA_12 - EMA_26)
        x = np.linspace(0, 100, 60)
        trend = 0.1
        cycle = 5 * np.sin(2 * np.pi * x / 20)
        y = trend * x + cycle + np.random.normal(0, 0.5, 60)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 18,
            'true_form': 'trend + cycle',
            'true_params': {'trend': trend}
        }
    
    elif domain == "control_theory":
        # 控制理論：PID輸出 u(t) = K_p·e(t) + K_i·∫e(τ)dτ + K_d·de/dt
        x = np.linspace(0, 10, 100)
        Kp = 2.0
        Ki = 0.5
        Kd = 0.1
        error = np.sin(x)
        y = Kp*error + Ki*np.cumsum(error)*0.1 + Kd*np.gradient(error)
        y += np.random.normal(0, 0.05, 100)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 28,
            'true_form': 'PID control',
            'true_params': {'Kp': Kp, 'Ki': Ki, 'Kd': Kd}
        }
    
    elif domain == "information_theory":
        # 資訊理論：夏農熵 H = -∑ p(x)·log₂ p(x)
        x = np.linspace(0.01, 0.99, 40)
        y = -x * np.log2(x) - (1-x) * np.log2(1-x)
        y += np.random.normal(0, 0.01, 40)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 35,
            'true_form': 'binary entropy',
            'true_params': {}
        }
    
    elif domain == "financial":
        # 財務工程：夏普比率 Sharpe = (R_p - R_f)/σ_p
        x = np.linspace(0.05, 0.2, 35)  # σ_p
        R_p_minus_Rf = 0.1
        y = R_p_minus_Rf / x + np.random.normal(0, 0.02, 35)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 24,
            'true_form': 'Sharpe = (R_p - R_f)/σ_p',
            'true_params': {'R_p_minus_Rf': R_p_minus_Rf}
        }
    
    elif domain == "power_supply":
        # 電源行為：CV/CC模式 V_out = V_set when RL > V_set/I_set
        x = np.linspace(10, 1000, 40)  # RL
        V_set = 12
        I_set = 1
        y = np.where(x > V_set/I_set, V_set, I_set*x) + np.random.normal(0, 0.1, 40)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 30,
            'true_form': 'CV/CC mode',
            'true_params': {'V_set': V_set, 'I_set': I_set}
        }
    
    elif domain == "substrate":
        # 基板材料：翹曲控制 warpage = f(CTE_mismatch)
        x = np.linspace(0, 20, 30)  # CTE mismatch
        y = 0.5 * x**1.2 + np.random.normal(0, 2, 30)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 22,
            'true_form': 'warpage ∝ (ΔCTE)^n',
            'true_params': {}
        }
    
    elif domain == "manufacturing":
        # 製造工藝：CNC切削速度 Vc = π·D·n/1000
        x = np.linspace(1000, 10000, 35)  # n (RPM)
        D = 10
        y = np.pi * D * x / 1000 + np.random.normal(0, 5, 35)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 32,
            'true_form': 'Vc = π·D·n/1000',
            'true_params': {'D': D}
        }
    
    elif domain == "healthcare":
        # 醫療保健：PK/PD 藥動學 C = C₀·e^(-kt)
        x = np.linspace(0, 24, 30)  # time (hours)
        C0 = 100
        k = 0.2
        y = C0 * np.exp(-k * x) + np.random.normal(0, 2, 30)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 26,
            'true_form': 'C = C₀·e^(-kt)',
            'true_params': {'C0': C0, 'k': k}
        }
    
    elif domain == "quality":
        # 品質管理：FMEA風險優先數 RPN = S × O × D
        x = np.linspace(1, 10, 30)  # S
        O = 5
        D = 3
        y = x * O * D + np.random.normal(0, 5, 30)
        return {
            'x': x.tolist(),
            'y': y.tolist(),
            'snr': 28,
            'true_form': 'RPN = S × O × D',
            'true_params': {'O': O, 'D': D}
        }
    
    else:
        return None

def test_cross_domain():
    """跨領域完整測試"""
    print("=" * 70)
    print("🌐 XRAG-UPASL 跨領域完整測試")
    print("=" * 70)
    
    # 初始化系統
    bus = XRBUS("xrbus-cross")
    db = XRAGDatabase('data/xrag_complete.db')
    interface = XRAGInterface(db)
    xrag = XRAGUPASLModule(bus, interface)
    upasl_core = UPASLRuntimeCore("UPASL-Cross")
    upasl = UPASLXRModule(bus, upasl_core)
    
    print(f"\n✅ 系統初始化完成")
    print(f"📊 資料庫公理數: {len(interface.search_axioms({}))}")
    
    # 定義要測試的領域
    domains = [
        ("electrical", "⚡ 電學"),
        ("thermal", "🔥 熱學"),
        ("emc", "📡 EMC"),
        ("fluid", "💧 流體力學"),
        ("mechanics", "🔧 固體力學"),
        ("thermodynamics", "🧪 熱力學"),
        ("semiconductor", "🔬 半導體"),
        ("quantum", "⚛️ 量子力學"),
        ("aging", "⏳ 老化"),
        ("causal_drift", "🔄 因果漂移"),
        ("statistics", "📊 統計指標"),
        ("control_theory", "🎛️ 控制理論"),
        ("information_theory", "📐 資訊理論"),
        ("financial", "💰 財務工程"),
        ("power_supply", "🔋 電源行為"),
        ("substrate", "🧩 基板材料"),
        ("manufacturing", "⚙️ 製造工藝"),
        ("healthcare", "🏥 醫療保健"),
        ("quality", "✅ 品質管理")
    ]
    
    results = []
    
    for i, (domain_key, domain_name) in enumerate(domains, 1):
        print(f"\n" + "-" * 70)
        print(f"📌 測試案例 {i}/{len(domains)}: {domain_name}")
        print("-" * 70)
        
        # 生成測試數據
        data = generate_test_data(domain_key)
        if not data:
            print(f"  ⚠️ 跳過 {domain_key}")
            continue
        
        context = {
            'domain': domain_key,
            'application': f'{domain_key}_test',
            'snr': data['snr']
        }
        
        # 生成凍結包
        reviewer = f"Dr. Test-{domain_key}"
        package = xrag.generate_freeze_package(
            data=data,
            context=context,
            human_reviewer=reviewer
        )
        
        # 發送給 UPASL
        success = xrag.send_to_upasl(package.model_id)
        
        # 記錄結果
        result = {
            'domain': domain_key,
            'name': domain_name,
            'package_id': package.model_id,
            'model_name': package.model_name,
            'model_form': package.model_form,
            'confidence': package.confidence_interval,
            'success': success,
            'deployed': False
        }
        
        # 檢查是否部署成功
        time.sleep(0.3)
        for dep in xrag.deployment_history:
            if dep.get('package_id') == package.model_id and dep.get('status') == 'deployed':
                result['deployed'] = True
                break
        
        results.append(result)
        
        # 顯示結果
        status = "✅" if result['deployed'] else "⚠️"
        print(f"\n  {status} 結果: {package.model_name}")
        print(f"    公式: {package.model_form[:60]}...")
        print(f"    信心: {package.confidence_interval:.2%}")
        print(f"    真值: {data['true_form']}")
        
        time.sleep(0.2)
    
    # 顯示總結
    print("\n" + "=" * 70)
    print("📊 跨領域測試總結")
    print("=" * 70)
    
    successful = sum(1 for r in results if r['deployed'])
    total = len(results)
    
    print(f"\n✅ 成功部署: {successful}/{total} ({successful/total*100:.1f}%)")
    print("\n📋 詳細結果:")
    
    for r in results:
        icon = "✅" if r['deployed'] else "⚠️"
        print(f"  {icon} {r['name']}: {r['model_name']} (信心: {r['confidence']:.0%})")
    
    # XR-BUS 統計
    print("\n" + "-" * 70)
    print("📊 XR-BUS 統計")
    print("-" * 70)
    
    stats = bus.get_stats()
    print(f"  發送幀數: {stats['frames_sent']}")
    print(f"  錯誤數: {stats['errors']}")
    print(f"  因果鏈: {stats['causal_chains']}")
    
    # UPASL 狀態
    print("\n" + "-" * 70)
    print("🛡️ UPASL 最終狀態")
    print("-" * 70)
    
    upasl_status = upasl_core.get_status()
    print(f"  已部署公理總數: {upasl_status['deployed_axioms']}")
    
    print("\n" + "=" * 70)
    print("✅ 跨領域測試完成")
    print("=" * 70)

if __name__ == "__main__":
    test_cross_domain()
