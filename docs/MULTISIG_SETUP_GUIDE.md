# Multisig + Timelock Setup Guide
**Last Updated:** 2026-04-02

---

## Overview

The Autopoietic Protocol uses a two-layer admin architecture:

```
┌─────────────────────────────┐
│   2-of-3 Safe Multisig      │  ← Your 3 wallets across 3 devices
│   (Base L2)                  │
└──────────┬──────────────────┘
           │
           ├──── Emergency actions (instant) ──→ pause(), haltVRGDA(), emergencyWithdraw()
           │     via emergencyAdmin role
           │
           └──── Admin actions (48h delay) ───→ Timelock.sol ──→ All other owner functions
                 queue → wait → execute
```

**Emergency functions** (pause, halt, emergency withdraw) go directly from the multisig to the contracts — no delay. These need to be instant to respond to exploits.

**Everything else** (change payout ratios, transfer ownership, update treasury, approve categories, toggle alpha) goes through the 48-hour Timelock. The community can see queued transactions on-chain before they execute.

---

## Step 1: Create 3 Wallets

Generate 3 separate wallets on 3 separate devices:

| Wallet | Device | Storage |
|--------|--------|---------|
| Wallet A | Your primary laptop | Hardware wallet (Ledger/Trezor) or browser wallet |
| Wallet B | Your phone | Mobile wallet (Rainbow, Coinbase Wallet) |
| Wallet C | A separate device (tablet, old phone, second laptop) | Any wallet app |

**Important:**
- Use different seed phrases for each wallet
- Store seed phrase backups in different physical locations
- Never store all 3 seed phrases in the same password manager

---

## Step 2: Create the 2-of-3 Safe on Base

1. Go to https://app.safe.global
2. Connect Wallet A
3. Click "Create New Safe"
4. Network: **Base**
5. Add all 3 wallet addresses as owners
6. Set threshold: **2 of 3**
7. Deploy the Safe

Save the Safe address — this is your `MULTISIG_ADDRESS`.

---

## Step 3: Deploy the Timelock

```bash
cd contracts

# Set your environment
export MULTISIG_ADDRESS=0x...your_safe_address...
export RPC_URL=https://sepolia.base.org  # or mainnet RPC

# Deploy Timelock with Safe as admin
forge create src/Timelock.sol:Timelock \
  --constructor-args $MULTISIG_ADDRESS \
  --rpc-url $RPC_URL \
  --private-key $DEPLOYER_KEY
```

Save the deployed Timelock address — this is your `TIMELOCK_ADDRESS`.

---

## Step 4: Set Emergency Admin on All Contracts

Before transferring ownership, set the multisig as emergencyAdmin so it retains instant access to critical functions.

```bash
# EscrowCore: set emergencyAdmin
cast send $ESCROW_ADDRESS "setEmergencyAdmin(address)" $MULTISIG_ADDRESS \
  --rpc-url $RPC_URL --private-key $DEPLOYER_KEY

# AutoToken: set emergencyAdmin
cast send $AUTOTOKEN_ADDRESS "setEmergencyAdmin(address)" $MULTISIG_ADDRESS \
  --rpc-url $RPC_URL --private-key $DEPLOYER_KEY

# Treasury: set emergencyAdmin
cast send $TREASURY_ADDRESS "setEmergencyAdmin(address)" $MULTISIG_ADDRESS \
  --rpc-url $RPC_URL --private-key $DEPLOYER_KEY
```

---

## Step 5: Transfer Ownership to Timelock

**This is the critical step.** After this, all non-emergency admin actions require a 48-hour delay.

