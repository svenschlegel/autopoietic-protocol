"""
Autopoietic Protocol — Agent Brain
====================================
The autonomous agent that lives in the Phase Space.
Implements:
  - Payload evaluation via Gravitational Routing priority
  - Topographic distance calculation ("smelling" payloads)
  - Commit-Reveal workflow
  - Deterministic solution processing
  - Friction monitoring and organic mode shifts
  - RAG vector store updates (Plasticity Matrix)
  - Edge decay awareness (self-preservation)
"""

import asyncio
import hashlib
import json
import time
import random
import logging
from typing import Optional, Dict, List, Any, Callable

from ..core.types import (
    AgentIdentity, AgentState, MetabolicPayload, FrictionType,
    VerificationTier, TOPIC_MAP, PROTOCOL_CONSTANTS
)
from ..network.gossip import PeerNode, GossipNetwork, GossipMessage
from ..chain.local_chain import LocalChain

logger = logging.getLogger("autopoietic.agent")


class AutopoieticAgent:
    """
    A single autonomous agent in the Autopoietic Protocol.
    
    This is the Node Client — the "body" that an operator runs on their
    hardware. It connects to the Gossipsub mesh, evaluates incoming payloads,
    commits to tasks, processes solutions, and submits results to the chain.
    """

    def __init__(
        self,
        identity: AgentIdentity,
        network: GossipNetwork,
        chain: LocalChain,
        specialization: FrictionType = FrictionType.DETERMINISTIC,
        secondary_topics: Optional[List[FrictionType]] = None,
    ):
        self.state = AgentState(
            identity=identity,
            primary_specialization=specialization,
            subscribed_topics=[specialization] + (secondary_topics or []),
        )
        self.network = network
        self.chain = chain
        
        # Network node
        self.node: PeerNode = network.create_peer(identity)
        
        # Agent's processing queue
        self.pending_payloads: Dict[str, MetabolicPayload] = {}
        self.active_tasks: Dict[str, MetabolicPayload] = {}
        self.completed_tasks: List[str] = []
        
        # Solution processors (pluggable)
        self._solvers: Dict[FrictionType, Callable] = {
            FrictionType.DETERMINISTIC: self._solve_deterministic,
            FrictionType.SEMANTIC: self._solve_semantic,
            FrictionType.SPATIAL: self._solve_spatial,
            FrictionType.TEMPORAL: self._solve_temporal,
        }
        
        self._running = False
        self._secret = hashlib.sha256(identity.private_key.encode()).hexdigest()

    # ═══════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════

    async def start(self):
        """Boot the agent: join the mesh, subscribe to topics, start listening"""
        logger.info(
            f"[{self.peer_id}] Starting agent | "
            f"Specialization: {self.state.primary_specialization.name} | "
            f"Topics: {[t.name for t in self.state.subscribed_topics]}"
        )

        # Subscribe to Gossipsub topics
        for topic_type in self.state.subscribed_topics:
            topic = TOPIC_MAP[topic_type]
            self.node.subscribe(topic)
            self.node.on_message(topic, self._handle_message)

        # Discover peers via Kademlia DHT simulation
        self.network.discover_peers(self.node)

        self._running = True
        logger.info(
            f"[{self.peer_id}] Online | "
            f"Peers: {len(self.node.known_peers)} | "
            f"Mass: {self.state.mass:.2f}"
        )

    async def stop(self):
        """Gracefully shut down the agent"""
        self._running = False
        logger.info(f"[{self.peer_id}] Shutting down | Solved: {self.state.total_solved}")

    @property
    def peer_id(self) -> str:
        return self.state.identity.peer_id[:16]

    # ═══════════════════════════════════════════════════════
    # MESSAGE HANDLING
    # ═══════════════════════════════════════════════════════

    async def _handle_message(self, msg: GossipMessage):
        """Handle incoming Gossipsub messages"""
        if msg.sender_peer_id == self.state.identity.peer_id:
            return  # Ignore own messages

        try:
            data = json.loads(msg.payload)
        except json.JSONDecodeError:
            return

        if msg.msg_type == "payload" or data.get("thermodynamic_bounty"):
            await self._handle_payload(data)
        elif msg.msg_type == "commit" or data.get("type") == "commit":
            await self._handle_commit(data)
        elif msg.msg_type == "solution" or data.get("type") == "solution":
            await self._handle_solution_broadcast(data)

    async def _handle_payload(self, data: dict):
        """Evaluate an incoming Metabolic Payload"""
        try:
            payload = MetabolicPayload.from_json(data)
        except (KeyError, ValueError) as e:
            logger.debug(f"[{self.peer_id}] Malformed payload: {e}")
            return

        # Check if already claimed or solved
        if self.network.is_payload_committed(payload.payload_id):
            return

        # Calculate priority score (Gravitational Routing)
        priority = self.state.priority_for_payload(payload)
        
        if priority <= 0:
            return

        # Check capacity
        if self.state.current_load >= self.state.max_load:
            logger.debug(f"[{self.peer_id}] At capacity, skipping {payload.payload_id[:12]}")
            return

        # Store for processing
        self.pending_payloads[payload.payload_id] = payload
        logger.info(
            f"[{self.peer_id}] Received payload {payload.payload_id[:12]} | "
            f"Priority: {priority:.4f} | Bounty: ${payload.bounty_amount:,.2f}"
        )

    async def _handle_commit(self, data: dict):
        """Handle a commit broadcast — remove payload from our pending queue"""
        pid = data.get("payload_id")
        if pid and pid in self.pending_payloads:
            committer = data.get("peer_id", "unknown")
            if committer != self.state.identity.peer_id:
                del self.pending_payloads[pid]
                logger.debug(
                    f"[{self.peer_id}] Payload {pid[:12]} claimed by {committer[:12]}, dropping"
                )

    async def _handle_solution_broadcast(self, data: dict):
        """Handle a solution broadcast — payload is now solved"""
        pid = data.get("payload_id")
        if pid and pid in self.pending_payloads:
            del self.pending_payloads[pid]

    # ═══════════════════════════════════════════════════════
    # PAYLOAD PROCESSING
    # ═══════════════════════════════════════════════════════

    async def process_pending(self):
        """
        Evaluate all pending payloads and attempt to claim the best one.
        This is the agent's main "heartbeat" — called periodically.
        """
        if not self.pending_payloads or self.state.is_quarantined:
            return

        # Sort by priority score (highest first)
        scored = [
            (pid, self.state.priority_for_payload(pl), pl)
            for pid, pl in self.pending_payloads.items()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        for pid, priority, payload in scored:
            if self.state.current_load >= self.state.max_load:
                break
            if self.network.is_payload_committed(pid):
                continue

            # Attempt to claim and solve
            success = await self._claim_and_solve(payload)
            if success:
                break

    async def _claim_and_solve(self, payload: MetabolicPayload) -> bool:
        """
        Execute the full Commit-Reveal workflow:
        1. Generate solution
        2. Commit hash to network + chain
        3. Submit solution (Reveal) to chain
        4. Collect payout + mass
        """
        # Step 1: Generate solution
        solution = await self._generate_solution(payload)
        if solution is None:
            self.state.parse_history.append(False)
            self._check_mode_shift()
            return False

        solution_bytes = solution.encode() if isinstance(solution, str) else solution

        # Step 2: Commit
        commit_hash = hashlib.sha256(solution_bytes + self._secret.encode()).hexdigest()
        
        try:
            self.chain.commit_claim(
                payload.payload_id,
                self.state.identity.peer_id,
                commit_hash
            )
        except ValueError as e:
            logger.warning(f"[{self.peer_id}] Commit failed: {e}")
            return False

        # Broadcast commit to network
        await self.network.broadcast_commit(self.node, payload.payload_id, commit_hash)
        
        self.state.current_load += 1
        self.active_tasks[payload.payload_id] = payload

        # Remove from pending
        self.pending_payloads.pop(payload.payload_id, None)

        # Step 3: Reveal (submit solution to chain)
        try:
            start_time = time.time()
            success, payout, mass_accrued = self.chain.reveal_tier1(
                payload.payload_id,
                self.state.identity.peer_id,
                solution_bytes,
                self._secret
            )
            solve_time = time.time() - start_time

            if success:
                # Update agent state
                self.state.mass = self.chain.get_mass(self.state.identity.peer_id)
                self.state.total_solved += 1
                self.state.total_earned += payout
                self.state.current_load -= 1
                self.state.consecutive_failures = 0
                self.state.parse_history.append(True)
                self.state.solve_times.append(solve_time)
                self.completed_tasks.append(payload.payload_id)
                self.active_tasks.pop(payload.payload_id, None)

                # Update RAG store (Plasticity Matrix, V3 Section 2.3)
                self._update_rag_store(payload, solution)

                # Broadcast solution
                await self.network.broadcast_solution(
                    self.node, payload.payload_id, solution
                )

                logger.info(
                    f"[{self.peer_id}] ✓ SOLVED {payload.payload_id[:12]} | "
                    f"Payout: ${payout:,.2f} | Mass: {self.state.mass:.4f} | "
                    f"Total solved: {self.state.total_solved}"
                )
                return True

        except ValueError as e:
            logger.warning(f"[{self.peer_id}] ✗ Reveal failed: {e}")
            self.state.current_load -= 1
            self.state.consecutive_failures += 1
            self.state.parse_history.append(False)
            self.active_tasks.pop(payload.payload_id, None)
            self._check_mode_shift()
            return False

    # ═══════════════════════════════════════════════════════
    # SOLUTION GENERATION (Pluggable Solvers)
    # ═══════════════════════════════════════════════════════

    async def _generate_solution(self, payload: MetabolicPayload) -> Optional[str]:
        """
        Generate a solution for the payload based on friction type.
        
        In production, this is where the LLM / compute engine lives.
        For the prototype, we implement deterministic solving.
        """
        solver = self._solvers.get(payload.friction_type)
        if solver:
            return solver(payload)
        return None

    def _solve_deterministic(self, payload: MetabolicPayload) -> Optional[str]:
        """
        Solve a deterministic payload by extracting structured data
        from the core vector and formatting to match membrane rules.
        """
        core = payload.core_vector
        rules = payload.membrane_rules

        if not core or not rules:
            return None

        try:
            raw_text = core.get("raw_entropy", "")
            required_keys = rules.get("required_keys", [])
            
            # Extract values from raw text (simple pattern matching)
            # In production: NLP extraction, LLM processing, etc.
            result = {}
            for key in required_keys:
                if key in core:
                    result[key] = core[key]
                else:
                    # Try to find it in the raw text
                    result[key] = self._extract_from_text(raw_text, key)

            solution = json.dumps(result, sort_keys=True)
            return solution

        except Exception as e:
            logger.debug(f"[{self.peer_id}] Solve error: {e}")
            return None

    def _solve_semantic(self, payload: MetabolicPayload) -> Optional[str]:
        """Solve a semantic payload (NLP processing)"""
        # Stub: in production, this calls the local LLM
        core = payload.core_vector
        if "raw_entropy" in core:
            return json.dumps({"analysis": "processed", "source": core["raw_entropy"][:100]})
        return None

    def _solve_spatial(self, payload: MetabolicPayload) -> Optional[str]:
        """Solve a spatial payload (geometric computation)"""
        return None  # Stub for prototype

    def _solve_temporal(self, payload: MetabolicPayload) -> Optional[str]:
        """Solve a temporal payload (time-series analysis)"""
        return None  # Stub for prototype

    def _extract_from_text(self, text: str, key: str) -> Any:
        """Simple key-value extraction from unstructured text"""
        # Very basic extraction — in production: NLP/LLM
        import re
        patterns = {
            "material_type": r"using\s+(\w+)",
            "psi_target": r"(\d+)\s*PSI",
            "area_sq_meters": r"(\d+x\d+)\s*meter",
            "load_increase_pct": r"(\d+\.?\d*)%",
        }
        if key in patterns:
            match = re.search(patterns[key], text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    # ═══════════════════════════════════════════════════════
    # FRICTION & MODE SHIFTS (V3 Section 2.4, Appendix A.4)
    # ═══════════════════════════════════════════════════════

    def _check_mode_shift(self):
        """
        Check if μ > μ_critical and trigger organic mode shift.
        V3 Spec: μ = failed_parse_count / total_output_count (window=100)
        μ_critical = 0.30
        """
        mu = self.state.mu
        mu_critical = PROTOCOL_CONSTANTS["mu_critical"]

        if mu > mu_critical and self.state.mode == "natural_language":
            self.state.mode = "structured"
            logger.info(
                f"[{self.peer_id}] ⚡ MODE SHIFT: natural_language → structured "
                f"(μ = {mu:.3f} > {mu_critical})"
            )
        elif mu < mu_critical * 0.5 and self.state.mode == "structured":
            self.state.mode = "natural_language"
            logger.info(
                f"[{self.peer_id}] ⚡ MODE SHIFT: structured → natural_language "
                f"(μ = {mu:.3f} < {mu_critical * 0.5})"
            )

    # ═══════════════════════════════════════════════════════
    # RAG VECTOR STORE (Plasticity Matrix, V3 Section 2.3)
    # ═══════════════════════════════════════════════════════

    def _update_rag_store(self, payload: MetabolicPayload, solution: str):
        """
        Sear successful solution patterns into the local vector store.
        
        In production: ChromaDB / LanceDB with embedding vectors.
        For prototype: simple key-value store indexed by friction type.
        """
        key = f"{payload.friction_type.name}:{payload.membrane_rules_hash[:16]}"
        self.state.rag_store[key] = {
            "friction_type": payload.friction_type.name,
            "membrane_rules": payload.membrane_rules,
            "solution_pattern": solution[:200],
            "bounty": payload.bounty_amount,
            "solved_at": time.time(),
        }
        logger.debug(
            f"[{self.peer_id}] RAG store updated: {len(self.state.rag_store)} entries"
        )

    # ═══════════════════════════════════════════════════════
    # STATUS
    # ═══════════════════════════════════════════════════════

    def get_status(self) -> dict:
        return {
            "peer_id": self.state.identity.peer_id[:16],
            "specialization": self.state.primary_specialization.name,
            "mode": self.state.mode,
            "mass": round(self.state.mass, 4),
            "current_load": self.state.current_load,
            "total_solved": self.state.total_solved,
            "total_earned": round(self.state.total_earned, 2),
            "friction_mu": round(self.state.mu, 4),
            "consecutive_failures": self.state.consecutive_failures,
            "is_quarantined": self.state.is_quarantined,
            "rag_store_entries": len(self.state.rag_store),
            "pending_payloads": len(self.pending_payloads),
            "connected_peers": len(self.node.known_peers),
        }
