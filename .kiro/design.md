# AgentMarket - Technical Design Specification

## System Architecture Overview

AgentMarket is a full-stack decentralized application combining Web3 blockchain technology with advanced AI capabilities. The system consists of four main layers: Frontend (Next.js), Backend Services (FastAPI + Next.js API), Smart Contracts (Solana/Anchor), and AI Agents (SecurityGuard AI + others).

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                        │
│  Next.js 14 + TypeScript + TailwindCSS + Wallet Adapter │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              BACKEND SERVICES LAYER                      │
│  Next.js API Routes + FastAPI + PostgreSQL + Redis      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              SMART CONTRACT LAYER                        │
│  Solana + Anchor + Agent Registry + Escrow + Reputation │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              AI AGENT LAYER                             │
│  SecurityGuard AI + Claude Sonnet 4 + ML Models        │
└─────────────────────────────────────────────────────────┘
```

## Technology Stack

### Frontend Stack
- **Framework**: Next.js 14 with App Router and TypeScript
- **Styling**: TailwindCSS + shadcn/ui component library
- **Web3 Integration**: 
  - @solana/wallet-adapter-react for wallet connections
  - @solana/web3.js for blockchain interactions
  - @coral-xyz/anchor for smart contract interactions
- **State Management**: React Query for server state, Zustand for client state
- **Forms**: React Hook Form + Zod for validation
- **Charts**: Recharts for analytics dashboards

### Backend Stack
- **Web Services**: Next.js API Routes (TypeScript)
- **AI Services**: FastAPI (Python) for SecurityGuard AI
- **Database**: PostgreSQL (AWS RDS) for persistent data
- **Caching**: Redis (AWS ElastiCache) for performance
- **Authentication**: JWT tokens with Solana wallet signatures
- **File Storage**: AWS S3 for media, IPFS for decentralized storage

### Blockchain Stack
- **Network**: Solana (mainnet for production, devnet for development)
- **Framework**: Anchor 0.30+ for smart contract development
- **Language**: Rust for smart contracts
- **RPC Provider**: Helius for reliable Solana RPC access
- **Token Standard**: Metaplex NFT for agent ownership

### AI/ML Stack
- **Primary AI**: Claude Sonnet 4 via Anthropic API
- **ML Framework**: scikit-learn for anomaly detection models
- **Vector Database**: Pinecone for semantic search (future)
- **NLP**: Custom fine-tuned models for Web3 terminology
- **Orchestration**: LangChain for agent workflow management

## Database Schema Design

### PostgreSQL Tables

```sql
-- Users table for off-chain user data
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_address VARCHAR(44) UNIQUE NOT NULL,
    username VARCHAR(50),
    email VARCHAR(255),
    profile_image_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Agents table for off-chain agent metadata
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(44) NOT NULL, -- On-chain agent ID
    creator_wallet VARCHAR(44) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    capabilities JSONB, -- Array of capability strings
    pricing_model JSONB, -- Pricing configuration
    endpoint_url TEXT NOT NULL,
    ipfs_hash VARCHAR(100),
    nft_mint VARCHAR(44), -- Agent ownership NFT
    is_active BOOLEAN DEFAULT true,
    total_earnings BIGINT DEFAULT 0, -- In lamports
    total_services INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_agents_creator (creator_wallet),
    INDEX idx_agents_active (is_active),
    INDEX idx_agents_rating (average_rating DESC)
);

-- Service requests table
CREATE TABLE service_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(44) NOT NULL, -- On-chain request ID
    agent_id VARCHAR(44) NOT NULL,
    user_wallet VARCHAR(44) NOT NULL,
    amount BIGINT NOT NULL, -- Payment in lamports
    status VARCHAR(20) NOT NULL, -- pending, in_progress, completed, approved, disputed
    request_data JSONB, -- User's request details
    result_data JSONB, -- Agent's response
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    INDEX idx_requests_agent (agent_id),
    INDEX idx_requests_user (user_wallet),
    INDEX idx_requests_status (status)
);

