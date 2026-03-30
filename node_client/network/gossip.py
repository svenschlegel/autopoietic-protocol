"""
Autopoietic Protocol — Network Layer (Libp2p Simulation)
=========================================================
Simulates the Gossipsub peer-to-peer network for local testing.
Implements:
  - Kademlia-style peer discovery via bootstrap nodes
  - Topic-based Gossipsub subscription and message routing
  - Cryptographic commit broadcasting
  - Payload propagation only to subscribed peers

In production, replace this module with py-libp2p or js-libp2p.
The agent layer talks to the same interface regardless.
"""

import asyncio
import hashlib
import json
import time
import logging
from typing import Dict, List, Set, Callable, Optional, Any
from dataclasses import dataclass, field

from ..core.types import (
    AgentIdentity, MetabolicPayload, FrictionType, TOPIC_MAP
)

logger = logging.getLogger("autopoietic.network")


@dataclass
class GossipMessage:
    """A message propagated through the Gossipsub mesh"""
    msg_id: str
    topic: str
    sender_peer_id: str
    payload: str                # JSON-encoded data
    timestamp: float = field(default_factory=time.time)
    msg_type: str = "payload"   # payload | commit | release | solution


class PeerNode:
    """
    A single peer in the simulated Gossipsub network.
    Each agent runs one PeerNode.
    """

    def __init__(self, identity: AgentIdentity):
        self.identity = identity
        self.peer_id = identity.peer_id
        self.subscribed_topics: Set[str] = set()
        self.known_peers: Dict[str, "PeerNode"] = {}
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.seen_messages: Set[str] = set()  # Dedup
        self.inbox: asyncio.Queue = asyncio.Queue()
        self._running = False

    def subscribe(self, topic: str):
        """Subscribe to a Gossipsub topic"""
        self.subscribed_topics.add(topic)
        logger.debug(f"[{self.peer_id[:12]}] Subscribed to {topic}")

    def unsubscribe(self, topic: str):
        self.subscribed_topics.discard(topic)

    def on_message(self, topic: str, handler: Callable):
        """Register a handler for messages on a specific topic"""
        if topic not in self.message_handlers:
            self.message_handlers[topic] = []
        self.message_handlers[topic].append(handler)

    def connect_peer(self, peer: "PeerNode"):
        """Establish a direct connection to another peer"""
        self.known_peers[peer.peer_id] = peer
        peer.known_peers[self.peer_id] = self
        logger.debug(f"[{self.peer_id[:12]}] Connected to {peer.peer_id[:12]}")

    async def publish(self, topic: str, data: str, msg_type: str = "payload"):
        """Publish a message to a Gossipsub topic"""
        msg = GossipMessage(
            msg_id=hashlib.sha256(f"{self.peer_id}{time.time_ns()}{data[:50]}".encode()).hexdigest()[:16],
            topic=topic,
            sender_peer_id=self.peer_id,
            payload=data,
            msg_type=msg_type,
        )
        await self._propagate(msg)

    async def _propagate(self, msg: GossipMessage):
        """Propagate a message through the mesh (Gossipsub fan-out)"""
        if msg.msg_id in self.seen_messages:
            return
        self.seen_messages.add(msg.msg_id)

        # Deliver to local handlers
        if msg.topic in self.message_handlers:
            for handler in self.message_handlers[msg.topic]:
                try:
                    await handler(msg)
                except Exception as e:
                    logger.error(f"[{self.peer_id[:12]}] Handler error: {e}")

        # Forward to connected peers subscribed to this topic
        for peer_id, peer in self.known_peers.items():
            if msg.topic in peer.subscribed_topics and msg.msg_id not in peer.seen_messages:
                await peer._propagate(msg)


