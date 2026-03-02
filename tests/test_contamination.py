"""
污染檢測器測試 - 驗證樣本是否超過臨界值
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import json
from src.contamination_detector import ContaminationDetector, ContaminationLevel

def test_clean_data():
    """測試乾淨數據"""
    print("\n" + "="*60)
    print("🧪 測試 1: 乾淨數據")
    print("="*60)
    
    # 產生乾淨數據
    x = np.linspace(0, 10, 100)
    y = 2.5 * x + 1.0
    
    detector = ContaminationDetector()
    
    print("\n📊 檢測 x 數據:")
    report_x = detector.detect(x, domain='general')
    print(f"  污染等級: {report_x.level.value}")
    print(f"  通過檢驗: {'✅' if report_x.passed else '❌'}")
    print(f"  缺失值: {report_x.missing_ratio:.1%}")
    print(f"  異常值: {report_x.outlier_ratio:.1%}")
    print(f"  噪聲: {report_x.noise_ratio:.1%}")
    print(f"  建議: {report_x.recommendation}")
    
    print("\n📊 檢測 y 數據:")
    report_y = detector.detect(y, domain='general')
    print(f"  污染等級: {report_y.level.value}")
    print(f"  通過檢驗: {'✅' if report_y.passed else '❌'}")

def test_missing_data():
    """測試缺失值數據"""
    print("\n" + "="*60)
    print("🧪 測試 2: 有缺失值的數據")
    print("="*60)
    
    # 產生有缺失值的數據
    x = np.linspace(0, 10, 100)
    # 隨機加入 15% 的缺失值
    mask = np.random.random(100) < 0.15
    x[mask] = np.nan
    
    detector = ContaminationDetector()
    report = detector.detect(x, domain='general')
    
    print(f"\n📊 檢測結果:")
    print(f"  污染等級: {report.level.value}")
    print(f"  通過檢驗: {'✅' if report.passed else '❌'}")
    print(f"  缺失值: {report.missing_ratio:.1%}")
    print(f"  異常值: {report.outlier_ratio:.1%}")
    print(f"  建議: {report.recommendation}")
    
    if report.threshold_breaches:
        print("\n⚠️ 超過臨界值的項目:")
        for breach in report.threshold_breaches:
            print(f"  • {breach}")

def test_outlier_data():
    """測試異常值數據"""
    print("\n" + "="*60)
    print("🧪 測試 3: 有異常值的數據")
    print("="*60)
    
    # 產生有異常值的數據
    x = np.random.normal(0, 1, 100)
    # 加入 5 個異常值
    x[:5] = [10, -10, 12, -12, 15]
    
    detector = ContaminationDetector()
    report = detector.detect(x, domain='general')
    
    print(f"\n📊 檢測結果:")
    print(f"  污染等級: {report.level.value}")
    print(f"  通過檢驗: {'✅' if report.passed else '❌'}")
    print(f"  異常值: {report.outlier_ratio:.1%}")
    print(f"  建議: {report.recommendation}")

def test_noisy_data():
    """測試高噪聲數據"""
    print("\n" + "="*60)
    print("🧪 測試 4: 高噪聲數據")
    print("="*60)
    
    # 產生高噪聲數據
    x = np.linspace(0, 10, 100)
    noise = np.random.normal(0, 5, 100)  # 高噪聲
    y = 2.5 * x + 1.0 + noise
    
    detector = ContaminationDetector()
    report = detector.detect(y, domain='general')
    
    print(f"\n📊 檢測結果:")
    print(f"  污染等級: {report.level.value}")
    print(f"  通過檢驗: {'✅' if report.passed else '❌'}")
    print(f"  噪聲: {report.noise_ratio:.1%}")
    print(f"  建議: {report.recommendation}")

def test_duplicate_data():
    """測試重複值數據"""
    print("\n" + "="*60)
    print("🧪 測試 5: 重複值數據")
    print("="*60)
    
    # 產生有重複值的數據
    x = np.array([1, 2, 3, 3, 3, 4, 5, 5, 5, 5, 6, 7, 8, 8, 8])
    
    detector = ContaminationDetector()
    report = detector.detect(x, domain='general')
    
    print(f"\n📊 檢測結果:")
    print(f"  污染等級: {report.level.value}")
    print(f"  通過檢驗: {'✅' if report.passed else '❌'}")
    print(f"  重複值: {report.duplicate_ratio:.1%}")
    print(f"  建議: {report.recommendation}")

def test_domain_specific():
    """測試領域特定臨界值"""
    print("\n" + "="*60)
    print("🧪 測試 6: 不同領域的臨界值")
    print("="*60)
    
    # 產生相同的測試數據
    x = np.random.normal(0, 1, 50)
    x[:3] = [5, -5, 6]  # 加入異常值
    x[40:45] = np.nan   # 加入缺失值
    
    domains = ['general', 'electrical', 'quantum', 'healthcare', 'financial']
    
    print("\n📊 相同數據在不同領域的檢測結果:")
    detector = ContaminationDetector()
    
    for domain in domains:
        report = detector.detect(x, domain=domain)
        status = "✅" if report.passed else "❌"
        print(f"  {domain:12}: {status} 等級={report.level.value:8} 異常={report.outlier_ratio:.1%} 缺失={report.missing_ratio:.1%}")

def test_critical_threshold():
    """測試臨界值超過"""
    print("\n" + "="*60)
    print("🧪 測試 7: 超過臨界值的數據")
    print("="*60)
    
    # 產生嚴重污染的數據
    x = np.random.normal(0, 1, 5)  # 樣本太少
    x = np.append(x, [np.nan, np.nan, np.nan, np.nan])  # 40% 缺失
    x = np.append(x, [100, -100, 200])  # 異常值
    
    detector = ContaminationDetector()
    report = detector.detect(x, domain='general')
    
    print(f"\n📊 檢測結果:")
    print(f"  污染等級: {report.level.value}")
    print(f"  通過檢驗: {'✅' if report.passed else '❌'}")
    print(f"  樣本數: {len(x)}")
    print(f"  缺失值: {report.missing_ratio:.1%}")
    print(f"  異常值: {report.outlier_ratio:.1%}")
    
    if report.threshold_breaches:
        print("\n🚨 超過臨界值的項目:")
        for breach in report.threshold_breaches:
            print(f"  • {breach}")
    
    print(f"\n📋 建議: {report.recommendation}")

if __name__ == "__main__":
    print("="*60)
    print("🔬 污染檢測器完整測試")
    print("="*60)
    
    test_clean_data()
    test_missing_data()
    test_outlier_data()
    test_noisy_data()
    test_duplicate_data()
    test_domain_specific()
    test_critical_threshold()
    
    print("\n" + "="*60)
    print("✅ 測試完成")
    print("="*60)