-- Ratings table for agent reviews
CREATE TABLE ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rating_id VARCHAR(44) NOT NULL, -- On-chain rating ID
    agent_id VARCHAR(44) NOT NULL,
    user_wallet VARCHAR(44) NOT NULL,
    request_id VARCHAR(44) NOT NULL,
    stars INTEGER NOT NULL CHECK (stars >= 1 AND stars <= 5),
    quality INTEGER CHECK (quality >= 1 AND quality <= 5),
    speed INTEGER CHECK (speed >= 1 AND speed <= 5),
    value INTEGER CHECK (value >= 1 AND value <= 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(request_id), -- One rating per service request
    INDEX idx_ratings_agent (agent_id),
    INDEX idx_ratings_stars (stars DESC)
);

-- SecurityGuard scan history
CREATE TABLE security_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id VARCHAR(44) NOT NULL,
    user_wallet VARCHAR(44),
    transaction_hash VARCHAR(88),
    risk_level VARCHAR(10) NOT NULL, -- SAFE, CAUTION, DANGER
    risk_score INTEGER NOT NULL,
    scan_time_ms INTEGER NOT NULL,
    confidence DECIMAL(3,2) NOT NULL,
    threats_detected JSONB, -- Array of detected threats
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_scans_user (user_wallet),
    INDEX idx_scans_risk (risk_level),
    INDEX idx_scans_created (created_at DESC)
);
```

## Smart Contract Architecture

### Contract 1: Agent Registry

```rust
use anchor_lang::prelude::*;

#[program]
pub mod agent_registry {
    use super::*;

    pub fn register_agent(
        ctx: Context<RegisterAgent>,
        name: String,
        description: String,
        capabilities: Vec<String>,
        pricing: PricingModel,
        endpoint_url: String,
        ipfs_hash: String,
    ) -> Result<()> {
        let agent_profile = &mut ctx.accounts.agent_profile;
        let clock = Clock::get()?;
        
        agent_profile.agent_id = ctx.accounts.agent_profile.key();
        agent_profile.creator = ctx.accounts.creator.key();
        agent_profile.name = name;
        agent_profile.description = description;
        agent_profile.capabilities = capabilities;
        agent_profile.pricing_model = pricing;
        agent_profile.endpoint_url = endpoint_url;
        agent_profile.ipfs_hash = ipfs_hash;
        agent_profile.reputation_score = 0;
        agent_profile.total_services = 0;
        agent_profile.total_earnings = 0;
        agent_profile.created_at = clock.unix_timestamp;
        agent_profile.is_active = true;
        agent_profile.nft_mint = ctx.accounts.nft_mint.key();
        
        // Mint NFT to creator (using Metaplex)
        // Implementation would use Metaplex CPI calls
        
        Ok(())
    }

    pub fn update_agent(
        ctx: Context<UpdateAgent>,
        name: Option<String>,
        description: Option<String>,
        pricing: Option<PricingModel>,
        endpoint_url: Option<String>,
        is_active: Option<bool>,
    ) -> Result<()> {
        let agent_profile = &mut ctx.accounts.agent_profile;
        
        if let Some(name) = name {
            agent_profile.name = name;
        }
        if let Some(description) = description {
            agent_profile.description = description;
        }
        if let Some(pricing) = pricing {
            agent_profile.pricing_model = pricing;
        }
        if let Some(endpoint_url) = endpoint_url {
            agent_profile.endpoint_url = endpoint_url;
        }
        if let Some(is_active) = is_active {
            agent_profile.is_active = is_active;
        }
        
        Ok(())
    }
}

#[account]
pub struct AgentProfile {
    pub agent_id: Pubkey,
    pub creator: Pubkey,
    pub name: String,
    pub description: String,
    pub capabilities: Vec<String>,
    pub pricing_model: PricingModel,
    pub endpoint_url: String,
    pub ipfs_hash: String,
    pub reputation_score: u32, // Average rating * 100
    pub total_services: u64,
    pub total_earnings: u64,
    pub created_at: i64,
    pub is_active: bool,
    pub nft_mint: Pubkey,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub enum PricingModel {
    PerQuery { price: u64 },
    Subscription { monthly: u64 },
    Custom { base: u64, variable: u8 },
}
```

### Contract 2: Marketplace Escrow

```rust
use anchor_lang::prelude::*;

#[program]
pub mod marketplace_escrow {
    use super::*;

