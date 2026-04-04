# core/circuit_builder.py (Qiskit 1.0+ compatible)
"""
Quantum Circuit Builder - Converts grammar into quantum circuits
"""

import numpy as np
from typing import Dict, Any, Optional

# Qiskit 1.0+ imports
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

class CircuitBuilder:
    """Builds quantum circuits from transaction commands."""
    
    def __init__(self):
        self.simulator = AerSimulator()
    
    def build(self, command: str) -> Dict[str, Any]:
        """
        Build quantum circuit for a command.
        
        Args:
            command: DSL command string
            
        Returns:
            Dictionary with circuit and measurement results
        """
        # Tokenize command
        tokens = command.lower().split()
        
        # Determine number of qubits based on command complexity
        n_qubits = min(len(tokens) + 1, 5)
        n_qubits = max(n_qubits, 2)
        
        # Create quantum circuit
        qc = QuantumCircuit(n_qubits, 1)
        
        # Encode command features into quantum gates
        for i, token in enumerate(tokens):
            if i < n_qubits:
                # Encode token as rotation angle
                angle = hash(token) % 100 / 100.0 * np.pi
                qc.ry(angle, i)
        
        # Add entanglement based on grammar structure
        for i in range(min(len(tokens) - 1, n_qubits - 1)):
            if i + 1 < n_qubits:
                qc.cx(i, i + 1)
        
        # Detect vulnerability patterns
        is_vulnerable = self._detect_vulnerability(tokens)
        
        if is_vulnerable:
            # Add X gate to flip outcome for vulnerable patterns
            qc.x(0)
        
        # Measure first qubit
        qc.measure(0, 0)
        
        # Run simulation
        measurement_counts = self._run_simulation(qc)
        
        # Calculate safe probability
        safe_shots = measurement_counts.get('0', 0)
        total_shots = sum(measurement_counts.values())
        safe_probability = safe_shots / total_shots if total_shots > 0 else 0.5
        
        return {
            'circuit': qc,
            'measurement_counts': measurement_counts,
            'safe_probability': safe_probability,
            'is_vulnerable': is_vulnerable,
            'n_qubits': n_qubits,
            'command': command
        }
    
    def _detect_vulnerability(self, tokens: list) -> bool:
        """Detect vulnerability patterns in tokens."""
        # Reentrancy pattern: CALL before UPDATE
        if 'call' in tokens and 'update' in tokens:
            call_idx = tokens.index('call') if 'call' in tokens else -1
            update_idx = tokens.index('update') if 'update' in tokens else -1
            if call_idx < update_idx and call_idx != -1:
                return True
        
        # Unauthorized access: action without ADMIN
        if ('mint' in tokens or 'burn' in tokens) and 'admin' not in tokens:
            return True
        
        # Overflow pattern
        if 'overflow' in tokens:
            return True
        
        return False
    
    def _run_simulation(self, circuit: QuantumCircuit, shots: int = 1024) -> Dict[str, int]:
        """Run quantum circuit simulation."""
        try:
            # Transpile for simulator
            compiled_circuit = transpile(circuit, self.simulator)
            
            # Run simulation
            job = self.simulator.run(compiled_circuit, shots=shots)
            result = job.result()
            counts = result.get_counts()
            
            return counts
        except Exception as e:
            print(f"⚠️ Simulation error: {e}")
            # Return default counts
            return {'0': shots, '1': 0}
    
    def build_circuit(self, command: str) -> QuantumCircuit:
        """Legacy method for backward compatibility."""
        return self.build(command)['circuit']