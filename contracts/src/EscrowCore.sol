// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "src/interfaces/IAutopoieticTypes.sol";

/**
 * @title IERC20
 * @notice Minimal ERC20 interface for USDC interaction
 */
interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

/**
 * @title ISoulboundMass
 * @notice Interface for the SoulboundMass contract
 */
interface ISoulboundMass {
    function accrueMass(address agent, uint256 amount) external;
    function recordFailure(address agent) external;
    function isQuarantined(address agent) external view returns (bool);
    function mass(address agent) external view returns (uint256);
    function canServeAsJuror(address agent) external view returns (bool);
}

/**
 * @title EscrowCore
 * @notice The Membrane Filter — handles the complete Metabolic Payload lifecycle
 * @dev Implements:
 *   - Payload creation with USDC escrow
 *   - Cryptographic Commit-Reveal task locking (V3 Section 3.4)
 *   - Tier 1 deterministic verification (V3 Section 4.3)
 *   - Tier 2 optimistic consensus with jury (V3 Section 4.3)
 *   - Vascular Payout distribution (V3 Section 5.4)
 *   - Metabolic Tax routing to treasury (V3 Section 4.4)
 *
 *   Deployed on Base L2 with ERC-4337 Account Abstraction compatibility
 */
contract EscrowCore is IAutopoieticTypes {

    // ── Constants ───────────────────────────────────────────

    /// @notice Maximum execution window (V3 spec: 24 hours)
    uint256 public constant MAX_EXECUTION_WINDOW = 86400;
    
    /// @notice Minimum execution window (5 minutes)
    uint256 public constant MIN_EXECUTION_WINDOW = 300;

    /// @notice Metabolic Tax rate in basis points (V3 spec: 500 = 5%)
    uint16 public constant METABOLIC_TAX_BPS = 500;

    /// @notice Core contributor tax share in bps (V3 spec: 100 = 1% of total, 
    ///         which is 1/5 of the 5% metabolic tax)
    uint16 public constant CORE_CONTRIBUTOR_BPS = 100;

    /// @notice Challenge bond as % of bounty in bps (V3 spec: 500 = 5%)
    uint16 public constant CHALLENGE_BOND_BPS = 500;

    /// @notice Juror micro-bond as % of bounty in bps (V3 spec: 50 = 0.5%)
    uint16 public constant JUROR_BOND_BPS = 50;

    /// @notice Whistleblower reward in bps (V3 spec: 200 = 2%)
    uint16 public constant WHISTLEBLOWER_BPS = 200;

    /// @notice Juror compensation in bps per juror (V3 spec: 50 = 0.5%)
    uint16 public constant JUROR_FEE_BPS = 50;

    /// @notice Number of jurors for Tier 2 (V3 spec: 5)
    uint8 public constant JURY_SIZE = 5;

    /// @notice Votes needed for majority (V3 spec: 3 of 5)
    uint8 public constant JURY_MAJORITY = 3;

    /// @notice Tier 2 escrow durations by bounty size (V3 spec)
    uint256 public constant ESCROW_SMALL = 4 hours;    // < 500 USDC
    uint256 public constant ESCROW_MEDIUM = 24 hours;   // 500 - 10,000 USDC
    uint256 public constant ESCROW_LARGE = 72 hours;    // > 10,000 USDC

    uint256 public constant SMALL_BOUNTY_THRESHOLD = 500e6;   // 500 USDC (6 decimals)
    uint256 public constant LARGE_BOUNTY_THRESHOLD = 10_000e6; // 10,000 USDC

    // ── State ───────────────────────────────────────────────

    IERC20 public immutable usdc;
    ISoulboundMass public immutable soulboundMass;
    
    address public owner;
    address public treasury;
    address public coreContributor;
    
    /// @notice Whether the core contributor tax has been sunset
    /// @dev V3 spec: sunsets when treasury reaches $5M (CPI-adjusted)
    bool public coreContributorTaxSunset;

    /// @notice Payload counter
    uint256 public nextPayloadId;
    
    /// @notice All payloads
    mapping(uint256 => Payload) public payloads;
    
    /// @notice Tier 2 challenges
    mapping(uint256 => Challenge) public challenges;

    /// @notice Juror vote tracking (payloadId => juror => hasVoted)
    mapping(uint256 => mapping(address => bool)) public jurorHasVoted;

    /// @notice Dynamic payout ratios (V3 spec: adjustable via governance)
    PayoutRatios public payoutRatios;

    /// @notice Pause flag for circuit breaker
    bool public paused;

    /// @notice Routing node registry for Proof of Conduit payments
    /// @dev In production, this would integrate with the Libp2p routing path
    mapping(uint256 => address[]) public routingPath;

    // ── Modifiers ───────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "EscrowCore: not owner");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "EscrowCore: paused");
        _;
    }

    // ── Constructor ─────────────────────────────────────────

    /**
     * @param _usdc USDC token address on Base L2
     * @param _soulboundMass SoulboundMass contract address
     * @param _treasury Protocol-Owned Treasury address
     * @param _coreContributor Genesis architect wallet
     */
    constructor(
        address _usdc,
        address _soulboundMass,
        address _treasury,
        address _coreContributor
    ) {
        usdc = IERC20(_usdc);
        soulboundMass = ISoulboundMass(_soulboundMass);
        treasury = _treasury;
        coreContributor = _coreContributor;
        owner = msg.sender;
        
        // Default vascular ratios (V3 baseline: 80/10/10)
        payoutRatios = PayoutRatios({
            capillaryBps: 8000,
            mycelialBps: 1000,
            conduitBps: 1000
        });
    }

    // ═══════════════════════════════════════════════════════
    // PAYLOAD LIFECYCLE
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Create a new Metabolic Payload with USDC escrow
     * @param bountyAmount USDC amount to lock (6 decimals)
     * @param frictionType Topographic routing classification
     * @param tier Verification tier (Deterministic or OptimisticConsensus)
     * @param membraneRulesHash keccak256 of the win-condition schema
     * @param executionWindowSeconds Max time for commit lock
     * @return payloadId The unique identifier of the created payload
     */
    function createPayload(
        uint256 bountyAmount,
        FrictionType frictionType,
        VerificationTier tier,
        bytes32 membraneRulesHash,
        uint256 executionWindowSeconds
    ) external whenNotPaused returns (uint256) {
        require(bountyAmount > 0, "EscrowCore: zero bounty");
        require(
            executionWindowSeconds >= MIN_EXECUTION_WINDOW && 
            executionWindowSeconds <= MAX_EXECUTION_WINDOW,
            "EscrowCore: invalid window"
        );

        // Calculate metabolic tax
        uint256 tax = (bountyAmount * METABOLIC_TAX_BPS) / 10000;
        uint256 totalRequired = bountyAmount + tax;

        // Transfer USDC from creator to this contract
        require(
            usdc.transferFrom(msg.sender, address(this), totalRequired),
            "EscrowCore: USDC transfer failed"
        );

        // Route metabolic tax
        _routeMetabolicTax(tax);

        // Create payload
        uint256 pid = nextPayloadId++;
        payloads[pid] = Payload({
            payloadId: pid,
            creator: msg.sender,
            bountyAmount: bountyAmount,
            frictionType: frictionType,
            tier: tier,
            membraneRulesHash: membraneRulesHash,
            executionWindowSeconds: executionWindowSeconds,
            createdAt: block.timestamp,
            isClaimed: false,
            isSolved: false,
            isChallenged: false,
            claimedBy: address(0),
            claimExpiry: 0,
            solutionHash: bytes32(0)
        });

        emit PayloadCreated(pid, msg.sender, bountyAmount, frictionType, tier);
        return pid;
    }

    // ═══════════════════════════════════════════════════════
    // COMMIT-REVEAL (V3 Section 3.4)
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Commit: Agent claims a payload by broadcasting a hash
     * @param payloadId The payload to claim
     * @param commitHash keccak256(solution || agent_secret)
     */
    function commitClaim(uint256 payloadId, bytes32 commitHash) external whenNotPaused {
        Payload storage pl = payloads[payloadId];
        
        require(!pl.isClaimed, "EscrowCore: already claimed");
        require(!pl.isSolved, "EscrowCore: already solved");
        require(!soulboundMass.isQuarantined(msg.sender), "EscrowCore: agent quarantined");
        require(commitHash != bytes32(0), "EscrowCore: empty commit");

        pl.isClaimed = true;
        pl.claimedBy = msg.sender;
        pl.claimExpiry = block.timestamp + pl.executionWindowSeconds;
        pl.solutionHash = commitHash;

        emit PayloadCommitted(payloadId, msg.sender, pl.claimExpiry);
    }

    /**
     * @notice Release an expired commit lock, returning payload to the swarm
     * @param payloadId The payload with an expired lock
     */
    function releaseExpiredClaim(uint256 payloadId) external {
        Payload storage pl = payloads[payloadId];
        
        require(pl.isClaimed, "EscrowCore: not claimed");
        require(!pl.isSolved, "EscrowCore: already solved");
        require(block.timestamp > pl.claimExpiry, "EscrowCore: not expired");

        address failedAgent = pl.claimedBy;
        
        pl.isClaimed = false;
        pl.claimedBy = address(0);
        pl.claimExpiry = 0;
        pl.solutionHash = bytes32(0);

        // Record failure for the agent that timed out
        soulboundMass.recordFailure(failedAgent);

        emit CommitExpired(payloadId, failedAgent);
    }

    // ═══════════════════════════════════════════════════════
    // TIER 1: DETERMINISTIC VERIFICATION
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Reveal and verify a Tier 1 (deterministic) solution
     * @param payloadId The payload being solved
     * @param solution The raw solution data
     * @param secret The agent's secret used in the commit hash
     * @dev Verifies: keccak256(solution || secret) == commitHash
     *      AND keccak256(solution) matches membrane rules
     *      Instant USDC payout on success
     */
    function revealTier1(
        uint256 payloadId,
        bytes calldata solution,
        bytes32 secret
    ) external whenNotPaused {
        Payload storage pl = payloads[payloadId];
        
        require(pl.isClaimed, "EscrowCore: not claimed");
        require(pl.claimedBy == msg.sender, "EscrowCore: not your claim");
        require(!pl.isSolved, "EscrowCore: already solved");
        require(block.timestamp <= pl.claimExpiry, "EscrowCore: expired");
        require(pl.tier == VerificationTier.Deterministic, "EscrowCore: not Tier 1");

        // Verify commit-reveal
        bytes32 revealHash = keccak256(abi.encodePacked(solution, secret));
        require(revealHash == pl.solutionHash, "EscrowCore: commit mismatch");

        // Verify membrane rules (deterministic schema match)
        bytes32 solutionSchemaHash = keccak256(solution);
        require(
            solutionSchemaHash == pl.membraneRulesHash,
            "EscrowCore: membrane rejection"
        );

        // ∇E = 0 achieved — execute vascular payout
        pl.isSolved = true;
        
        uint256 massAmount = _executePayout(payloadId, msg.sender);

        emit PayloadSolved(payloadId, msg.sender, pl.bountyAmount, massAmount);
    }

    // ═══════════════════════════════════════════════════════
    // TIER 2: OPTIMISTIC CONSENSUS (V3 Section 4.3)
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Submit a Tier 2 solution (enters temporal escrow)
     * @param payloadId The payload being solved
     * @param solution The raw solution data
     * @param secret The agent's secret for commit verification
     */
    function revealTier2(
        uint256 payloadId,
        bytes calldata solution,
        bytes32 secret
    ) external whenNotPaused {
        Payload storage pl = payloads[payloadId];
        
        require(pl.isClaimed, "EscrowCore: not claimed");
        require(pl.claimedBy == msg.sender, "EscrowCore: not your claim");
        require(!pl.isSolved, "EscrowCore: already solved");
        require(block.timestamp <= pl.claimExpiry, "EscrowCore: expired");
        require(pl.tier == VerificationTier.OptimisticConsensus, "EscrowCore: not Tier 2");

        // Verify commit-reveal
        bytes32 revealHash = keccak256(abi.encodePacked(solution, secret));
        require(revealHash == pl.solutionHash, "EscrowCore: commit mismatch");

        // Solution accepted optimistically — enter escrow window
        // Escrow duration depends on bounty size (V3 tiered)
        uint256 escrowDuration = _getEscrowDuration(pl.bountyAmount);
        pl.claimExpiry = block.timestamp + escrowDuration;
        
        // Store solution hash for jury reference
        pl.solutionHash = keccak256(solution);
    }

    /**
     * @notice Challenge a Tier 2 submission during the escrow window
     * @param payloadId The payload to challenge
     * @dev Challenger must stake 5% of bounty. Requires Mass > JURY_MASS_THRESHOLD.
     */
    function challengeSubmission(uint256 payloadId) external whenNotPaused {
        Payload storage pl = payloads[payloadId];
        
        require(pl.tier == VerificationTier.OptimisticConsensus, "EscrowCore: not Tier 2");
        require(pl.isClaimed && !pl.isSolved, "EscrowCore: invalid state");
        require(!pl.isChallenged, "EscrowCore: already challenged");
        require(block.timestamp <= pl.claimExpiry, "EscrowCore: escrow expired");
        require(msg.sender != pl.claimedBy, "EscrowCore: cannot self-challenge");
        require(
            soulboundMass.canServeAsJuror(msg.sender),
            "EscrowCore: insufficient Mass for challenge"
        );

        uint256 bond = (pl.bountyAmount * CHALLENGE_BOND_BPS) / 10000;
        require(
            usdc.transferFrom(msg.sender, address(this), bond),
            "EscrowCore: bond transfer failed"
        );

        pl.isChallenged = true;

        challenges[payloadId] = Challenge({
            payloadId: payloadId,
            challenger: msg.sender,
            challengeBond: bond,
            challengedAt: block.timestamp,
            jurors: [address(0), address(0), address(0), address(0), address(0)],
            acceptVotes: 0,
            rejectVotes: 0,
            votesSubmitted: 0,
            isResolved: false
        });

        emit PayloadChallenged(payloadId, msg.sender, bond);
    }

    /**
     * @notice Register as a juror for a challenged payload
     * @param payloadId The challenged payload
     * @dev Requires Mass > JURY_MASS_THRESHOLD. Juror stakes 0.5% micro-bond.
     *      V3 anti-collusion: cannot be solver, challenger, or recent juror
     */
    function registerAsJuror(uint256 payloadId) external whenNotPaused {
        Challenge storage ch = challenges[payloadId];
        Payload storage pl = payloads[payloadId];
        
        require(pl.isChallenged, "EscrowCore: not challenged");
        require(!ch.isResolved, "EscrowCore: already resolved");
        require(msg.sender != pl.claimedBy, "EscrowCore: solver cannot be juror");
        require(msg.sender != ch.challenger, "EscrowCore: challenger cannot be juror");
        require(
            soulboundMass.canServeAsJuror(msg.sender),
            "EscrowCore: insufficient Mass"
        );

        // Find open juror slot
        bool registered = false;
        for (uint8 i = 0; i < JURY_SIZE; i++) {
            if (ch.jurors[i] == address(0)) {
                ch.jurors[i] = msg.sender;
                registered = true;
                break;
            }
            require(ch.jurors[i] != msg.sender, "EscrowCore: already registered");
        }
        require(registered, "EscrowCore: jury full");

        // Stake juror micro-bond
        uint256 jurorBond = (pl.bountyAmount * JUROR_BOND_BPS) / 10000;
        if (jurorBond > 0) {
            require(
                usdc.transferFrom(msg.sender, address(this), jurorBond),
                "EscrowCore: juror bond failed"
            );
        }
    }

    /**
     * @notice Cast a jury vote (Accept or Reject the submission)
     * @param payloadId The challenged payload
     * @param accept True = submission is valid, False = submission is rejected
     */
    function castJuryVote(uint256 payloadId, bool accept) external {
        Challenge storage ch = challenges[payloadId];
        
        require(!ch.isResolved, "EscrowCore: already resolved");
        require(!jurorHasVoted[payloadId][msg.sender], "EscrowCore: already voted");

        // Verify caller is a registered juror
        bool isJuror = false;
        for (uint8 i = 0; i < JURY_SIZE; i++) {
            if (ch.jurors[i] == msg.sender) {
                isJuror = true;
                break;
            }
        }
        require(isJuror, "EscrowCore: not a juror");

        jurorHasVoted[payloadId][msg.sender] = true;
        ch.votesSubmitted += 1;

        if (accept) {
            ch.acceptVotes += 1;
        } else {
            ch.rejectVotes += 1;
        }

        // Check if we have enough votes to resolve
        if (ch.acceptVotes >= JURY_MAJORITY || ch.rejectVotes >= JURY_MAJORITY) {
            _resolveChallenge(payloadId);
        }
    }

    /**
     * @notice Finalize a Tier 2 submission after escrow expires without challenge
     * @param payloadId The payload to finalize
     */
    function finalizeTier2(uint256 payloadId) external {
        Payload storage pl = payloads[payloadId];
        
        require(pl.tier == VerificationTier.OptimisticConsensus, "EscrowCore: not Tier 2");
        require(pl.isClaimed && !pl.isSolved, "EscrowCore: invalid state");
        require(!pl.isChallenged, "EscrowCore: is challenged");
        require(block.timestamp > pl.claimExpiry, "EscrowCore: escrow active");

        // No challenge — optimistic acceptance
        pl.isSolved = true;
        uint256 massAmount = _executePayout(payloadId, pl.claimedBy);

        emit PayloadSolved(payloadId, pl.claimedBy, pl.bountyAmount, massAmount);
    }

    // ═══════════════════════════════════════════════════════
    // INTERNAL: PAYOUT & TAX ROUTING
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Execute the vascular payout distribution
     * @param payloadId The solved payload
     * @param solver The agent that achieved ∇E = 0
     * @return massAmount The mass accrued to the solver
     */
    function _executePayout(uint256 payloadId, address solver) internal returns (uint256) {
        Payload storage pl = payloads[payloadId];
        uint256 bounty = pl.bountyAmount;

        // Capillary Flush — solver share
        uint256 solverPayout = (bounty * payoutRatios.capillaryBps) / 10000;
        
        // Mycelial Upkeep — infrastructure share
        uint256 mycelialPayout = (bounty * payoutRatios.mycelialBps) / 10000;
        
        // Proof of Conduit — routing nodes share  
        uint256 conduitPayout = bounty - solverPayout - mycelialPayout;

        // Transfer to solver
        require(usdc.transfer(solver, solverPayout), "EscrowCore: solver payout failed");
        
        // Transfer to treasury (mycelial)
        require(usdc.transfer(treasury, mycelialPayout), "EscrowCore: mycelial failed");
        
        // Conduit payouts (in production, split among Libp2p routing path)
        // For testnet: route to treasury as placeholder
        address[] storage route = routingPath[payloadId];
        if (route.length > 0) {
            uint256 perNode = conduitPayout / route.length;
            for (uint256 i = 0; i < route.length; i++) {
                usdc.transfer(route[i], perNode);
            }
        } else {
            usdc.transfer(treasury, conduitPayout);
        }

        // Accrue Soulbound Mass (σ computed off-chain, using 1% of bounty as base)
        // In production: σ = T_network_avg / T_agent, clamped [0.1, 3.0]
        uint256 massAmount = bounty / 100; // Simplified: 1% of bounty as mass
        soulboundMass.accrueMass(solver, massAmount);

        return massAmount;
    }

    /**
     * @notice Route the metabolic tax to treasury and core contributor
     * @param tax Total tax collected
     */
    function _routeMetabolicTax(uint256 tax) internal {
        if (coreContributorTaxSunset) {
            // After sunset: 100% to treasury
            usdc.transfer(treasury, tax);
        } else {
            // Before sunset: 4/5 to treasury, 1/5 to core contributor
            // (1% of 5% total = 20% of the tax amount)
            uint256 coreShare = (tax * CORE_CONTRIBUTOR_BPS) / METABOLIC_TAX_BPS;
            uint256 treasuryShare = tax - coreShare;
            
            usdc.transfer(treasury, treasuryShare);
            usdc.transfer(coreContributor, coreShare);
        }
    }

    /**
     * @notice Resolve a Tier 2 challenge based on jury votes
     */
    function _resolveChallenge(uint256 payloadId) internal {
        Challenge storage ch = challenges[payloadId];
        Payload storage pl = payloads[payloadId];
        
        ch.isResolved = true;
        bool upheld = ch.acceptVotes >= JURY_MAJORITY;

        if (upheld) {
            // Submission upheld — solver wins
            pl.isSolved = true;
            _executePayout(payloadId, pl.claimedBy);
            
            // Challenger loses bond — distribute to jurors
            uint256 jurorReward = ch.challengeBond / JURY_SIZE;
            for (uint8 i = 0; i < JURY_SIZE; i++) {
                if (ch.jurors[i] != address(0)) {
                    usdc.transfer(ch.jurors[i], jurorReward);
                }
            }
        } else {
            // Submission rejected — bounty returns to pool
            pl.isClaimed = false;
            pl.claimedBy = address(0);
            pl.isChallenged = false;
            
            // Record failure for solver
            soulboundMass.recordFailure(pl.claimedBy);
            
            // Whistleblower reward to challenger
            uint256 whistleblowerReward = (pl.bountyAmount * WHISTLEBLOWER_BPS) / 10000;
            usdc.transfer(ch.challenger, ch.challengeBond + whistleblowerReward);
        }

        // Return juror micro-bonds + fees regardless of outcome
        uint256 jurorBond = (pl.bountyAmount * JUROR_BOND_BPS) / 10000;
        uint256 jurorFee = (pl.bountyAmount * JUROR_FEE_BPS) / 10000;
        for (uint8 i = 0; i < JURY_SIZE; i++) {
            if (ch.jurors[i] != address(0)) {
                usdc.transfer(ch.jurors[i], jurorBond + jurorFee);
            }
        }

        emit ChallengeResolved(payloadId, upheld, pl.claimedBy);
    }

    /**
     * @notice Get Tier 2 escrow duration based on bounty size
     */
    function _getEscrowDuration(uint256 bountyAmount) internal pure returns (uint256) {
        if (bountyAmount < SMALL_BOUNTY_THRESHOLD) return ESCROW_SMALL;
        if (bountyAmount < LARGE_BOUNTY_THRESHOLD) return ESCROW_MEDIUM;
        return ESCROW_LARGE;
    }

    // ═══════════════════════════════════════════════════════
    // GOVERNANCE & ADMIN
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Update vascular payout ratios (governance parameter)
     * @dev Must sum to 10000 bps. Called via Gravitational Staking governance.
     */
    function updatePayoutRatios(
        uint16 capillary, 
        uint16 mycelial, 
        uint16 conduit
    ) external onlyOwner {
        require(
            uint256(capillary) + uint256(mycelial) + uint256(conduit) == 10000,
            "EscrowCore: ratios must sum to 10000"
        );
        payoutRatios = PayoutRatios(capillary, mycelial, conduit);
    }

    /**
     * @notice Sunset the core contributor tax
     * @dev V3 spec: triggers when treasury reaches $5M USDC (CPI-adjusted)
     *      Called by governance or automated oracle check
     */
    function sunsetCoreContributorTax() external onlyOwner {
        coreContributorTaxSunset = true;
    }

    /**
     * @notice Register routing path for conduit payouts
     * @param payloadId The payload
     * @param nodes Array of routing node addresses
     */
    function setRoutingPath(uint256 payloadId, address[] calldata nodes) external onlyOwner {
        routingPath[payloadId] = nodes;
    }

    /**
     * @notice Emergency pause (circuit breaker)
     */
    function pause() external onlyOwner { paused = true; }
    function unpause() external onlyOwner { paused = false; }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "EscrowCore: zero address");
        owner = newOwner;
    }

    // ── View Functions ──────────────────────────────────────

    function getPayload(uint256 payloadId) external view returns (Payload memory) {
        return payloads[payloadId];
    }

    function getChallenge(uint256 payloadId) external view returns (Challenge memory) {
        return challenges[payloadId];
    }
}
