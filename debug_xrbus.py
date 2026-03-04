import sys
import os
print(f"Python 路徑: {sys.executable}")
print(f"當前目錄: {os.getcwd()}")
print("\n模組搜尋路徑:")
for p in sys.path:
    print(f"  {p}")

print("\n嘗試載入 xrbus.core...")
try:
    from src.xrbus.core import XRBUS, XRFrame
    print("✅ 成功載入 xrbus.core")
    
    # 檢查 XRFrame 的 __init__ 方法
    print("\n檢查 XRFrame 的 _compute_checksum 方法:")
    import inspect
    source = inspect.getsource(XRFrame._compute_checksum)
    print(source)
    
    # 檢查 json 是否在 globals 中
    print("\n檢查 XRFrame 的 globals:")
    print("  'json' in globals():", 'json' in globals())
    
except Exception as e:
    print(f"❌ 載入失敗: {e}")
    import traceback
    traceback.print_exc()
