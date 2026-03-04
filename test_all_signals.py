#!/usr/bin/env python3
"""
XRAG - 測試多種信號類型
"""

import numpy as np
from src.xrag_core import XRAGEngine
import json
from datetime import datetime

def print_separator(title):
    """打印分隔線"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

# 初始化引擎
print("🚀 初始化 XRAG Engine...")
engine = XRAGEngine(verbose=False)  # 設為 False 減少輸出

# 創建時間向量
t = np.linspace(0, 10, 500)

# === 1. 指數衰減信號 ===
print_separator("測試 1: 指數衰減信號")
signal1 = 10 * np.exp(-0.5 * t) + 0.1 * np.random.randn(500)
result1 = engine.run(signal1, t)
print(f"✅ 最佳模型: {result1.calibrated_models[result1.best_model_idx].hypothesis_name}")
print(f"   R² = {result1.calibrated_models[result1.best_model_idx].r2:.4f}")
print(f"   參數: {result1.calibrated_models[result1.best_model_idx].parameters}")

# === 2. 正弦波信號 ===
print_separator("測試 2: 正弦波信號")
signal2 = 5 * np.sin(2 * np.pi * 2 * t) + 0.2 * np.random.randn(500)
result2 = engine.run(signal2, t)
print(f"✅ 最佳模型: {result2.calibrated_models[result2.best_model_idx].hypothesis_name}")
print(f"   R² = {result2.calibrated_models[result2.best_model_idx].r2:.4f}")

# === 3. 線性趨勢信號 ===
print_separator("測試 3: 線性趨勢信號")
signal3 = 2 * t + 10 + np.random.randn(500)
result3 = engine.run(signal3, t)
print(f"✅ 最佳模型: {result3.calibrated_models[result3.best_model_idx].hypothesis_name}")
print(f"   R² = {result3.calibrated_models[result3.best_model_idx].r2:.4f}")

# === 4. 二次曲線信號 ===
print_separator("測試 4: 二次曲線信號")
signal4 = 0.5 * t**2 - 3 * t + 10 + 0.5 * np.random.randn(500)
result4 = engine.run(signal4, t)
print(f"✅ 最佳模型: {result4.calibrated_models[result4.best_model_idx].hypothesis_name}")
print(f"   R² = {result4.calibrated_models[result4.best_model_idx].r2:.4f}")

# === 5. 隨機噪聲信號 ===
print_separator("測試 5: 隨機噪聲信號")
signal5 = np.random.randn(500)
result5 = engine.run(signal5, np.arange(500))
print(f"✅ 最佳模型: {result5.calibrated_models[result5.best_model_idx].hypothesis_name if result5.best_model_idx >= 0 else '無'}")
print(f"   R² = {result5.calibrated_models[result5.best_model_idx].r2:.4f if result5.best_model_idx >= 0 else 'N/A'}")

# === 6. 不同領域測試 ===
print_separator("測試 6: 熱力學領域")
# 模擬溫度冷卻數據
t_thermal = np.linspace(0, 60, 300)  # 60分鐘
T_env = 20  # 環境溫度 20°C
T_initial = 100  # 初始溫度 100°C
k = 0.1  # 冷卻常數
signal_thermal = T_env + (T_initial - T_env) * np.exp(-k * t_thermal) + 0.5 * np.random.randn(300)
result_thermal = engine.run(signal_thermal, t_thermal, domain="thermal")
print(f"✅ 最佳模型 (thermal): {result_thermal.calibrated_models[result_thermal.best_model_idx].hypothesis_name}")
print(f"   R² = {result_thermal.calibrated_models[result_thermal.best_model_idx].r2:.4f}")

# === 7. 老化測試領域 ===
print_separator("測試 7: 老化測試領域")
# 模擬 Arrhenius 老化數據
T_aging = np.linspace(300, 400, 200)  # 溫度 (K)
Ea = 0.85  # 活化能 (eV)
k_B = 8.617e-5  # Boltzmann 常數
L0 = 1000  # 初始壽命
signal_aging = L0 * np.exp(-Ea / (k_B * T_aging)) + 5 * np.random.randn(200)
result_aging = engine.run(signal_aging, T_aging, domain="aging")
print(f"✅ 最佳模型 (aging): {result_aging.calibrated_models[result_aging.best_model_idx].hypothesis_name}")
print(f"   R² = {result_aging.calibrated_models[result_aging.best_model_idx].r2:.4f}")

# === 總結 ===
print_separator("測試總結")
print(f"""
測試結果匯總:
1. 指數衰減: {result1.calibrated_models[result1.best_model_idx].hypothesis_name} (R²={result1.calibrated_models[result1.best_model_idx].r2:.3f})
2. 正弦波: {result2.calibrated_models[result2.best_model_idx].hypothesis_name} (R²={result2.calibrated_models[result2.best_model_idx].r2:.3f})
3. 線性趨勢: {result3.calibrated_models[result3.best_model_idx].hypothesis_name} (R²={result3.calibrated_models[result3.best_model_idx].r2:.3f})
4. 二次曲線: {result4.calibrated_models[result4.best_model_idx].hypothesis_name} (R²={result4.calibrated_models[result4.best_model_idx].r2:.3f})
5. 隨機噪聲: {result5.calibrated_models[result5.best_model_idx].hypothesis_name if result5.best_model_idx >= 0 else '無'} (R²={result5.calibrated_models[result5.best_model_idx].r2:.3f if result5.best_model_idx >= 0 else 'N/A'})
6. 熱力學: {result_thermal.calibrated_models[result_thermal.best_model_idx].hypothesis_name} (R²={result_thermal.calibrated_models[result_thermal.best_model_idx].r2:.3f})
7. 老化: {result_aging.calibrated_models[result_aging.best_model_idx].hypothesis_name} (R²={result_aging.calibrated_models[result_aging.best_model_idx].r2:.3f})
""")
