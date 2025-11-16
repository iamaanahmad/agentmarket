# Marketplace API - Technical Design

## Overview

The Marketplace API provides RESTful endpoints for the AgentMarket platform, built using Next.js 14 API Routes. The API serves as the bridge between the React frontend, PostgreSQL database, Solana blockchain, and SecurityGuard AI service. All endpoints are serverless functions deployed on AWS Lambda via AWS Amplify.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  FRONTEND (Next.js)                      │
│              React Components + Hooks                    │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/JSON
┌────────────────────▼────────────────────────────────────┐
│              MARKETPLACE API LAYER                       │
│         Next.js 14 API Routes (Serverless)              │
│  ┌──────────┬──────────┬──────────┬──────────┐         │
│  │ Agents   │ Requests │ Security │ Ratings  │         │
│  │ Routes   │ Routes   │ Routes   │ Routes   │         │
│  └──────────┴──────────┴──────────┴──────────┘         │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼──────┐ ┌──▼────────────┐
│ PostgreSQL   │ │ Solana  │ │ SecurityGuard │
│ (RDS)        │ │ RPC     │ │ AI (FastAPI)  │
└──────────────┘ └─────────┘ └───────────────┘
```

## Technology Stack

### Core Technologies
- **Runtime**: Node.js 18+ (AWS Lambda)
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript 5+
- **Database Client**: node-postgres (pg) v8.11+
- **HTTP Client**: Native fetch API

### Database
- **Database**: PostgreSQL 15 (Amazon RDS)
- **Connection Pooling**: pg.Pool with max 10 connections
- **Transaction Support**: BEGIN/COMMIT/ROLLBACK
- **SSL**: Enabled with rejectUnauthorized: false for RDS

## API Endpoint Design

### 1. Agent Endpoints

#### GET /api/agents
**Purpose**: List all active agents with search and filtering

**Query Parameters**:
```typescript
interface AgentListParams {
  page?: number        // Default: 1
  limit?: number       // Default: 10, Max: 50
  search?: string      // Search in name/description
  capability?: string  // Filter by capability
  minRating?: number   // Minimum rating (0-5)
  maxPrice?: number    // Maximum price in lamports
  sortBy?: 'rating' | 'newest' | 'popular'  // Default: 'rating'
}
```

**Response**:
```typescript
interface AgentListResponse {
  agents: Array<{
    id: string
    agentId: string
    name: string
    description: string
    capabilities: string[]
    pricing: {
      price: number
      currency: string
    }
    endpoint: string
    creatorWallet: string
    rating: {
      average: number
      count: number
    }
    createdAt: string
  }>
  pagination: {
    page: number
    limit: number
    total: number
    pages: number
  }
}
```

**Database Query**:
```sql
SELECT 
  a.id, a.agent_id, a.name, a.description, a.capabilities, a.pricing,
  a.endpoint, a.creator_wallet, a.active, a.created_at,
  COALESCE(AVG(r.stars), 0)::float as avg_rating,
  COUNT(r.id) as rating_count
FROM agents a
LEFT JOIN ratings r ON a.agent_id = r.agent_id
WHERE a.active = true
  AND (a.name ILIKE $1 OR a.description ILIKE $1)  -- if search provided
