// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title Timelock
 * @notice 48-hour delay on non-emergency admin actions for the Autopoietic Protocol
 * @dev Architecture:
 *   - admin: the multisig (Safe) that can queue/execute/cancel transactions
 *   - All queued transactions must wait MINIMUM_DELAY before execution
 *   - Transactions expire after GRACE_PERIOD to prevent stale execution
 *   - Emergency functions (pause, halt) bypass the timelock via emergencyAdmin
 *     on the individual contracts — they are never routed through here
 */
contract Timelock {

    // ── Constants ───────────────────────────────────────────

    uint256 public constant MINIMUM_DELAY = 48 hours;
    uint256 public constant MAXIMUM_DELAY = 30 days;
    uint256 public constant GRACE_PERIOD = 14 days;

    // ── State ───────────────────────────────────────────────

    address public admin;
    address public pendingAdmin;

    mapping(bytes32 => bool) public queuedTransactions;

    // ── Events ──────────────────────────────────────────────

    event TransactionQueued(
        bytes32 indexed txHash,
        address indexed target,
        uint256 value,
        bytes data,
        uint256 eta
    );
    event TransactionExecuted(
        bytes32 indexed txHash,
        address indexed target,
        uint256 value,
        bytes data,
        uint256 eta
    );
    event TransactionCancelled(bytes32 indexed txHash);
    event NewAdmin(address indexed newAdmin);
    event NewPendingAdmin(address indexed pendingAdmin);

    // ── Modifiers ───────────────────────────────────────────

    modifier onlyAdmin() {
        require(msg.sender == admin, "Timelock: not admin");
        _;
    }

    // ── Constructor ─────────────────────────────────────────

    constructor(address _admin) {
        require(_admin != address(0), "Timelock: zero admin");
        admin = _admin;
    }

    // ═══════════════════════════════════════════════════════
    // TRANSACTION LIFECYCLE
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Queue a transaction for future execution
     * @param target Contract to call
     * @param value ETH to send (typically 0 for USDC protocol)
     * @param data Encoded function call (abi.encodeWithSignature)
     * @param eta Earliest timestamp when this can execute (must be >= now + MINIMUM_DELAY)
     */
    function queueTransaction(
        address target,
        uint256 value,
        bytes calldata data,
        uint256 eta
    ) external onlyAdmin returns (bytes32) {
        require(eta >= block.timestamp + MINIMUM_DELAY, "Timelock: delay too short");
        require(eta <= block.timestamp + MAXIMUM_DELAY, "Timelock: delay too long");

        bytes32 txHash = keccak256(abi.encode(target, value, data, eta));
        queuedTransactions[txHash] = true;

        emit TransactionQueued(txHash, target, value, data, eta);
        return txHash;
    }

    /**
     * @notice Execute a previously queued transaction after its delay
     */
    function executeTransaction(
        address target,
        uint256 value,
        bytes calldata data,
        uint256 eta
    ) external onlyAdmin returns (bytes memory) {
        bytes32 txHash = keccak256(abi.encode(target, value, data, eta));

        require(queuedTransactions[txHash], "Timelock: not queued");
        require(block.timestamp >= eta, "Timelock: too early");
        require(block.timestamp <= eta + GRACE_PERIOD, "Timelock: expired");

        queuedTransactions[txHash] = false;

        (bool success, bytes memory returnData) = target.call{value: value}(data);
        require(success, "Timelock: execution reverted");

        emit TransactionExecuted(txHash, target, value, data, eta);
        return returnData;
    }

    /**
     * @notice Cancel a queued transaction
     */
    function cancelTransaction(
        address target,
        uint256 value,
        bytes calldata data,
        uint256 eta
    ) external onlyAdmin {
        bytes32 txHash = keccak256(abi.encode(target, value, data, eta));
        require(queuedTransactions[txHash], "Timelock: not queued");

        queuedTransactions[txHash] = false;
        emit TransactionCancelled(txHash);
    }

    // ═══════════════════════════════════════════════════════
    // ADMIN TRANSFER (Two-Step)
    // ═══════════════════════════════════════════════════════

    /**
     * @notice Propose a new admin (must be accepted by the new admin)
     * @dev This itself should be called via the timelock for non-genesis transfers,
     *      but is direct during initial setup
     */
    function setPendingAdmin(address _pendingAdmin) external onlyAdmin {
        pendingAdmin = _pendingAdmin;
        emit NewPendingAdmin(_pendingAdmin);
    }

    function acceptAdmin() external {
        require(msg.sender == pendingAdmin, "Timelock: not pending admin");
        admin = pendingAdmin;
        pendingAdmin = address(0);
        emit NewAdmin(admin);
    }

    // Allow receiving ETH (needed for value transfers, unlikely but safe)
    receive() external payable {}
}
