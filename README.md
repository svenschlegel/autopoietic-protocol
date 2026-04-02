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
