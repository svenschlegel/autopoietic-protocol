// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "test/BaseTest.sol";

/**
 * @title TreasuryTest
 * @notice Tests for the Protocol-Owned Treasury
 * @dev Validates V3 Spec: §4.4, §6.3
 */
contract TreasuryTest is BaseTest {

    // ═══════════════════════════════════════════════════════
    // INITIAL STATE
    // ═══════════════════════════════════════════════════════

    function test_initialBalance() public view {
        uint256 bal = usdc.balanceOf(address(treasury));
        assertEq(bal, MIN_RESERVE * 2); // setUp funds 2x minimum
    }

    function test_initialCategories() public view {
        assertTrue(treasury.approvedCategories(keccak256("Infrastructure")));
        assertTrue(treasury.approvedCategories(keccak256("DataCommons")));
        assertTrue(treasury.approvedCategories(keccak256("Research")));
        assertFalse(treasury.approvedCategories(keccak256("Marketing")));
    }

    // ═══════════════════════════════════════════════════════
    // DEPOSITS
    // ═══════════════════════════════════════════════════════

    function test_deposit() public {
        uint256 amount = 50_000e6;
        uint256 balBefore = usdc.balanceOf(address(treasury));

        vm.startPrank(alice);
        usdc.approve(address(treasury), amount);
        treasury.deposit(amount);
        vm.stopPrank();

        assertEq(usdc.balanceOf(address(treasury)), balBefore + amount);
        assertEq(treasury.totalReceived(), amount);
    }

    // ═══════════════════════════════════════════════════════
    // DEPLOYMENTS
    // ═══════════════════════════════════════════════════════

    function test_deploy_approvedCategory() public {
        uint256 amount = 10_000e6;
        uint256 bobBefore = usdc.balanceOf(bob);

        vm.prank(deployer);
        treasury.deploy(bob, amount, keccak256("Infrastructure"));

        assertEq(usdc.balanceOf(bob), bobBefore + amount);
        assertEq(treasury.totalDeployed(), amount);
    }

    function test_deploy_revertsUnapprovedCategory() public {
        vm.prank(deployer);
        vm.expectRevert("Treasury: unapproved category");
        treasury.deploy(bob, 1000e6, keccak256("Marketing"));
    }

    function test_deploy_revertsBreachMinimumReserve() public {
        uint256 balance = usdc.balanceOf(address(treasury));
        // Try to deploy so much that we'd go below minimum reserve
        uint256 tooMuch = balance - MIN_RESERVE + 1;
        
        vm.prank(deployer);
        vm.expectRevert("Treasury: would breach minimum reserve");
        treasury.deploy(bob, tooMuch, keccak256("Infrastructure"));
    }

    function test_deploy_exactlyToMinimum() public {
        uint256 balance = usdc.balanceOf(address(treasury));
        uint256 maxDeploy = balance - MIN_RESERVE;
        
        vm.prank(deployer);
        treasury.deploy(bob, maxDeploy, keccak256("Infrastructure"));
        
        assertEq(usdc.balanceOf(address(treasury)), MIN_RESERVE);
    }

    // ═══════════════════════════════════════════════════════
    // CIRCUIT BREAKER (V3 Section 4.4)
    // ═══════════════════════════════════════════════════════

    function test_circuitBreaker_notActiveWhenHealthy() public view {
        assertFalse(treasury.isCircuitBreakerActive());
    }

    function test_circuitBreaker_activeWhenBelowMinimum() public {
        // Drain treasury to below minimum
        uint256 balance = usdc.balanceOf(address(treasury));
        uint256 deployable = balance - MIN_RESERVE;
        
        vm.prank(deployer);
        treasury.deploy(bob, deployable, keccak256("Research"));
        
        // Now at exactly minimum — not yet active
        assertFalse(treasury.isCircuitBreakerActive());

        // Update minimum to be higher than current balance
        vm.prank(deployer);
        treasury.setMinimumReserve(balance); // Way above current balance
        
        assertTrue(treasury.isCircuitBreakerActive());
    }

    function test_circuitBreaker_updateMinimum() public {
        vm.prank(deployer);
        treasury.setMinimumReserve(500_000e6);
        
        assertEq(treasury.minimumReserve(), 500_000e6);
    }

    // ═══════════════════════════════════════════════════════
    // ECOSYSTEM EXPANSION (V3 Section 4.4)
    // ═══════════════════════════════════════════════════════

    function test_expansion_notReadyInitially() public view {
        assertFalse(treasury.isExpansionReady());
    }

    function test_expansion_surplusTracking() public {
        // Treasury has 2x minimum — surplus starts tracking on deposit
        vm.startPrank(alice);
        usdc.approve(address(treasury), 1e6);
        treasury.deposit(1e6); // Trigger surplus check
        vm.stopPrank();

        // Surplus tracking started but 30 days haven't passed
        assertFalse(treasury.isExpansionReady());

        // Fast-forward 30 days
        vm.warp(block.timestamp + 30 days + 1);
        assertTrue(treasury.isExpansionReady());
    }

    function test_expansion_resetsIfBalanceDrops() public {
        // Start surplus tracking
        vm.startPrank(alice);
        usdc.approve(address(treasury), 1e6);
        treasury.deposit(1e6);
        vm.stopPrank();

        // Fast-forward 15 days
        vm.warp(block.timestamp + 15 days);
        assertFalse(treasury.isExpansionReady());

        // Drain treasury below surplus threshold
        uint256 balance = usdc.balanceOf(address(treasury));
        uint256 surplus = balance - MIN_RESERVE;
        
        vm.prank(deployer);
        treasury.deploy(bob, surplus, keccak256("Infrastructure"));

        // Re-deposit to trigger check (now below 2x, resets tracker)
        vm.startPrank(alice);
        usdc.approve(address(treasury), 1e6);
        treasury.deposit(1e6);
        vm.stopPrank();

        // Even after 30 more days, expansion not ready (counter reset)
        vm.warp(block.timestamp + 30 days + 1);
        // Need to trigger another check
        vm.startPrank(alice);
        usdc.approve(address(treasury), 1e6);
        treasury.deposit(1e6);
        vm.stopPrank();
        
        // Balance is now around MIN_RESERVE + 2e6 — below 2x threshold
        assertFalse(treasury.isExpansionReady());
    }

    function test_expansionBudget() public view {
        uint256 balance = usdc.balanceOf(address(treasury));
        uint256 expected = balance - MIN_RESERVE;
        assertEq(treasury.expansionBudget(), expected);
    }

    function test_expansionBudget_zeroWhenAtMinimum() public {
        // Drain to minimum
        uint256 deployable = usdc.balanceOf(address(treasury)) - MIN_RESERVE;
        vm.prank(deployer);
        treasury.deploy(bob, deployable, keccak256("Infrastructure"));
        
        assertEq(treasury.expansionBudget(), 0);
    }

    // ═══════════════════════════════════════════════════════
    // CORE TAX SUNSET (V3 Section 6.3: $5M threshold)
    // ═══════════════════════════════════════════════════════

    function test_coreTaxSunset_notReadyInitially() public view {
        assertFalse(treasury.shouldSunsetCoreTax());
    }

    function test_coreTaxSunset_readyAtThreshold() public {
        // Mint enough USDC to treasury to hit $5M
        usdc.mint(address(treasury), 5_000_000e6);
        assertTrue(treasury.shouldSunsetCoreTax());
    }

    // ═══════════════════════════════════════════════════════
    // HEALTH METRICS
    // ═══════════════════════════════════════════════════════

    function test_healthMetrics() public view {
        (
            uint256 balance,
            uint256 minimum,
            bool healthy,
            bool expansionReady,
            bool sunsetReady
        ) = treasury.getHealth();

        assertEq(balance, usdc.balanceOf(address(treasury)));
        assertEq(minimum, MIN_RESERVE);
        assertTrue(healthy);
        assertFalse(expansionReady);
        assertFalse(sunsetReady);
    }

    // ═══════════════════════════════════════════════════════
    // CATEGORY MANAGEMENT
    // ═══════════════════════════════════════════════════════

    function test_approveNewCategory() public {
        bytes32 cat = keccak256("Education");
        assertFalse(treasury.approvedCategories(cat));
        
        vm.prank(deployer);
        treasury.approveCategory(cat);
        
        assertTrue(treasury.approvedCategories(cat));
    }

    // ═══════════════════════════════════════════════════════
    // ACCESS CONTROL
    // ═══════════════════════════════════════════════════════

    function test_deploy_onlyOwner() public {
        vm.prank(alice);
        vm.expectRevert("Treasury: not owner");
        treasury.deploy(alice, 1000e6, keccak256("Infrastructure"));
    }

    function test_emergencyWithdraw() public {
        uint256 amount = 1000e6;
        uint256 bobBefore = usdc.balanceOf(bob);
        
        vm.prank(deployer);
        treasury.emergencyWithdraw(bob, amount);
        
        assertEq(usdc.balanceOf(bob), bobBefore + amount);
    }

    function test_emergencyWithdraw_onlyOwner() public {
        vm.prank(alice);
        vm.expectRevert("Treasury: not owner");
        treasury.emergencyWithdraw(alice, 1000e6);
    }

    // ═══════════════════════════════════════════════════════
    // GAS BENCHMARKS
    // ═══════════════════════════════════════════════════════

    function test_gas_deposit() public {
        vm.startPrank(alice);
        usdc.approve(address(treasury), 10_000e6);
        
        uint256 g = gasleft();
        treasury.deposit(10_000e6);
        emit log_named_uint("Gas: deposit", g - gasleft());
        vm.stopPrank();
    }

    function test_gas_deploy() public {
        vm.prank(deployer);
        uint256 g = gasleft();
        treasury.deploy(bob, 1000e6, keccak256("Infrastructure"));
        emit log_named_uint("Gas: deploy", g - gasleft());
    }

    function test_gas_getHealth() public view {
        uint256 g = gasleft();
        treasury.getHealth();
        // Note: view functions don't cost gas on-chain, but this measures compute
        uint256 used = g - gasleft();
        // Just verify it runs without reverting
        assertGt(used, 0);
    }
}
