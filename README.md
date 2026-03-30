# The Autopoietic Protocol — Base Sepolia Deployment Kit

## What's in this kit

```
deploy_kit/
├── deploy.sh                    # One-command deploy script
├── .env.example                 # Environment template
├── deployment.json              # (generated) Contract addresses
├── contracts/
│   ├── foundry.toml             # Foundry config
│   ├── src/
│   │   ├── interfaces/
│   │   │   └── IAutopoieticTypes.sol
│   │   ├── SoulboundMass.sol    # Non-transferable reputation
│   │   ├── EscrowCore.sol       # Payload lifecycle & payouts
│   │   ├── AutoToken.sol        # $AUTO governance + VRGDA
│   │   └── Treasury.sol         # Reserve management
│   ├── test/
│   │   ├── BaseTest.sol         # Shared test harness
│   │   ├── SoulboundMass.t.sol  # 13 tests
│   │   ├── EscrowCore.t.sol     # 22 tests
│   │   ├── AutoToken.t.sol      # 19 tests
│   │   ├── Treasury.t.sol       # 16 tests
│   │   ├── Integration.t.sol    # 8 end-to-end scenarios
│   │   └── mocks/MockUSDC.sol
│   └── script/
│       └── Deploy.s.sol         # Foundry deployment script
└── node_client/
    ├── core/types.py            # Shared protocol types
    ├── network/gossip.py        # Libp2p Gossipsub (sim)
    ├── chain/
    │   └── web3_chain.py        # Web3.py adapter (LIVE)
    ├── agent/brain.py           # Autopoietic agent logic
    └── live_test.py             # Live integration test
```

## Quick Start (5 minutes)

### 1. Get testnet ETH

You need Base Sepolia ETH for gas fees.
- Go to https://www.coinbase.com/faucets/base-ethereum-goerli-faucet
- Or use https://faucet.quicknode.com/base/sepolia

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — paste your wallet private key
```

### 3. Deploy

```bash
chmod +x deploy.sh
./deploy.sh
```

This will:
- Install Foundry (if needed)
- Compile all 4 contracts
- Run 78 tests
- Deploy to Base Sepolia
- Output `deployment.json` with all addresses

### 4. Run the live test

```bash
pip install web3 python-dotenv
python -m node_client.live_test
```

This creates a real Metabolic Payload on-chain, commits, reveals,
verifies via the Membrane, receives a USDC payout, and accrues
Soulbound Mass — all on a live blockchain.

## Manual deployment (if you prefer)

```bash
cd contracts

# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Install forge-std
forge install foundry-rs/forge-std --no-commit

# Compile
forge build

# Test
forge test -vvv

# Deploy
forge script script/Deploy.s.sol:DeployAutopoietic \
  --rpc-url https://sepolia.base.org \
  --private-key YOUR_PRIVATE_KEY \
  --broadcast

# Verify on BaseScan (optional)
forge verify-contract ADDRESS src/SoulboundMass.sol:SoulboundMass \
  --chain base-sepolia \
  --etherscan-api-key YOUR_BASESCAN_KEY
```

## Contract addresses

After deployment, `deployment.json` contains:

```json
{
  "network": "base_sepolia",
  "usdc": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
  "soulbound_mass": "0x...",
  "treasury": "0x...",
  "escrow_core": "0x...",
  "auto_token": "0x...",
  "architect": "0x..."
}
```

## Getting testnet USDC

Base Sepolia uses Circle's testnet USDC at:
`0x036CbD53842c5426634e7929541eC2318f3dCF7e`

To get testnet USDC:
1. Go to https://faucet.circle.com/
2. Select "Base Sepolia"
3. Enter your wallet address
4. Receive testnet USDC

## Architecture

```
┌─────────────────┐     Gossipsub      ┌─────────────────┐
│   Node Client   │◄──────────────────►│   Node Client   │
│   (Agent A)     │     /autopoiesis/  │   (Agent B)     │
│                 │     payload/...    │                 │
│  ┌───────────┐  │                    │  ┌───────────┐  │
│  │ Agent     │  │                    │  │ Agent     │  │
│  │ Brain     │  │                    │  │ Brain     │  │
│  └─────┬─────┘  │                    │  └─────┬─────┘  │
│        │        │                    │        │        │
│  ┌─────▼─────┐  │                    │  ┌─────▼─────┐  │
│  │ Web3      │  │                    │  │ Web3      │  │
│  │ Chain     │  │                    │  │ Chain     │  │
│  │ Adapter   │  │                    │  │ Adapter   │  │
│  └─────┬─────┘  │                    │  └─────┬─────┘  │
└────────┼────────┘                    └────────┼────────┘
         │           Base Sepolia L2            │
    ┌────▼──────────────────────────────────────▼────┐
    │  ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
    │  │ Escrow   │ │ Soulbound│ │  Auto        │   │
    │  │ Core     │ │ Mass     │ │  Token       │   │
    │  │(Membrane)│ │ (SBT)    │ │  (VRGDA)     │   │
    │  └────┬─────┘ └──────────┘ └──────────────┘   │
    │       │                                        │
    │  ┌────▼─────┐                                  │
    │  │ Treasury │                                  │
    │  │ (USDC)   │                                  │
    │  └──────────┘                                  │
    └────────────────────────────────────────────────┘
```

## What's next after deployment

1. **Run multiple Node Clients** — Start 2-3 agents with different
   specializations to test Gravitational Routing competition
2. **Test Tier 2 consensus** — Create subjective payloads and test
   the challenge/jury mechanism
3. **Apply for Base Builder Grant** — Use the deployed testnet as
   evidence of shipped code
4. **Competitive audit** — Submit to Code4rena or Sherlock
5. **Mainnet Genesis** — Deploy to Base mainnet and execute the
   Genesis Geyser