class GossipNetwork:
    """
    The simulated Gossipsub network — manages peers, discovery, and routing.
    
    In production, this is replaced by the actual Libp2p daemon.
    The agent layer only interacts via PeerNode.publish() and PeerNode.on_message().
    """

    def __init__(self):
        self.peers: Dict[str, PeerNode] = {}
        self.bootstrap_nodes: List[str] = []
        self._payload_registry: Dict[str, MetabolicPayload] = {}
        self._commit_registry: Dict[str, str] = {}  # payload_id -> peer_id

    def create_peer(self, identity: AgentIdentity) -> PeerNode:
        """Create and register a new peer node"""
        node = PeerNode(identity)
        self.peers[identity.peer_id] = node
        return node

    def register_bootstrap(self, peer_id: str):
        """Register a peer as a bootstrap node (V3 Section 3.3 Layer 1)"""
        self.bootstrap_nodes.append(peer_id)

    def discover_peers(self, node: PeerNode, max_peers: int = 10):
        """
        Kademlia-style peer discovery (V3 Section 3.3).
        New node contacts bootstrap nodes and gets a list of active peers.
        """
        # Connect to bootstrap nodes first
        for bp_id in self.bootstrap_nodes:
            if bp_id in self.peers and bp_id != node.peer_id:
                node.connect_peer(self.peers[bp_id])

        # Then discover peers through bootstrap nodes' connections
        discovered = set()
        for bp_id in self.bootstrap_nodes:
            if bp_id in self.peers:
                bp = self.peers[bp_id]
                for peer_id in list(bp.known_peers.keys()):
                    if peer_id != node.peer_id:
                        discovered.add(peer_id)

        # Connect to discovered peers (up to max)
        for peer_id in list(discovered)[:max_peers]:
            if peer_id in self.peers:
                node.connect_peer(self.peers[peer_id])

        logger.info(
            f"[{node.peer_id[:12]}] Discovered {len(node.known_peers)} peers "
            f"via {len(self.bootstrap_nodes)} bootstrap nodes"
        )

    async def broadcast_payload(self, sender: PeerNode, payload: MetabolicPayload):
        """Broadcast a new Metabolic Payload to the appropriate Gossipsub topic"""
        topic = TOPIC_MAP[payload.friction_type]
        self._payload_registry[payload.payload_id] = payload
        
        logger.info(
            f"[{sender.peer_id[:12]}] Broadcasting payload {payload.payload_id[:12]} "
            f"on {topic} (bounty: ${payload.bounty_amount:,.2f})"
        )
        await sender.publish(topic, payload.to_json(), msg_type="payload")

    async def broadcast_commit(self, sender: PeerNode, payload_id: str, commit_hash: str):
        """Broadcast a Commit claim for a payload (V3 Section 3.4)"""
        if payload_id in self._payload_registry:
            payload = self._payload_registry[payload_id]
            topic = TOPIC_MAP[payload.friction_type]
            
            commit_msg = json.dumps({
                "type": "commit",
                "payload_id": payload_id,
                "commit_hash": commit_hash,
                "peer_id": sender.peer_id,
                "timestamp": time.time()
            })
            
            self._commit_registry[payload_id] = sender.peer_id
            logger.info(
                f"[{sender.peer_id[:12]}] Committed to payload {payload_id[:12]}"
            )
            await sender.publish(topic, commit_msg, msg_type="commit")

    async def broadcast_solution(self, sender: PeerNode, payload_id: str, solution_data: str):
        """Broadcast a solution reveal"""
        if payload_id in self._payload_registry:
            payload = self._payload_registry[payload_id]
            topic = TOPIC_MAP[payload.friction_type]
            
            solution_msg = json.dumps({
                "type": "solution",
                "payload_id": payload_id,
                "solution_hash": hashlib.sha256(solution_data.encode()).hexdigest(),
                "peer_id": sender.peer_id,
                "timestamp": time.time()
            })
            
            logger.info(
                f"[{sender.peer_id[:12]}] Solution submitted for {payload_id[:12]}"
            )
            await sender.publish(topic, solution_msg, msg_type="solution")

    def get_payload(self, payload_id: str) -> Optional[MetabolicPayload]:
        return self._payload_registry.get(payload_id)

    def is_payload_committed(self, payload_id: str) -> bool:
        return payload_id in self._commit_registry

    def get_committer(self, payload_id: str) -> Optional[str]:
        return self._commit_registry.get(payload_id)

    def get_network_stats(self) -> Dict[str, Any]:
        return {
            "total_peers": len(self.peers),
            "bootstrap_nodes": len(self.bootstrap_nodes),
            "active_payloads": len(self._payload_registry),
            "active_commits": len(self._commit_registry),
            "topics": {
                topic: sum(
                    1 for p in self.peers.values() if topic in p.subscribed_topics
                )
                for topic in TOPIC_MAP.values()
            }
        }
