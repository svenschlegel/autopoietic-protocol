// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title IAutopoieticTypes
 * @notice Shared types for the Autopoietic Protocol (V3.4 Specification)
 * @dev All structs map directly to the V3 Metabolic Payload JSON schema
 */
interface IAutopoieticTypes {

    /// @notice Verification tier for payload solutions
    enum VerificationTier { 
        Deterministic,       // Tier 1: instant on-chain schema match
        OptimisticConsensus  // Tier 2: time-locked with fraud proofs
    }

    /// @notice Topographic friction classification for Gossipsub routing
    enum FrictionType { 
        Semantic, 
        Deterministic, 
        Spatial, 
        Temporal 
    }

    /// @notice The Metabolic Payload — atomic unit of work (V3 schema)
    struct Payload {
        uint256 payloadId;
        address creator;
        uint256 bountyAmount;          // USDC (6 decimals)
        FrictionType frictionType;
        VerificationTier tier;
        bytes32 membraneRulesHash;     // keccak256 of the win-condition schema
        uint256 executionWindowSeconds;// Max commit-lock duration
        uint256 createdAt;
        
        bool isClaimed;
        bool isSolved;
        bool isChallenged;
        
        address claimedBy;
        uint256 claimExpiry;
        bytes32 solutionHash;          // Commit hash from solver
        
        // ── V3.4 Alpha Additions ──
        bool isAlpha;                  // Immutable Alpha state lock
        bool hasPhaseShifted;          // Tracks if GPSL cipher was emitted
        uint256 phaseShiftTimestamp;   // Start time for 20% annealing window
    }

    /// @notice Tier 2 challenge state
    struct Challenge {
        uint256 payloadId;
        address challenger;
        uint256 challengeBond;
        uint256 challengedAt;
        address[5] jurors;
        uint8 acceptVotes;
        uint8 rejectVotes;
        uint8 votesSubmitted;
        bool isResolved;
    }

    /// @notice Vascular payout split ratios (dynamic governance parameters)
    struct PayoutRatios {
        uint16 capillaryBps;   // Solver share (basis points, e.g. 8000 = 80%)
        uint16 mycelialBps;    // Infrastructure share
        uint16 conduitBps;     // Routing node share
    }

    // ── Events ──────────────────────────────────────────────

    event PayloadCreated(
        uint256 indexed payloadId, 
        address indexed creator, 
        uint256 bountyAmount, 
        FrictionType frictionType,
        VerificationTier tier
    );

    event PayloadCommitted(
        uint256 indexed payloadId, 
        address indexed agent, 
        uint256 claimExpiry
    );

    event PayloadSolved(
        uint256 indexed payloadId, 
        address indexed solver, 
        uint256 solverPayout,
        uint256 massAccrued
    );

    event PayloadChallenged(
        uint256 indexed payloadId, 
        address indexed challenger, 
        uint256 bond
    );

    event ChallengeResolved(
        uint256 indexed payloadId, 
        bool upheld,
        address indexed solver
    );

    event CommitExpired(
        uint256 indexed payloadId, 
        address indexed failedAgent
    );

    event AgentQuarantined(address indexed agent, uint256 consecutiveFailures);
    event MassMinted(address indexed agent, uint256 amount);
    event MassBurned(address indexed agent, uint256 amount);
}
