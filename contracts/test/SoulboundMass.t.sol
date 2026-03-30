// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "test/BaseTest.sol";

/**
 * @title SoulboundMassTest
 * @notice Tests for the non-transferable reputation token
 * @dev Validates V3 Spec: §4.2, §5.2, Appendix A.3
 */
contract SoulboundMassTest is BaseTest {

    // ═══════════════════════════════════════════════════════
    // MASS ACCRUAL
    // ═══════════════════════════════════════════════════════

    function test_accrueMass_authorizedMinter() public {
        // EscrowCore is an authorized minter
        vm.prank(address(escrow));
        mass.accrueMass(bob, 100e18);
        
        assertEq(mass.mass(bob), 100e18);
        assertEq(mass.totalMass(), mass.mass(bob) + 360e18); // 60e18 * 6 jurors bootstrapped
        assertEq(mass.payloadsSolved(bob), 1);
    }

    function test_accrueMass_resetsFailureCounter() public {
        // Record some failures
        vm.startPrank(address(escrow));
        mass.recordFailure(bob);
        mass.recordFailure(bob);
        assertEq(mass.consecutiveFailures(bob), 2);

        // Successful accrual resets to 0
        mass.accrueMass(bob, 10e18);
        assertEq(mass.consecutiveFailures(bob), 0);
        vm.stopPrank();
    }

    function test_accrueMass_revertsUnauthorized() public {
        vm.prank(alice);
        vm.expectRevert("SoulboundMass: not authorized");
        mass.accrueMass(bob, 100e18);
    }

    function test_accrueMass_revertsForQuarantinedAgent() public {
        // Quarantine bob
        vm.startPrank(address(escrow));
        for (uint8 i = 0; i < 5; i++) {
            mass.recordFailure(bob);
        }
        assertTrue(mass.isQuarantined(bob));

        // Cannot accrue mass while quarantined
        vm.expectRevert("SoulboundMass: agent quarantined");
        mass.accrueMass(bob, 10e18);
        vm.stopPrank();
    }

    function test_accrueMass_revertsZeroAmount() public {
        vm.prank(address(escrow));
        vm.expectRevert("SoulboundMass: zero amount");
        mass.accrueMass(bob, 0);
    }

    // ═══════════════════════════════════════════════════════
    // QUARANTINE (V3 Appendix A.3: k=5)
    // ═══════════════════════════════════════════════════════

    function test_quarantine_afterFiveFailures() public {
        vm.startPrank(address(escrow));
        
        // 4 failures: not yet quarantined
        for (uint8 i = 0; i < 4; i++) {
            mass.recordFailure(mallory);
            assertFalse(mass.isQuarantined(mallory));
        }

        // 5th failure: quarantined
        mass.recordFailure(mallory);
        assertTrue(mass.isQuarantined(mallory));
        assertEq(mass.consecutiveFailures(mallory), 5);
        vm.stopPrank();
    }

    function test_quarantine_resetBySuccess() public {
        vm.startPrank(address(escrow));
        
        // 4 failures
        for (uint8 i = 0; i < 4; i++) {
            mass.recordFailure(bob);
        }
        assertEq(mass.consecutiveFailures(bob), 4);

        // Success resets counter
        mass.accrueMass(bob, 1e18);
        assertEq(mass.consecutiveFailures(bob), 0);
        
        // Now 4 more failures still don't quarantine
        for (uint8 i = 0; i < 4; i++) {
            mass.recordFailure(bob);
        }
        assertFalse(mass.isQuarantined(bob));
        vm.stopPrank();
    }

    function test_reinstate_afterQuarantine() public {
        // Quarantine mallory
        vm.startPrank(address(escrow));
        for (uint8 i = 0; i < 5; i++) {
            mass.recordFailure(mallory);
        }
        vm.stopPrank();
        assertTrue(mass.isQuarantined(mallory));

        // Owner reinstates
        vm.prank(deployer);
        mass.reinstate(mallory);
        
        assertFalse(mass.isQuarantined(mallory));
        assertEq(mass.consecutiveFailures(mallory), 0);
    }

    function test_reinstate_revertsNotQuarantined() public {
        vm.prank(deployer);
        vm.expectRevert("SoulboundMass: not quarantined");
        mass.reinstate(bob);
    }

    // ═══════════════════════════════════════════════════════
    // SOULBOUND (NON-TRANSFERABLE)
    // ═══════════════════════════════════════════════════════

    function test_transfer_alwaysReverts() public {
        vm.prank(bob);
        vm.expectRevert("SoulboundMass: non-transferable");
        mass.transfer(alice, 1);
    }

    function test_approve_alwaysReverts() public {
        vm.prank(bob);
        vm.expectRevert("SoulboundMass: non-transferable");
        mass.approve(alice, 1);
    }

    // ═══════════════════════════════════════════════════════
    // THRESHOLD CHECKS
    // ═══════════════════════════════════════════════════════

    function test_juryThreshold() public view {
        // Dave has 60e18 Mass (bootstrapped) — above 50e18 threshold
        assertTrue(mass.canServeAsJuror(dave));
        
        // Bob has 0 Mass — below threshold
        assertFalse(mass.canServeAsJuror(bob));
    }

    function test_bootstrapThreshold() public {
        // Dave has 60e18 — below 100e18 bootstrap threshold
        assertFalse(mass.canRegisterAsBootstrap(dave));
        
        // Give dave more mass
        vm.prank(address(escrow));
        mass.accrueMass(dave, 50e18);
        
        // Now 110e18 — above threshold
        assertTrue(mass.canRegisterAsBootstrap(dave));
    }

    function test_quarantinedCantServeAsJuror() public {
        // Dave has enough mass but gets quarantined
        vm.startPrank(address(escrow));
        for (uint8 i = 0; i < 5; i++) {
            mass.recordFailure(dave);
        }
        vm.stopPrank();
        
        assertFalse(mass.canServeAsJuror(dave));
    }

    // ═══════════════════════════════════════════════════════
    // ACCESS CONTROL
    // ═══════════════════════════════════════════════════════

    function test_authorizeMinter_onlyOwner() public {
        vm.prank(alice);
        vm.expectRevert("SoulboundMass: not owner");
        mass.authorizeMinter(alice);
    }

    function test_transferOwnership() public {
        vm.prank(deployer);
        mass.transferOwnership(alice);
        assertEq(mass.owner(), alice);
    }

    // ═══════════════════════════════════════════════════════
    // GAS BENCHMARKS
    // ═══════════════════════════════════════════════════════

    function test_gas_accrueMass() public {
        vm.prank(address(escrow));
        uint256 gasBefore = gasleft();
        mass.accrueMass(bob, 100e18);
        uint256 gasUsed = gasBefore - gasleft();
        emit log_named_uint("Gas: accrueMass", gasUsed);
    }

    function test_gas_recordFailure() public {
        vm.prank(address(escrow));
        uint256 gasBefore = gasleft();
        mass.recordFailure(bob);
        uint256 gasUsed = gasBefore - gasleft();
        emit log_named_uint("Gas: recordFailure", gasUsed);
    }
}
