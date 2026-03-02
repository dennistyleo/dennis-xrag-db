"""
XRAG Unified Matching Interface Module
"""

from typing import Dict, List, Optional
import json
from datetime import datetime

class UnifiedMatcher:
    """Unified interface for axiom matching"""
    
    def __init__(self, db_interface, matcher):
        self.db = db_interface
        self.matcher = matcher
    
    def match_axiom(self, candidate: Dict, config: Optional[Dict] = None) -> Dict:
        """Unified matching interface"""
        
        # 執行匹配
        matches = self.matcher.match_candidate(candidate)
        
        return {
            'candidate_id': candidate.get('name', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'matches': matches,
            'match_summary': {
                'total_matches': len(matches),
                'best_match': matches[0] if matches else None
            }
        }
