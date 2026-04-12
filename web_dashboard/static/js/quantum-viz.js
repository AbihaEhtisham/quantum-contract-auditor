/**
 * quantum-viz.js
 * 3D Quantum State-Space Simulation
 * Bloch spheres · probability threads · quantum walk · wavefunction collapse
 */

'use strict';

// ── STATE ─────────────────────────────────────────────────────────────────────
let _scene, _camera, _renderer, _animId = null;
let _nodes = [], _threads = [], _particles = [];
let _rotating = true;
let _lastResult = null;
let _walkPhase = 'idle';   // idle | superposition | walk | collapse
let _walkT = 0;            // animation clock 0→1

// ── SPREAD-OUT NODE DEFINITIONS ──────────────────────────────────────────────
const NODE_DEFS = [
    { id: 'ENTRY',       label: 'Entry Point',      pos: [-10,  0.5,   0   ], baseColor: 0x29b6f6 }, // Pushed far left
    { id: 'AUTH',        label: 'Authorization',    pos: [-4.5,  2.5,   1.0 ], baseColor: 0x29b6f6 }, // Higher and left
    { id: 'STATE_READ',  label: 'State Read',       pos: [-1.0,  3.5,  -1.5 ], baseColor: 0x29b6f6 }, // Top center
    { id: 'OP_EXEC',     label: 'Op Execute',       pos: [ 2.5,  1.5,   1.5 ], baseColor: 0x29b6f6 }, // Middle right
    { id: 'STATE_WRITE', label: 'State Write',      pos: [ 10,  2.0,  -0.8 ], baseColor: 0x29b6f6 }, // Further right
    { id: 'EXT_CALL',    label: 'External Call',    pos: [ 0.0, -2.5,   2.5 ], baseColor: 0xff6b6b }, // Dropped low
    { id: 'REENTRY',     label: 'Reentrancy Sink',  pos: [ 9.0, -3.5,   0.8 ], baseColor: 0xff3333 }, // Deep bottom right
    { id: 'ACCEPT',      label: 'Accept',           pos: [ 11.0,  0,     0   ], baseColor: 0x00e676 }, // Final far right
    { id: 'REJECT',      label: 'Reject',           pos: [ 7.0, -2.0,   0   ], baseColor: 0xff3333 }, // Bottom far right
];

// Edge connections (from → to)
const EDGES = [
    ['ENTRY','AUTH'], ['ENTRY','EXT_CALL'],
    ['AUTH','STATE_READ'], ['AUTH','EXT_CALL'],
    ['STATE_READ','OP_EXEC'],
    ['OP_EXEC','STATE_WRITE'], ['OP_EXEC','EXT_CALL'],
    ['STATE_WRITE','ACCEPT'],
    ['EXT_CALL','REENTRY'], ['EXT_CALL','STATE_WRITE'],
    ['REENTRY','REJECT'],
];

// ── INIT (lazy — called on first visit to sim tab) ────────────────────────────
function _ensureInit() {
    if (_renderer) return;
    const wrap = document.getElementById('sim-canvas-wrap');
    if (!wrap || typeof THREE === 'undefined') return;

    const W = wrap.clientWidth  || 800;
    const H = wrap.clientHeight || 500;

    // Scene
    _scene = new THREE.Scene();
    _scene.fog = new THREE.FogExp2(0x000000, 0.04);

    // Camera
    _camera = new THREE.PerspectiveCamera(65, W / H, 0.1, 200);
    _camera.position.set(0, 2, 14);
    _camera.lookAt(0, 0, 0);

    // Renderer
    const canvas = document.getElementById('simCanvas');
    _renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
    _renderer.setSize(W, H);
    _renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    _renderer.setClearColor(0x030508);

    // Lights
    _scene.add(new THREE.AmbientLight(0x112233, 2));
    const pt1 = new THREE.PointLight(0x29b6f6, 1.5, 30); pt1.position.set(-4, 4, 4); _scene.add(pt1);
    const pt2 = new THREE.PointLight(0xff6b6b, 1.0, 30); pt2.position.set( 4,-4,-4); _scene.add(pt2);

    // Star-field background particles
    _buildStarField();

    // Build node spheres
    _buildNodes();

    // Build thread lines
    _buildThreads();

    // Resize handler
    window.addEventListener('resize', _onResize);

    // Start render loop
    _animate();

    // Update overlay counts
    document.getElementById('sim-node-count').textContent  = NODE_DEFS.length;
    document.getElementById('sim-thread-count').textContent = EDGES.length;
}

