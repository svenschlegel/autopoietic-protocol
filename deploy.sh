#!/bin/bash
set -e

# ============================================================
# THE AUTOPOIETIC PROTOCOL — Deploy to Base Sepolia
# ============================================================
# 
# This script:
#   1. Installs Foundry (if not present)
#   2. Initializes the Foundry project
#   3. Compiles all contracts
#   4. Runs the full test suite
#   5. Deploys to Base Sepolia
#   6. Outputs deployment.json for the Node Client
#
# Prerequisites:
#   - A Base Sepolia wallet with ETH for gas
#     (Get testnet ETH from https://www.coinbase.com/faucets/base-ethereum-goerli-faucet)
#   - An RPC URL (default: https://sepolia.base.org)
#
# Usage:
#   cp .env.example .env
#   # Edit .env with your private key
#   chmod +x deploy.sh
#   ./deploy.sh
#
# ============================================================

YELLOW='\033[1;33m'
GREEN='\033[1;32m'
RED='\033[1;31m'
CYAN='\033[1;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  THE AUTOPOIETIC PROTOCOL — Base Sepolia Deployment${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# ── Load environment ─────────────────────────────────────────

if [ -f .env ]; then
    echo -e "${GREEN}▸ Loading .env...${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${RED}ERROR: .env file not found.${NC}"
    echo "  cp .env.example .env"
    echo "  Then edit .env with your DEPLOYER_PRIVATE_KEY"
    exit 1
fi

if [ -z "$DEPLOYER_PRIVATE_KEY" ]; then
    echo -e "${RED}ERROR: DEPLOYER_PRIVATE_KEY not set in .env${NC}"
    exit 1
fi

export BASE_SEPOLIA_RPC_URL="${BASE_SEPOLIA_RPC_URL:-https://sepolia.base.org}"

# ── Step 1: Install Foundry ──────────────────────────────────

if ! command -v forge &> /dev/null; then
    echo -e "${YELLOW}▸ Step 1: Installing Foundry...${NC}"
    curl -L https://foundry.paradigm.xyz | bash
    source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null || true
    foundryup
    echo -e "${GREEN}  ✓ Foundry installed${NC}"
else
    echo -e "${GREEN}▸ Step 1: Foundry already installed ($(forge --version | head -1))${NC}"
fi

# ── Step 2: Initialize Foundry project ───────────────────────

echo -e "${YELLOW}▸ Step 2: Initializing Foundry project...${NC}"

cd contracts

# Install forge-std if not present
if [ ! -d "lib/forge-std" ]; then
    forge install foundry-rs/forge-std --no-commit
fi

echo -e "${GREEN}  ✓ Project initialized${NC}"

# ── Step 3: Compile ──────────────────────────────────────────

echo -e "${YELLOW}▸ Step 3: Compiling contracts...${NC}"
forge build
echo -e "${GREEN}  ✓ Compilation successful${NC}"

# ── Step 4: Run tests ────────────────────────────────────────

echo -e "${YELLOW}▸ Step 4: Running test suite...${NC}"
forge test -vv
echo -e "${GREEN}  ✓ All tests passed${NC}"

# ── Step 5: Gas report ───────────────────────────────────────

echo -e "${YELLOW}▸ Step 5: Generating gas report...${NC}"
forge test --gas-report > ../gas_report.txt 2>&1 || true
echo -e "${GREEN}  ✓ Gas report saved to gas_report.txt${NC}"

# ── Step 6: Deploy to Base Sepolia ───────────────────────────

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  DEPLOYING TO BASE SEPOLIA${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

forge script script/Deploy.s.sol:DeployAutopoietic \
    --rpc-url "$BASE_SEPOLIA_RPC_URL" \
    --private-key "$DEPLOYER_PRIVATE_KEY" \
    --broadcast \
    -vvvv

# ── Step 7: Move deployment.json to project root ─────────────

if [ -f deployment.json ]; then
    cp deployment.json ../deployment.json
    echo -e "${GREEN}  ✓ deployment.json copied to project root${NC}"
fi

cd ..

# ── Step 8: Install Python dependencies for Node Client ──────

echo ""
echo -e "${YELLOW}▸ Step 8: Setting up Node Client...${NC}"

pip install web3 python-dotenv 2>/dev/null || pip3 install web3 python-dotenv 2>/dev/null || {
    echo -e "${YELLOW}  Warning: Could not install Python deps. Run manually:${NC}"
    echo "  pip install web3 python-dotenv"
}

echo -e "${GREEN}  ✓ Node Client ready${NC}"

# ── Done ─────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  DEPLOYMENT COMPLETE${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "  Contract addresses saved to: deployment.json"
echo "  Gas report saved to: gas_report.txt"
echo ""
echo "  Next steps:"
echo "    1. Verify contracts on BaseScan (addresses in deployment.json)"
echo "    2. Get testnet USDC from Base Sepolia faucet"
echo "    3. Run the Node Client:"
echo "       python -m node_client.live_test"
echo ""
echo -e "${GREEN}============================================================${NC}"
