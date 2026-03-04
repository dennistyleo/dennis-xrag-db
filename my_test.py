# 2. 貼上這段測試代碼
from src.xrag_core import XRAGEngine
import numpy as np

# 創建信號
t = np.linspace(0, 5, 200)
signal = 10 * np.exp(-0.5 * t) + 0.1 * np.random.randn(200)

# 初始化引擎
engine = XRAGEngine()

# 運行分析
result = engine.run(signal, t)

# 查看結果
print(result.report.executive_summary)
