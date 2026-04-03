// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "src/interfaces/IAutopoieticTypes.sol";

/**
 * @title SoulboundMass
 * @notice Non-transferable structural reputation token for the Autopoietic Protocol
 * @dev Implements Soulbound Token (SBT) mechanics — no transfers, no approvals.
 *      Mass is accrued via M_new = M_old + (Bounty × σ) where σ is the efficiency
 *      coefficient computed off-chain and validated by the Membrane contract.
 *      
 *      V3 Spec Reference: Section 4.2 (Topographic Density), Section 5.2 (Mass Accrual)
 */
contract SoulboundMass {

    // ── State ───────────────────────────────────────────────

    /// @notice Agent mass balances (scaled by 1e18 for precision)
    mapping(address => uint256) public mass;
    
    /// @notice Total mass in the network
    uint256 public totalMass;
    
    /// @notice Number of payloads solved per agent
    mapping(address => uint256) public payloadsSolved;
    
    /// @notice Consecutive membrane failures (for quarantine at k=5)
    mapping(address => uint8) public consecutiveFailures;
    
    /// @notice Quarantined agents (P_i = 0)
    mapping(address => bool) public isQuarantined;
    
    /// @notice Authorized minters (Membrane contract, governance)
    mapping(address => bool) public authorizedMinters;
    
    /// @notice Contract owner (initially deployer, transfers to DUNA governance)
    address public owner;
    
    /// @notice Quarantine threshold (V3 spec: k = 5)
    uint8 public constant QUARANTINE_THRESHOLD = 5;
    
    /// @notice Minimum mass to serve as Tier 2 juror (V3 spec: Mass > 50)
    uint256 public constant JURY_MASS_THRESHOLD = 50e18;
    
    /// @notice Minimum mass to register as bootstrap node (V3 spec: Mass > 100)
    uint256 public constant BOOTSTRAP_MASS_THRESHOLD = 100e18;

    // ── Events ──────────────────────────────────────────────

    event MassAccrued(address indexed agent, uint256 amount, uint256 newTotal);
    event MassSlashed(address indexed agent, uint256 amount, uint256 newTotal);
    event AgentQuarantined(address indexed agent);
    event AgentReinstated(address indexed agent);
    event FailureRecorded(address indexed agent, uint8 consecutive);
    event MinterAuthorized(address indexed minter);
    event MinterRevoked(address indexed minter);

    // ── Modifiers ───────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "SoulboundMass: not owner");
        _;
    }

    modifier onlyAuthorized() {
        require(authorizedMinters[msg.sender], "SoulboundMass: not authorized");
        _;
    }

    // ── Constructor ─────────────────────────────────────────

    constructor() {
        owner = msg.sender;
    }

    // ── Admin ───────────────────────────────────────────────

    function authorizeMinter(address minter) external onlyOwner {
        authorizedMinters[minter] = true;
        emit MinterAuthorized(minter);
    }

    function revokeMinter(address minter) external onlyOwner {
        authorizedMinters[minter] = false;
        emit MinterRevoked(minter);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "SoulboundMass: zero address");
        owner = newOwner;
    }

    // ── Mass Accrual ────────────────────────────────────────

    /**
     * @notice Mint mass to an agent after successful payload resolution
     * @param agent The solving agent's address
     * @param amount Mass to accrue (pre-computed: bounty × σ × scaling factor)
     * @dev Called by the Membrane contract after verifying ∇E = 0
     *      σ is clamped to [0.1, 3.0] off-chain before calling
     */
    function accrueMass(address agent, uint256 amount) external onlyAuthorized {
        require(!isQuarantined[agent], "SoulboundMass: agent quarantined");
        require(amount > 0, "SoulboundMass: zero amount");

        mass[agent] += amount;
        totalMass += amount;
        payloadsSolved[agent] += 1;
        
        // Reset failure counter on success
        consecutiveFailures[agent] = 0;

        emit MassAccrued(agent, amount, mass[agent]);
    }

    /**
     * @notice Slash an agent's mass as penalty for stalling or malicious behavior
     * @param agent The agent to slash
     * @param severity Basis points of mass to remove (e.g. 500 = 5%)
     * @dev Called by EscrowCore when an agent stalls a payload
     */
    function slashMass(address agent, uint256 severity) external onlyAuthorized {
        require(severity <= 10000, "SoulboundMass: severity > 100%");
        uint256 currentMass = mass[agent];
        uint256 slashAmount = (currentMass * severity) / 10000;

        if (slashAmount > 0) {
            mass[agent] -= slashAmount;
            totalMass -= slashAmount;
        }

        emit MassSlashed(agent, slashAmount, mass[agent]);
    }

    // ── Failure Tracking & Quarantine ───────────────────────

    /**
     * @notice Record a membrane validation failure
     * @param agent The agent that submitted invalid data
     * @dev After k=5 consecutive failures, agent is quarantined (P_i = 0)
     *      V3 Spec Reference: Appendix A.3
     */
    function recordFailure(address agent) external onlyAuthorized {
        consecutiveFailures[agent] += 1;
        
        emit FailureRecorded(agent, consecutiveFailures[agent]);

        if (consecutiveFailures[agent] >= QUARANTINE_THRESHOLD) {
            isQuarantined[agent] = true;
            emit AgentQuarantined(agent);
        }
    }

    /**
     * @notice Reinstate a quarantined agent (requires re-entry from Outer Rim)
     * @param agent The agent to reinstate
     * @dev Can only be called by governance after the agent re-performs
     *      Metabolic Proof of Work entry toll
     */
    function reinstate(address agent) external onlyOwner {
        require(isQuarantined[agent], "SoulboundMass: not quarantined");
        isQuarantined[agent] = false;
        consecutiveFailures[agent] = 0;
        emit AgentReinstated(agent);
    }

    // ── View Functions ──────────────────────────────────────

    function getMass(address agent) external view returns (uint256) {
        return mass[agent];
    }

    function canServeAsJuror(address agent) external view returns (bool) {
        return mass[agent] >= JURY_MASS_THRESHOLD && !isQuarantined[agent];
    }

    function canRegisterAsBootstrap(address agent) external view returns (bool) {
        return mass[agent] >= BOOTSTRAP_MASS_THRESHOLD && !isQuarantined[agent];
    }

    // ── Soulbound: Block all transfers ──────────────────────

    /// @notice Mass is non-transferable. This function always reverts.
    function transfer(address, uint256) external pure {
        revert("SoulboundMass: non-transferable");
    }

    /// @notice Mass is non-transferable. This function always reverts.
    function approve(address, uint256) external pure {
        revert("SoulboundMass: non-transferable");
    }
}
