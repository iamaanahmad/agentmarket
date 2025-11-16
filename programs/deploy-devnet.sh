#!/bin/bash
# Deploy to Solana Devnet Script

echo "🚀 Deploying AgentMarket to Solana Devnet..."
echo "============================================="
echo ""

# Navigate to programs directory (already in correct directory)
# cd /mnt/c/Projects/agentmarket/programs || exit 1

# Check Solana config
echo "📡 Current Solana configuration:"
solana config get
echo ""

# Set to devnet if not already
echo "🔧 Setting cluster to devnet..."
solana config set --url https://api.devnet.solana.com
echo ""

# Check balance
echo "💰 Checking SOL balance..."
BALANCE=$(solana balance)
echo "Balance: $BALANCE"
echo ""

if [[ "$BALANCE" == "0 SOL" ]]; then
    echo "💸 Airdropping SOL for deployment..."
    solana airdrop 2
    echo ""
fi

# Deploy all programs
echo "🚀 Deploying programs to devnet..."
anchor deploy --provider.cluster devnet

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "📋 Deployed Program IDs:"
    anchor keys list
else
    echo ""
    echo "❌ Deployment failed! Check errors above."
    exit 1
fi
