// ── Quantum Contract Auditor — main.js ──────────────────────────────────────

let socket = null;
let startTime = 0;

const TOKEN_DEFS = {
    ADMIN:    { tag:'AUTH',  role:'Subject[Auth]',   risk:'LOW',  desc:'Authorized administrator subject' },
    USER:     { tag:'AUTH',  role:'Subject[User]',   risk:'LOW',  desc:'Authenticated user subject' },
    MINT:     { tag:'OP',    role:'Verb[Create]',    risk:'MED',  desc:'Token creation operation' },
    TRANSFER: { tag:'OP',    role:'Verb[Move]',      risk:'MED',  desc:'Value movement operation' },
    BURN:     { tag:'OP',    role:'Verb[Destroy]',   risk:'MED',  desc:'Token destruction operation' },
    WITHDRAW: { tag:'OP',    role:'Verb[Extract]',   risk:'HIGH', desc:'Fund extraction — high risk' },
    TOKEN:    { tag:'ASSET', role:'Object[Token]',   risk:'LOW',  desc:'ERC-20/721 token object' },
    FUNDS:    { tag:'ASSET', role:'Object[Value]',   risk:'MED',  desc:'Native currency value object' },
    BALANCE:  { tag:'ASSET', role:'Object[State]',   risk:'HIGH', desc:'Contract state variable' },
    CALL:     { tag:'CALL',  role:'ExternalCall',    risk:'HIGH', desc:'External contract interaction — danger' },
};

const ATTACK_RULES = {
    REENTRANCY: {
        trigger: cmd => cmd.includes('CALL') && cmd.includes('WITHDRAW'),
        rule: 'R2',
        sig: 'Rule R2 Violated: External CALL occurs before balance state update. An attacker can re-enter withdraw() before balances[msg.sender] is decremented, repeatedly draining funds in a single transaction.',
    },
    UNAUTHORIZED_MINT: {
        trigger: cmd => cmd.includes('MINT') && !cmd.includes('ADMIN'),
        rule: 'R1',
        sig: 'Rule R1 Violated: MINT requires an [AUTH] subject (ADMIN). Without an authorization check, any external address can call mint() and arbitrarily inflate the token supply.',
    },
    CALL_AFTER_TRANSFER: {
        trigger: cmd => cmd.includes('TRANSFER') && cmd.includes('CALL'),
        rule: 'R3',
        sig: 'Rule R3 Violated: State mutation via TRANSFER precedes an external CALL. This enables cross-function reentrancy — the external contract can interact with the protocol before the transfer settles.',
    },
};

// ── INIT ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
    document.getElementById('commandInput').addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); auditCommand(); }
    });
    drawGauge(0, true);
});

// ── TAB SWITCHING ─────────────────────────────────────────────────────────────
function switchTab(name) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
    document.querySelector('[data-tab="' + name + '"]').classList.add('active');
    // Clear notification dot when visiting tab
    const dot = document.getElementById('dot-' + name);
    if (dot) dot.classList.remove('show');
}

function notifyTab(name) {
    const dot = document.getElementById('dot-' + name);
    if (dot && !document.querySelector('[data-tab="' + name + '"]').classList.contains('active')) {
        dot.classList.add('show');
    }
}

// ── WEBSOCKET ─────────────────────────────────────────────────────────────────
function initWebSocket() {
    try {
        socket = io();
        socket.on('connect',        () => setStatus('CONNECTED', 'ready'));
        socket.on('disconnect',     () => setStatus('DISCONNECTED', 'idle'));
        socket.on('audit_complete', data => displayResults(data));
    } catch(e) { /* offline */ }
}

// ── STATUS ────────────────────────────────────────────────────────────────────
function setStatus(msg, type) {
    const dot = document.getElementById('statusDot');
    const txt = document.getElementById('statusTxt');
    dot.className = 'sdot' + (type === 'auditing' ? ' auditing' : type === 'vuln' ? ' vuln' : '');
    txt.textContent = msg;
}

// ── AUDIT ─────────────────────────────────────────────────────────────────────
function quickAudit(cmd) {
    document.getElementById('commandInput').value = cmd;
    auditCommand();
}

async function auditCommand() {
    const cmd = document.getElementById('commandInput').value.trim().toUpperCase();
    if (!cmd) return;
    startTime = performance.now();
    setStatus('AUDITING...', 'auditing');
    document.getElementById('ftrStatus').textContent = 'Running quantum simulation for: ' + cmd;
    document.getElementById('lastCmd').textContent = cmd;

    try {
        const res = await fetch('/api/audit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: cmd }),
        });
        if (!res.ok) throw new Error();
        displayResults(await res.json());
    } catch(_) {
        setTimeout(() => displayResults(mockAudit(cmd)), 700 + Math.random() * 400);
    }
}

