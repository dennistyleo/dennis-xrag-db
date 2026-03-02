"""
XRAG Matching Engine Module
"""

import json
import re
from difflib import SequenceMatcher
from typing import Dict, List

class XRAGMatcher:
    def __init__(self, db_interface):
        self.db = db_interface
        self.match_methods = [
            {'id': 'syntax', 'name': 'Syntax Tree Matching', 'weight': 0.40, 'threshold': 0.5},
            {'id': 'variables', 'name': 'Variable Signature Matching', 'weight': 0.40, 'threshold': 0.4},
            {'id': 'boundary', 'name': 'Boundary Matching', 'weight': 0.20, 'threshold': 0.3}
        ]
    
    def match_candidate(self, candidate: Dict, threshold: float = 0.5, top_k: int = 3) -> List[Dict]:
        axioms = self.db.search_axioms({'domain': candidate.get('domain', '')})
        matches = []
        
        for axiom in axioms:
            scores = self._calculate_similarity(candidate, axiom)
            total = sum(scores.get(m['id'], 0) * m['weight'] for m in self.match_methods)
            
            if total >= threshold:
                matches.append({
                    'axiom_id': axiom['id'],
                    'axiom_name': axiom['name'],
                    'domain': axiom['domain'],
                    'similarity_score': round(total, 3),
                    'details': scores
                })
        
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        return matches[:top_k]
    
    def _calculate_similarity(self, candidate: Dict, axiom: Dict) -> Dict:
        scores = {}
        
        # 解析
        cand_core = candidate.get('computational_core', {})
        cand_input = candidate.get('input_signature', {})
        
        axiom_core = self._parse_json(axiom.get('computational_core', '{}'))
        axiom_input = self._parse_json(axiom.get('input_signature', '{}'))
        
        # 語法相似度 (比較 type)
        cand_type = cand_core.get('type', '')
        ax_type = axiom_core.get('type', '')
        scores['syntax'] = 0.8 if cand_type and ax_type and cand_type == ax_type else 0.0
        
        # 變數相似度 (放寬版本)
        cand_vars = set(cand_input.get('required_vars', []))
        ax_vars = set(axiom_input.get('required_vars', []))
        
        if cand_vars and ax_vars:
            # 特殊處理：ΔT 可以視為 T₁,T₂ 的組合
            if 'ΔT' in ax_vars and ('T₁' in cand_vars or 'T₂' in cand_vars):
                scores['variables'] = 0.7
            else:
                intersection = len(cand_vars.intersection(ax_vars))
                union = len(cand_vars.union(ax_vars))
                scores['variables'] = intersection / union if union > 0 else 0.0
        else:
            scores['variables'] = 0.0
        
        # 邊界相似度 (預設)
        scores['boundary'] = 0.6
        
        return scores
    
    def _parse_json(self, field):
        if isinstance(field, str):
            try:
                return json.loads(field)
            except:
                return {}
        return field if isinstance(field, dict) else {}
