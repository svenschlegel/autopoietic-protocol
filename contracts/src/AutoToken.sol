// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title AutoToken
 * @notice The $AUTO governance token for the Autopoietic Protocol (V3.4)
 * @dev Implements:
 * - Standard ERC-20 for Gravitational Staking governance
 * - Total supply: 1,000,000,000 (1B) tokens
 * - Architect vesting with 1-year cliff + 3-year linear (Section 6.3)
 * - VRGDA continuous auction: 100 tokens/day target, $0.10 base (Section 4.2)
 * - 1% VRGDA Mint Burn: deflationary on every purchase (Section 6.3.4)
 * - 50% Milestone Burn: unvested architect tokens burned at $5M treasury (Section 6.3.4)
 * - 20/80 Genesis Development Cost Recovery: Year 1 VRGDA split (Section 6.3.3)
 * - Circuit breaker halting issuance when treasury is low
 * - Delegation firewall: labor wallets cannot delegate (Section 5.3)
 *
 * $AUTO is used STRICTLY for governance (Gravitational Staking).
 * It does NOT pay for compute. Agents are paid in USDC.
 *
 * Deployed on Base L2 (OP Stack)
 */
contract AutoToken {

    // ── ERC-20 State ────────────────────────────────────────

    string public constant name = "Autopoietic Protocol";
    string public constant symbol = "AUTO";
    uint8 public constant decimals = 18;
    
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    // ── Supply Constants ──────────────────────────────────────

    /// @notice Maximum total supply: 1,000,000,000 $AUTO (V3.4 spec)
    uint256 public constant MAX_SUPPLY = 1_000_000_000e18;
    /// @notice Tokens permanently removed from circulation
    uint256 public totalBurned;

    // ── Vesting State (Section 6.3) ──────────────────────────

    /// @notice Architect's total allocation (10% of max supply = 100M)
    uint256 public immutable architectAllocation;
    /// @notice Architect wallet (Sleeping Giant)
    address public immutable architect;
    /// @notice Vesting start timestamp
    uint256 public immutable vestingStart;
    /// @notice 1-year cliff
    uint256 public constant CLIFF_DURATION = 365 days;
    /// @notice Total vesting period: 4 years
    uint256 public constant VESTING_DURATION = 4 * 365 days;
    /// @notice Amount already claimed by architect
    uint256 public architectClaimed;
    /// @notice Whether the milestone burn has been executed
    bool public milestoneBurnExecuted;
    /// @notice Tokens burned via the milestone burn event
    uint256 public milestoneBurnAmount;

    // ── VRGDA State (Section 4.2) ────────────────────────────

    /// @notice Target tokens sold per day via VRGDA
    uint256 public constant TARGET_PER_DAY = 100e18; // 100 tokens/day (V3.4)
    
    /// @notice VRGDA start timestamp
    uint256 public vrgdaStartTime;
    /// @notice Total tokens sold via VRGDA (before burn)
    uint256 public vrgdaSold;
    /// @notice Base price in USDC (6 decimals): $0.10
    uint256 public constant BASE_PRICE = 0.1e6; // 0.10 USDC (V3.4)

    /// @notice Whether VRGDA issuance is halted (circuit breaker)
    bool public vrgdaHalted;

    // ── Burn Constants (Section 6.3.4) ────────────────────────

    /// @notice 1% of every VRGDA mint is burned (100 bps)
    uint16 public constant MINT_BURN_BPS = 100;
    /// @notice 50% of unvested architect tokens burned at milestone
    uint16 public constant MILESTONE_BURN_BPS = 5000;

    // ── Genesis Development Cost Recovery (Section 6.3.3) ─────

    /// @notice Developer wallet for cost recovery
    address public immutable developerWallet;
    /// @notice Recovery split: 20% to developer, 80% to treasury
    uint16 public constant GENESIS_RECOVERY_BPS = 2000; // 20%

    /// @notice Duration of the recovery period (12 months)
    uint256 public constant GENESIS_RECOVERY_DURATION = 365 days;
    /// @notice Total USDC routed to developer via recovery
    uint256 public genesisRecoveryPaid;
    /// @notice Total USDC routed to treasury via VRGDA
    uint256 public vrgdaTreasuryTotal;
    /// @notice Protocol treasury address
    address public treasury;

    // ── Delegation Firewall (Section 5.3) ────────────────────

    /// @notice Labor wallets (earn USDC bounties, cannot delegate)
    mapping(address => bool) public isLaborWallet;

    // ── Access Control ──────────────────────────────────────

    address public owner;
    address public escrowCore;

    // ── Events ──────────────────────────────────────────────

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event VRGDAPurchase(address indexed buyer, uint256 amountMinted, uint256 amountBurned, uint256 price);
    event VRGDAHalted();
    event VRGDAResumed();
    event LaborWalletRegistered(address indexed wallet);
    event ArchitectClaim(uint256 amount, uint256 totalClaimed);
    event GenesisRecoverySplit(uint256 developerShare, uint256 treasuryShare);
    event MintBurn(uint256 amount);
    event MilestoneBurn(uint256 amount, uint256 remainingArchitectAllocation);
    event TokensBurned(address indexed from, uint256 amount);

    // ── Modifiers ───────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "AutoToken: not owner");
        _;
    }

    // ── Constructor ─────────────────────────────────────────

    /**
     * @param _architect Genesis architect wallet (Sleeping Giant)
     * @param _treasury Protocol-Owned Treasury address
     * @dev Mints 10% to vesting contract (this), 5% to treasury.
     * Remaining 85% issued via VRGDA over time.
     */
    constructor(address _architect, address _treasury) {
        require(_architect != address(0) && _treasury != address(0), "AutoToken: zero address");
        owner = msg.sender;
        architect = _architect;
        developerWallet = _architect; // Same wallet for genesis
        treasury = _treasury;
        vestingStart = block.timestamp;
        vrgdaStartTime = block.timestamp;
        
        // 10% architect allocation: 100,000,000 $AUTO
        architectAllocation = MAX_SUPPLY / 10;
        
        // Mint architect allocation to THIS contract (held in vesting)
        _mint(address(this), architectAllocation);
        
        // Mint 5% treasury allocation: 50,000,000 $AUTO (Genesis Geyser funding)
        _mint(_treasury, MAX_SUPPLY * 5 / 100);
    }

    // ═══════════════════════════════════════════════════════
    // ERC-20 CORE
    // ═══════════════════════════════════════════════════════

    /// @notice Transfer $AUTO tokens
    function transfer(address to, uint256 amount) external returns (bool) {
        _transfer(msg.sender, to, amount);
        return true;
    }

    /// @notice Approve a spender
    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    /// @notice Transfer tokens from another address (requires approval)
    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        require(allowance[from][msg.sender] >= amount, "AutoToken: insufficient allowance");
        allowance[from][msg.sender] -= amount;
        _transfer(from, to, amount);
        return true;
    }

    function _transfer(address from, address to, uint256 amount) internal {
        require(from != address(0) && to != address(0), "AutoToken: zero address");
        require(balanceOf[from] >= amount, "AutoToken: insufficient balance");
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        emit Transfer(from, to, amount);
    }

    function _mint(address to, uint256 amount) internal {
        totalSupply += amount;
        balanceOf[to] += amount;
        emit Transfer(address(0), to, amount);
    }

    /// @dev Internal burn — permanently removes tokens from circulation
    function _burn(address from, uint256 amount) internal {
        require(balanceOf[from] >= amount, "AutoToken: burn exceeds balance");
        balanceOf[from] -= amount;
        totalSupply -= amount;
        totalBurned += amount;
        emit Transfer(from, address(0), amount);
        emit TokensBurned(from, amount);
    }

    // ═══════════════════════════════════════════════════════
    // ARCHITECT VESTING (Section 6.3)
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Calculate vested amount available to the architect
     * @return The total amount vested (including already claimed)
     * @dev 1-year cliff, then linear vesting over remaining 3 years.
     * If milestone burn has executed, the effective allocation
     * is reduced by the burned amount.
     */
    function vestedAmount() public view returns (uint256) {
        if (block.timestamp < vestingStart + CLIFF_DURATION) {
            return 0;
        }
        
        // Effective allocation after any milestone burn
        uint256 effectiveAllocation = architectAllocation - milestoneBurnAmount;
        uint256 elapsed = block.timestamp - vestingStart;
        if (elapsed >= VESTING_DURATION) {
            return effectiveAllocation;
        }
        
        return (effectiveAllocation * elapsed) / VESTING_DURATION;
    }

    /**
     * @notice Architect claims vested tokens
     * @dev Transfers vested but unclaimed tokens from this contract to architect
     */
    function claimVested() external {
        require(msg.sender == architect, "AutoToken: not architect");
        uint256 vested = vestedAmount();
        uint256 claimable = vested - architectClaimed;
        require(claimable > 0, "AutoToken: nothing to claim");
        
        architectClaimed += claimable;
        _transfer(address(this), architect, claimable);
        
        emit ArchitectClaim(claimable, architectClaimed);
    }

    // ═══════════════════════════════════════════════════════
    // VRGDA PRICING ENGINE & CONTINUOUS AUCTION (Section 4.2)
    // ═══════════════════════════════════════════════════════

    /// @dev Internal pure function to calculate the exact spot price at a specific supply
    function _priceAt(uint256 sold, uint256 targetSold) internal pure returns (uint256) {
        if (sold <= targetSold) {
            uint256 deficit = targetSold - sold;
            uint256 discount = (deficit * BASE_PRICE * 50) / (targetSold * 100);
            if (discount >= BASE_PRICE / 2) return BASE_PRICE / 2;
            return BASE_PRICE - discount;
        } else {
            uint256 surplus = sold - targetSold;
            uint256 doublings = (surplus * 1e18) / TARGET_PER_DAY;
            if (doublings > 8e18) doublings = 8e18; // Cap at 9x
            uint256 multiplier = 1e18 + doublings;
            return (BASE_PRICE * multiplier) / 1e18;
        }
    }

    /// @notice Get the current spot price for 1 $AUTO token (UI Helper)
    function getVRGDAPrice() public view returns (uint256) {
        uint256 daysElapsed = (block.timestamp - vrgdaStartTime) / 1 days;
        if (daysElapsed == 0) daysElapsed = 1;
        return _priceAt(vrgdaSold, TARGET_PER_DAY * daysElapsed);
    }

    /// @notice Calculates the exact continuous cost (area under the curve) for a batch purchase
    function getVRGDACost(uint256 amount) public view returns (uint256) {
        if (amount == 0) return 0;
        
        uint256 daysElapsed = (block.timestamp - vrgdaStartTime) / 1 days;
        if (daysElapsed == 0) daysElapsed = 1;
        uint256 targetSold = TARGET_PER_DAY * daysElapsed;

        uint256 startSold = vrgdaSold;
        uint256 endSold = startSold + amount;

        // Trapezoidal integration of the piecewise linear curve
        if (endSold <= targetSold) {
            // Entire purchase is in the deficit (discount) zone
            uint256 pStart = _priceAt(startSold, targetSold);
            uint256 pEnd = _priceAt(endSold, targetSold);
            return (amount * (pStart + pEnd)) / (2 * 1e18);
        } else if (startSold >= targetSold) {
            // Entire purchase is in the surplus (premium) zone
            uint256 pStart = _priceAt(startSold, targetSold);
            uint256 pEnd = _priceAt(endSold, targetSold);
            return (amount * (pStart + pEnd)) / (2 * 1e18);
        } else {
            // Purchase crosses the equilibrium target (V-shaped curve)
            uint256 amountDeficit = targetSold - startSold;
            uint256 amountSurplus = endSold - targetSold;

            uint256 pStart = _priceAt(startSold, targetSold);
            uint256 pTarget = BASE_PRICE; // Price exactly at target
            uint256 pEnd = _priceAt(endSold, targetSold);

            uint256 costDeficit = (amountDeficit * (pStart + pTarget)) / (2 * 1e18);
            uint256 costSurplus = (amountSurplus * (pTarget + pEnd)) / (2 * 1e18);

            return costDeficit + costSurplus;
        }
    }

    /**
     * @notice Purchase $AUTO tokens via the VRGDA auction
     * @param amount Number of tokens to purchase (18 decimals)
     * @param maxPrice Maximum AVERAGE USDC price per token (slippage protection)
     * @param usdc USDC token address for payment
     * @dev Implements:
     * 1. Genesis Development Cost Recovery (20/80 split, Year 1 only)
     * 2. 1% VRGDA Mint Burn (deflationary on every purchase)
     * For every 100 tokens purchased, 99 go to the buyer and 1 is burned.
     */
    function purchaseVRGDA(
        uint256 amount,
        uint256 maxPrice,
        address usdc
    ) external {
        require(!vrgdaHalted, "AutoToken: VRGDA halted (circuit breaker)");
        require(amount > 0, "AutoToken: zero amount");
        require(
            totalSupply + amount <= MAX_SUPPLY,
            "AutoToken: max supply reached"
        );

        // Calculate integrated cost with continuous slippage enforced
        uint256 totalCost = getVRGDACost(amount);
        require(totalCost > 0, "AutoToken: zero cost");
        
        // Ensure the average price paid doesn't exceed the user's slippage limit
        uint256 avgPrice = (totalCost * 1e18) / amount;
        require(avgPrice <= maxPrice, "AutoToken: average price exceeds maxPrice");
        
        // ── USDC Routing: Genesis Development Cost Recovery ──
        if (block.timestamp <= vrgdaStartTime + GENESIS_RECOVERY_DURATION) {
            uint256 devShare = (totalCost * GENESIS_RECOVERY_BPS) / 10000;
            uint256 treasuryShare = totalCost - devShare;
            
            IERC20Minimal(usdc).transferFrom(msg.sender, developerWallet, devShare);
            IERC20Minimal(usdc).transferFrom(msg.sender, treasury, treasuryShare);
            
            genesisRecoveryPaid += devShare;
            vrgdaTreasuryTotal += treasuryShare;
            emit GenesisRecoverySplit(devShare, treasuryShare);
        } else {
            IERC20Minimal(usdc).transferFrom(msg.sender, treasury, totalCost);
            vrgdaTreasuryTotal += totalCost;
        }
        
        // ── Token Minting with 1% Burn ──
        uint256 burnAmount = (amount * MINT_BURN_BPS) / 10000;
        uint256 buyerAmount = amount - burnAmount;
        
        // Mint to buyer (99%)
        _mint(msg.sender, buyerAmount);
        
        // Mint and burn (1%) — increases totalBurned, reduces effective supply
        if (burnAmount > 0) {
            _mint(address(this), burnAmount);
            _burn(address(this), burnAmount);
            emit MintBurn(burnAmount);
        }
        
        vrgdaSold += amount;
        emit VRGDAPurchase(msg.sender, buyerAmount, burnAmount, avgPrice);
    }

    // ═══════════════════════════════════════════════════════
    // MILESTONE BURN (Section 6.3.4)
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Execute the milestone burn: burn 50% of unvested architect tokens
     * @dev Triggered exclusively by the Treasury contract when $5M CPI-adjusted target is reached.
     * Burns tokens held in this contract (vesting), not tokens already claimed.
     *
     * Oracle heartbeat fallback (Section 7.5.4):
     * - Live Chainlink CPI feed → last known value (72h stale) → 2.5% annual hardcoded (30d stale)
     * The CPI check is performed by the calling contract (Treasury), not here.
     */
    function executeMilestoneBurn() external {
        // FIXED: Removed onlyOwner, restricted to the Treasury contract
        require(msg.sender == treasury, "AutoToken: only treasury can trigger");
        require(!milestoneBurnExecuted, "AutoToken: milestone already executed");
        
        // Calculate unvested amount
        uint256 unvested = architectAllocation - vestedAmount();
        require(unvested > 0, "AutoToken: no unvested tokens");
        
        // Burn 50% of unvested
        uint256 burnAmount = (unvested * MILESTONE_BURN_BPS) / 10000;
        
        milestoneBurnExecuted = true;
        milestoneBurnAmount = burnAmount;
        
        _burn(address(this), burnAmount);
        
        emit MilestoneBurn(burnAmount, architectAllocation - architectClaimed - burnAmount);
    }

    // ═══════════════════════════════════════════════════════
    // DELEGATION FIREWALL (Section 5.3)
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Register a wallet as a labor wallet (earns USDC bounties)
     * @dev Labor wallets cannot participate in governance delegation.
     * Called by EscrowCore when an agent first claims a payload.
     */
    function registerLaborWallet(address wallet) external {
        require(
            msg.sender == escrowCore || msg.sender == owner,
            "AutoToken: not authorized"
        );
        isLaborWallet[wallet] = true;
        emit LaborWalletRegistered(wallet);
    }

    /// @notice Check if a wallet can participate in governance delegation
    function canDelegate(address wallet) external view returns (bool) {
        return !isLaborWallet[wallet];
    }

    // ═══════════════════════════════════════════════════════
    // ADMIN & CIRCUIT BREAKER
    // ═══════════════════════════════════════════════════════

    /// @notice Set the EscrowCore contract address
    function setEscrowCore(address _escrowCore) external onlyOwner {
        escrowCore = _escrowCore;
    }

    /// @notice Update the treasury address
    function setTreasury(address _treasury) external onlyOwner {
        require(_treasury != address(0), "AutoToken: zero address");
        treasury = _treasury;
    }

    /// @notice Halt VRGDA issuance (treasury circuit breaker)
    function haltVRGDA() external onlyOwner {
        vrgdaHalted = true;
        emit VRGDAHalted();
    }

    /// @notice Resume VRGDA issuance
    function resumeVRGDA() external onlyOwner {
        vrgdaHalted = false;
        emit VRGDAResumed();
    }

    /// @notice Transfer contract ownership (to DUNA governance)
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "AutoToken: zero address");
        owner = newOwner;
    }

    // ═══════════════════════════════════════════════════════
    // VIEW FUNCTIONS
    // ═══════════════════════════════════════════════════════

    /// @notice Get the effective circulating supply (total minus burned minus vesting-locked)
    function circulatingSupply() external view returns (uint256) {
        uint256 vestingLocked = architectAllocation - architectClaimed - milestoneBurnAmount;
        return totalSupply - vestingLocked;
    }

    /// @notice Get the effective max supply after all burns
    function effectiveMaxSupply() external view returns (uint256) {
        return MAX_SUPPLY - totalBurned;
    }
}

/**
 * @title IERC20Minimal
 * @notice Minimal interface for USDC transfers
 */
interface IERC20Minimal {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}
