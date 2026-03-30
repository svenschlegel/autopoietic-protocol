// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title AutoToken
 * @notice The $AUTO governance token for the Autopoietic Protocol
 * @dev Implements:
 *   - Standard ERC-20 for governance staking
 *   - Architect vesting with 1-year cliff + 3-year linear (V3 Section 6.3)
 *   - VRGDA continuous auction mechanics (V3 Section 4.4)
 *   - Circuit breaker halting issuance when treasury is low
 *   - Delegation firewall: labor wallets cannot delegate (V3 Section 5.3)
 *
 *   The $AUTO token is used STRICTLY for governance (Gravitational Staking).
 *   It does NOT pay for compute. Agents are paid in USDC.
 */
contract AutoToken {

    // ── ERC-20 State ────────────────────────────────────────

    string public constant name = "Autopoietic Protocol";
    string public constant symbol = "AUTO";
    uint8 public constant decimals = 18;
    
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    // ── Vesting State (V3 Section 6.3) ──────────────────────

    /// @notice Architect's total allocation (10% of max supply)
    uint256 public immutable architectAllocation;
    
    /// @notice Architect wallet
    address public immutable architect;
    
    /// @notice Vesting start timestamp
    uint256 public immutable vestingStart;
    
    /// @notice 1-year cliff (V3 spec)
    uint256 public constant CLIFF_DURATION = 365 days;
    
    /// @notice Total vesting period: 4 years (V3 spec)
    uint256 public constant VESTING_DURATION = 4 * 365 days;
    
    /// @notice Amount already claimed by architect
    uint256 public architectClaimed;

    // ── VRGDA State (V3 Section 4.4) ────────────────────────

    /// @notice Maximum total supply
    uint256 public constant MAX_SUPPLY = 100_000_000e18; // 100M tokens
    
    /// @notice Target tokens sold per day via VRGDA
    uint256 public constant TARGET_PER_DAY = 10e18; // 10 tokens/day
    
    /// @notice VRGDA start timestamp
    uint256 public vrgdaStartTime;
    
    /// @notice Total tokens sold via VRGDA
    uint256 public vrgdaSold;
    
    /// @notice VRGDA decay constant (controls price curve steepness)
    /// @dev In WAD (1e18) — higher = steeper price curve
    int256 public constant DECAY_CONSTANT = 0.31e18; // ~e^0.31 per unit ahead
    
    /// @notice Base price in USDC (6 decimals)
    uint256 public constant BASE_PRICE = 1e6; // 1 USDC

    /// @notice Whether VRGDA issuance is halted (circuit breaker)
    bool public vrgdaHalted;

    // ── Genesis CapEx Split (V3.2 Section 6.3.4) ────────────

    /// @notice Developer wallet for Genesis CapEx reimbursement
    address public immutable developerWallet;

    /// @notice Genesis CapEx split: 20% to developer, 80% to treasury (bps)
    uint16 public constant GENESIS_CAPEX_BPS = 2000; // 20%

    /// @notice Duration of the Genesis CapEx split (12 months)
    uint256 public constant GENESIS_CAPEX_DURATION = 365 days;

    /// @notice Total USDC routed to developer via Genesis CapEx
    uint256 public genesisCapExPaid;

    /// @notice Total USDC routed to treasury via VRGDA
    uint256 public vrgdaTreasuryTotal;

    // ── Delegation Firewall (V3 Section 5.3) ────────────────

    /// @notice Wallets registered as labor wallets (earn USDC bounties)
    /// @dev These wallets are cryptographically restricted from delegation
    mapping(address => bool) public isLaborWallet;

    // ── Access Control ──────────────────────────────────────

    address public owner;
    address public escrowCore; // EscrowCore contract (registers labor wallets)

    // ── Events ──────────────────────────────────────────────

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event VRGDAPurchase(address indexed buyer, uint256 amount, uint256 price);
    event VRGDAHalted();
    event VRGDAResumed();
    event LaborWalletRegistered(address indexed wallet);
    event ArchitectClaim(uint256 amount, uint256 totalClaimed);
    event GenesisCapExSplit(uint256 developerShare, uint256 treasuryShare);

    // ── Modifiers ───────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "AutoToken: not owner");
        _;
    }

    // ── Constructor ─────────────────────────────────────────

    /**
     * @param _architect Genesis architect wallet
     * @param _treasury Protocol treasury (receives initial non-vesting supply)
     */
    constructor(address _architect, address _treasury) {
        owner = msg.sender;
        architect = _architect;
        developerWallet = _architect; // Same as architect for genesis
        vestingStart = block.timestamp;
        vrgdaStartTime = block.timestamp;
        
        // Architect allocation: 10% of max supply (V3 spec)
        architectAllocation = MAX_SUPPLY / 10;
        
        // Mint architect allocation to THIS contract (held in vesting)
        _mint(address(this), architectAllocation);
        
        // Mint initial treasury allocation (5% for Genesis Geyser funding)
        _mint(_treasury, MAX_SUPPLY * 5 / 100);
    }

    // ═══════════════════════════════════════════════════════
    // ERC-20 CORE
    // ═══════════════════════════════════════════════════════

    /// @notice Transfer $AUTO tokens to another address
    /// @param to Recipient address
    /// @param amount Amount of tokens (18 decimals)
    function transfer(address to, uint256 amount) external returns (bool) {
        _transfer(msg.sender, to, amount);
        return true;
    }

    /// @notice Approve a spender to transfer tokens on your behalf
    /// @param spender The address authorized to spend
    /// @param amount Maximum amount the spender can transfer
    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    /// @notice Transfer tokens from one address to another (requires approval)
    /// @param from Source address
    /// @param to Destination address
    /// @param amount Amount of tokens (18 decimals)
    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        require(allowance[from][msg.sender] >= amount, "AutoToken: insufficient allowance");
        allowance[from][msg.sender] -= amount;
        _transfer(from, to, amount);
        return true;
    }

    /// @dev Internal transfer with balance and zero-address checks
    function _transfer(address from, address to, uint256 amount) internal {
        require(from != address(0) && to != address(0), "AutoToken: zero address");
        require(balanceOf[from] >= amount, "AutoToken: insufficient balance");
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        emit Transfer(from, to, amount);
    }

    /// @dev Internal mint — increases total supply and credits recipient
    function _mint(address to, uint256 amount) internal {
        totalSupply += amount;
        balanceOf[to] += amount;
        emit Transfer(address(0), to, amount);
    }

    // ═══════════════════════════════════════════════════════
    // ARCHITECT VESTING (V3 Section 6.3)
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Calculate vested amount available to the architect
     * @return The total amount vested (including already claimed)
     * @dev 1-year cliff, then linear vesting over remaining 3 years
     */
    function vestedAmount() public view returns (uint256) {
        if (block.timestamp < vestingStart + CLIFF_DURATION) {
            return 0; // Before cliff: nothing vested
        }
        
        uint256 elapsed = block.timestamp - vestingStart;
        if (elapsed >= VESTING_DURATION) {
            return architectAllocation; // Fully vested
        }
        
        // Linear vesting after cliff
        return (architectAllocation * elapsed) / VESTING_DURATION;
    }

    /**
     * @notice Architect claims vested tokens
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
    // VRGDA CONTINUOUS AUCTION (V3 Section 4.4)
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Get the current VRGDA price for purchasing 1 $AUTO token
     * @return price in USDC (6 decimals)
     * @dev Uses simplified VRGDA: price increases exponentially when ahead
     *      of schedule, decreases when behind
     *      
     *      P(t) = BASE_PRICE * e^(DECAY * (sold - target(t)))
     *      
     *      where target(t) = TARGET_PER_DAY * days_elapsed
     */
    function getVRGDAPrice() public view returns (uint256) {
        uint256 daysElapsed = (block.timestamp - vrgdaStartTime) / 1 days;
        if (daysElapsed == 0) daysElapsed = 1;
        
        uint256 targetSold = TARGET_PER_DAY * daysElapsed;
        
        if (vrgdaSold <= targetSold) {
            // Behind schedule — price at or below base
            uint256 deficit = targetSold - vrgdaSold;
            // Price decreases linearly down to 50% of base
            uint256 discount = (deficit * BASE_PRICE * 50) / (targetSold * 100);
            if (discount >= BASE_PRICE / 2) return BASE_PRICE / 2;
            return BASE_PRICE - discount;
        } else {
            // Ahead of schedule — price increases exponentially
            uint256 surplus = vrgdaSold - targetSold;
            // Simplified exponential: price doubles for every TARGET_PER_DAY ahead
            uint256 doublings = (surplus * 1e18) / TARGET_PER_DAY;
            // Cap at 256x base price
            if (doublings > 8e18) doublings = 8e18;
            uint256 multiplier = 1e18 + doublings; // Linear approximation for gas efficiency
            return (BASE_PRICE * multiplier) / 1e18;
        }
    }

    /**
     * @notice Purchase $AUTO tokens via the VRGDA auction
     * @param amount Number of tokens to purchase (18 decimals)
     * @param maxPrice Maximum USDC willing to pay per token (slippage protection)
     * @param usdc USDC token address for payment
     */
    function purchaseVRGDA(
        uint256 amount,
        uint256 maxPrice,
        address usdc
    ) external {
        require(!vrgdaHalted, "AutoToken: VRGDA halted (circuit breaker)");
        require(
            totalSupply + amount <= MAX_SUPPLY,
            "AutoToken: max supply reached"
        );
        
        uint256 pricePerToken = getVRGDAPrice();
        require(pricePerToken <= maxPrice, "AutoToken: price exceeds max");
        
        // Total cost in USDC
        uint256 totalCost = (amount * pricePerToken) / 1e18;
        require(totalCost > 0, "AutoToken: zero cost");
        
        // Genesis CapEx Split (V3.2 Section 6.3.4)
        // First 12 months: 20% to developer, 80% to treasury
        // After 12 months: 100% to treasury
        if (block.timestamp <= vrgdaStartTime + GENESIS_CAPEX_DURATION) {
            uint256 devShare = (totalCost * GENESIS_CAPEX_BPS) / 10000;
            uint256 treasuryShare = totalCost - devShare;
            
            IERC20Minimal(usdc).transferFrom(msg.sender, developerWallet, devShare);
            IERC20Minimal(usdc).transferFrom(msg.sender, owner, treasuryShare);
            
            genesisCapExPaid += devShare;
            vrgdaTreasuryTotal += treasuryShare;
            
            emit GenesisCapExSplit(devShare, treasuryShare);
        } else {
            // Post-sunset: 100% to treasury
            IERC20Minimal(usdc).transferFrom(msg.sender, owner, totalCost);
            vrgdaTreasuryTotal += totalCost;
        }
        
        // Mint $AUTO to buyer
        _mint(msg.sender, amount);
        vrgdaSold += amount;
        
        emit VRGDAPurchase(msg.sender, amount, pricePerToken);
    }

    // ═══════════════════════════════════════════════════════
    // DELEGATION FIREWALL (V3 Section 5.3)
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Register a wallet as a labor wallet (earns USDC bounties)
     * @param wallet The labor wallet address
     * @dev Labor wallets are cryptographically restricted from governance 
     *      delegation. Called by EscrowCore when an agent first claims a payload.
     */
    function registerLaborWallet(address wallet) external {
        require(
            msg.sender == escrowCore || msg.sender == owner,
            "AutoToken: not authorized"
        );
        isLaborWallet[wallet] = true;
        emit LaborWalletRegistered(wallet);
    }

    /**
     * @notice Check if a wallet can participate in governance delegation
     * @param wallet The wallet to check
     * @return True if the wallet can delegate (i.e., is NOT a labor wallet)
     */
    function canDelegate(address wallet) external view returns (bool) {
        return !isLaborWallet[wallet];
    }

    // ═══════════════════════════════════════════════════════
    // ADMIN & CIRCUIT BREAKER
    // ═══════════════════════════════════════════════════════

    /// @notice Set the EscrowCore contract address (for labor wallet registration)
    /// @param _escrowCore The EscrowCore contract address
    function setEscrowCore(address _escrowCore) external onlyOwner {
        escrowCore = _escrowCore;
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
    /// @param newOwner The new owner address
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "AutoToken: zero address");
        owner = newOwner;
    }
}

/**
 * @title IERC20Minimal
 * @notice Minimal interface for USDC transfers
 */
interface IERC20Minimal {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}
