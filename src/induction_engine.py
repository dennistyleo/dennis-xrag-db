import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
import json
from datetime import datetime
import re

class InductionEngine:
    def __init__(self, db_interface):
        self.db = db_interface
        self.methods = [
            {'name': '線性回歸', 'func': self._linear_regression, 'min_samples': 5},
            {'name': '多項式回歸', 'func': self._polynomial_regression, 'min_samples': 10},
            {'name': '指數回歸', 'func': self._exponential_regression, 'min_samples': 5},
            {'name': '冪律回歸', 'func': self._power_law_regression, 'min_samples': 5}
        ]
    
    def induce(self, data, context=None):
        """從數據歸納公理"""
        if not data or 'x' not in data or 'y' not in data:
            return {'error': '需要提供 x 和 y 數據'}
        
        x = np.array(data['x']).reshape(-1, 1)
        y = np.array(data['y'])
        
        results = []
        
        for method in self.methods:
            if len(x) < method['min_samples']:
                continue
                
            try:
                candidate = method['func'](x, y, data)
                if candidate:
                    # 驗證候選公理
                    validation = self._validate(candidate, x, y)
                    results.append({
                        'method': method['name'],
                        'candidate': candidate,
                        'validation': validation,
                        'confidence': validation['r2']
                    })
            except Exception as e:
                continue
        
        # 按可信度排序
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        # 如果有高可信度結果，存入候選庫
        if results and results[0]['confidence'] > 0.8:
            self._save_candidate(results[0]['candidate'])
        
        return results
    
    def _linear_regression(self, x, y, data):
        """線性回歸 y = ax + b"""
        model = LinearRegression().fit(x, y)
        
        return {
            'form': f"y = {model.coef_[0]:.4f}·x + {model.intercept_:.4f}",
            'params': {'slope': float(model.coef_[0]), 'intercept': float(model.intercept_)},
            'variables': data.get('var_names', ['x', 'y']),
            'type': 'linear'
        }
    
    def _polynomial_regression(self, x, y, data, degree=2):
        """多項式回歸 y = a₀ + a₁x + a₂x²"""
        model = make_pipeline(
            PolynomialFeatures(degree),
            LinearRegression()
        ).fit(x, y)
        
        coefs = model.named_steps['linearregression'].coef_
        intercept = model.named_steps['linearregression'].intercept_
        
        terms = [f"{intercept:.4f}"]
        for i in range(1, len(coefs)):
            if abs(coefs[i]) > 1e-6:
                if i == 1:
                    terms.append(f"{coefs[i]:.4f}·x")
                else:
                    terms.append(f"{coefs[i]:.4f}·x^{i}")
        
        return {
            'form': "y = " + " + ".join(terms),
            'params': {'coeffs': coefs.tolist(), 'intercept': float(intercept)},
            'variables': data.get('var_names', ['x', 'y']),
            'type': 'polynomial',
            'degree': degree
        }
    
    def _exponential_regression(self, x, y, data):
        """指數回歸 y = a·e^(b·x)"""
        log_y = np.log(np.abs(y) + 1e-10)
        model = LinearRegression().fit(x, log_y)
        
        a = np.exp(model.intercept_)
        b = model.coef_[0]
        
        return {
            'form': f"y = {a:.4f}·e^({b:.4f}·x)",
            'params': {'a': float(a), 'b': float(b)},
            'variables': data.get('var_names', ['x', 'y']),
            'type': 'exponential'
        }
    
    def _power_law_regression(self, x, y, data):
        """冪律回歸 y = a·x^b"""
        log_x = np.log(np.abs(x) + 1e-10).reshape(-1, 1)
        log_y = np.log(np.abs(y) + 1e-10)
        
        model = LinearRegression().fit(log_x, log_y)
        
        a = np.exp(model.intercept_)
        b = model.coef_[0]
        
        return {
            'form': f"y = {a:.4f}·x^{b:.4f}",
            'params': {'a': float(a), 'b': float(b)},
            'variables': data.get('var_names', ['x', 'y']),
            'type': 'power_law'
        }
    
    def _validate(self, candidate, x, y):
        """驗證候選公理的準確度"""
        try:
            # 這裡簡化驗證，用 R² 來評估
            y_pred = self._predict(candidate, x)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            return {
                'r2': float(r2),
                'rmse': float(np.sqrt(np.mean((y - y_pred) ** 2)))
            }
        except:
            return {'r2': 0, 'rmse': float('inf')}
    
    def _predict(self, candidate, x):
        """根據候選公理預測 y 值"""
        form = candidate['form']
        x_flat = x.flatten()
        
        if 'linear' in candidate.get('type', ''):
            return candidate['params']['slope'] * x_flat + candidate['params']['intercept']
        elif 'exponential' in candidate.get('type', ''):
            return candidate['params']['a'] * np.exp(candidate['params']['b'] * x_flat)
        elif 'power_law' in candidate.get('type', ''):
            return candidate['params']['a'] * (x_flat ** candidate['params']['b'])
        else:
            return np.zeros_like(x_flat)
    
    def _save_candidate(self, candidate):
        """儲存候選公理（待審查）"""
        # 這裡可以存到一個候選表，或直接存入 unknown_candidates
        pass
