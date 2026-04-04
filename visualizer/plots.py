# visualizer/plots.py
"""
Publication-quality Matplotlib figures for academic presentation.
Generates 4 key visuals:
1. Grammar derivation tree
2. Quantum circuit diagram
3. Measurement histogram (|0⟩ vs |1⟩)
4. State transition automaton
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import networkx as nx
import numpy as np
from pathlib import Path
from qiskit import QuantumCircuit
from qiskit.visualization import plot_histogram, circuit_drawer

class PlotGenerator:
    """Generate all publication-quality figures for the project."""
    
    def __init__(self, output_dir: str = "figures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Set publication-quality style
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams['font.family'] = 'serif'
        plt.rcParams['font.size'] = 11
        plt.rcParams['figure.dpi'] = 150
        plt.rcParams['savefig.dpi'] = 300
        plt.rcParams['figure.figsize'] = (12, 6)
    
    def figure1_grammar_tree(self, save: bool = True) -> plt.Figure:
        """
        Figure 1: Grammar Derivation Tree for SAFE transaction.
        Shows how ADMIN MINT TOKEN parses according to CFG rules.
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 10)
        ax.axis('off')
        ax.set_title("Context-Free Grammar Derivation Tree\nSAFE Transaction: ADMIN MINT TOKEN", 
                     fontsize=14, fontweight='bold', pad=20)
        
        # Define tree structure
        tree = {
            'S': (7, 9),
            'AUTH_CHECK': (3.5, 7),
            'UPDATE': (7, 7),
            'CALL': (10.5, 7),
            'ADMIN': (1.5, 5),
            'ROLE': (3.5, 5),
            'MINT': (5.5, 5),
            'BALANCE_UPDATE': (7, 5),
            'TOKEN': (9.5, 5),
            'TRANSFER': (11.5, 5),
        }
        
        # Draw edges
        edges = [
            ('S', 'AUTH_CHECK'), ('S', 'UPDATE'), ('S', 'CALL'),
            ('AUTH_CHECK', 'ADMIN'), ('AUTH_CHECK', 'ROLE'),
            ('UPDATE', 'MINT'), ('UPDATE', 'BALANCE_UPDATE'),
            ('CALL', 'TOKEN'), ('CALL', 'TRANSFER'),
        ]
        
        for parent, child in edges:
            px, py = tree[parent]
            cx, cy = tree[child]
            ax.annotate('', xy=(cx, cy-0.3), xytext=(px, py-0.3),
                       arrowprops=dict(arrowstyle='->', color='#2E86AB',
                                      lw=2, alpha=0.7))
        
        # Draw nodes with custom styling
        for node, (x, y) in tree.items():
            color = '#A23B72' if node == 'S' else '#F18F01' if node in ['AUTH_CHECK', 'UPDATE', 'CALL'] else '#73AB84'
            box = FancyBboxPatch((x-0.8, y-0.4), 1.6, 0.8,
                                 boxstyle="round,pad=0.1",
                                 facecolor=color, edgecolor='black',
                                 linewidth=2, alpha=0.9)
            ax.add_patch(box)
            ax.text(x, y, node, ha='center', va='center',
                   fontweight='bold', fontsize=10, color='white')
        
        # Add legend
        legend_elements = [
            mpatches.Patch(facecolor='#A23B72', label='Start Symbol (S)', alpha=0.9),
            mpatches.Patch(facecolor='#F18F01', label='Non-terminals', alpha=0.9),
            mpatches.Patch(facecolor='#73AB84', label='Terminals', alpha=0.9),
        ]
        ax.legend(handles=legend_elements, loc='upper left', frameon=True, fontsize=9)
        
        plt.tight_layout()
        if save:
            plt.savefig(self.output_dir / 'figure1_grammar_tree.png', bbox_inches='tight')
            plt.savefig(self.output_dir / 'figure1_grammar_tree.pdf', bbox_inches='tight')
        return fig
    
    def figure2_quantum_circuit(self, circuit: QuantumCircuit = None, save: bool = True) -> plt.Figure:
        """
        Figure 2: Quantum Circuit Diagram (Phase 2).
        Shows IQP ansatz encoding grammar features.
        """
        if circuit is None:
            # Build a representative circuit
            from qiskit import QuantumCircuit
            circuit = QuantumCircuit(4, 1)
            circuit.h([0, 1, 2, 3])
            circuit.rz(0.5, 0)
            circuit.rz(0.8, 1)
            circuit.rz(0.3, 2)
            circuit.rz(0.6, 3)
            circuit.cz(0, 1)
            circuit.cz(1, 2)
            circuit.cz(2, 3)
            circuit.measure(0, 0)
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Use Qiskit's drawer
        circuit_drawer(circuit, output='mpl', ax=ax, 
                      style={'name': 'clifford', 'displaytext': {'fontsize': 10}})
        
        ax.set_title("Quantum Circuit Encoding\nIQP Ansatz for Transaction Validation", 
                    fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        if save:
            plt.savefig(self.output_dir / 'figure2_quantum_circuit.png', bbox_inches='tight')
            plt.savefig(self.output_dir / 'figure2_quantum_circuit.pdf', bbox_inches='tight')
        return fig
    
    def figure3_measurement_histogram(self, counts: dict = None, save: bool = True) -> plt.Figure:
        """
        Figure 3: Measurement Histogram (Phase 3).
        Shows |0⟩ (SAFE) vs |1⟩ (VULNERABLE) probabilities.
        """
        if counts is None:
            # Demo data
            counts = {'0': 892, '1': 132}
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        outcomes = list(counts.keys())
        frequencies = list(counts.values())
        total = sum(frequencies)
        percentages = [f/total * 100 for f in frequencies]
        
        bars = ax.bar(outcomes, percentages, color=['#73AB84', '#D62828'], 
                     edgecolor='black', linewidth=1.5, alpha=0.8)
        
        # Add value labels on bars
        for bar, pct in zip(bars, percentages):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                   f'{pct:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        ax.set_xlabel('Measurement Outcome', fontsize=12, fontweight='bold')
        ax.set_ylabel('Frequency (%)', fontsize=12, fontweight='bold')
        ax.set_title('Quantum Measurement Results\n1024 Shots on AerSimulator', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_ylim(0, 105)
        ax.set_xticklabels(['|0⟩\n(SAFE)', '|1⟩\n(VULNERABLE)'], fontsize=11)
        
        # Add grid
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # Add annotation
        if percentages[0] > 80:
            ax.annotate('✓ HIGH CONFIDENCE', xy=(0, percentages[0]), xytext=(0.5, 90),
                       ha='center', fontsize=10, color='#73AB84', fontweight='bold')
        
        plt.tight_layout()
        if save:
            plt.savefig(self.output_dir / 'figure3_measurement_histogram.png', bbox_inches='tight')
            plt.savefig(self.output_dir / 'figure3_measurement_histogram.pdf', bbox_inches='tight')
        return fig
    
    def figure4_state_automaton(self, save: bool = True) -> plt.Figure:
        """
        Figure 4: State Transition Automaton (from proposal).
        Shows q0 → q1 → q2 → q3 → q_accept with q_reject trap.
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 8)
        ax.axis('off')
        ax.set_title("Pushdown Automaton for Smart Contract Safety\nState Transition Diagram", 
                    fontsize=14, fontweight='bold', pad=20)
        
        # State positions
        states = {
            'q0': (2, 4),
            'q1': (5, 4),
            'q2': (8, 4),
            'q3': (11, 4),
            'q_accept': (11, 1.5),
            'q_reject': (8, 6.5),
        }
        
        # Transitions: (from, to, label, color)
        transitions = [
            ('q0', 'q1', 'AUTH', '#2E86AB'),
            ('q1', 'q2', 'CHECK', '#2E86AB'),
            ('q2', 'q3', 'UPDATE', '#2E86AB'),
            ('q3', 'q_accept', 'CALL ✓', '#73AB84'),
            ('q2', 'q_reject', 'UNSAFE\n(CALL before UPDATE)', '#D62828'),
            ('q1', 'q_reject', 'UNAUTHORIZED', '#D62828'),
            ('q0', 'q_reject', 'INVALID', '#D62828'),
        ]
        
        # Draw transitions
        for from_state, to_state, label, color in transitions:
            x1, y1 = states[from_state]
            x2, y2 = states[to_state]
            
            # Curved path for reject transitions
            if 'reject' in to_state:
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2 + 0.5
                ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                           arrowprops=dict(arrowstyle='->', color=color,
                                          lw=2.5, connectionstyle=f'arc3,rad=0.3'))
            else:
                ax.annotate('', xy=(x2-0.3, y2), xytext=(x1+0.3, y1),
                           arrowprops=dict(arrowstyle='->', color=color,
                                          lw=2.5, shrinkA=5, shrinkB=5))
            
            # Add label
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            ax.text(mid_x, mid_y + 0.2, label, ha='center', va='bottom',
                   fontsize=9, color=color, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))
        
        # Draw states
        for state, (x, y) in states.items():
            if 'accept' in state:
                color = '#73AB84'
                shape = 'doublecircle'
            elif 'reject' in state:
                color = '#D62828'
                shape = 'circle'
            else:
                color = '#F18F01'
                shape = 'circle'
            
            circle = plt.Circle((x, y), 0.5, color=color, ec='black', 
                               linewidth=2, alpha=0.9, zorder=10)
            ax.add_patch(circle)
            ax.text(x, y, state, ha='center', va='center',
                   fontweight='bold', fontsize=11, color='white')
            
            # Start arrow for q0
            if state == 'q0':
                ax.annotate('', xy=(1.3, 4), xytext=(0.5, 4),
                           arrowprops=dict(arrowstyle='->', color='black', lw=2))
                ax.text(0.3, 4.2, 'START', ha='center', fontsize=9, style='italic')
        
        # Add legend
        legend_elements = [
            mpatches.Patch(facecolor='#F18F01', label='Intermediate States', alpha=0.9),
            mpatches.Patch(facecolor='#73AB84', label='Accept State (SAFE)', alpha=0.9),
            mpatches.Patch(facecolor='#D62828', label='Reject State (VULNERABLE)', alpha=0.9),
        ]
        ax.legend(handles=legend_elements, loc='upper left', frameon=True, fontsize=10)
        
        plt.tight_layout()
        if save:
            plt.savefig(self.output_dir / 'figure4_state_automaton.png', bbox_inches='tight')
            plt.savefig(self.output_dir / 'figure4_state_automaton.pdf', bbox_inches='tight')
        return fig
    
    def generate_all_figures(self, circuit: QuantumCircuit = None, counts: dict = None):
        """Generate all four figures for the project."""
        print("📊 Generating publication-quality figures...")
        
        self.figure1_grammar_tree()
        print("  ✓ Figure 1: Grammar Tree")
        
        self.figure2_quantum_circuit(circuit)
        print("  ✓ Figure 2: Quantum Circuit")
        
        self.figure3_measurement_histogram(counts)
        print("  ✓ Figure 3: Measurement Histogram")
        
        self.figure4_state_automaton()
        print("  ✓ Figure 4: State Automaton")
        
        print(f"\n📁 All figures saved to: {self.output_dir}/")
        print("   - PNG (for presentations)")
        print("   - PDF (for publication)")
        
        return True


# Quick test
if __name__ == "__main__":
    plotter = PlotGenerator()
    plotter.generate_all_figures()