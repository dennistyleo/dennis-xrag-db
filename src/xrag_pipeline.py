import json
from datetime import datetime

class XRAGPipeline:
    """完整的 XRAG 推理管線"""
    
    def __init__(self, db_interface, matcher, rejection_handler, induction_engine):
        self.db = db_interface
        self.matcher = matcher
        self.rejection = rejection_handler
        self.induction = induction_engine
    
    def process(self, input_data):
        """處理輸入的完整流程"""
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'input_type': input_data.get('type', 'unknown'),
            'stages': [],
            'final_result': None,
            'recommendation': None
        }
        
        # 階段 1：嘗試匹配
        if 'candidate' in input_data:
            matches = self.matcher.match(input_data['candidate'])
            result['stages'].append({
                'stage': 'matching',
                'matches_found': len(matches),
                'best_match': matches[0] if matches else None
            })
            
            if matches:
                result['final_result'] = {
                    'type': 'matched',
                    'matches': matches[:3],
                    'confidence': matches[0]['score']
                }
                result['recommendation'] = self._generate_recommendation(matches[0])
                return result
        
        # 階段 2：如果沒有匹配，嘗試被拒處理
        if 'candidate' in input_data:
            rejection_result = self.rejection.handle(
                input_data['candidate'],
                result['stages'][0].get('matches_found', 0) if result['stages'] else 0
            )
            result['stages'].append({
                'stage': 'rejection_handling',
                'strategies_tried': len(rejection_result['search_path']),
                'final_match': rejection_result.get('final_match')
            })
            
            if rejection_result.get('final_match'):
                result['final_result'] = {
                    'type': 'matched_after_search',
                    'match': rejection_result['final_match'],
                    'strategy': rejection_result.get('strategy_used')
                }
                return result
            elif rejection_result.get('unknown_id'):
                result['final_result'] = {
                    'type': 'unknown',
                    'unknown_id': rejection_result['unknown_id'],
                    'message': '已存入未知通道，待人工審查'
                }
                return result
        
        # 階段 3：如果有數據，嘗試歸納
        if 'data' in input_data:
            induction_results = self.induction.induce(
                input_data['data'],
                input_data.get('context', {})
            )
            result['stages'].append({
                'stage': 'induction',
                'candidates_found': len(induction_results),
                'best_candidate': induction_results[0] if induction_results else None
            })
            
            if induction_results and induction_results[0]['confidence'] > 0.8:
                result['final_result'] = {
                    'type': 'induced',
                    'candidate': induction_results[0]['candidate'],
                    'confidence': induction_results[0]['confidence'],
                    'method': induction_results[0]['method']
                }
                return result
        
        # 預設結果
        result['final_result'] = {
            'type': 'no_result',
            'message': '無法處理輸入數據'
        }
        return result
    
    def _generate_recommendation(self, match):
        """生成使用建議"""
        if match['score'] > 0.8:
            return f"✅ 可直接使用 {match['name']} (相似度 {match['score']})"
        elif match['score'] > 0.6:
            return f"⚠️ 建議參考 {match['name']} 後調整 (相似度 {match['score']})"
        else:
            return f"🔍 相似度偏低，建議人工審查"
    
    def batch_process(self, inputs):
        """批量處理多個輸入"""
        results = []
        for i, input_data in enumerate(inputs):
            print(f"處理第 {i+1}/{len(inputs)} 個輸入...")
            results.append(self.process(input_data))
        return results
