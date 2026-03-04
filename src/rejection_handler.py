import json
from datetime import datetime

class RejectionHandler:
    def __init__(self, db_interface, matcher):
        self.db = db_interface
        self.matcher = matcher
        self.strategies = [
            {'name': '放寬閾值', 'threshold': 0.3, 'action': self._relax_threshold},
            {'name': '模糊匹配', 'threshold': 0.4, 'action': self._fuzzy_match},
            {'name': '跨領域', 'threshold': 0.35, 'action': self._cross_domain},
            {'name': '類比擴展', 'threshold': 0.4, 'action': self._analogy_search}
        ]
    
    def handle(self, candidate, initial_matches=[]):
        """被拒公理處理流程"""
        result = {
            'candidate': candidate,
            'initial_matches': len(initial_matches),
            'search_path': [],
            'final_match': None,
            'needs_review': True
        }
        
        for strategy in self.strategies:
            matches = strategy['action'](candidate)
            result['search_path'].append({
                'strategy': strategy['name'],
                'matches': len(matches),
                'best': matches[0] if matches else None
            })
            
            if matches:
                result['final_match'] = matches[0]
                result['needs_review'] = False
                result['strategy_used'] = strategy['name']
                break
        
        if result['needs_review']:
            result['unknown_id'] = self._save_unknown(candidate)
            result['message'] = '無匹配，已存入未知通道'
        
        return result
    
    def _relax_threshold(self, candidate):
        """放寬匹配閾值"""
        return self.matcher.match(candidate, threshold=0.3)
    
    def _fuzzy_match(self, candidate):
        """模糊匹配（忽略部分變數）"""
        simplified = candidate.copy()
        vars_list = candidate.get('xr_variables', '').split(',')
        if len(vars_list) > 3:
            simplified['xr_variables'] = ','.join(vars_list[:3])
        return self.matcher.match(simplified, threshold=0.4)
    
    def _cross_domain(self, candidate):
        """跨領域搜尋"""
        candidate['domain'] = None
        return self.matcher.match(candidate, threshold=0.35)
    
    def _analogy_search(self, candidate):
        """類比搜尋"""
        domain = candidate.get('domain', '')
        analogies = {
            'electrical': ['thermal', 'mechanical'],
            'thermal': ['electrical', 'fluid'],
            'mechanical': ['electrical', 'acoustic'],
            'fluid': ['thermal', 'mechanical']
        }
        
        results = []
        for target in analogies.get(domain, []):
            candidate['domain'] = target
            matches = self.matcher.match(candidate, threshold=0.4)
            results.extend(matches)
        
        return sorted(results, key=lambda x: x['score'], reverse=True)
    
    def _save_unknown(self, candidate):
        """儲存到未知通道"""
        unknown_id = self.db.add_unknown_candidate(
            candidate,
            reason='rejection_handler_no_match'
        )
        return unknown_id