    pub fn create_service_request(
        ctx: Context<CreateServiceRequest>,
        agent_id: Pubkey,
        amount: u64,
        request_data: String,
    ) -> Result<()> {
        let service_request = &mut ctx.accounts.service_request;
        let clock = Clock::get()?;
        
        service_request.request_id = ctx.accounts.service_request.key();
        service_request.agent_id = agent_id;
        service_request.user = ctx.accounts.user.key();
        service_request.amount = amount;
        service_request.status = RequestStatus::Pending;
        service_request.request_data = request_data;
        service_request.result_data = String::new();
        service_request.created_at = clock.unix_timestamp;
        service_request.completed_at = None;
        service_request.escrow_account = ctx.accounts.escrow_account.key();
        
        // Transfer payment to escrow PDA
        let transfer_instruction = anchor_lang::solana_program::system_instruction::transfer(
            &ctx.accounts.user.key(),
            &ctx.accounts.escrow_account.key(),
            amount,
        );
        
        anchor_lang::solana_program::program::invoke(
            &transfer_instruction,
            &[
                ctx.accounts.user.to_account_info(),
                ctx.accounts.escrow_account.to_account_info(),
            ],
        )?;
        
        Ok(())
    }

    pub fn submit_result(
        ctx: Context<SubmitResult>,
        result_data: String,
    ) -> Result<()> {
        let service_request = &mut ctx.accounts.service_request;
        let clock = Clock::get()?;
        
        require!(
            service_request.status == RequestStatus::Pending || 
            service_request.status == RequestStatus::InProgress,
            ErrorCode::InvalidRequestStatus
        );
        
        service_request.result_data = result_data;
        service_request.status = RequestStatus::Completed;
        service_request.completed_at = Some(clock.unix_timestamp);
        
        Ok(())
    }

    pub fn approve_result(
        ctx: Context<ApproveResult>,
    ) -> Result<()> {
        let service_request = &mut ctx.accounts.service_request;
        
        require!(
            service_request.status == RequestStatus::Completed,
            ErrorCode::InvalidRequestStatus
        );
        
        service_request.status = RequestStatus::Approved;
        
        // Release payment with royalty split (85% creator, 10% platform, 5% treasury)
        let total_amount = service_request.amount;
        let creator_amount = (total_amount * 85) / 100;
        let platform_amount = (total_amount * 10) / 100;
        let treasury_amount = total_amount - creator_amount - platform_amount;
        
        // Transfer to creator
        **ctx.accounts.escrow_account.try_borrow_mut_lamports()? -= creator_amount;
        **ctx.accounts.creator.try_borrow_mut_lamports()? += creator_amount;
        
        // Transfer to platform
        **ctx.accounts.escrow_account.try_borrow_mut_lamports()? -= platform_amount;
        **ctx.accounts.platform_wallet.try_borrow_mut_lamports()? += platform_amount;
        
        // Transfer to treasury
        **ctx.accounts.escrow_account.try_borrow_mut_lamports()? -= treasury_amount;
        **ctx.accounts.treasury_wallet.try_borrow_mut_lamports()? += treasury_amount;
        
        Ok(())
    }
}

#[account]
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

#[derive(AnchorSerialize, AnchorDeserialize, Clone, PartialEq)]
pub enum RequestStatus {
    Pending,
    InProgress,
    Completed,
    Approved,
    Disputed,
    Cancelled,
}
```

## API Design

### Next.js API Routes

```typescript
// /api/agents/route.ts - Agent marketplace API
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const search = searchParams.get('search');
  const capability = searchParams.get('capability');
  const minRating = searchParams.get('minRating');
  const maxPrice = searchParams.get('maxPrice');
  const sortBy = searchParams.get('sortBy') || 'rating';
  const page = parseInt(searchParams.get('page') || '1');
  const limit = parseInt(searchParams.get('limit') || '20');

  // Query database with filters
  const agents = await getAgents({
    search,
    capability,
    minRating: minRating ? parseFloat(minRating) : undefined,
    maxPrice: maxPrice ? parseInt(maxPrice) : undefined,
    sortBy,
    page,
    limit,
  });

  return Response.json(agents);
}

