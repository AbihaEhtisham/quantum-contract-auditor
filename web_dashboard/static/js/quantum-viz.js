/**
 * 3D Quantum Circuit Visualization with Three.js
 * Shows qubit states, quantum gates, and entanglement
 */

let scene, camera, renderer, controls;
let qubits = [];
let quantumField = null;
let particles = [];
let animationId = null;

// Quantum state colors
const COLORS = {
    SUPERPOSITION: 0x00ffcc,  // Cyan - multiple states
    MEASURED_0: 0x00ff00,     // Green - |0⟩ state
    MEASURED_1: 0xff0000,     // Red - |1⟩ state
    ENTANGLED: 0xff00ff,      // Magenta - entangled
    IDLE: 0x3366ff            // Blue - idle
};

// Initialize 3D scene
function init3DVisualization() {
    const container = document.getElementById('canvas-container');
    if (!container) return;
    
    // Create scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);
    scene.fog = new THREE.FogExp2(0x000000, 0.008);
    
    // Create camera
    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(5, 3, 8);
    camera.lookAt(0, 0, 0);
    
    // Create renderer
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);
    
    // Add lights
    addLights();
    
    // Add quantum background field
    addQuantumField();
    
    // Create qubits
    createQubits(4);
    
    // Add floating particles
    addQuantumParticles();
    
    // Add grid floor
    addGridFloor();
    
    // Start animation
    animate();
    
    // Handle window resize
    window.addEventListener('resize', onWindowResize, false);
}

function addLights() {
    // Ambient light
    const ambientLight = new THREE.AmbientLight(0x222222);
    scene.add(ambientLight);
    
    // Main directional light
    const mainLight = new THREE.DirectionalLight(0xffffff, 1);
    mainLight.position.set(5, 10, 7);
    mainLight.castShadow = true;
    mainLight.receiveShadow = true;
    scene.add(mainLight);
    
    // Fill light from below
    const fillLight = new THREE.PointLight(0x00ffcc, 0.5);
    fillLight.position.set(0, -2, 0);
    scene.add(fillLight);
    
    // Back rim light
    const rimLight = new THREE.PointLight(0xff00ff, 0.3);
    rimLight.position.set(-3, 2, -5);
    scene.add(rimLight);
    
    // Colored quantum glow lights
    const colors = [0x00ffcc, 0xff00ff, 0x3366ff];
    for (let i = 0; i < 3; i++) {
        const light = new THREE.PointLight(colors[i], 0.4);
        light.position.set(Math.sin(i) * 4, 2, Math.cos(i) * 4);
        scene.add(light);
    }
}

function addQuantumField() {
    // Create a shimmering quantum field background
    const geometry = new THREE.SphereGeometry(12, 64, 64);
    const material = new THREE.MeshPhongMaterial({
        color: 0x00ffcc,
        emissive: 0x003333,
        transparent: true,
        opacity: 0.05,
        wireframe: true
    });
    quantumField = new THREE.Mesh(geometry, material);
    scene.add(quantumField);
}

function createQubits(count) {
    const positions = [
        { x: -2.5, y: 0.5, z: -1 },   // q0
        { x: -0.8, y: 0.5, z: -1 },   // q1
        { x: 0.8, y: 0.5, z: -1 },    // q2
        { x: 2.5, y: 0.5, z: -1 }     // q3
    ];
    
    for (let i = 0; i < Math.min(count, positions.length); i++) {
        const pos = positions[i];
        
        // Create qubit sphere
        const geometry = new THREE.SphereGeometry(0.6, 64, 64);
        const material = new THREE.MeshStandardMaterial({
            color: COLORS.IDLE,
            emissive: 0x112233,
            metalness: 0.7,
            roughness: 0.3,
            emissiveIntensity: 0.5
        });
        
        const qubit = new THREE.Mesh(geometry, material);
        qubit.position.set(pos.x, pos.y, pos.z);
        qubit.castShadow = true;
        qubit.receiveShadow = true;
        qubit.userData = { index: i, state: 'idle', angle: 0 };
        
        scene.add(qubit);
        
        // Add orbit ring around qubit
        const ringGeometry = new THREE.TorusGeometry(0.8, 0.05, 32, 100);
        const ringMaterial = new THREE.MeshStandardMaterial({
            color: COLORS.IDLE,
            emissive: 0x00ffcc,
            emissiveIntensity: 0.3
        });
        const ring = new THREE.Mesh(ringGeometry, ringMaterial);
        ring.rotation.x = Math.PI / 2;
        qubit.add(ring);
        
        // Add label
        const canvas = document.createElement('canvas');
        canvas.width = 128;
        canvas.height = 64;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#00ffcc';
        ctx.font = 'Bold 20px Arial';
        ctx.fillText(`q${i}`, 10, 30);
        
        const texture = new THREE.CanvasTexture(canvas);
        const labelMaterial = new THREE.SpriteMaterial({ map: texture });
        const label = new THREE.Sprite(labelMaterial);
        label.scale.set(0.8, 0.4, 1);
        label.position.set(0, -0.8, 0);
        qubit.add(label);
        
        qubits.push({ mesh: qubit, ring: ring, state: 'idle' });
    }
    
    // Add entanglement lines between qubits
    addEntanglementLines();
}

