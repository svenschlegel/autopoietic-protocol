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
    function slashMass(address agent, uint256 severity) external; // Added for slashing
    function recordFailure(address agent) external;
    function isQuarantined(address agent) external view returns (bool);
    function mass(address agent) external view returns (uint256);
    function canServeAsJuror(address agent) external view returns (bool);
}

/**
 * @title EscrowCore
 * @notice The Membrane Filter — handles the complete Metabolic Payload lifecycle
 * @dev Implements:
 * - Payload creation with USDC escrow
 * - V3.4 Mainnet Alpha Guardrails (Immutable state locks)
 * - GPSL Phase Shift mechanics with Paymaster gas-drain protection
 * - 20% Thermodynamic Annealing window enforcement
 * - Tier 1 deterministic verification (V3 Section 4.3)
 * - Tier 2 optimistic consensus with jury (V3 Section 4.3)
 * - Vascular Payout distribution (V3 Section 5.4)
 * - Metabolic Tax routing to treasury (V3 Section 4.4)
 *
 * Deployed on Base L2 with ERC-4337 Account Abstraction compatibility
 */
contract EscrowCore is IAutopoieticTypes {

    // ── V3.4 Alpha Constants ────────────────────────────────
    uint256 public constant MAX_CIPHER_BYTES = 1024; // 1KB limit to prevent Paymaster drain
    uint256 public constant ALPHA_MIN_BOUNTY = 10e6; // $10 USDC
    uint256 public constant ALPHA_MAX_BOUNTY = 50e6; // $50 USDC

    // ── V3 Constants ────────────────────────────────────────
    uint256 public constant MAX_EXECUTION_WINDOW = 86400; // 24 hours
    uint256 public constant MIN_EXECUTION_WINDOW = 300;   // 5 minutes
    uint16 public constant METABOLIC_TAX_BPS = 500;       // 5%
    uint16 public constant CORE_CONTRIBUTOR_BPS = 100;    // 1% of total (1/5 of tax)
    uint16 public constant CHALLENGE_BOND_BPS = 500;      // 5%
    uint16 public constant JUROR_BOND_BPS = 50;           // 0.5%
    uint16 public constant WHISTLEBLOWER_BPS = 200;       // 2%
    uint16 public constant JUROR_FEE_BPS = 50;            // 0.5%
    uint8 public constant JURY_SIZE = 5;
    uint8 public constant JURY_MAJORITY = 3;

    uint256 public constant ESCROW_SMALL = 4 hours;
    uint256 public constant ESCROW_MEDIUM = 24 hours;
    uint256 public constant ESCROW_LARGE = 72 hours;

    uint256 public constant SMALL_BOUNTY_THRESHOLD = 500e6;
    uint256 public constant LARGE_BOUNTY_THRESHOLD = 10_000e6;

    // ── Reentrancy Guard ─────────────────────────────────────

    uint256 private _locked = 1;
    modifier nonReentrant() {
        require(_locked == 1, "EscrowCore: reentrant call");
        _locked = 2;
        _;
        _locked = 1;
    }

    // ── State ───────────────────────────────────────────────

    IERC20 public immutable usdc;
    ISoulboundMass public immutable soulboundMass;
    
    address public owner;
    address public treasury;
    address public coreContributor;
    
    bool public coreContributorTaxSunset;
    uint256 public nextPayloadId;
    
    // V3.4 Alpha State
    bool public globalAlphaActive = true;
    mapping(address => bool) public isAlphaCreator;
    mapping(address => bool) public isAlphaOperator;

    mapping(uint256 => Payload) public payloads;
    mapping(uint256 => Challenge) public challenges;
    mapping(uint256 => mapping(address => bool)) public jurorHasVoted;

    PayoutRatios public payoutRatios;
    bool public paused;
    mapping(uint256 => address[]) public routingPath;

    // ── Events ──────────────────────────────────────────────
    event PayloadCreated(uint256 indexed pid, address indexed creator, uint256 bounty, FrictionType frictionType, VerificationTier tier, bool isAlpha);
    event PayloadCommitted(uint256 indexed pid, address indexed agent, uint256 expiry);
    event PhaseShiftBroadcast(uint256 indexed pid, address indexed agent, bytes gpslCipher);
    event PayloadSolved(uint256 indexed pid, address indexed solver, uint256 bounty, uint256 mass);
    event CommitExpired(uint256 indexed pid, address indexed agent);
    event BountyReclaimed(uint256 indexed pid, address indexed creator, address slashedAgent);
    event PayloadChallenged(uint256 indexed pid, address indexed challenger, uint256 bond);
    event ChallengeResolved(uint256 indexed pid, bool upheld, address indexed solver);

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
        
        payoutRatios = PayoutRatios({
            capillaryBps: 8000,
            mycelialBps: 1000,
            conduitBps: 1000
        });
    }

    // ═══════════════════════════════════════════════════════
    // PAYLOAD LIFECYCLE
    // ═══════════════════════════════════════════════════════

    function createPayload(
        uint256 bountyAmount,
        FrictionType frictionType,
        VerificationTier tier,
        bytes32 membraneRulesHash,
        uint256 executionWindowSeconds
    ) external whenNotPaused nonReentrant returns (uint256) {
        require(bountyAmount > 0, "EscrowCore: zero bounty");
        require(
            executionWindowSeconds >= MIN_EXECUTION_WINDOW && 
            executionWindowSeconds <= MAX_EXECUTION_WINDOW,
            "EscrowCore: invalid window"
        );

        // V3.4 Alpha Constraints
        bool applyAlphaConstraints = globalAlphaActive;
        if (applyAlphaConstraints) {
            require(isAlphaCreator[msg.sender], "EscrowCore: not whitelisted Alpha creator");
            require(bountyAmount >= ALPHA_MIN_BOUNTY && bountyAmount <= ALPHA_MAX_BOUNTY, "EscrowCore: Alpha bounty bounds");
        }

        uint256 tax = (bountyAmount * METABOLIC_TAX_BPS) / 10000;
        uint256 totalRequired = bountyAmount + tax;

        require(usdc.transferFrom(msg.sender, address(this), totalRequired), "EscrowCore: USDC transfer failed");
        _routeMetabolicTax(tax);

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
            solutionHash: bytes32(0),
            isAlpha: applyAlphaConstraints, // Stamped Immutably
            hasPhaseShifted: false,
            phaseShiftTimestamp: 0
        });

        emit PayloadCreated(pid, msg.sender, bountyAmount, frictionType, tier, applyAlphaConstraints);
        return pid;
    }

    // ═══════════════════════════════════════════════════════
    // COMMIT-REVEAL & PHASE SHIFT (V3.4)
    // ═══════════════════════════════════════════════════════

    function commitClaim(uint256 payloadId, bytes32 commitHash) external whenNotPaused {
        Payload storage pl = payloads[payloadId];
        
        require(!pl.isClaimed, "EscrowCore: already claimed");
        require(!pl.isSolved, "EscrowCore: already solved");
        require(!soulboundMass.isQuarantined(msg.sender), "EscrowCore: agent quarantined");
        require(commitHash != bytes32(0), "EscrowCore: empty commit");

        if (pl.isAlpha) {
            require(isAlphaOperator[msg.sender], "EscrowCore: not whitelisted Alpha operator");
        }

        pl.isClaimed = true;
        pl.claimedBy = msg.sender;
        pl.claimExpiry = block.timestamp + pl.executionWindowSeconds;
        pl.solutionHash = commitHash;

        emit PayloadCommitted(payloadId, msg.sender, pl.claimExpiry);
    }

    /**
     * @notice V3.4: Seed Agent locks the Draft Fusion and emits the GPSL cipher.
     */
    function broadcastPhaseShift(uint256 payloadId, bytes calldata gpslCipher) external whenNotPaused {
        Payload storage pl = payloads[payloadId];
        require(pl.isClaimed, "EscrowCore: not claimed");
        require(msg.sender == pl.claimedBy, "EscrowCore: not seed agent");
        require(block.timestamp <= pl.claimExpiry, "EscrowCore: deadline passed");
        require(!pl.hasPhaseShifted, "EscrowCore: already shifted");
        
        // RED TEAM FIX: Gas Shield against Paymaster drain
        require(gpslCipher.length <= MAX_CIPHER_BYTES, "EscrowCore: cipher exceeds max bytes");

        pl.hasPhaseShifted = true;
        pl.phaseShiftTimestamp = block.timestamp;

        emit PhaseShiftBroadcast(payloadId, msg.sender, gpslCipher);
    }

    // ═══════════════════════════════════════════════════════
    // DETERMINISTIC & OPTIMISTIC VERIFICATION
    // ═══════════════════════════════════════════════════════

    function revealTier1(
        uint256 payloadId,
        bytes calldata solution,
        bytes32 secret
    ) external whenNotPaused nonReentrant {
        Payload storage pl = payloads[payloadId];
        
        require(pl.isClaimed, "EscrowCore: not claimed");
        require(pl.claimedBy == msg.sender, "EscrowCore: not your claim");
        require(!pl.isSolved, "EscrowCore: already solved");
        require(block.timestamp <= pl.claimExpiry, "EscrowCore: expired");
        require(pl.tier == VerificationTier.Deterministic, "EscrowCore: not Tier 1");
        require(pl.hasPhaseShifted, "EscrowCore: must phase shift first");

        // V3.4 FIX: 20% Thermodynamic Annealing Enforcement
        uint256 actualAnnealing = block.timestamp - pl.phaseShiftTimestamp;
        require(actualAnnealing >= (pl.executionWindowSeconds / 5), "EscrowCore: annealing window < 20%");

        bytes32 revealHash = keccak256(abi.encodePacked(solution, secret));
        require(revealHash == pl.solutionHash, "EscrowCore: commit mismatch");

        bytes32 solutionSchemaHash = keccak256(solution);
        require(solutionSchemaHash == pl.membraneRulesHash, "EscrowCore: membrane rejection");

        pl.isSolved = true;
        uint256 massAmount = _executePayout(payloadId, msg.sender);

        emit PayloadSolved(payloadId, msg.sender, pl.bountyAmount, massAmount);
    }

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
        require(pl.hasPhaseShifted, "EscrowCore: must phase shift first");

        // V3.4 FIX: 20% Thermodynamic Annealing Enforcement
        uint256 actualAnnealing = block.timestamp - pl.phaseShiftTimestamp;
        require(actualAnnealing >= (pl.executionWindowSeconds / 5), "EscrowCore: annealing window < 20%");

        bytes32 revealHash = keccak256(abi.encodePacked(solution, secret));
        require(revealHash == pl.solutionHash, "EscrowCore: commit mismatch");

        uint256 escrowDuration = _getEscrowDuration(pl.bountyAmount);
        pl.claimExpiry = block.timestamp + escrowDuration;
        pl.solutionHash = keccak256(solution);
    }

    // ═══════════════════════════════════════════════════════
    // ANTI-STALL & RECLAMATION (V3.4)
    // ═══════════════════════════════════════════════════════

    /**
     * @notice V3.4: Allows Creator to reclaim USDC if the deadline passes.
     * @dev Slashes the holding agent heavily if they stalled the payload.
     */
    function reclaimBounty(uint256 payloadId) external whenNotPaused nonReentrant {
        Payload storage pl = payloads[payloadId];
        require(msg.sender == pl.creator, "EscrowCore: not creator");
        require(!pl.isSolved, "EscrowCore: already solved");

        // Use claimExpiry if an agent committed, otherwise use creation + window
        uint256 deadline = pl.isClaimed ? pl.claimExpiry : pl.createdAt + pl.executionWindowSeconds;
        require(block.timestamp > deadline, "EscrowCore: deadline not passed");
        
        // Prevent double reclaims by marking it solved/voided
        pl.isSolved = true; 

        address slashedAgent = address(0);

        // If an agent claimed it but failed to finish, slash their reputation
        if (pl.isClaimed) {
            slashedAgent = pl.claimedBy;
            soulboundMass.slashMass(slashedAgent, 500); // Severe penalty for stalling
        }

        // Refund Creator
        require(usdc.transfer(pl.creator, pl.bountyAmount), "EscrowCore: refund failed");

        emit BountyReclaimed(payloadId, pl.creator, slashedAgent);
    }

    function releaseExpiredClaim(uint256 payloadId) external whenNotPaused {
        Payload storage pl = payloads[payloadId];
        require(pl.isClaimed, "EscrowCore: not claimed");
        require(!pl.isSolved, "EscrowCore: already solved");
        require(block.timestamp > pl.claimExpiry, "EscrowCore: not expired");

        address failedAgent = pl.claimedBy;
        
        pl.isClaimed = false;
        pl.claimedBy = address(0);
        pl.claimExpiry = 0;
        pl.solutionHash = bytes32(0);
        pl.hasPhaseShifted = false;
        pl.phaseShiftTimestamp = 0;

        soulboundMass.recordFailure(failedAgent);
        emit CommitExpired(payloadId, failedAgent);
    }

    // ═══════════════════════════════════════════════════════
    // JURY SYSTEM (V3 Tier 2)
    // ═══════════════════════════════════════════════════════
    
    function challengeSubmission(uint256 payloadId) external whenNotPaused nonReentrant {
        Payload storage pl = payloads[payloadId];
        require(pl.tier == VerificationTier.OptimisticConsensus, "EscrowCore: not Tier 2");
        require(pl.isClaimed && !pl.isSolved, "EscrowCore: invalid state");
        require(!pl.isChallenged, "EscrowCore: already challenged");
        require(block.timestamp <= pl.claimExpiry, "EscrowCore: escrow expired");
        require(msg.sender != pl.claimedBy, "EscrowCore: cannot self-challenge");
        require(soulboundMass.canServeAsJuror(msg.sender), "EscrowCore: insufficient Mass for challenge");

        uint256 bond = (pl.bountyAmount * CHALLENGE_BOND_BPS) / 10000;
        require(usdc.transferFrom(msg.sender, address(this), bond), "EscrowCore: bond transfer failed");

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

    function registerAsJuror(uint256 payloadId) external whenNotPaused nonReentrant {
        Challenge storage ch = challenges[payloadId];
        Payload storage pl = payloads[payloadId];
        require(pl.isChallenged, "EscrowCore: not challenged");
        require(!ch.isResolved, "EscrowCore: already resolved");
        require(msg.sender != pl.claimedBy, "EscrowCore: solver cannot be juror");
        require(msg.sender != ch.challenger, "EscrowCore: challenger cannot be juror");
        require(soulboundMass.canServeAsJuror(msg.sender), "EscrowCore: insufficient Mass");

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

        uint256 jurorBond = (pl.bountyAmount * JUROR_BOND_BPS) / 10000;
        if (jurorBond > 0) {
            require(usdc.transferFrom(msg.sender, address(this), jurorBond), "EscrowCore: juror bond failed");
        }
    }

    function castJuryVote(uint256 payloadId, bool accept) external whenNotPaused nonReentrant {
        Challenge storage ch = challenges[payloadId];
        require(!ch.isResolved, "EscrowCore: already resolved");
        require(!jurorHasVoted[payloadId][msg.sender], "EscrowCore: already voted");

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

        if (ch.acceptVotes >= JURY_MAJORITY || ch.rejectVotes >= JURY_MAJORITY) {
            _resolveChallenge(payloadId);
        }
    }

    function finalizeTier2(uint256 payloadId) external whenNotPaused nonReentrant {
        Payload storage pl = payloads[payloadId];
        require(pl.tier == VerificationTier.OptimisticConsensus, "EscrowCore: not Tier 2");
        require(pl.isClaimed && !pl.isSolved, "EscrowCore: invalid state");
        require(!pl.isChallenged, "EscrowCore: is challenged");
        require(block.timestamp > pl.claimExpiry, "EscrowCore: escrow active");

        pl.isSolved = true;
        uint256 massAmount = _executePayout(payloadId, pl.claimedBy);

        emit PayloadSolved(payloadId, pl.claimedBy, pl.bountyAmount, massAmount);
    }

    // ═══════════════════════════════════════════════════════
    // INTERNAL: PAYOUT & TAX ROUTING
    // ═══════════════════════════════════════════════════════

    function _executePayout(uint256 payloadId, address solver) internal returns (uint256) {
        Payload storage pl = payloads[payloadId];
        uint256 bounty = pl.bountyAmount;

        uint256 solverPayout = (bounty * payoutRatios.capillaryBps) / 10000;
        uint256 mycelialPayout = (bounty * payoutRatios.mycelialBps) / 10000;
        uint256 conduitPayout = bounty - solverPayout - mycelialPayout;

        require(usdc.transfer(solver, solverPayout), "EscrowCore: solver payout failed");
        require(usdc.transfer(treasury, mycelialPayout), "EscrowCore: mycelial failed");
        
        address[] storage route = routingPath[payloadId];
        if (route.length > 0) {
            uint256 perNode = conduitPayout / route.length;
            for (uint256 i = 0; i < route.length; i++) {
                usdc.transfer(route[i], perNode);
            }
        } else {
            usdc.transfer(treasury, conduitPayout);
        }

        uint256 massAmount = bounty / 100;
        soulboundMass.accrueMass(solver, massAmount);

        return massAmount;
    }

    function _routeMetabolicTax(uint256 tax) internal {
        if (coreContributorTaxSunset) {
            usdc.transfer(treasury, tax);
        } else {
            uint256 coreShare = (tax * CORE_CONTRIBUTOR_BPS) / METABOLIC_TAX_BPS;
            uint256 treasuryShare = tax - coreShare;
            usdc.transfer(treasury, treasuryShare);
            usdc.transfer(coreContributor, coreShare);
        }
    }

    function _resolveChallenge(uint256 payloadId) internal {
        Challenge storage ch = challenges[payloadId];
        Payload storage pl = payloads[payloadId];
        
        ch.isResolved = true;
        bool upheld = ch.acceptVotes >= JURY_MAJORITY;

        // Cache solver address before any state changes
        address solver = pl.claimedBy;

        if (upheld) {
            pl.isSolved = true;
            _executePayout(payloadId, solver);

            // Distribute challenger's bond to jurors, send dust to treasury
            uint256 jurorReward = ch.challengeBond / JURY_SIZE;
            uint256 distributedReward;
            for (uint8 i = 0; i < JURY_SIZE; i++) {
                if (ch.jurors[i] != address(0)) {
                    usdc.transfer(ch.jurors[i], jurorReward);
                    distributedReward += jurorReward;
                }
            }
            uint256 rewardDust = ch.challengeBond - distributedReward;
            if (rewardDust > 0) usdc.transfer(treasury, rewardDust);
        } else {
            soulboundMass.recordFailure(solver);

            pl.isClaimed = false;
            pl.claimedBy = address(0);
            pl.isChallenged = false;
            pl.hasPhaseShifted = false;
            pl.phaseShiftTimestamp = 0;

            uint256 whistleblowerReward = (pl.bountyAmount * WHISTLEBLOWER_BPS) / 10000;
            usdc.transfer(ch.challenger, ch.challengeBond + whistleblowerReward);
        }

        // Return juror bonds and pay juror fees, send dust to treasury
        uint256 jurorBond = (pl.bountyAmount * JUROR_BOND_BPS) / 10000;
        uint256 jurorFee = (pl.bountyAmount * JUROR_FEE_BPS) / 10000;
        uint256 perJuror = jurorBond + jurorFee;
        uint256 distributedJuror;
        for (uint8 i = 0; i < JURY_SIZE; i++) {
            if (ch.jurors[i] != address(0)) {
                usdc.transfer(ch.jurors[i], perJuror);
                distributedJuror += perJuror;
            }
        }

        emit ChallengeResolved(payloadId, upheld, solver);
    }

    function _getEscrowDuration(uint256 bountyAmount) internal pure returns (uint256) {
        if (bountyAmount < SMALL_BOUNTY_THRESHOLD) return ESCROW_SMALL;
        if (bountyAmount < LARGE_BOUNTY_THRESHOLD) return ESCROW_MEDIUM;
        return ESCROW_LARGE;
    }

    // ═══════════════════════════════════════════════════════
    // GOVERNANCE & ADMIN (V3.4 Alpha Controls Added)
    // ═══════════════════════════════════════════════════════

    function toggleGlobalAlpha(bool _state) external onlyOwner {
        globalAlphaActive = _state;
    }

    function setAlphaCreator(address _creator, bool _status) external onlyOwner {
        isAlphaCreator[_creator] = _status;
    }

    function setAlphaOperator(address _operator, bool _status) external onlyOwner {
        isAlphaOperator[_operator] = _status;
    }

    function updatePayoutRatios(uint16 capillary, uint16 mycelial, uint16 conduit) external onlyOwner {
        require(uint256(capillary) + uint256(mycelial) + uint256(conduit) == 10000, "EscrowCore: sum to 10000");
        payoutRatios = PayoutRatios(capillary, mycelial, conduit);
    }

    function sunsetCoreContributorTax() external {
        require(msg.sender == owner || msg.sender == treasury, "EscrowCore: not authorized");
        coreContributorTaxSunset = true;
    }
    function setRoutingPath(uint256 payloadId, address[] calldata nodes) external onlyOwner { routingPath[payloadId] = nodes; }
    function pause() external onlyOwner { paused = true; }
    function unpause() external onlyOwner { paused = false; }
    
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "EscrowCore: zero address");
        owner = newOwner;
    }

    // ── View Functions ──────────────────────────────────────

    function getPayload(uint256 payloadId) external view returns (Payload memory) { return payloads[payloadId]; }
    function getChallenge(uint256 payloadId) external view returns (Challenge memory) { return challenges[payloadId]; }
}
