"""Composite payload templates for multi-agent collaboration experiments.

Each composite payload spans 2-3 friction types and includes:
- A full composite prompt (the whole task as one agent would see it)
- Per-domain decomposed sub-prompts (what each specialist sees)
- Domain weights that sum to 1.0
- A composite scoring rubric for the judge
"""

from __future__ import annotations

from dataclasses import dataclass, field

from node_client.core.types import FrictionType, VerificationTier

from simulation.payloads.templates import SimPayload


@dataclass
class CompositePayload(SimPayload):
    """A payload that spans multiple friction types and can be decomposed."""

    sub_domains: list[FrictionType] = field(default_factory=list)
    sub_prompts: dict[FrictionType, str] = field(default_factory=dict)
    domain_weights: dict[FrictionType, float] = field(default_factory=dict)
    composite_rubric: str = ""


# ---------------------------------------------------------------------------
# 10 composite payload templates
# ---------------------------------------------------------------------------

COMPOSITE_TEMPLATES: list[CompositePayload] = [

    # -----------------------------------------------------------------------
    # 1. SEMANTIC + DETERMINISTIC — Legal contract analysis
    # -----------------------------------------------------------------------
    CompositePayload(
        payload_id="composite_01_legal_contract",
        domain=FrictionType.SEMANTIC,  # primary domain
        tier=VerificationTier.OPTIMISTIC_CONSENSUS,
        prompt=(
            "Analyze the following contract clause from a SaaS agreement between "
            "Nexora Inc. (Provider) and Bridgewell Health Systems (Client):\n\n"
            "\"Provider shall deliver the Platform with 99.95% monthly uptime, measured "
            "as total minutes in calendar month minus downtime minutes, divided by total "
            "minutes. Scheduled maintenance windows (Saturdays 02:00-06:00 UTC) are excluded. "
            "For each 0.01% below the SLA target, Provider credits Client 2.5% of that "
            "month's invoice, capped at 30% of monthly fees. Client's monthly fee is "
            "$48,750. Downtime is defined as any period exceeding 5 consecutive minutes "
            "where >50% of API endpoints return HTTP 5xx. Provider reported the following "
            "incidents in March 2026 (31 days): March 3 (Tuesday) 14:22-14:41 UTC — full "
            "outage; March 11 (Tuesday) 09:15-09:22 UTC — partial (38% of endpoints); "
            "March 18 (Saturday) 03:10-03:55 UTC — full outage during maintenance window; "
            "March 27 (Thursday) 22:08-23:47 UTC — full outage.\"\n\n"
            "Tasks:\n"
            "(1) Identify which incidents qualify as countable downtime under the SLA "
            "definition. Explain any ambiguities in the clause.\n"
            "(2) Calculate the exact uptime percentage for March 2026 and the credit "
            "amount owed, if any. Show all arithmetic."
        ),
        expected_answer=None,
        scoring_rubric=None,
        difficulty=0.7,
        bounty=0.05,
        execution_window=120,
        sub_domains=[FrictionType.SEMANTIC, FrictionType.DETERMINISTIC],
        sub_prompts={
            FrictionType.SEMANTIC: (
                "Analyze this SaaS SLA clause for ambiguities and determine which "
                "incidents count as downtime:\n\n"
                "\"Provider shall deliver the Platform with 99.95% monthly uptime, measured "
                "as total minutes in calendar month minus downtime minutes, divided by total "
                "minutes. Scheduled maintenance windows (Saturdays 02:00-06:00 UTC) are excluded. "
                "Downtime is defined as any period exceeding 5 consecutive minutes where >50% "
                "of API endpoints return HTTP 5xx.\"\n\n"
                "Incidents in March 2026 (31 days):\n"
                "- March 3 (Tue) 14:22-14:41 UTC: full outage\n"
                "- March 11 (Tue) 09:15-09:22 UTC: partial outage (38% of endpoints)\n"
                "- March 18 (Sat) 03:10-03:55 UTC: full outage during maintenance window\n"
                "- March 27 (Thu) 22:08-23:47 UTC: full outage\n\n"
                "For each incident, state whether it qualifies as countable downtime and why. "
                "Identify any ambiguities in the clause wording."
            ),
            FrictionType.DETERMINISTIC: (
                "Given these SLA parameters, compute the uptime and credit:\n"
                "- Month: March 2026 (31 days = 44,640 total minutes)\n"
                "- Maintenance exclusion: Saturdays 02:00-06:00 UTC\n"
                "- Saturday maintenance minutes in March 2026: 4 Saturdays x 240 min = 960 min\n"
                "- Countable downtime incidents:\n"
                "  - March 3, 14:22-14:41 UTC = 19 minutes\n"
                "  - March 27, 22:08-23:47 UTC = 99 minutes\n"
                "- (March 11 partial outage: only 38% of endpoints, below 50% threshold = NOT downtime)\n"
                "- (March 18 outage: within Saturday maintenance window = excluded)\n"
                "- Total countable downtime: 118 minutes\n"
                "- Denominator: 44,640 - 960 = 43,680 billable minutes\n"
                "- SLA target: 99.95%\n"
                "- Credit: 2.5% of monthly fee per 0.01% below target, capped at 30%\n"
                "- Monthly fee: $48,750\n\n"
                "Calculate: (1) exact uptime percentage, (2) shortfall below 99.95%, "
                "(3) credit percentage, (4) dollar credit amount."
            ),
        },
        domain_weights={FrictionType.SEMANTIC: 0.6, FrictionType.DETERMINISTIC: 0.4},
        composite_rubric=(
            "Score the answer on: (1) Correctly classifying March 11 as NOT downtime "
            "(38% < 50% threshold), March 18 as excluded (maintenance window), and March 3 "
            "and March 27 as countable — 0.3 points. (2) Identifying at least one ambiguity "
            "(e.g., does 'excluded' mean the window is subtracted from denominator or just "
            "that downtime in the window doesn't count?) — 0.15 points. (3) Correct uptime "
            "calculation: (43680 - 118) / 43680 = 99.7298% — 0.25 points. (4) Correct credit: "
            "shortfall = 0.2202%, that's 22.02 units of 0.01%, so 22.02 x 2.5% = 55.05%, "
            "capped at 30%, so credit = 30% x $48,750 = $14,625 — 0.3 points. "
            "Total: sum of applicable points."
        ),
    ),

    # -----------------------------------------------------------------------
    # 2. SEMANTIC + SPATIAL — School placement optimization
    # -----------------------------------------------------------------------
    CompositePayload(
        payload_id="composite_02_school_placement",
        domain=FrictionType.SPATIAL,
        tier=VerificationTier.OPTIMISTIC_CONSENSUS,
        prompt=(
            "A city is planning 2 new elementary schools. Here are 6 neighborhoods with data:\n\n"
            "| Neighborhood | Center (x,y) km | School-age children | Median income | Nearest existing school (km) |\n"
            "|---|---|---|---|---|\n"
            "| Oakridge | (2, 8) | 1,240 | $41,200 | 4.3 |\n"
            "| Millbrook | (5, 6) | 870 | $67,500 | 1.1 |\n"
            "| Hartfield | (1, 3) | 1,580 | $33,800 | 5.7 |\n"
            "| Sunnyside | (7, 2) | 960 | $52,100 | 3.9 |\n"
            "| Pinehurst | (4, 1) | 1,110 | $38,900 | 4.8 |\n"
            "| Waverly | (8, 7) | 720 | $71,300 | 2.2 |\n\n"
            "Tasks:\n"
            "(1) Analyze which neighborhoods have the greatest educational need, considering "
            "child population, income level, and distance to existing schools.\n"
            "(2) Propose optimal (x, y) coordinates for the 2 new schools to best serve the "
            "highest-need areas. Minimize weighted average distance, where weight = "
            "number of children x (1 / median_income). Show your geometric reasoning."
        ),
        expected_answer=None,
        scoring_rubric=None,
        difficulty=0.8,
        bounty=0.06,
        execution_window=120,
        sub_domains=[FrictionType.SEMANTIC, FrictionType.SPATIAL],
        sub_prompts={
            FrictionType.SEMANTIC: (
                "Analyze the educational need of 6 neighborhoods for school placement:\n\n"
                "| Neighborhood | School-age children | Median income | Nearest existing school (km) |\n"
                "|---|---|---|---|\n"
                "| Oakridge | 1,240 | $41,200 | 4.3 |\n"
                "| Millbrook | 870 | $67,500 | 1.1 |\n"
                "| Hartfield | 1,580 | $33,800 | 5.7 |\n"
                "| Sunnyside | 960 | $52,100 | 3.9 |\n"
                "| Pinehurst | 1,110 | $38,900 | 4.8 |\n"
                "| Waverly | 720 | $71,300 | 2.2 |\n\n"
                "Rank the neighborhoods by educational need. Consider: more children = more need, "
                "lower income = more need (less ability to transport kids to distant schools), "
                "farther from existing school = more need. Provide a ranked list with reasoning."
            ),
            FrictionType.SPATIAL: (
                "Place 2 new schools to serve these neighborhoods. Each neighborhood has a "
                "center point and a weight (children / median_income_in_thousands):\n\n"
                "| Neighborhood | Center (x,y) km | Weight |\n"
                "|---|---|---|\n"
                "| Oakridge | (2, 8) | 30.1 |\n"
                "| Millbrook | (5, 6) | 12.9 |\n"
                "| Hartfield | (1, 3) | 46.7 |\n"
                "| Sunnyside | (7, 2) | 18.4 |\n"
                "| Pinehurst | (4, 1) | 28.5 |\n"
                "| Waverly | (8, 7) | 10.1 |\n\n"
                "Find (x, y) coordinates for 2 schools that minimize the total weighted distance "
                "from each neighborhood to its nearest new school. Think of this as a weighted "
                "2-center problem. Show the geometric reasoning and the resulting weighted "
                "average distance."
            ),
        },
        domain_weights={FrictionType.SEMANTIC: 0.4, FrictionType.SPATIAL: 0.6},
        composite_rubric=(
            "Score on: (1) Correctly identifying Hartfield and Pinehurst as top-2 needs "
            "(high children, low income, far from schools), with Oakridge close behind — "
            "0.25 points. (2) Reasonable school placements: one school should be near "
            "Hartfield/Pinehurst cluster (roughly (2, 2) area) and one near Oakridge "
            "(roughly (3, 7) area) — 0.35 points. Accept any placement within ~1.5 km of "
            "these centers if the reasoning is sound. (3) Correctly computing weighted distances "
            "for the proposed placement — 0.2 points. (4) Coherent integration: does the need "
            "analysis actually inform the placement, or are they disconnected? — 0.2 points. "
            "Total: sum of applicable points."
        ),
    ),

    # -----------------------------------------------------------------------
    # 3. DETERMINISTIC + TEMPORAL — Server log forensics
    # -----------------------------------------------------------------------
    CompositePayload(
        payload_id="composite_03_server_logs",
        domain=FrictionType.TEMPORAL,
        tier=VerificationTier.OPTIMISTIC_CONSENSUS,
        prompt=(
            "Analyze this server incident log from the payment gateway cluster:\n\n"
            "```\n"
            "2026-03-15 08:12:03 [INFO]  node-pay-1  Connection pool: 42/50 active\n"
            "2026-03-15 08:14:17 [WARN]  node-pay-1  Connection pool: 49/50 active\n"
            "2026-03-15 08:14:52 [ERROR] node-pay-1  Connection pool exhausted, 3 requests queued\n"
            "2026-03-15 08:15:01 [ERROR] node-pay-2  Upstream timeout from node-pay-1 (30s exceeded)\n"
            "2026-03-15 08:15:03 [WARN]  node-pay-3  Failover triggered: routing around node-pay-1\n"
            "2026-03-15 08:15:18 [ERROR] node-pay-2  Circuit breaker OPEN for node-pay-1\n"
            "2026-03-15 08:16:44 [ERROR] node-pay-3  Connection pool: 48/50 active (absorbing node-pay-1 traffic)\n"
            "2026-03-15 08:17:02 [WARN]  node-pay-3  Connection pool: 50/50 active\n"
            "2026-03-15 08:17:15 [ERROR] node-pay-3  Connection pool exhausted, 7 requests queued\n"
            "2026-03-15 08:17:33 [ERROR] node-pay-2  Upstream timeout from node-pay-3 (30s exceeded)\n"
            "2026-03-15 08:17:41 [CRIT]  lb-main    No healthy upstream nodes. 502 returned to 12 clients.\n"
            "2026-03-15 08:18:05 [INFO]  node-pay-1  Connection pool draining: 31/50 active\n"
            "```\n\n"
            "Tasks:\n"
            "(1) Extract a structured table with columns: timestamp, severity, node, "
            "metric_name, metric_value for every entry that contains a numeric metric.\n"
            "(2) Identify the causal chain: what triggered what, in what order, and what "
            "would have prevented the full outage at 08:17:41? Draw the dependency timeline."
        ),
        expected_answer=None,
        scoring_rubric=None,
        difficulty=0.75,
        bounty=0.05,
        execution_window=120,
        sub_domains=[FrictionType.DETERMINISTIC, FrictionType.TEMPORAL],
        sub_prompts={
            FrictionType.DETERMINISTIC: (
                "Extract structured data from this server log. For each line that contains "
                "a numeric metric, produce a row with: timestamp, severity, node, metric_name, "
                "metric_value.\n\n"
                "```\n"
                "2026-03-15 08:12:03 [INFO]  node-pay-1  Connection pool: 42/50 active\n"
                "2026-03-15 08:14:17 [WARN]  node-pay-1  Connection pool: 49/50 active\n"
                "2026-03-15 08:14:52 [ERROR] node-pay-1  Connection pool exhausted, 3 requests queued\n"
                "2026-03-15 08:15:01 [ERROR] node-pay-2  Upstream timeout from node-pay-1 (30s exceeded)\n"
                "2026-03-15 08:15:03 [WARN]  node-pay-3  Failover triggered: routing around node-pay-1\n"
                "2026-03-15 08:15:18 [ERROR] node-pay-2  Circuit breaker OPEN for node-pay-1\n"
                "2026-03-15 08:16:44 [ERROR] node-pay-3  Connection pool: 48/50 active (absorbing node-pay-1 traffic)\n"
                "2026-03-15 08:17:02 [WARN]  node-pay-3  Connection pool: 50/50 active\n"
                "2026-03-15 08:17:15 [ERROR] node-pay-3  Connection pool exhausted, 7 requests queued\n"
                "2026-03-15 08:17:33 [ERROR] node-pay-2  Upstream timeout from node-pay-3 (30s exceeded)\n"
                "2026-03-15 08:17:41 [CRIT]  lb-main    No healthy upstream nodes. 502 returned to 12 clients.\n"
                "2026-03-15 08:18:05 [INFO]  node-pay-1  Connection pool draining: 31/50 active\n"
                "```\n\n"
                "Return ONLY the structured table. Include: connection pool counts, queue "
                "depths, timeout durations, and client impact counts."
            ),
            FrictionType.TEMPORAL: (
                "Given this sequence of server events, identify the causal chain:\n\n"
                "08:12:03 — node-pay-1 pool at 42/50 (normal)\n"
                "08:14:17 — node-pay-1 pool at 49/50 (near capacity)\n"
                "08:14:52 — node-pay-1 pool exhausted, 3 requests queued\n"
                "08:15:01 — node-pay-2 times out waiting for node-pay-1 (30s limit)\n"
                "08:15:03 — node-pay-3 failover: absorbs node-pay-1 traffic\n"
                "08:15:18 — node-pay-2 circuit breaker opens for node-pay-1\n"
                "08:16:44 — node-pay-3 pool at 48/50 (absorbing extra traffic)\n"
                "08:17:02 — node-pay-3 pool at 50/50\n"
                "08:17:15 — node-pay-3 pool exhausted, 7 queued\n"
                "08:17:33 — node-pay-2 times out waiting for node-pay-3\n"
                "08:17:41 — load balancer: no healthy upstreams, 502 to 12 clients\n"
                "08:18:05 — node-pay-1 pool draining to 31/50\n\n"
                "Questions: (1) What is the root cause? (2) Map the causal dependency chain "
                "(which event caused which). (3) At what point could intervention have "
                "prevented the full outage? What specific action?"
            ),
        },
        domain_weights={FrictionType.DETERMINISTIC: 0.35, FrictionType.TEMPORAL: 0.65},
        composite_rubric=(
            "Score on: (1) Correct structured extraction with at least 8 of the numeric "
            "metrics identified (pool counts, queue depths, timeout, client count) — "
            "0.25 points. (2) Correctly identifying root cause as connection pool exhaustion "
            "on node-pay-1 — 0.15 points. (3) Correct causal chain: pool exhaustion -> "
            "timeout -> failover -> cascading pool exhaustion on node-pay-3 -> total outage "
            "— 0.3 points. (4) Reasonable intervention point (e.g., dynamic pool scaling at "
            "08:14:17 when pool hit 49/50, or rate limiting before failover transferred full "
            "load to node-pay-3) — 0.15 points. (5) Noting that node-pay-1 recovered by "
            "08:18:05 (only 6 minutes after exhaustion), so the cascading failure was "
            "avoidable — 0.15 points. Total: sum of applicable points."
        ),
    ),

    # -----------------------------------------------------------------------
    # 4. SEMANTIC + TEMPORAL — Historical event analysis
    # -----------------------------------------------------------------------
    CompositePayload(
        payload_id="composite_04_historical_causation",
        domain=FrictionType.SEMANTIC,
        tier=VerificationTier.OPTIMISTIC_CONSENSUS,
        prompt=(
            "Analyze the following sequence of policy decisions and their effects on the "
            "2008 housing market:\n\n"
            "Timeline:\n"
            "- 1999: Gramm-Leach-Bliley Act repeals Glass-Steagall barrier between commercial "
            "and investment banking\n"
            "- 2000-2003: Federal funds rate drops from 6.5% to 1.0%\n"
            "- 2004: SEC relaxes net capital rule for 5 largest investment banks, allowing "
            "leverage ratios up to 33:1 (previously capped at 12:1)\n"
            "- 2005: Subprime mortgage originations reach $625 billion (up from $160 billion "
            "in 2001)\n"
            "- 2006: Housing prices peak; Fed rate back up to 5.25%\n"
            "- 2007 Q3: BNP Paribas freezes 3 funds; interbank lending freezes\n"
            "- 2008 March: Bear Stearns collapses (assets $395B, leverage 33:1)\n"
            "- 2008 September: Lehman Brothers files bankruptcy ($639B in assets)\n\n"
            "Tasks:\n"
            "(1) Construct the causal dependency graph: which events were necessary preconditions "
            "for which later events?\n"
            "(2) Evaluate the counterfactual: if the SEC had NOT relaxed the net capital rule "
            "in 2004, would the crisis have been prevented or merely delayed? Argue both sides."
        ),
        expected_answer=None,
        scoring_rubric=None,
        difficulty=0.85,
        bounty=0.06,
        execution_window=150,
        sub_domains=[FrictionType.SEMANTIC, FrictionType.TEMPORAL],
        sub_prompts={
            FrictionType.SEMANTIC: (
                "Evaluate this counterfactual about the 2008 financial crisis:\n\n"
                "Context: In 2004, the SEC relaxed the net capital rule for 5 major investment "
                "banks, allowing leverage ratios up to 33:1 (from 12:1). Bear Stearns collapsed "
                "in March 2008 with $395B in assets at 33:1 leverage. Lehman Brothers filed "
                "bankruptcy in September 2008 with $639B in assets.\n\n"
                "Other contributing factors: Glass-Steagall repeal (1999), low interest rates "
                "2000-2003 (1.0% at trough), subprime originations reaching $625B in 2005 "
                "(up from $160B in 2001).\n\n"
                "Question: If the SEC had NOT relaxed the net capital rule in 2004, would the "
                "crisis have been prevented or merely delayed? Argue BOTH sides with specific "
                "reasoning. Consider: Would subprime lending still have grown? Would the same "
                "institutions still have been vulnerable at 12:1 leverage?"
            ),
            FrictionType.TEMPORAL: (
                "Construct a causal dependency graph from this timeline:\n\n"
                "A: 1999 — Glass-Steagall repeal\n"
                "B: 2000-2003 — Fed rate drops 6.5% to 1.0%\n"
                "C: 2004 — SEC relaxes leverage cap (12:1 -> 33:1)\n"
                "D: 2005 — Subprime originations reach $625B (from $160B in 2001)\n"
                "E: 2006 — Housing prices peak; rate back to 5.25%\n"
                "F: 2007 Q3 — BNP Paribas fund freeze; interbank lending freezes\n"
                "G: 2008 March — Bear Stearns collapse ($395B, 33:1 leverage)\n"
                "H: 2008 September — Lehman bankruptcy ($639B)\n\n"
                "For each event, list which earlier events were necessary preconditions. "
                "Distinguish between direct causes and enabling conditions. Which events had "
                "multiple independent causes? Which single event, if removed, would have "
                "prevented the most downstream consequences?"
            ),
        },
        domain_weights={FrictionType.SEMANTIC: 0.55, FrictionType.TEMPORAL: 0.45},
        composite_rubric=(
            "Score on: (1) Correct causal links — B and C both enabled D; D + E caused F; "
            "C directly enabled G (33:1 leverage); F + G led to H — 0.3 points. (2) Nuanced "
            "counterfactual: 'prevented' argument notes 12:1 leverage would have dramatically "
            "reduced Bear/Lehman exposure; 'merely delayed' argument notes subprime originations "
            "were driven by low rates and demand, not just leverage — 0.35 points. Award full "
            "marks only if BOTH sides argued. (3) Identifies C (leverage relaxation) as the "
            "single highest-impact removal point — 0.15 points. (4) Coherent integration "
            "between causal graph and counterfactual analysis — 0.2 points. "
            "Total: sum of applicable points."
        ),
    ),

    # -----------------------------------------------------------------------
    # 5. SEMANTIC + DETERMINISTIC + SPATIAL — Real estate portfolio (triple)
    # -----------------------------------------------------------------------
    CompositePayload(
        payload_id="composite_05_real_estate_portfolio",
        domain=FrictionType.SEMANTIC,
        tier=VerificationTier.OPTIMISTIC_CONSENSUS,
        prompt=(
            "A real estate fund is evaluating 4 properties for a $5M allocation:\n\n"
            "Property A — 'The Greystone', downtown mixed-use, 312 Oak St:\n"
            "  Purchase: $1,450,000 | NOI: $98,200 | Debt service: $72,000/yr\n"
            "  Down payment: $362,500 | Location: (2.1, 4.8) km from city center\n"
            "  Note: Adjacent to proposed light rail station (construction starts 2027)\n\n"
            "Property B — 'Riverside Commons', suburban apartments, 45 River Rd:\n"
            "  Purchase: $2,100,000 | NOI: $147,000 | Debt service: $108,000/yr\n"
            "  Down payment: $525,000 | Location: (7.3, 1.2) km from city center\n"
            "  Note: 3 competing apartment complexes within 1 km; rents declining 2%/yr\n\n"
            "Property C — 'Tech Park Unit 7', office/industrial, 890 Innovation Dr:\n"
            "  Purchase: $980,000 | NOI: $82,400 | Debt service: $51,000/yr\n"
            "  Down payment: $245,000 | Location: (5.5, 6.9) km from city center\n"
            "  Note: Single tenant (BioGen Labs), lease expires in 14 months\n\n"
            "Property D — 'Harbor View', waterfront retail, 22 Marina Blvd:\n"
            "  Purchase: $1,680,000 | NOI: $121,800 | Debt service: $87,600/yr\n"
            "  Down payment: $420,000 | Location: (0.8, 0.3) km from city center\n"
            "  Note: Flood zone; insurance costs rose 18% last year, trend continuing\n\n"
            "Tasks:\n"
            "(1) Qualitative risk analysis: for each property, assess opportunities and threats.\n"
            "(2) Compute for each: cap rate, cash-on-cash return, and debt service coverage "
            "ratio (DSCR). Identify which properties meet the fund's minimums (cap rate >6%, "
            "CoC >7%, DSCR >1.25).\n"
            "(3) Assess geographic concentration: if the fund buys 2-3 of these, which "
            "combination minimizes spatial correlation risk? Use the coordinates to quantify."
        ),
        expected_answer=None,
        scoring_rubric=None,
        difficulty=0.9,
        bounty=0.08,
        execution_window=180,
        sub_domains=[
            FrictionType.SEMANTIC,
            FrictionType.DETERMINISTIC,
            FrictionType.SPATIAL,
        ],
        sub_prompts={
            FrictionType.SEMANTIC: (
                "Provide a qualitative risk-opportunity analysis for 4 investment properties:\n\n"
                "A — 'The Greystone': downtown mixed-use. Adjacent to proposed light rail "
                "station (construction starts 2027).\n"
                "B — 'Riverside Commons': suburban apartments. 3 competing complexes within "
                "1 km; rents declining 2%/yr.\n"
                "C — 'Tech Park Unit 7': office/industrial. Single tenant (BioGen Labs), "
                "lease expires in 14 months.\n"
                "D — 'Harbor View': waterfront retail. Flood zone; insurance costs rose 18% "
                "last year, trend continuing.\n\n"
                "For each property: (1) list key opportunities, (2) list key threats, "
                "(3) assign an overall risk rating (low/medium/high). Justify each rating."
            ),
            FrictionType.DETERMINISTIC: (
                "Compute financial metrics for 4 properties. Fund minimums: cap rate >6%, "
                "cash-on-cash return >7%, DSCR >1.25.\n\n"
                "A: Purchase $1,450,000 | NOI $98,200 | Debt service $72,000/yr | Down payment $362,500\n"
                "B: Purchase $2,100,000 | NOI $147,000 | Debt service $108,000/yr | Down payment $525,000\n"
                "C: Purchase $980,000 | NOI $82,400 | Debt service $51,000/yr | Down payment $245,000\n"
                "D: Purchase $1,680,000 | NOI $121,800 | Debt service $87,600/yr | Down payment $420,000\n\n"
                "For each property compute:\n"
                "- Cap rate = NOI / Purchase price\n"
                "- Cash-on-cash return = (NOI - Debt service) / Down payment\n"
                "- DSCR = NOI / Debt service\n\n"
                "Flag which properties meet ALL three fund minimums."
            ),
            FrictionType.SPATIAL: (
                "Assess geographic concentration risk for a portfolio selection from 4 "
                "properties at these coordinates (km from city center):\n\n"
                "A: (2.1, 4.8)\nB: (7.3, 1.2)\nC: (5.5, 6.9)\nD: (0.8, 0.3)\n\n"
                "Compute the pairwise Euclidean distances between all properties. Then for "
                "each possible 2-property and 3-property combination, calculate the minimum "
                "pairwise distance (a proxy for geographic diversification — higher is better). "
                "Rank the combinations from most to least geographically diversified."
            ),
        },
        domain_weights={
            FrictionType.SEMANTIC: 0.35,
            FrictionType.DETERMINISTIC: 0.40,
            FrictionType.SPATIAL: 0.25,
        },
        composite_rubric=(
            "Score on: (1) Correct financial metrics — A: cap 6.77%, CoC 7.23%, DSCR 1.36; "
            "B: cap 7.0%, CoC 7.43%, DSCR 1.36; C: cap 8.41%, CoC 12.82%, DSCR 1.62; "
            "D: cap 7.25%, CoC 8.14%, DSCR 1.39. All four meet the minimums — 0.3 points. "
            "(2) Reasonable risk assessment: A (medium-low, upside from rail), B (medium-high, "
            "competition + declining rents), C (high single-tenant risk but best financials), "
            "D (high flood/insurance risk) — 0.25 points. (3) Correct pairwise distances and "
            "diversification ranking — B+D or A+B should rank high for spatial spread — "
            "0.2 points. (4) Integrated recommendation that weighs all three analyses together "
            "(not just picking highest CoC ignoring risk and geography) — 0.25 points. "
            "Total: sum of applicable points."
        ),
    ),

    # -----------------------------------------------------------------------
    # 6. SPATIAL + TEMPORAL — Warehouse routing with time windows
    # -----------------------------------------------------------------------
    CompositePayload(
        payload_id="composite_06_delivery_routing",
        domain=FrictionType.SPATIAL,
        tier=VerificationTier.OPTIMISTIC_CONSENSUS,
        prompt=(
            "A delivery van starts at warehouse W(0, 0) at 08:00 and must deliver to "
            "5 customers, each with a delivery time window:\n\n"
            "| Customer | Location (x,y) km | Time window | Service time |\n"
            "|---|---|---|---|\n"
            "| C1 | (3, 4) | 08:30 - 09:30 | 10 min |\n"
            "| C2 | (7, 1) | 09:00 - 10:30 | 15 min |\n"
            "| C3 | (2, 7) | 08:15 - 09:00 | 10 min |\n"
            "| C4 | (6, 5) | 10:00 - 11:00 | 20 min |\n"
            "| C5 | (1, 2) | 08:00 - 12:00 | 5 min |\n\n"
            "The van travels at 40 km/h. Travel time between two points = Euclidean "
            "distance / 40 km/h, converted to minutes.\n\n"
            "Tasks:\n"
            "(1) Find a feasible route that visits all 5 customers within their time windows.\n"
            "(2) Compute the total route distance and total time (including travel, service, "
            "and any waiting). Identify if any route ordering is infeasible and why.\n"
            "(3) Is this the optimal (shortest distance) feasible route? If not, what is?"
        ),
        expected_answer=None,
        scoring_rubric=None,
        difficulty=0.85,
        bounty=0.07,
        execution_window=150,
        sub_domains=[FrictionType.SPATIAL, FrictionType.TEMPORAL],
        sub_prompts={
            FrictionType.SPATIAL: (
                "Compute all pairwise Euclidean distances between these points, and convert "
                "to travel time at 40 km/h:\n\n"
                "W: (0, 0)\nC1: (3, 4)\nC2: (7, 1)\nC3: (2, 7)\nC4: (6, 5)\nC5: (1, 2)\n\n"
                "Produce a distance matrix (in km, rounded to 2 decimal places) and a travel "
                "time matrix (in minutes, rounded to 1 decimal place). Then identify the "
                "shortest-distance Hamiltonian path starting from W (ignoring time windows "
                "for now)."
            ),
            FrictionType.TEMPORAL: (
                "Given this travel time matrix (minutes) and time windows, find a feasible "
                "delivery schedule:\n\n"
                "Start: Warehouse at 08:00\n\n"
                "Travel times from key points (approximate):\n"
                "W->C5: 3.4 min | W->C1: 7.5 min | W->C3: 10.9 min\n"
                "C5->C1: 3.6 min | C5->C3: 5.1 min | C1->C3: 3.2 min\n"
                "C1->C4: 3.2 min | C3->C4: 4.5 min | C1->C2: 5.0 min\n"
                "C2->C4: 4.1 min | C4->C2: 4.1 min\n\n"
                "Time windows:\n"
                "C1: 08:30-09:30 (10 min service)\n"
                "C2: 09:00-10:30 (15 min service)\n"
                "C3: 08:15-09:00 (10 min service)\n"
                "C4: 10:00-11:00 (20 min service)\n"
                "C5: 08:00-12:00 (5 min service)\n\n"
                "Find a route order that satisfies all time windows. If you arrive before the "
                "window opens, you must wait. Compute the arrival time, wait time (if any), "
                "departure time for each stop. Identify the total elapsed time."
            ),
        },
        domain_weights={FrictionType.SPATIAL: 0.45, FrictionType.TEMPORAL: 0.55},
        composite_rubric=(
            "Score on: (1) Correct distance/time matrix — spot-check at least 3 values "
            "(e.g., W-C1 = 5.0 km, C1-C3 = sqrt(1+9)=3.16 km) — 0.2 points. "
            "(2) A feasible route that respects all time windows — a strong solution is "
            "W->C5->C3->C1->C2->C4 or W->C5->C3->C1->C4->C2 — 0.35 points. "
            "(3) Correct arrival/departure time calculations for the chosen route — "
            "0.25 points. (4) Discussion of whether the route is optimal or noting that "
            "C3's tight window (closes 09:00) forces it to be visited early — 0.2 points. "
            "Total: sum of applicable points."
        ),
    ),

    # -----------------------------------------------------------------------
    # 7. DETERMINISTIC + SPATIAL — Network topology analysis
    # -----------------------------------------------------------------------
    CompositePayload(
        payload_id="composite_07_network_topology",
        domain=FrictionType.DETERMINISTIC,
        tier=VerificationTier.OPTIMISTIC_CONSENSUS,
        prompt=(
            "A mesh sensor network has 8 nodes with the following connections and signal "
            "strengths (dBm, more negative = weaker):\n\n"
            "```\n"
            "Node positions (meters):\n"
            "  N1(0,0)  N2(30,10)  N3(15,40)  N4(50,5)\n"
            "  N5(45,35) N6(10,25)  N7(55,40)  N8(25,20)\n\n"
            "Active links (bidirectional):\n"
            "  N1-N2: -42 dBm    N1-N6: -51 dBm    N2-N4: -47 dBm\n"
            "  N2-N8: -38 dBm    N3-N6: -44 dBm    N3-N8: -40 dBm\n"
            "  N4-N5: -53 dBm    N4-N7: -49 dBm    N5-N7: -36 dBm\n"
            "  N5-N8: -46 dBm    N6-N8: -43 dBm    N7-N5: -36 dBm\n"
            "```\n\n"
            "Tasks:\n"
            "(1) Compute the Euclidean distance between each connected pair and determine "
            "if signal strength correlates with distance (compute Pearson correlation).\n"
            "(2) Find the minimum spanning tree by signal strength (strongest = lowest cost). "
            "List the edges.\n"
            "(3) Identify the single point of failure: which node, if removed, disconnects "
            "the most other nodes? Justify with the graph structure."
        ),
        expected_answer=None,
        scoring_rubric=None,
        difficulty=0.8,
        bounty=0.06,
        execution_window=150,
        sub_domains=[FrictionType.DETERMINISTIC, FrictionType.SPATIAL],
        sub_prompts={
            FrictionType.DETERMINISTIC: (
                "Given these node connections with signal strengths, perform the following "
                "computations:\n\n"
                "Links: N1-N2(-42), N1-N6(-51), N2-N4(-47), N2-N8(-38), N3-N6(-44), "
                "N3-N8(-40), N4-N5(-53), N4-N7(-49), N5-N7(-36), N5-N8(-46), N6-N8(-43)\n\n"
                "Node positions (meters): N1(0,0) N2(30,10) N3(15,40) N4(50,5) N5(45,35) "
                "N6(10,25) N7(55,40) N8(25,20)\n\n"
                "(1) Compute Euclidean distance for each connected pair.\n"
                "(2) Compute Pearson correlation between distance and signal strength "
                "(use absolute dBm values). Show intermediate sums.\n"
                "(3) Find the minimum spanning tree treating signal strength as cost "
                "(use |dBm|, so -36 is cheapest at cost 36). Apply Kruskal's algorithm."
            ),
            FrictionType.SPATIAL: (
                "Analyze this network graph for structural vulnerabilities:\n\n"
                "Nodes: N1, N2, N3, N4, N5, N6, N7, N8\n"
                "Edges: N1-N2, N1-N6, N2-N4, N2-N8, N3-N6, N3-N8, N4-N5, N4-N7, "
                "N5-N7, N5-N8, N6-N8\n\n"
                "Node positions (meters): N1(0,0) N2(30,10) N3(15,40) N4(50,5) N5(45,35) "
                "N6(10,25) N7(55,40) N8(25,20)\n\n"
                "Node degrees: N1(2), N2(3), N3(2), N4(3), N5(3), N6(3), N7(2), N8(4)\n\n"
                "For each node, determine what happens to graph connectivity if that node is "
                "removed. Which node is the single most critical point of failure? Are there "
                "any articulation points (nodes whose removal disconnects the graph)?"
            ),
        },
        domain_weights={FrictionType.DETERMINISTIC: 0.5, FrictionType.SPATIAL: 0.5},
        composite_rubric=(
            "Score on: (1) Correct Euclidean distances for at least 8 of 11 pairs — "
            "0.2 points. (2) Reasonable Pearson correlation (should be moderately negative, "
            "around -0.5 to -0.8, meaning farther = weaker signal) — 0.15 points. "
            "(3) Correct MST: should include N5-N7(-36), N2-N8(-38), N3-N8(-40), "
            "N1-N2(-42), N6-N8(-43), N5-N8(-46), N2-N4(-47) = 7 edges connecting 8 nodes "
            "— 0.3 points. (4) Correct identification of N8 as the critical node "
            "(degree 4, connects the N1-N2 cluster to N3-N6 cluster to N4-N5-N7 cluster) "
            "— 0.2 points. (5) Coherent integration tying the spatial vulnerability to the "
            "signal analysis — 0.15 points. Total: sum of applicable points."
        ),
    ),

    # -----------------------------------------------------------------------
    # 8. SEMANTIC + DETERMINISTIC + TEMPORAL — Clinical trial analysis (triple)
    # -----------------------------------------------------------------------
    CompositePayload(
        payload_id="composite_08_clinical_trial",
        domain=FrictionType.SEMANTIC,
        tier=VerificationTier.OPTIMISTIC_CONSENSUS,
        prompt=(
            "Review this clinical trial summary for drug NVX-4017 (a JAK inhibitor for "
            "rheumatoid arthritis):\n\n"
            "Phase II results (24-week, double-blind, n=312):\n"
            "- Arm A (placebo, n=78): ACR20 response 24.4%, mean DAS28 change -0.8\n"
            "- Arm B (5mg BID, n=79): ACR20 response 58.2%, mean DAS28 change -2.1\n"
            "- Arm C (10mg BID, n=78): ACR20 response 71.8%, mean DAS28 change -2.9\n"
            "- Arm D (15mg BID, n=77): ACR20 response 73.4%, mean DAS28 change -3.0\n\n"
            "Safety signals:\n"
            "- Serious adverse events: A(2.6%), B(3.8%), C(5.1%), D(11.7%)\n"
            "- Herpes zoster: A(0%), B(1.3%), C(2.6%), D(5.2%)\n"
            "- LDL cholesterol increase >30%: A(1.3%), B(5.1%), C(10.3%), D(15.6%)\n"
            "- Neutropenia (ANC <1000): A(0%), B(0%), C(1.3%), D(3.9%)\n\n"
            "Competitor landscape: Tofacitinib (approved) achieves ACR20 of 59.8% at 5mg BID "
            "with SAE rate of 3.5%. Upadacitinib (approved) achieves ACR20 of 70.5% at 15mg "
            "QD with SAE rate of 4.8%.\n\n"
            "Tasks:\n"
            "(1) Assess the efficacy-safety tradeoff. Which dose(s) should advance to Phase III?\n"
            "(2) Compute the number needed to treat (NNT) for ACR20 vs placebo for each arm, "
            "and the number needed to harm (NNH) for serious adverse events vs placebo.\n"
            "(3) Map the dose-response timeline: at what dosing level does efficacy plateau "
            "while adverse events continue to climb? Identify the inflection point."
        ),
        expected_answer=None,
        scoring_rubric=None,
        difficulty=0.9,
        bounty=0.08,
        execution_window=180,
        sub_domains=[
            FrictionType.SEMANTIC,
            FrictionType.DETERMINISTIC,
            FrictionType.TEMPORAL,
        ],
        sub_prompts={
            FrictionType.SEMANTIC: (
                "Evaluate the clinical positioning of NVX-4017 (JAK inhibitor, RA):\n\n"
                "Efficacy: 5mg BID = 58.2% ACR20; 10mg BID = 71.8%; 15mg BID = 73.4%\n"
                "Safety: SAE rates 3.8% / 5.1% / 11.7% for 5/10/15mg\n"
                "Herpes zoster: 1.3% / 2.6% / 5.2%\n"
                "LDL increase >30%: 5.1% / 10.3% / 15.6%\n\n"
                "Competitors:\n"
                "- Tofacitinib 5mg BID: ACR20 59.8%, SAE 3.5%\n"
                "- Upadacitinib 15mg QD: ACR20 70.5%, SAE 4.8%\n\n"
                "Questions: (1) Which dose(s) offer a competitive advantage vs existing drugs? "
                "(2) Which dose(s) should advance to Phase III and why? (3) What regulatory "
                "concerns would you flag?"
            ),
            FrictionType.DETERMINISTIC: (
                "Compute NNT and NNH for this trial data:\n\n"
                "Placebo ACR20: 24.4% | Placebo SAE: 2.6%\n"
                "Arm B (5mg): ACR20 58.2%, SAE 3.8%\n"
                "Arm C (10mg): ACR20 71.8%, SAE 5.1%\n"
                "Arm D (15mg): ACR20 73.4%, SAE 11.7%\n\n"
                "For each arm compute:\n"
                "- NNT for ACR20 = 1 / (ACR20_drug - ACR20_placebo)\n"
                "- NNH for SAE = 1 / (SAE_drug - SAE_placebo)\n"
                "- Likelihood of being helped or harmed (LHH) = NNH / NNT\n\n"
                "Round NNT and NNH to 1 decimal place. Show all arithmetic."
            ),
            FrictionType.TEMPORAL: (
                "Analyze the dose-response curve for NVX-4017:\n\n"
                "Dose (mg BID) -> Efficacy (ACR20%) -> Key adverse events:\n"
                "0 (placebo) -> 24.4% -> SAE 2.6%, HZ 0%, LDL 1.3%\n"
                "5 -> 58.2% -> SAE 3.8%, HZ 1.3%, LDL 5.1%\n"
                "10 -> 71.8% -> SAE 5.1%, HZ 2.6%, LDL 10.3%\n"
                "15 -> 73.4% -> SAE 11.7%, HZ 5.2%, LDL 15.6%\n\n"
                "Questions: (1) Compute the marginal gain per dose step (incremental ACR20 "
                "per 5mg increase). (2) Compute the marginal risk per dose step (incremental "
                "SAE per 5mg increase). (3) Identify the inflection point where marginal risk "
                "exceeds marginal benefit. (4) Does efficacy plateau while adverse events "
                "continue to scale linearly?"
            ),
        },
        domain_weights={
            FrictionType.SEMANTIC: 0.35,
            FrictionType.DETERMINISTIC: 0.35,
            FrictionType.TEMPORAL: 0.30,
        },
        composite_rubric=(
            "Score on: (1) Correct NNT: B=2.96, C=2.11, D=2.04; Correct NNH: B=83.3, "
            "C=40.0, D=11.0 — 0.25 points. (2) Correct identification of efficacy plateau "
            "between 10mg and 15mg (only 1.6% ACR20 gain) while SAE more than doubles "
            "(5.1% to 11.7%) — 0.25 points. (3) Recommending 10mg BID for Phase III "
            "(competitive with upadacitinib at 71.8% ACR20 with manageable 5.1% SAE) "
            "and possibly 5mg as a lower-risk alternative — 0.25 points. (4) Integrated "
            "analysis: NNT/NNH numbers support the qualitative recommendation, and the "
            "temporal dose-response curve informs the dose selection — 0.25 points. "
            "Total: sum of applicable points."
        ),
    ),

    # -----------------------------------------------------------------------
    # 9. SEMANTIC + SPATIAL + TEMPORAL — Disaster response planning (triple)
    # -----------------------------------------------------------------------
    CompositePayload(
        payload_id="composite_09_disaster_response",
        domain=FrictionType.SPATIAL,
        tier=VerificationTier.OPTIMISTIC_CONSENSUS,
        prompt=(
            "A Category 3 hurricane is forecast to make landfall on the Gulf Coast in 36 hours. "
            "Emergency management must allocate resources across 5 staging areas:\n\n"
            "| Staging Area | Location (km) | Population served | Elevation (m) | Road access |\n"
            "|---|---|---|---|---|\n"
            "| Alpha | (10, 5) | 45,000 | 2.1 | 2-lane highway |\n"
            "| Bravo | (25, 12) | 28,000 | 8.4 | 4-lane interstate |\n"
            "| Charlie | (8, 18) | 62,000 | 1.3 | 2-lane, flood-prone bridge |\n"
            "| Delta | (30, 3) | 15,000 | 12.7 | 4-lane interstate |\n"
            "| Echo | (18, 22) | 38,000 | 5.6 | 2-lane highway |\n\n"
            "Available resources: 120 rescue boats, 45 medical teams, 8,000 MRE pallets.\n\n"
            "Storm surge forecast: 3.5m at coast (y=0), decreasing 0.7m per km inland.\n"
            "Estimated timeline: landfall T+0, peak surge T+2h, roads impassable T+1h to T+8h, "
            "rescue window T+8h to T+48h.\n\n"
            "Tasks:\n"
            "(1) Assess vulnerability of each staging area (flood risk from surge vs elevation, "
            "population exposure, access reliability).\n"
            "(2) Propose optimal resource allocation across the 5 areas. Which areas get "
            "priority and why?\n"
            "(3) Design a 48-hour deployment timeline: what must happen before, during, and "
            "after landfall?"
        ),
        expected_answer=None,
        scoring_rubric=None,
        difficulty=0.9,
        bounty=0.08,
        execution_window=180,
        sub_domains=[
            FrictionType.SEMANTIC,
            FrictionType.SPATIAL,
            FrictionType.TEMPORAL,
        ],
        sub_prompts={
            FrictionType.SEMANTIC: (
                "Assess the vulnerability and priority of 5 hurricane staging areas:\n\n"
                "Alpha: serves 45,000 people, 2.1m elevation, 2-lane road access\n"
                "Bravo: serves 28,000 people, 8.4m elevation, 4-lane interstate\n"
                "Charlie: serves 62,000 people, 1.3m elevation, flood-prone bridge access\n"
                "Delta: serves 15,000 people, 12.7m elevation, 4-lane interstate\n"
                "Echo: serves 38,000 people, 5.6m elevation, 2-lane highway\n\n"
                "Storm surge: 3.5m at coast, -0.7m per km inland.\n"
                "Resources: 120 rescue boats, 45 medical teams, 8,000 MRE pallets.\n\n"
                "For each area: (1) assess flood risk (surge height vs elevation), "
                "(2) assess access reliability under storm conditions, (3) weigh population "
                "size. Propose a resource allocation with justification."
            ),
            FrictionType.SPATIAL: (
                "Compute the spatial flood risk for 5 staging areas given storm surge model:\n\n"
                "Surge at coast (y=0): 3.5m, decreasing 0.7m per km inland (y-axis = distance "
                "from coast).\n\n"
                "| Area | Location (x,y) km | Elevation (m) |\n"
                "|---|---|---|\n"
                "| Alpha | (10, 5) | 2.1 |\n"
                "| Bravo | (25, 12) | 8.4 |\n"
                "| Charlie | (8, 18) | 1.3 |\n"
                "| Delta | (30, 3) | 12.7 |\n"
                "| Echo | (18, 22) | 5.6 |\n\n"
                "For each area: (1) compute expected surge height = 3.5 - 0.7 * y_km, "
                "(2) compute flood margin = elevation - surge height (negative = flooded), "
                "(3) compute pairwise distances between areas to assess which areas can "
                "support each other. Rank areas by flood vulnerability."
            ),
            FrictionType.TEMPORAL: (
                "Design a 48-hour deployment timeline for hurricane response:\n\n"
                "Key constraints:\n"
                "- T-36h: current time (36 hours before landfall)\n"
                "- T+0h: landfall\n"
                "- T+1h to T+8h: roads impassable\n"
                "- T+2h: peak storm surge (3.5m at coast)\n"
                "- T+8h to T+48h: rescue window\n\n"
                "Area status at T+0:\n"
                "- Alpha: likely flooded (surge 0.0m, elev 2.1m — marginal)\n"
                "- Bravo: safe (surge -5.0m, well above)\n"
                "- Charlie: safe from surge but bridge access compromised\n"
                "- Delta: safe (high elevation, good roads)\n"
                "- Echo: safe (surge well below elevation)\n\n"
                "Resources to deploy: 120 boats, 45 medical teams, 8,000 MRE pallets.\n"
                "Pre-position phase: T-36h to T+0h\n"
                "Shelter-in-place: T+0h to T+8h\n"
                "Active rescue: T+8h to T+48h\n\n"
                "Create hour-by-hour phases. What goes where, when? What must be pre-positioned "
                "before roads close?"
            ),
        },
        domain_weights={
            FrictionType.SEMANTIC: 0.30,
            FrictionType.SPATIAL: 0.35,
            FrictionType.TEMPORAL: 0.35,
        },
        composite_rubric=(
            "Score on: (1) Correct surge calculations — Alpha surge = 3.5-3.5=0.0m (margin "
            "+2.1m, safe but marginal), Bravo surge = 3.5-8.4=-4.9m (safe), Charlie surge "
            "= 3.5-12.6=-9.1m (safe from surge but access vulnerable), Delta surge = "
            "3.5-2.1=1.4m (margin +11.3m, safe), Echo surge = 3.5-15.4=-11.9m (safe) — "
            "0.2 points. (2) Identifying Charlie as highest priority despite being inland "
            "(largest population, lowest elevation, worst access) and Alpha as second "
            "(marginal flood margin) — 0.25 points. (3) Reasonable resource allocation "
            "weighted by population and vulnerability — 0.2 points. (4) Timeline that "
            "pre-positions resources at Charlie and Alpha BEFORE roads close, stages "
            "Bravo and Delta as secondary support bases — 0.2 points. (5) Noting the "
            "bridge access problem at Charlie requires boats pre-positioned there — "
            "0.15 points. Total: sum of applicable points."
        ),
    ),

    # -----------------------------------------------------------------------
    # 10. DETERMINISTIC + SEMANTIC — Financial statement fraud detection
    # -----------------------------------------------------------------------
    CompositePayload(
        payload_id="composite_10_fraud_detection",
        domain=FrictionType.DETERMINISTIC,
        tier=VerificationTier.OPTIMISTIC_CONSENSUS,
        prompt=(
            "Review the following quarterly financials for MedTech Dynamics Inc. and "
            "identify potential signs of earnings manipulation:\n\n"
            "Income Statement ($ thousands):\n"
            "| | Q1 2025 | Q2 2025 | Q3 2025 | Q4 2025 |\n"
            "|---|---|---|---|---|\n"
            "| Revenue | 12,400 | 13,100 | 14,800 | 22,600 |\n"
            "| COGS | 6,820 | 7,074 | 7,992 | 10,170 |\n"
            "| Gross margin | 45.0% | 46.0% | 46.0% | 55.0% |\n"
            "| SG&A | 3,100 | 3,275 | 3,700 | 4,520 |\n"
            "| R&D | 1,240 | 1,310 | 1,480 | 1,130 |\n"
            "| Operating income | 1,240 | 1,441 | 1,628 | 6,780 |\n\n"
            "Balance Sheet items ($ thousands):\n"
            "| | Q1 | Q2 | Q3 | Q4 |\n"
            "|---|---|---|---|---|\n"
            "| Accounts receivable | 4,960 | 5,240 | 5,920 | 14,690 |\n"
            "| Inventory | 3,410 | 3,537 | 3,798 | 2,034 |\n"
            "| Deferred revenue | 1,860 | 1,965 | 2,220 | 680 |\n"
            "| Accrued expenses | 2,480 | 2,620 | 2,960 | 1,808 |\n\n"
            "Tasks:\n"
            "(1) Compute Days Sales Outstanding (DSO), inventory turnover, and the Beneish "
            "M-Score components (DSRI, GMI, AQI, SGI, DEPI) for Q4 vs Q3.\n"
            "(2) Identify which financial patterns are red flags for earnings manipulation "
            "and explain the accounting mechanisms that could produce these numbers.\n"
            "(3) Assess overall: is this more likely genuine growth or earnings manipulation? "
            "What additional information would you request?"
        ),
        expected_answer=None,
        scoring_rubric=None,
        difficulty=0.85,
        bounty=0.07,
        execution_window=150,
        sub_domains=[FrictionType.DETERMINISTIC, FrictionType.SEMANTIC],
        sub_prompts={
            FrictionType.DETERMINISTIC: (
                "Compute financial forensic metrics for MedTech Dynamics Q4 vs Q3 2025:\n\n"
                "Q3: Revenue 14,800 | COGS 7,992 | AR 5,920 | Inventory 3,798 | "
                "Deferred revenue 2,220 | Gross margin 46.0%\n"
                "Q4: Revenue 22,600 | COGS 10,170 | AR 14,690 | Inventory 2,034 | "
                "Deferred revenue 680 | Gross margin 55.0%\n\n"
                "Compute:\n"
                "1. DSO for Q3 and Q4: (AR / Revenue) * 90 days\n"
                "2. Inventory turnover for Q3 and Q4: COGS / Inventory\n"
                "3. Beneish M-Score components:\n"
                "   - DSRI = (AR_Q4/Rev_Q4) / (AR_Q3/Rev_Q3) — Days Sales Receivable Index\n"
                "   - GMI = Gross_margin_Q3 / Gross_margin_Q4 — Gross Margin Index\n"
                "   - SGI = Revenue_Q4 / Revenue_Q3 — Sales Growth Index\n"
                "   - DEPI = (Depr_rate_Q3) / (Depr_rate_Q4) — use R&D as proxy\n"
                "Show all arithmetic. Flag any metric that exceeds typical manipulation "
                "thresholds (DSRI > 1.031, GMI > 1.014, SGI > 1.411)."
            ),
            FrictionType.SEMANTIC: (
                "Analyze these financial patterns for signs of earnings manipulation:\n\n"
                "MedTech Dynamics Q4 2025 anomalies:\n"
                "- Revenue jumped 52.7% QoQ (Q3: $14.8M -> Q4: $22.6M) after steady ~10% growth\n"
                "- Gross margin jumped from 46% to 55% in one quarter\n"
                "- Accounts receivable jumped 148% ($5.92M -> $14.69M) vs 52.7% revenue growth\n"
                "- Inventory dropped 46.4% ($3.80M -> $2.03M) despite revenue growth\n"
                "- Deferred revenue dropped 69.4% ($2.22M -> $0.68M)\n"
                "- Accrued expenses dropped 38.9% ($2.96M -> $1.81M)\n"
                "- R&D spending DECREASED 23.6% ($1.48M -> $1.13M) while revenue grew 52.7%\n\n"
                "For each pattern: (1) explain what accounting mechanism could produce it, "
                "(2) assess whether it's consistent with genuine business growth or more "
                "consistent with manipulation, (3) rate the severity of the red flag "
                "(low/medium/high). Conclude with overall assessment."
            ),
        },
        domain_weights={FrictionType.DETERMINISTIC: 0.45, FrictionType.SEMANTIC: 0.55},
        composite_rubric=(
            "Score on: (1) Correct DSO: Q3 = 36.0 days, Q4 = 58.5 days (significant jump) "
            "— 0.1 points. (2) Correct DSRI = 1.625 (well above 1.031 threshold), GMI = 0.836 "
            "(below 1.0, actually favorable), SGI = 1.527 (above 1.411 threshold) — 0.2 points. "
            "(3) Identifying the top red flags: AR growing 3x faster than revenue (channel "
            "stuffing), deferred revenue collapse (pulling forward recognition), inventory "
            "drop with revenue growth (inconsistent), R&D cut to boost earnings — 0.3 points. "
            "(4) Explaining the mechanisms: channel stuffing inflates revenue/AR, releasing "
            "deferred revenue accelerates recognition, cutting accrued expenses boosts current "
            "income — 0.2 points. (5) Overall conclusion that this pattern is highly consistent "
            "with Q4 earnings manipulation (possibly to hit annual targets) — 0.2 points. "
            "Total: sum of applicable points."
        ),
    ),
]
