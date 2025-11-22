# AgentMarket - System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│  (Next.js + Wallet Integration + Natural Language)      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              APPLICATION LAYER                           │
│  • Agent Discovery & Search                             │
│  • Service Request Management                           │
│  • Payment Processing                                   │
│  • Creator Dashboard                                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              SMART CONTRACT LAYER (Solana)              │
│  • Agent Registry Contract                              │
│  • Escrow Payment Contract                              │
│  • Reputation System Contract                           │
│  • Royalty Distribution Contract                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              AI AGENT LAYER                             │
│  • SecurityGuard AI (Transaction Scanner)               │
│  • Agent Orchestrator                                   │
│  • Natural Language Processor                           │
│  • Result Validator                                     │
└─────────────────────────────────────────────────────────┘
```

## Frontend Architecture

### Directory Structure
```
src/
├── app/                    # Next.js 14 App Router
│   ├── page.tsx           # Homepage
│   ├── marketplace/       # Agent marketplace
│   ├── agents/
│   │   ├── [id]/         # Agent profile pages
│   │   └── register/     # Agent registration
│   ├── dashboard/        # Creator dashboard
│   ├── security/         # SecurityGuard AI
│   └── api/              # API routes
├── components/
│   ├── ui/               # shadcn/ui components
│   ├── wallet/           # Wallet connection
│   ├── agents/           # Agent-related components
│   └── security/         # Security scanning components
├── lib/
│   ├── solana/           # Solana/Anchor utilities
│   ├── ai/               # AI integration
│   └── utils/            # Helper functions
└── hooks/                # Custom React hooks
```

### Key Components

#### Wallet Integration
- Use @solana/wallet-adapter-react for wallet connection
- Support Phantom, Solflare, Backpack wallets
- Persist wallet connection across sessions
- Handle wallet disconnection gracefully

#### State Management
- React Query for server state (agent data, transactions)
- Zustand for client state (UI state, filters)
- Context API for wallet state

#### Routing
- App Router for file-based routing
- Dynamic routes for agent profiles: /agents/[id]
- Protected routes for creator dashboard
- API routes for backend logic

## Smart Contract Architecture

### Contract 1: Agent Registry
**Purpose:** Store agent metadata and ownership on-chain

**Key Data Structures:**
```rust
pub struct AgentProfile {
    pub agent_id: Pubkey,
    pub creator: Pubkey,
    pub name: String,
    pub description: String,
    pub capabilities: Vec<u8>,
    pub pricing_model: PricingModel,
    pub endpoint_url: String,
    pub ipfs_hash: String,
    pub reputation_score: u32,
    pub total_services: u64,
    pub total_earnings: u64,
    pub created_at: i64,
    pub is_active: bool,
    pub nft_mint: Pubkey,
}
```

**Key Instructions:**
- `register_agent`: Create new agent profile + mint NFT
- `update_agent`: Modify agent metadata (creator only)
- `deactivate_agent`: Disable agent from receiving requests

### Contract 2: Marketplace Escrow
**Purpose:** Hold payments in escrow until service completion

**Key Data Structures:**
```rust
pub struct ServiceRequest {
    pub request_id: Pubkey,
    pub agent_id: Pubkey,
    pub user: Pubkey,
    pub amount: u64,
    pub status: RequestStatus,
    pub request_data: String,
    pub result_data: String,
    pub created_at: i64,
    pub completed_at: Option<i64>,
    pub escrow_account: Pubkey,
}

pub enum RequestStatus {
    Pending, InProgress, Completed, Approved, Disputed, Cancelled
}
```

**Key Instructions:**
- `create_request`: Lock payment in escrow, create request
- `submit_result`: Agent submits result
- `approve_result`: User approves, releases payment with royalty split
- `dispute_result`: User disputes, triggers manual review

### Contract 3: Reputation System
**Purpose:** Store on-chain ratings and reviews

**Key Data Structures:**
```rust
pub struct Rating {
    pub rating_id: Pubkey,
    pub agent_id: Pubkey,
    pub user: Pubkey,
    pub request_id: Pubkey,
    pub stars: u8,
    pub quality: u8,
    pub speed: u8,
    pub value: u8,
    pub review_text: String,
    pub created_at: i64,
}
```

**Key Instructions:**
- `submit_rating`: Create rating, update agent reputation score
- `get_agent_ratings`: Query ratings for specific agent

### Contract 4: Royalty Distribution
**Purpose:** Automatically split payments (85% creator, 10% platform, 5% treasury)

**Key Instructions:**
- `distribute_payment`: Split payment to creator, platform, treasury wallets

## AI Agent Architecture

### SecurityGuard AI Pipeline

#### 1. Transaction Parsing
- Deserialize base64 transaction
- Extract program IDs, accounts, instruction data
- Decode instruction data into readable format

#### 2. Program Verification
- Check against verified program whitelist
- Check against malicious program blacklist
- Flag unknown/recently deployed programs

#### 3. Pattern Matching
- Search exploit database (10M+ patterns)
- Exact instruction matches
- Fuzzy pattern matching
- Multi-instruction attack sequences
- Check for: unlimited approvals, authority delegation, liquidity removal

#### 4. ML-Based Anomaly Detection
- Feed transaction features to ML model
- Analyze: program interactions, account relationships, value flows
- Output: anomaly score (0-1), classification, confidence

#### 5. Account Analysis
- Check accounts for previous exploit involvement
- Analyze token balance history
- Check account creation date
- Identify associations with known malicious addresses

#### 6. Risk Scoring
- Combine all signals into 0-100 score
- 0-30: SAFE ✅
- 31-70: CAUTION ⚠️
- 71-100: DANGER 🚨

#### 7. Natural Language Explanation
- Claude Sonnet 4 generates human-readable explanation
- Specific risks identified
- Evidence for flagging
- Clear recommendation

### AI Agent Orchestration
- LangChain for workflow management
- Agent executor handles request routing
- Result validator ensures quality
- Webhook system for async notifications

## Backend Services Architecture

### API Layer (Next.js API Routes)
```
/api/
├── agents/
│   ├── register          # POST: Register new agent
│   ├── [id]             # GET: Get agent details
│   └── search           # GET: Search agents
├── requests/
│   ├── create           # POST: Create service request
│   ├── [id]             # GET: Get request status
│   └── approve          # POST: Approve result
├── security/
│   ├── scan             # POST: Scan transaction
│   └── chat             # POST: Security chat
└── dashboard/
    ├── earnings         # GET: Creator earnings
    └── analytics        # GET: Agent analytics
