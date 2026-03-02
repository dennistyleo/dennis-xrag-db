"""
XRAG Database Configuration Module
Provides unified database access with connection management.
"""

import sqlite3
import json
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

class XRAGDatabase:
    """Unified database access interface for XRAG system"""
    
    def __init__(self, db_path: str = "data/xrag_complete.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            # Known axioms table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS known_axioms (
                id TEXT PRIMARY KEY,
                name TEXT,
                domain TEXT,
                subdomain TEXT,
                computational_core TEXT,
                input_signature TEXT,
                output_signature TEXT,
                boundary_conditions TEXT,
                precision_requirements TEXT,
                xr_variables TEXT,
                analogy_group TEXT,
                source TEXT,
                human_verified BOOLEAN,
                verified_date TEXT,
                version INTEGER,
                embedding TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # XR variables table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS xr_variables (
                symbol TEXT PRIMARY KEY,
                name TEXT,
                unit TEXT,
                description TEXT,
                min_range REAL,
                max_range REAL,
                domain TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Match history table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS match_history (
                id TEXT PRIMARY KEY,
                candidate_id TEXT,
                candidate_hash TEXT,
                matched_axiom_id TEXT,
                similarity_score REAL,
                match_details TEXT,
                match_method TEXT,
                timestamp TEXT,
                action_taken TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Unknown candidates table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS unknown_candidates (
                id TEXT PRIMARY KEY,
                candidate_json TEXT,
                candidate_hash TEXT,
                reason TEXT,
                generated_date TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
    
    def _generate_id(self, prefix: str) -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique = uuid.uuid4().hex[:6]
        return f"{prefix}_{timestamp}_{unique}"
    
    def _compute_hash(self, data: Dict) -> str:
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
