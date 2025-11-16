#!/usr/bin/env bash
# AWS Amplify Deployment Script for AgentMarket
# Quick reference for manual deployment testing

set -e

echo "🚀 AgentMarket AWS Amplify Deployment Setup"
echo "==========================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm ci
echo "✅ Dependencies installed"
echo ""

# Run type check
echo "🔍 Running TypeScript type check..."
npm run type-check
echo "✅ Type check passed"
echo ""

# Build for production
echo "🔨 Building for production..."
npm run build
echo "✅ Build completed successfully"
echo ""

# List build output
echo "📂 Build artifacts:"
ls -lh .next/
echo ""

echo "✅ Ready for AWS Amplify deployment!"
echo ""
echo "Next steps:"
echo "1. Commit these changes: git add . && git commit -m 'Ready for AWS Amplify deployment'"
echo "2. Push to GitHub: git push origin main"
echo "3. Go to https://console.aws.amazon.com/amplify/ and connect your repo"
echo "4. Amplify will automatically deploy using amplify.yml"
echo ""
echo "The app will be available at: https://main.xxxxx.amplifyapp.com"
