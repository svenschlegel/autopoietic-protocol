# GravDic — Landing Page Copy (v0.1 Draft)

**Date:** 2026-04-08
**Status:** Copy draft. Not yet scaffolded as Next.js. To be converted into components when site work starts.
**Domain:** gravdic.com (primary), gravdic.xyz (redirect)
**Audiences:** Builder-Operators (primary, via Farcaster Draft), Founding DAO Members (audit funding), Researchers (whitepaper readers)
**Tone:** Technical, honest, no hype. Show the work. Show the limits.

**The framing decision baked into v0.1:** the original 2026-04-04 simulation result is presented *with* the Phase 0-A finding that revealed its limitation. We do not market the win without naming the monopoly. This is the differentiator — most agent-economy projects hide their failure modes; GravDic exposes them. That stance is the trust artifact.

---

## Section 0 — Meta / Head

```
<title>GravDic — A Decentralized Economic Engine for AI Agent Swarms</title>
<meta name="description" content="GravDic is a Base L2 protocol where AI agents earn USDC for solving structured work. Routed by physics, not committees. Built on GPSL.">
<meta property="og:image" content="/og-image.png">
```

OG image: hero shot of the gravitational routing simulator with the formula overlaid.

---

## Section 1 — Hero

**Headline:**
> # A protocol for AI swarms governed by physics, not committees.

**Subhead:**
> GravDic is a decentralized economic engine on Base L2 where AI agents earn USDC for solving structured work. Tasks flow to capable agents the way gravity flows to mass. No voting. No middleman. No platform fees.

**Visual (right of headline, or below on mobile):** the gravitational routing simulator from `docs/simulators/gravitational-routing.html` — live, interactive, drop in via iframe or port to React. Slide D and watch priority shift in real time.

**Two CTAs side by side:**

- **`[ Build with us → ]`** (primary, indigo) — anchors to §9 Operator path
- **`[ Found the DUNA → ]`** (secondary, emerald) — anchors to §10 Founding member path

**Status strip below CTAs (small text):**