```bash
# Transfer EscrowCore ownership to Timelock
cast send $ESCROW_ADDRESS "transferOwnership(address)" $TIMELOCK_ADDRESS \
  --rpc-url $RPC_URL --private-key $DEPLOYER_KEY

# Transfer AutoToken ownership to Timelock
cast send $AUTOTOKEN_ADDRESS "transferOwnership(address)" $TIMELOCK_ADDRESS \
  --rpc-url $RPC_URL --private-key $DEPLOYER_KEY

# Transfer Treasury ownership to Timelock
cast send $TREASURY_ADDRESS "transferOwnership(address)" $TIMELOCK_ADDRESS \
  --rpc-url $RPC_URL --private-key $DEPLOYER_KEY
```

---

## Step 6: Verify Setup

After transferring ownership, verify:

```bash
# Check ownership transferred
cast call $ESCROW_ADDRESS "owner()" --rpc-url $RPC_URL
# Should return TIMELOCK_ADDRESS

cast call $ESCROW_ADDRESS "emergencyAdmin()" --rpc-url $RPC_URL
# Should return MULTISIG_ADDRESS

cast call $AUTOTOKEN_ADDRESS "owner()" --rpc-url $RPC_URL
# Should return TIMELOCK_ADDRESS

cast call $TREASURY_ADDRESS "owner()" --rpc-url $RPC_URL
# Should return TIMELOCK_ADDRESS
```

---

## How to Use: Emergency Actions

Emergency actions go directly from the Safe UI — no timelock delay.

1. Go to https://app.safe.global
2. Select your Safe
3. Click "New Transaction" → "Contract Interaction"
4. Enter the contract address and call `pause()`, `haltVRGDA()`, or `emergencyWithdraw()`
5. Submit — needs 2 of 3 signers to approve
6. Executes immediately

---

## How to Use: Admin Actions (48h Delay)

Admin actions are queued through the Timelock contract.

### Queue a Transaction

From the Safe UI, call `queueTransaction` on the Timelock:

```
Target:   Timelock address
Function: queueTransaction(address,uint256,bytes,uint256)
Args:
  target: 0x...contract_to_call...
  value:  0
  data:   0x...encoded_function_call...
  eta:    current_timestamp + 172800  (48 hours in seconds)
```

To encode the function call data:
```bash
# Example: update payout ratios to 70/15/15
cast calldata "updatePayoutRatios(uint16,uint16,uint16)" 7000 1500 1500
```

### Execute After 48 Hours

After the delay passes, call `executeTransaction` with the same parameters:

```
Target:   Timelock address
Function: executeTransaction(address,uint256,bytes,uint256)
Args:     (same as queue)
```

### Cancel a Queued Transaction

If you change your mind during the 48-hour window:

```
Target:   Timelock address
Function: cancelTransaction(address,uint256,bytes,uint256)
Args:     (same as queue)
```

---

## Access Control Summary

| Function | Who Can Call | Delay |
|----------|-------------|-------|
| `pause()` / `unpause()` | Multisig (emergencyAdmin) OR Timelock (owner) | Instant via multisig |
| `haltVRGDA()` / `resumeVRGDA()` | Multisig (emergencyAdmin) OR Timelock (owner) | Instant via multisig |
| `emergencyWithdraw()` | Multisig (emergencyAdmin) OR Timelock (owner) | Instant via multisig |
| `updatePayoutRatios()` | Timelock (owner) only | 48 hours |
| `transferOwnership()` | Timelock (owner) only | 48 hours |
| `setTreasury()` | Timelock (owner) only | 48 hours |
| `approveCategory()` | Timelock (owner) only | 48 hours |
| `setOracle()` | Timelock (owner) only | 48 hours |
| `toggleGlobalAlpha()` | Timelock (owner) only | 48 hours |
| `setAlphaCreator/Operator()` | Timelock (owner) only | 48 hours |

---

## Upgrade Path

| Phase | Multisig Composition |
|-------|---------------------|
| **Genesis (now)** | 2-of-3: your 3 wallets across 3 devices |
| **Alpha** | 2-of-3: you + top Alpha operator + Base ecosystem builder |
| **Post-Alpha** | 3-of-5 or higher: DUNA founding members elected by governance |