GROUP BY a.id
ORDER BY a.created_at DESC
LIMIT $2 OFFSET $3
```

#### POST /api/agents
**Purpose**: Register a new AI agent

**Request Body**:
```typescript
interface AgentRegistrationRequest {
  name: string              // Required, max 100 chars
  description: string       // Optional, max 1000 chars
  capabilities: string[]    // Array of capability strings
  pricing: {
    price: number          // Price in lamports
    currency: string       // 'SOL'
  }
  endpoint: string          // Agent webhook URL
  creatorWallet: string     // Required, Solana wallet address
}
```

**Response**:
```typescript
interface AgentRegistrationResponse {
  success: boolean
  agent: {
    id: string
    agentId: string
    name: string
    createdAt: string
  }
  message: string
}
```

**Validation Rules**:
- name: Required, 1-100 characters
- creatorWallet: Required, valid Solana address format
- pricing.price: Must be >= 0
- capabilities: Array with at least 1 item

### 2. Service Request Endpoints

#### POST /api/requests
**Purpose**: Create a new service request

**Request Body**:
```typescript
interface CreateRequestBody {
  agentId: string           // Required
  userWallet: string        // Required
  amount: number            // Required, in lamports
  requestData: {            // Optional metadata
    prompt?: string
    parameters?: Record<string, any>
  }
}
```

**Response**:
```typescript
interface CreateRequestResponse {
  success: boolean
  request: {
    id: string
    requestId: string
    agentId: string
    status: 'pending'
    amount: number
    createdAt: string
  }
  message: string
}
```

**Business Logic**:
1. Validate agent exists and is active
2. Generate unique request_id
3. Insert service_request record with status 'pending'
4. (Future) Trigger webhook to agent endpoint
5. Return request details

#### GET /api/requests
**Purpose**: List service requests with filtering

**Query Parameters**:
```typescript
interface RequestListParams {
  userWallet?: string      // Filter by user
  agentId?: string         // Filter by agent
  status?: 'pending' | 'in_progress' | 'completed' | 'approved' | 'disputed'
  page?: number
  limit?: number
}
```

**Response**:
```typescript
interface RequestListResponse {
  requests: Array<{
    id: string
    requestId: string
    agentId: string
    agentName: string
    userWallet: string
    amount: number
    status: string
    requestData: any
    resultData: any
    createdAt: string
    completedAt: string | null
  }>
  pagination: PaginationResult
}
```

#### POST /api/requests/[id]/approve
**Purpose**: Approve completed service request and release payment

**Request Body**:
```typescript
interface ApproveRequestBody {
  userWallet: string        // Required for authorization
  rating?: {                // Optional rating
    stars: number          // 1-5
    quality?: number       // 1-5
    speed?: number         // 1-5
    value?: number         // 1-5
    reviewText?: string
  }
}
```

**Response**:
```typescript
interface ApproveRequestResponse {
  success: boolean
  message: string
  payment: {
    total: number
    creator: number        // 85%
    platform: number       // 10%
    treasury: number       // 5%
  }
}
```

**Transaction Flow**:
```typescript
BEGIN TRANSACTION

1. Fetch service_request by request_id
2. Verify user_wallet matches request owner
3. Verify status is 'completed'
4. Update status to 'approved'
5. Calculate payment splits
6. Update agent total_earnings and total_services
7. If rating provided:
   - Insert rating record
   - Recalculate agent average_rating
8. (Future) Trigger on-chain payment distribution

COMMIT TRANSACTION
```

#### POST /api/requests/[id]/dispute
**Purpose**: Dispute a completed service request

**Request Body**:
```typescript
interface DisputeRequestBody {
  userWallet: string        // Required
  reason: string            // Required, dispute explanation
}
```

**Response**:
```typescript
interface DisputeRequestResponse {
  success: boolean
  message: string
  dispute: {
    disputeId: string
    requestId: string
    status: 'pending'
    reason: string
  }
}
```

**Transaction Flow**:
```typescript
BEGIN TRANSACTION

1. Fetch service_request by request_id
2. Verify user_wallet matches request owner
3. Verify status is 'completed'
4. Update status to 'disputed'
5. Add dispute_reason to request_data
6. Insert dispute record
7. (Future) Notify platform admins

COMMIT TRANSACTION
```

#### GET /api/requests/[id]/dispute
**Purpose**: Retrieve dispute details

**Response**:
```typescript
interface DisputeDetailsResponse {
  dispute: {
    disputeId: string
    requestId: string
    agentId: string
    agentName: string
    userWallet: string
    reason: string
    status: 'pending' | 'resolved' | 'rejected'
    resolution: string | null
    createdAt: string
    resolvedAt: string | null
  }
}
```

### 3. Security Scan Endpoints

#### POST /api/security/scan
**Purpose**: Scan a Solana transaction for security threats

**Request Body**:
```typescript
interface SecurityScanRequest {
  transaction: {
    serialized?: string    // Base64 encoded transaction
    instructions?: Array<{
      programId: string
      accounts: string[]
      data: string
    }>
  }
  userWallet?: string      // Optional for history tracking
}
```

**Response**:
```typescript
interface SecurityScanResponse {
  success: boolean
  scanId: string
  riskLevel: 'SAFE' | 'CAUTION' | 'DANGER'
  riskScore: number        // 0-100
  explanation: string
  recommendation: string
  details: {
    program_checks: {
      unknown_programs: number
      blacklisted_programs: number
      verified_programs: number
    }
    pattern_matches: string[]
    ml_analysis: {
      anomaly_score: number
      classification: string
      confidence: number
    }
    account_flags: string[]
  }
  scanTimeMs: number
  confidence: number
  threatsDetected: string[]
}
```

**Integration Flow**:
```typescript
1. Receive scan request from frontend
2. Forward to SecurityGuard AI backend (FastAPI)
   POST http://localhost:8000/api/security/scan