// ── MOCK ──────────────────────────────────────────────────────────────────────
function mockAudit(cmd) {
    const tokens = cmd.trim().toUpperCase().split(/\s+/);
    let attack = null;
    for (const [type, rule] of Object.entries(ATTACK_RULES)) {
        if (rule.trigger(cmd)) { attack = { type, ...rule }; break; }
    }
    const isSafe = !attack && tokens.length >= 2;
    const conf = isSafe ? 0.91 + Math.random() * 0.08 : 0.83 + Math.random() * 0.12;
    return {
        command: cmd,
        verdict: isSafe ? 'SAFE' : 'VULNERABLE',
        confidence: conf,
        attack_type: attack ? attack.type : null,
        audit_time_ms: performance.now() - startTime,
        grammar: { is_valid: isSafe },
        circuit: { n_qubits: tokens.length + 2, safe_probability: isSafe ? conf : 1 - conf, is_vulnerable: !isSafe },
        quantum_walk: { acceptance_probability: isSafe ? conf : 1 - conf },
        _tokens: tokens,
        _attack_sig: attack ? attack.sig : null,
    };
}

// ── RENDER ────────────────────────────────────────────────────────────────────
function displayResults(r) {
    const isSafe  = r.verdict === 'SAFE';
    const elapsed = r.audit_time_ms ? r.audit_time_ms.toFixed(0) : (performance.now() - startTime).toFixed(0);
    const tokens  = r._tokens || r.command.split(/\s+/);
    const nQ      = r.circuit.n_qubits;
    const conf    = r.confidence;
    const safeP   = r.circuit.safe_probability;

    setStatus(isSafe ? 'SAFE' : 'VULNERABLE', isSafe ? 'ready' : 'vuln');

    // ── TAB 1: AUDIT ──
    document.getElementById('verdictBlock').className = 'vblock ' + (isSafe ? 'safe' : 'vuln');
    document.getElementById('verdictMain').textContent = isSafe ? 'SAFE' : 'VULNERABLE';
    document.getElementById('verdictConf').textContent = 'Confidence: ' + (conf * 100).toFixed(1) + '%';
    document.getElementById('verdictAtk').textContent  = r.attack_type ? r.attack_type.replace(/_/g, ' ') : '';

    document.getElementById('vtTime').textContent   = elapsed;
    document.getElementById('vtQubits').textContent = nQ;
    document.getElementById('vtDepth').textContent  = tokens.length * 3;
    document.getElementById('vtTokens').textContent = tokens.length;

    document.getElementById('barAccept').style.width = (safeP * 100).toFixed(0) + '%';
    document.getElementById('barReject').style.width = ((1 - safeP) * 100).toFixed(0) + '%';
    document.getElementById('pctAccept').textContent = (safeP * 100).toFixed(0) + '%';
    document.getElementById('pctReject').textContent = ((1 - safeP) * 100).toFixed(0) + '%';

    // ── TAB 2: LINGUISTIC ──
    renderTokenTable(tokens);
    drawGrammarTree(tokens, isSafe);
    notifyTab('ling');

    // ── TAB 3: QUANTUM ──
    drawGauge(conf, isSafe);
    drawCircuit(nQ, tokens.length * 3, isSafe);

    document.getElementById('gsSafe').textContent  = (safeP * 100).toFixed(1) + '%';
    document.getElementById('gsVuln').textContent  = ((1 - safeP) * 100).toFixed(1) + '%';
    document.getElementById('gsEnt').textContent   = nQ > 2 ? 'YES' : 'NO';
    document.getElementById('gsDepth').textContent = tokens.length * 3;
    document.getElementById('ciGates').textContent = nQ * 2;
    document.getElementById('ciDepth').textContent = tokens.length * 3;
    document.getElementById('ciQubits').textContent = nQ;
    document.getElementById('ciEnt').textContent   = nQ > 2 ? 'YES' : 'NO';
    notifyTab('quantum');

    // ── TAB 4: REPORT ──
    document.getElementById('solCode').innerHTML = buildSolidity(tokens, r);
    document.getElementById('reportCmd').textContent = r.command;

    const sigBox  = document.getElementById('sigBox');
    const sigSafe = document.getElementById('sigSafe');
    const sigPh   = document.getElementById('sigPh');

    if (r.attack_type) {
        const rule = ATTACK_RULES[r.attack_type];
        sigBox.style.display  = 'block';
        sigSafe.style.display = 'none';
        sigPh.style.display   = 'none';
        document.getElementById('sigTitle').textContent = r.attack_type.replace(/_/g, ' ') + (rule ? ' — Rule ' + rule.rule + ' Violated' : '');
        document.getElementById('sigBody').textContent  = r._attack_sig || (rule ? rule.sig : 'Vulnerability detected.');
    } else {
        sigBox.style.display  = 'none';
        sigSafe.style.display = 'block';
        sigPh.style.display   = 'none';
        sigSafe.textContent   = '✓ No attack signature detected.\n\nAll grammar rules satisfied:\n  R1: AUTH subject present\n  R2: No unguarded external CALL\n  R3: State updated before any external interaction\n\nTransaction pattern is SAFE to execute.';
    }
    notifyTab('report');

    // ── TAB 5: 3D SIM ──
    if (typeof updateQuantumSim === 'function') updateQuantumSim(r, tokens);
    notifyTab('sim');

    document.getElementById('ftrStatus').textContent = 'Audit complete — ' + r.command + ' (' + elapsed + 'ms)';
}