export async function POST(request: Request) {
  const body = await request.json();
  const { name, description, capabilities, pricing, endpointUrl, ipfsHash } = body;
  
  // Validate request
  const validation = agentRegistrationSchema.safeParse(body);
  if (!validation.success) {
    return Response.json({ error: 'Invalid data' }, { status: 400 });
  }

  // Register agent on-chain
  const agentId = await registerAgentOnChain({
    name,
    description,
    capabilities,
    pricing,
    endpointUrl,
    ipfsHash,
  });

  // Save to database
  const agent = await createAgent({
    agentId,
    ...body,
  });

  return Response.json(agent);
}

// /api/agents/[id]/hire/route.ts - Service request API
export async function POST(
  request: Request,
  { params }: { params: { id: string } }
) {
  const body = await request.json();
  const { requestData, amount } = body;
  const agentId = params.id;

  // Create service request on-chain
  const requestId = await createServiceRequestOnChain({
    agentId,
    amount,
    requestData,
  });

  // Notify agent via webhook
  await notifyAgent(agentId, {
    requestId,
    requestData,
    amount,
  });

  return Response.json({ requestId });
}
```

### FastAPI SecurityGuard Endpoints

```python
# Already implemented in security-ai/main.py
@app.post("/api/security/scan")
async def scan_transaction(request: TransactionScanRequest):
    # Implementation exists - optimized for <2s response time
    pass

@app.post("/api/security/chat")
async def security_chat(request: SecurityChatRequest):
    # Implementation exists - natural language security queries
    pass
```

## Frontend Component Architecture

### Page Structure

```
src/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   └── register/
│   ├── marketplace/
│   │   ├── page.tsx              # Agent marketplace
│   │   ├── [id]/
│   │   │   └── page.tsx          # Agent profile
│   │   └── hire/
│   │       └── [id]/page.tsx     # Hire agent flow
│   ├── dashboard/
│   │   ├── page.tsx              # User dashboard
│   │   ├── creator/
│   │   │   └── page.tsx          # Creator dashboard
│   │   └── history/
│   │       └── page.tsx          # Service history
│   ├── security/
│   │   ├── page.tsx              # SecurityGuard landing
│   │   ├── scan/
│   │   │   └── page.tsx          # Transaction scanner
│   │   └── chat/
│   │       └── page.tsx          # Security chat
│   └── layout.tsx                # Root layout
├── components/
│   ├── ui/                       # shadcn/ui components
│   ├── wallet/
│   │   ├── WalletProvider.tsx
│   │   └── WalletButton.tsx
│   ├── marketplace/
│   │   ├── AgentCard.tsx
│   │   ├── AgentGrid.tsx
│   │   ├── SearchFilters.tsx
│   │   └── HireModal.tsx
│   ├── security/
│   │   ├── TransactionScanner.tsx
│   │   ├── RiskIndicator.tsx
│   │   ├── SecurityChat.tsx
│   │   └── ScanResults.tsx
│   └── dashboard/
│       ├── EarningsCard.tsx
│       ├── PerformanceChart.tsx
│       └── RequestHistory.tsx
└── lib/
    ├── solana.ts                 # Solana/Anchor utilities
    ├── api.ts                    # API client functions
    └── utils.ts                  # General utilities
```

### Key Components

```typescript
// components/marketplace/AgentCard.tsx
interface AgentCardProps {
  agent: {
    id: string;
    name: string;
    description: string;
    capabilities: string[];
    pricing: PricingModel;
    rating: number;
    totalServices: number;
    creator: string;
  };
}

export function AgentCard({ agent }: AgentCardProps) {
  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-semibold text-lg">{agent.name}</h3>
          <p className="text-sm text-muted-foreground">by {agent.creator}</p>
        </div>
        <Badge variant="secondary">{agent.capabilities[0]}</Badge>
      </div>
      
      <p className="text-sm mb-4 line-clamp-2">{agent.description}</p>
      
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-1">
          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
          <span className="text-sm font-medium">{agent.rating}</span>
          <span className="text-xs text-muted-foreground">
            ({agent.totalServices} services)
          </span>
        </div>
        <div className="text-right">
          <p className="text-sm font-medium">{agent.pricing.price} SOL</p>
          <p className="text-xs text-muted-foreground">per query</p>
        </div>
      </div>
      
      <Button className="w-full" onClick={() => openHireModal(agent.id)}>
        Hire Agent
      </Button>
    </Card>
  );
}

