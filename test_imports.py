#!/usr/bin/env python3
"""
測試所有模塊的導入
"""

print("測試 XRAG Core 模塊導入...")

try:
    from src.xrag_core.stage1_characterization import ProblemCharacterizer
    print("✅ stage1_characterization 導入成功")
except Exception as e:
    print(f"❌ stage1_characterization 導入失敗: {e}")

try:
    from src.xrag_core.stage2_generation import PathwayGenerator
    print("✅ stage2_generation 導入成功")
except Exception as e:
    print(f"❌ stage2_generation 導入失敗: {e}")

try:
    from src.xrag_core.stage3_feasibility import FeasibilityAssessor
    print("✅ stage3_feasibility 導入成功")
except Exception as e:
    print(f"❌ stage3_feasibility 導入失敗: {e}")

try:
    from src.xrag_core.stage4_calibration import ParameterCalibrator
    print("✅ stage4_calibration 導入成功")
except Exception as e:
    print(f"❌ stage4_calibration 導入失敗: {e}")

try:
    from src.xrag_core.stage5_explainability import ExplainabilityEngine
    print("✅ stage5_explainability 導入成功")
except Exception as e:
    print(f"❌ stage5_explainability 導入失敗: {e}")

print("\n測試完成！")
