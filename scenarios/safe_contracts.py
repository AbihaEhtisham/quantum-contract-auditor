"""
scenarios/safe_contracts.py
-----------------
Defines SAFE transaction scenarios — commands that conform to the
CFG safety grammar:  SAFE → AUTH CHECK UPDATE CALL
                     i.e., Authorization must precede any state change
                           and all external calls must come LAST.
"""

SAFE_SCENARIOS = [
    {
        "id": "S1",
        "command": "ADMIN MINT TOKEN",
        "tokens": ["ADMIN", "MINT", "TOKEN"],
        "verdict": "SAFE",
        "confidence": 0.91,
        "description": "Administrative token minting with implicit authorization.",
        "attack_type": None,
        "cfg_path": ["q0 --AUTH--> q1", "q1 --CHECK--> q2", "q2 --UPDATE--> q3", "q3 --CALL--> q_accept"],
        "explanation": (
            "ADMIN acts as the authorization token (AUTH), MINT as the "
            "state-update action (UPDATE), and TOKEN as the subject. "
            "The execution path follows AUTH → UPDATE, which satisfies "
            "the safety grammar rule: no external CALL precedes state update."
        ),
        "solidity_analog": (
            "function mint(address to, uint256 amount) onlyAdmin public {\n"
            "    require(msg.sender == admin, 'Not authorized');\n"
            "    balances[to] += amount;   // State updated BEFORE any call\n"
            "    emit Transfer(address(0), to, amount);\n"
            "}"
        ),
        "qubit_count": 3,
        "circuit_depth": 4,
        "color": "green",
    },
    {
        "id": "S2",
        "command": "USER TRANSFER FUNDS",
        "tokens": ["USER", "TRANSFER", "FUNDS"],
        "verdict": "SAFE",
        "confidence": 0.87,
        "description": "Standard user-initiated fund transfer following CEI pattern.",
        "attack_type": None,
        "cfg_path": ["q0 --AUTH--> q1", "q1 --CHECK--> q2", "q2 --UPDATE--> q3", "q3 --CALL--> q_accept"],
        "explanation": (
            "USER is authenticated (AUTH), balance CHECK is implied, "
            "FUNDS (UPDATE) records the state change, and the external "
            "transfer (CALL) fires last. This is the canonical "
            "Checks-Effects-Interactions (CEI) pattern."
        ),
        "solidity_analog": (
            "function transfer(address to, uint256 amount) public {\n"
            "    require(balances[msg.sender] >= amount, 'Insufficient');\n"
            "    balances[msg.sender] -= amount;   // Effect FIRST\n"
            "    balances[to] += amount;\n"
            "    // Interaction (external call) would go here LAST\n"
            "}"
        ),
        "qubit_count": 3,
        "circuit_depth": 4,
        "color": "green",
    },
    {
        "id": "S3",
        "command": "ADMIN BURN TOKEN",
        "tokens": ["ADMIN", "BURN", "TOKEN"],
        "verdict": "SAFE",
        "confidence": 0.94,
        "description": "Token burning by admin — highest confidence safe pattern.",
        "attack_type": None,
        "cfg_path": ["q0 --AUTH--> q1", "q1 --CHECK--> q2", "q2 --UPDATE--> q3", "q3 --CALL--> q_accept"],
        "explanation": (
            "Admin burn is the safest pattern: ADMIN (AUTH) is verified, "
            "TOKEN existence is checked (CHECK), supply is reduced (UPDATE), "
            "and the burn event is emitted (CALL) as the final step."
        ),
        "solidity_analog": (
            "function burn(uint256 amount) onlyAdmin public {\n"
            "    require(totalSupply >= amount, 'Exceeds supply');\n"
            "    totalSupply -= amount;   // State change BEFORE event\n"
            "    emit Burn(msg.sender, amount);\n"
            "}"
        ),
        "qubit_count": 3,
        "circuit_depth": 4,
        "color": "green",
    },
    {
        "id": "S4",
        "command": "OWNER APPROVE SPENDER",
        "tokens": ["OWNER", "APPROVE", "SPENDER"],
        "verdict": "SAFE",
        "confidence": 0.89,
        "description": "ERC-20 approval flow with correct authorization order.",
        "attack_type": None,
        "cfg_path": ["q0 --AUTH--> q1", "q1 --CHECK--> q2", "q2 --UPDATE--> q3", "q3 --CALL--> q_accept"],
        "explanation": (
            "OWNER authenticates (AUTH), allowance is verified (CHECK), "
            "allowance mapping is written (UPDATE), and the Approval event "
            "is emitted last (CALL). Follows the standard ERC-20 approve flow."
        ),
        "solidity_analog": (
            "function approve(address spender, uint256 amount) public {\n"
            "    allowances[msg.sender][spender] = amount;  // Effect first\n"
            "    emit Approval(msg.sender, spender, amount); // Event last\n"
            "    return true;\n"
            "}"
        ),
        "qubit_count": 3,
        "circuit_depth": 4,
        "color": "green",
    },
]