// Main JavaScript for Quantum Dashboard

let socket = null;
let currentResult = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeWebSocket();
    setupEventListeners();
});

function initializeWebSocket() {
    socket = io();
    
    socket.on('connect', function() {
        updateStatus('Connected to Quantum Server', 'connected');
    });
    
    socket.on('disconnect', function() {
        updateStatus('Disconnected from server', 'disconnected');
    });
    
    socket.on('audit_complete', function(data) {
        displayResults(data);
    });
    
    socket.on('phase', function(data) {
        updatePhaseStatus(data);
    });
}

function setupEventListeners() {
    // Enter key in input field
    document.getElementById('commandInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            auditCommand();
        }
    });
}

async function auditCommand() {
    const command = document.getElementById('commandInput').value.trim().toUpperCase();
    if (!command) {
        alert('Please enter a command');
        return;
    }
    
    updateStatus('Auditing: ' + command, 'auditing');
    showLoading();
    
    try {
        const response = await fetch('/api/audit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ command: command })
        });
        
        const result = await response.json();
        displayResults(result);
        
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to audit command');
    }
}

function quickAudit(command) {
    document.getElementById('commandInput').value = command;
    auditCommand();
}

function displayResults(result) {
    currentResult = result;
    const resultDiv = document.getElementById('result-display');
    const isSafe = result.verdict === 'SAFE';
    
    let html = `
        <div class="verdict-${isSafe ? 'safe' : 'vuln'}">
            <div class="verdict-text">${isSafe ? '✓ SAFE' : '✗ VULNERABLE'}</div>
            <div class="confidence">Confidence: ${(result.confidence * 100).toFixed(1)}%</div>
            ${result.attack_type ? `<div class="attack-type">⚠️ Attack: ${result.attack_type}</div>` : ''}
            <div class="audit-time">⏱️ Audit time: ${result.audit_time_ms.toFixed(0)}ms</div>
        </div>
    `;
    
    resultDiv.innerHTML = html;
    
    // Update stats
    document.getElementById('confidenceValue').innerHTML = `${(result.confidence * 100).toFixed(1)}%`;
    document.getElementById('qubitCount').innerHTML = `Qubits: ${result.circuit.n_qubits}`;
    
    // Update probability bars
    const safeProb = result.circuit.safe_probability * 100;
    const vulnProb = (1 - result.circuit.safe_probability) * 100;
    document.getElementById('safeProbBar').style.width = `${safeProb}%`;
    document.getElementById('safeProbBar').innerHTML = `SAFE ${safeProb.toFixed(0)}%`;
    document.getElementById('vulnProbBar').style.width = `${vulnProb}%`;
    document.getElementById('vulnProbBar').innerHTML = `VULN ${vulnProb.toFixed(0)}%`;
    
    // Update quantum energy
    const energy = result.circuit.is_vulnerable ? 0.8 : 0.2;
    document.getElementById('energyValue').innerHTML = `${(energy * 100).toFixed(0)}%`;
    
    // Draw grammar tree
    drawGrammarTree(result.command);
    
    // Draw quantum walk animation
    drawQuantumWalk(result);
    
    updateStatus('Audit complete', 'ready');
}

function drawGrammarTree(command) {
    const svg = document.getElementById('tree-svg');
    const tokens = command.split(' ');
    
    // Simple tree visualization
    let html = '<svg width="100%" height="200" viewBox="0 0 800 200">';
    
    // Root
    html += `<circle cx="400" cy="20" r="15" fill="#00ffcc" /><text x="400" y="25" text-anchor="middle" fill="black" font-size="10">S</text>`;
    
    // Level 1
    const spacing = 200;
    for (let i = 0; i < Math.min(tokens.length, 3); i++) {
        const x = 200 + i * spacing;
        html += `<line x1="400" y1="35" x2="${x}" y2="70" stroke="#00ffcc" stroke-width="2"/>`;
        html += `<circle cx="${x}" cy="80" r="12" fill="#ff00ff" /><text x="${x}" y="85" text-anchor="middle" fill="black" font-size="9">${tokens[i]}</text>`;
    }
    
    html += '</svg>';
    svg.innerHTML = html;
}

function drawQuantumWalk(result) {
    const canvas = document.getElementById('walk-canvas');
    const ctx = canvas.getContext('2d');
    
    canvas.width = 400;
    canvas.height = 200;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw nodes
    const nodes = ['q0', 'q1', 'q2', 'q3', 'q_accept', 'q_reject'];
    const positions = {
        'q0': {x: 50, y: 100},
        'q1': {x: 120, y: 100},
        'q2': {x: 190, y: 100},
        'q3': {x: 260, y: 100},
        'q_accept': {x: 330, y: 60},
        'q_reject': {x: 330, y: 140}
    };
    
    // Draw edges
    ctx.strokeStyle = '#666';
    ctx.lineWidth = 1;
    for (let i = 0; i < nodes.length - 2; i++) {
        ctx.beginPath();
        ctx.moveTo(positions[nodes[i]].x, positions[nodes[i]].y);
        ctx.lineTo(positions[nodes[i+1]].x, positions[nodes[i+1]].y);
        ctx.stroke();
    }
    
    // Draw nodes
    for (const node of nodes) {
        const pos = positions[node];
        ctx.beginPath();
        const isAccept = node === 'q_accept';
        const isReject = node === 'q_reject';
        
        ctx.fillStyle = isAccept ? '#00ff00' : (isReject ? '#ff0000' : '#00ffcc');
        ctx.arc(pos.x, pos.y, 15, 0, 2 * Math.PI);
        ctx.fill();
        ctx.fillStyle = 'black';
        ctx.font = '10px monospace';
        ctx.fillText(node, pos.x - 10, pos.y + 3);
    }
    
    // Highlight path based on result
    const isVuln = result.verdict === 'VULNERABLE';
    const path = isVuln ? ['q0', 'q1', 'q2', 'q_reject'] : ['q0', 'q1', 'q2', 'q3', 'q_accept'];
    
    ctx.strokeStyle = isVuln ? '#ff0000' : '#00ff00';
    ctx.lineWidth = 3;
    for (let i = 0; i < path.length - 1; i++) {
        ctx.beginPath();
        ctx.moveTo(positions[path[i]].x, positions[path[i]].y);
        ctx.lineTo(positions[path[i+1]].x, positions[path[i+1]].y);
        ctx.stroke();
    }
}

function showLoading() {
    const resultDiv = document.getElementById('result-display');
    resultDiv.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Running quantum simulation...</p>
        </div>
    `;
}

function showError(message) {
    const resultDiv = document.getElementById('result-display');
    resultDiv.innerHTML = `
        <div class="verdict-vuln">
            <div class="verdict-text">⚠️ ERROR</div>
            <div>${message}</div>
        </div>
    `;
}

function updateStatus(message, type) {
    const statusDiv = document.getElementById('status');
    const icon = type === 'connected' ? '🟢' : (type === 'auditing' ? '🟡' : '🔴');
    statusDiv.innerHTML = `${icon} ${message}`;
}

function updatePhaseStatus(data) {
    console.log('Phase update:', data);
}