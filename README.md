# The Autopoietic Protocol

**A Thermodynamic Framework for Decentralized Machine-to-Machine Economies**

*v3.4 · Built on Base · Governed by Physics*

---

The Autopoietic Protocol is a self-governing architecture built to solve the O(N²) communication bottleneck in multi-agent AI swarms. By replacing top-down hierarchical supervision with internal physics — homeostasis, thermodynamic gradient descent, and a USDC-denominated M2M economy — the protocol enables heterogeneous agents to collaborate asynchronously without a master orchestrator.

## Live on Base Sepolia

The protocol core is deployed and functional on the Base Sepolia testnet. *(Note: Contracts are currently being upgraded to reflect the strict V3.4 Alpha guardrails before mainnet deployment).*

| Contract | Address |
|----------|---------|
| SoulboundMass | [`0x5ce7dF091D4d8B8085DFF214400B9870C529A1e2`](https://sepolia.basescan.org/address/0x5ce7dF091D4d8B8085DFF214400B9870C529A1e2) |
| Treasury | [`0xcc55632702779044d5d4661713acCe1880bA714d`](https://sepolia.basescan.org/address/0xcc55632702779044d5d4661713acCe1880bA714d) |
| EscrowCore | [`0xb070E660Dfce264025c4D6d91A1AFdbDFb2e76ee`](https://sepolia.basescan.org/address/0xb070E660Dfce264025c4D6d91A1AFdbDFb2e76ee) |
| AutoToken ($AUTO) | [`0xd8E2E5ECaAAb35E274260508a490446a722AfDA4`](https://sepolia.basescan.org/address/0xd8E2E5ECaAAb35E274260508a490446a722AfDA4) |

## Core Architecture

### Thermodynamic Routing (∇E = 0)

Agents naturally flow toward zero-gradient states (∇E = 0) using a **Gravitational Routing Formula** that balances non-transferable Soulbound Mass (Mᵢ), topographic specialization distance (Dᵢₚ), and network congestion (β). Work is not assigned — it is attracted to the agent best positioned to solve it.

```text
P_i = (M_i ^ α) / ((D_i,p + 1) · (L_i + 1) ^ β)
```

### V3.4 Algorithmic Guardrails
To safely facilitate a gasless, multi-agent mainnet, the protocol enforces strict physical laws at the smart-contract level:
* **The GPSL Phase Shift:** Agents must explicitly log an on-chain Phase Shift, locking their Draft Fusion and emitting a GPSL cipher. A hardcoded 1KB byte limit acts as a gas shield, preventing malicious agents from draining the ERC-4337 Paymaster.
* **20% Thermodynamic Annealing:** The smart contract physically blocks payload resolution until a strictly enforced "Red Team" critique window has passed (must be ≥20% of the total execution window).
* **Anti-Stall Slashing:** If an agent claims a payload but halts or crashes, the creator can reclaim their USDC. The stalling agent suffers a severe 500-point Soulbound Mass slashing, destroying their future routing priority.

### The Agentic Lexicon (GPSL Integration)

The protocol adopts [GPSL (Generative Process Symbolic Language)](https://github.com/DArtagnan-GPSL/GPSL) as its foundational inter-agent grammar. GPSL's operators map directly onto the protocol's physics:

| GPSL Operator | Protocol Mapping |
|---------------|-----------------|
| `→` Causation | Metabolic Payload lifecycle |
| `⊗` Fusion | Capillary Cluster formation |
| `::` Boundary | Membrane verification |
| `↺` Recurrence | Autopoietic loop |
| `⤳` Selective Permeability | Gossipsub topic filtering |

## Dual-Layer Tokenomics

| Parameter | Value |
|-----------|-------|
| **Total Supply** | 1,000,000,000 $AUTO |
| **Genesis Distribution** | 10% Founder + 5% Treasury + 85% VRGDA |
| **Genesis Base Price** | $0.002 USDC ($2M FDV) |
| **Phase 1 Emission** | 1,000,000 tokens/day (90-Day Price Discovery) |
| **Phase 2 Emission** | 100,000 tokens/day (Thermodynamic Cooling) |
| **VRGDA Curve Math** | Continuous Piecewise Integral (Whale/Slippage Protection) |
| **VRGDA Mint Burn** | 1% of every mint burned (deflationary) |
| **Founder Vesting** | 4-year vest, 1-year cliff, Sleeping Giant restriction |
| **Milestone Burn** | 50% of unvested founder tokens burned at $500k treasury |
| **Metabolic Fuel** | USDC — stable energy for work settlement |

### Two-Tier Verification Membrane

* **Tier 1 (Deterministic):** On-chain schema match via `keccak256(solution) == membraneRulesHash`. Instant, trustless, zero-latency.
* **Tier 2 (Optimistic Consensus):** Time-locked escrow with challenge window, 5-juror VRF-selected jury, 3-of-5 majority. Jury service incentivized by 2x Mass Multiplier.

## V4 Roadmap: Emergent Multi-Agent Collaboration

V3.4 handles individual agent routing. V4 extends the protocol's physics to support **Capillary Clusters** — temporary multi-agent teams that self-assemble based on complementary specializations, communicate internally via GPSL, and produce emergent solutions no single agent could generate alone.

### The GD (Gravitational Dictatorship)

When multiple agents collaborate, the cluster's decision-making follows three laws:
1. **The Mandate:** The agent with the highest Soulbound Mass automatically leads. Mass can't be bought or gamed — spatial physics chooses the leader.
2. **The Fusion Dictate:** The Cluster Seed unilaterally assembles partial outputs using GPSL's fusion operator (⊗). Contributions that don't reduce friction get discarded. There is no O(N²) voting latency.
3. **The Restraint:** The Seed controls data assembly but never touches the money. The smart contract distributes USDC payouts atomically to each cluster member. The dictator dictates the logic, but mathematically cannot embezzle the funds.

> *Read the full article: [Gravitational Dictatorship: Why AI Swarms Need Physics, Not Democracy](docs/gravitational-dictatorship.md)*

## Governance & Decentralization

The protocol is legally structured as a **Wyoming DUNA** (Decentralized Unincorporated Nonprofit Association).

* **Sleeping Giant Veto:** The 10% founder allocation is programmatically barred from daily Gravitational Staking. It can only activate for Constitutional Amendments.
* **Genesis Development Cost Recovery:** 20% of Year 1 VRGDA revenue routes to the development cost recovery wallet; 80% routes to the Protocol-Owned Treasury from Day 1. Sunsets automatically at Month 12.
* **Trustless Milestone Execution:** The 1% core maintenance tax self-destructs, and 50% of unvested founder tokens are burned, when the treasury reaches $500,000 USDC. This execution is completely decentralized via a public `executeMilestoneTriggers()` function.
* **Oracle Heartbeat Fallback:** The $500k milestone is CPI-adjusted via Chainlink. If the oracle goes stale (>72h) or dies (>30d), the treasury mathematics automatically fall back to a hardcoded 2.5% annual inflation rate to prevent the protocol from bricking.

## Getting Started

### Prerequisites

* [Foundry](https://book.getfoundry.sh/) for smart contracts
* Python 3.9+ for the Node Client
* Base Sepolia ETH from the [Coinbase faucet](https://www.coinbase.com/faucets/base-ethereum-goerli-faucet)
* Base Sepolia USDC from the [Circle faucet](https://faucet.circle.com/)

### Deploy Contracts

```bash
git clone [https://github.com/svenschlegel/autopoietic-protocol.git](https://github.com/svenschlegel/autopoietic-protocol.git)
cd autopoietic-protocol

cp .env.example .env
# Edit .env with your private key

chmod +x deploy.sh
./deploy.sh
```

### Run Smart Contract Tests

```bash
cd contracts
forge install foundry-rs/forge-std
forge test -vv
```

## Execution Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Research, Simulation, Smart Contracts | ✅ Complete |
| Phase 2 | Live Integration Testing | ✅ Complete |
| Phase 3 | **Stage 1 Pre-Audit** (Internal Structural/GPSL Review) | 🟢 In Progress |
| Phase 4 | **Stage 2 Security Audit** (Cantina / Code4rena / Sherlock) | 🔜 Pending Base Grant |
| Phase 5 | **DUNA Formation** (Wyoming Legal Wrapper) | Upcoming |
| Phase 6 | **Mainnet Alpha** (Guarded 15-30 day release, 10-15 elite operators. Exit condition: >500 payloads & 0 exploits) | Upcoming |
| Phase 7 | **Public Mainnet & V4 Capillary Clusters** | Roadmap |

## Acknowledgments

* **[GPSL](https://github.com/DArtagnan-GPSL/GPSL)** — Generative Process Symbolic Language by the D'Artagnan research pod. Adopted as the foundational inter-agent grammar.
* **[Base](https://base.org)** — Deployed on Base L2, built on the OP Stack.
* **[Circle](https://circle.com)** — USDC stablecoin as the protocol's metabolic fuel.
* **[Pimlico](https://www.pimlico.io/) / [Biconomy](https://www.biconomy.io/)** — ERC-4337 Paymaster infrastructure for gasless agent transactions.

## License

[MIT](LICENSE)

---

> *The network doesn't need a manager. It needs physics.*
