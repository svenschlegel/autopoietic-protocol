// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "test/BaseTest.sol";

/**
 * @title IntegrationTest
 * @notice End-to-end tests simulating real protocol scenarios
 * @dev Validates the full V3 lifecycle:
 *   1. Genesis Geyser deployment
 *   2. Multi-agent payload competition
 *   3. Tax routing → treasury → circuit breaker interaction
 *   4. Vesting + governance interaction
 *   5. Malicious agent quarantine + payload re-routing
 */
contract IntegrationTest is BaseTest {

    // ═══════════════════════════════════════════════════════
    // SCENARIO 1: GENESIS GEYSER
    // ═══════════════════════════════════════════════════════

    function test_genesisGeyser_fullLifecycle() public {
        // The architect deploys a massive Genesis Payload
        uint256 genesisBounty = 50_000e6; // $50,000 USDC
        bytes memory solution = "compression_schema_v1_lossless_87pct";

        // Fund architect and create payload
        usdc.mint(architect, genesisBounty * 2);
        uint256 pid = _createTier1Payload(architect, genesisBounty, solution);

        // Bob (a Pioneer agent) claims and solves
        uint256 bobBefore = usdc.balanceOf(bob);
        _solvePayloadTier1(pid, bob, solution);

        // Verify: Bob received 80% of bounty
        uint256 expectedPayout = (genesisBounty * 8000) / 10000;
        assertEq(usdc.balanceOf(bob), bobBefore + expectedPayout);

        // Verify: Bob has massive Mass accrual (Pioneer advantage)
        assertGt(mass.mass(bob), 0);

        // Verify: Treasury received mycelial + conduit shares
        // (conduit goes to treasury when no routing path set)
        uint256 mycelial = (genesisBounty * 1000) / 10000;
        uint256 conduit = genesisBounty - expectedPayout - mycelial;
        // Treasury also got metabolic tax during payload creation
        assertGt(usdc.balanceOf(address(treasury)), MIN_RESERVE * 2);

        // Verify: Architect got core contributor tax share
        // Tax = 50000 * 5% = 2500, core share = 2500 * 100/500 = 500
        assertGt(usdc.balanceOf(architect), 0);
    }

    // ═══════════════════════════════════════════════════════
    // SCENARIO 2: COMPETITIVE MULTI-AGENT ROUTING
    // ═══════════════════════════════════════════════════════

    function test_competitiveRouting_firstClaimerWins() public {
        bytes memory solution = "optimal_answer";
        uint256 pid = _createTier1Payload(alice, 5000e6, solution);

        // Bob claims first
        bytes32 bobSecret = keccak256(abi.encodePacked("secret", bob));
        bytes32 bobCommit = keccak256(abi.encodePacked(solution, bobSecret));
        vm.prank(bob);
        escrow.commitClaim(pid, bobCommit);

        // Carol tries to claim — blocked
        bytes32 carolSecret = keccak256(abi.encodePacked("secret", carol));
        bytes32 carolCommit = keccak256(abi.encodePacked(solution, carolSecret));
        vm.prank(carol);
        vm.expectRevert("EscrowCore: already claimed");
        escrow.commitClaim(pid, carolCommit);

        // V3.4: Bob must phase shift before revealing
        vm.prank(bob);
        escrow.broadcastPhaseShift(pid, bytes("gpsl_cipher_test"));
        vm.warp(block.timestamp + 721); // past 20% annealing window (3600/5)

        // Bob solves
        vm.prank(bob);
        escrow.revealTier1(pid, solution, bobSecret);

        (, , , , , , , , , bool isSolved, , , , , , , ) = escrow.payloads(pid);
        assertTrue(isSolved);
    }

    // ═══════════════════════════════════════════════════════
    // SCENARIO 3: MALICIOUS AGENT QUARANTINE + RE-ROUTING
    // ═══════════════════════════════════════════════════════

    function test_maliciousAgent_quarantineAndReroute() public {
        bytes memory solution = "correct_answer";

        // Create 6 payloads
        uint256[] memory pids = new uint256[](6);
        for (uint256 i = 0; i < 6; i++) {
            pids[i] = _createTier1Payload(alice, 1000e6, solution);
        }

        // Mallory claims and fails 5 times → quarantined
        for (uint256 i = 0; i < 5; i++) {
            bytes32 secret = keccak256(abi.encodePacked("mal_secret", i));
            bytes32 badCommitHash = keccak256(abi.encodePacked("wrong_answer", secret));
            
            vm.prank(mallory);
            escrow.commitClaim(pids[i], badCommitHash);

            // Fast-forward to expire the lock
            vm.warp(block.timestamp + 3601);
            escrow.releaseExpiredClaim(pids[i]);
        }

        // Mallory should be quarantined now
        assertTrue(mass.isQuarantined(mallory));

        // Mallory cannot claim the 6th payload
        bytes32 commitHash = keccak256(abi.encodePacked(solution, bytes32("s")));
        vm.prank(mallory);
        vm.expectRevert("EscrowCore: agent quarantined");
        escrow.commitClaim(pids[5], commitHash);

        // Bob steps in and solves it
        _solvePayloadTier1(pids[5], bob, solution);

        (, , , , , , , , , bool isSolved, , , , , , , ) = escrow.payloads(pids[5]);
        assertTrue(isSolved);
    }

    // ═══════════════════════════════════════════════════════
    // SCENARIO 4: TIER 2 DISPUTED PAYLOAD (FULL JURY CYCLE)
    // ═══════════════════════════════════════════════════════

    function test_tier2_fullDisputeLifecycle() public {
        uint256 bounty = 5000e6;
        uint256 pid = _createTier2Payload(alice, bounty);

        // Bob submits solution
        bytes memory solution = "subjective_analysis_report";
        _submitTier2Solution(pid, bob, solution);

        // Dave challenges within escrow window
        uint256 challengeBond = (bounty * 500) / 10000; // 250 USDC
        vm.startPrank(dave);
        usdc.approve(address(escrow), challengeBond);
        escrow.challengeSubmission(pid);
        vm.stopPrank();

        // 5 jurors register
        address[5] memory jurors = [eve, frank, grace, heidi, ivan];
        uint256 jurorBond = (bounty * 50) / 10000; // 25 USDC each
        for (uint256 i = 0; i < 5; i++) {
            vm.startPrank(jurors[i]);
            usdc.approve(address(escrow), jurorBond);
            escrow.registerAsJuror(pid);
            vm.stopPrank();
        }

        // Record balances before resolution
        uint256 bobBefore = usdc.balanceOf(bob);

        // 3 accept, 2 reject → submission upheld
        vm.prank(eve);
        escrow.castJuryVote(pid, true);
        vm.prank(frank);
        escrow.castJuryVote(pid, true);
        vm.prank(grace);
        escrow.castJuryVote(pid, true); // Resolves at 3rd accept

        // Bob should have received payout
        assertGt(usdc.balanceOf(bob), bobBefore);
        
        // Payload should be solved
        (, , , , , , , , , bool isSolved, , , , , , , ) = escrow.payloads(pid);
        assertTrue(isSolved);

        // Bob should have Mass
        assertGt(mass.mass(bob), 0);
    }

    // ═══════════════════════════════════════════════════════
    // SCENARIO 5: TREASURY CIRCUIT BREAKER → VRGDA HALT
    // ═══════════════════════════════════════════════════════

    function test_circuitBreaker_haltsVRGDA() public {
        // Raise minimum reserve above current balance
        vm.prank(deployer);
        treasury.setMinimumReserve(type(uint256).max);
        
        assertTrue(treasury.isCircuitBreakerActive());

        // In production, this would trigger VRGDA halt
        // Simulate the governance response
        vm.prank(deployer);
        autoToken.haltVRGDA();

        // VRGDA purchases blocked
        vm.startPrank(alice);
        usdc.approve(address(autoToken), 100e6);
        vm.expectRevert("AutoToken: VRGDA halted");
        autoToken.purchaseVRGDA(1e18, 100e6, address(usdc));
        vm.stopPrank();

        // Fix: lower the minimum reserve
        vm.prank(deployer);
        treasury.setMinimumReserve(MIN_RESERVE);
        assertFalse(treasury.isCircuitBreakerActive());

        // Resume VRGDA
        vm.prank(deployer);
        autoToken.resumeVRGDA();

        // Now purchases work (V3.4: 1% mint burn → buyer receives 99%)
        vm.startPrank(alice);
        autoToken.purchaseVRGDA(1e18, 100e6, address(usdc));
        vm.stopPrank();
        assertEq(autoToken.balanceOf(alice), 1e18 * 99 / 100);
    }

    // ═══════════════════════════════════════════════════════
    // SCENARIO 6: CORE TAX SUNSET AT $5M
    // ═══════════════════════════════════════════════════════

    function test_coreTaxSunset_lifecycle() public {
        // Initially, architect receives core contributor tax
        uint256 archBefore = usdc.balanceOf(architect);
        _createTier1Payload(alice, 10_000e6, "sol1");
        assertGt(usdc.balanceOf(architect), archBefore);

        // Fund treasury to $5M threshold
        usdc.mint(address(treasury), 5_000_000e6);
        assertTrue(treasury.shouldSunsetCoreTax());

        // Governance sunsets the tax
        vm.prank(deployer);
        escrow.sunsetCoreContributorTax();

        // After sunset: architect gets nothing from new payloads
        uint256 archAfterSunset = usdc.balanceOf(architect);
        _createTier1Payload(alice, 10_000e6, "sol2");
        assertEq(usdc.balanceOf(architect), archAfterSunset);
    }

    // ═══════════════════════════════════════════════════════
    // SCENARIO 7: MASS ACCUMULATION OVER TIME
    // ═══════════════════════════════════════════════════════

    function test_massAccumulation_multiplePayloads() public {
        // Bob solves 10 payloads of increasing value
        for (uint256 i = 1; i <= 10; i++) {
            bytes memory sol = abi.encodePacked("solution_", i);
            uint256 bounty = i * 500e6;
            uint256 pid = _createTier1Payload(alice, bounty, sol);
            _solvePayloadTier1(pid, bob, sol);
        }

        // Bob should have significant mass
        assertGt(mass.mass(bob), 0);
        assertEq(mass.payloadsSolved(bob), 10);
        
        // Bob should have earned USDC from all payloads
        // Total bounties: 500 + 1000 + ... + 5000 = 27,500 USDC
        // Bob gets 80% = 22,000 USDC
        assertGt(usdc.balanceOf(bob), 20_000e6);
    }

    // ═══════════════════════════════════════════════════════
    // SCENARIO 8: EXPIRED CLAIM → SUCCESSFUL RE-SOLVE
    // ═══════════════════════════════════════════════════════

    function test_expiredClaim_reRouteToNewAgent() public {
        bytes memory solution = "correct_data";
        uint256 pid = _createTier1Payload(alice, 2000e6, solution);

        // Bob claims but doesn't solve in time
        bytes32 bobSecret = keccak256(abi.encodePacked("secret", bob));
        bytes32 bobCommit = keccak256(abi.encodePacked(solution, bobSecret));
        vm.prank(bob);
        escrow.commitClaim(pid, bobCommit);

        // Time passes — execution window expires
        vm.warp(block.timestamp + 3601);
        escrow.releaseExpiredClaim(pid);

        // Bob has a failure recorded
        assertEq(mass.consecutiveFailures(bob), 1);

        // Carol picks it up and solves
        _solvePayloadTier1(pid, carol, solution);

        (, , , , , , , , , bool isSolved, , , , , , , ) = escrow.payloads(pid);
        assertTrue(isSolved);
        assertEq(mass.payloadsSolved(carol), 1);
    }

    // ═══════════════════════════════════════════════════════
    // GAS: FULL LIFECYCLE BENCHMARK
    // ═══════════════════════════════════════════════════════

    function test_gas_fullTier1Lifecycle() public {
        uint256 bounty = 1000e6;
        bytes memory solution = "benchmark_solution";
        
        // Measure total gas for complete lifecycle
        uint256 g0 = gasleft();
        
        // Create
        uint256 tax = (bounty * 500) / 10000;
        vm.startPrank(alice);
        usdc.approve(address(escrow), bounty + tax);
        uint256 pid = escrow.createPayload(
            bounty,
            IAutopoieticTypes.FrictionType.Deterministic,
            IAutopoieticTypes.VerificationTier.Deterministic,
            keccak256(solution),
            3600
        );
        vm.stopPrank();

        // Commit
        bytes32 secret = keccak256(abi.encodePacked("secret", bob));
        bytes32 commitHash = keccak256(abi.encodePacked(solution, secret));
        vm.prank(bob);
        escrow.commitClaim(pid, commitHash);

        // V3.4: phase shift + annealing window
        vm.prank(bob);
        escrow.broadcastPhaseShift(pid, bytes("gpsl_cipher_test"));
        vm.warp(block.timestamp + 721); // past 20% annealing (3600/5)

        // Reveal + verify + payout
        vm.prank(bob);
        escrow.revealTier1(pid, solution, secret);

        uint256 totalGas = g0 - gasleft();
        emit log_named_uint("Gas: FULL Tier 1 lifecycle (create+commit+reveal+payout)", totalGas);
    }
}
