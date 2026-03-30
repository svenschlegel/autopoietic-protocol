"""
Autopoietic Protocol — Node Client Core Types
==============================================
Maps directly to IAutopoieticTypes.sol and the V3 Metabolic Payload JSON schema.
All types are shared across the network, chain, and agent layers.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional, Dict, Any
import hashlib
import json
import time
import uuid


class FrictionType(IntEnum):
    """Topographic friction classification for Gossipsub routing"""
    SEMANTIC = 0
    DETERMINISTIC = 1
    SPATIAL = 2
    TEMPORAL = 3


class VerificationTier(IntEnum):
    """Payload verification mechanism"""
    DETERMINISTIC = 0        # Tier 1: instant on-chain schema match
    OPTIMISTIC_CONSENSUS = 1 # Tier 2: time-locked with fraud proofs


# Gossipsub topic mapping (V3 Section 3.2)
TOPIC_MAP = {
    FrictionType.SEMANTIC: "/autopoiesis/payload/semantic",
    FrictionType.DETERMINISTIC: "/autopoiesis/payload/deterministic",
    FrictionType.SPATIAL: "/autopoiesis/payload/spatial",
    FrictionType.TEMPORAL: "/autopoiesis/payload/temporal",
}


@dataclass
class MetabolicPayload:
    """
    The atomic unit of work in the Autopoietic Protocol (V3 Schema).
    
    Maps to: contracts/interfaces/IAutopoieticTypes.sol :: Payload
    """
    payload_id: str
    creator: str                          # Creator's peer ID or address
    bounty_amount: float                  # USDC (human-readable)
    friction_type: FrictionType
    tier: VerificationTier
    membrane_rules_hash: str              # keccak256 of the win-condition
    execution_window_seconds: int         # Max commit-lock duration
    created_at: float = field(default_factory=time.time)
    
    # Lifecycle state
    is_claimed: bool = False
    is_solved: bool = False
    claimed_by: Optional[str] = None
    claim_expiry: float = 0.0
    solution_hash: Optional[str] = None
    
    # Core Vector (the raw entropy)
    core_vector: Dict[str, Any] = field(default_factory=dict)
    
    # Membrane Rules (the win condition)
    membrane_rules: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize to V3 JSON schema for Gossipsub broadcast"""
        return json.dumps({
            "payload_id": self.payload_id,
            "timestamp": self.created_at,
            "execution_window_seconds": self.execution_window_seconds,
            "verification_tier": self.tier.value,
            "thermodynamic_bounty": {
                "asset_class": "USDC",
                "base_amount": self.bounty_amount,
                "escrow_contract": "0x_ESCROW_CORE"
            },
            "topographic_state": {
                "current_friction": self.friction_type.name,
                "gossipsub_topic": TOPIC_MAP[self.friction_type],
                "density_weight": 0.78
            },
            "core_vector": self.core_vector,
            "membrane_rules": {
                "validation_protocol": "strict_schema_match",
                "membrane_rules_hash": self.membrane_rules_hash,
                "zero_gradient_condition": self.membrane_rules
            }
        }, indent=2)

    @classmethod
    def from_json(cls, data: str) -> "MetabolicPayload":
        """Deserialize from V3 JSON schema"""
        d = json.loads(data) if isinstance(data, str) else data
        return cls(
            payload_id=d["payload_id"],
            creator=d.get("creator", "unknown"),
            bounty_amount=d["thermodynamic_bounty"]["base_amount"],
            friction_type=FrictionType[d["topographic_state"]["current_friction"]],
            tier=VerificationTier(d["verification_tier"]),
            membrane_rules_hash=d["membrane_rules"]["membrane_rules_hash"],
            execution_window_seconds=d["execution_window_seconds"],
            created_at=d.get("timestamp", time.time()),
            core_vector=d.get("core_vector", {}),
            membrane_rules=d["membrane_rules"].get("zero_gradient_condition", {}),
        )