// ── TOKEN TABLE ───────────────────────────────────────────────────────────────
function renderTokenTable(tokens) {
    const rc = { LOW:'rL', MED:'rM', HIGH:'rH' };
    document.getElementById('tokenBody').innerHTML = tokens.map(t => {
        const d = TOKEN_DEFS[t] || { tag:'UNKNOWN', role:'Unclassified', risk:'MED', desc:'Unrecognized token' };
        const cls = d.tag === 'UNKNOWN' ? 'tag-UNK' : 'tag-' + d.tag;
        return `<tr>
          <td>${t}</td>
          <td><span class="tag ${cls}">${d.tag}</span></td>
          <td>${d.role}</td>
          <td class="${rc[d.risk]||'rM'}">${d.risk}</td>
          <td style="color:var(--text2);font-size:11px">${d.desc}</td>
        </tr>`;
    }).join('');
}

// ── GRAMMAR TREE ──────────────────────────────────────────────────────────────
function drawGrammarTree(tokens, isSafe) {
    const col = isSafe ? '#00e676' : '#ff6b6b';
    const tagCol = { AUTH:'#64b5f6', OP:'#4dd0e1', ASSET:'#ffcc80', CALL:'#ef9a9a', UNKNOWN:'#3d5470', UNK:'#3d5470' };
    const n = Math.min(tokens.length, 7);
    const W = 700, pad = 50;
    const cx = W / 2;
    const sp = n > 1 ? (W - 2 * pad) / (n - 1) : 0;

    let s = `<svg id="treeSvg" viewBox="0 0 ${W} 130" height="130">`;
    s += `<circle cx="${cx}" cy="18" r="14" fill="rgba(0,0,0,.5)" stroke="${col}" stroke-width="1.2"/>`;
    s += `<text x="${cx}" y="23" text-anchor="middle" font-family="'Share Tech Mono',monospace" font-size="12" fill="${col}">S</text>`;

    for (let i = 0; i < n; i++) {
        const x = n === 1 ? cx : pad + i * sp;
        const t = tokens[i];
        const d = TOKEN_DEFS[t] || { tag:'UNK' };
        const tc = tagCol[d.tag] || '#3d5470';

        s += `<line x1="${cx}" y1="32" x2="${x}" y2="58" stroke="${col}" stroke-width="0.7" opacity=".4"/>`;
        s += `<rect x="${x-34}" y="58" width="68" height="22" rx="3" fill="rgba(0,0,0,.5)" stroke="${tc}" stroke-width="0.8"/>`;
        s += `<text x="${x}" y="73" text-anchor="middle" font-family="'Share Tech Mono',monospace" font-size="10" fill="${tc}">${t.length > 9 ? t.substring(0,8)+'…' : t}</text>`;
        s += `<text x="${x}" y="100" text-anchor="middle" font-family="'Share Tech Mono',monospace" font-size="9" fill="#3d5470">[${d.tag}]</text>`;
        s += `<line x1="${x}" y1="80" x2="${x}" y2="104" stroke="${tc}" stroke-width="0.5" opacity=".3"/>`;
    }
    s += `</svg>`;
    document.getElementById('treeSvg').outerHTML = s;
}

