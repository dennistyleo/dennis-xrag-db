#!/usr/bin/env python3
"""
完整的XRAG Core導入測試
"""

import sys
import importlib

def test_import(module_name, class_name=None):
    """測試導入模塊"""
    try:
        if class_name:
            module = importlib.import_module(f"src.xrag_core.{module_name}")
            getattr(module, class_name)
            print(f"✅ {module_name}.{class_name} 導入成功")
        else:
            importlib.import_module(f"src.xrag_core.{module_name}")
            print(f"✅ {module_name} 導入成功")
        return True
    except Exception as e:
        print(f"❌ {module_name} 導入失敗: {e}")
        return False

def main():
    """主函數"""
    print("="*60)
    print("XRAG Core 完整導入測試")
    print("="*60)
    
    # 測試Python版本
    print(f"\n🐍 Python 版本: {sys.version}")
    
    # 測試必要套件
    print("\n📦 必要套件:")
    packages = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("statsmodels", "statsmodels"),
    ]
    
    for package_name, import_name in packages:
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, "__version__", "unknown")
            print(f"   ✅ {package_name} {version}")
        except ImportError as e:
            print(f"   ❌ {package_name}: {e}")
    
    # 測試XRAG模塊
    print("\n🔧 XRAG Core 模塊:")
    
    modules = [
        ("__init__", None),
        ("stage1_characterization", "ProblemCharacterizer"),
        ("stage2_generation", "PathwayGenerator"),
        ("stage3_feasibility", "FeasibilityAssessor"),
        ("stage4_calibration", "ParameterCalibrator"),
        ("stage5_explainability", "ExplainabilityEngine"),
        ("xrag_engine", "XRAGEngine"),
    ]
    
    all_success = True
    for module_name, class_name in modules:
        if not test_import(module_name, class_name):
            all_success = False
    
    # 最終結果
    print("\n" + "="*60)
    if all_success:
        print("✅ 所有模塊導入成功！")
    else:
        print("⚠️  部分模塊導入失敗")
    print("="*60)

if __name__ == "__main__":
    main()
