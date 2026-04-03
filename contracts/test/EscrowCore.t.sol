// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "test/BaseTest.sol";

/**
 * @title EscrowCoreTest
 * @notice Comprehensive tests for the Membrane Filter — the economic backbone
 * @dev Validates V3 Spec: §3, §4.3, §5.4
 *
 * Test coverage:
 *   - Payload creation & USDC escrow
 *   - Metabolic Tax routing (5% split: 4% treasury, 1% core contributor)
 *   - Commit-Reveal: claim, solve, timeout
 *   - Tier 1 deterministic verification
 *   - Tier 2 optimistic consensus (challenge, jury, settlement)
 *   - Vascular payout distribution (80/10/10)
 *   - Mass accrual on successful solve
 *   - Quarantine integration
 *   - Gas benchmarks
 */
contract EscrowCoreTest is BaseTest {

    bytes constant SOLUTION = "material_type:concrete,psi_target:4500";
    bytes constant BAD_SOLUTION = "material_type:wood,psi_target:100";

    // ═══════════════════════════════════════════════════════
    // PAYLOAD CREATION
    // ═══════════════════════════════════════════════════════

    function test_createPayload_locksUSDC() public {
        uint256 bounty = 1000e6; // 1000 USDC
        uint256 tax = (bounty * 500) / 10000; // 50 USDC
        uint256 total = bounty + tax;

        uint256 aliceBefore = usdc.balanceOf(alice);

        uint256 pid = _createTier1Payload(alice, bounty, SOLUTION);

        assertEq(usdc.balanceOf(alice), aliceBefore - total);
        assertEq(pid, 0);
        
        // Verify payload stored correctly
        (
            uint256 storedId,
            address creator,
            uint256 storedBounty,
            , , , , , , , , , , , , ,
        ) = escrow.payloads(pid);
        assertEq(storedId, 0);
        assertEq(creator, alice);
        assertEq(storedBounty, bounty);
    }

    function test_createPayload_routesMetabolicTax() public {
        uint256 bounty = 10_000e6; // 10,000 USDC
        uint256 tax = (bounty * 500) / 10000; // 500 USDC

        uint256 treasuryBefore = usdc.balanceOf(address(treasury));
        uint256 architectBefore = usdc.balanceOf(architect);

        _createTier1Payload(alice, bounty, SOLUTION);

        // Tax split: 4/5 to treasury, 1/5 to core contributor
        // Core share = tax * 100 / 500 = 100 USDC
        uint256 coreShare = (tax * 100) / 500;
        uint256 treasuryShare = tax - coreShare;

        assertEq(usdc.balanceOf(address(treasury)), treasuryBefore + treasuryShare);
        assertEq(usdc.balanceOf(architect), architectBefore + coreShare);
    }

    function test_createPayload_revertsZeroBounty() public {
        vm.startPrank(alice);
        usdc.approve(address(escrow), 1e6);
        vm.expectRevert("EscrowCore: zero bounty");
        escrow.createPayload(
            0,
            IAutopoieticTypes.FrictionType.Semantic,
            IAutopoieticTypes.VerificationTier.Deterministic,
            bytes32(0),
            3600
        );
        vm.stopPrank();
    }

    function test_createPayload_revertsInvalidWindow() public {
        vm.startPrank(alice);
        usdc.approve(address(escrow), 2000e6);
        
        // Too short
        vm.expectRevert("EscrowCore: invalid window");
        escrow.createPayload(
            1000e6,
            IAutopoieticTypes.FrictionType.Semantic,
            IAutopoieticTypes.VerificationTier.Deterministic,
            bytes32(0),
            100 // Below MIN_EXECUTION_WINDOW (300)
        );

        // Too long
        vm.expectRevert("EscrowCore: invalid window");
        escrow.createPayload(
            1000e6,
            IAutopoieticTypes.FrictionType.Semantic,
            IAutopoieticTypes.VerificationTier.Deterministic,
            bytes32(0),
            100000 // Above MAX_EXECUTION_WINDOW (86400)
        );
        vm.stopPrank();
    }

    // ═══════════════════════════════════════════════════════
    // COMMIT-REVEAL
    // ═══════════════════════════════════════════════════════

    function test_commitClaim_locksPayload() public {
        uint256 pid = _createTier1Payload(alice, 1000e6, SOLUTION);

        bytes32 secret = keccak256("bobsecret");
        bytes32 commitHash = keccak256(abi.encodePacked(SOLUTION, secret));

        vm.prank(bob);
        escrow.commitClaim(pid, commitHash);

        (, , , , , , , , bool isClaimed, , , address claimedBy, , , , , ) = escrow.payloads(pid);
        assertTrue(isClaimed);
        assertEq(claimedBy, bob);
    }

    function test_commitClaim_revertsDoubleClaim() public {
        uint256 pid = _createTier1Payload(alice, 1000e6, SOLUTION);

        bytes32 commitHash = keccak256(abi.encodePacked(SOLUTION, bytes32("s")));
        
        vm.prank(bob);
        escrow.commitClaim(pid, commitHash);

        // Carol tries to claim the same payload
        vm.prank(carol);
        vm.expectRevert("EscrowCore: already claimed");
        escrow.commitClaim(pid, commitHash);
    }

    function test_commitClaim_revertsQuarantinedAgent() public {
        uint256 pid = _createTier1Payload(alice, 1000e6, SOLUTION);

        // Quarantine mallory
        vm.startPrank(address(escrow));
        for (uint8 i = 0; i < 5; i++) {
            mass.recordFailure(mallory);
        }
        vm.stopPrank();

        bytes32 commitHash = keccak256(abi.encodePacked(SOLUTION, bytes32("s")));
        vm.prank(mallory);
        vm.expectRevert("EscrowCore: agent quarantined");
        escrow.commitClaim(pid, commitHash);
    }

    function test_releaseExpiredClaim() public {
        uint256 pid = _createTier1Payload(alice, 1000e6, SOLUTION);
        
        bytes32 commitHash = keccak256(abi.encodePacked(SOLUTION, bytes32("s")));
        vm.prank(bob);
        escrow.commitClaim(pid, commitHash);

        // Fast-forward past execution window (1 hour)
        vm.warp(block.timestamp + 3601);

        // Anyone can release the expired claim
        escrow.releaseExpiredClaim(pid);

        (, , , , , , , , bool isClaimed, , , address claimedBy, , , , , ) = escrow.payloads(pid);
        assertFalse(isClaimed);
        assertEq(claimedBy, address(0));

        // Bob should have a failure recorded
        assertEq(mass.consecutiveFailures(bob), 1);
    }

    function test_releaseExpiredClaim_revertsBeforeExpiry() public {
        uint256 pid = _createTier1Payload(alice, 1000e6, SOLUTION);
        
        bytes32 commitHash = keccak256(abi.encodePacked(SOLUTION, bytes32("s")));
        vm.prank(bob);
        escrow.commitClaim(pid, commitHash);

        // Try to release before expiry
        vm.expectRevert("EscrowCore: not expired");
        escrow.releaseExpiredClaim(pid);
    }

    // ═══════════════════════════════════════════════════════
    // TIER 1: DETERMINISTIC VERIFICATION
    // ═══════════════════════════════════════════════════════

    function test_tier1_successfulSolve() public {
        uint256 bounty = 1000e6;
        uint256 pid = _createTier1Payload(alice, bounty, SOLUTION);

        uint256 bobBefore = usdc.balanceOf(bob);

        _solvePayloadTier1(pid, bob, SOLUTION);

        // Verify payload is solved
        (, , , , , , , , , bool isSolved, , , , , , , ) = escrow.payloads(pid);
        assertTrue(isSolved);

        // Bob should receive 80% of bounty
        uint256 expectedPayout = (bounty * 8000) / 10000;
        assertEq(usdc.balanceOf(bob), bobBefore + expectedPayout);

        // Bob should have Mass accrued
        assertGt(mass.mass(bob), 0);
        assertEq(mass.payloadsSolved(bob), 1);
    }

    function test_tier1_membraneRejection() public {
        uint256 pid = _createTier1Payload(alice, 1000e6, SOLUTION);

        // Bob tries to submit wrong solution
        bytes32 secret = keccak256(abi.encodePacked("secret", bob));
        bytes32 commitHash = keccak256(abi.encodePacked(BAD_SOLUTION, secret));

        vm.startPrank(bob);
        escrow.commitClaim(pid, commitHash);
        // V3.4: must phase shift before revealing
        escrow.broadcastPhaseShift(pid, bytes("gpsl_cipher_test"));
        vm.stopPrank();

        // V3.4: warp past 20% annealing window (3600 / 5 = 720s)
        vm.warp(block.timestamp + 721);

        vm.startPrank(bob);
        vm.expectRevert("EscrowCore: membrane rejection");
        escrow.revealTier1(pid, BAD_SOLUTION, secret);
        vm.stopPrank();
    }

    function test_tier1_commitMismatch() public {
        uint256 pid = _createTier1Payload(alice, 1000e6, SOLUTION);

        bytes32 secret = keccak256(abi.encodePacked("secret", bob));
        bytes32 commitHash = keccak256(abi.encodePacked(SOLUTION, secret));

        vm.startPrank(bob);
        escrow.commitClaim(pid, commitHash);
        // V3.4: must phase shift before revealing
        escrow.broadcastPhaseShift(pid, bytes("gpsl_cipher_test"));
        vm.stopPrank();

        // V3.4: warp past 20% annealing window (3600 / 5 = 720s)
        vm.warp(block.timestamp + 721);

        vm.startPrank(bob);
        // Try to reveal with wrong secret
        vm.expectRevert("EscrowCore: commit mismatch");
        escrow.revealTier1(pid, SOLUTION, bytes32("wrong_secret"));
        vm.stopPrank();
    }

    function test_tier1_revertsAfterExpiry() public {
        uint256 pid = _createTier1Payload(alice, 1000e6, SOLUTION);

        bytes32 secret = keccak256(abi.encodePacked("secret", bob));
        bytes32 commitHash = keccak256(abi.encodePacked(SOLUTION, secret));

        vm.prank(bob);
        escrow.commitClaim(pid, commitHash);

        // Fast-forward past execution window
        vm.warp(block.timestamp + 3601);

        vm.prank(bob);
        vm.expectRevert("EscrowCore: expired");
        escrow.revealTier1(pid, SOLUTION, secret);
    }

    function test_tier1_onlyClaimerCanReveal() public {
        uint256 pid = _createTier1Payload(alice, 1000e6, SOLUTION);

        bytes32 secret = keccak256(abi.encodePacked("secret", bob));
        bytes32 commitHash = keccak256(abi.encodePacked(SOLUTION, secret));

        vm.prank(bob);
        escrow.commitClaim(pid, commitHash);

        // Carol tries to reveal Bob's solution
        vm.prank(carol);
        vm.expectRevert("EscrowCore: not your claim");
        escrow.revealTier1(pid, SOLUTION, secret);
    }

    // ═══════════════════════════════════════════════════════
    // TIER 2: OPTIMISTIC CONSENSUS
    // ═══════════════════════════════════════════════════════

    function test_tier2_unchallengedFinalization() public {
        uint256 bounty = 1000e6;
        uint256 pid = _createTier2Payload(alice, bounty);

        _submitTier2Solution(pid, bob, SOLUTION);

        // Fast-forward past escrow window (4 hours for <500 USDC)
        vm.warp(block.timestamp + 24 hours + 1);

        uint256 bobBefore = usdc.balanceOf(bob);
        escrow.finalizeTier2(pid);

        (, , , , , , , , , bool isSolved, , , , , , , ) = escrow.payloads(pid);
        assertTrue(isSolved);

        uint256 expectedPayout = (bounty * 8000) / 10000;
        assertEq(usdc.balanceOf(bob), bobBefore + expectedPayout);
    }

    function test_tier2_cannotFinalizeBeforeEscrow() public {
        uint256 pid = _createTier2Payload(alice, 1000e6);
        _submitTier2Solution(pid, bob, SOLUTION);

        vm.expectRevert("EscrowCore: escrow active");
        escrow.finalizeTier2(pid);
    }

    function test_tier2_challenge() public {
        uint256 bounty = 1000e6;
        uint256 pid = _createTier2Payload(alice, bounty);
        _submitTier2Solution(pid, bob, SOLUTION);

        // Dave challenges
        uint256 bond = (bounty * 500) / 10000; // 5% = 50 USDC

        vm.startPrank(dave);
        usdc.approve(address(escrow), bond);
        escrow.challengeSubmission(pid);
        vm.stopPrank();

        (, , , , , , , , , , bool isChallenged, , , , , , ) = escrow.payloads(pid);
        assertTrue(isChallenged);
    }

    function test_tier2_challengeRequiresMass() public {
        uint256 pid = _createTier2Payload(alice, 1000e6);
        _submitTier2Solution(pid, bob, SOLUTION);

        // Mallory has no mass — cannot challenge
        vm.startPrank(mallory);
        usdc.approve(address(escrow), 100e6);
        vm.expectRevert("EscrowCore: insufficient Mass for challenge");
        escrow.challengeSubmission(pid);
        vm.stopPrank();
    }

    function test_tier2_solverCannotSelfChallenge() public {
        uint256 pid = _createTier2Payload(alice, 1000e6);
        
        // Give bob jury-level mass first
        vm.prank(deployer);
        mass.authorizeMinter(deployer);
        vm.prank(deployer);
        mass.accrueMass(bob, 60e18);
        vm.prank(deployer);
        mass.revokeMinter(deployer);
        
        _submitTier2Solution(pid, bob, SOLUTION);

        vm.startPrank(bob);
        usdc.approve(address(escrow), 100e6);
        vm.expectRevert("EscrowCore: cannot self-challenge");
        escrow.challengeSubmission(pid);
        vm.stopPrank();
    }

    function test_tier2_juryRegistrationAndVoting() public {
        uint256 bounty = 1000e6;
        uint256 pid = _createTier2Payload(alice, bounty);
        _submitTier2Solution(pid, bob, SOLUTION);

        // Dave challenges
        uint256 challengeBond = (bounty * 500) / 10000;
        vm.startPrank(dave);
        usdc.approve(address(escrow), challengeBond);
        escrow.challengeSubmission(pid);
        vm.stopPrank();

        // Register 5 jurors (eve, frank, grace, heidi, ivan)
        address[5] memory jurors = [eve, frank, grace, heidi, ivan];
        uint256 jurorBond = (bounty * 50) / 10000; // 0.5%

        for (uint256 i = 0; i < 5; i++) {
            vm.startPrank(jurors[i]);
            usdc.approve(address(escrow), jurorBond);
            escrow.registerAsJuror(pid);
            vm.stopPrank();
        }

        // 3 vote Accept (majority upheld)
        for (uint256 i = 0; i < 3; i++) {
            vm.prank(jurors[i]);
            escrow.castJuryVote(pid, true);
        }

        // Challenge should be resolved — submission upheld
        (, , , , , , , , , bool isSolved, , , , , , , ) = escrow.payloads(pid);
        assertTrue(isSolved);
    }

    function test_tier2_juryRejectsSubmission() public {
        uint256 bounty = 1000e6;
        uint256 pid = _createTier2Payload(alice, bounty);
        _submitTier2Solution(pid, bob, BAD_SOLUTION);

        // Dave challenges
        uint256 challengeBond = (bounty * 500) / 10000;
        vm.startPrank(dave);
        usdc.approve(address(escrow), challengeBond);
        escrow.challengeSubmission(pid);
        vm.stopPrank();

        // Register jurors
        address[5] memory jurors = [eve, frank, grace, heidi, ivan];
        uint256 jurorBond = (bounty * 50) / 10000;
        for (uint256 i = 0; i < 5; i++) {
            vm.startPrank(jurors[i]);
            usdc.approve(address(escrow), jurorBond);
            escrow.registerAsJuror(pid);
            vm.stopPrank();
        }

        uint256 daveBefore = usdc.balanceOf(dave);

        // 3 vote Reject
        for (uint256 i = 0; i < 3; i++) {
            vm.prank(jurors[i]);
            escrow.castJuryVote(pid, false);
        }

        // Submission rejected — payload returned to pool
        (, , , , , , , , bool isClaimed, bool isSolved, , , , , , , ) = escrow.payloads(pid);
        assertFalse(isSolved);

        // Dave gets bond back + whistleblower reward
        uint256 whistleblower = (bounty * 200) / 10000;
        assertGt(usdc.balanceOf(dave), daveBefore); // Bond + reward
    }

    function test_tier2_jurorCannotVoteTwice() public {
        uint256 pid = _createTier2Payload(alice, 1000e6);
        _submitTier2Solution(pid, bob, SOLUTION);

        uint256 challengeBond = (1000e6 * 500) / 10000;
        vm.startPrank(dave);
        usdc.approve(address(escrow), challengeBond);
        escrow.challengeSubmission(pid);
        vm.stopPrank();

        // Register eve as juror
        uint256 jurorBond = (1000e6 * 50) / 10000;
        vm.startPrank(eve);
        usdc.approve(address(escrow), jurorBond);
        escrow.registerAsJuror(pid);
        vm.stopPrank();

        vm.prank(eve);
        escrow.castJuryVote(pid, true);

        vm.prank(eve);
        vm.expectRevert("EscrowCore: already voted");
        escrow.castJuryVote(pid, true);
    }

    function test_tier2_solverCannotBeJuror() public {
        uint256 pid = _createTier2Payload(alice, 1000e6);
        
        // Give bob jury mass
        vm.prank(deployer);
        mass.authorizeMinter(deployer);
        vm.prank(deployer);
        mass.accrueMass(bob, 60e18);
        vm.prank(deployer);
        mass.revokeMinter(deployer);
        
        _submitTier2Solution(pid, bob, SOLUTION);

        uint256 challengeBond = (1000e6 * 500) / 10000;
        vm.startPrank(dave);
        usdc.approve(address(escrow), challengeBond);
        escrow.challengeSubmission(pid);
        vm.stopPrank();

        uint256 jurorBond = (1000e6 * 50) / 10000;
        vm.startPrank(bob);
        usdc.approve(address(escrow), jurorBond);
        vm.expectRevert("EscrowCore: solver cannot be juror");
        escrow.registerAsJuror(pid);
        vm.stopPrank();
    }

    // ═══════════════════════════════════════════════════════
    // VASCULAR PAYOUT DISTRIBUTION
    // ═══════════════════════════════════════════════════════

    function test_payoutRatios_default() public {
        (uint16 cap, uint16 myc, uint16 con) = escrow.payoutRatios();
        assertEq(cap, 8000); // 80%
        assertEq(myc, 1000); // 10%
        assertEq(con, 1000); // 10%
    }

    function test_payoutRatios_update() public {
        vm.prank(deployer);
        escrow.updatePayoutRatios(7000, 1000, 2000);
        
        (uint16 cap, , uint16 con) = escrow.payoutRatios();
        assertEq(cap, 7000);
        assertEq(con, 2000);
    }

    function test_payoutRatios_mustSumTo10000() public {
        vm.prank(deployer);
        vm.expectRevert("EscrowCore: sum to 10000");
        escrow.updatePayoutRatios(7000, 1000, 1000); // = 9000, not 10000
    }

    // ═══════════════════════════════════════════════════════
    // CORE CONTRIBUTOR TAX SUNSET
    // ═══════════════════════════════════════════════════════

    function test_coreContributorTax_routesCorrectly() public {
        uint256 bounty = 10_000e6;
        uint256 tax = (bounty * 500) / 10000; // 500 USDC
        uint256 coreShare = (tax * 100) / 500; // 100 USDC
        
        uint256 archBefore = usdc.balanceOf(architect);
        _createTier1Payload(alice, bounty, SOLUTION);
        
        assertEq(usdc.balanceOf(architect), archBefore + coreShare);
    }

    function test_coreContributorTax_afterSunset() public {
        // Sunset the tax
        vm.prank(deployer);
        escrow.sunsetCoreContributorTax();

        uint256 bounty = 10_000e6;
        uint256 archBefore = usdc.balanceOf(architect);
        uint256 treasBefore = usdc.balanceOf(address(treasury));

        _createTier1Payload(alice, bounty, SOLUTION);

        // Architect gets nothing after sunset
        assertEq(usdc.balanceOf(architect), archBefore);
        
        // Treasury gets 100% of tax
        uint256 tax = (bounty * 500) / 10000;
        assertEq(usdc.balanceOf(address(treasury)), treasBefore + tax);
    }

    // ═══════════════════════════════════════════════════════
    // PAUSE / CIRCUIT BREAKER
    // ═══════════════════════════════════════════════════════

    function test_pause_blocksNewPayloads() public {
        vm.prank(deployer);
        escrow.pause();

        vm.startPrank(alice);
        usdc.approve(address(escrow), 2000e6);
        vm.expectRevert("EscrowCore: paused");
        escrow.createPayload(
            1000e6,
            IAutopoieticTypes.FrictionType.Semantic,
            IAutopoieticTypes.VerificationTier.Deterministic,
            bytes32(0), 3600
        );
        vm.stopPrank();
    }

    function test_unpause_resumesOperations() public {
        vm.prank(deployer);
        escrow.pause();
        
        vm.prank(deployer);
        escrow.unpause();
        
        // Should work now
        _createTier1Payload(alice, 1000e6, SOLUTION);
    }

    // ═══════════════════════════════════════════════════════
    // MULTIPLE PAYLOAD LIFECYCLE (Integration)
    // ═══════════════════════════════════════════════════════

    function test_multiplePayloads_sequentialSolves() public {
        // Create 3 payloads, solve them all
        bytes memory sol1 = "solution_one";
        bytes memory sol2 = "solution_two";
        bytes memory sol3 = "solution_three";

        uint256 pid1 = _createTier1Payload(alice, 500e6, sol1);
        uint256 pid2 = _createTier1Payload(alice, 1000e6, sol2);
        uint256 pid3 = _createTier1Payload(alice, 2000e6, sol3);

        _solvePayloadTier1(pid1, bob, sol1);
        _solvePayloadTier1(pid2, carol, sol2);
        _solvePayloadTier1(pid3, bob, sol3);

        // Bob solved 2, Carol solved 1
        assertEq(mass.payloadsSolved(bob), 2);
        assertEq(mass.payloadsSolved(carol), 1);
        assertGt(mass.mass(bob), mass.mass(carol));
    }

    // ═══════════════════════════════════════════════════════
    // GAS BENCHMARKS
    // ═══════════════════════════════════════════════════════

    function test_gas_createPayload() public {
        vm.startPrank(alice);
        usdc.approve(address(escrow), 2000e6);
        
        uint256 g = gasleft();
        escrow.createPayload(
            1000e6,
            IAutopoieticTypes.FrictionType.Semantic,
            IAutopoieticTypes.VerificationTier.Deterministic,
            keccak256(SOLUTION), 3600
        );
        emit log_named_uint("Gas: createPayload", g - gasleft());
        vm.stopPrank();
    }

    function test_gas_commitClaim() public {
        uint256 pid = _createTier1Payload(alice, 1000e6, SOLUTION);
        bytes32 commitHash = keccak256(abi.encodePacked(SOLUTION, bytes32("s")));

        vm.prank(bob);
        uint256 g = gasleft();
        escrow.commitClaim(pid, commitHash);
        emit log_named_uint("Gas: commitClaim", g - gasleft());
    }

    function test_gas_revealTier1() public {
        uint256 pid = _createTier1Payload(alice, 1000e6, SOLUTION);
        bytes32 secret = keccak256(abi.encodePacked("secret", bob));
        bytes32 commitHash = keccak256(abi.encodePacked(SOLUTION, secret));

        vm.startPrank(bob);
        escrow.commitClaim(pid, commitHash);
        // V3.4: phase shift required before reveal
        escrow.broadcastPhaseShift(pid, bytes("gpsl_cipher_test"));
        vm.stopPrank();

        vm.warp(block.timestamp + 721); // past 20% annealing window

        vm.prank(bob);
        uint256 g = gasleft();
        escrow.revealTier1(pid, SOLUTION, secret);
        emit log_named_uint("Gas: revealTier1 (full solve)", g - gasleft());
    }

    function test_gas_fullTier2Lifecycle() public {
        uint256 bounty = 1000e6;
        uint256 pid = _createTier2Payload(alice, bounty);
        _submitTier2Solution(pid, bob, SOLUTION);

        uint256 challengeBond = (bounty * 500) / 10000;
        vm.startPrank(dave);
        usdc.approve(address(escrow), challengeBond);
        uint256 g1 = gasleft();
        escrow.challengeSubmission(pid);
        emit log_named_uint("Gas: challengeSubmission", g1 - gasleft());
        vm.stopPrank();

        address[5] memory jurors = [eve, frank, grace, heidi, ivan];
        uint256 jurorBond = (bounty * 50) / 10000;
        for (uint256 i = 0; i < 5; i++) {
            vm.startPrank(jurors[i]);
            usdc.approve(address(escrow), jurorBond);
            escrow.registerAsJuror(pid);
            vm.stopPrank();
        }

        vm.prank(jurors[0]);
        uint256 g2 = gasleft();
        escrow.castJuryVote(pid, true);
        emit log_named_uint("Gas: castJuryVote (non-resolving)", g2 - gasleft());

        vm.prank(jurors[1]);
        escrow.castJuryVote(pid, true);

        vm.prank(jurors[2]);
        uint256 g3 = gasleft();
        escrow.castJuryVote(pid, true); // This resolves
        emit log_named_uint("Gas: castJuryVote (resolving, 3rd accept)", g3 - gasleft());
    }
}