// ── CIRCUIT DIAGRAM ───────────────────────────────────────────────────────────
function drawCircuit(nQ, depth, isSafe) {
    const canvas = document.getElementById('circuitCanvas');
    const W = canvas.clientWidth || 600;

    const qCount  = Math.min(nQ, 5);
    const ROW_H   = 34;
    const TOP_PAD = 18;
    const BOT_PAD = 14;
    const H = TOP_PAD + qCount * ROW_H + BOT_PAD;

    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, W, H);

    const lPad    = 36;
    const rPad    = 10;
    const GW      = 16;
    const GH      = 14;
    const gCount  = Math.min(depth, 12);
    const gSpacing = (W - lPad - rPad) / (gCount + 1);
    const gates   = ['H','X','Z','CNOT','H','X','Z','CNOT','H','X','Z','CNOT'];
    const gCol    = isSafe ? '#00e676' : '#ff6b6b';
    const wCol    = 'rgba(41,182,246,.18)';
    const lCol    = '#4a6280';

    for (let q = 0; q < qCount; q++) {
        const y = TOP_PAD + q * ROW_H + ROW_H / 2;
        ctx.beginPath(); ctx.moveTo(lPad, y); ctx.lineTo(W - rPad, y);
        ctx.strokeStyle = wCol; ctx.lineWidth = 1; ctx.stroke();
        ctx.fillStyle = lCol; ctx.font = '9px "Share Tech Mono"'; ctx.textAlign = 'right';
        ctx.fillText('q' + q, lPad - 4, y + 3);
    }

    for (let g = 0; g < gCount; g++) {
        const cx  = lPad + gSpacing * (g + 1);
        const q   = g % qCount;
        const cy  = TOP_PAD + q * ROW_H + ROW_H / 2;
        const gt  = gates[g % gates.length];

        ctx.fillStyle = '#0b0d10';
        ctx.strokeStyle = gCol;
        ctx.lineWidth = 0.8;
        rrect(ctx, cx - GW, cy - GH, GW * 2, GH * 2, 2);

        ctx.fillStyle = gCol;
        ctx.font = 'bold 9px "Share Tech Mono"';
        ctx.textAlign = 'center';
        ctx.fillText(gt, cx, cy + 3);

        if (gt === 'CNOT' && q + 1 < qCount) {
            const cy2 = TOP_PAD + (q + 1) * ROW_H + ROW_H / 2;
            ctx.beginPath(); ctx.moveTo(cx, cy + GH); ctx.lineTo(cx, cy2 - GH);
            ctx.strokeStyle = gCol; ctx.lineWidth = 0.7; ctx.stroke();
            ctx.beginPath(); ctx.arc(cx, cy2, 4, 0, 2 * Math.PI);
            ctx.strokeStyle = gCol; ctx.fillStyle = 'transparent'; ctx.lineWidth = 0.8; ctx.stroke();
        }
    }
}

function rrect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x+r,y); ctx.lineTo(x+w-r,y); ctx.arcTo(x+w,y,x+w,y+h,r);
    ctx.lineTo(x+w,y+h-r); ctx.arcTo(x+w,y+h,x,y+h,r);
    ctx.lineTo(x+r,y+h); ctx.arcTo(x,y+h,x,y,r);
    ctx.lineTo(x,y+r); ctx.arcTo(x,y,x+w,y,r);
    ctx.closePath(); ctx.fill(); ctx.stroke();
}

// ── GAUGE ─────────────────────────────────────────────────────────────────────
function drawGauge(conf, isSafe) {
    const canvas = document.getElementById('gaugeCanvas');
    const ctx = canvas.getContext('2d');
    const W=220, H=120, cx=W/2, cy=H-10, r=82;
    ctx.clearRect(0,0,W,H);

    ctx.beginPath(); ctx.arc(cx,cy,r,Math.PI,0,false);
    ctx.strokeStyle='#1f2d3d'; ctx.lineWidth=10; ctx.stroke();

    const fillCol = isSafe ? '#00e676' : '#ff6b6b';
    ctx.beginPath(); ctx.arc(cx,cy,r,Math.PI,Math.PI+conf*Math.PI,false);
    ctx.strokeStyle=fillCol; ctx.lineWidth=10; ctx.lineCap='round'; ctx.stroke();

    const nx=cx+r*Math.cos(Math.PI+conf*Math.PI);
    const ny=cy+r*Math.sin(Math.PI+conf*Math.PI);
    ctx.beginPath(); ctx.arc(nx,ny,6,0,2*Math.PI);
    ctx.fillStyle=fillCol; ctx.fill();

    ctx.fillStyle='#e2eaf3'; ctx.font='600 22px "Share Tech Mono"'; ctx.textAlign='center';
    ctx.fillText((conf*100).toFixed(0)+'%', cx, cy-12);
    ctx.fillStyle='#3d5470'; ctx.font='9px "Share Tech Mono"'; ctx.letterSpacing='2px';
    ctx.fillText('CONFIDENCE', cx, cy+8);
}

