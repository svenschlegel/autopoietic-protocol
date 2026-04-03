// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "test/BaseTest.sol";

/**
 * @title AutoTokenTest
 * @notice Tests for the $AUTO governance token
 * @dev Validates V3 Spec: §4.4 (VRGDA), §5.3 (delegation firewall), §6.3 (vesting)
 */
contract AutoTokenTest is BaseTest {

    // ═══════════════════════════════════════════════════════
    // INITIAL STATE
    // ═══════════════════════════════════════════════════════

    function test_initialSupply() public view {
        // 10% to vesting (held by contract) + 15% Genesis Geyser to treasury (V3.4)
        uint256 maxSupply = autoToken.MAX_SUPPLY();
        uint256 expected = (maxSupply * 25) / 100;
        assertEq(autoToken.totalSupply(), expected);
    }

    function test_architectAllocation() public view {
        uint256 expected = autoToken.MAX_SUPPLY() / 10;
        assertEq(autoToken.architectAllocation(), expected);
        // Held by the token contract itself (in vesting)
        assertEq(autoToken.balanceOf(address(autoToken)), expected);
    }

    function test_treasuryReceivesInitialAllocation() public view {
        // V3.4: Genesis Geyser expanded to 15%
        uint256 expected = (autoToken.MAX_SUPPLY() * 15) / 100;
        assertEq(autoToken.balanceOf(address(treasury)), expected);
    }

    // ═══════════════════════════════════════════════════════
    // VESTING (V3 Section 6.3: 1-year cliff + 4-year total)
    // ═══════════════════════════════════════════════════════

    function test_vesting_nothingBeforeCliff() public view {
        assertEq(autoToken.vestedAmount(), 0);
    }

    function test_vesting_nothingAt364Days() public {
        vm.warp(block.timestamp + 364 days);
        assertEq(autoToken.vestedAmount(), 0);
    }

    function test_vesting_startsAfterCliff() public {
        // Warp to exactly 1 year + 1 day
        vm.warp(block.timestamp + 366 days);
        uint256 vested = autoToken.vestedAmount();
        assertGt(vested, 0);
        
        // Should be approximately 25% (1 year of 4)
        uint256 expectedApprox = autoToken.architectAllocation() / 4;
        assertApproxEqRel(vested, expectedApprox, 0.02e18); // 2% tolerance
    }

    function test_vesting_halfwayAt2Years() public {
        vm.warp(block.timestamp + 730 days);
        uint256 vested = autoToken.vestedAmount();
        uint256 expected = autoToken.architectAllocation() / 2;
        assertApproxEqRel(vested, expected, 0.02e18);
    }

    function test_vesting_fullAt4Years() public {
        vm.warp(block.timestamp + 4 * 365 days);
        assertEq(autoToken.vestedAmount(), autoToken.architectAllocation());
    }

    function test_vesting_claimAfterCliff() public {
        vm.warp(block.timestamp + 2 * 365 days);
        
        uint256 vested = autoToken.vestedAmount();
        assertGt(vested, 0);
        
        vm.prank(architect);
        autoToken.claimVested();
        
        assertEq(autoToken.balanceOf(architect), vested);
        assertEq(autoToken.architectClaimed(), vested);
    }

    function test_vesting_claimBeforeCliff_reverts() public {
        vm.warp(block.timestamp + 100 days);
        
        vm.prank(architect);
        vm.expectRevert("AutoToken: nothing to claim");
        autoToken.claimVested();
    }

    function test_vesting_onlyArchitectCanClaim() public {
        vm.warp(block.timestamp + 2 * 365 days);
        
        vm.prank(alice);
        vm.expectRevert("AutoToken: not architect");
        autoToken.claimVested();
    }

    function test_vesting_incrementalClaims() public {
        // Claim at year 2
        vm.warp(block.timestamp + 2 * 365 days);
        vm.prank(architect);
        autoToken.claimVested();
        uint256 firstClaim = autoToken.architectClaimed();

        // Claim again at year 3
        vm.warp(block.timestamp + 365 days);
        vm.prank(architect);
        autoToken.claimVested();
        uint256 secondClaim = autoToken.architectClaimed();

        assertGt(secondClaim, firstClaim);
        assertEq(autoToken.balanceOf(architect), secondClaim);
    }

    // ═══════════════════════════════════════════════════════
    // VRGDA CONTINUOUS AUCTION (V3 Section 4.4)
    // ═══════════════════════════════════════════════════════

    function test_vrgda_initialPrice() public view {
        uint256 price = autoToken.getVRGDAPrice();
        // Should be at or near base price (1 USDC)
        assertGt(price, 0);
        assertLe(price, 2e6); // Not more than 2x base
    }

    function test_vrgda_priceIncreasesWhenAhead() public {
        // V3.4 Phase 1 target = 1M tokens/day. Buy 2M to be 1M ahead of schedule.
        uint256 amount = 2_000_000e18;

        vm.startPrank(alice);
        usdc.approve(address(autoToken), type(uint256).max);
        autoToken.purchaseVRGDA(amount, 10e6, address(usdc));
        vm.stopPrank();

        uint256 priceAfter = autoToken.getVRGDAPrice();
        // Price should be elevated above base
        assertGt(priceAfter, autoToken.BASE_PRICE());
    }

    function test_vrgda_priceDecreasesWhenBehind() public {
        // Fast-forward 30 days with no purchases
        vm.warp(block.timestamp + 30 days);
        
        uint256 price = autoToken.getVRGDAPrice();
        // Should be below base price (discounted)
        assertLt(price, autoToken.BASE_PRICE());
        // But not below 50% floor
        assertGe(price, autoToken.BASE_PRICE() / 2);
    }

    function test_vrgda_slippageProtection() public {
        vm.startPrank(alice);
        usdc.approve(address(autoToken), 1e6);

        // Set max price very low — should revert
        vm.expectRevert("AutoToken: average price exceeds maxPrice");
        autoToken.purchaseVRGDA(1e18, 1, address(usdc)); // maxPrice = 1 wei of USDC
        vm.stopPrank();
    }

    function test_vrgda_halted_reverts() public {
        vm.prank(deployer);
        autoToken.haltVRGDA();

        vm.startPrank(alice);
        usdc.approve(address(autoToken), 10e6);
        vm.expectRevert("AutoToken: VRGDA halted");
        autoToken.purchaseVRGDA(1e18, 10e6, address(usdc));
        vm.stopPrank();
    }

    function test_vrgda_resumeAfterHalt() public {
        vm.prank(deployer);
        autoToken.haltVRGDA();
        
        vm.prank(deployer);
        autoToken.resumeVRGDA();

        // Should work now
        vm.startPrank(alice);
        usdc.approve(address(autoToken), 10e6);
        autoToken.purchaseVRGDA(1e18, 10e6, address(usdc));
        vm.stopPrank();
        
        // V3.4: 1% of minted tokens are burned (MINT_BURN_BPS = 100)
        assertEq(autoToken.balanceOf(alice), 1e18 * 99 / 100);
    }

    function test_vrgda_maxSupply() public {
        uint256 remaining = autoToken.MAX_SUPPLY() - autoToken.totalSupply();
        
        vm.startPrank(alice);
        usdc.approve(address(autoToken), type(uint256).max);
        
        vm.expectRevert("AutoToken: max supply reached");
        autoToken.purchaseVRGDA(remaining + 1, type(uint256).max, address(usdc));
        vm.stopPrank();
    }

    // ═══════════════════════════════════════════════════════
    // DELEGATION FIREWALL (V3 Section 5.3)
    // ═══════════════════════════════════════════════════════

    function test_delegationFirewall_laborWalletRegistered() public {
        vm.prank(deployer);
        autoToken.registerLaborWallet(bob);
        
        assertTrue(autoToken.isLaborWallet(bob));
        assertFalse(autoToken.canDelegate(bob));
    }

    function test_delegationFirewall_nonLaborCanDelegate() public view {
        // Alice is not a labor wallet
        assertFalse(autoToken.isLaborWallet(alice));
        assertTrue(autoToken.canDelegate(alice));
    }

    function test_delegationFirewall_onlyAuthorized() public {
        vm.prank(alice);
        vm.expectRevert("AutoToken: not authorized");
        autoToken.registerLaborWallet(bob);
    }

    function test_delegationFirewall_escrowCanRegister() public {
        // EscrowCore should be able to register labor wallets
        vm.prank(address(escrow));
        autoToken.registerLaborWallet(carol);
        assertTrue(autoToken.isLaborWallet(carol));
    }

    // ═══════════════════════════════════════════════════════
    // ERC-20 BASICS
    // ═══════════════════════════════════════════════════════

    function test_transfer() public {
        // V3.4: buying 10e18 tokens burns 1%, alice receives 9.9e18
        vm.startPrank(alice);
        usdc.approve(address(autoToken), 100e6);
        autoToken.purchaseVRGDA(10e18, 100e6, address(usdc));
        uint256 aliceBalance = autoToken.balanceOf(alice); // 9.9e18

        autoToken.transfer(bob, 5e18);
        vm.stopPrank();

        assertEq(autoToken.balanceOf(bob), 5e18);
        assertEq(autoToken.balanceOf(alice), aliceBalance - 5e18);
    }

    function test_transferFrom() public {
        // Alice buys tokens (receives 99% due to 1% mint burn)
        vm.startPrank(alice);
        usdc.approve(address(autoToken), 100e6);
        autoToken.purchaseVRGDA(10e18, 100e6, address(usdc));
        autoToken.approve(bob, 5e18);
        vm.stopPrank();

        // Bob transfers from Alice
        vm.prank(bob);
        autoToken.transferFrom(alice, carol, 5e18);

        assertEq(autoToken.balanceOf(carol), 5e18);
    }

    function test_transfer_insufficientBalance() public {
        vm.prank(alice);
        vm.expectRevert("AutoToken: insufficient balance");
        autoToken.transfer(bob, 1e18);
    }

    // ═══════════════════════════════════════════════════════
    // GAS BENCHMARKS
    // ═══════════════════════════════════════════════════════

    function test_gas_purchaseVRGDA() public {
        vm.startPrank(alice);
        usdc.approve(address(autoToken), 100e6);
        
        uint256 g = gasleft();
        autoToken.purchaseVRGDA(1e18, 100e6, address(usdc));
        emit log_named_uint("Gas: purchaseVRGDA", g - gasleft());
        vm.stopPrank();
    }

    function test_gas_claimVested() public {
        vm.warp(block.timestamp + 2 * 365 days);
        
        vm.prank(architect);
        uint256 g = gasleft();
        autoToken.claimVested();
        emit log_named_uint("Gas: claimVested", g - gasleft());
    }

    function test_gas_transfer() public {
        vm.startPrank(alice);
        usdc.approve(address(autoToken), 100e6);
        autoToken.purchaseVRGDA(10e18, 100e6, address(usdc));
        
        uint256 g = gasleft();
        autoToken.transfer(bob, 5e18);
        emit log_named_uint("Gas: transfer", g - gasleft());
        vm.stopPrank();
    }
}