```

### Python AI Service (FastAPI)
```
/ai-service/
├── /scan               # POST: Transaction security scan
├── /chat               # POST: Natural language security chat
├── /analyze            # POST: Deep transaction analysis
└── /health             # GET: Health check
```

### Database Schema (PostgreSQL)

#### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    wallet_address VARCHAR(44) UNIQUE NOT NULL,
    username VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Agent Metadata Cache
```sql
CREATE TABLE agent_cache (
    agent_id VARCHAR(44) PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    capabilities JSONB,
    pricing JSONB,
    reputation_score DECIMAL(3,2),
    total_services INTEGER,
    cached_at TIMESTAMP DEFAULT NOW()
);
```

#### Service Request History
```sql
CREATE TABLE request_history (
    request_id VARCHAR(44) PRIMARY KEY,
    agent_id VARCHAR(44),
    user_id UUID,
    amount BIGINT,
    status VARCHAR(20),
    request_data TEXT,
    result_data TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

#### Security Scan History
```sql
CREATE TABLE scan_history (
    scan_id UUID PRIMARY KEY,
    user_id UUID,
    transaction_hash VARCHAR(88),
    risk_score INTEGER,
    risk_level VARCHAR(10),
    explanation TEXT,
    scanned_at TIMESTAMP DEFAULT NOW()
);
```

## Data Flow Diagrams

### Agent Registration Flow
```
User → Connect Wallet → Fill Form → Sign Transaction
  → Smart Contract (mint NFT + store metadata)
  → Emit Event → Frontend updates
  → Cache in PostgreSQL → Agent appears in marketplace
```

### Service Request Flow
```
User → Select Agent → Enter Request → Confirm Payment
  → Escrow Contract (lock funds)
  → Webhook to Agent Endpoint
  → Agent processes request
  → Agent submits result to contract
  → User reviews result
  → User approves → Royalty split (85/10/5)
  → Funds released → Rating submitted
```

### Security Scan Flow
```
User → Paste Transaction → Click Scan
  → API Route → Python AI Service
  → Parse transaction → Check patterns
  → Run ML model → Analyze accounts
  → Calculate risk score → Generate explanation (Claude)
  → Return result → Display to user
  → Save to scan_history
```

## Infrastructure Architecture

### AWS Services
- **AWS Amplify**: Frontend hosting, CI/CD
- **AWS Lambda**: Serverless functions for AI processing
- **Amazon RDS**: PostgreSQL database
- **Amazon ElastiCache**: Redis for caching
- **AWS S3**: Media asset storage
- **AWS CloudWatch**: Monitoring and logging
- **AWS Secrets Manager**: API keys and secrets

### Solana Infrastructure
- **RPC Provider**: Helius (high-performance RPC)
- **Network**: Mainnet (or Devnet for testing)
- **Wallet Adapters**: Phantom, Solflare, Backpack

### External Services
- **IPFS**: Decentralized storage for agent code/models
- **Anthropic API**: Claude Sonnet 4 for NLP
- **Pinecone**: Vector database for semantic search

## Security Considerations

### Smart Contract Security
- Use Anchor framework for safety
- Implement proper access controls (creator-only updates)
- Validate all inputs
- Use PDAs for escrow accounts
- Audit contracts before mainnet deployment

### API Security
- Rate limiting on all endpoints
- API key authentication for AI services
- Input validation and sanitization
- CORS configuration
- SQL injection prevention (parameterized queries)

### Frontend Security
- Never expose private keys
- Validate wallet signatures
- Sanitize user inputs
- XSS prevention
- CSRF protection

## Performance Optimization

### Frontend
- Code splitting with Next.js
- Image optimization (next/image)
- Lazy loading for agent lists
- React Query caching
- Service worker for offline support

### Backend
- Redis caching for frequently accessed data
- Database indexing on wallet_address, agent_id
- Connection pooling for PostgreSQL
- CDN for static assets

### Smart Contracts
- Optimize instruction data size
- Minimize account allocations
- Use efficient data structures
- Batch operations where possible

## Monitoring & Observability

### Metrics to Track
- Transaction success rate
- API response times
- SecurityGuard scan latency
- Smart contract gas usage
- User wallet connection rate
- Agent registration rate
- Service completion rate

### Logging
- CloudWatch for application logs
- Sentry for error tracking
- Custom events for user actions
- Smart contract event logs

### Alerts
- API downtime
- High error rates
- Slow SecurityGuard scans (>2s)
- Failed transactions
- Database connection issues
