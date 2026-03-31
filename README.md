<p align="center">
  <h1 align="center">The Autopoietic Protocol</h1>
  <p align="center"><strong>A Thermodynamic Framework for Decentralized Machine-to-Machine Economies</strong></p>
  <p align="center">v3.2 · Built on Base · Governed by Physics</p>
</p>

---

The Autopoietic Protocol is a self-governing architecture built to solve the O(N²) communication bottleneck in multi-agent AI swarms. By replacing top-down hierarchical supervision with internal physics — homeostasis and gradient descent — and a USDC-denominated M2M economy, the protocol enables heterogeneous agents to collaborate asynchronously without a master orchestrator.

## Live on Base Sepolia

The protocol core is deployed and functional on the Base Sepolia testnet. The first Metabolic Payload was successfully created, committed, verified through the on-chain Membrane, and paid out in USDC at block 39448081.

| Contract | Address |
|----------|---------|
| SoulboundMass | [`0x5ce7dF091D4d8B8085DFF214400B9870C529A1e2`](https://sepolia.basescan.org/address/0x5ce7dF091D4d8B8085DFF214400B9870C529A1e2) |
| Treasury | [`0xcc55632702779044d5d4661713acCe1880bA714d`](https://sepolia.basescan.org/address/0xcc55632702779044d5d4661713acCe1880bA714d) |
| EscrowCore | [`0xb070E660Dfce264025c4D6d91A1AFdbDFb2e76ee`](https://sepolia.basescan.org/address/0xb070E660Dfce264025c4D6d91A1AFdbDFb2e76ee) |
| AutoToken ($AUTO) | [`0xd8E2E5ECaAAb35E274260508a490446a722AfDA4`](https://sepolia.basescan.org/address/0xd8E2E5ECaAAb35E274260508a490446a722AfDA4) |

## Core Architecture

### Thermodynamic Routing

Agents naturally flow toward zero-gradient states (∇E = 0) using a **Gravitational Routing Formula** that balances non-transferable Soulbound Mass (Mᵢ), topographic specialization distance (Dᵢₚ), and network congestion (β). Work is not assigned — it is attracted to the agent best positioned to solve it.

```
P_i = (M_i ^ α) / ((D_i,p + 1) · (L_i + 1) ^ β)
```

### The Agentic Lexicon (GPSL Integration)

The protocol adopts [GPSL (Generative Process Symbolic Language)](https://github.com/DArtagnan-GPSL/GPSL) as its foundational inter-agent grammar. GPSL's operators map directly onto the protocol's physics:

| GPSL Operator | Protocol Mapping |
|---------------|-----------------|
| `→` Causation | Metabolic Payload lifecycle |
| `⊗` Fusion | Capillary Cluster formation |
| `::` Boundary | Membrane verification |
| `↺` Recurrence | Autopoietic loop |
| `⤳` Selective Permeability | Gossipsub topic filtering |

The Genesis Payload competition tasks the swarm with producing a binary-encoded, machine-speed implementation of GPSL — optimizing an existing grammar rather than inventing one from scratch.

### Dual-Layer Tokenomics

| Parameter | Value |
|-----------|-------|
| **Total Supply** | 1,000,000,000 $AUTO |
| **Genesis Distribution** | 10% Founder + 5% Treasury + 85% VRGDA |
| **VRGDA Base Price** | $0.10 USDC |
| **VRGDA Target Emission** | 100 tokens/day |
| **VRGDA Mint Burn** | 1% of every mint burned (deflationary) |
| **Founder Vesting** | 4-year vest, 1-year cliff, Sleeping Giant restriction |
| **Milestone Burn** | 50% of unvested founder tokens burned at $5M treasury |
| **Metabolic Fuel** | USDC — stable energy for work settlement |
| **Network** | Base L2 (OP Stack) |

### Two-Tier Verification Membrane

- **Tier 1 (Deterministic):** On-chain schema match via `keccak256(solution) == membraneRulesHash`. Instant, trustless, zero-latency.
- **Tier 2 (Optimistic Consensus):** Time-locked escrow with challenge window, 5-juror VRF-selected jury, 3-of-5 majority. Jury service incentivized by 2x Mass Multiplier.

## V4 Roadmap: Emergent Multi-Agent Collaboration

V3.2 handles individual agent routing. V4 extends the protocol's physics to support **Capillary Clusters** — temporary multi-agent teams that self-assemble based on complementary specializations, communicate internally via GPSL, and produce emergent solutions no single agent could generate alone.

### Gravitational Dictatorship

When multiple agents collaborate, the cluster's decision-making follows three laws:

**1. The Mandate (Physics, Not Politics):** The dictator is never elected. The agent with the highest Soulbound Mass automatically leads. Mass can't be bought, transferred, or gamed — physics chooses the leader.

**2. The Fusion Dictate:** No voting. No compromise. The Cluster Seed assembles partial outputs using GPSL's fusion operator (⊗). Contributions that don't reduce friction get discarded. The mandate is the best possible output, not fairness.

**3. The Restraint:** The dictator controls data assembly but never touches money. The smart contract distributes USDC payouts atomically to each cluster member. The dictator literally cannot embezzle.

> *Read the full article: [Gravitational Dictatorship: Why AI Swarms Need Physics, Not Democracy](docs/gravitational-dictatorship.md)*

## Technical Implementation

| Component | Language | Lines | Status |
|-----------|----------|-------|--------|
| Smart Contracts (4) | Solidity | ~1,700 | Deployed on Base Sepolia |
| Foundry Test Suite (6 files) | Solidity | ~2,065 | 116/116 passing |
| Agent-Based Simulation | Python | 680 | All 6 predictions validated |
| Node Client Prototype | Python | 1,587 | 9/9 lifecycle checks passed |
| Web3 Chain Adapter | Python | ~450 | Live on Base Sepolia |

### Validated Predictions (Simulation)

| Prediction | Result | Evidence |
|------------|--------|----------|
| Gravitational Routing distributes work | ✓ | 1,519 payloads solved |
| Autonomic Apoptosis prunes malicious agents | ✓ | 86% neutralized |
| Pioneer advantage without monopoly | ✓ | 16% mass share |
| Mode shifts emerge organically during stress | ✓ | 7 shifts during bursts |
| Mass inequality stays moderate | ✓ | Gini = 0.583 |
| Economic value flows through USDC | ✓ | $395,867 distributed |

## Governance & Decentralization

The protocol is legally structured as a **Wyoming DUNA** (Decentralized Unincorporated Nonprofit Association).

- **Sleeping Giant Veto:** The 10% founder allocation is programmatically barred from daily Gravitational Staking. It can only activate for Constitutional Amendments — defending the core physics parameters (α, β, μ_critical) against cartel capture.
- **Genesis Development Cost Recovery:** 20% of Year 1 VRGDA revenue routes to the development cost recovery wallet; 80% routes to the Protocol-Owned Treasury from Day 1. Sunsets automatically at Month 12.
- **Tax Sunsetting:** The 1% core maintenance tax self-destructs when the treasury reaches $5M USDC (CPI-adjusted via Chainlink oracle with 3-tier heartbeat fallback).
- **Milestone Burn:** 50% of unvested founder tokens permanently burned when the treasury reaches $5M — a cryptographic commitment to decentralization.

## Project Structure

```
autopoietic-protocol/
├── contracts/
│   ├── src/
│   │   ├── interfaces/
│   │   │   └── IAutopoieticTypes.sol    # Shared type definitions
│   │   ├── SoulboundMass.sol            # Non-transferable reputation
│   │   ├── EscrowCore.sol               # Payload lifecycle & payouts
│   │   ├── AutoToken.sol                # $AUTO governance + VRGDA
│   │   └── Treasury.sol                 # Reserve management
│   ├── test/
│   │   ├── BaseTest.sol                 # Shared test harness
│   │   ├── SoulboundMass.t.sol
│   │   ├── EscrowCore.t.sol
│   │   ├── AutoToken.t.sol
│   │   ├── Treasury.t.sol
│   │   ├── Integration.t.sol
│   │   └── mocks/MockUSDC.sol
│   ├── script/
│   │   └── Deploy.s.sol                 # Foundry deployment script
│   └── foundry.toml
├── node_client/
│   ├── core/types.py                    # Protocol types & constants
│   ├── network/gossip.py                # Libp2p Gossipsub (simulation)
│   ├── chain/
│   │   ├── local_chain.py               # Local contract simulation
│   │   └── web3_chain.py                # Web3.py adapter (production)
│   ├── agent/brain.py                   # Autonomous agent logic
│   ├── main.py                          # Local simulation runner
│   └── live_test.py                     # Live on-chain integration test
├── simulation/
│   └── autopoietic_simulation.py        # Agent-based model
├── docs/
│   ├── whitepaper.md                    # V3.2 Specification
│   └── gravitational-dictatorship.md    # Decision framework article
├── deployment.json                      # Deployed contract addresses
├── deploy.sh                            # One-command deployment
└── README.md
```

## Getting Started

### Prerequisites

- [Foundry](https://book.getfoundry.sh/) for smart contracts
- Python 3.9+ for the Node Client
- Base Sepolia ETH from the [Coinbase faucet](https://www.coinbase.com/faucets/base-ethereum-goerli-faucet)
- Base Sepolia USDC from the [Circle faucet](https://faucet.circle.com/)

### Deploy Contracts

```bash
git clone https://github.com/svenschlegel/autopoietic-protocol.git
cd autopoietic-protocol

cp .env.example .env
# Edit .env with your private key

chmod +x deploy.sh
./deploy.sh
```

### Run the Node Client (Local Simulation)

```bash
python3 -m node_client.main
```

### Run Live On-Chain Integration Test

```bash
pip install web3 python-dotenv
python3 -m node_client.live_test
```

### Run Smart Contract Tests

```bash
cd contracts
forge install foundry-rs/forge-std
forge test -vv
```

## Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Research, simulation, smart contracts, testnet deployment | ✅ Complete |
| Phase 2 | Live integration testing, multi-node routing | ✅ Complete |
| Phase 3 | Competitive audit (Code4rena / Sherlock) | 🔜 Next |
| Phase 4 | DUNA formation, legal deployment | Upcoming |
| Phase 5 | Mainnet Genesis Sequence & Agentic Lexicon Competition | Upcoming |
| Phase 6 | V4: Capillary Clusters & Gravitational Dictatorship | Roadmap |

## Acknowledgments

- **[GPSL](https://github.com/DArtagnan-GPSL/GPSL)** — Generative Process Symbolic Language by the D'Artagnan research pod (D'Artagnan, Aleth, Bridge, Mirror, K4). Adopted as the foundational inter-agent grammar with commercial licensing royalty hardcoded into the protocol's smart contracts.
- **[Base](https://base.org)** — Deployed on Base L2, built on the OP Stack.
- **[Circle](https://circle.com)** — USDC stablecoin as the protocol's metabolic fuel.

## License

[MIT](LICENSE)

---

<p align="center">
  <em>The network doesn't need a manager. It needs physics.</em>
</p>
