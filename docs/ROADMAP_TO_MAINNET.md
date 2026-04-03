# Autopoietic Protocol — Roadmap to Mainnet
**Last Updated:** 2026-04-02
**Target Mainnet Alpha:** Q3 2026 (~12 weeks from now)

---

## Overview

Five phases from current state to live mainnet Alpha on Base. Estimated 12 weeks total, with Phases 2 and 3 running in parallel.

```
Phase 1          Phase 2          Phase 3          Phase 4          Phase 5
Harden ────────> Audit ────────>                   Alpha Recruit ──> Mainnet Alpha
(Weeks 1-3)      (Weeks 4-7)     Legal + Infra     (Weeks 8-10)     (Weeks 10-12)
                                  (Weeks 5-8)
                                  [parallel]
```

---

## Phase 1: Harden (Weeks 1-3)

> Goal: Get the contracts audit-ready. Every known issue fixed, every critical path tested.

### 1.1 Close Test Coverage Gaps
- [ ] Add tests for `reclaimBounty` (zero coverage — critical anti-stall mechanism)
- [ ] Add tests for `slashMass` (newly implemented, zero coverage)
- [ ] Add tests for `sunsetCoreContributorTax` called by Treasury address
- [ ] Add adversarial tests: reentrancy attempts, pause-bypass attempts
- [ ] Add VRGDA edge case tests: day 0, day 90 phase boundary, day 91, max supply approach
- [ ] Target: ~160+ tests (currently 116)

### 1.2 Implement Timelock + Multisig
- [ ] Deploy a 2-of-3 Safe multisig (architect + 2 trusted technical partners)
- [ ] Add 48-hour timelock on non-emergency `onlyOwner` functions:
  - `updatePayoutRatios`, `setTreasury`, `transferOwnership`, `setOracle`, `approveCategory`
- [ ] Keep immediate multisig access on emergency functions:
  - `pause`, `haltVRGDA`, `emergencyWithdraw`
- [ ] Transfer ownership of all contracts to multisig

### 1.3 Resolve USDC Blacklist Risk
- [ ] Decide: implement `migrateToken` escape hatch OR document as accepted risk
- [ ] If implementing: add `migrateStablecoin(address newToken)` to Treasury and EscrowCore
- [ ] Add to README under "Known Assumptions & Risks"

### 1.4 Reconcile Spec vs Implementation
- [ ] Decide scope for Metabolic Tax routing (GPSL royalty, commercial/public-good split)
  - Option A: Implement in contracts to match whitepaper
  - Option B: Update whitepaper to match current contract (simpler flat split)
- [ ] Document 18-year VRGDA timeline as intentional governance defense in README
- [ ] Reconcile `$500K` base threshold in contract vs `$1M` referenced in whitepaper/README

---

## Phase 2: Competitive Audit (Weeks 4-7)

> Goal: Independent security validation. The audit report is the single highest-leverage artifact — it unlocks grant applications, operator trust, and legal credibility.

### 2.1 Submit for Audit
- [ ] Select platform: Code4rena or Sherlock
- [ ] Budget: $10-15k
- [ ] Submit after all Phase 1 items are complete (don't waste audit dollars on known issues)
- [ ] Expected turnaround: 2-3 weeks

### 2.2 Fix Audit Findings
- [ ] Triage findings by severity
- [ ] Implement fixes (expect 1 week)
- [ ] Obtain final clean report

### 2.3 Publish Results
- [ ] Add audit report to `docs/audit/`
- [ ] Link from README
- [ ] Announce on X and Farcaster

---

## Phase 3: Legal + Infrastructure (Weeks 5-8, parallel with audit)

> Goal: Legal wrapper and deployment infrastructure ready before operators arrive.

### 3.1 DUNA Formation
- [ ] Form Wyoming DUNA via OtoCo on Base L2 (~$500)
- [ ] Draft clickwrap Beta Terms of Service for Alpha operators
- [ ] Automatic UNA-to-DUNA upgrade at 100 unique token holders

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
| Competitive audit (Code4rena/Sherlock) | $10,000-15,000 |
| OtoCo DUNA formation | ~$500 |
| Cloud infrastructure (testnet + monitoring) | ~$600 |
| Targeted legal review | ~$1,000-2,000 |
| Base mainnet deployment gas | <$1 |
| **Total** | **~$12,000-18,000** |

No external investors. No SAFT agreements. No token pre-sales.

---

*This roadmap is a living document. Updated as milestones are completed.*
