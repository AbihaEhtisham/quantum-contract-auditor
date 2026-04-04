# core/grammar.py (FIXED VERSION)
"""
Formal Grammar Engine - CFG validation for smart contract transactions
"""

from typing import Dict, Any, List, Tuple

class ContractGrammar:
    """Defines the CFG rules for safe transactions."""
    
    def __init__(self):
        # CFG Production Rules
        self.rules = {
            'S': ['AUTH_CHECK UPDATE CALL', 'AUTH_CHECK UPDATE', 'UPDATE CALL', 'UPDATE'],
            'AUTH_CHECK': ['ADMIN ROLE', 'USER ROLE', 'ADMIN', 'USER'],
            'UPDATE': ['MINT', 'BURN', 'TRANSFER', 'BALANCE_UPDATE'],
            'CALL': ['TOKEN', 'FUNDS', 'EXTERNAL']
        }
        
        # Safe patterns (correct order)
        self.safe_patterns = [
            ['admin', 'mint', 'token'],
            ['user', 'transfer', 'funds'],
            ['admin', 'burn', 'token'],
            ['update', 'balance', 'call', 'transfer'],
            ['auth', 'check', 'update']
        ]
        
        # Unsafe patterns (vulnerabilities)
        self.unsafe_patterns = [
            ['call', 'withdraw', 'balance'],  # Reentrancy
            ['transfer', 'funds', 'call'],     # Interaction before effect
            ['overflow', 'balance', 'check'],  # Integer overflow
            ['mint', 'token'],                 # No authorization
            ['call', 'update']                 # Wrong order
        ]
    
    def parse(self, command: str) -> Dict[str, Any]:
        """Parse command according to CFG rules."""
        tokens = command.lower().split()
        
        # Check if matches any safe pattern
        is_safe = self._matches_pattern(tokens, self.safe_patterns)
        
        # Check if matches any unsafe pattern
        is_unsafe = self._matches_pattern(tokens, self.unsafe_patterns)
        
        # Determine validity
        is_valid = is_safe and not is_unsafe
        
        # Find matching production rule
        production_rule = self._find_production_rule(tokens)
        
        return {
            'is_valid': is_valid,
            'is_safe': is_safe,
            'is_unsafe': is_unsafe,
            'tokens': tokens,
            'production_rule': production_rule,
            'command': command
        }
    
    def _matches_pattern(self, tokens: List[str], patterns: List[List[str]]) -> bool:
        """Check if tokens match any pattern."""
        for pattern in patterns:
            if len(tokens) >= len(pattern):
                # Check if pattern matches start of tokens
                match = True
                for i, p in enumerate(pattern):
                    if i < len(tokens) and p != tokens[i]:
                        match = False
                        break
                if match:
                    return True
        return False
    
    def _find_production_rule(self, tokens: List[str]) -> str:
        """Find matching production rule."""
        if len(tokens) >= 3 and tokens[0] in ['admin', 'user']:
            return "S → AUTH_CHECK UPDATE CALL"
        elif len(tokens) >= 2 and tokens[0] in ['admin', 'user']:
            return "S → AUTH_CHECK UPDATE"
        elif len(tokens) >= 2:
            return "S → UPDATE CALL"
        else:
            return "S → UPDATE"


