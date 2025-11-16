#!/bin/bash
# Anchor Test Script for WSL Ubuntu

echo "🧪 Testing AgentMarket Smart Contracts..."
echo "=========================================="
echo ""

# Navigate to programs directory (already in correct directory)
# cd /mnt/c/Projects/agentmarket/programs || exit 1

# Run tests
echo "🔬 Running anchor test..."
anchor test --skip-local-validator

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "❌ Tests failed! Check errors above."
    exit 1
fi
