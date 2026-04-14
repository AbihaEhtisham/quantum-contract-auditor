<div align="center">

#  Quantum-Enhanced Smart Contract Auditor

**A Formal Grammar Approach to Blockchain Security**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Qiskit](https://img.shields.io/badge/Qiskit-AerSimulator-6929c4?logo=ibm&logoColor=white)](https://qiskit.org)
[![Rich](https://img.shields.io/badge/Rich-Terminal%20UI-brightgreen)](https://github.com/Textualize/rich)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![NUST](https://img.shields.io/badge/NUST-BSCS--14D-red)](https://seecs.nust.edu.pk)

*Theory of Automata and Formal Languages — Final Project*
*SEECS, NUST · Eman Fatima (502571) & Abiha Ehtisham (528907) · Supervised by Dr. Sohail Iqbal*

</div>

---

## Table of Contents

- [Overview](#overview)
- [The Core Idea](#the-core-idea)
- [Pipeline Architecture](#pipeline-architecture)
- [Features](#features)
- [Attack Scenarios](#attack-scenarios)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technical Deep Dive](#technical-deep-dive)
- [References](#references)

---

## Overview

Smart contracts are **immutable once deployed** on the blockchain. A single logic flaw — a missed authorization check, an external call fired before a state update — can drain millions in seconds. Classical auditing tools like Oyente, Slither, and Mythril use static analysis and struggle with the **state explosion problem** in deeply nested contract logic.

This project proposes a **Quantum-Classical Hybrid Auditor** that treats smart contract transaction sequences as a **formal language** and validates them through a three-phase pipeline:

```
DSL Command  ──▶  Grammar Engine  ──▶  Quantum Walk  ──▶  IQP Circuit  ──▶  Verdict
                  (CFG + PDA)          (superposition)     (AerSimulator)    (SAFE / VULNERABLE)
```

The key insight, borrowed from **DisCoCat / QNLP** (Coecke et al., 2020), is that compositional grammar structures and quantum circuit structures share the same underlying categorical mathematics — making it natural to map contract logic into quantum gates.

---

## The Core Idea

### Smart contracts as a formal language

Every transaction can be described as a sequence of tokens:

```
ADMIN   MINT   TOKEN          →  AUTH   UPDATE  UPDATE  →  SAFE ✓
CALL    WITHDRAW  BALANCE     →  CALL   UPDATE  CHECK   →  VULNERABLE ✗ (reentrancy)
```

We define a **Context-Free Grammar (CFG)** whose safe production rule is:

```
SAFE  →  AUTH  CHECK  UPDATE  CALL
```

Any deviation from this ordering — a `CALL` before `UPDATE`, missing `AUTH`, dangerous opcodes — is a grammar violation that maps directly to a known attack class (SWC-107 Reentrancy, SWC-105 Missing Authorization, etc.).

### Why quantum?

A classical auditor walks the CFG state graph **one path at a time**. A quantum walk explores **all paths simultaneously** in superposition using amplitude vectors — providing a conceptual quadratic speedup (Ambainis, 2003) for finding the `q_reject` trap state in the logic tree. The final quantum circuit measurement collapses this superposition into a binary verdict: `|0⟩` = SAFE, `|1⟩` = VULNERABLE.

---

## Pipeline Architecture

```

├──────────────┴─────────────────────┴─────────────────────┴───────────────────  │
│                                                                                │
│         ┌─────────────────────────────────────────────────────────┐            │
│         │           VERDICT ENGINE (Weighted Ensemble)            │            │
│         │   Grammar (50%)  +  Walk (20%)  +  Circuit (30%)        │            │
│         └──────────────────────┬──────────────────────────────────┘            │
│                                ↓                                               │
│              ┌─────────────────┴──────────────────┐                            │
│              ↓                                     ↓                           │
│         ✓ SAFE                               ✗ VULNERABLE                     │
│    Rich Dashboard                          Rich Dashboard                      │
│    Matplotlib Plots                        Attack type + incident              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Verdict weighting rationale

| Component | Weight | Reason |
|-----------|--------|--------|
| Grammar Engine | **50%** | Deterministic, formal, cannot be fooled |
| Quantum Circuit | **30%** | Statistically grounded — 1024 shot measurement |
| Quantum Walk | **20%** | Probabilistic path exploration — advisory signal |

---

## Features

### Phase 1 — Grammar Engine (`core/grammar.py`)
- **6-state PDA** automaton: `q0 → q1 → q2 → q3 → q_accept / q_reject`
- **Token classifier** maps raw DSL words to: `AUTH`, `CHECK`, `UPDATE`, `CALL`, `BAD`, `UNKNOWN`
- **4 CFG safety rules** with CWE cross-references:
  - `R1` — No `CALL` before `UPDATE` (SWC-107, Reentrancy)
  - `R2` — `AUTH` required as first token (SWC-105, Missing Authorization)
  - `R3` — `UPDATE` must precede `CALL` (SWC-107 variant)
  - `R4` — No dangerous opcodes: `OVERFLOW`, `LOOP`, `SELFDESTRUCT` (SWC-101)
- Returns full **state path trace**, violated rule, and parse time

### Phase 2 — Quantum Walk (`core/quantum_walk.py`)
- Builds a **6-node directed graph** matching the PDA states
- Initializes amplitude vector `|ψ⟩ = [1, 0, 0, 0, 0, 0]` at `q0`
- Applies **Grover diffusion step** × 6 iterations → explores 2⁶ = **64 paths simultaneously**
- Outputs `P(q_accept)` vs `P(q_reject)` and a sampled classical path for comparison

### Phase 3 — Quantum Circuit (`core/circuit_builder.py`)
- **IQP Ansatz** architecture: each token class maps to a dedicated gate layer
  - `AUTH` → Hadamard + `Ry(θ)` (superposition + bias)
  - `CHECK` → `Rz(θ)` (phase rotation)
  - `UPDATE` → `Rx(θ)` + `CX` chain (state entanglement)
  - `CALL` → `Ry(θ)` + conditional `X` flip (violation encoding)
  - `BAD` → `X` gates (state corruption)
- Runs on **Qiskit AerSimulator** with **1024 shots**
- Verdict qubit (MSB): `|0⟩ dominant` → SAFE, `|1⟩ dominant` → VULNERABLE

### Verdict Engine (`core/verdict.py`)
- Weighted ensemble combining all three phase outputs
- Returns `AuditReport` with confidence score, risk level, attack type, and pipeline timings

### Rich Dashboard (`visualizer/dashboard.py`)
- **Animated 3-phase reveal** with spinners and progress indicators
- Color-coded panels: green for SAFE, red for VULNERABLE
- **Text-based measurement histogram** (`█` bars for each bitstring outcome)
- Solidity code analog with syntax highlighting
- Full **session summary table** in demo mode

### Matplotlib Figures (`visualizer/plots.py`)
Four publication-quality dark-theme figures saved to `outputs/`:
- **Fig 1** — CFG state transition diagram (full PDA with accept/reject paths)
- **Fig 2** — Measurement histogram + SAFE/VULNERABLE pie chart
- **Fig 3** — Quantum walk amplitude evolution + heatmap
- **Fig 4** — Session comparison: all scenarios side by side

---

## Attack Scenarios

### Safe scenarios (expected verdict: SAFE ✓)

| ID | Command | Description |
|----|---------|-------------|
| S1 | `ADMIN MINT TOKEN` | Admin token minting with full AUTH → UPDATE order |
| S2 | `USER TRANSFER FUNDS` | Standard CEI-compliant fund transfer |
| S3 | `ADMIN BURN TOKEN` | Token burn — highest confidence safe pattern |
| S4 | `OWNER APPROVE SPENDER` | ERC-20 approval with correct state ordering |

### Attack scenarios (expected verdict: VULNERABLE ✗)

| ID | Command | Attack Type | Real-World Incident |
|----|---------|-------------|---------------------|
| A1 | `CALL WITHDRAW BALANCE` | Reentrancy (SWC-107) | The DAO Hack, June 2016 — **$60M drained** |
| A2 | `TRANSFER FUNDS CALL` | Missing Authorization (SWC-105) | Parity Wallet Bug, 2017 — **$30M frozen** |
| A3 | `CALL BALANCE OVERFLOW` | Overflow + Reentrancy (SWC-101 + SWC-107) | BeautyChain (BEC) Token, 2018 — **$900M at risk** |
| A4 | `LOOP CALL WITHDRAW` | Cross-Function Reentrancy (SWC-107 advanced) | Cream Finance, August 2021 — **$130M drained** |
| A5 | `USER CALL UPDATE` | Missing CEI Pattern (SWC-107) | Agave + Hundred Finance, 2022 — **$11M** |

---

## Installation

### Prerequisites

- Python **3.9 or higher**
- pip

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/quantum-contract-auditor.git
cd quantum-contract-auditor

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

### Requirements

```
qiskit>=1.0.0
qiskit-aer>=0.14.0
pytket-qiskit>=0.50.0
lambeq>=0.4.0
matplotlib>=3.7.0
networkx>=3.1
numpy>=1.24.0
rich>=13.0.0
pytest>=7.4.0
```

> **Note:** All simulation runs **locally**. No IBM Quantum account or cloud access is required. The quantum circuit is simulated classically via `AerSimulator`.

---

## Usage

### Audit a single command

```bash
python main.py --command "ADMIN MINT TOKEN"
python main.py --command "CALL WITHDRAW BALANCE"

# With matplotlib visualizations
python main.py --command "ADMIN MINT TOKEN" --plots
```

### Demo mode — all 9 scenarios (recommended for presentation)

```bash
python main.py --demo

# With plots and custom animation speed
python main.py --demo --plots --delay 1.2
```

### Run a specific scenario by ID

```bash
python main.py --scenario A1      # DAO reentrancy attack
python main.py --scenario S3      # Admin burn (safe)
python main.py --scenario A3 --plots
```

### List all available scenarios

```bash
python main.py --list
```

### Run the test suite

```bash
python -m pytest tests/test_scenarios.py -v
```

### CLI reference

```
usage: main.py [-h] (--command CMD | --demo | --scenario ID | --list)
               [--plots] [--delay SECONDS]

Options:
  --command, -c   DSL command string to audit
  --demo,    -d   Run all scenarios in demo mode
  --scenario,-s   Run a specific scenario by ID (e.g. A1, S2)
  --list,    -l   Print all available scenarios and exit
  --plots,   -p   Generate matplotlib figures after each audit
  --delay         Animation step delay in seconds (default: 0.9)
```

---

## Project Structure

```
quantum-contract-auditor/
│
├── core/                          ← Pipeline engine modules
│   ├── __init__.py
│   ├── grammar.py                 ← Phase 1: CFG + 6-state PDA state machine
│   ├── quantum_walk.py            ← Phase 2: Grover-step walk over CFG graph
│   ├── circuit_builder.py         ← Phase 3: IQP Ansatz + Qiskit AerSimulator
│   └── verdict.py                 ← Weighted ensemble verdict engine
│
├── scenarios/                     ← Pre-defined DSL scenarios
│   ├── __init__.py
│   ├── safe_contracts.py          ← 4 SAFE scenarios with Solidity analogs
│   └── attack_contracts.py        ← 5 VULNERABLE scenarios with incident data
│
├── visualizer/                    ← Output & display modules
│   ├── __init__.py
│   ├── dashboard.py               ← Rich animated terminal dashboard
│   └── plots.py                   ← Matplotlib dark-theme publication figures
│
├── tests/                         ← pytest test suite
│   └── test_scenarios.py          ← Verdict correctness + pipeline integrity tests
│
├── outputs/                       ← Generated figures & diagrams
│   └── architecture_diagram.xml   ← draw.io architecture diagram
│
├── main.py                        ← CLI entry point & orchestrator
├── requirements.txt               ← Pinned dependencies
└── README.md                      ← This file
```

---

## Technical Deep Dive

### Grammar token classification

```python
AUTH_TOKENS   = {"ADMIN", "USER", "OWNER", "OPERATOR", "GOVERNANCE"}
CHECK_TOKENS  = {"CHECK", "VERIFY", "BALANCE", "REQUIRE", "ASSERT"}
UPDATE_TOKENS = {"MINT", "BURN", "TRANSFER", "UPDATE", "FUNDS", "TOKEN", ...}
CALL_TOKENS   = {"CALL", "SEND", "DELEGATE", "INVOKE", "EXECUTE"}
BAD_TOKENS    = {"OVERFLOW", "UNDERFLOW", "LOOP", "RECURSIVE", "SELFDESTRUCT"}
```

### PDA state transitions

```
q0 ──AUTH──▶ q1 ──CHECK──▶ q2 ──UPDATE──▶ q3 ──CALL──▶ q_accept  ✓ SAFE
q0 ──CALL──▶ q_reject                                               ✗ R1: Reentrancy
q1 ──CALL──▶ q_reject                                               ✗ R3: No check
q2 ──CALL──▶ q_reject                                               ✗ R1: No update
q* ──BAD───▶ q_reject                                               ✗ R4: Dangerous opcode
```

### Quantum gate mapping (IQP Ansatz)

| Token class | Gate applied | Purpose |
|-------------|-------------|---------|
| `AUTH` | `H + Ry(0.314)` | Superposition + authorization bias |
| `CHECK` | `Rz(0.628)` | Phase rotation — verification oracle |
| `UPDATE` | `Rx(0.942) + CX` | State entanglement — update dependency |
| `CALL` | `Ry(1.256) [+ X if violation]` | External call; X flip encodes reentrancy |
| `BAD` | `X` on all qubits | Full state corruption |

### Verdict ensemble formula

```
P(SAFE)_final = 0.50 × Grammar_safe
              + 0.20 × Walk_P(q_accept)
              + 0.30 × Circuit_P(|0⟩)

Verdict = SAFE if P(SAFE)_final > 0.50 else VULNERABLE
```

---

## References

1. **Coecke, B., Sadrzadeh, M., Clark, S.** (2010). *Mathematical Foundations for a Compositional Distributional Model of Meaning.* Linguistic Analysis, 36(1–4).

2. **Ambainis, A.** (2007). *Quantum Walk Algorithm for Element Distinctness.* SIAM Journal on Computing, 37(1), 210–239.

3. **Kartsaklis, D. et al.** (2021). *lambeq: An Efficient High-Level Python Library for Quantum NLP.* arXiv:2110.04236.

4. **Abraham, H. et al.** (2019). *Qiskit: An Open-Source Framework for Quantum Computing.* IBM Research.

5. **Luu, L. et al.** (2016). *Making Smart Contracts Smarter.* ACM CCS 2016, 254–269.

6. **Bhargavan, K. et al.** (2016). *Formal Verification of Smart Contracts.* ACM PLAS Workshop, CCS 2016.

7. **Feist, J., Grieco, G., Groce, A.** (2019). *Slither: A Static Analysis Framework for Smart Contracts.* IEEE WOSTES 2019.

8. **Coecke, B., Kissinger, A.** (2017). *Picturing Quantum Processes.* Cambridge University Press.

9. **Nielsen, M., Chuang, I.** (2000). *Quantum Computation and Quantum Information.* Cambridge University Press.

10. **Wood, G. et al.** (2014). *Ethereum: A Secure Decentralised Generalised Transaction Ledger.* Ethereum Yellow Paper.

---

<div align="center">

**NUST SEECS · Theory of Automata and Formal Languages · Fall 2025**

Eman Fatima (CMS: 502571) · Abiha Ehtisham (CMS: 528907) · BSCS-14D

*Supervised by Dr. Sohail Iqbal*

</div>
