# Autopoietic Protocol V3.4 — Progress Report
**Date:** 2026-04-02
**Phase:** 3 — Multi-node testing, whitepaper polish, pre-audit hardening

---

## 1. Executive Summary

A comprehensive security review of the Autopoietic Protocol V3.4 smart contracts was conducted, combining an initial automated audit with an independent external critique. The process identified **6 critical bugs, 5 high-severity issues, and 4 medium-severity items**. Eight fixes have been implemented and submitted as PR #1. All 116 existing Foundry tests continue to pass.

---

## 2. Security Review Findings

### 2.1 Critical — Smart Contract Bugs (Fixed in PR #1)

| # | Bug | Impact | Status |
|---|-----|--------|--------|
| 1 | `_resolveChallenge` reads `pl.claimedBy` after zeroing it | Solver escapes reputation penalty on rejected challenges | **Fixed** |
| 2 | `reclaimBounty` checks `createdAt + window` instead of `claimExpiry` | Creator can reclaim USDC while agent is still within commit window | **Fixed** |
| 3 | `sunsetCoreContributorTax` restricted to `onlyOwner` | Treasury cannot call it — milestone triggers permanently broken | **Fixed** |
| 4 | `slashMass` not implemented in SoulboundMass | Every `reclaimBounty` call reverts — anti-stall mechanism non-functional | **Fixed** |
| 5 | README states 25% milestone burn; contract and whitepaper specify 50% | Documentation inconsistency confuses investors/auditors | **Fixed** |
| 6 | Juror reward rounding dust locked in contract | `challengeBond / 5` remainder permanently inaccessible | **Fixed** |

### 2.2 High — Architecture Issues (Fixed in PR #1)

| # | Issue | Impact | Status |
|---|-------|--------|--------|
| 7 | No reentrancy protection on EscrowCore or Treasury | If USDC ever adds transfer hooks, contracts could be drained | **Fixed** |
| 8 | Incomplete `whenNotPaused` coverage | `reclaimBounty`, `releaseExpiredClaim`, `finalizeTier2`, `castJuryVote` callable during emergency pause | **Fixed** |

### 2.3 High — Exogenous Risks (Identified, not yet mitigated)

| # | Risk | Impact | Status |
|---|------|--------|--------|
| 9 | Circle USDC blacklist | If Circle blacklists Escrow or Treasury address, all protocol USDC is permanently frozen | **Documented — needs `migrateToken` escape hatch or risk acceptance** |
| 10 | No timelock/multisig on `onlyOwner` functions | Compromised deployer key can halt VRGDA, drain treasury via `emergencyWithdraw`, change payout ratios | **Pending — required before mainnet** |

### 2.4 Medium — Economic & Design Issues (Acknowledged)

| # | Issue | Notes |
|---|-------|-------|
| 11 | Metabolic Tax routing doesn't match whitepaper (no GPSL royalty, no commercial/public-good split) | Contract does flat 4/1; whitepaper specifies 3.5/1/0.5 with Cryptographic Lock |
| 12 | `vrgdaSold` tracks requested amount including burned tokens | Pricing curve diverges from actual circulating supply over time |
| 13 | Jury system is first-come not VRF-selected; no penalty for incorrect votes | Whitepaper claims VRF selection |
| 14 | 18-year VRGDA emission timeline | **Not a bug** — intentional governance defense against hostile capture at low FDV. Should be documented as such. |

---

## 3. Current Contract State

### 3.1 Deployed (Base Sepolia — Pre-Fix)

| Contract | Address |
|----------|---------|
| SoulboundMass | `0x5ce7dF091D4d8B8085DFF214400B9870C529A1e2` |
| Treasury | `0xcc55632702779044d5d4661713acCe1880bA714d` |
| EscrowCore | `0xb070E660Dfce264025c4D6d91A1AFdbDFb2e76ee` |
| AutoToken ($AUTO) | `0xd8E2E5ECaAAb35E274260508a490446a722AfDA4` |

> **Note:** These deployed contracts contain the pre-fix code. A redeployment to Base Sepolia is required after PR #1 is merged.

### 3.2 Test Suite

- **116 / 116 tests passing** (post-fix)
- Coverage gaps identified:
  - `reclaimBounty` — zero test coverage
  - `slashMass` — newly implemented, zero test coverage
  - `sunsetCoreContributorTax` called by Treasury — untested path
  - Reentrancy guard interaction with integration flows — untested

---

## 4. Codebase Metrics

| Metric | Value |
|--------|-------|
| Solidity contracts | 4 (AutoToken, Treasury, EscrowCore, SoulboundMass) |
| Shared interfaces | 1 (IAutopoieticTypes) |
| Test files | 6 (unit + integration) |
| Total Foundry tests | 116 |
| Node Client | Python prototype (agent brain + web3 chain adapter + gossip network) |
| Whitepaper | V3.4 (docs/whitepaper-v3.4.md) |
| First on-chain payload | Block 39448081 (Base Sepolia) |
| Total deployment cost | 0.000035 ETH (~$0.07) |

---

## 5. Action Items — Priority Order

### Immediate (Before Merge)
- [ ] Add test coverage for `reclaimBounty`, `slashMass`, and Treasury milestone trigger path
- [ ] Review and merge PR #1

### Pre-Audit
- [ ] Implement timelock or multisig on all `onlyOwner` admin functions
- [ ] Decide on USDC blacklist mitigation strategy (`migrateToken` vs. documented risk acceptance)
- [ ] Reconcile Metabolic Tax routing with whitepaper (GPSL royalty, commercial/public-good split) or update whitepaper to match contract
- [ ] Document 18-year VRGDA timeline as intentional governance defense in README

### Pre-Mainnet
- [ ] Competitive smart contract audit (Code4rena or Sherlock, est. $10-15k)
- [ ] Redeploy all contracts to Base Sepolia with fixes
- [ ] DUNA formation via OtoCo
- [ ] Farcaster Alpha Draft recruitment (10-15 operators)
- [ ] Go rewrite of Node Client networking layer

---

## 6. Design Decisions Log

| Decision | Rationale | Date |
|----------|-----------|------|
| 18-year VRGDA emission at $2M FDV | Prevents hostile governance capture by mercenary capital during vulnerable early years. Slow drip ensures architect's 10% allocation acts as stabilizing force. | 2026-04-02 |
| 50% milestone burn (not 25%) | Stronger decentralization signal — burns half of unvested architect tokens when treasury hits $500K CPI-adjusted, proving self-sustainability | 2026-04-02 |
| Reentrancy guards added despite USDC not being reentrant today | Defensive coding — if Base ever upgrades USDC implementation or protocol migrates stablecoins, contracts remain safe | 2026-04-02 |
| `sunsetCoreContributorTax` callable by Treasury OR owner | Treasury must be able to trigger tax sunset as part of the atomic milestone execution. Owner retains ability for manual override. | 2026-04-02 |

---

*Report generated during security review session. PR #1: https://github.com/svenschlegel/gravdic/pull/1*