// ── STAR FIELD ────────────────────────────────────────────────────────────────
function _buildStarField() {
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array(1200);
    for (let i = 0; i < 1200; i++) pos[i] = (Math.random() - 0.5) * 80;
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const mat = new THREE.PointsMaterial({ color: 0x334455, size: 0.06, transparent: true, opacity: 0.6 });
    _scene.add(new THREE.Points(geo, mat));
}

// ── NODE SPHERES ──────────────────────────────────────────────────────────────
function _buildNodes() {
    _nodes = [];
    NODE_DEFS.forEach(def => {
        const group = new THREE.Group();
        group.position.set(...def.pos);

        // Outer glow ring
        const ringGeo = new THREE.TorusGeometry(0.85, 0.03, 16, 80);
        const ringMat = new THREE.MeshBasicMaterial({ color: def.baseColor, transparent: true, opacity: 0.4 });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.rotation.x = Math.PI / 2;
        group.add(ring);

        // Second ring at 90°
        const ring2 = new THREE.Mesh(
            new THREE.TorusGeometry(0.52, 0.015, 16, 80),
            new THREE.MeshBasicMaterial({ color: def.baseColor, transparent: true, opacity: 0.25 })
        );
        group.add(ring2);

        // Core sphere (Bloch sphere)
        const sphereGeo = new THREE.SphereGeometry(0.65, 32, 32);
        const sphereMat = new THREE.MeshStandardMaterial({
            color: def.baseColor,
            emissive: def.baseColor,
            emissiveIntensity: 0.3,
            metalness: 0.6,
            roughness: 0.3,
            transparent: true,
            opacity: 0.85,
        });
        const sphere = new THREE.Mesh(sphereGeo, sphereMat);
        group.add(sphere);
        _addLabel(group, def.label);
        // State vector arrow (line from center to pole)
        const arrowGeo = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(0, 0.36, 0),
        ]);
        const arrow = new THREE.Line(arrowGeo, new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.7 }));
        group.add(arrow);

        // Wireframe overlay
        const wireMat = new THREE.MeshBasicMaterial({ color: def.baseColor, wireframe: true, transparent: true, opacity: 0.08 });
        group.add(new THREE.Mesh(new THREE.SphereGeometry(0.42, 10, 10), wireMat));

        _scene.add(group);

        _nodes.push({
            group, sphere, ring, ring2, arrow,
            sphereMat, ringMat,
            def,
            baseColor: def.baseColor,
            currentColor: def.baseColor,
            prob: 0,
            phase: Math.random() * Math.PI * 2,
            rotSpeed: 0.004 + Math.random() * 0.006,
        });
    });
}

// ── PROBABILITY THREADS ───────────────────────────────────────────────────────
function _buildThreads() {
    _threads = [];
    const nodeMap = {};
    NODE_DEFS.forEach((d, i) => nodeMap[d.id] = i);

    EDGES.forEach(([fromId, toId]) => {
        const fromDef = NODE_DEFS[nodeMap[fromId]];
        const toDef   = NODE_DEFS[nodeMap[toId]];
        if (!fromDef || !toDef) return;

        const from = new THREE.Vector3(...fromDef.pos);
        const to   = new THREE.Vector3(...toDef.pos);

        // Slightly curved path via midpoint offset
        const mid = from.clone().lerp(to, 0.5).add(
            new THREE.Vector3((Math.random()-.5)*.8, (Math.random()-.5)*.8, (Math.random()-.5)*.8)
        );

        const curve = new THREE.QuadraticBezierCurve3(from, mid, to);
        const pts   = curve.getPoints(40);
        const geo   = new THREE.BufferGeometry().setFromPoints(pts);
        const mat   = new THREE.LineBasicMaterial({ color: 0x1a3a5c, transparent: true, opacity: 0.3 });
        const line  = new THREE.Line(geo, mat);
        _scene.add(line);

        // Pulse particle travelling the thread
        const pulseGeo = new THREE.SphereGeometry(0.055, 8, 8);
        const pulseMat = new THREE.MeshBasicMaterial({ color: 0x29b6f6, transparent: true, opacity: 0 });
        const pulse    = new THREE.Mesh(pulseGeo, pulseMat);
        _scene.add(pulse);

        _threads.push({ line, mat, pulse, pulseMat, curve, fromId, toId, t: Math.random(), speed: 0.003 + Math.random() * 0.004 });
    });
}