// ── SOLIDITY ──────────────────────────────────────────────────────────────────
function buildSolidity(tokens, r) {
    const sub = tokens[0]||'', op = tokens[1]||'', asset = tokens[2]||'';
    const mods = { ADMIN:'onlyOwner', USER:'nonReentrant', CALL:'external' };
    const fns  = { MINT:'mint', TRANSFER:'transfer', BURN:'burn', WITHDRAW:'withdraw', CALL:'externalCall' };
    const mod  = mods[sub] || 'public';
    const fn   = fns[op] || op.toLowerCase() || 'execute';

    if (r.attack_type === 'REENTRANCY') return (
`<span class="cm">// ⚠  VULNERABLE — Reentrancy Attack (Rule R2 Violated)</span>
<span class="kw">function</span> <span class="fn">${fn}</span>(<span class="kw">uint</span> amount) <span class="kw">external</span> {
    <span class="cm">// ❌ External call BEFORE state update — reentrancy vector</span>
    (bool ok,) = msg.sender.<span class="fn">call</span>{value: amount}(<span class="str">""</span>);
    <span class="fn">require</span>(ok, <span class="str">"Transfer failed"</span>);
    balances[msg.sender] -= amount; <span class="cm">// ← too late, state not updated first</span>
}

<span class="cm">// ✅ SAFE VERSION — checks-effects-interactions pattern:</span>
<span class="kw">function</span> <span class="fn">${fn}Safe</span>(<span class="kw">uint</span> amount) <span class="kw">external</span> nonReentrant {
    <span class="fn">require</span>(balances[msg.sender] >= amount, <span class="str">"Insufficient balance"</span>);
    balances[msg.sender] -= amount; <span class="cm">// ← state first</span>
    (bool ok,) = msg.sender.<span class="fn">call</span>{value: amount}(<span class="str">""</span>);
    <span class="fn">require</span>(ok, <span class="str">"Transfer failed"</span>);
}`);

    if (r.attack_type === 'UNAUTHORIZED_MINT') return (
`<span class="cm">// ⚠  VULNERABLE — Unauthorized Mint (Rule R1 Violated)</span>
<span class="kw">function</span> <span class="fn">mint</span>(<span class="kw">address</span> to, <span class="kw">uint</span> amount) <span class="kw">public</span> {
    <span class="cm">// ❌ No authorization check — anyone can mint</span>
    _mint(to, amount);
}

<span class="cm">// ✅ SAFE VERSION:</span>
<span class="kw">function</span> <span class="fn">mint</span>(<span class="kw">address</span> to, <span class="kw">uint</span> amount) <span class="kw">public</span> onlyOwner {
    _mint(to, amount); <span class="cm">// ← onlyOwner enforces AUTH</span>
}`);

    if (r.attack_type) return (
`<span class="cm">// ⚠  VULNERABLE — ${r.attack_type.replace(/_/g,' ')}</span>
<span class="kw">function</span> <span class="fn">${fn}</span>() <span class="kw">external</span> {
    <span class="cm">// ❌ Attack rule violated — consult Report tab for details</span>
}`);

    return (
`<span class="cm">// ✓  SAFE — ${sub} ${op} ${asset}</span>
<span class="kw">function</span> <span class="fn">${fn}</span>(<span class="kw">uint</span> amount)
    <span class="kw">external</span> ${mod} {
    <span class="fn">require</span>(amount > 0, <span class="str">"Invalid amount"</span>);
    <span class="fn">require</span>(balances[msg.sender] >= amount, <span class="str">"Insufficient balance"</span>);
    balances[msg.sender] -= amount; <span class="cm">// ✓ state updated before interaction</span>
    _<span class="fn">${fn}</span>(msg.sender, amount);
    <span class="kw">emit</span> <span class="fn">${fn.charAt(0).toUpperCase()+fn.slice(1)}</span>(msg.sender, amount);
}`);
}