function addEntanglementLines() {
    for (let i = 0; i < qubits.length - 1; i++) {
        const points = [];
        points.push(qubits[i].mesh.position.clone());
        points.push(qubits[i + 1].mesh.position.clone());
        
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const material = new THREE.LineBasicMaterial({ color: 0xff00ff, transparent: true, opacity: 0.3 });
        const line = new THREE.Line(geometry, material);
        scene.add(line);
    }
}

function addQuantumParticles() {
    const particleCount = 500;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    
    for (let i = 0; i < particleCount; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 30;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 15;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 20 - 5;
    }
    
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    const material = new THREE.PointsMaterial({
        color: 0x00ffcc,
        size: 0.05,
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending
    });
    
    const particleSystem = new THREE.Points(geometry, material);
    scene.add(particleSystem);
    
    // Store for animation
    particles.push(particleSystem);
}

function addGridFloor() {
    // Quantum grid floor
    const gridHelper = new THREE.GridHelper(20, 40, 0x00ffcc, 0x3366ff);
    gridHelper.position.y = -1.5;
    gridHelper.material.transparent = true;
    gridHelper.material.opacity = 0.3;
    scene.add(gridHelper);
    
    // Add glow effect at floor
    const glowGeometry = new THREE.PlaneGeometry(15, 10);
    const glowMaterial = new THREE.MeshBasicMaterial({
        color: 0x00ffcc,
        transparent: true,
        opacity: 0.05,
        side: THREE.DoubleSide
    });
    const glowFloor = new THREE.Mesh(glowGeometry, glowMaterial);
    glowFloor.rotation.x = -Math.PI / 2;
    glowFloor.position.y = -1.4;
    scene.add(glowFloor);
}

// Animate quantum states based on audit result
function animateQuantumStates(result) {
    if (!qubits.length) return;
    
    const isSafe = result.verdict === 'SAFE';
    const confidence = result.confidence;
    const hasVulnerability = result.attack_type !== null;
    
    qubits.forEach((qubit, idx) => {
        let targetColor;
        let intensity;
        
        if (isSafe) {
            // Safe: Mostly |0⟩ states (green)
            targetColor = COLORS.MEASURED_0;
            intensity = 0.5 + confidence * 0.5;
        } else if (hasVulnerability) {
            // Vulnerable: Show |1⟩ states (red) with entanglement
            targetColor = COLORS.MEASURED_1;
            intensity = 0.8;
            
            // Make vulnerable qubits pulse red
            const scale = 1 + Math.sin(Date.now() * 0.008) * 0.1;
            qubit.mesh.scale.setScalar(scale);
        } else {
            // Uncertain: Superposition (cyan)
            targetColor = COLORS.SUPERPOSITION;
            intensity = 0.6;
        }
        
        // Smooth color transition
        qubit.mesh.material.color.setHex(targetColor);
        qubit.mesh.material.emissiveIntensity = intensity;
        
        // Rotate orbit ring
        if (qubit.ring) {
            qubit.ring.rotation.z += 0.02;
        }
        
        // Add quantum fluctuation
        const bob = Math.sin(Date.now() * 0.005 + idx) * 0.05;
        qubit.mesh.position.y = 0.5 + bob;
    });
}