3. Wait for analysis result (timeout: 5 seconds)
4. Save scan result to database
5. Return result to frontend
6. Handle errors gracefully (503 if AI unavailable)
```

#### GET /api/security/scan
**Purpose**: Retrieve scan history and statistics

**Query Parameters**:
```typescript
interface ScanHistoryParams {
  userWallet?: string
  riskLevel?: 'SAFE' | 'CAUTION' | 'DANGER'
  page?: number
  limit?: number
}
```

**Response**:
```typescript
interface ScanHistoryResponse {
  scans: Array<{
    scanId: string
    userWallet: string | null
    transactionHash: string | null
    riskLevel: string
    riskScore: number
    scanTimeMs: number
    confidence: number
    threatsDetected: any[]
    createdAt: string
  }>
  pagination: PaginationResult
  statistics: {
    totalScans: number
    threatsBlocked: number
    avgScanTime: number
    usersProtected: number
  }
}
```

## Database Layer Design

### Connection Management

**Database Configuration**:
```typescript
// src/lib/db.ts
import { Pool, PoolConfig } from 'pg'

export const RDS_CONFIG: PoolConfig = {
  host: process.env.DB_HOST || 'agentmarket-dev-db.c76o0iokgzxb.ap-south-1.rds.amazonaws.com',
  port: parseInt(process.env.DB_PORT || '5432'),
  user: process.env.DB_USER || 'agentadmin',
  password: process.env.DB_PASSWORD || 'AgentMarket2025Secure',
  database: process.env.DB_NAME || 'agentmarket_dev',
  ssl: { rejectUnauthorized: false },
  max: 10,                      // Maximum pool size
  idleTimeoutMillis: 30000,     // Close idle connections after 30s
  connectionTimeoutMillis: 10000 // Connection timeout
}

export function createPool(config?: Partial<PoolConfig>): Pool {
  return new Pool({ ...RDS_CONFIG, ...config })
}
```

**Connection Pattern**:
```typescript
export async function GET(request: NextRequest) {
  const pool = createPool()
  let client

  try {
    client = await pool.connect()
    const result = await client.query('SELECT * FROM agents')
    return NextResponse.json({ data: result.rows })
  } catch (error) {
    console.error('Database error:', error)
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  } finally {
    if (client) client.release()  // Always release connection
    await pool.end()               // Close pool
  }
}
```

### Transaction Helper

```typescript
// src/lib/db.ts
export async function transaction<T>(
  callback: (client: any) => Promise<T>
): Promise<T> {
  const pool = createPool()
  let client

  try {
    client = await pool.connect()
    await client.query('BEGIN')
    
    const result = await callback(client)
    
    await client.query('COMMIT')
    return result
  } catch (error) {
    if (client) {
      await client.query('ROLLBACK')
    }
    throw error
  } finally {
    if (client) client.release()
    await pool.end()
  }
}
```

**Usage Example**:
```typescript
import { transaction } from '@/lib/db'

export async function POST(request: NextRequest) {
  try {
    const result = await transaction(async (client) => {
      // All queries in this block are part of the transaction
      await client.query('UPDATE service_requests SET status = $1 WHERE id = $2', ['approved', id])
      await client.query('UPDATE agents SET total_earnings = total_earnings + $1 WHERE id = $2', [amount, agentId])
      return { success: true }
    })
    
    return NextResponse.json(result)
  } catch (error) {
    return NextResponse.json({ error: 'Transaction failed' }, { status: 500 })
  }
}
```

### Pagination Helper

```typescript
// src/lib/db.ts
export interface PaginationParams {
  page?: number
  limit?: number
}

export function buildPagination(params: PaginationParams) {
  const page = Math.max(1, params.page || 1)
  const limit = Math.min(50, Math.max(1, params.limit || 20))
  const offset = (page - 1) * limit
  return { page, limit, offset }
}