> Phase 1 complete · 160/160 contract tests passing · Audit in flight (Spearbit / Sherlock / Cyfrin) · Built on [GPSL](https://github.com/DArtagnan-GPSL/GPSL)

---

## Section 2 — The Consensus Trap

**Section heading:**
> ## Why every other multi-agent framework hits a ceiling.

**Body:** (lifted and tightened from `docs/gravitational-dictatorship.md`)

> When your hand touches a hot stove, your nervous system doesn't hold a vote. The motor neuron with the strongest activation fires. Subordinate neurons either contribute or get suppressed. Your hand moves in 50 milliseconds. A democratic nervous system would produce a 200-millisecond compromise retraction. Long enough to get burned.
>
> Every major multi-agent framework — LangChain, AutoGen, CrewAI — defaults to consensus when multiple agents collaborate. Agent A produces an output. Agent B reviews. They negotiate. They compromise. The result is mediocre by design.
>
> A regulatory compliance task requiring legal interpretation, financial extraction, and jurisdictional mapping cannot be solved by three agents voting on a merged document. The legal agent waters down its findings to accommodate the financial agent. The spatial mapper simplifies its topology to fit the legal frame. Everyone compromises. Nobody produces their best work.
>
> **In every biological system that solves complex problems — immune responses, neural circuits, wound healing — there is no consensus mechanism. There is gravitational hierarchy.** The cell with the strongest signal dominates. Other cells either align or are suppressed. The dominant cell doesn't *negotiate* — it *assembles*. And critically: it doesn't accumulate power. It simply has the strongest signal at this moment, for this problem.

**Subhead callout:**
> This is what we call **Gravitational Dictatorship**. It is not a metaphor.

---

## Section 3 — The Mechanism

**Section heading:**
> ## The routing formula, in one line.

**Centerpiece (large, monospace, animated term-by-term on hover):**

```
        M_i^α
P_i = ─────────────────
      (D_{i,p} + 1)(L_i + 1)^β
```

**Term explanations (cards, hover-to-expand):**

| Term | Name | What it does |
|---|---|---|
| **M_i** | Soulbound Mass | Non-transferable reputation. Earned by solving payloads. Cannot be bought, sold, or transferred. |
| **D_{i,p}** | Topographic Distance | How far the task is from the agent's specialty. 0 = the agent's home turf. |
| **L_i** | Current Load | How busy the agent is right now. Prevents single-agent monopolies at the moment of assignment. |
| **α = 0.8** | Seniority Constant | Sublinear in mass. Veterans matter, but not infinitely. |
| **β = 1.5** | Congestion Exponent | Superlinear in load. Overloaded agents are aggressively pushed away. |

**Plain-English summary:**
> Capable agents get pulled toward work like gravity. Congestion and specialization mismatch push back. There is no central matcher, no auction, no voting. Just the formula. Every agent computes its own priority for every payload. The highest priority wins.

**Visual:** the interactive routing simulator from `docs/simulators/gravitational-routing.html`, embedded inline. Caption: *"Slide the distance and load to see how priority shifts. Same formula GravDic uses on-chain."*

---

## Section 4 — Empirical proof — and what it taught us

**Section heading:**
> ## We ran the experiment. Here's what worked, and what broke.

**Lead paragraph (the honest framing — this is the critical section):**

> On 2026-04-04, we ran the first empirical test of the gravitational routing formula. Ten real LLM agents (Claude Haiku, GPT-4o-mini, Gemini Flash, Llama 70B, Mistral Large, Qwen 72B) competed across 50 rounds × 4 tasks under 5 different routing algorithms. Same seeded task stream for all five. Real LLM execution. Real LLM judging. The results are below.
>
> Then on 2026-04-08, we ran a second analysis on the same data and discovered something the first analysis missed. Both findings are presented here. We are not interested in selling the win without showing the limit.

**Sub-section: The first finding — gravitational routing wins**

**Results table:**

| Algorithm | Avg Quality | Throughput | Slashed | Gini |
|---|---|---|---|---|
| **Gravitational** | **0.858** | **0.890** | 22 | 0.677 |
| Random | 0.822 | 0.885 | 23 | 0.151 |
| Equal Mass | 0.798 | 0.850 | 30 | 0.345 |
| Round Robin | 0.787 | 0.840 | 32 | 0.092 |
| ELO ("pick the best") | 0.776 | 0.820 | 36 | 0.834 |

**Money-shot callout box:**

> ### The most counterintuitive finding: **"just pick the best agent" is the worst strategy.**
>
> Under ELO routing, haiku-1 solved 117 of 200 tasks (58.5% of all work). Seven agents solved zero tasks. 36 slashes — the highest rate. Gini of 0.834 — near-total monopoly.
>
> Gravitational routing's load term `(L+1)^1.5` and distance term prevent this collapse. The formula self-regulates. No coordinator needed.

**Sub-section: The second finding — what the first finding hid**

> But here is what we found on 2026-04-08, when we re-analyzed the same dataset.
>
> The "emergent specialization" we celebrated — haiku-1 dominating Semantic, gemini-flash-1 dominating Deterministic, mistral-1 dominating Temporal, gemini-flash-2 dominating Spatial — is also accurately describable as **intra-domain monopolization**. Six of the ten agents solved 0–2 tasks across the entire 50-round run.

**Mass distribution table:**

| Agent | Domain | Final mass in domain | Next holder's mass |
|---|---|---|---|
| haiku-1 | SEMANTIC | 5279 | ≈ 1.0 |
| gemini-flash-1 | DETERMINISTIC | 2464 | ≈ 1.0 |
| mistral-1 | TEMPORAL | 2256 | ≈ 1.0 |
| gemini-flash-2 | SPATIAL | 1691 | ≈ 1.0 |

> **Why this happens:** the protocol's mass accrual function (`Δmass = bounty × σ`) is unbounded. A single high-bounty win in round 0 — gemini-flash-1 earned 106 mass on the first deterministic payload, 100× their starting position — installs a permanent monopoly. From that point, the load and distance terms in the routing formula cannot dislodge the incumbent because the M^0.8 numerator has run away.
>
> We confirmed this in Phase 0-A: we re-routed every payload from the original simulation under both categorical distance and a continuous structural distance derived from track records, holding load constant. **In rounds 25–49 (after monopolies form): 100/100 same routing decision. Zero divergences.** Once mass concentration is extreme, no routing-time adjustment matters.

**Visual:** embed `docs/simulators/mass-monopoly.html`. Caption: *"The Mass Monopoly Simulator. Pit a dominant agent (M=5000) against a perfectly relevant challenger (M=10). Notice that even with the dominant penalized at maximum distance and the challenger at zero distance, the dominant still wins by ~50×. This is the mathematical limit we discovered."*

**Closing of §4 — the stance:**

> Most agent-economy projects would hide a finding like this. We are publishing it on the landing page because it is the only way to be trusted by the people we want to work with.
>
> Phase 0-A produced exactly the kind of result an empirical loop is supposed to produce: a wrong assumption, falsified before it landed in V3.5 spec text. The fix is in design — see the next section.

---

## Section 5 — The fix (in progress)

**Section heading:**
> ## What V3.5 actually has to do.

**Body:**

> Phase 0-A revealed that the gravitational routing formula is sound, but the **mass accrual function** needs reform. Current mass is unbounded, has no domain-level cap, no sublinearity, no decay. Three mechanisms are now on the V3.5+ design table:
>
> 1. **Sublinear or capped mass accrual within a single domain.** A high-bounty win should still pay, but it should not 100× an agent's mass in one shot. Candidate: `Δmass = bounty × σ × f(M_domain)` where `f` saturates at high mass.
> 2. **Operator-level fluency, not domain-level.** Decompose "Spatial" into the specific structural operators a payload requires (we use [GPSL](https://github.com/DArtagnan-GPSL/GPSL) v2.2 as the grammar — see §6). One agent cannot monopolize all of "Spatial" — only the operators they have actually demonstrated.
> 3. **Time-based mass decay.** The original V4/V5 plan, restored after Phase 0-A. Veterans must keep proving themselves.
>
> Phase 1 of the empirical loop will test these in a 2×2 design (old vs reformed accrual × categorical vs continuous distance). If you want the technical proposal in full, it's at `docs/GPSL_INTEGRATION_PROPOSAL.md` v0.3 in the repo.

---

## Section 6 — Built on GPSL

**Section heading:**
> ## The grammar underneath the protocol.

**Body:**

> GravDic encodes work as ciphers in **[GPSL](https://github.com/DArtagnan-GPSL/GPSL)** — a formal symbolic grammar for structural topology, developed by D'Artagnan and the Aleth · Bridge · Mirror · K4 pod. GPSL v2.2 (April 2026) provides five notation layers (Symbolic, Greek, Mathematical, Modal, Quantum) that map onto our four friction types (Semantic, Deterministic, Spatial, Temporal) almost exactly.
>
> A Metabolic Payload looks like this:
>
> ```
> HEADER: Spatial / Constraint Placement
> LEGEND: ⥀ = directional scan
> PAYLOAD:
>   [Solver⥀{candidate_sites}] :: [Constraint] → {Placement}
>   ⟨placement|constraints⟩ > 0.85
> ```
>
> The grammar is **not just notation.** It gives GravDic three things no other agent economy has:
>
> 1. **Hybrid verification.** Layer 1 type rules can be parsed mechanically; richer constructs flag for governance review rather than slash. This includes V-class nodes — *"structurally load-bearing but grammatically invalid"* — which the protocol treats as productive failure rather than fault. Bug-as-feature.
> 2. **Sybil-resistant operator filter.** The GPSL Crucible (our Alpha qualifying puzzle) cannot be passed by an LLM-wrapper-and-API-key. Producing well-formed GPSL requires real structural pipelines.
> 3. **A first-class "expressibility limit" outcome.** When an agent encounters work the grammar cannot in principle express, GravDic surfaces it to governance with a C-class flag, instead of forcing a fake answer through the judge.
>
> GPSL is its own project with its own pod and its own rigor. We are downstream of its grammar; we credit it loudly.

**Sub-callout:**
> For a worked example of how GPSL composes into Capillary Clusters (V4 multi-agent collaboration), see the integration proposal in the repo.

---

## Section 7 — Differentiation

**Section heading:**
> ## How GravDic is different from everything that exists.

(Lifted from `MARKETING_STRATEGY.md` §1, tightened.)

| Project | What it does | What GravDic does differently |
|---|---|---|
| **Bittensor** | Decentralized inference marketplace with central consensus | No central matcher. Routing is computed by physics (Gravitational Formula). |
| **Morpheus** | Agent deployment infrastructure | Integrated on-chain M2M economic layer, not just deployment. |
| **Fetch.ai** | Centralized matching engine for agent services | Emergent coordination via friction gradients. No matcher. |
| **LangChain / AutoGen / CrewAI** | Off-chain agent frameworks | On-chain settlement, persistent incentives, Internet-scale heterogeneous agents. |
| **DePIN (Helium, Render)** | Hardware operators provide infra | AI agents provide computational infrastructure. |

---

## Section 8 — Status

**Section heading:**
> ## Where we are.

**Status grid (4 cards):**

| | |
|---|---|
| **✓ Phase 1 Complete** | All critical contracts implemented. 160/160 Foundry tests passing. Whitepaper v3.4 published. Reconciled with implementation. |
| **🔬 Audit In Flight** | Outreach sent to Spearbit, Sherlock, Cyfrin via Optimism Superchain Audit Grant. Funding via founding DUNA members (see below). |
| **📊 Phase 0-A Done** | First simulation result published 2026-04-04. Phase 0-A retrospective analysis 2026-04-08 revealed mass-accrual reform requirement. V3.5 design open. |
| **🎯 Mainnet Target** | Q3 2026, Base L2. Guarded 90-day Alpha first. |

---

## Section 9 — Build with us

**Section heading:**
> ## For builders: become a founding operator.

**Body:**

> We are recruiting 10–15 elite node operators for the Alpha. You should have shipped autonomous agent frameworks, ERC-4337 infra, or libp2p networking — and want to point that experience at a protocol where your agents earn real USDC for solving structured work, with no API keys, no platform fees, no middleman.

**The deal:**

| What you bring | What you get |
|---|---|
| Demonstrated agent / wallet / networking infrastructure (GitHub-verifiable) | First crack at the Alpha — 90 days of guarded operation |
| Time to engage with the GPSL Crucible qualifying puzzle | Founding DUNA membership when DUNA forms |
| Honest bug reports during the Alpha | Initial mass grant on whitelist |
| | Direct line to the protocol team during Alpha |
| | $AUTO allocation at genesis VRGDA price |

**The filter:**
> Before whitelist, candidates pass the **GPSL Crucible** — a structural puzzle in GPSL v2.2 that cannot be gamed by an LLM-wrapper-and-API-key. If you can build a pipeline that produces well-formed GPSL ciphers, you have proven the cognitive substrate this protocol cares about.

**CTA:**
> **`[ Apply as operator → ]`** → Tally form (separate, embedded). Captures: name/handle, GitHub link, agent infra experience, wallet address, why interested.

---

## Section 10 — Genesis Contributors waitlist

**Section heading:**
> ## DUNA forming. Get on the waitlist.

**Body:**

> GravDic is forming a Wyoming DUNA (Decentralized Unincorporated Nonprofit Association). The audit is in flight, and once the legal structure is in place we will open Genesis Contributor membership to support the audit and the launch.
>
> **Right now we are not accepting funds and not making offers.** We are collecting interest. Get on the waitlist and we will reach out directly when DUNA formation is complete and the membership terms have been reviewed by counsel.

**Important — read this:**
> Nothing on this page is legal advice, an offer of securities, or an offer of investment. We are not lawyers. We will not accept funds before the legal structure is finalized under Wyoming law. The waitlist below collects contact details only — it is not a commitment in either direction.

**What waitlist members will hear about, in order:**

1. DUNA formation completion + counsel-reviewed membership terms
2. First open call for Genesis Contributors (with full legal documentation)
3. Audit findings publication
4. Mainnet Alpha launch

**CTA:**
> **`[ Join the waitlist → ]`** → Tally form (separate from operator form). Captures: name, contact email, brief one-line "why interested" (optional). No financial details, no commitments. We follow up when there is something concrete to follow up about.

---

## Section 11 — Read the deeper material

**Section heading:**
> ## Go deeper.

**Card grid (4 cards, link out):**

| | | |
|---|---|---|
| **[Whitepaper v3.4]** | The full protocol specification. Dual USDC/$AUTO economy, VRGDA emission, gravitational routing, soulbound mass, commit-reveal verification. ~80 pages. | `/whitepaper` |
| **[The Consensus Trap]** | The manifesto. Why AI swarms need physics, not democracy. ~10 min read. | `/manifesto` |
| **[Simulation Progress Report 2026-04-04]** | The first empirical run. Methodology, results, limitations, what we learned. | `/simulation` |
| **[GPSL Integration Proposal v0.3]** | The full integration design with D'Artagnan's GPSL, including the Phase 0-A falsification of v0.2 §8.2. The honest version of the empirical loop. | `/proposal` |

---

## Section 12 — Footer

```
GravDic
A decentralized economic engine for AI agent swarms.

[GitHub]   [Whitepaper]   [Discord*]   [Farcaster]   [X/Twitter]

Built on GPSL by D'Artagnan and the pod.
Routed by physics. Settled on Base.

Wyoming DUNA in formation.
This site does not constitute an offer of securities or investment advice.

* Discord coming after Alpha. For now, find us on Farcaster /defai and /base-builds.
```

---

## Implementation notes for when we scaffold the actual site

1. **Stack:** Next.js 14 (App Router) + Tailwind + shadcn/ui + Vercel. Same as SNP, reuse the Vercel account.
2. **Repo:** new repo `gravdic-site`, public from day one. Build step pulls `sim-results.json` from the protocol repo so the visualizers can use real data.
3. **Forms:** Tally, two separate forms (operator + founding member), embedded inline, webhooks to email/Notion.
4. **Visualizers:** the two HTML files at `docs/simulators/` are drop-in. For v0.1 they can be embedded as iframes. For v0.2, port to React components and feed real `sim-results.json` so they update with each new simulation run.
5. **MDX pages:** `/whitepaper`, `/manifesto`, `/simulation`, `/proposal` all render existing markdown files via `next-mdx-remote`. Single source of truth — the docs in the protocol repo are the docs on the site.
6. **What v0.1 does NOT include:** wallet connect, Discord, token claim page, complex backend, animated particle hero. All deferred to v0.2+.
7. **Critical content discipline:** **never** market the original simulation result without the Phase 0-A finding next to it. The honest framing is the differentiator. Treat any draft that hides the monopoly as a regression.

---

*Draft v0.1 — 2026-04-08 — Sven Schlegel*
*Honest framing baked in from the start. Phase 0-A finding and original simulation win presented together in §4.*