// Update circuit visualization based on qubit count
function updateCircuitVisualization(nQubits) {
    // Show/hide qubits based on actual count
    qubits.forEach((qubit, idx) => {
        qubit.mesh.visible = idx < nQubits;
    });
    
    // Update camera to show all qubits
    if (nQubits <= 2) {
        camera.position.set(3, 2, 6);
    } else if (nQubits <= 4) {
        camera.position.set(5, 3, 8);
    } else {
        camera.position.set(7, 4, 10);
    }
    camera.lookAt(0, 0, 0);
}

// Create quantum gate visualization
function addQuantumGate(position, gateType) {
    const gateColors = {
        'H': 0x00ffcc,   // Hadamard - cyan
        'X': 0xff00ff,   // Pauli-X - magenta
        'Z': 0x3366ff,   // Pauli-Z - blue
        'CNOT': 0xff6600 // CNOT - orange
    };
    
    const geometry = new THREE.BoxGeometry(0.5, 0.5, 0.1);
    const material = new THREE.MeshStandardMaterial({
        color: gateColors[gateType] || 0xffffff,
        emissive: 0x442200,
        metalness: 0.8,
        roughness: 0.2
    });
    
    const gate = new THREE.Mesh(geometry, material);
    gate.position.set(position.x, position.y, position.z);
    scene.add(gate);
    
    // Add gate label
    const canvas = document.createElement('canvas');
    canvas.width = 64;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ffffff';
    ctx.font = 'Bold 24px Arial';
    ctx.fillText(gateType, 15, 40);
    
    const texture = new THREE.CanvasTexture(canvas);
    const labelMaterial = new THREE.SpriteMaterial({ map: texture });
    const label = new THREE.Sprite(labelMaterial);
    label.scale.set(0.4, 0.4, 1);
    gate.add(label);
    
    return gate;
}

// Create quantum probability wave effect
function createProbabilityWave(probability, isVulnerable) {
    const waveCount = 30;
    const waves = [];
    const color = isVulnerable ? 0xff0000 : 0x00ffcc;
    
    for (let i = 0; i < waveCount; i++) {
        const radius = 0.5 + i * 0.15;
        const geometry = new THREE.TorusGeometry(radius, 0.03, 32, 100);
        const material = new THREE.MeshBasicMaterial({
            color: color,
            transparent: true,
            opacity: probability * (1 - i / waveCount),
            blending: THREE.AdditiveBlending
        });
        const wave = new THREE.Mesh(geometry, material);
        wave.rotation.x = Math.PI / 2;
        scene.add(wave);
        waves.push(wave);
    }
    
    // Animate waves expanding
    let expand = 0;
    const interval = setInterval(() => {
        expand += 0.05;
        waves.forEach((wave, idx) => {
            const scale = 1 + expand + idx * 0.1;
            wave.scale.setScalar(scale);
            if (wave.material) {
                wave.material.opacity = probability * (1 - (idx / waveCount) - expand * 0.5);
            }
        });
        
        if (expand > 2) {
            clearInterval(interval);
            waves.forEach(wave => scene.remove(wave));
        }
    }, 50);
}

// Main animation loop
function animate() {
    animationId = requestAnimationFrame(animate);
    
    // Rotate quantum field background
    if (quantumField) {
        quantumField.rotation.y += 0.002;
        quantumField.rotation.x += 0.001;
    }
    
    // Animate particles
    particles.forEach(particleSystem => {
        particleSystem.rotation.y += 0.005;
        particleSystem.rotation.x += 0.003;
    });
    
    // Camera orbit (slow)
    const time = Date.now() * 0.0005;
    camera.position.x = 5 + Math.sin(time) * 0.5;
    camera.position.z = 8 + Math.cos(time * 0.7) * 0.5;
    camera.lookAt(0, 0, 0);
    
    renderer.render(scene, camera);
}

function onWindowResize() {
    const container = document.getElementById('canvas-container');
    if (!container) return;
    
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

// Clean up animation
function cleanup3DVisualization() {
    if (animationId) {
        cancelAnimationFrame(animationId);
    }
    if (renderer) {
        renderer.dispose();
    }
}

// Export functions for use in main.js
window.init3DVisualization = init3DVisualization;
window.animateQuantumStates = animateQuantumStates;
window.updateCircuitVisualization = updateCircuitVisualization;
window.addQuantumGate = addQuantumGate;
window.createProbabilityWave = createProbabilityWave;
window.cleanup3DVisualization = cleanup3DVisualization;