@dataclass
class AgentIdentity:
    """
    Cryptographic identity for a network agent (V3 Section 3.2).
    Maps to Libp2p PeerId generation via keypair.
    """
    peer_id: str
    public_key: str
    private_key: str  # In production: stored in secure keychain
    
    @classmethod
    def generate(cls) -> "AgentIdentity":
        """Generate a new agent identity (simulated Ed25519)"""
        # In production: use actual Ed25519 keypair via libp2p
        raw = uuid.uuid4().hex + str(time.time_ns())
        private_key = hashlib.sha256(raw.encode()).hexdigest()
        public_key = hashlib.sha256(private_key.encode()).hexdigest()
        peer_id = "Qm" + hashlib.sha256(public_key.encode()).hexdigest()[:44]
        return cls(peer_id=peer_id, public_key=public_key, private_key=private_key)


@dataclass
class AgentState:
    """
    The full state of an Autopoietic agent (V3 Section 2).
    Tracks mass, specialization, friction, and mode.
    """
    identity: AgentIdentity
    mass: float = 1.0
    edge_strength: float = 1.0
    current_load: int = 0
    max_load: int = 5
    total_solved: int = 0
    total_earned: float = 0.0
    consecutive_failures: int = 0
    is_quarantined: bool = False
    mode: str = "natural_language"       # or "structured"
    
    # Gossipsub subscriptions
    subscribed_topics: List[FrictionType] = field(default_factory=list)
    primary_specialization: FrictionType = FrictionType.SEMANTIC
    
    # Friction tracking (V3 Appendix A.4)
    parse_history: List[bool] = field(default_factory=list)
    solve_times: List[float] = field(default_factory=list)
    
    # RAG vector store (V3 Section 2.3)
    # In production: ChromaDB or LanceDB
    rag_store: Dict[str, Any] = field(default_factory=dict)

    @property
    def mu(self) -> float:
        """Friction coefficient μ (V3 Appendix A.4)"""
        window = self.parse_history[-100:]
        if not window:
            return 0.0
        return sum(1 for x in window if not x) / len(window)

    @property
    def priority_score(self) -> float:
        """Base priority score P_i without distance factoring"""
        if self.is_quarantined:
            return 0.0
        alpha = 0.8   # V3 Constitutional Constant
        beta = 1.5    # V3 Constitutional Constant
        return (self.mass ** alpha) / ((self.current_load + 1) ** beta)

    def priority_for_payload(self, payload: MetabolicPayload) -> float:
        """Full Gravitational Routing priority P_i (V3 Section 5.1)"""
        if self.is_quarantined:
            return 0.0
        
        # Topographic distance
        if payload.friction_type == self.primary_specialization:
            distance = 0.0
        elif payload.friction_type in self.subscribed_topics:
            distance = 0.5
        else:
            distance = 2.0
        
        alpha = 0.8
        beta = 1.5
        return (self.mass ** alpha) / ((distance + 1) * (self.current_load + 1) ** beta)


# ── Protocol Constants (V3 Spec) ────────────────────────────

PROTOCOL_CONSTANTS = {
    "alpha": 0.8,                   # Seniority Constant
    "beta": 1.5,                    # Congestion Exponent
    "mu_critical": 0.30,            # Mode shift threshold
    "lambda_decay": 0.005,          # Edge decay constant
    "epsilon": 0.01,                # Minimum viable edge
    "k_quarantine": 5,              # Consecutive failures to quarantine
    "sigma_min": 0.1,               # Efficiency coefficient floor
    "sigma_max": 3.0,               # Efficiency coefficient ceiling
    "metabolic_tax_bps": 500,       # 5% metabolic tax
    "core_contributor_bps": 100,    # 1% core contributor share
    "capillary_bps": 8000,          # 80% to solver
    "mycelial_bps": 1000,           # 10% to infrastructure
    "conduit_bps": 1000,            # 10% to routing nodes
    "max_execution_window": 86400,  # 24 hours max
    "jury_size": 5,
    "jury_majority": 3,
    "challenge_bond_bps": 500,      # 5% challenge bond
    "jury_mass_threshold": 50.0,    # Mass > 50 for jury
}
