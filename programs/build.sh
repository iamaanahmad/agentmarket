#!/bin/bash
# Anchor Build Script for WSL Ubuntu

echo "🔨 Building AgentMarket Smart Contracts..."
echo "=========================================="
echo ""

# Use Windows anchor installation
ANCHOR_CMD="/mnt/c/Users/iamas/.cargo/bin/anchor.exe"

if [ ! -f "$ANCHOR_CMD" ]; then
    echo "❌ Error: Could not find anchor at $ANCHOR_CMD"
    exit 1
fi

echo "Using anchor at: $ANCHOR_CMD"
echo ""

# Build all programs
echo "📦 Running anchor build..."
$ANCHOR_CMD build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "📋 Build artifacts:"
    ls -lh target/deploy/*.so 2>/dev/null || echo "No .so files found"
    ls -lh target/idl/*.json 2>/dev/null || echo "No IDL files found"
else
    echo ""
    echo "❌ Build failed! Check errors above."
    exit 1
fi
