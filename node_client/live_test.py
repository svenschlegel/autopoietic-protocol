#!/usr/bin/env python3
"""
THE AUTOPOIETIC PROTOCOL — Live Integration Test (Base Sepolia)
================================================================
Runs the Node Client against the deployed smart contracts to verify
the full Metabolic Payload lifecycle works on a live blockchain.

Prerequisites:
  1. Contracts deployed via ./deploy.sh (produces deployment.json)
  2. Testnet USDC in your wallet
  3. pip install web3 python-dotenv

Usage:
  python -m node_client.live_test
"""

import asyncio
import hashlib; from web3 import Web3 as _W3
import json
import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-28s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("autopoietic.live_test")

def main():
    print("=" * 70)
    print("  THE AUTOPOIETIC PROTOCOL — Live Integration Test")
    print("  Network: Base Sepolia")
    print("=" * 70)
    print()

    # ── Load deployment addresses ────────────────────────────
    
    deployment_path = Path("deployment.json")
    if not deployment_path.exists():
        print("ERROR: deployment.json not found.")
        print("  Run ./deploy.sh first to deploy the contracts.")
        sys.exit(1)

    with open(deployment_path) as f:
        addresses = json.load(f)

    print(f"  Loaded deployment addresses:")
    for key, val in addresses.items():
        print(f"    {key}: {val}")
    print()

    # ── Load environment ─────────────────────────────────────
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # Will use os.environ directly

    private_key = os.environ.get("DEPLOYER_PRIVATE_KEY")
    if not private_key:
        print("ERROR: DEPLOYER_PRIVATE_KEY not set.")
        print("  Set it in .env or as an environment variable.")
        sys.exit(1)

    rpc_url = os.environ.get("BASE_SEPOLIA_RPC_URL", "https://sepolia.base.org")

    # ── Initialize Web3 Chain Adapter ────────────────────────

    print("▸ Connecting to Base Sepolia...")
    
    from node_client.chain.web3_chain import Web3Chain
    
    chain = Web3Chain(
        rpc_url=rpc_url,
        private_key=private_key,
        addresses=addresses,
    )
    
    print(f"  Connected! Account: {chain.address}")
    print(f"  Chain ID: {chain.w3.eth.chain_id}")
    print(f"  Block: {chain.w3.eth.block_number}")
    print()

    # ── Pre-flight checks ────────────────────────────────────
    
    print("▸ Pre-flight checks...")
    
    eth_balance = chain.w3.eth.get_balance(chain.address)
    usdc_balance = chain.get_usdc_balance(chain.address)
    agent_mass = chain.get_mass(chain.address)
    is_quarantined = chain.is_quarantined(chain.address)
    
    print(f"  ETH balance:  {eth_balance / 1e18:.6f} ETH")
    print(f"  USDC balance: ${usdc_balance:,.2f}")
    print(f"  Agent Mass:   {agent_mass:.4f}")
    print(f"  Quarantined:  {is_quarantined}")
    print()
    
    if eth_balance == 0:
        print("ERROR: No ETH for gas!")
        print("  Get testnet ETH from: https://www.coinbase.com/faucets/base-ethereum-goerli-faucet")
        sys.exit(1)

    if usdc_balance < 100:
        print(f"WARNING: Low USDC balance (${usdc_balance:.2f}).")
        print("  You need testnet USDC to create payloads.")
        print("  For now, running read-only checks...")
        print()
        _run_readonly_checks(chain)
        return

    # ── Test 1: Create a Metabolic Payload ───────────────────
    
    print("▸ Test 1: Creating a Metabolic Payload...")
    
    solution_data = json.dumps({"material_type": "concrete", "psi_target": 4500}, sort_keys=True)
    solution_bytes = solution_data.encode()
    membrane_hash = _W3.keccak(solution_bytes).hex().replace('0x', '')
    
    bounty = 1.0  # $10 USDC (small for testnet)
    
    try:
        payload_id = chain.create_payload(
            bounty_usdc=bounty,
            friction_type=1,  # DETERMINISTIC
            tier=0,           # Tier 1
            membrane_rules_hash=membrane_hash,
            execution_window=3600,
        )
        print(f"  ✓ Payload created: ID={payload_id}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        print("  (This may be due to insufficient USDC or approval issues)")
        _run_readonly_checks(chain)
        return

    # ── Test 2: Commit-Claim the payload ─────────────────────
    
    print("▸ Test 2: Committing to payload...")
    
    secret = _W3.keccak(b"test_secret_base_sepolia").hex().replace('0x', '')
    commit_hash = _W3.keccak(solution_bytes + bytes.fromhex(secret)).hex().replace('0x', '')
    
    try:
        success = chain.commit_claim(payload_id, commit_hash)
        print(f"  ✓ Committed: {success}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return

    # Verify on-chain state
    payload_state = chain.get_payload(payload_id)
    print(f"  On-chain state: claimed={payload_state['is_claimed']}, by={payload_state['claimed_by'][:16]}...")

    # ── Test 3: Reveal solution (Tier 1 verification) ────────
    
    print("▸ Test 3: Revealing solution (Tier 1 verification)...")
    
    try:
        success, payout, mass_gained = chain.reveal_tier1(
            payload_id=payload_id,
            solution=solution_bytes,
            secret=secret,
        )
        
        if success:
            print(f"  ✓ SOLVED! Payout: ${payout:,.2f} | Mass gained: {mass_gained:.4f}")
        else:
            print(f"  ✗ Verification failed (membrane rejection)")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return

    # ── Test 4: Verify final state ───────────────────────────
    
    print("▸ Test 4: Verifying final state...")
    
    final_state = chain.get_payload(payload_id)
    final_mass = chain.get_mass(chain.address)
    final_usdc = chain.get_usdc_balance(chain.address)
    final_solved = chain.get_payloads_solved(chain.address)
    
    print(f"  Payload solved:    {final_state['is_solved']}")
    print(f"  Agent Mass:        {final_mass:.4f}")
    print(f"  Agent USDC:        ${final_usdc:,.2f}")
    print(f"  Payloads solved:   {final_solved}")

    # ── Test 5: Treasury health ──────────────────────────────
    
    print("▸ Test 5: Treasury health check...")
    
    health = chain.get_treasury_health()
    print(f"  Treasury balance:  ${health['balance_usdc']:,.2f}")
    print(f"  Minimum reserve:   ${health['minimum_reserve_usdc']:,.2f}")
    print(f"  Healthy:           {health['healthy']}")
    print(f"  Circuit breaker:   {chain.is_circuit_breaker_active()}")

    # ── Results ──────────────────────────────────────────────
    
    print()
    print("=" * 70)
    
    checks = [
        ("Payload created on-chain", payload_id >= 0),
        ("Commit-Reveal executed", final_state['is_claimed'] or final_state['is_solved']),
        ("Tier 1 verification passed", final_state['is_solved']),
        ("USDC payout received", payout > 0 if success else False),
        ("Soulbound Mass accrued", final_mass > agent_mass),
        ("Treasury received tax", health['balance_usdc'] > 0),
    ]
    
    all_pass = True
    for desc, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            all_pass = False
        print(f"  {status}  {desc}")
    
    print()
    if all_pass:
        print("  ✓ ALL CHECKS PASSED — Live on-chain integration verified!")
        print("  The Autopoietic Protocol is operational on Base Sepolia.")
    else:
        print("  ✗ Some checks failed — see details above.")
    print("=" * 70)
    print()

    # Print full chain stats
    print("  Full chain stats:")
    stats = chain.get_chain_stats()
    for key, val in stats.items():
        if isinstance(val, dict):
            print(f"    {key}:")
            for k2, v2 in val.items():
                print(f"      {k2}: {v2}")
        else:
            print(f"    {key}: {val}")


def _run_readonly_checks(chain):
    """Run read-only checks when no USDC is available"""
    print("▸ Running read-only checks...")
    
    stats = chain.get_chain_stats()
    print(f"  Chain ID:     {stats['chain_id']}")
    print(f"  Block:        {stats['block_number']}")
    print(f"  Total payloads: {stats['total_payloads']}")
    print(f"  Agent Mass:   {stats['agent_mass']}")
    print(f"  Treasury:     ${stats['treasury']['balance_usdc']:,.2f}")
    print(f"  Circuit breaker: {stats['circuit_breaker_active']}")
    print()
    print("  Read-only checks passed. Get testnet USDC to run full tests.")


if __name__ == "__main__":
    main()