// ── MAIN ANIMATION LOOP ───────────────────────────────────────────────────────
function _animate() {
    _animId = requestAnimationFrame(_animate);

    const t = Date.now() * 0.001;

    // Slow camera orbit
    if (_rotating) {
        _camera.position.x = Math.sin(t * 0.05) * 0.5; 
    _camera.position.z = 12; // Pull back slightly for better FOV
    _camera.position.y = 1.5;
    _camera.lookAt(0, 0, 0);
    }

    // Animate nodes
    // ── UPDATED FORMAL ANIMATION LOOP ──────────────────
_nodes.forEach(n => {
    // 1. REMOVE: n.group.position.y = ... (No more bobbing)
    
    // 2. SLOW DOWN: Subtle rotation only for the inner arrow (The Bloch Vector)
    n.group.rotation.y += n.rotSpeed; 

    // 3. LOGICAL PULSE: Intensity tied to probability, not just time
    const basePulse = 0.1 + 0.05 * Math.sin(t * 1.0);
    n.sphereMat.emissiveIntensity = basePulse + (n.prob * 1.2);

    // 4. RESET POSITION: Ensure they stay exactly where defined in NODE_DEFS
    n.group.position.set(...n.def.pos);
});

    // Walk phase animation
    if (_walkPhase === 'superposition') _tickSuperposition(t);
    else if (_walkPhase === 'walk')          _tickWalk(t);
    else if (_walkPhase === 'collapse')      _tickCollapse(t);
    else _tickIdle();

    _renderer.render(_scene, _camera);
}

// ── IDLE TICK ─────────────────────────────────────────────────────────────────
function _tickIdle() {
    _threads.forEach(th => {
        th.mat.opacity = 0.18 + 0.08 * Math.sin(Date.now() * 0.001 + th.t * 10);
        th.pulseMat.opacity = 0;
    });
}

// ── SUPERPOSITION TICK ────────────────────────────────────────────────────────
function _tickSuperposition(t) {
    // All nodes glow amber — system is in superposition
    _nodes.forEach(n => {
        n.sphereMat.color.setHex(0xffd54f);
        n.sphereMat.emissive.setHex(0xffd54f);
        n.ringMat.color.setHex(0xffd54f);
        n.ringMat.opacity = 0.5 + 0.3 * Math.sin(t * 4 + n.phase);
    });
    // Threads all lit
    _threads.forEach(th => {
        th.mat.color.setHex(0xffd54f);
        th.mat.opacity = 0.35 + 0.2 * Math.sin(t * 3 + th.t * 5);
        th.pulseMat.opacity = 0;
    });
}

// ── WALK TICK ─────────────────────────────────────────────────────────────────
function _tickWalk(t) {
    const isSafe = _lastResult && _lastResult.verdict === 'SAFE';
    const activeColor = isSafe ? 0x29b6f6 : 0xff6b6b;
    const threadColor = isSafe ? 0x29b6f6 : 0xff5555;

    // Advance pulse particles along threads
    _threads.forEach(th => {
        th.t = (th.t + th.speed) % 1;
        const pt = th.curve.getPoint(th.t);
        th.pulse.position.copy(pt);

        // Brighter pulse on active path
        const isActive = _isActiveEdge(th.fromId, th.toId);
        th.pulseMat.color.setHex(isActive ? threadColor : 0x334466);
        th.pulseMat.opacity = isActive ? 0.8 + 0.2 * Math.sin(t * 6) : 0.25;
        th.mat.color.setHex(isActive ? threadColor : 0x1a3a5c);
        th.mat.opacity = isActive ? 0.55 : 0.12;
    });

    // Node colors based on role
    _nodes.forEach(n => {
        const color = _nodeWalkColor(n.def.id, isSafe);
        n.sphereMat.color.setHex(color);
        n.sphereMat.emissive.setHex(color);
        n.ringMat.color.setHex(color);
    });
}

// ── COLLAPSE TICK ─────────────────────────────────────────────────────────────
function _tickCollapse(t) {
    const isSafe = _lastResult && _lastResult.verdict === 'SAFE';
    // Settled — show final path brightly, others dim
    _threads.forEach(th => {
        const onPath = _isActiveEdge(th.fromId, th.toId);
        th.mat.opacity   = onPath ? 0.7 : 0.06;
        th.mat.color.setHex(onPath ? (isSafe ? 0x00e676 : 0xff3333) : 0x111c2a);
        th.pulseMat.opacity = 0; // stopped
    });
    _nodes.forEach(n => {
        const final = _nodeCollapseColor(n.def.id, isSafe);
        n.sphereMat.color.setHex(final);
        n.sphereMat.emissive.setHex(final);
        n.ringMat.color.setHex(final);
        n.ringMat.opacity = _isNodeOnPath(n.def.id, isSafe) ? 0.7 : 0.1;
    });
}

