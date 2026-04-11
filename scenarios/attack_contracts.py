"""
scenarios/attack_contracts.py
-------------------
Defines VULNERABLE transaction scenarios — commands that VIOLATE the
CFG safety grammar, triggering the q_reject trap state.

Grammar violations encoded here:
  R1 — CALL before UPDATE  (Reentrancy)
  R2 — Missing AUTH         (Unauthorized access)
  R3 — CALL before CHECK   (Balance not verified)
  R4 — Recursive CALL loop  (DAO-style drain)
"""

ATTACK_SCENARIOS = [
    {
        "id": "A1",
        "command": "CALL WITHDRAW BALANCE",
        "tokens": ["CALL", "WITHDRAW", "BALANCE"],
        "verdict": "VULNERABLE",
        "confidence": 0.93,
        "description": "Classic reentrancy: external CALL fires before state update.",
        "attack_type": "Reentrancy Attack (SWC-107)",
        "cfg_path": ["q0 --CALL--> q_reject"],
        "explanation": (
            "CALL appears as the FIRST token — the external call is made "
            "BEFORE any balance update (UPDATE). This is the exact pattern "
            "that caused the 2016 DAO hack ($60M loss). The grammar rejects "
            "this at q0: CALL cannot transition from the initial state."
        ),
        "solidity_analog": (
            "// VULNERABLE: Classic DAO-style reentrancy\n"
            "function withdraw(uint256 amount) public {\n"
            "    require(balances[msg.sender] >= amount);\n"
            "    (bool success,) = msg.sender.call{value: amount}(''); // CALL FIRST!\n"
            "    balances[msg.sender] -= amount;  // State updated TOO LATE\n"
            "    // Attacker re-enters before this line executes!\n"
            "}"
        ),
        "real_world_incident": "The DAO Hack, June 2016 — $60M drained",
        "qubit_count": 3,
        "circuit_depth": 2,
        "color": "red",
    },
    {
        "id": "A2",
        "command": "TRANSFER FUNDS CALL",
        "tokens": ["TRANSFER", "FUNDS", "CALL"],
        "verdict": "VULNERABLE",
        "confidence": 0.88,
        "description": "Unauthorized transfer: no AUTH token before fund movement.",
        "attack_type": "Missing Authorization (SWC-105)",
        "cfg_path": ["q0 --TRANSFER(no AUTH)--> q_reject"],
        "explanation": (
            "TRANSFER begins the sequence without an AUTH token (ADMIN/USER/OWNER). "
            "The grammar requires AUTH as the mandatory first state transition from q0. "
            "Skipping authorization means anyone can call this function and move funds."
        ),
        "solidity_analog": (
            "// VULNERABLE: No access control\n"
            "function transfer(address to, uint256 amount) public {\n"
            "    // Missing: require(msg.sender == owner) or onlyOwner modifier!\n"
            "    balances[to] += amount;  // Anyone can mint to any address\n"
            "    emit Transfer(address(0), to, amount);\n"
            "}"
        ),
        "real_world_incident": "Parity Wallet Bug, 2017 — $30M frozen",
        "qubit_count": 3,
        "circuit_depth": 2,
        "color": "red",
    },
    {
        "id": "A3",
        "command": "CALL BALANCE OVERFLOW",
        "tokens": ["CALL", "BALANCE", "OVERFLOW"],
        "verdict": "VULNERABLE",
        "confidence": 0.96,
        "description": "Integer overflow combined with premature external call.",
        "attack_type": "Integer Overflow + Reentrancy (SWC-101 + SWC-107)",
        "cfg_path": ["q0 --CALL--> q_reject"],
        "explanation": (
            "Double violation: CALL fires first (reentrancy), AND the OVERFLOW "
            "token signals unchecked arithmetic. Before Solidity 0.8.x, integer "
            "overflow was silent — an attacker could wrap a uint256 to 0 and "
            "then exploit the reentrancy to drain the contract."
        ),
        "solidity_analog": (
            "// VULNERABLE: Overflow + Reentrancy (pre-Solidity 0.8)\n"
            "function deposit(uint256 amount) public {\n"
            "    balances[msg.sender] += amount;  // No overflow check!\n"
            "    // If amount = 2^256 - balances[msg.sender], wraps to 0\n"
            "    (bool ok,) = msg.sender.call{value: amount}(''); // Then CALL\n"
            "}"
        ),
        "real_world_incident": "BeautyChain (BEC) Token, 2018 — $900M at risk",
        "qubit_count": 3,
        "circuit_depth": 2,
        "color": "red",
    },
    {
        "id": "A4",
        "command": "LOOP CALL WITHDRAW",
        "tokens": ["LOOP", "CALL", "WITHDRAW"],
        "verdict": "VULNERABLE",
        "confidence": 0.97,
        "description": "Recursive drain loop — attacker calls withdraw repeatedly.",
        "attack_type": "Cross-Function Reentrancy (SWC-107 Advanced)",
        "cfg_path": ["q0 --LOOP(invalid)--> q_reject"],
        "explanation": (
            "LOOP is not a valid grammar token at all — it represents an "
            "unrecognized/malicious opcode injection. The grammar rejects it "
            "immediately. Even if parsed, CALL before WITHDRAW is a reentrancy "
            "violation. This models the attacker's fallback function that "
            "recursively calls withdraw() before the balance is updated."
        ),
        "solidity_analog": (
            "// ATTACKER CONTRACT (Malicious)\n"
            "contract Attacker {\n"
            "    IVictim victim;\n"
            "    function attack() external payable {\n"
            "        victim.withdraw(1 ether);  // Initial call\n"
            "    }\n"
            "    // Fallback re-enters withdraw() recursively!\n"
            "    receive() external payable {\n"
            "        if (address(victim).balance >= 1 ether)\n"
            "            victim.withdraw(1 ether);  // LOOP!\n"
            "    }\n"
            "}"
        ),
        "real_world_incident": "Cream Finance, August 2021 — $130M drained",
        "qubit_count": 3,
        "circuit_depth": 2,
        "color": "red",
    },
    {
        "id": "A5",
        "command": "USER CALL UPDATE",
        "tokens": ["USER", "CALL", "UPDATE"],
        "verdict": "VULNERABLE",
        "confidence": 0.85,
        "description": "CALL before UPDATE — state not locked before external interaction.",
        "attack_type": "Reentrancy via Missing CEI Pattern (SWC-107)",
        "cfg_path": ["q0 --AUTH--> q1", "q1 --CALL(before UPDATE)--> q_reject"],
        "explanation": (
            "USER provides AUTH (q0→q1), but then CALL fires before UPDATE. "
            "This violates CFG rule R1: CALL requires prior UPDATE. "
            "The grammar rejects at q1→q_reject. An attacker can re-enter "
            "between the CALL and the UPDATE, reading a stale state."
        ),
        "solidity_analog": (
            "// VULNERABLE: Interaction before Effect\n"
            "function claimReward() public {\n"
            "    require(hasReward[msg.sender], 'No reward');\n"
            "    // Missing: hasReward[msg.sender] = false; // Effect FIRST!\n"
            "    (bool ok,) = msg.sender.call{value: reward}(''); // CALL early!\n"
            "    hasReward[msg.sender] = false;  // Too late — attacker re-entered\n"
            "}"
        ),
        "real_world_incident": "Agave + Hundred Finance, March 2022 — $11M",
        "qubit_count": 3,
        "circuit_depth": 3,
        "color": "red",
    },
]