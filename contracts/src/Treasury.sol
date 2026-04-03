// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "src/EscrowCore.sol";

interface IEscrowCore {
    function sunsetCoreContributorTax() external;
}

interface IAutoToken {
    function executeMilestoneBurn() external;
}

interface AggregatorV3Interface {
    function latestRoundData() external view returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    );
}

/**
 * @title Treasury
 * @notice Protocol-Owned Treasury for the Autopoietic Protocol (V3.4)
 * @dev Implements:
 * - USDC reserve management & Circuit Breaker
 * - Ecosystem Expansion automatic deployment
 * - Cross-contract execution of Milestone Burn & Tax Sunset
 * - CPI Oracle Heartbeat Fallback (Section 7.5.4)
 */
contract Treasury {

    // ── Reentrancy Guard ─────────────────────────────────────

    uint256 private _locked = 1;
    modifier nonReentrant() {
        require(_locked == 1, "Treasury: reentrant call");
        _locked = 2;
        _;
        _locked = 1;
    }

    // ── State ───────────────────────────────────────────────

    IERC20 public usdc;
    address public owner;
    address public emergencyAdmin; // Multisig for instant emergency withdraw
    
    address public escrowCore;
    address public autoToken;
    
    AggregatorV3Interface public cpiOracle;

    uint256 public minimumReserve;
    uint256 public immutable genesisTimestamp;

    // Base threshold in 2026 dollars (USDC 6 decimals) scaled for $2M FDV Genesis
    uint256 public constant BASE_SUNSET_THRESHOLD = 500_000e6; // $500,000
    
    // Fallback constants
    uint256 public constant ORACLE_STALE_72H = 72 hours;
    uint256 public constant ORACLE_DEAD_30D = 30 days;
    uint256 public constant HARDCODED_ANNUAL_INFLATION_BPS = 250; // 2.5%

    uint256 public surplusStartTimestamp;
    uint256 public constant SURPLUS_DURATION = 30 days;

    mapping(bytes32 => bool) public approvedCategories;

    uint256 public totalReceived;
    uint256 public totalDeployed;
    
    bool public milestoneTriggersExecuted;

    // ── Events ──────────────────────────────────────────────

    event FundsReceived(address indexed from, uint256 amount);
    event FundsDeployed(address indexed to, uint256 amount, bytes32 category);
    event MinimumReserveUpdated(uint256 newMinimum);
    event EcosystemExpansionTriggered(uint256 surplusAmount);
    event CategoryApproved(bytes32 indexed category);
    event MilestoneTriggersExecuted(uint256 thresholdHit);
    event BaseCurrencyMigrated(address indexed oldToken, address indexed newToken);
    event OracleFallbackActivated(string reason, uint256 adjustedThreshold);

    // ── Modifiers ───────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "Treasury: not owner");
        _;
    }

    // ── Constructor ─────────────────────────────────────────

    constructor(address _usdc, uint256 _minimumReserve, address _cpiOracle) {
        usdc = IERC20(_usdc);
        cpiOracle = AggregatorV3Interface(_cpiOracle);
        owner = msg.sender;
        minimumReserve = _minimumReserve;
        genesisTimestamp = block.timestamp;

        approvedCategories[keccak256("Infrastructure")] = true;
        approvedCategories[keccak256("DataCommons")] = true;
        approvedCategories[keccak256("Research")] = true;
    }

    // ═══════════════════════════════════════════════════════
    // INFLOW & OUTFLOW
    // ═══════════════════════════════════════════════════════

    function deposit(uint256 amount) external nonReentrant {
        require(usdc.transferFrom(msg.sender, address(this), amount), "Treasury: deposit failed");
        totalReceived += amount;
        emit FundsReceived(msg.sender, amount);
        _checkSurplusStatus();
    }

    function deploy(address to, uint256 amount, bytes32 category) external onlyOwner nonReentrant {
        require(approvedCategories[category], "Treasury: unapproved category");
        require(usdc.balanceOf(address(this)) - amount >= minimumReserve, "Treasury: would breach minimum reserve");

        require(usdc.transfer(to, amount), "Treasury: transfer failed");
        totalDeployed += amount;

        emit FundsDeployed(to, amount, category);
    }

    // ═══════════════════════════════════════════════════════
    // CIRCUIT BREAKER & SURPLUS
    // ═══════════════════════════════════════════════════════

    function isCircuitBreakerActive() public view returns (bool) {
        return usdc.balanceOf(address(this)) < minimumReserve;
    }

    function setMinimumReserve(uint256 newMinimum) external onlyOwner {
        minimumReserve = newMinimum;
        emit MinimumReserveUpdated(newMinimum);
    }

    function _checkSurplusStatus() internal {
        uint256 balance = usdc.balanceOf(address(this));
        uint256 surplusThreshold = minimumReserve * 2;

        if (balance >= surplusThreshold) {
            if (surplusStartTimestamp == 0) surplusStartTimestamp = block.timestamp;
        } else {
            surplusStartTimestamp = 0;
        }
    }

    function isExpansionReady() public view returns (bool) {
        if (surplusStartTimestamp == 0) return false;
        return block.timestamp >= surplusStartTimestamp + SURPLUS_DURATION;
    }

    // ═══════════════════════════════════════════════════════
    // ORACLE FALLBACK & MILESTONE TRIGGERS (V3.4 Section 7.5.4)
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Calculates the CPI-adjusted $500k threshold with rigorous fallback mechanisms.
     */
    function getAdjustedMilestoneThreshold() public view returns (uint256) {
        if (address(cpiOracle) == address(0)) {
            return _calculateHardcodedInflation(); // Testnet or pure fallback
        }

        try cpiOracle.latestRoundData() returns (
            uint80 /* roundId */,
            int256 answer,
            uint256 /* startedAt */,
            uint256 updatedAt,
            uint80 /* answeredInRound */
        ) {
            uint256 timeSinceUpdate = block.timestamp - updatedAt;

            // Condition 3: Dead Oracle (>30 days). Fall back to 2.5% hardcoded annual.
            if (timeSinceUpdate > ORACLE_DEAD_30D) {
                return _calculateHardcodedInflation();
            }
            
            // Condition 1 & 2: Live or Stale-but-acceptable (<30 days). Use last known CPI.
            // Assuming oracle returns percentage increase scaled by 1e8 (Chainlink standard)
            // Example: 1e8 = baseline, 1.05e8 = 5% inflation.
            if (answer > 0) {
                uint256 inflationMultiplier = uint256(answer);
                return (BASE_SUNSET_THRESHOLD * inflationMultiplier) / 1e8;
            } else {
                return _calculateHardcodedInflation();
            }
        } catch {
            // Oracle contract reverted
            return _calculateHardcodedInflation();
        }
    }

    /**
     * @notice Applies a flat 2.5% annual inflation to the base threshold if oracle fails.
     */
    function _calculateHardcodedInflation() internal view returns (uint256) {
        uint256 yearsElapsed = (block.timestamp - genesisTimestamp) / 365 days;
        uint256 adjusted = BASE_SUNSET_THRESHOLD;
        
        // Simple linear 2.5% per year adjustment
        for (uint256 i = 0; i < yearsElapsed; i++) {
            adjusted = adjusted + ((adjusted * HARDCODED_ANNUAL_INFLATION_BPS) / 10000);
        }
        return adjusted;
    }

    /**
     * @notice Checks if threshold is met and triggers external actions.
     * @dev Anyone can call this to enforce decentralization.
     */
    function executeMilestoneTriggers() external nonReentrant {
        require(!milestoneTriggersExecuted, "Treasury: triggers already executed");
        require(autoToken != address(0) && escrowCore != address(0), "Treasury: addresses not set");

        uint256 currentThreshold = getAdjustedMilestoneThreshold();
        require(usdc.balanceOf(address(this)) >= currentThreshold, "Treasury: threshold not reached");

        milestoneTriggersExecuted = true;

        // 1. Tell Escrow to stop taking the 1% architect tax
        IEscrowCore(escrowCore).sunsetCoreContributorTax();

        // 2. Tell AutoToken to burn 50% of the architect's unvested governance tokens
        IAutoToken(autoToken).executeMilestoneBurn();

        emit MilestoneTriggersExecuted(currentThreshold);
    }

    // ── Admin ───────────────────────────────────────────────

    function setProtocolContracts(address _escrowCore, address _autoToken) external onlyOwner {
        escrowCore = _escrowCore;
        autoToken = _autoToken;
    }

    function setOracle(address _cpiOracle) external onlyOwner {
        cpiOracle = AggregatorV3Interface(_cpiOracle);
    }

    function approveCategory(bytes32 category) external onlyOwner {
        approvedCategories[category] = true;
        emit CategoryApproved(category);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Treasury: zero address");
        owner = newOwner;
    }

    function emergencyWithdraw(address to, uint256 amount) external nonReentrant {
        require(msg.sender == owner || msg.sender == emergencyAdmin, "Treasury: not authorized");
        require(usdc.transfer(to, amount), "Treasury: emergency failed");
    }

    function setEmergencyAdmin(address _emergencyAdmin) external onlyOwner {
        emergencyAdmin = _emergencyAdmin;
    }

    /**
     * @notice Migrate the Treasury's base currency to a new ERC-20 stablecoin
     * @param newToken The replacement stablecoin address (e.g., DAI, LUSD)
     * @dev Emergency migration flow (executed by multisig):
     *   1. Pause protocol (EscrowCore.pause + AutoToken.haltVRGDA)
     *   2. emergencyWithdraw all old token to the multisig Safe
     *   3. Swap old token for new token off-chain (e.g., Aerodrome)
     *   4. Call migrateBaseCurrency(newToken) — this function
     *   5. Transfer new token back into Treasury
     *   6. Unpause protocol
     *
     *   Protected by onlyOwner (Timelock with 48h delay).
     *   Does NOT migrate EscrowCore — active escrows are short-lived
     *   and share Circle counterparty risk by design.
     */
    function migrateBaseCurrency(address newToken) external onlyOwner {
        require(newToken != address(0), "Treasury: zero address");
        require(newToken != address(usdc), "Treasury: same token");

        address oldToken = address(usdc);
        usdc = IERC20(newToken);

        emit BaseCurrencyMigrated(oldToken, newToken);
    }

    // ── View Helpers ─────────────────────────────────────────

    function shouldSunsetCoreTax() public view returns (bool) {
        return usdc.balanceOf(address(this)) >= getAdjustedMilestoneThreshold();
    }

    function expansionBudget() public view returns (uint256) {
        uint256 balance = usdc.balanceOf(address(this));
        if (balance <= minimumReserve) return 0;
        return balance - minimumReserve;
    }

    function getHealth() external view returns (
        uint256 balance,
        uint256 minimum,
        bool healthy,
        bool expansionReady,
        bool sunsetReady
    ) {
        balance = usdc.balanceOf(address(this));
        minimum = minimumReserve;
        healthy = balance >= minimum;
        expansionReady = isExpansionReady();
        sunsetReady = shouldSunsetCoreTax();
    }
}
