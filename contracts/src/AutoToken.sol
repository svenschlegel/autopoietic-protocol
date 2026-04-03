// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title AutoToken
 * @notice The $AUTO governance token for the Autopoietic Protocol (V3.4)
 * @dev Implements:
 * - Standard ERC-20 for Gravitational Staking governance
 * - Total supply: 1,000,000,000 (1B) tokens
 * - Architect vesting with 1-year cliff + 3-year linear
 * - Two-Phase VRGDA Emission: 90-day Price Discovery (1M/day) -> Cooling (100k/day)
 * - $2M Genesis FDV: Base price of $0.002 USDC
 * - 1% VRGDA Mint Burn: deflationary on every purchase
 * - 50% Milestone Burn: unvested architect tokens burned by Treasury
 * - 20/80 Genesis Development Cost Recovery: Year 1 VRGDA split
 * - Delegation firewall: labor wallets cannot delegate
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

    // ── VRGDA State (V3.4 Price Discovery) ───────────────────

    /// @notice Phase 1: 1M tokens/day for 90 days
    uint256 public constant DISCOVERY_RATE = 1_000_000e18; 
    /// @notice Phase 2: 100k tokens/day thereafter (Thermodynamic Cooling)
    uint256 public constant COOLING_RATE = 100_000e18; 
    /// @notice Duration of the Price Discovery phase
    uint256 public constant PHASE_SHIFT_DAYS = 90;
    
    uint256 public vrgdaStartTime;
    uint256 public vrgdaSold;
    
    /// @notice Genesis Base Price in USDC (6 decimals): $0.002 ($2M FDV)
    uint256 public constant BASE_PRICE = 0.002e6; 

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
    address public emergencyAdmin; // Multisig for instant halt/resume
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
        
        // Mint 15% Genesis Geyser: 150,000,000 $AUTO (V3.4: expanded from 5%)
        _mint(_treasury, MAX_SUPPLY * 15 / 100);
    }

    // ═══════════════════════════════════════════════════════
    // ERC-20 CORE
    // ═══════════════════════════════════════════════════════

    function transfer(address to, uint256 amount) external returns (bool) {
        _transfer(msg.sender, to, amount);
        return true;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

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

    function vestedAmount() public view returns (uint256) {
        if (block.timestamp < vestingStart + CLIFF_DURATION) {
            return 0;
        }
        
        uint256 effectiveAllocation = architectAllocation - milestoneBurnAmount;
        uint256 elapsed = block.timestamp - vestingStart;
        if (elapsed >= VESTING_DURATION) {
            return effectiveAllocation;
        }
        
        return (effectiveAllocation * elapsed) / VESTING_DURATION;
    }

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
    // VRGDA PRICING ENGINE & CONTINUOUS AUCTION
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Calculates the total expected supply on a given day using the two-phase integral
     */
    function _getTargetSold(uint256 daysElapsed) internal pure returns (uint256) {
        if (daysElapsed == 0) daysElapsed = 1;
        
        if (daysElapsed <= PHASE_SHIFT_DAYS) {
            return daysElapsed * DISCOVERY_RATE;
        } else {
            uint256 discoveryTotal = PHASE_SHIFT_DAYS * DISCOVERY_RATE;
            uint256 coolingDays = daysElapsed - PHASE_SHIFT_DAYS;
            return discoveryTotal + (coolingDays * COOLING_RATE);
        }
    }

    /**
     * @notice Determines the active daily rate for penalty calculation
     */
    function _getCurrentRate(uint256 daysElapsed) internal pure returns (uint256) {
        if (daysElapsed <= PHASE_SHIFT_DAYS) return DISCOVERY_RATE;
        return COOLING_RATE;
    }

    /// @dev Internal pure function to calculate the exact spot price
    function _priceAt(uint256 sold, uint256 targetSold, uint256 dailyRate) internal pure returns (uint256) {
        if (sold <= targetSold) {
            uint256 deficit = targetSold - sold;
            uint256 discount = (deficit * BASE_PRICE * 50) / (targetSold * 100);
            if (discount >= BASE_PRICE / 2) return BASE_PRICE / 2;
            return BASE_PRICE - discount;
        } else {
            uint256 surplus = sold - targetSold;
            // The penalty scales based on the current active daily rate
            uint256 doublings = (surplus * 1e18) / dailyRate;
            if (doublings > 8e18) doublings = 8e18; // Cap at 9x
            uint256 multiplier = 1e18 + doublings;
            return (BASE_PRICE * multiplier) / 1e18;
        }
    }

    /// @notice Get the current spot price for 1 $AUTO token (UI Helper)
    function getVRGDAPrice() public view returns (uint256) {
        uint256 daysElapsed = (block.timestamp - vrgdaStartTime) / 1 days;
        if (daysElapsed == 0) daysElapsed = 1;
        
        uint256 targetSold = _getTargetSold(daysElapsed);
        uint256 currentRate = _getCurrentRate(daysElapsed);
        
        return _priceAt(vrgdaSold, targetSold, currentRate);
    }

    /// @notice Calculates the exact continuous cost (area under the curve) for a batch purchase
    function getVRGDACost(uint256 amount) public view returns (uint256) {
        if (amount == 0) return 0;
        
        uint256 daysElapsed = (block.timestamp - vrgdaStartTime) / 1 days;
        if (daysElapsed == 0) daysElapsed = 1;
        
        uint256 targetSold = _getTargetSold(daysElapsed);
        uint256 currentRate = _getCurrentRate(daysElapsed);

        uint256 startSold = vrgdaSold;
        uint256 endSold = startSold + amount;

        // Trapezoidal integration of the piecewise linear curve
        if (endSold <= targetSold) {
            uint256 pStart = _priceAt(startSold, targetSold, currentRate);
            uint256 pEnd = _priceAt(endSold, targetSold, currentRate);
            return (amount * (pStart + pEnd)) / (2 * 1e18);
        } else if (startSold >= targetSold) {
            uint256 pStart = _priceAt(startSold, targetSold, currentRate);
            uint256 pEnd = _priceAt(endSold, targetSold, currentRate);
            return (amount * (pStart + pEnd)) / (2 * 1e18);
        } else {
            uint256 amountDeficit = targetSold - startSold;
            uint256 amountSurplus = endSold - targetSold;

            uint256 pStart = _priceAt(startSold, targetSold, currentRate);
            uint256 pTarget = BASE_PRICE; // Equilibrium
            uint256 pEnd = _priceAt(endSold, targetSold, currentRate);

            uint256 costDeficit = (amountDeficit * (pStart + pTarget)) / (2 * 1e18);
            uint256 costSurplus = (amountSurplus * (pTarget + pEnd)) / (2 * 1e18);

            return costDeficit + costSurplus;
        }
    }

    function purchaseVRGDA(
        uint256 amount,
        uint256 maxPrice,
        address usdc
    ) external {
        require(!vrgdaHalted, "AutoToken: VRGDA halted");
        require(amount > 0, "AutoToken: zero amount");
        require(
            totalSupply + amount <= MAX_SUPPLY,
            "AutoToken: max supply reached"
        );

        uint256 totalCost = getVRGDACost(amount);
        require(totalCost > 0, "AutoToken: zero cost");
        
        uint256 avgPrice = (totalCost * 1e18) / amount;
        require(avgPrice <= maxPrice, "AutoToken: average price exceeds maxPrice");
        
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
        
        uint256 burnAmount = (amount * MINT_BURN_BPS) / 10000;
        uint256 buyerAmount = amount - burnAmount;
        
        _mint(msg.sender, buyerAmount);
        
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

    function executeMilestoneBurn() external {
        require(msg.sender == treasury, "AutoToken: only treasury can trigger");
        require(!milestoneBurnExecuted, "AutoToken: milestone already executed");
        
        uint256 unvested = architectAllocation - vestedAmount();
        require(unvested > 0, "AutoToken: no unvested tokens");
        
        uint256 burnAmount = (unvested * MILESTONE_BURN_BPS) / 10000;
        
        milestoneBurnExecuted = true;
        milestoneBurnAmount = burnAmount;
        
        _burn(address(this), burnAmount);
        
        emit MilestoneBurn(burnAmount, architectAllocation - architectClaimed - burnAmount);
    }

    // ═══════════════════════════════════════════════════════
    // DELEGATION FIREWALL (Section 5.3)
    // ═══════════════════════════════════════════════════════

    function registerLaborWallet(address wallet) external {
        require(
            msg.sender == escrowCore || msg.sender == owner,
            "AutoToken: not authorized"
        );
        isLaborWallet[wallet] = true;
        emit LaborWalletRegistered(wallet);
    }

    function canDelegate(address wallet) external view returns (bool) {
        return !isLaborWallet[wallet];
    }

    // ═══════════════════════════════════════════════════════
    // ADMIN & CIRCUIT BREAKER
    // ═══════════════════════════════════════════════════════

    function setEscrowCore(address _escrowCore) external onlyOwner {
        escrowCore = _escrowCore;
    }

    function setTreasury(address _treasury) external onlyOwner {
        require(_treasury != address(0), "AutoToken: zero address");
        treasury = _treasury;
    }

    function haltVRGDA() external {
        require(msg.sender == owner || msg.sender == emergencyAdmin, "AutoToken: not authorized");
        vrgdaHalted = true;
        emit VRGDAHalted();
    }

    function resumeVRGDA() external {
        require(msg.sender == owner || msg.sender == emergencyAdmin, "AutoToken: not authorized");
        vrgdaHalted = false;
        emit VRGDAResumed();
    }

    function setEmergencyAdmin(address _emergencyAdmin) external onlyOwner {
        emergencyAdmin = _emergencyAdmin;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "AutoToken: zero address");
        owner = newOwner;
    }

    // ═══════════════════════════════════════════════════════
    // VIEW FUNCTIONS
    // ═══════════════════════════════════════════════════════

    function circulatingSupply() external view returns (uint256) {
        uint256 vestingLocked = architectAllocation - architectClaimed - milestoneBurnAmount;
        return totalSupply - vestingLocked;
    }

    function effectiveMaxSupply() external view returns (uint256) {
        return MAX_SUPPLY - totalBurned;
    }
}

interface IERC20Minimal {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}