// ── PATH HELPERS ──────────────────────────────────────────────────────────────
const SAFE_PATH  = new Set(['ENTRY-AUTH','AUTH-STATE_READ','STATE_READ-OP_EXEC','OP_EXEC-STATE_WRITE','STATE_WRITE-ACCEPT']);
const VULN_PATH  = new Set(['ENTRY-EXT_CALL','EXT_CALL-REENTRY','REENTRY-REJECT']);
const SAFE_NODES = new Set(['ENTRY','AUTH','STATE_READ','OP_EXEC','STATE_WRITE','ACCEPT']);
const VULN_NODES = new Set(['ENTRY','EXT_CALL','REENTRY','REJECT']);

function _isActiveEdge(from, to) {
    if (!_lastResult) return false;
    const key = `${from}-${to}`;
    return _lastResult.verdict === 'SAFE' ? SAFE_PATH.has(key) : VULN_PATH.has(key);
}

function _isNodeOnPath(id, isSafe) {
    return isSafe ? SAFE_NODES.has(id) : VULN_NODES.has(id);
}

function _nodeWalkColor(id, isSafe) {
    if (id === 'REENTRY' || id === 'REJECT') return 0xff3333;
    if (id === 'EXT_CALL') return isSafe ? 0xffd54f : 0xff6b6b;
    if (id === 'ACCEPT')   return 0x00e676;
    if (id === 'ENTRY')    return 0x29b6f6;
    return isSafe ? 0x29b6f6 : 0xffd54f;
}

function _nodeCollapseColor(id, isSafe) {
    if (isSafe) {
        // High-contrast "Secure" colors
        if (SAFE_NODES.has(id)) return id === 'ACCEPT' ? 0x00e676 : 0x29b6f6;
        return 0x1c2430; // Dim inactive nodes
    } else {
        // Highlight the specific attack path in RED
        if (VULN_NODES.has(id)) {
            if (id === 'EXT_CALL' || id === 'REENTRY') return 0xff3333;
            return 0xff6b6b;
        }
        return 0x1c2430;
    }
}
// ── PHASE CONTROLLER ─────────────────────────────────────────────────────────
function _runPhases(result) {
    _lastResult = result;
    const isSafe = result.verdict === 'SAFE';

    _setPhaseLabel('INITIALISING STATE SPACE...', 0x29b6f6);
    _setWalkState('SUPERPOSITION');

    // Phase 1: Superposition (1.2s)
    _walkPhase = 'superposition';
    setTimeout(() => {
        _setPhaseLabel('QUANTUM WALK IN PROGRESS...', 0xffd54f);
        _setWalkState('WALKING');
        _walkPhase = 'walk';
    }, 1200);

    // Phase 2: Walk (2.5s)
    setTimeout(() => {
        _setPhaseLabel(isSafe ? '⬡ WAVEFUNCTION COLLAPSED — SAFE' : '⚠ WAVEFUNCTION COLLAPSED — VULNERABLE', isSafe ? 0x00e676 : 0xff3333);
        _setWalkState('COLLAPSED');
        _walkPhase = 'collapse';
        _updateSidebarProbs(result);
    }, 3700);

    // Phase 3: Hold collapse, then settle
    setTimeout(() => {
        _setPhaseLabel('', 0xffffff);
        document.getElementById('simPhaseLabel').textContent =
            (isSafe ? 'SAFE' : 'VULNERABLE') + ' — Wavefunction collapsed';
    }, 6000);
}

function _setPhaseLabel(text, color) {
    const el = document.getElementById('sim-phase');
    if (!el) return;
    el.textContent = text;
    el.style.color = '#' + color.toString(16).padStart(6, '0');
    el.style.textShadow = '0 0 20px #' + color.toString(16).padStart(6, '0');
    el.style.opacity = text ? '1' : '0';
}

function _setWalkState(txt) {
    const el = document.getElementById('sim-walk-state');
    if (el) el.textContent = txt;
}

