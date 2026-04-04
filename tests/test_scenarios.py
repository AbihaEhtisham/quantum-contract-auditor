# tests/test_scenarios.py
"""
Unit tests for all audit scenarios.
Ensures each transaction returns expected verdict.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import QuantumContractAuditor
from scenarios.safe_contracts import SAFE_SCENARIOS
from scenarios.attack_contracts import ATTACK_SCENARIOS


class TestSafeScenarios(unittest.TestCase):
    """Test that safe transactions pass the audit."""
    
    @classmethod
    def setUpClass(cls):
        cls.auditor = QuantumContractAuditor()
    
    def test_all_safe_scenarios(self):
        """All safe scenarios should return SAFE verdict."""
        for scenario in SAFE_SCENARIOS:
            with self.subTest(command=scenario['command']):
                result = self.auditor.audit_command(
                    scenario['command'], 
                    show_dashboard=False
                )
                self.assertEqual(
                    result['verdict']['final_verdict'],
                    "SAFE",
                    f"Command '{scenario['command']}' should be SAFE"
                )
                self.assertGreater(
                    result['verdict']['confidence'],
                    0.7,
                    f"Confidence too low for '{scenario['command']}'"
                )
    
    def test_safe_grammar_validation(self):
        """Safe transactions should pass grammar validation."""
        for scenario in SAFE_SCENARIOS:
            with self.subTest(command=scenario['command']):
                result = self.auditor.validator.validate(scenario['command'])
                self.assertTrue(
                    result['is_valid'],
                    f"Grammar validation failed for '{scenario['command']}'"
                )
    
    def test_safe_quantum_walk(self):
        """Safe transactions should have high acceptance probability."""
        for scenario in SAFE_SCENARIOS:
            with self.subTest(command=scenario['command']):
                result = self.auditor.walk_sim.run(scenario['command'], steps=10)
                self.assertGreater(
                    result['acceptance_probability'],
                    0.5,
                    f"Quantum walk acceptance too low for '{scenario['command']}'"
                )


class TestAttackScenarios(unittest.TestCase):
    """Test that attack scenarios are detected as VULNERABLE."""
    
    @classmethod
    def setUpClass(cls):
        cls.auditor = QuantumContractAuditor()
    
    def test_all_attack_scenarios(self):
        """All attack scenarios should return VULNERABLE."""
        for scenario in ATTACK_SCENARIOS:
            with self.subTest(command=scenario['command']):
                result = self.auditor.audit_command(
                    scenario['command'],
                    show_dashboard=False
                )
                self.assertEqual(
                    result['verdict']['final_verdict'],
                    "VULNERABLE",
                    f"Command '{scenario['command']}' should be VULNERABLE"
                )
                self.assertIn(
                    scenario['attack_type'],
                    result['verdict'].get('attack_type', ''),
                    f"Wrong attack type detected for '{scenario['command']}'"
                )
    
    def test_attack_grammar_failure(self):
        """Attack transactions should fail grammar validation."""
        for scenario in ATTACK_SCENARIOS:
            with self.subTest(command=scenario['command']):
                result = self.auditor.validator.validate(scenario['command'])
                self.assertFalse(
                    result['is_valid'],
                    f"Grammar validation should fail for '{scenario['command']}'"
                )
    
    def test_attack_quantum_walk(self):
        """Attack transactions should have low acceptance probability."""
        for scenario in ATTACK_SCENARIOS:
            with self.subTest(command=scenario['command']):
                result = self.auditor.walk_sim.run(scenario['command'], steps=10)
                self.assertLess(
                    result['acceptance_probability'],
                    0.5,
                    f"Quantum walk acceptance too high for '{scenario['command']}'"
                )
    
    def test_specific_reentrancy_detection(self):
        """Reentrancy attacks should be specifically identified."""
        reentrancy_scenarios = [
            s for s in ATTACK_SCENARIOS 
            if s['attack_type'] == 'Reentrancy'
        ]
        
        for scenario in reentrancy_scenarios:
            with self.subTest(command=scenario['command']):
                result = self.auditor.audit_command(
                    scenario['command'],
                    show_dashboard=False
                )
                self.assertIn(
                    'reentrancy',
                    result['verdict'].get('attack_type', '').lower(),
                    f"Reentrancy not detected in '{scenario['command']}'"
                )


class TestIntegration(unittest.TestCase):
    """Integration tests for the full pipeline."""
    
    @classmethod
    def setUpClass(cls):
        cls.auditor = QuantumContractAuditor()
    
    def test_full_pipeline_no_errors(self):
        """Full pipeline should run without exceptions."""
        commands = [
            "ADMIN MINT TOKEN",
            "USER TRANSFER FUNDS",
            "CALL WITHDRAW BALANCE",
        ]
        
        for command in commands:
            with self.subTest(command=command):
                try:
                    result = self.auditor.audit_command(command, show_dashboard=False)
                    self.assertIn('verdict', result)
                    self.assertIn('final_verdict', result['verdict'])
                except Exception as e:
                    self.fail(f"Pipeline failed for '{command}': {e}")
    
    def test_confidence_scores_reasonable(self):
        """Confidence scores should be between 0 and 1."""
        for scenario in SAFE_SCENARIOS[:2] + ATTACK_SCENARIOS[:2]:
            result = self.auditor.audit_command(scenario['command'], show_dashboard=False)
            confidence = result['verdict']['confidence']
            self.assertGreaterEqual(confidence, 0)
            self.assertLessEqual(confidence, 1)
    
    def test_circuit_generation_consistent(self):
        """Same command should generate similar circuits."""
        command = "ADMIN MINT TOKEN"
        
        result1 = self.auditor.circuit_builder.build(command)
        result2 = self.auditor.circuit_builder.build(command)
        
        # Both should have circuits
        self.assertIsNotNone(result1.get('circuit'))
        self.assertIsNotNone(result2.get('circuit'))


class TestGrammarRules(unittest.TestCase):
    """Test specific grammar rules."""
    
    @classmethod
    def setUpClass(cls):
        cls.validator = GrammarValidator()
    
    def test_auth_before_action_rule(self):
        """Rule: Authorization must happen before action."""
        valid = "ADMIN MINT TOKEN"
        invalid = "MINT TOKEN ADMIN"  # Wrong order
        
        self.assertTrue(self.validator.validate(valid)['is_valid'])
        self.assertFalse(self.validator.validate(invalid)['is_valid'])
    
    def test_update_before_call_rule(self):
        """Rule: Update state before external call."""
        valid = "UPDATE BALANCE CALL TRANSFER"
        invalid = "CALL TRANSFER UPDATE BALANCE"
        
        self.assertTrue(self.validator.validate(valid)['is_valid'])
        self.assertFalse(self.validator.validate(invalid)['is_valid'])
    
    def test_unknown_token_rejection(self):
        """Unknown tokens should be rejected."""
        result = self.validator.validate("RANDOM UNKNOWN COMMAND")
        self.assertFalse(result['is_valid'])


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)