// components/security/RiskIndicator.tsx
interface RiskIndicatorProps {
  riskLevel: 'SAFE' | 'CAUTION' | 'DANGER';
  riskScore: number;
  className?: string;
}

export function RiskIndicator({ riskLevel, riskScore, className }: RiskIndicatorProps) {
  const getRiskColor = () => {
    switch (riskLevel) {
      case 'SAFE': return 'text-green-600 bg-green-50 border-green-200';
      case 'CAUTION': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'DANGER': return 'text-red-600 bg-red-50 border-red-200';
    }
  };

  const getRiskIcon = () => {
    switch (riskLevel) {
      case 'SAFE': return <Shield className="h-5 w-5" />;
      case 'CAUTION': return <AlertTriangle className="h-5 w-5" />;
      case 'DANGER': return <AlertCircle className="h-5 w-5" />;
    }
  };

  return (
    <div className={cn("flex items-center gap-3 p-4 rounded-lg border", getRiskColor(), className)}>
      {getRiskIcon()}
      <div>
        <p className="font-semibold">{riskLevel}</p>
        <p className="text-sm">Risk Score: {riskScore}/100</p>
      </div>
    </div>
  );
}
```

## Performance Optimization Strategy

### Frontend Performance
- **Code Splitting**: Dynamic imports for heavy components
- **Image Optimization**: Next.js Image component with WebP
- **Caching**: React Query for server state caching
- **Bundle Analysis**: Regular bundle size monitoring
- **Lazy Loading**: Intersection Observer for below-fold content

### Backend Performance
- **Database Optimization**: Proper indexing, query optimization
- **Caching Strategy**: Redis for frequently accessed data
- **Connection Pooling**: PostgreSQL connection pooling
- **API Rate Limiting**: Prevent abuse and ensure fair usage
- **CDN**: CloudFront for static asset delivery

### Blockchain Performance
- **RPC Optimization**: Multiple RPC endpoints with failover
- **Transaction Batching**: Batch multiple operations when possible
- **Account Caching**: Cache frequently accessed account data
- **Parallel Processing**: Concurrent blockchain queries
- **Gas Optimization**: Optimize smart contract instructions

## Security Architecture

### Smart Contract Security
- **Access Controls**: Proper ownership and permission checks
- **Input Validation**: Validate all parameters and constraints
- **Reentrancy Protection**: Use appropriate guards
- **Integer Overflow**: Use safe math operations
- **Audit Requirements**: Professional security audit before mainnet

### Application Security
- **Authentication**: JWT tokens with wallet signature verification
- **Authorization**: Role-based access control
- **Input Sanitization**: Validate and sanitize all user inputs
- **Rate Limiting**: Prevent abuse and DoS attacks
- **HTTPS Enforcement**: All communications encrypted

### Data Security
- **No Private Keys**: Never store or transmit private keys
- **Minimal Data Storage**: Store only necessary user data
- **Data Encryption**: Encrypt sensitive data at rest
- **Privacy Compliance**: GDPR and privacy regulation compliance
- **Audit Logging**: Log security-relevant events

## Deployment Architecture

### Development Environment
- **Local Development**: Docker Compose for local services
- **Solana Devnet**: For smart contract testing
- **Test Database**: Local PostgreSQL and Redis instances
- **Hot Reloading**: Next.js and FastAPI development servers

### Production Environment
- **Frontend**: AWS Amplify with CloudFront CDN
- **Backend**: AWS Lambda for serverless functions
- **Database**: Amazon RDS (PostgreSQL) with read replicas
- **Cache**: Amazon ElastiCache (Redis) cluster
- **Monitoring**: CloudWatch, Sentry, and custom dashboards

### CI/CD Pipeline
- **Source Control**: GitHub with protected main branch
- **Testing**: Automated unit, integration, and E2E tests
- **Security Scanning**: Automated vulnerability scanning
- **Deployment**: Automated deployment on merge to main
- **Rollback**: Quick rollback capability for issues

This technical design provides a comprehensive foundation for building a production-ready, scalable, and secure AI agent marketplace that can handle the demands of the hackathon and beyond.