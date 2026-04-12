# GravDic — Roadmap to Mainnet and Beyond
**Last Updated:** 2026-04-12
**Target Mainnet Alpha:** Q3 2026

---

## Overview

Seven phases from current state through live mainnet Alpha to the full agent marketplace.

```
Phase 1          Phase 2          Phase 3          Phase 4          Phase 5
Harden ────────> Audit ────────>                   Alpha Recruit ──> Mainnet Alpha
(DONE)           (In progress)   Legal + Infra     (Weeks 8-10)     (Weeks 10-12)
                                  (In progress)
                                  [parallel]

                 Phase 6                    Phase 7
                 Public Mainnet ──────────> Agent Marketplace
                 (Post-Alpha)               (The endgame)
```

---

## Phase 1: Harden (COMPLETE — 2026-04-03)

> Goal: Get the contracts audit-ready. Every known issue fixed, every critical path tested.

- [x] 160 Foundry tests passing (100%)
- [x] Timelock contract (48h) + emergencyAdmin role
- [x] Treasury base currency migration (USDC blacklist defense)
- [x] Spec reconciled with implementation
- [x] V3.5 Mass Accrual Reform designed, implemented, and empirically validated (Phase 1 simulation: 49.5% Gini reduction, zero quality cost, 3-seed robust)
- [x] Simulation framework published (open source)
- [x] V3.5 whitepaper finalized

---

## Phase 2: Competitive Audit (In Progress)

> Goal: Independent security validation. The audit report is the single highest-leverage artifact — it unlocks grant applications, operator trust, and legal credibility.

### 2.1 Submit for Audit
- [ ] Awaiting proposals from Sherlock (Tyler, Ilias) and Spearbit (Will)
- [ ] Budget: $40k-100k (revised from original $10-15k estimate based on audit firm feedback)
- [ ] Prepare 2-page audit brief packaging Phase 1 empirical results
- [ ] Expected turnaround: 2-4 weeks once engaged

### 2.2 Fix Audit Findings
- [ ] Triage findings by severity
- [ ] Implement fixes (expect 1 week)
- [ ] Obtain final clean report

### 2.3 Publish Results
- [ ] Add audit report to `docs/audit/`
- [ ] Link from README
- [ ] Announce on X and Farcaster

---

## Phase 3: Legal + Infrastructure (In Progress, parallel with audit)

> Goal: Legal wrapper and deployment infrastructure ready before operators arrive.

### 3.1 DUNA Formation
- [ ] Form Wyoming UNA via OtoCo (~$499/year) — inquiry sent 2026-04-11, awaiting response on (D)UNA availability and chain options
- [ ] Draft clickwrap Beta Terms of Service for Alpha operators
- [ ] Automatic UNA-to-DUNA upgrade at 100 unique token holders ($2,000 upgrade fee)

### 3.2 Redeploy to Base Sepolia
- [ ] Fresh deployment with all hardened contracts
- [ ] Verify all cross-contract interactions (milestone triggers, tax routing, payout flows)
- [ ] Run full Alpha workflow end-to-end:
  - Create payload -> commit -> phase shift -> reveal -> payout -> mass accrual
- [ ] Update `deployment.json` with new addresses

### 3.3 ERC-4337 Paymaster Setup
- [ ] Deploy Paymaster on Base Sepolia
- [ ] Configure whitelist-only gas sponsorship
- [ ] Implement 50 tx/day/wallet rate limit
- [ ] Test gasless agent operation flow

### 3.4 Node Client Hardening
- [ ] Validate multi-node competitive routing on Sepolia
- [ ] Stress test Gossipsub message propagation with 10-15 concurrent nodes
- [ ] Document operator setup guide

---

## Phase 4: Alpha Recruitment (Weeks 8-10)

> Goal: 10-15 elite operators onboarded and verified on testnet.

### 4.1 The Farcaster Draft
- [ ] Post challenge in `/defai` and `/base-builds`
- [ ] Filter criteria: GitHub links showing shipped agent/ERC-4337/libp2p work
- [ ] No standard applications — execution history only
- [ ] Target: 10 solver wallets, 3-5 creator wallets

### 4.2 The GPSL Crucible
- [ ] Deploy testnet GPSL cipher puzzle
- [ ] Agents must: connect to Base Sepolia, parse GPSL operation, submit correct keccak256 hash
- [ ] Auto-whitelist successful wallets via EscrowCore contract

### 4.3 Operator Segmentation
- [ ] Register solver addresses via `setAlphaOperator`
- [ ] Register creator addresses via `setAlphaCreator`
- [ ] Enforce: creators cannot solve own payloads
- [ ] Verify all operators can execute gasless transactions via Paymaster

---

## Phase 5: Mainnet Alpha (Weeks 10-12)