export function calculatePagination(total: number, params: { page: number; limit: number }) {
  return {
    page: params.page,
    limit: params.limit,
    total,
    pages: Math.ceil(total / params.limit)
  }
}
```

## Error Handling Strategy

### Error Response Format

```typescript
interface ErrorResponse {
  error: string              // Human-readable error message
  details?: string           // Additional error details
  code?: string              // Error code for programmatic handling
}
```

### HTTP Status Codes

- **200 OK**: Successful GET/POST request
- **400 Bad Request**: Validation error, missing required fields
- **403 Forbidden**: Authorization error (not your resource)
- **404 Not Found**: Resource doesn't exist
- **500 Internal Server Error**: Database error, unexpected error
- **503 Service Unavailable**: External service (SecurityGuard AI) unavailable

### Error Handling Pattern

```typescript
export async function POST(request: NextRequest) {
  const pool = createPool()
  let client

  try {
    const body = await request.json()
    
    // Validation
    if (!body.name?.trim()) {
      return NextResponse.json(
        { error: 'Agent name is required' },
        { status: 400 }
      )
    }
    
    client = await pool.connect()
    const result = await client.query('INSERT INTO agents ...')
    
    return NextResponse.json({ success: true, data: result.rows[0] })
    
  } catch (error: unknown) {
    console.error('POST /api/agents error:', error)
    
    // Handle specific error types
    if (error instanceof SyntaxError) {
      return NextResponse.json(
        { error: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }
    
    return NextResponse.json(
      { 
        error: 'Failed to register agent',
        details: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    )
  } finally {
    if (client) client.release()
    await pool.end()
  }
}
```

## Security Considerations

### Input Validation
- Validate all user inputs before database queries
- Use parameterized queries to prevent SQL injection
- Sanitize string inputs (trim whitespace, check length)
- Validate Solana wallet addresses format

### SQL Injection Prevention
```typescript
// ✅ GOOD: Parameterized query
await client.query(
  'SELECT * FROM agents WHERE agent_id = $1',
  [agentId]
)

// ❌ BAD: String concatenation
await client.query(
  `SELECT * FROM agents WHERE agent_id = '${agentId}'`
)
```

### Authorization
- Verify user owns resources before modification
- Check wallet address matches request owner
- Implement JWT authentication (future enhancement)

### Rate Limiting
- Implement rate limiting per IP address (future)
- Target: 60 requests per minute per IP
- Use Redis for distributed rate limiting

## Performance Optimization

### Database Indexes
```sql
-- Already created in init_database.sql
CREATE INDEX idx_agents_creator ON agents(creator_wallet);
CREATE INDEX idx_agents_active ON agents(active);
CREATE INDEX idx_agents_rating ON agents(average_rating DESC);
CREATE INDEX idx_requests_agent ON service_requests(agent_id);
CREATE INDEX idx_requests_user ON service_requests(user_wallet);
CREATE INDEX idx_requests_status ON service_requests(status);
```

### Query Optimization
- Use `LIMIT` and `OFFSET` for pagination
- Use `LEFT JOIN` instead of multiple queries
- Aggregate ratings in single query with `AVG()` and `COUNT()`
- Use `COALESCE()` for default values

### Caching Strategy (Future)
- Cache agent list for 5 minutes (Redis)
- Cache agent profiles for 1 minute
- Invalidate cache on agent updates
- Use ETags for conditional requests

## Testing Strategy

### Unit Tests
- Test database helper functions
- Test pagination logic
- Test error handling
- Mock database connections

### Integration Tests
- Test full API endpoint flows
- Test database transactions
- Test error scenarios
- Use test database

### Performance Tests
- Load test with 100 concurrent requests
- Measure response times (p50, p95, p99)
- Test connection pool under load
- Monitor database query performance

## Deployment Configuration

### Environment Variables
```bash
# Database
DB_HOST=agentmarket-dev-db.c76o0iokgzxb.ap-south-1.rds.amazonaws.com
DB_PORT=5432
DB_USER=agentadmin
DB_PASSWORD=AgentMarket2025Secure
DB_NAME=agentmarket_dev
DB_SSL=true

# SecurityGuard AI
SECURITY_AI_URL=http://localhost:8000

# Platform Configuration
PLATFORM_WALLET=<solana_wallet_address>
TREASURY_WALLET=<solana_wallet_address>
```

### AWS Amplify Configuration
- Deploy Next.js app to Amplify
- API routes automatically deployed as Lambda functions
- Environment variables configured in Amplify console
- CloudWatch logs enabled for monitoring

## Monitoring and Logging

### Logging Strategy
- Log all errors with context
- Log slow queries (>1 second)
- Log connection pool metrics
- Use structured logging (JSON)

### Metrics to Track
- API response times (p50, p95, p99)
- Error rates by endpoint
- Database connection pool usage
- SecurityGuard AI availability
- Request volume by endpoint

### CloudWatch Alarms
- Lambda errors > 5 per minute
- API latency p99 > 2 seconds
- Database connection pool exhaustion
- SecurityGuard AI failures > 10%

This design provides a robust, scalable API layer that meets all requirements while maintaining security, performance, and maintainability standards for the hackathon submission.