// ── SIDEBAR NODE LIST ─────────────────────────────────────────────────────────
function _updateSidebarProbs(result) {
    const isSafe = result.verdict === 'SAFE';
    const conf   = result.confidence;
    const list   = document.getElementById('simNodeList');
    if (!list) return;

    const probMap = {
        ENTRY:       1.0,
        AUTH:        isSafe ? conf : 1 - conf,
        STATE_READ:  isSafe ? conf * 0.97 : 0.12,
        OP_EXEC:     isSafe ? conf * 0.95 : 0.10,
        STATE_WRITE: isSafe ? conf * 0.93 : 0.08,
        EXT_CALL:    isSafe ? 0.05 : 1 - conf,
        REENTRY:     isSafe ? 0.01 : (1 - conf) * 0.92,
        ACCEPT:      isSafe ? conf * 0.91 : 0.04,
        REJECT:      isSafe ? 0.02 : (1 - conf) * 0.88,
    };

    const colorMap = {
        ENTRY: '#29b6f6', AUTH: '#29b6f6', STATE_READ: '#29b6f6',
        OP_EXEC: '#29b6f6', STATE_WRITE: '#29b6f6',
        EXT_CALL: '#ff6b6b', REENTRY: '#ff3333',
        ACCEPT: '#00e676', REJECT: '#ff3333',
    };

    list.innerHTML = NODE_DEFS.map(d => {
        const p   = probMap[d.id] || 0;
        const col = colorMap[d.id] || '#29b6f6';
        return `<div class="sim-node">
            <div class="sim-node-dot" style="background:${col}"></div>
            <span class="sim-node-name">${d.label}</span>
            <span class="sim-node-prob">${(p * 100).toFixed(0)}%</span>
        </div>`;
    }).join('');

    // Update status
    const el = document.getElementById('sim-status');
    if (el) el.innerHTML =
        `Command: <span style="color:var(--cyan)">${result.command}</span><br>` +
        `Verdict: <span style="color:${isSafe ? '#00e676' : '#ff6b6b'}">${result.verdict}</span><br>` +
        `Confidence: <span style="color:var(--text2)">${(conf*100).toFixed(1)}%</span><br>` +
        `Walk steps: <span style="color:var(--text2)">${result._tokens ? result._tokens.length * 3 : '—'}</span>`;
}

// ── RESIZE ────────────────────────────────────────────────────────────────────
function _onResize() {
    if (!_renderer) return;
    const wrap = document.getElementById('sim-canvas-wrap');
    if (!wrap) return;
    const W = wrap.clientWidth, H = wrap.clientHeight;
    _camera.aspect = W / H;
    _camera.updateProjectionMatrix();
    _renderer.setSize(W, H);
}

// ── PUBLIC API ────────────────────────────────────────────────────────────────

/** Called by main.js after every audit */
function updateQuantumSim(result, tokens) {
    // Lazily init when first called — Three.js must be loaded
    _ensureInit();
    if (!_renderer) return;

    _lastResult = result;
    _walkPhase  = 'idle';

    // Reset all nodes to base color before starting
    _nodes.forEach(n => {
        n.sphereMat.color.setHex(n.def.baseColor);
        n.sphereMat.emissive.setHex(n.def.baseColor);
        n.ringMat.color.setHex(n.def.baseColor);
        n.ringMat.opacity = 0.4;
        n.prob = 0;
    });
    _threads.forEach(th => {
        th.mat.color.setHex(0x1a3a5c);
        th.mat.opacity = 0.3;
        th.t = Math.random();
    });

    // Run phase sequence after short delay
    setTimeout(() => _runPhases(result), 300);
}

/** Replay the last simulation */
function replaySimulation() {
    if (_lastResult) updateQuantumSim(_lastResult, null);
}

/** Toggle camera orbit */
function toggleSimRotation() {
    _rotating = !_rotating;
}
function _addLabel(group, text) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 512;
    canvas.height = 128;

    // Label Styling
    ctx.font = 'Bold 48px Arial'; 
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.fillText(text.toUpperCase(), 256, 80);

    const texture = new THREE.CanvasTexture(canvas);
    const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(spriteMat);

    // --- PASTE THE LINE HERE ---
    sprite.position.set(0, 1.4, 0); // This moves the text 1.2 units above the center of the blob
    
    sprite.scale.set(3, 1, 1);
    group.add(sprite);
}
// Auto-init if sim tab is visited before first audit
document.addEventListener('DOMContentLoaded', () => {
    // Lazy-init on tab click
    const simNav = document.querySelector('[data-tab="sim"]');
    if (simNav) {
        simNav.addEventListener('click', () => {
            setTimeout(_ensureInit, 50);
        });
    }
});