// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "test/BaseTest.sol";
import "src/Timelock.sol";

/**
 * @title TimelockTest
 * @notice Tests for the 48-hour admin timelock
 * @dev Validates queue, execute, cancel, delay enforcement, expiry, and admin transfer
 */
contract TimelockTest is BaseTest {

    Timelock public timelock;
    address public multisig = makeAddr("multisig");

    function setUp() public override {
        super.setUp();

        // Deploy timelock with multisig as admin
        timelock = new Timelock(multisig);

        // Transfer EscrowCore ownership to timelock
        vm.prank(deployer);
        escrow.transferOwnership(address(timelock));

        // Set multisig as emergencyAdmin on escrow (direct, no timelock needed)
        // Queue this through the timelock since owner is now timelock
        _queueAndExecute(
            address(escrow),
            abi.encodeWithSignature("setEmergencyAdmin(address)", multisig)
        );
    }

    // ═══════════════════════════════════════════════════════
    // QUEUE & EXECUTE
    // ═══════════════════════════════════════════════════════

    function test_queueAndExecute_updatePayoutRatios() public {
        bytes memory data = abi.encodeWithSignature(
            "updatePayoutRatios(uint16,uint16,uint16)",
            uint16(7000), uint16(1500), uint16(1500)
        );
        uint256 eta = block.timestamp + 48 hours;

        // Queue
        vm.prank(multisig);
        bytes32 txHash = timelock.queueTransaction(address(escrow), 0, data, eta);
        assertTrue(timelock.queuedTransactions(txHash));

        // Can't execute before eta
        vm.prank(multisig);
        vm.expectRevert("Timelock: too early");
        timelock.executeTransaction(address(escrow), 0, data, eta);

        // Warp to eta
        vm.warp(eta);

        // Execute
        vm.prank(multisig);
        timelock.executeTransaction(address(escrow), 0, data, eta);

        // Verify the change took effect
        (uint16 cap, uint16 myc, uint16 con) = escrow.payoutRatios();
        assertEq(cap, 7000);
        assertEq(myc, 1500);
        assertEq(con, 1500);

        // Transaction no longer queued
        assertFalse(timelock.queuedTransactions(txHash));
    }

    function test_queue_revertsDelayTooShort() public {
        bytes memory data = abi.encodeWithSignature("pause()");
        uint256 eta = block.timestamp + 1 hours; // Too short

        vm.prank(multisig);
        vm.expectRevert("Timelock: delay too short");
        timelock.queueTransaction(address(escrow), 0, data, eta);
    }

    function test_queue_revertsDelayTooLong() public {
        bytes memory data = abi.encodeWithSignature("pause()");
        uint256 eta = block.timestamp + 31 days; // Too long

        vm.prank(multisig);
        vm.expectRevert("Timelock: delay too long");
        timelock.queueTransaction(address(escrow), 0, data, eta);
    }

    function test_execute_revertsIfNotQueued() public {
        bytes memory data = abi.encodeWithSignature("pause()");
        uint256 eta = block.timestamp + 48 hours;

        vm.prank(multisig);
        vm.expectRevert("Timelock: not queued");
        timelock.executeTransaction(address(escrow), 0, data, eta);
    }

    function test_execute_revertsIfExpired() public {
        bytes memory data = abi.encodeWithSignature(
            "updatePayoutRatios(uint16,uint16,uint16)",
            uint16(7000), uint16(1500), uint16(1500)
        );
        uint256 eta = block.timestamp + 48 hours;

        vm.prank(multisig);
        timelock.queueTransaction(address(escrow), 0, data, eta);

        // Warp past eta + grace period (14 days)
        vm.warp(eta + 14 days + 1);

        vm.prank(multisig);
        vm.expectRevert("Timelock: expired");
        timelock.executeTransaction(address(escrow), 0, data, eta);
    }

    // ═══════════════════════════════════════════════════════
    // CANCEL
    // ═══════════════════════════════════════════════════════

    function test_cancel() public {
        bytes memory data = abi.encodeWithSignature(
            "updatePayoutRatios(uint16,uint16,uint16)",
            uint16(7000), uint16(1500), uint16(1500)
        );
        uint256 eta = block.timestamp + 48 hours;

        vm.prank(multisig);
        bytes32 txHash = timelock.queueTransaction(address(escrow), 0, data, eta);
        assertTrue(timelock.queuedTransactions(txHash));

        vm.prank(multisig);
        timelock.cancelTransaction(address(escrow), 0, data, eta);
        assertFalse(timelock.queuedTransactions(txHash));
    }

    function test_cancel_revertsIfNotQueued() public {
        bytes memory data = abi.encodeWithSignature("pause()");
        uint256 eta = block.timestamp + 48 hours;

        vm.prank(multisig);
        vm.expectRevert("Timelock: not queued");
        timelock.cancelTransaction(address(escrow), 0, data, eta);
    }

    // ═══════════════════════════════════════════════════════
    // ACCESS CONTROL
    // ═══════════════════════════════════════════════════════

    function test_queue_revertsNonAdmin() public {
        bytes memory data = abi.encodeWithSignature("pause()");
        uint256 eta = block.timestamp + 48 hours;

        vm.prank(alice);
        vm.expectRevert("Timelock: not admin");
        timelock.queueTransaction(address(escrow), 0, data, eta);
    }

    function test_execute_revertsNonAdmin() public {
        bytes memory data = abi.encodeWithSignature("pause()");
        uint256 eta = block.timestamp + 48 hours;

        vm.prank(multisig);
        timelock.queueTransaction(address(escrow), 0, data, eta);
        vm.warp(eta);

        vm.prank(alice);
        vm.expectRevert("Timelock: not admin");
        timelock.executeTransaction(address(escrow), 0, data, eta);
    }

    // ═══════════════════════════════════════════════════════
    // EMERGENCY ADMIN (Bypass Timelock)
    // ═══════════════════════════════════════════════════════

    function test_emergencyAdmin_canPauseInstantly() public {
        // Multisig is emergencyAdmin — can pause without timelock
        vm.prank(multisig);
        escrow.pause();
        assertTrue(escrow.paused());

        vm.prank(multisig);
        escrow.unpause();
        assertFalse(escrow.paused());
    }

    function test_emergencyAdmin_randomCannotPause() public {
        vm.prank(alice);
        vm.expectRevert("EscrowCore: not authorized");
        escrow.pause();
    }

    // ═══════════════════════════════════════════════════════
    // ADMIN TRANSFER (Two-Step)
    // ═══════════════════════════════════════════════════════

    function test_adminTransfer_twoStep() public {
        address newMultisig = makeAddr("newMultisig");

        vm.prank(multisig);
        timelock.setPendingAdmin(newMultisig);
        assertEq(timelock.pendingAdmin(), newMultisig);

        // Old admin still active
        assertEq(timelock.admin(), multisig);

        // New admin accepts
        vm.prank(newMultisig);
        timelock.acceptAdmin();
        assertEq(timelock.admin(), newMultisig);
        assertEq(timelock.pendingAdmin(), address(0));
    }

    function test_acceptAdmin_revertsIfNotPending() public {
        vm.prank(alice);
        vm.expectRevert("Timelock: not pending admin");
        timelock.acceptAdmin();
    }

    // ═══════════════════════════════════════════════════════
    // HELPER
    // ═══════════════════════════════════════════════════════

    function _queueAndExecute(address target, bytes memory data) internal {
        uint256 eta = block.timestamp + 48 hours;
        vm.prank(multisig);
        timelock.queueTransaction(target, 0, data, eta);
        vm.warp(eta);
        vm.prank(multisig);
        timelock.executeTransaction(target, 0, data, eta);
    }
}
