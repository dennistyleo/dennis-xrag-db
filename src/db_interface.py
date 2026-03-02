"""
XRAG Database Interface Module
Provides high-level CRUD operations.
"""

import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime

class XRAGInterface:
    def __init__(self, db):
        self.db = db
    
    def add_axiom(self, axiom_data: Dict) -> str:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            axiom_id = self.db._generate_id('ax')
            
            cursor.execute('''
            INSERT INTO known_axioms 
            (id, name, domain, subdomain, computational_core, input_signature, 
             output_signature, boundary_conditions, precision_requirements, 
             xr_variables, analogy_group, source, human_verified, verified_date, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                axiom_id,
                axiom_data.get('name'),
                axiom_data.get('domain'),
                axiom_data.get('subdomain'),
                json.dumps(axiom_data.get('computational_core', {})),
                json.dumps(axiom_data.get('input_signature', {})),
                json.dumps(axiom_data.get('output_signature', {})),
                json.dumps(axiom_data.get('boundary_conditions', {})),
                json.dumps(axiom_data.get('precision_requirements', {})),
                axiom_data.get('xr_variables', ''),
                axiom_data.get('analogy_group', ''),
                axiom_data.get('source', ''),
                axiom_data.get('human_verified', 0),
                axiom_data.get('verified_date', ''),
                axiom_data.get('version', 1)
            ))
            conn.commit()
            return axiom_id
    
    def search_axioms(self, criteria: Dict) -> List[Dict]:
        """Search axioms by criteria"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM known_axioms WHERE 1=1"
            params = []
            
            if criteria.get('domain'):
                query += " AND domain = ?"
                params.append(criteria['domain'])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Convert to list of dicts
            results = []
            for row in rows:
                axiom_dict = dict(zip(columns, row))
                results.append(axiom_dict)
            
            return results
    
    def add_variable(self, var_data: Dict) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO xr_variables 
            (symbol, name, unit, description, min_range, max_range, domain)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                var_data.get('symbol'),
                var_data.get('name'),
                var_data.get('unit'),
                var_data.get('description'),
                var_data.get('min_range', 0),
                var_data.get('max_range', 1e9),
                var_data.get('domain', 'general')
            ))
            conn.commit()
            return True
    
    def add_unknown_candidate(self, candidate: Dict, reason: str) -> str:
        unknown_id = self.db._generate_id('unknown')
        candidate_hash = self.db._compute_hash(candidate)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO unknown_candidates 
            (id, candidate_json, candidate_hash, reason, generated_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                unknown_id,
                json.dumps(candidate),
                candidate_hash,
                reason,
                datetime.now().isoformat(),
                'pending'
            ))
            conn.commit()
            return unknown_id
    
    def get_axiom_count(self) -> int:
        """Get total number of axioms"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM known_axioms')
            return cursor.fetchone()[0]
