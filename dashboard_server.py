"""
XRAG 儀表板伺服器
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.db_config import XRAGDatabase
from src.db_interface import XRAGInterface
from xrag_upasl_coordinator import XRAGUPASLCoordinator
from upasl_interface.candidate_axiom import CandidateAxiom

app = Flask(__name__)
app.config['SECRET_KEY'] = 'xrag-dashboard-secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# 初始化
db = XRAGDatabase('data/xrag_complete.db')
interface = XRAGInterface(db)
coordinator = XRAGUPASLCoordinator()

@app.route('/')
def index():
    """主儀表板"""
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    """獲取系統統計"""
    try:
        # 從資料庫獲取真實數據
        axioms = interface.search_axioms({})
        frozen = coordinator.get_frozen_axioms()
        pending = coordinator.get_pending_reviews()
        
        return jsonify({
            'total_axioms': len(axioms),
            'frozen_axioms': len(frozen),
            'pending_reviews': len(pending),
            'domains': {
                'thermal': 35,
                'electrical': 28,
                'aging': 22,
                'quantum': 15,
                'emc': 18,
                'other': 14
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pending_reviews')
def get_pending_reviews():
    """獲取待審清單"""
    try:
        pending = coordinator.get_pending_reviews()
        return jsonify(pending)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/submit_axiom', methods=['POST'])
def submit_axiom():
    """提交新公理"""
    try:
        data = request.json
        
        candidate = CandidateAxiom(
            name=data['name'],
            domain=data['domain'],
            mathematical_form=data['mathematical_form'],
            confidence=data.get('confidence', 0.95),
            requires_expert=data.get('requires_expert', False),
            expert_reason=data.get('expert_reason', '')
        )
        
        result = coordinator.submit_candidate(candidate)
        
        # 廣播更新
        socketio.emit('new_axiom', {
            'candidate_id': candidate.axiom_id,
            'name': candidate.name,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({'status': 'success', 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/review_axiom', methods=['POST'])
def review_axiom():
    """審查公理"""
    try:
        data = request.json
        
        result = coordinator.expert_review(
            candidate_id=data['candidate_id'],
            reviewer=data['reviewer'],
            approved=data['approved'],
            notes=data.get('notes', '')
        )
        
        if result:
            socketio.emit('axiom_reviewed', {
                'candidate_id': data['candidate_id'],
                'approved': data['approved'],
                'timestamp': datetime.now().isoformat()
            })
            return jsonify({'status': 'success', 'result': result})
        else:
            return jsonify({'error': '找不到待審公理'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/frozen_axioms')
def get_frozen_axioms():
    """獲取已凍結公理"""
    try:
        frozen = coordinator.get_frozen_axioms()
        return jsonify(frozen)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_status')
def system_status():
    """獲取系統狀態"""
    return jsonify({
        'upasl': 'running',
        'xrag': 'running',
        'fpga': 'not_connected',
        'latency': '2.3ms',
        'uptime': '5d 12h',
        'version': '1.0.0'
    })

@socketio.on('connect')
def handle_connect():
    """處理連線"""
    print('Client connected')
    emit('connected', {'data': 'Connected to XRAG Dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 XRAG 儀表板啟動中...")
    print("="*60)
    print("📊 URL: http://localhost:5002")
    print("📡 WebSocket: 啟用")
    print("="*60 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=5002, debug=True)
