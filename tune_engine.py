#!/usr/bin/env python3
"""
XRAG 引擎參數調整測試
"""

import numpy as np
import time
from src.xrag_core import XRAGEngine

def test_engine_configs():
    """測試不同的引擎配置"""
    
    print("="*70)
    print("🚀 XRAG 引擎參數調整測試")
    print("="*70)
    
    # 創建測試信號
    t = np.linspace(0, 10, 500)
    signal = 10 * np.exp(-0.5 * t) + 0.1 * np.random.randn(500)
    
    # 不同的配置
    configs = [
        {
            "name": "默認配置",
            "calibration_method": "auto",
            "strict_filtering": True,
            "max_candidates": 10
        },
        {
            "name": "快速模式 (較少候選)",
            "calibration_method": "approximate",
            "strict_filtering": False,
            "max_candidates": 3
        },
        {
            "name": "精確模式 (MCMC)",
            "calibration_method": "mcmc",
            "strict_filtering": True,
            "max_candidates": 5
        },
        {
            "name": "優化模式",
            "calibration_method": "optimization",
            "strict_filtering": True,
            "max_candidates": 8
        },
        {
            "name": "寬鬆過濾",
            "calibration_method": "auto",
            "strict_filtering": False,
            "max_candidates": 15
        }
    ]
    
    results = []
    
    for config in configs:
        print(f"\n{'='*50}")
        print(f"測試: {config['name']}")
        print(f"{'='*50}")
        
        # 初始化引擎
        engine = XRAGEngine(
            calibration_method=config['calibration_method'],
            strict_filtering=config['strict_filtering'],
            max_candidates_to_calibrate=config['max_candidates'],
            verbose=False
        )
        
        # 計時
        start = time.time()
        
        # 運行
        result = engine.run(signal, t)
        
        elapsed = time.time() - start
        
        if result.success and result.best_model_idx >= 0:
            best = result.calibrated_models[result.best_model_idx]
            
            print(f"✅ 成功!")
            print(f"   運行時間: {elapsed:.2f} 秒")
            print(f"   候選模型: {len(result.candidates)}")
            print(f"   可行模型: {len(result.feasible_hypotheses)}")
            print(f"   校準模型: {len([m for m in result.calibrated_models if m])}")
            print(f"   最佳模型: {best.hypothesis_name}")
            print(f"   R²: {best.r2:.4f}")
            print(f"   MAE: {best.mae:.4f}")
            
            results.append({
                "config": config['name'],
                "time": elapsed,
                "r2": best.r2,
                "mae": best.mae,
                "n_candidates": len(result.candidates),
                "n_feasible": len(result.feasible_hypotheses),
                "n_calibrated": len([m for m in result.calibrated_models if m]),
                "best_model": best.hypothesis_name
            })
        else:
            print(f"❌ 失敗: {result.error}")
    
    # 顯示比較結果
    print("\n" + "="*70)
    print("📊 配置比較結果")
    print("="*70)
    
    print(f"\n{'配置':<20} {'時間(秒)':<10} {'R²':<8} {'MAE':<8} {'最佳模型'}")
    print("-"*70)
    
    for r in results:
        print(f"{r['config']:<20} {r['time']:<10.2f} {r['r2']:<8.4f} {r['mae']:<8.4f} {r['best_model']}")
    
    # 建議
    print("\n📝 建議:")
    print("   • 如果需要快速結果: 使用 '快速模式'")
    print("   • 如果需要高精度: 使用 '精確模式' (需要安裝 pymc3)")
    print("   • 如果需要平衡: 使用 '默認配置'")
    print("   • 如果數據質量差: 使用 '寬鬆過濾'")

def test_different_domains():
    """測試不同領域的影響"""
    
    print("\n" + "="*70)
    print("🌍 不同領域測試")
    print("="*70)
    
    # 創建一個通用信號
    t = np.linspace(0, 10, 300)
    signal = 10 * np.exp(-0.5 * t) + 0.1 * np.random.randn(300)
    
    engine = XRAGEngine(verbose=False)
    
    domains = ["general", "thermal", "aging", "electrical", "mechanical"]
    
    print(f"\n{'領域':<15} {'最佳模型':<30} {'R²':<8}")
    print("-"*55)
    
    for domain in domains:
        result = engine.run(signal, t, domain=domain)
        if result.success and result.best_model_idx >= 0:
            best = result.calibrated_models[result.best_model_idx]
            print(f"{domain:<15} {best.hypothesis_name:<30} {best.r2:<8.4f}")

def test_data_quality_impact():
    """測試數據質量的影響"""
    
    print("\n" + "="*70)
    print("📈 數據質量影響測試")
    print("="*70)
    
    t = np.linspace(0, 10, 200)
    engine = XRAGEngine(verbose=False)
    
    # 不同 SNR 水平
    snr_levels = [30, 20, 10, 5, 0]
    
    print(f"\n{'SNR (dB)':<10} {'最佳模型':<30} {'R²':<8} {'可行模型':<10}")
    print("-"*60)
    
    for snr in snr_levels:
        # 根據 SNR 調整噪聲
        noise_std = 10 / (10 ** (snr/20))
        signal = 10 * np.exp(-0.5 * t) + noise_std * np.random.randn(200)
        
        result = engine.run(signal, t)
        
        if result.success and result.best_model_idx >= 0:
            best = result.calibrated_models[result.best_model_idx]
            print(f"{snr:<10} {best.hypothesis_name:<30} {best.r2:<8.4f} {len(result.feasible_hypotheses):<10}")

def main():
    """主函數"""
    
    # 測試不同配置
    test_engine_configs()
    
    # 測試不同領域
    test_different_domains()
    
    # 測試數據質量影響
    test_data_quality_impact()
    
    print("\n" + "="*70)
    print("✅ 參數調整測試完成!")
    print("="*70)

if __name__ == "__main__":
    main()
