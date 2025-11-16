#!/bin/bash
# Complete Smart Contract Deployment Script
# Usage: ./deploy-complete.sh

set -e  # Exit on error

echo "════════════════════════════════════════════════════════"
echo "  AgentMarket Smart Contract Complete Deployment"
echo "════════════════════════════════════════════════════════"
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Pre-flight checks
echo -e "${BLUE}[1/6] Running pre-flight checks...${NC}"
echo ""

if ! command -v solana &> /dev/null; then
    echo -e "${RED}❌ Solana CLI not installed!${NC}"
    exit 1
fi

if ! command -v anchor &> /dev/null; then
    echo -e "${RED}❌ Anchor CLI not installed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Solana CLI found: $(solana --version)${NC}"
echo -e "${GREEN}✅ Anchor CLI found: $(anchor --version)${NC}"
echo ""

# Step 2: Configure network
echo -e "${BLUE}[2/6] Configuring Solana network...${NC}"
solana config set --url https://api.devnet.solana.com
CURRENT_CLUSTER=$(solana config get cluster)
echo -e "${GREEN}✅ Cluster set to: $CURRENT_CLUSTER${NC}"
echo ""

# Step 3: Fund wallet
echo -e "${BLUE}[3/6] Checking wallet balance...${NC}"
WALLET=$(solana address)
echo "Wallet address: $WALLET"
echo ""

BALANCE=$(solana balance 2>&1)
echo "Current balance: $BALANCE"

if [[ "$BALANCE" == "0 SOL" ]]; then
    echo -e "${YELLOW}⚠️  Balance is 0 SOL, attempting airdrop...${NC}"
    solana airdrop 2 && sleep 3
    solana airdrop 2 && sleep 3
    NEW_BALANCE=$(solana balance)
    echo -e "${GREEN}✅ New balance: $NEW_BALANCE${NC}"
else
    echo -e "${GREEN}✅ Sufficient balance available${NC}"
fi
echo ""

# Step 4: Build programs
echo -e "${BLUE}[4/6] Building smart contracts...${NC}"
cd "$(dirname "$0")" || exit 1
cd programs || exit 1

echo "Running: anchor build"
if anchor build --force; then
    echo -e "${GREEN}✅ Build successful!${NC}"
else
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi
echo ""

# Step 5: Deploy programs
echo -e "${BLUE}[5/6] Deploying to Devnet...${NC}"
echo "Running: anchor deploy --provider.cluster devnet"
echo ""

if anchor deploy --provider.cluster devnet; then
    echo ""
    echo -e "${GREEN}✅ Deployment successful!${NC}"
else
    echo ""
    echo -e "${RED}❌ Deployment failed!${NC}"
    exit 1
fi
echo ""

# Step 6: Capture program IDs
echo -e "${BLUE}[6/6] Capturing deployed program IDs...${NC}"
echo ""
echo -e "${YELLOW}📋 Deployed Program IDs:${NC}"
anchor keys list

echo ""
echo "════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📌 Next steps:"
echo "   1. Copy IDL files to frontend:"
echo "      cp ./target/idl/*.json ../src/lib/idl/"
echo ""
echo "   2. Update src/lib/constants.ts with new program IDs"
echo ""
echo "   3. Test frontend integration:"
echo "      npm run dev"
echo ""
echo "   4. Run integration tests:"
echo "      anchor test --provider.cluster devnet"
echo ""

