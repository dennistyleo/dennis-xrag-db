from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_config import XRAGDatabase
from db_interface import XRAGInterface
from matcher_engine import XRAGMatcher
from matcher_interface import UnifiedMatcher

app = Flask(__name__)
CORS(app)

# 初始化
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'xrag_complete.db')
db = XRAGDatabase(db_path)
interface = XRAGInterface(db)
matcher = XRAGMatcher(interface)
unified = UnifiedMatcher(interface, matcher)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': db_path
    })

@app.route('/api/match', methods=['POST'])
def match_axiom():
    """匹配 AI 自創公理"""
    data = request.json
    if not data or 'candidate' not in data:
        return jsonify({'error': 'Missing candidate'}), 400
    
    result = unified.match_axiom(data['candidate'], data.get('config', {}))
    return jsonify(result)

@app.route('/api/unknown', methods=['POST'])
def add_unknown():
    data = request.json
    if not data or 'candidate' not in data:
        return jsonify({'error': 'Missing candidate'}), 400
    
    unknown_id = interface.add_unknown_candidate(
        data['candidate'], 
        data.get('reason', 'manual_submission')
    )
    return jsonify({
        'unknown_id': unknown_id,
        'message': 'Candidate saved to unknown channel'
    }), 201

@app.route('/api/variables', methods=['GET'])
def list_variables():
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT symbol, name, unit, domain FROM xr_variables ORDER BY domain, symbol')
        rows = cursor.fetchall()
        return jsonify({
            'total': len(rows),
            'variables': [dict(zip(['symbol','name','unit','domain'], row)) for row in rows]
        })

@app.route('/api/axioms', methods=['GET'])
def list_axioms():
    """列出所有公理"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, domain, subdomain FROM known_axioms ORDER BY domain, name')
        rows = cursor.fetchall()
        return jsonify({
            'total': len(rows),
            'axioms': [dict(zip(['id','name','domain','subdomain'], row)) for row in rows]
        })

if __name__ == '__main__':
    print(f"\n🚀 XRAG API Server Started")
    print(f"📁 Database: {db_path}")
    print(f"📊 Axioms: {len(interface.search_axioms({}))}") 
    print(f"🌐 URL: http://localhost:5001")
    print("\n📌 Available endpoints:")
    print("   GET  /api/health")
    print("   GET  /api/variables")
    print("   GET  /api/axioms")
    print("   POST /api/match")
    print("   POST /api/unknown\n")
    app.run(host='0.0.0.0', port=5001, debug=True)
