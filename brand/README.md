# GravDic Brand Guidelines

> Topological minimalism. Serious. Academic. Not crypto-bro.

## Color Palette

| Role             | Hex       | Usage                                      |
|------------------|-----------|---------------------------------------------|
| Deep Slate       | `#020617` | Backgrounds, primary surfaces               |
| Ghost White      | `#F8FAFC` | Body text, primary foreground                |
| Indigo           | `#6366F1` | Established mass, accent, links, CTA         |
| Emerald          | `#10B981` | Growth, new fluency, positive deltas         |
| Slate 400        | `#94A3B8` | Secondary text, muted annotations            |
| Slate 700        | `#334155` | Borders, dividers, subtle separators         |

### Usage rules

- Background is always deep slate (`#020617`) or near-black. Never white.
- Indigo marks things with proven weight: established agents, confirmed mass, primary actions.
- Emerald marks growth and newcomers: new agents gaining fluency, positive metrics, onboarding.
- Never use both accents on the same element. One accent per context.
- Red (`#EF4444`) is reserved strictly for errors and destructive actions.

## Typography

| Context           | Font            | Weight       |
|-------------------|-----------------|--------------|
| Headers / Display | Inter or Geist  | 600-700      |
| Body              | Inter           | 400          |
| Data / Formulas   | JetBrains Mono  | 400-500      |
| Code              | JetBrains Mono  | 400          |

### Rules

- Formulas and empirical numbers always render in JetBrains Mono.
- Headers are sentence case, not title case. "Gravitational routing" not "Gravitational Routing".
- No all-caps except acronyms (USDC, GPSL, SVG).

## Logo

The GravDic logomark is a geometric **G** with a subtle gravitational-lens distortion — the lower stroke warps slightly inward, suggesting a gravity well.

### Usage rules

- Minimum size: 40x40px.
- Always use the SVG source files; never rasterize below 2x.
- On dark backgrounds: white G (`#F8FAFC`).
- On light backgrounds (rare): deep slate G (`#020617`).
- Clear space: at least 50% of the logo width on all sides.
- Never add effects (drop shadows, glows, gradients) beyond what is in the source SVG.
- Never rotate, stretch, or recolor the logo.

### Files

- `logo.svg` — White G on transparent background.
- `logo-on-slate.svg` — White G on `#020617` slate background (X/Twitter avatar).

## Banner

The X banner (`banner.svg`, 1500x500) visualizes the Phase 1 monopoly collapse:

- **Left:** V3.4 regime. One massive node, 9 dormant dots. Monopoly.
- **Right:** V3.5 regime. 7 active nodes, compressed mass range. Distributed.
- **Center divider:** "Metabolic Season Rebase" label.
- **Annotations** (JetBrains Mono): `9726:1 -> 15:1`, `Gini 0.685 -> 0.257`, `Quality cost: 0%`.

## Open Graph Image

`og-image.svg` (1200x630) for link previews:

- GravDic wordmark.
- Tagline: "A protocol for AI swarms governed by physics, not committees."
- Key number: 49.5% Gini reduction, zero quality cost.

## Tone of Voice

- **Register:** Academic but accessible. Like a well-written arXiv abstract, not a Medium post.
- **Stance:** Empirical. Every claim has a number behind it. "49.5% Gini reduction" not "fairer for everyone."
- **Avoid:** Hype words (revolutionary, game-changing, next-gen), emoji in technical contexts, exclamation marks.
- **Preferred framing:** Physics metaphors (mass, gravity, orbits, collapse) over economic metaphors (markets, incentives, tokenomics).
- **First person:** "The protocol" or "GravDic" — never "we" in technical docs. "We" is acceptable in community/social posts only.
