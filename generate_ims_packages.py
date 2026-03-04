#!/usr/bin/env python3
"""
生成 IMS 凍結包 - 給 Alex 的驅動程序
"""

import numpy as np
import json
import hashlib
from datetime import datetime
import os
from src.xrag_core import XRAGEngine

def create_freeze_package(result, signal_type, description, package_id=None):
    """創建符合 Alex 驅動程序格式的凍結包"""
    
    if not result.success or result.best_model_idx < 0:
        return None
    
    best_model = result.calibrated_models[result.best_model_idx]
    
    # 生成 package_id
    if package_id is None:
        package_id = f"ims_xrag_{signal_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 創建凍結包
    package = {
        "message_type": "frozen.axiom",
        "package_id": package_id,
        "created_at": datetime.now().isoformat(),
        "producer": {
            "name": "xrag_core",
            "version": "2.0.0"
        },
        "payload": {
            "record_type": "analysis_report",
            "record_id": f"xrag_{signal_type}",
            "record": {
                "signal_type": signal_type,
                "description": description,
                "best_model": {
                    "name": best_model.hypothesis_name,
                    "formulation": best_model.formulation,
                    "r2": best_model.r2,
                    "mae": best_model.mae,
                    "parameters": best_model.parameters,
                    "parameter_uncertainty": best_model.parameter_hdi
                },
                "summary": result.report.executive_summary if result.report else "No summary available",
                "recommendations": result.report.recommendations if result.report else []
            }
        },
        "provenance": {
            "source": "xrag_core",
            "chain": result.report.provenance_chain if result.report else [],
            "timestamp": datetime.now().isoformat()
        },
        "protocol": {"frozen": True},
        "comparator": {"frozen": True},
        "bridge_rules": {"frozen": True}
    }
    
    # 添加完整性哈希
    package_str = json.dumps(package, sort_keys=True, default=str)
    package["integrity"] = {
        "hash_alg": "sha256",
        "package_hash": hashlib.sha256(package_str.encode()).hexdigest(),
        "verification_code": hashlib.sha256(package_str.encode()).hexdigest()[:16]
    }
    
    return package

def main():
    """生成多個測試凍結包"""
    
    print("="*70)
    print("📦 IMS 凍結包生成器")
    print("="*70)
    
    # 初始化引擎
    print("\n🛠️  初始化 XRAG Engine...")
    engine = XRAGEngine(verbose=False)
    
    # 創建輸出目錄
    os.makedirs("ims_packages", exist_ok=True)
    
    # 定義測試案例
    test_cases = [
        {
            "name": "exponential_decay",
            "description": "指數衰減信號 - 應該 ACCEPT",
            "func": lambda t: 10 * np.exp(-0.5 * t) + 0.1 * np.random.randn(len(t)),
            "domain": "general"
        },
        {
            "name": "sine_wave",
            "description": "正弦波信號 - 應該 ACCEPT",
            "func": lambda t: 5 * np.sin(2 * np.pi * 2 * t) + 0.2 * np.random.randn(len(t)),
            "domain": "general"
        },
        {
            "name": "linear_trend",
            "description": "線性趨勢 - 應該 ACCEPT",
            "func": lambda t: 2 * t + 10 + np.random.randn(len(t)),
            "domain": "general"
        },
        {
            "name": "random_walk",
            "description": "隨機漫步 - 可能 REFUSE",
            "func": lambda t: np.cumsum(0.1 * np.random.randn(len(t))),
            "domain": "general"
        },
        {
            "name": "thermal_cooling",
            "description": "熱力學冷卻 - 應該 ACCEPT (thermal domain)",
            "func": lambda t: 20 + 80 * np.exp(-0.1 * t) + 0.5 * np.random.randn(len(t)),
            "domain": "thermal"
        },
        {
            "name": "arrhenius_aging",
            "description": "Arrhenius 老化 - 應該 ACCEPT (aging domain)",
            "func": lambda t: 1000 * np.exp(-0.85 / (8.617e-5 * t)) + 5 * np.random.randn(len(t)),
            "domain": "aging",
            "t_range": (300, 400)  # 溫度範圍 (K)
        }
    ]
    
    packages = []
    
    # 生成每個測試案例
    for case in test_cases:
        print(f"\n📊 處理: {case['name']}")
        print(f"   描述: {case['description']}")
        
        # 生成時間向量
        if 't_range' in case:
            t = np.linspace(case['t_range'][0], case['t_range'][1], 300)
        else:
            t = np.linspace(0, 10, 300)
        
        # 生成信號
        signal = case['func'](t)
        
        # 運行 XRAG
        print(f"   運行 XRAG 分析...")
        result = engine.run(signal, t, domain=case['domain'])
        
        if result.success and result.best_model_idx >= 0:
            # 創建凍結包
            package = create_freeze_package(
                result, 
                case['name'], 
                case['description']
            )
            
            if package:
                # 保存到文件
                filename = f"ims_packages/{case['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(package, f, indent=2)
                
                print(f"   ✅ 已保存: {filename}")
                print(f"      最佳模型: {package['payload']['record']['best_model']['name']}")
                print(f"      R²: {package['payload']['record']['best_model']['r2']:.3f}")
                print(f"      哈希: {package['integrity']['verification_code']}")
                
                packages.append({
                    "name": case['name'],
                    "filename": filename,
                    "package_id": package['package_id'],
                    "hash": package['integrity']['verification_code']
                })
        else:
            print(f"   ❌ 分析失敗")
    
    # 生成摘要文件
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_packages": len(packages),
        "packages": packages,
        "instructions": "使用 Alex 的驅動程序測試: python alex_driver.py --package <filename>"
    }
    
    summary_file = f"ims_packages/summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "="*70)
    print(f"📦 完成! 生成了 {len(packages)} 個凍結包")
    print(f"   摘要文件: {summary_file}")
    print("="*70)
    print("\n要測試 Alex 的驅動程序:")
    print("  python alex_driver.py --package ims_packages/exponential_decay_*.json")
    print("  python alex_driver.py --package ims_packages/sine_wave_*.json")
    print("  python alex_driver.py --package ims_packages/thermal_cooling_*.json")

if __name__ == "__main__":
    main()
