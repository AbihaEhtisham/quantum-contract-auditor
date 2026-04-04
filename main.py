# main.py
#!/usr/bin/env python3
"""
Quantum-Enhanced Smart Contract Auditor
Main Orchestrator - CLI Interface

Usage:
    python main.py --command "ADMIN MINT TOKEN"
    python main.py --demo
    python main.py --interactive
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.grammar import ContractGrammar, GrammarValidator
from core.circuit_builder import CircuitBuilder
from core.quantum_walk import QuantumWalkSimulator
from core.verdict import VerdictEngine
from scenarios.safe_contracts import SAFE_SCENARIOS
from scenarios.attack_contracts import ATTACK_SCENARIOS
from visualizer.dashboard import AuditDashboard
from visualizer.plots import PlotGenerator


class QuantumContractAuditor:
    """Main orchestrator for the quantum-enhanced auditor."""
    
    def __init__(self):
        self.grammar = ContractGrammar()
        self.validator = GrammarValidator()
        self.circuit_builder = CircuitBuilder()
        self.walk_sim = QuantumWalkSimulator()
        self.verdict_engine = VerdictEngine()
        self.dashboard = AuditDashboard()
        self.plotter = PlotGenerator()
        
        self.all_scenarios = {
            **{f"safe_{i}": s for i, s in enumerate(SAFE_SCENARIOS)},
            **{f"attack_{i}": s for i, s in enumerate(ATTACK_SCENARIOS)}
        }
    
# In main.py, replace the audit_command method with this:

    def audit_command(self, command: str, show_dashboard: bool = True, scenario: dict = None) -> Dict[str, Any]:
        """
        Audit a single transaction command.
        
        Args:
            command: DSL command like "ADMIN MINT TOKEN"
            show_dashboard: Whether to show rich dashboard
            scenario: Optional scenario dict for dashboard
        
        Returns:
            Dictionary with full audit results
        """
        # Phase 1: Grammar Validation
        grammar_result = self.validator.validate(command)
        
        # Phase 2: Quantum Circuit Generation
        circuit_result = self.circuit_builder.build(command)
        
        # Phase 3: Quantum Walk
        walk_result = self.walk_sim.run(command, steps=10)
        
        # Phase 4: Verdict
        verdict = self.verdict_engine.combine_verdicts(
            grammar_result=grammar_result,
            circuit_result=circuit_result,
            walk_result=walk_result
        )
        
        result = {
            "command": command,
            "grammar": grammar_result,
            "circuit": circuit_result,
            "quantum_walk": walk_result,
            "verdict": verdict,
            "timestamp": time.time()
        }
        
        if show_dashboard:
            # Import dashboard adapter
            from core.dashboard_adapter import DashboardAdapter
            
            # Convert to dashboard-compatible report
            report = DashboardAdapter.convert(command, grammar_result, circuit_result, walk_result, verdict, scenario)
            
            # Create scenario dict for dashboard
            simple_scenario = scenario or {
                'id': 'CUSTOM',
                'command': command,
                'description': 'Manual audit transaction',
                'attack_type': verdict.get('attack_type', 'None')
            }
            
            # Start dashboard if not already started
            if not hasattr(self, '_dashboard_started'):
                self.dashboard.start()
                self._dashboard_started = True
            
            # Audit the scenario using dashboard's method
            self.dashboard.audit_scenario(simple_scenario, report)
        
        return result
    
    def run_demo(self):
        """Run full demo with all scenarios."""
        print("\n" + "="*70)
        print("🔬 QUANTUM-ENHANCED SMART CONTRACT AUDITOR")
        print("   Full Demo Mode - All Scenarios")
        print("="*70 + "\n")
        
        results = []
        
        # Demo safe scenarios first
        print("\n📋 SECTION 1: SAFE TRANSACTIONS (Should pass)")
        print("-" * 50)
        for scenario in SAFE_SCENARIOS:
            print(f"\n🔹 Auditing: {scenario['command']}")
            print(f"   Description: {scenario['description']}")
            
            result = self.audit_command(scenario['command'], show_dashboard=False)
            results.append(result)
            
            # Simple console output
            verdict_icon = "✅" if result['verdict']['final_verdict'] == "SAFE" else "❌"
            print(f"   {verdict_icon} Verdict: {result['verdict']['final_verdict']}")
            print(f"   Confidence: {result['verdict']['confidence']:.1%}")
            
            time.sleep(0.5)  # Small pause for readability
        
        # Demo attack scenarios
        print("\n\n📋 SECTION 2: ATTACK SCENARIOS (Should fail)")
        print("-" * 50)
        for scenario in ATTACK_SCENARIOS:
            print(f"\n🔹 Auditing: {scenario['command']}")
            print(f"   Description: {scenario['description']}")
            print(f"   Attack Type: {scenario['attack_type']}")
            
            result = self.audit_command(scenario['command'], show_dashboard=False)
            results.append(result)
            
            verdict_icon = "✅" if result['verdict']['final_verdict'] == "SAFE" else "❌"
            print(f"   {verdict_icon} Verdict: {result['verdict']['final_verdict']}")
            print(f"   Confidence: {result['verdict']['confidence']:.1%}")
            
            time.sleep(0.5)
        
        # Summary
        print("\n\n" + "="*70)
        print("📊 DEMO SUMMARY")
        print("="*70)
        
        safe_count = sum(1 for r in results if r['verdict']['final_verdict'] == "SAFE")
        vulnerable_count = len(results) - safe_count
        
        print(f"\nTotal Scenarios: {len(results)}")
        print(f"✅ Safe: {safe_count}")
        print(f"❌ Vulnerable: {vulnerable_count}")
        
        accuracy = safe_count / len(SAFE_SCENARIOS) if SAFE_SCENARIOS else 0
        detection_rate = vulnerable_count / len(ATTACK_SCENARIOS) if ATTACK_SCENARIOS else 0
        
        print(f"\n📈 Performance:")
        print(f"   Safe Transaction Accuracy: {accuracy:.1%}")
        print(f"   Vulnerability Detection Rate: {detection_rate:.1%}")
        
        # Ask about generating figures
        print("\n" + "="*70)
        generate = input("\n📊 Generate publication-quality figures? (y/n): ").lower()
        if generate == 'y':
            # Get a sample circuit for demo
            sample_result = self.audit_command("ADMIN MINT TOKEN", show_dashboard=False)
            circuit = sample_result['circuit'].get('circuit')
            counts = sample_result['circuit'].get('measurement_counts')
            
            self.plotter.generate_all_figures(circuit, counts)
        
        return results
    
    def interactive_mode(self):
        """Interactive CLI for real-time auditing."""
        print("\n" + "="*70)
        print("🔬 QUANTUM-ENHANCED SMART CONTRACT AUDITOR")
        print("   Interactive Mode")
        print("="*70)
        print("\nCommands:")
        print("  - Enter a DSL command (e.g., 'ADMIN MINT TOKEN')")
        print("  - Type 'help' for examples")
        print("  - Type 'quit' to exit")
        print("-" * 50)
        
        # Start dashboard
        self.dashboard.start()
        
        scenario_counter = 1
        
        while True:
            try:
                user_input = input("\n🔍 Enter command to audit: ").strip().upper()
                
                if user_input == 'QUIT':
                    # Show summary before exiting
                    if hasattr(self.dashboard, '_reports') and self.dashboard._reports:
                        self.dashboard.show_summary()
                    print("\n👋 Goodbye!")
                    break
                elif user_input == 'HELP':
                    print("\n📚 Example commands:")
                    print("   SAFE:     ADMIN MINT TOKEN")
                    print("   SAFE:     USER TRANSFER FUNDS")
                    print("   UNSAFE:   CALL WITHDRAW BALANCE")
                    print("   UNSAFE:   TRANSFER FUNDS CALL")
                    print("   UNSAFE:   MINT TOKEN")
                    continue
                
                if user_input:
                    # Create scenario for this command
                    scenario = {
                        'id': f"INT_{scenario_counter}",
                        'command': user_input,
                        'description': 'Interactive audit'
                    }
                    
                    result = self.audit_command(user_input, show_dashboard=True, scenario=scenario)
                    scenario_counter += 1
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n⚠️ Error: {e}")
                import traceback
                traceback.print_exc()


# Replace the main() function in main.py with this:

def main():
    parser = argparse.ArgumentParser(
        description="Quantum-Enhanced Smart Contract Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--command', '-c',
        type=str,
        help='Single command to audit (e.g., "ADMIN MINT TOKEN")'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode'
    )
    
    parser.add_argument(
        '--generate-figures', '-g',
        action='store_true',
        help='Generate publication-quality figures'
    )
    
    args = parser.parse_args()
    
    auditor = QuantumContractAuditor()
    
    if args.generate_figures:
        print("📊 Generating publication-quality figures...")
        sample_result = auditor.audit_command("ADMIN MINT TOKEN", show_dashboard=False)
        circuit = sample_result['circuit'].get('circuit')
        counts = sample_result['circuit'].get('measurement_counts')
        auditor.plotter.generate_all_figures(circuit, counts)
    
    elif args.command:
        result = auditor.audit_command(args.command)
        verdict = result['verdict']['final_verdict']
        confidence = result['verdict']['confidence']
        
        if verdict == "SAFE":
            print(f"\n✅ VERDICT: {verdict} (Confidence: {confidence:.1%})")
        else:
            print(f"\n❌ VERDICT: {verdict} (Confidence: {confidence:.1%})")
            if result['verdict'].get('attack_type'):
                print(f"   Attack Pattern: {result['verdict']['attack_type']}")
    
    elif args.interactive:
        auditor.interactive_mode()
    
    else:
        parser.print_help()
        print("\n📌 Quick start:")
        print("   python main.py --command 'ADMIN MINT TOKEN'")
        print("   python main.py --interactive")


if __name__ == "__main__":
    main()