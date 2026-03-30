// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
import "src/EscrowCore.sol";

/**
 * @title IERC20
 */

/**
 * @title Treasury
 * @notice Protocol-Owned Treasury for the Autopoietic Protocol
 * @dev Implements:
 *   - USDC reserve management
 *   - Circuit breaker threshold monitoring (V3 Section 4.4)
 *   - Ecosystem Expansion automatic deployment (V3 Section 4.4)
 *   - Core contributor tax sunset at $5M threshold (V3 Section 6.3)
 *   - Health metrics for governance dashboards
 */
contract Treasury {

    // ── State ───────────────────────────────────────────────

    IERC20 public immutable usdc;
    address public owner;
    address public escrowCore;

    /// @notice Minimum reserve ratio (USDC balance below which VRGDA halts)
    /// @dev Set to cover 90 days of estimated network operations
    uint256 public minimumReserve;

    /// @notice Core contributor tax sunset threshold (V3 spec: $5M)
    /// @dev In USDC (6 decimals). V3 notes this should be CPI-adjusted
    ///      via Chainlink oracle in production. For testnet: fixed $5M.
    uint256 public constant CORE_TAX_SUNSET_THRESHOLD = 5_000_000e6;

    /// @notice Ecosystem Expansion trigger: 200% of minimum reserve for 30 days
    uint256 public surplusStartTimestamp;
    uint256 public constant SURPLUS_DURATION = 30 days;

    /// @notice Whitelisted recipient categories for ecosystem expansion
    mapping(bytes32 => bool) public approvedCategories;

    /// @notice Total USDC received (lifetime)
    uint256 public totalReceived;

    /// @notice Total USDC deployed (payloads, grants, expenses)
    uint256 public totalDeployed;

    // ── Events ──────────────────────────────────────────────

    event FundsReceived(address indexed from, uint256 amount);
    event FundsDeployed(address indexed to, uint256 amount, bytes32 category);
    event MinimumReserveUpdated(uint256 newMinimum);
    event CircuitBreakerTriggered(uint256 balance, uint256 minimum);
    event CircuitBreakerCleared(uint256 balance, uint256 minimum);
    event EcosystemExpansionTriggered(uint256 surplusAmount);
    event CategoryApproved(bytes32 indexed category);
    event CoreTaxSunsetReached(uint256 balance);

    // ── Modifiers ───────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "Treasury: not owner");
        _;
    }

    modifier onlyAuthorized() {
        require(
            msg.sender == owner || msg.sender == escrowCore,
            "Treasury: not authorized"
        );
        _;
    }

    // ── Constructor ─────────────────────────────────────────

    /**
     * @param _usdc USDC token address on Base L2
     * @param _minimumReserve Initial minimum reserve (e.g., 100,000 USDC)
     */
    constructor(address _usdc, uint256 _minimumReserve) {
        usdc = IERC20(_usdc);
        owner = msg.sender;
        minimumReserve = _minimumReserve;

        // Pre-approve ecosystem expansion categories (V3 spec)
        approvedCategories[keccak256("Infrastructure")] = true;
        approvedCategories[keccak256("DataCommons")] = true;
        approvedCategories[keccak256("Research")] = true;

        emit CategoryApproved(keccak256("Infrastructure"));
        emit CategoryApproved(keccak256("DataCommons"));
        emit CategoryApproved(keccak256("Research"));
    }

    // ═══════════════════════════════════════════════════════
    // INFLOW
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Receive USDC (from metabolic tax, VRGDA auctions, etc.)
     * @param amount USDC amount to deposit
     */
    function deposit(uint256 amount) external {
        require(
            usdc.transferFrom(msg.sender, address(this), amount),
            "Treasury: deposit failed"
        );
        totalReceived += amount;
        emit FundsReceived(msg.sender, amount);

        // Check if surplus tracking should start/reset
        _checkSurplusStatus();
    }

    // ═══════════════════════════════════════════════════════
    // OUTFLOW
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Deploy USDC for ecosystem purposes
     * @param to Recipient address
     * @param amount USDC amount
     * @param category The purpose category (must be pre-approved)
     */
    function deploy(
        address to, 
        uint256 amount, 
        bytes32 category
    ) external onlyOwner {
        require(approvedCategories[category], "Treasury: unapproved category");
        require(
            usdc.balanceOf(address(this)) - amount >= minimumReserve,
            "Treasury: would breach minimum reserve"
        );

        require(usdc.transfer(to, amount), "Treasury: transfer failed");
        totalDeployed += amount;

        emit FundsDeployed(to, amount, category);
    }

    // ═══════════════════════════════════════════════════════
    // CIRCUIT BREAKER (V3 Section 4.4)
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Check if the circuit breaker should be active
     * @return True if USDC balance is below minimum reserve
     */
    function isCircuitBreakerActive() public view returns (bool) {
        return usdc.balanceOf(address(this)) < minimumReserve;
    }

    /**
     * @notice Update the minimum reserve threshold
     * @param newMinimum New minimum USDC reserve
     */
    function setMinimumReserve(uint256 newMinimum) external onlyOwner {
        minimumReserve = newMinimum;
        emit MinimumReserveUpdated(newMinimum);
    }

    // ═══════════════════════════════════════════════════════
    // ECOSYSTEM EXPANSION (V3 Section 4.4)
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Check if ecosystem expansion should trigger
     * @dev Triggers when balance > 200% of minimum reserve for 30+ days
     */
    function _checkSurplusStatus() internal {
        uint256 balance = usdc.balanceOf(address(this));
        uint256 surplusThreshold = minimumReserve * 2;

        if (balance >= surplusThreshold) {
            if (surplusStartTimestamp == 0) {
                surplusStartTimestamp = block.timestamp;
            }
        } else {
            surplusStartTimestamp = 0;
        }
    }

    /**
     * @notice Check if ecosystem expansion conditions are met
     * @return True if surplus has persisted for 30+ days
     */
    function isExpansionReady() public view returns (bool) {
        if (surplusStartTimestamp == 0) return false;
        return block.timestamp >= surplusStartTimestamp + SURPLUS_DURATION;
    }

    /**
     * @notice Get the amount available for ecosystem expansion
     * @return Excess USDC above the minimum reserve
     */
    function expansionBudget() public view returns (uint256) {
        uint256 balance = usdc.balanceOf(address(this));
        if (balance <= minimumReserve) return 0;
        return balance - minimumReserve;
    }

    // ═══════════════════════════════════════════════════════
    // CORE TAX SUNSET (V3 Section 6.3)
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Check if the core contributor tax should be sunset
     * @return True if treasury balance has reached the $5M threshold
     */
    function shouldSunsetCoreTax() public view returns (bool) {
        return usdc.balanceOf(address(this)) >= CORE_TAX_SUNSET_THRESHOLD;
    }

    // ═══════════════════════════════════════════════════════
    // HEALTH METRICS
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Get comprehensive treasury health data
     * @return balance Current USDC balance
     * @return minimum Minimum reserve threshold
     * @return healthy Whether balance exceeds minimum
     * @return expansionReady Whether expansion conditions are met
     * @return sunsetReady Whether core tax should sunset
     */
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

    // ── Admin ───────────────────────────────────────────────

    /// @notice Set the EscrowCore contract address (authorized depositor)
    /// @param _escrowCore The EscrowCore contract address
    function setEscrowCore(address _escrowCore) external onlyOwner {
        escrowCore = _escrowCore;
    }

    /// @notice Approve a new spending category for treasury deployments
    /// @param category keccak256 hash of the category name
    function approveCategory(bytes32 category) external onlyOwner {
        approvedCategories[category] = true;
        emit CategoryApproved(category);
    }

    /// @notice Transfer contract ownership (to DUNA governance)
    /// @param newOwner The new owner address
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Treasury: zero address");
        owner = newOwner;
    }

    /// @notice Emergency withdrawal (only for migration, requires governance)
    function emergencyWithdraw(address to, uint256 amount) external onlyOwner {
        require(usdc.transfer(to, amount), "Treasury: emergency failed");
    }
}
