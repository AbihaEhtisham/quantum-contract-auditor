"""
Web Dashboard for Quantum Smart Contract Auditor
Flask backend with WebSocket support for real-time updates
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import sys
import os
import json
import time
from pathlib import Path

# Add parent directory to path to import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import QuantumContractAuditor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'quantum_secret_key_2025'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize auditor
auditor = QuantumContractAuditor()

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')

@app.route('/api/audit', methods=['POST'])
def audit_command():
    """API endpoint for auditing commands"""
    data = request.json
    command = data.get('command', '').upper()
    
    if not command:
        return jsonify({'error': 'No command provided'}), 400
    
    try:
        # Run audit
        start_time = time.time()
        result = auditor.audit_command(command, show_dashboard=False)
        audit_time = (time.time() - start_time) * 1000
        
        # Format response for web
        response = {
            'command': command,
            'verdict': result['verdict']['final_verdict'],
            'confidence': result['verdict']['confidence'],
            'attack_type': result['verdict'].get('attack_type'),
            'audit_time_ms': audit_time,
            'grammar': {
                'is_valid': result['grammar']['is_valid'],
                'attack_type': result['grammar'].get('attack_type')
            },
            'circuit': {
                'n_qubits': result['circuit']['n_qubits'],
                'safe_probability': result['circuit']['safe_probability'],
                'is_vulnerable': result['circuit']['is_vulnerable']
            },
            'quantum_walk': {
                'acceptance_probability': result['quantum_walk']['acceptance_probability'],
                'is_vulnerable': result['quantum_walk']['is_vulnerable']
            }
        }
        
        # Emit real-time update via WebSocket
        socketio.emit('audit_complete', response)
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    """Get all test scenarios"""
    from scenarios.safe_contracts import SAFE_SCENARIOS
    from scenarios.attack_contracts import ATTACK_SCENARIOS
    
    scenarios = {
        'safe': SAFE_SCENARIOS,
        'vulnerable': ATTACK_SCENARIOS
    }
    return jsonify(scenarios)

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    emit('connected', {'message': 'Connected to Quantum Auditor'})

@socketio.on('audit_stream')
def handle_stream_audit(data):
    """Stream audit results in real-time"""
    command = data.get('command', '').upper()
    
    # Emit phases as they complete
    emit('phase', {'phase': 1, 'name': 'Grammar Validation', 'status': 'running'})
    time.sleep(0.3)
    
    result = auditor.audit_command(command, show_dashboard=False)
    
    emit('phase', {'phase': 1, 'name': 'Grammar Validation', 'status': 'complete', 'result': result['grammar']['is_valid']})
    emit('phase', {'phase': 2, 'name': 'Quantum Walk', 'status': 'complete'})
    emit('phase', {'phase': 3, 'name': 'Circuit Simulation', 'status': 'complete'})
    
    emit('audit_complete', result)

if __name__ == '__main__':
    print("="*60)
    print("⚛ QUANTUM CONTRACT AUDITOR - WEB DASHBOARD")
    print("="*60)
    print("\n🌐 Starting server at: http://localhost:5000")
    print("📡 WebSocket enabled for real-time updates")
    print("\nPress Ctrl+C to stop\n")
    socketio.run(app, debug=True, port=5000)