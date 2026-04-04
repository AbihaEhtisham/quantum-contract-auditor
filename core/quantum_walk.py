# core/quantum_walk.py (FIXED VERSION)
"""
Quantum Walk Simulator - Graph-based vulnerability search
"""

import numpy as np
import networkx as nx
from typing import Dict, Any, List, Tuple

class QuantumWalkSimulator:
    """Simulates quantum walk on contract state graph."""
    
    def __init__(self):
        self.graph = None
        self.adjacency_matrix = None
    
    def build_graph(self, command: str) -> nx.Graph:
        """Build state graph from command structure."""
        tokens = command.lower().split()
        
        # Create graph with states as nodes
        G = nx.Graph()
        
        # Add nodes for each token
        for i, token in enumerate(tokens):
            G.add_node(i, label=token)
        
        # Add edges between consecutive tokens
        for i in range(len(tokens) - 1):
            G.add_edge(i, i + 1, weight=1.0)
        
        # Add vulnerability edges based on patterns
        if 'call' in tokens and 'update' in tokens:
            call_idx = tokens.index('call') if 'call' in tokens else -1
            update_idx = tokens.index('update') if 'update' in tokens else -1
            if call_idx < update_idx:
                # Add extra edge for vulnerability
                G.add_edge(call_idx, update_idx, weight=0.1, is_vulnerable=True)
        
        self.graph = G
        return G
    
    def run(self, command: str, steps: int = 10) -> Dict[str, Any]:
        """
        Run quantum walk simulation.
        
        Args:
            command: Transaction command
            steps: Number of walk steps
            
        Returns:
            Dictionary with walk results
        """
        # Build graph
        graph = self.build_graph(command)
        
        if graph.number_of_nodes() == 0:
            return {
                'acceptance_probability': 0.5,
                'is_vulnerable': True,
                'steps': steps,
                'command': command
            }
        
        # Create adjacency matrix
        n_nodes = graph.number_of_nodes()
        adj = nx.adjacency_matrix(graph).todense()
        
        # Normalize adjacency matrix (quantum walk coin)
        row_sums = np.array(adj.sum(axis=1)).flatten()
        row_sums = np.where(row_sums == 0, 1, row_sums)
        transition = adj / row_sums[:, np.newaxis]
        
        # Initial state (localized at node 0)
        initial_state = np.zeros(n_nodes)
        initial_state[0] = 1.0
        
        # Quantum walk evolution (simulated)
        current_state = initial_state.copy()
        
        for _ in range(steps):
            # Apply transition
            current_state = current_state @ transition
            # Add quantum interference (simulated)
            current_state = current_state + 0.1 * np.sin(current_state)
            # Renormalize
            current_state = current_state / (np.sum(current_state) + 1e-10)
        
        # Acceptance probability = probability mass at safe states
        # Safe states are those with 'accept' or 'update' in label
        safe_prob = 0
        for node in graph.nodes():
            label = graph.nodes[node].get('label', '')
            if label in ['update', 'balance', 'admin', 'user']:
                safe_prob += current_state[node]
        
        # Check for vulnerability patterns
        is_vulnerable = self._check_vulnerability(command)
        
        # Adjust probability based on vulnerability
        if is_vulnerable:
            safe_prob = 1 - safe_prob
        
        return {
            'acceptance_probability': float(safe_prob),
            'is_vulnerable': is_vulnerable,
            'steps': steps,
            'n_nodes': n_nodes,
            'command': command,
            'transition_matrix': transition.tolist() if n_nodes <= 5 else None
        }
    
    def _check_vulnerability(self, command: str) -> bool:
        """Check if command contains vulnerability patterns."""
        cmd_lower = command.lower()
        
        vulnerability_patterns = [
            'call withdraw',
            'transfer call',
            'overflow',
            'mint token' and 'admin' not in cmd_lower
        ]
        
        for pattern in vulnerability_patterns:
            if isinstance(pattern, str) and pattern in cmd_lower:
                return True
            elif isinstance(pattern, tuple) and pattern[0] in cmd_lower and not pattern[1]:
                return True
        
        return False