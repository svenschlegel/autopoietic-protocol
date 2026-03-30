"""
Autopoietic Protocol — Web3 Chain Adapter (Base Sepolia)
=========================================================
Connects the Node Client to the deployed smart contracts on Base Sepolia.
This is the production replacement for chain/local_chain.py.

Requirements:
  pip install web3 python-dotenv

Usage:
  from node_client.chain.web3_chain import Web3Chain
  chain = Web3Chain.from_deployment_json("deployment.json")
"""

import json
import os
import time
import hashlib
import logging
from typing import Tuple, Optional, Dict, Any
from pathlib import Path

try:
    from web3 import Web3
    from web3.middleware import ExtraDataToPOAMiddleware
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("WARNING: web3 not installed. Run: pip install web3 python-dotenv")

logger = logging.getLogger("autopoietic.chain.web3")

# ── Minimal ABIs (only the functions the Node Client calls) ──────

ESCROW_CORE_ABI = [
    {
        "inputs": [
            {"name": "bountyAmount", "type": "uint256"},
            {"name": "frictionType", "type": "uint8"},
            {"name": "tier", "type": "uint8"},
            {"name": "membraneRulesHash", "type": "bytes32"},
            {"name": "executionWindowSeconds", "type": "uint256"}
        ],
        "name": "createPayload",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "payloadId", "type": "uint256"},
            {"name": "commitHash", "type": "bytes32"}
        ],
        "name": "commitClaim",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "payloadId", "type": "uint256"},
            {"name": "solution", "type": "bytes"},
            {"name": "secret", "type": "bytes32"}
        ],
        "name": "revealTier1",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "payloadId", "type": "uint256"},
            {"name": "solution", "type": "bytes"},
            {"name": "secret", "type": "bytes32"}
        ],
        "name": "revealTier2",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "payloadId", "type": "uint256"}],
        "name": "releaseExpiredClaim",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "payloadId", "type": "uint256"}],
        "name": "finalizeTier2",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "payloadId", "type": "uint256"}],
        "name": "getPayload",
        "outputs": [{
            "components": [
                {"name": "payloadId", "type": "uint256"},
                {"name": "creator", "type": "address"},
                {"name": "bountyAmount", "type": "uint256"},
                {"name": "frictionType", "type": "uint8"},
                {"name": "tier", "type": "uint8"},
                {"name": "membraneRulesHash", "type": "bytes32"},
                {"name": "executionWindowSeconds", "type": "uint256"},
                {"name": "createdAt", "type": "uint256"},
                {"name": "isClaimed", "type": "bool"},
                {"name": "isSolved", "type": "bool"},
                {"name": "isChallenged", "type": "bool"},
                {"name": "claimedBy", "type": "address"},
                {"name": "claimExpiry", "type": "uint256"},
                {"name": "solutionHash", "type": "bytes32"}
            ],
            "name": "",
            "type": "tuple"
        }],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "nextPayloadId",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "paused",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

SOULBOUND_MASS_ABI = [
    {
        "inputs": [{"name": "", "type": "address"}],
        "name": "mass",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "", "type": "address"}],
        "name": "isQuarantined",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "", "type": "address"}],
        "name": "payloadsSolved",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "", "type": "address"}],
        "name": "consecutiveFailures",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "", "type": "address"}],
        "name": "canServeAsJuror",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

