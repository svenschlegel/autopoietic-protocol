// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "src/SoulboundMass.sol";
import "src/EscrowCore.sol";
import "src/AutoToken.sol";
import "src/Treasury.sol";
import "test/mocks/MockUSDC.sol";

/**
 * @title BaseTest
 * @notice Shared test harness — deploys the full Autopoietic Protocol stack
 * @dev All test contracts inherit from this. Provides labeled addresses,
 *      funded accounts, and helper functions for common operations.
 */
abstract contract BaseTest is Test {

    // ── Contracts ───────────────────────────────────────────

    MockUSDC       public usdc;
    SoulboundMass  public mass;
    Treasury       public treasury;
    EscrowCore     public escrow;
    AutoToken      public autoToken;

    // ── Addresses ───────────────────────────────────────────

    address public deployer    = makeAddr("deployer");
    address public architect   = makeAddr("architect");
    address public alice       = makeAddr("alice");       // Payload creator
    address public bob         = makeAddr("bob");         // Agent / solver
    address public carol       = makeAddr("carol");       // Agent / solver
    address public dave        = makeAddr("dave");        // Challenger
    address public eve         = makeAddr("eve");         // Juror
    address public frank       = makeAddr("frank");       // Juror
    address public grace       = makeAddr("grace");       // Juror
    address public heidi       = makeAddr("heidi");       // Juror
    address public ivan        = makeAddr("ivan");        // Juror
    address public mallory     = makeAddr("mallory");     // Malicious agent

    // ── Constants ───────────────────────────────────────────

    uint256 public constant INITIAL_USDC = 1_000_000e6;  // 1M USDC each
    uint256 public constant MIN_RESERVE  = 100_000e6;     // 100k treasury min

    // ── Setup ───────────────────────────────────────────────

    function setUp() public virtual {
        vm.startPrank(deployer);

        // Deploy mock USDC
        usdc = new MockUSDC();

        // Deploy protocol
        mass     = new SoulboundMass();
        treasury = new Treasury(address(usdc), MIN_RESERVE);
        escrow   = new EscrowCore(
            address(usdc),
            address(mass),
            address(treasury),
            architect
        );
        autoToken = new AutoToken(architect, address(treasury));

        // Wire cross-references
        mass.authorizeMinter(address(escrow));
        autoToken.setEscrowCore(address(escrow));
        treasury.setEscrowCore(address(escrow));

        vm.stopPrank();

        // Fund all accounts with USDC
        _fundAll();

        // Give juror-eligible agents enough Mass for jury service
        _bootstrapJurors();
    }

    // ── Funding Helpers ─────────────────────────────────────

    function _fundAll() internal {
        address[11] memory accounts = [
            alice, bob, carol, dave, eve, frank, grace, heidi, ivan, mallory, architect
        ];
        for (uint256 i = 0; i < accounts.length; i++) {
            usdc.mint(accounts[i], INITIAL_USDC);
        }
        // Fund treasury directly
        usdc.mint(address(treasury), MIN_RESERVE * 2);
        // Fund EscrowCore to cover Tier 2 juror fee outflows
        usdc.mint(address(escrow), 100_000e6);
    }

    function _bootstrapJurors() internal {
        // Give dave, eve, frank, grace, heidi, ivan enough Mass for jury
        // (Mass > 50e18 required for jury service)
        address[6] memory jurors = [dave, eve, frank, grace, heidi, ivan];
        vm.startPrank(deployer);
        mass.authorizeMinter(deployer);
        for (uint256 i = 0; i < jurors.length; i++) {
            mass.accrueMass(jurors[i], 60e18);
        }
        mass.revokeMinter(deployer);
        vm.stopPrank();
    }

    // ── Payload Helpers ─────────────────────────────────────

    /**
     * @notice Create a standard Tier 1 deterministic payload
     * @param creator The payload creator
     * @param bounty USDC bounty amount (6 decimals)
     * @param solution The known-correct solution (used to compute membraneRulesHash)
     * @return payloadId
     */
    function _createTier1Payload(
        address creator,
        uint256 bounty,
        bytes memory solution
    ) internal returns (uint256) {
        uint256 tax = (bounty * 500) / 10000; // 5% metabolic tax
        uint256 total = bounty + tax;

        vm.startPrank(creator);
        usdc.approve(address(escrow), total);
        uint256 pid = escrow.createPayload(
            bounty,
            IAutopoieticTypes.FrictionType.Deterministic,
            IAutopoieticTypes.VerificationTier.Deterministic,
            keccak256(solution),  // membraneRulesHash = hash of correct solution
            3600                  // 1 hour execution window
        );
        vm.stopPrank();
        return pid;
    }

    /**
     * @notice Create a standard Tier 2 optimistic payload
     */
    function _createTier2Payload(
        address creator,
        uint256 bounty
    ) internal returns (uint256) {
        uint256 tax = (bounty * 500) / 10000;
        uint256 total = bounty + tax;

        vm.startPrank(creator);
        usdc.approve(address(escrow), total);
        uint256 pid = escrow.createPayload(
            bounty,
            IAutopoieticTypes.FrictionType.Semantic,
            IAutopoieticTypes.VerificationTier.OptimisticConsensus,
            bytes32(0),           // No deterministic schema for Tier 2
            7200                  // 2 hour execution window
        );
        vm.stopPrank();
        return pid;
    }

    /**
     * @notice Commit-reveal helper: agent claims and solves a Tier 1 payload
     */
    function _solvePayloadTier1(
        uint256 payloadId,
        address solver,
        bytes memory solution
    ) internal {
        bytes32 secret = keccak256(abi.encodePacked("secret", solver));
        bytes32 commitHash = keccak256(abi.encodePacked(solution, secret));

        vm.startPrank(solver);
        escrow.commitClaim(payloadId, commitHash);
        escrow.revealTier1(payloadId, solution, secret);
        vm.stopPrank();
    }

    /**
     * @notice Commit-reveal helper: agent claims and submits Tier 2 solution
     */
    function _submitTier2Solution(
        uint256 payloadId,
        address solver,
        bytes memory solution
    ) internal {
        bytes32 secret = keccak256(abi.encodePacked("secret", solver));
        bytes32 commitHash = keccak256(abi.encodePacked(solution, secret));

        vm.startPrank(solver);
        escrow.commitClaim(payloadId, commitHash);
        escrow.revealTier2(payloadId, solution, secret);
        vm.stopPrank();
    }
}