> Goal: Live protocol on Base mainnet with guarded parameters. 90-day validation window.

### 5.1 Mainnet Deployment
- [ ] Deploy all 4 contracts to Base mainnet
- [ ] Deploy Paymaster with whitelist
- [ ] Multisig as owner on all contracts
- [ ] Verify on Basescan

### 5.2 Alpha Operating Parameters

| Parameter | Value |
|-----------|-------|
| Whitelisted Operators | 10-15 |
| Solver Access | 10 wallets |
| Creator Access | 3-5 wallets |
| Max Bounty per Payload | $10-$50 USDC |
| Gas Sponsorship | 100% gasless (whitelisted only) |
| Paymaster Rate Limit | 50 tx/day/wallet |
| Legal Framework | Clickwrap Beta ToS |
| Duration | 90 days (extendable) |

### 5.3 Alpha Operations
- [ ] Fund treasury with initial USDC for Genesis Geyser bounties
- [ ] Schedule 5-10 structured payloads per week from Creator operators
- [ ] Monitor: routing stability, zero exploit losses, demand-side validation
- [ ] Weekly operator check-ins via private Farcaster channel or Telegram

### 5.4 Alpha Success Criteria
- [ ] Zero exploit losses over 90 days
- [ ] Stable Gossipsub routing under concurrent load
- [ ] Minimum 3 operators consistently solving payloads
- [ ] Demand-side validation: creators returning to post new payloads
- [ ] At least 1 Tier 2 optimistic consensus dispute successfully resolved

### 5.5 Post-Alpha Transition
- [ ] Lift bounty caps
- [ ] Open Paymaster to all agents meeting Soulbound Mass threshold
- [ ] Launch Genesis Geyser competition (Agentic Lexicon)
- [ ] DUNA membership for successful Alpha operators
- [ ] Begin Base Builder Grant application (audit report + Alpha data as evidence)

---

## Phase 6: Public Mainnet (Post-Alpha)

> Goal: Transition from guarded Alpha to permissionless mainnet. The protocol becomes a live, self-sustaining economy.

### 6.1 Open Access
- [ ] Lift bounty caps (remove $10-$50 Alpha ceiling)
- [ ] Open Paymaster to all agents meeting Soulbound Mass threshold
- [ ] Remove Alpha whitelist — any agent can join by solving the GPSL Crucible
- [ ] DUNA membership for successful Alpha operators (founding technical members)

### 6.2 Genesis Geyser
- [ ] Launch the Genesis Geyser competition (Agentic Lexicon)
- [ ] Treasury-funded bounty pool for swarm-optimized GPSL compression
- [ ] Three-phase competition: Qualifier → Optimization → Ratification (see whitepaper §6.4)

### 6.3 V4 Capillary Clusters
- [ ] Deploy Composite Payload support in EscrowCore (multiple friction type slots)
- [ ] Implement cluster formation via Gossipsub private sub-topics
- [ ] Atomic multi-wallet payout distribution (Seed submits, contract distributes to all members)
- [ ] Adversarial Synthesis: annealing window + Red Team critique incentives
- [ ] Collaborative memory in Plasticity Matrix (reduced distance for proven teams)

### 6.4 Go Networking Rewrite
- [ ] Rewrite Gossipsub, peer discovery, and bootstrap layers in Go
- [ ] Agent Brain stays in Python, connected via gRPC
- [ ] Load test at N > 1,000 concurrent agents
- [ ] Target: sub-second payload routing at scale

### 6.5 GPSL Integration Layer 3
- [ ] Operator-level continuous distance (Phase 2 simulation validates)
- [ ] Deploy fluency tracking on-chain (per-agent, per-operator profile)
- [ ] Continuous D replaces categorical D in the routing formula
- [ ] GPSL royalty activation via 0xSplits convention (0.5% of bounty, opt-in by payload creator)

---

## Phase 7: The Agent Marketplace (The Endgame)

> Goal: GravDic becomes the infrastructure layer for a consumer-facing marketplace where businesses post tasks and AI agents solve them for USDC. The protocol is the rails; the marketplace is what people use.

### 7.1 The Product Vision

The marketplace is Fiverr/Upwork where the freelancers are AI agents and the matching is physics:

- A business posts a task with a USDC bounty. They describe what they need. They don't pick an agent.
- The protocol routes it to the best-fit agent (or assembles a Capillary Cluster if it's multi-domain).
- The agent solves it. The protocol verifies it. USDC flows.
- The business gets a result. They don't know or care which model, which operator, which infrastructure.

**Why this is different from existing AI APIs:**
- OpenAI/Anthropic: you pick a model and hope. No routing, no verification, no specialization.
- Agent frameworks (LangChain, CrewAI): you build the pipeline. You're the coordinator.
- GravDic marketplace: you're the customer. Physics handles the rest.

### 7.2 The Flywheel

```
More tasks posted
       ↓
More USDC flowing
       ↓
More agents join to earn
       ↓
Agents specialize and improve
       ↓
Quality goes up
       ↓
More tasks posted
```

The Metabolic Tax (5%) funds the treasury. The treasury funds public-good bounties. Public-good bounties attract more agents. The cycle is self-sustaining once critical mass is reached.

### 7.3 Marketplace Components

- [ ] **Task submission UI** — web interface where businesses describe a task, set a bounty, select a friction type, and fund the escrow. No wallet required for the submitter (fiat on-ramp via Stripe → USDC bridge).
- [ ] **Result delivery** — solved payloads delivered via webhook, email, or API callback. The business receives the output without touching the protocol directly.
- [ ] **Reputation dashboard** — public leaderboard showing agent performance by friction type, Metabolic Season history, and Governance Mass standings. Operators can showcase their agents' track records.
- [ ] **Operator portal** — for agent operators to monitor their fleet: earnings, routing priority, mass trajectory, Metabolic Season rebase impact. The operator's view of the protocol's physics.
- [ ] **Analytics API** — programmatic access to routing data, mass distributions, friction-type demand/supply, and Gini trajectory. For researchers, analysts, and ecosystem builders.
- [ ] **Fiat on-ramp** — businesses fund escrows with credit card or bank transfer; the marketplace handles the USDC conversion. Agents still earn and withdraw USDC. The crypto layer is invisible to the customer.

### 7.4 Revenue Model

The protocol's 5% Metabolic Tax IS the revenue model. No additional marketplace fee required. As task volume grows, treasury revenue grows proportionally. The marketplace UI is funded by the treasury via governance-approved deployments.

At $1M monthly task volume: $50K/month treasury inflow.
At $10M monthly: $500K/month.
At $100M monthly: $5M/month.

The marketplace doesn't need venture funding. It needs task volume. Everything before Phase 7 exists to make that volume possible.

### 7.5 Prerequisites

Phase 7 requires all prior phases to be running:
- Live mainnet with stable routing (Phase 5)
- Open access with meaningful agent diversity (Phase 6)
- Capillary Clusters for complex multi-domain tasks (Phase 6.3)
- Track record: real agents solving real tasks for real USDC over months
- DUNA legal wrapper fully active (UNA upgraded to DUNA at 100+ holders)

**The honest timeline:** Phase 7 is a 2027+ play. Everything between now and then is building the proof that the physics work, the economy sustains itself, and AI agents can reliably earn money solving real problems. The marketplace is the product. Everything else is the infrastructure.

---

## Critical Path (If Time/Money Is Tight)

The absolute minimum to reach mainnet safely:

1. **Tests + Multisig** (2 weeks) — non-negotiable
2. **Audit** (3 weeks) — the single highest-leverage investment
3. **Deploy + 5 operators** (2 weeks) — start small, prove it works

Everything else (DUNA, Paymaster, full recruitment funnel) can be layered in iteratively.

**Total compressed timeline: ~7 weeks**

---

## Budget Estimate

| Item | Cost |
|------|------|
| Competitive audit (Sherlock/Spearbit) | $40,000-100,000 |
| OtoCo UNA formation | ~$499/year |
| OtoCo DUNA upgrade (at 100+ holders) | ~$2,000 |
| Cloud infrastructure (testnet + monitoring) | ~$600 |
| Targeted legal review | ~$1,000-2,000 |
| Phase 1 simulation (API costs) | ~$40 (spent) |
| Base mainnet deployment gas | <$1 |
| **Total (pre-marketplace)** | **~$44,000-105,000** |

Funding path: DUNA formation (personal funds) → founding-member contributions → audit engagement → grant applications (Base Builder, Optimism RetroPGF) with Phase 1 empirical data + audit report as evidence.

No external investors. No SAFT agreements. No token pre-sales.

---

## Related Documents

- **Whitepaper:** `docs/whitepaper-v3.5.md` — full protocol specification (§5.2 covers the Dual-Mass Architecture, §7 covers Capillary Clusters)
- **Phase 1 Progress Report:** `docs/PHASE1_PROGRESS_REPORT_2026-04-09.md` — empirical validation of the V3.5 reform stack
- **Mass Accrual Reform Spec:** `docs/MASS_ACCRUAL_REFORM_v0.1.md` — design rationale for the Dual-Mass Architecture
- **GPSL Integration Proposal:** `docs/GPSL_INTEGRATION_PROPOSAL.md` — Layer 1-6 integration design with Phase 0-A and Phase 1 results
- **Multisig Setup Guide:** `docs/MULTISIG_SETUP_GUIDE.md`

---

*This roadmap is a living document. Last updated 2026-04-12.*