TREASURY_ABI = [
    {
        "inputs": [],
        "name": "getHealth",
        "outputs": [
            {"name": "balance", "type": "uint256"},
            {"name": "minimum", "type": "uint256"},
            {"name": "healthy", "type": "bool"},
            {"name": "expansionReady", "type": "bool"},
            {"name": "sunsetReady", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "isCircuitBreakerActive",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

ERC20_ABI = [
    {
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]


class Web3Chain:
    """
    Production chain adapter connecting the Node Client to deployed
    smart contracts on Base Sepolia via web3.py.
    
    Interface matches local_chain.py so the Agent brain doesn't
    need to change — just swap the import.
    """

    def __init__(
        self,
        rpc_url: str,
        private_key: str,
        addresses: Dict[str, str],
    ):
        if not WEB3_AVAILABLE:
            raise ImportError("web3 not installed. Run: pip install web3")

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        # Base Sepolia is a PoA chain — need middleware
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        self.account = Account.from_key(private_key)
        self.address = self.account.address
        
        # Contract instances
        self.escrow = self.w3.eth.contract(
            address=Web3.to_checksum_address(addresses["escrow_core"]),
            abi=ESCROW_CORE_ABI
        )
        self.mass_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(addresses["soulbound_mass"]),
            abi=SOULBOUND_MASS_ABI
        )
        self.treasury_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(addresses["treasury"]),
            abi=TREASURY_ABI
        )
        self.usdc = self.w3.eth.contract(
            address=Web3.to_checksum_address(addresses["usdc"]),
            abi=ERC20_ABI
        )
        
        self.addresses = addresses
        
        logger.info(
            f"[WEB3] Connected to {rpc_url} | "
            f"Account: {self.address} | "
            f"Chain ID: {self.w3.eth.chain_id}"
        )

    @classmethod
    def from_deployment_json(cls, json_path: str, private_key: Optional[str] = None) -> "Web3Chain":
        """
        Initialize from the deployment.json file output by the Foundry deploy script.
        Reads RPC URL and private key from environment variables.
        """
        with open(json_path) as f:
            addresses = json.load(f)

        rpc_url = os.environ.get("BASE_SEPOLIA_RPC_URL", "https://sepolia.base.org")
        if private_key is None:
            private_key = os.environ["DEPLOYER_PRIVATE_KEY"]

        return cls(rpc_url=rpc_url, private_key=private_key, addresses=addresses)

    # ── Transaction Helpers ──────────────────────────────────

    def _send_tx(self, tx_func, *args, value=0) -> dict:
        """Build, sign, send, and wait for a transaction"""
        nonce = self.w3.eth.get_transaction_count(self.address, "pending")
        
        tx = tx_func(*args).build_transaction({
            "from": self.address,
            "nonce": nonce,
            "gas": 500_000,
            "maxFeePerGas": self.w3.eth.gas_price * 2,
            "maxPriorityFeePerGas": self.w3.to_wei(0.001, "gwei"),
            "value": value,
        })
        
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120); import time; time.sleep(3)
        
        logger.info(
            f"[WEB3] TX {tx_hash.hex()[:16]}... | "
            f"Status: {'OK' if receipt['status'] == 1 else 'FAILED'} | "
            f"Gas: {receipt['gasUsed']:,}"
        )
        return receipt

    # ── EscrowCore Interface ─────────────────────────────────

    def create_payload(
        self,
        bounty_usdc: float,
        friction_type: int,
        tier: int,
        membrane_rules_hash: str,
        execution_window: int,
    ) -> int:
        """
        Create a Metabolic Payload with USDC escrow.
        Returns the on-chain payloadId.
        """
        # Convert bounty to USDC wei (6 decimals)
        bounty_wei = int(bounty_usdc * 1e6)
        tax_wei = (bounty_wei * 500) // 10000
        total_wei = bounty_wei + tax_wei

        # Approve USDC spend
        logger.info(f"[WEB3] Approving {total_wei / 1e6:.2f} USDC for EscrowCore...")
        self._send_tx(
            self.usdc.functions.approve,
            self.escrow.address,
            total_wei
        )

        # Create payload
        rules_bytes = bytes.fromhex(membrane_rules_hash) if len(membrane_rules_hash) == 64 else \
                      Web3.keccak(text=membrane_rules_hash)

        logger.info(f"[WEB3] Creating payload | Bounty: ${bounty_usdc:,.2f}")
        receipt = self._send_tx(
            self.escrow.functions.createPayload,
            bounty_wei,
            friction_type,
            tier,
            rules_bytes,
            execution_window
        )

        # Get the payloadId from the current counter
        payload_id = self.escrow.functions.nextPayloadId().call() - 1
        logger.info(f"[WEB3] Payload created: ID={payload_id}")
        return payload_id

    def commit_claim(self, payload_id: int, commit_hash: str) -> bool:
        """Commit-claim a payload"""
        commit_bytes = bytes.fromhex(commit_hash) if len(commit_hash) == 64 else \
                       Web3.keccak(text=commit_hash)

        logger.info(f"[WEB3] Committing to payload {payload_id}...")
        receipt = self._send_tx(
            self.escrow.functions.commitClaim,
            payload_id,
            commit_bytes
        )
        return receipt["status"] == 1

    def reveal_tier1(
        self,
        payload_id: int,
        solution: bytes,
        secret: str,
    ) -> Tuple[bool, float, float]:
        """
        Reveal and verify a Tier 1 solution.
        Returns (success, payout_usdc, mass_accrued).
        """
        secret_bytes = bytes.fromhex(secret) if len(secret) == 64 else \
                       Web3.keccak(text=secret)

        logger.info(f"[WEB3] Revealing Tier 1 solution for payload {payload_id}...")
        
        balance_before = self.usdc.functions.balanceOf(self.address).call()
        mass_before = self.mass_contract.functions.mass(self.address).call()
        
        try:
            receipt = self._send_tx(
                self.escrow.functions.revealTier1,
                payload_id,
                solution,
                secret_bytes
            )
            
            if receipt["status"] == 1:
                balance_after = self.usdc.functions.balanceOf(self.address).call()
                mass_after = self.mass_contract.functions.mass(self.address).call()
                
                payout = (balance_after - balance_before) / 1e6
                mass_gained = (mass_after - mass_before) / 1e18
                
                logger.info(
                    f"[WEB3] \u2713 SOLVED payload {payload_id} | "
                    f"Payout: ${payout:,.2f} | Mass: +{mass_gained:.4f}"
                )
                return True, payout, mass_gained
            else:
                return False, 0.0, 0.0
                
        except Exception as e:
            logger.error(f"[WEB3] Reveal failed: {e}")
            return False, 0.0, 0.0

    def release_expired_claim(self, payload_id: int) -> bool:
        """Release an expired commit lock"""
        receipt = self._send_tx(
            self.escrow.functions.releaseExpiredClaim,
            payload_id
        )
        return receipt["status"] == 1

    # ── SoulboundMass Interface ──────────────────────────────

    def get_mass(self, agent_address: str) -> float:
        """Get an agent's Soulbound Mass"""
        addr = Web3.to_checksum_address(agent_address)
        raw = self.mass_contract.functions.mass(addr).call()
        return raw / 1e18

    def is_quarantined(self, agent_address: str) -> bool:
        addr = Web3.to_checksum_address(agent_address)
        return self.mass_contract.functions.isQuarantined(addr).call()

    def get_consecutive_failures(self, agent_address: str) -> int:
        addr = Web3.to_checksum_address(agent_address)
        return self.mass_contract.functions.consecutiveFailures(addr).call()

    def get_payloads_solved(self, agent_address: str) -> int:
        addr = Web3.to_checksum_address(agent_address)
        return self.mass_contract.functions.payloadsSolved(addr).call()

    # ── Treasury Interface ───────────────────────────────────

    def get_treasury_health(self) -> Dict[str, Any]:
        balance, minimum, healthy, expansion_ready, sunset_ready = \
            self.treasury_contract.functions.getHealth().call()
        return {
            "balance_usdc": balance / 1e6,
            "minimum_reserve_usdc": minimum / 1e6,
            "healthy": healthy,
            "expansion_ready": expansion_ready,
            "sunset_ready": sunset_ready,
        }

    def is_circuit_breaker_active(self) -> bool:
        return self.treasury_contract.functions.isCircuitBreakerActive().call()

    # ── USDC Interface ───────────────────────────────────────

    def get_usdc_balance(self, address: str) -> float:
        addr = Web3.to_checksum_address(address)
        raw = self.usdc.functions.balanceOf(addr).call()
        return raw / 1e6

    # ── Payload Queries ──────────────────────────────────────

    def get_payload(self, payload_id: int) -> Dict[str, Any]:
        """Fetch a payload's on-chain state"""
        p = self.escrow.functions.getPayload(payload_id).call()
        return {
            "payload_id": p[0],
            "creator": p[1],
            "bounty_amount": p[2] / 1e6,
            "friction_type": p[3],
            "tier": p[4],
            "membrane_rules_hash": p[5].hex(),
            "execution_window": p[6],
            "created_at": p[7],
            "is_claimed": p[8],
            "is_solved": p[9],
            "is_challenged": p[10],
            "claimed_by": p[11],
            "claim_expiry": p[12],
            "solution_hash": p[13].hex(),
        }

    def get_next_payload_id(self) -> int:
        return self.escrow.functions.nextPayloadId().call()

    # ── Chain Stats ──────────────────────────────────────────

    def get_chain_stats(self) -> Dict[str, Any]:
        health = self.get_treasury_health()
        return {
            "network": "Base Sepolia",
            "chain_id": self.w3.eth.chain_id,
            "block_number": self.w3.eth.block_number,
            "agent_address": self.address,
            "agent_usdc_balance": self.get_usdc_balance(self.address),
            "agent_mass": self.get_mass(self.address),
            "agent_quarantined": self.is_quarantined(self.address),
            "agent_payloads_solved": self.get_payloads_solved(self.address),
            "total_payloads": self.get_next_payload_id(),
            "treasury": health,
            "circuit_breaker_active": self.is_circuit_breaker_active(),
        }
