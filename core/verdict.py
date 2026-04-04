# core/verdict.py (COMPLETE WORKING VERSION)
"""
Verdict Engine - Combines all audit results
"""

from typing import Dict, Any

class VerdictEngine:
    """Combines grammar, circuit, and quantum walk results."""
    
    def __init__(self):
        # Weights for ensemble
        self.weights = {
            'grammar': 0.50,      # Grammar is most important
            'circuit': 0.30,      # Quantum circuit results
            'quantum_walk': 0.20   # Walk simulation
        }
    
    def combine_verdicts(self, 
                        grammar_result: Dict[str, Any],
                        circuit_result: Dict[str, Any],
                        walk_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine all audit results into final verdict.
        
        Args:
            grammar_result: Results from grammar validation
            circuit_result: Results from quantum circuit
            walk_result: Results from quantum walk
            
        Returns:
            Final verdict dictionary
        """
        # Extract individual verdicts
        grammar_safe = grammar_result.get('is_valid', False)
        grammar_confidence = grammar_result.get('confidence', 0.5)
        
        circuit_safe = not circuit_result.get('is_vulnerable', True)
        circuit_probability = circuit_result.get('safe_probability', 0.5)
        
        walk_safe = not walk_result.get('is_vulnerable', True)
        walk_probability = walk_result.get('acceptance_probability', 0.5)
        
        # Calculate weighted score
        weighted_score = (
            self.weights['grammar'] * (grammar_confidence if grammar_safe else 1 - grammar_confidence) +
            self.weights['circuit'] * circuit_probability +
            self.weights['quantum_walk'] * walk_probability
        )
        
        # Determine final verdict
        is_safe = weighted_score >= 0.6
        
        # Calculate overall confidence
        confidence = weighted_score if is_safe else 1 - weighted_score
        confidence = max(0.5, min(0.95, confidence))  # Clamp between 0.5 and 0.95
        
        # Get attack type if vulnerable
        attack_type = None
        if not is_safe:
            attack_type = grammar_result.get('attack_type')
            if not attack_type:
                attack_type = self._detect_attack_from_all(grammar_result, circuit_result, walk_result)
        
        return {
            'final_verdict': 'SAFE' if is_safe else 'VULNERABLE',
            'confidence': confidence,
            'weighted_score': weighted_score,
            'attack_type': attack_type,
            'components': {
                'grammar': {'safe': grammar_safe, 'confidence': grammar_confidence},
                'circuit': {'safe': circuit_safe, 'probability': circuit_probability},
                'quantum_walk': {'safe': walk_safe, 'probability': walk_probability}
            }
        }
    
    def _detect_attack_from_all(self, grammar_result, circuit_result, walk_result) -> str:
        """Detect attack type from all components."""
        cmd = grammar_result.get('command', '').lower()
        
        if 'call' in cmd and 'withdraw' in cmd:
            return "Reentrancy Attack"
        elif 'overflow' in cmd:
            return "Integer Overflow"
        elif 'mint' in cmd and 'admin' not in cmd:
            return "Unauthorized Minting"
        elif 'transfer' in cmd and 'call' in cmd:
            return "Interaction Before Effect"
        else:
            return "Grammar Security Violation"


class AuditReport:
    """Compatibility class for dashboard - holds all audit results."""
    
    def __init__(self, command: str, scenario_id: str = None):
        self.command = command
        self.scenario_id = scenario_id or command[:20]
        
        # Grammar results
        self.grammar_verdict = "SAFE"
        self.violated_rule = None
        self.attack_type = None
        self.parse_time_ms = 0.0
        self.cfg_path = []
        self.tokens = []
        
        # Walk results
        self.walk_verdict = "SAFE"
        self.walk_safe_prob = 0.0
        self.walk_vuln_prob = 0.0
        self.paths_explored = 0
        self.classical_path = []
        self.walk_time_ms = 0.0
        
        # Circuit results
        self.circuit_verdict = "SAFE"
        self.n_qubits = 0
        self.circuit_depth = 0
        self.gate_count = 0
        self.measurement_counts = {}
        self.prob_safe = 0.0
        self.prob_vulnerable = 0.0
        self.sim_time_ms = 0.0
        
        # Final verdict
        self.is_safe = True
        self.final_confidence = 0.0
        self.risk_level = "LOW"
        self.total_time_ms = 0.0
        
        # Additional
        self.explanation = ""
        self.solidity_analog = ""
        self.real_world_incident = ""