class GrammarValidator:
    """Validates transactions against safety grammar."""
    
    def __init__(self):
        self.grammar = ContractGrammar()
        
        # State machine for validation (from proposal diagram)
        self.states = ['q0', 'q1', 'q2', 'q3', 'q_accept', 'q_reject']
        self.current_state = 'q0'
        
        # Transition rules
        self.transitions = {
            ('q0', 'auth'): 'q1',
            ('q0', 'admin'): 'q1',
            ('q0', 'user'): 'q1',
            ('q0', 'update'): 'q2',
            ('q0', 'call'): 'q_reject',  # Call before update = reject
            ('q1', 'check'): 'q2',
            ('q1', 'update'): 'q2',
            ('q2', 'update'): 'q3',
            ('q2', 'call'): 'q_reject',  # Call before state update = reject
            ('q3', 'call'): 'q_accept',
            ('*', '*'): 'q_reject'  # Default: reject
        }
    
    def validate(self, command: str) -> Dict[str, Any]:
        """
        Validate command against safety grammar.
        
        Returns:
            Dictionary with validation results
        """
        # First, parse with CFG
        parse_result = self.grammar.parse(command)
        
        # Then run through state machine
        state_result = self._run_state_machine(command)
        
        # Combined result
        is_valid = parse_result['is_valid'] and state_result['accepted']
        
        # Determine attack type if vulnerable
        attack_type = None
        if not is_valid:
            attack_type = self._detect_attack_type(command)
        
        return {
            'is_valid': is_valid,
            'parse_result': parse_result,
            'state_result': state_result,
            'attack_type': attack_type,
            'command': command,
            'confidence': 0.9 if is_valid else 0.85
        }
    
    def _run_state_machine(self, command: str) -> Dict[str, Any]:
        """Run command through state machine."""
        tokens = command.lower().split()
        current = 'q0'
        path = [current]
        
        for token in tokens:
            # Map token to transition key
            trans_key = None
            if token in ['admin', 'user', 'auth']:
                trans_key = 'auth'
            elif token in ['check', 'verify']:
                trans_key = 'check'
            elif token in ['mint', 'burn', 'transfer', 'update', 'balance']:
                trans_key = 'update'
            elif token in ['call', 'withdraw', 'token', 'funds']:
                trans_key = 'call'
            
            if trans_key:
                next_state = self.transitions.get((current, trans_key), self.transitions.get(('*', '*'), 'q_reject'))
                current = next_state
                path.append(current)
            
            if current == 'q_reject':
                break
        
        accepted = current == 'q_accept'
        
        return {
            'accepted': accepted,
            'final_state': current,
            'path': path
        }
    
    def _detect_attack_type(self, command: str) -> str:
        """Detect specific attack type from command."""
        cmd_lower = command.lower()
        
        if 'call' in cmd_lower and 'withdraw' in cmd_lower:
            return "Reentrancy Attack"
        elif 'overflow' in cmd_lower:
            return "Integer Overflow"
        elif 'mint' in cmd_lower and 'admin' not in cmd_lower:
            return "Unauthorized Minting"
        elif 'call' in cmd_lower and 'update' in cmd_lower:
            call_idx = cmd_lower.find('call')
            update_idx = cmd_lower.find('update')
            if call_idx < update_idx:
                return "Reentrancy (Call before Update)"
        elif 'transfer' in cmd_lower and 'call' in cmd_lower:
            return "Interaction Before Effect"
        
        return "Grammar Violation"
    
# Add this to core/grammar.py (after your existing code)

class GrammarEngine:
    """Grammar engine for tokenization and classification."""
    
    def __init__(self):
        self.token_classes = {
            'admin': 'AUTH',
            'user': 'AUTH',
            'auth': 'AUTH',
            'check': 'CHECK',
            'verify': 'CHECK',
            'update': 'UPDATE',
            'mint': 'UPDATE',
            'burn': 'UPDATE',
            'transfer': 'UPDATE',
            'balance': 'UPDATE',
            'call': 'CALL',
            'withdraw': 'CALL',
            'token': 'CALL',
            'funds': 'CALL',
        }
    
    def tokenize(self, command: str) -> list:
        """Tokenize command string."""
        return command.lower().split()
    
    def _classify_token(self, token: str) -> str:
        """Classify token type."""
        return self.token_classes.get(token, 'UNKNOWN')
    
    def parse(self, command: str):
        """Parse command and return report-like object."""
        tokens = self.tokenize(command)
        classes = [self._classify_token(t) for t in tokens]
        
        # Simple CFG path simulation
        cfg_path = []
        for cls in classes:
            if cls == 'AUTH':
                cfg_path.append('q0→q1')
            elif cls == 'CHECK':
                cfg_path.append('q1→q2')
            elif cls == 'UPDATE':
                cfg_path.append('q2→q3')
            elif cls == 'CALL':
                cfg_path.append('q3→q_accept')
            else:
                cfg_path.append('→q_reject')
        
        # Determine verdict
        is_safe = 'AUTH' in classes and classes.index('AUTH') < len(classes) - 1
        if 'CALL' in classes and 'UPDATE' in classes:
            if classes.index('CALL') < classes.index('UPDATE'):
                is_safe = False
        
        # Check for violations
        violated_rule = None
        attack_type = None
        if 'CALL' in classes and 'UPDATE' in classes:
            if classes.index('CALL') < classes.index('UPDATE'):
                violated_rule = "R2: CALL before UPDATE"
                attack_type = "Reentrancy Vulnerability"
        elif 'AUTH' not in classes and ('MINT' in classes or 'BURN' in classes):
            violated_rule = "R1: Missing Authorization"
            attack_type = "Unauthorized Operation"
        
        return type('GrammarResult', (), {
            'command': command,
            'grammar_verdict': 'SAFE' if is_safe else 'VULNERABLE',
            'violated_rule': violated_rule,
            'attack_type': attack_type,
            'parse_time_ms': 0.5,
            'cfg_path': cfg_path,
            'tokens': tokens
        })()