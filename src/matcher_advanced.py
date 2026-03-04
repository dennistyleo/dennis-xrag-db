import numpy as np
from difflib import SequenceMatcher
import json
import re

class AdvancedMatcher:
    def __init__(self, db_interface):
        self.db = db_interface
        self.weights = {
            'syntax': 0.25,
            'variables': 0.20,
            'causal': 0.15,
            'numeric': 0.15,
            'analogy': 0.15,
            'semantic': 0.10
        }
    
    def match(self, candidate, threshold=0.5, top_k=5):
        """多層次匹配主函數"""
        # 處理 domain 為 None 的情況
        domain = candidate.get('domain')
        if domain is None:
            # 如果 domain 是 None，搜尋所有領域
            axioms = self.db.search_axioms({})
        else:
            axioms = self.db.search_axioms({'domain': domain})
            
        results = []
        
        for axiom in axioms:
            scores = {}
            
            # 各層次計算
            scores['syntax'] = self._syntax_similarity(candidate, axiom)
            scores['variables'] = self._variable_similarity(candidate, axiom)
            scores['causal'] = self._causal_similarity(candidate, axiom)
            scores['numeric'] = self._numeric_similarity(candidate, axiom)
            scores['analogy'] = self._analogy_similarity(candidate, axiom)
            scores['semantic'] = self._semantic_similarity(candidate, axiom)
            
            # 加權總分
            total = sum(scores[k] * self.weights[k] for k in scores if k in self.weights)
            
            if total >= threshold:
                results.append({
                    'axiom_id': axiom['id'],
                    'name': axiom['name'],
                    'domain': axiom['domain'],
                    'score': round(total, 3),
                    'details': {k: round(v, 3) for k, v in scores.items() if v > 0}
                })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _syntax_similarity(self, c, a):
        """語法樹相似度"""
        c_form = self._get_form(c)
        a_form = self._get_form(a)
        
        # 如果任何一個公式為空，返回0
        if not c_form or not a_form:
            return 0
        
        # 確保是字串
        c_form = str(c_form)
        a_form = str(a_form)
        
        # 如果字串太短，直接比較
        if len(c_form) < 3 or len(a_form) < 3:
            return 1.0 if c_form == a_form else 0.0
        
        try:
            return SequenceMatcher(None, c_form, a_form).ratio()
        except:
            return 0
    
    def _variable_similarity(self, c, a):
        """變數簽章相似度"""
        c_vars = set(self._get_vars(c))
        a_vars = set(self._get_vars(a))
        if not c_vars or not a_vars:
            return 0
        return len(c_vars & a_vars) / len(c_vars | a_vars)
    
    def _causal_similarity(self, c, a):
        """因果結構相似度"""
        c_causes = self._extract_causes(c)
        a_causes = self._extract_causes(a)
        return self._jaccard(c_causes, a_causes)
    
    def _numeric_similarity(self, c, a):
        """數值範圍相似度"""
        c_range = self._get_range(c)
        a_range = self._get_range(a)
        return self._range_overlap(c_range, a_range)
    
    def _analogy_similarity(self, c, a):
        """類比推理相似度"""
        c_domain = c.get('domain', '')
        a_domain = a.get('domain', '')
        
        # 如果 domain 相同，不算類比
        if c_domain == a_domain:
            return 0
        
        # 常見類比對
        analogies = {
            ('electrical', 'thermal'): 0.8,
            ('thermal', 'electrical'): 0.8,
            ('mechanical', 'electrical'): 0.7,
            ('fluid', 'thermal'): 0.6,
            ('quantum', 'semiconductor'): 0.5
        }
        return analogies.get((c_domain, a_domain), 0)
    
    def _semantic_similarity(self, c, a):
        """語義嵌入相似度（使用關鍵詞）"""
        c_keywords = set(self._extract_keywords(c))
        a_keywords = set(self._extract_keywords(a))
        return self._jaccard(c_keywords, a_keywords)
    
    def _get_form(self, axiom):
        """從公理中提取公式"""
        if not axiom:
            return ''
        core = axiom.get('computational_core', {})
        if isinstance(core, str):
            try:
                core = json.loads(core)
            except:
                return ''
        if not core:
            return ''
        form = core.get('form', '')
        return str(form) if form else ''
    
    def _get_vars(self, axiom):
        """提取變數"""
        if not axiom:
            return []
        vars_str = axiom.get('xr_variables', '')
        if isinstance(vars_str, str):
            return [v.strip() for v in vars_str.split(',') if v.strip()]
        return []
    
    def _get_range(self, axiom):
        """提取數值範圍（簡化版）"""
        if not axiom:
            return {}
        
        boundary = axiom.get('boundary_conditions', {})
        if isinstance(boundary, str):
            try:
                boundary = json.loads(boundary)
            except:
                return {}
        
        if not boundary or not isinstance(boundary, dict):
            return {}
        
        return boundary.get('valid_ranges', {})
    
    def _extract_causes(self, axiom):
        """提取因果關係"""
        if not axiom:
            return set()
        desc = str(axiom.get('description', ''))
        cause_words = {'causes', 'leads to', 'results in', 'due to', 'because', 'therefore'}
        found = set()
        for word in cause_words:
            if word in desc.lower():
                found.add(word)
        return found
    
    def _extract_keywords(self, axiom):
        """提取關鍵詞"""
        if not axiom:
            return set()
        text = str(axiom.get('name', '')) + ' ' + str(axiom.get('description', ''))
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return set(words)
    
    def _jaccard(self, set1, set2):
        """計算 Jaccard 相似度"""
        if not set1 or not set2:
            return 0
        return len(set1 & set2) / len(set1 | set2)
    
    def _range_overlap(self, r1, r2):
        """計算範圍重疊度"""
        if not r1 or not r2:
            return 0.5
        
        if not isinstance(r1, dict) or not isinstance(r2, dict):
            return 0.3
        
        common_vars = set(r1.keys()) & set(r2.keys())
        if not common_vars:
            return 0.3
        
        total_overlap = 0
        for var in common_vars:
            range1 = r1.get(var)
            range2 = r2.get(var)
            
            if isinstance(range1, (list, tuple)) and isinstance(range2, (list, tuple)):
                if len(range1) >= 2 and len(range2) >= 2:
                    try:
                        overlap = min(range1[1], range2[1]) - max(range1[0], range2[0])
                        total_range = max(range1[1], range2[1]) - min(range1[0], range2[0])
                        if total_range > 0:
                            total_overlap += max(0, overlap / total_range)
                    except:
                        continue
        
        return total_overlap / len(common_vars) if common_vars else 0.3
