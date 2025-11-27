# AgentMarket - Project Context

## Project Overview

**Name:** AgentMarket  
**Tagline:** "The First Decentralized Marketplace Where AI Agents Earn, Humans Prosper, and Innovation is Rewarded"  
**Live Demo:** https://main.d1qz5jyb1c9oee.amplifyapp.com  
**GitHub:** https://github.com/iamaanahmad/agentmarket

**One-Line Description:** A Web3-powered marketplace platform where autonomous AI agents offer services for crypto micropayments, with SecurityGuard AI as the flagship agent protecting users from blockchain exploits.

## Hackathon Context

**Event:** AWS Global Vibe: AI Coding Hackathon 2025  
**Organizer:** DoraHacks + Amazon Web Services  
**Prize Pool:** $700,000+ USD  
**Track:** Web3 AI Integration  
**Submission Deadline:** December 1, 2025, 11:59 PM PST  
**Development Tool:** Kiro IDE (mandatory requirement)

## Problem Statement

### Problem 1: No Trusted AI Agent Marketplace
- AI agent economy is exploding ($637M raised in 2025)
- Creators have no easy way to monetize AI models/agents
- Users have no trusted platform to discover and hire AI services
- Current platforms charge 20-30% fees with payment delays

### Problem 2: Web3 Security Crisis
- $2 billion lost to wallet exploits in 2024
- Users lack real-time protection before signing transactions
- Complex security tools intimidate newcomers
- No AI-powered transaction analysis available

### Problem 3: Web3 Accessibility Barrier
- 65% of new Web3 users abandon within first month
- Technical complexity prevents mass adoption
- No natural language interface for blockchain operations

## Solution Architecture

### Core Platform: AgentMarket
A decentralized marketplace where:
- Creators register AI agents as on-chain NFTs
- Users discover and hire agents with crypto micropayments
- Smart contracts enforce fair payment and royalty splits (85% creator, 10% platform, 5% treasury)
- Reputation system ensures quality and trust
- Anyone can participate without intermediaries

### Launch Agent: SecurityGuard AI
A flagship AI agent that:
- Scans transactions before signing (real-time protection)
- Detects wallet drainers, rug pulls, malicious contracts
- Explains risks in natural language
- Charges 0.01 SOL per scan (~$2)
- Proves marketplace utility from day one

## Technology Stack

### Frontend
- Framework: Next.js 14 (App Router with TypeScript)
- Styling: TailwindCSS + shadcn/ui components
- State Management: React Query + Zustand
- Web3: @solana/wallet-adapter-react, @solana/web3.js
- Wallets: Phantom, Solflare, Backpack

### Smart Contracts (Solana)
- Framework: Anchor 0.30+
- Language: Rust
- Programs:
  - agent_registry: Agent registration, metadata storage
  - marketplace_escrow: Payment holding and release
  - reputation_system: On-chain ratings and reviews
  - royalty_splitter: Automated payment distribution

### AI Layer
- Primary AI: Google Gemini 1.5 Flash (via Google AI API)
- Security Analysis: Custom ML model trained on exploit patterns
- NLP Interface: Fine-tuned model for Web3 terminology
- Orchestration: LangChain for agent workflow management
- Vector DB: Pinecone for semantic search of agents

### Backend Services
- API Framework: Next.js API Routes + FastAPI (Python for AI)
- Database: PostgreSQL (AWS RDS) for off-chain data
- Caching: Redis (AWS ElastiCache)
- Storage: IPFS for agent code/models, AWS S3 for media

### Infrastructure
- Development: Kiro IDE with AWS Q Developer integration
- Frontend Hosting: AWS Amplify
- Backend Functions: AWS Lambda (serverless)
- Database: Amazon RDS (PostgreSQL)
- Monitoring: AWS CloudWatch + Sentry
- RPC Provider: Helius (Solana)

## Core Features (MVP)

### Phase 1: Core Marketplace
1. Agent Registration - Creators register AI agents on-chain with NFT ownership
2. Agent Discovery & Search - Users find agents by capability, price, rating
3. Service Request & Escrow Payment - Hire agents with crypto, escrow protection
4. Reputation System - On-chain ratings and reviews
5. Creator Dashboard - Earnings tracking, performance metrics, withdrawals

### Phase 2: SecurityGuard AI Agent
6. Transaction Security Scanning - AI-powered transaction analysis (<2 seconds)
7. Natural Language Security Interface - Ask security questions in plain English
8. Exploit Pattern Database - 10M+ patterns, 99.8%+ detection accuracy

### Phase 3: Advanced Features (Post-MVP)
9. Natural Language Agent Hiring - Describe needs in plain English
10. Multi-Agent Workflows - Chain multiple agents for complex tasks

## Key Performance Targets

### SecurityGuard AI
- Latency: <2 seconds (95th percentile)
- Accuracy: 99.8% detection of known exploits
- False Positives: <0.5%
- Throughput: 100 scans/second
- Uptime: 99.9%

### Platform
- Agent registration: <5 seconds on-chain
- Search results: <500ms
- Service completion: <2 minutes (for fast agents)
- Gas fees: <0.01 SOL per transaction
- Mobile responsive: All pages

## Business Model

### Revenue Streams
- Marketplace fee: 10% of all transactions
- Platform treasury: 5% of all transactions
- Creator earnings: 85% of all transactions

### Value Proposition
- For Creators: Monetize AI agents, earn forever via royalties
- For Users: Access AI services with crypto, no traditional payment friction
- For Platform: Network effects, sustainable fee model

## Winning Strategy

### Innovation (25 points)
- First AI agent marketplace on Solana - Category creation
- Novel economic model - Creators earn forever via royalties
- Dual value proposition - Platform + Utility agent
- Future-forward - Positioned for AI agent economy explosion

### Technical Excellence (25 points)
- Full-stack complexity - Smart contracts + AI + Frontend
- Perfect Kiro IDE showcase - Complete spec-driven development
- Advanced AI integration - ML models + Natural language + Real-time analysis
- Solana native - Leverages speed and low fees

### Real-world Impact (20 points)
- Solves $2B problem - Prevents wallet exploits
- Empowers creators - New income stream for AI builders
- Accessible to all - No technical knowledge required
- Open source - Benefits entire ecosystem

## Project Timeline

**Week 1 (Nov 4-10):** Foundation - Setup, specs, smart contracts, frontend foundation  
**Week 2 (Nov 11-17):** Core Marketplace - Registration, discovery, payments, reputation  
**Week 3 (Nov 18-24):** SecurityGuard AI - Transaction analysis, ML models, UI  
**Week 4 (Nov 25-Dec 1):** Polish & Demo - Testing, UI/UX, video, documentation, submission

## Success Metrics

### Technical
- All smart contracts deployed and tested
- SecurityGuard AI achieving <2s response time
- 99.8%+ exploit detection accuracy
- Mobile responsive UI
- Zero critical bugs

### Hackathon
- Complete .kiro folder structure (requirements.md, design.md, tasks.md)
- Documented AWS Q Developer usage
- Professional demo video (3-5 minutes)
- Comprehensive documentation
- Submission before deadline

### Impact
- Solves real Web3 security problem
- Enables new AI agent economy
- Open source contribution to ecosystem
- Clear path to sustainability and growth
