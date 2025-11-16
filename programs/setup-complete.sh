#!/bin/bash
# Complete Rust + Solana + Anchor Setup for Ubuntu WSL

echo "🚀 Setting up Rust, Solana, and Anchor for AgentMarket..."
echo "=========================================================="
echo ""

# Step 1: Install Rust
echo "📦 Step 1: Installing Rust..."
if command -v rustc &> /dev/null; then
    echo "✅ Rust already installed"
    rustc --version
else
    echo "📥 Downloading Rust installer..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    
    echo "⚙️ Loading Rust environment..."
    source $HOME/.cargo/env
    
    echo "✅ Rust installed!"
    rustc --version
fi

echo ""
echo "📦 Step 2: Installing Solana CLI..."
if command -v solana &> /dev/null; then
    echo "✅ Solana CLI already installed"
    solana --version
else
    echo "📥 Downloading Solana installer..."
    sh -c "$(curl -sSfL https://release.solana.com/stable/install)"
    
    echo "⚙️ Setting up PATH..."
    export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
    
    if ! grep -q "solana/install/active_release/bin" ~/.bashrc; then
        echo 'export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"' >> ~/.bashrc
    fi
    
    echo "✅ Solana installed!"
    solana --version
fi

echo ""
echo "📦 Step 3: Installing cargo-build-sbf..."
if command -v cargo-build-sbf &> /dev/null; then
    echo "✅ cargo-build-sbf already installed"
else
    echo "📥 Installing via cargo..."
    cargo install --git https://github.com/solana-labs/cargo-build-sbf-cli cargo-build-sbf --locked --force
    echo "✅ cargo-build-sbf installed!"
fi

echo ""
echo "📦 Step 4: Installing Anchor..."
if command -v anchor &> /dev/null; then
    echo "✅ Anchor already installed"
    anchor --version
else
    echo "📥 Installing via cargo..."
    cargo install --git https://github.com/coral-xyz/anchor avm --locked --force
    
    echo "⚙️ Setting up Anchor version manager..."
    source $HOME/.cargo/env
    $HOME/.cargo/bin/avm install latest
    $HOME/.cargo/bin/avm use latest
    
    echo "✅ Anchor installed!"
    anchor --version
fi

echo ""
echo "=========================================================="
echo "✅ All tools installed successfully!"
echo ""
echo "📋 Installed versions:"
echo "   Rust: $(rustc --version)"
echo "   Solana: $(solana --version)"
echo "   Cargo Build SBF: $(cargo-build-sbf --version 2>/dev/null || echo 'installed')"
echo "   Anchor: $(anchor --version)"
echo ""
echo "🔄 Next steps:"
echo "   1. Close and reopen your terminal to load PATH changes"
echo "   2. Run: anchor build"
echo "   3. Run: anchor deploy --provider.cluster devnet"
