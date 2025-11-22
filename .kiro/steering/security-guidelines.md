# AgentMarket - Security Guidelines

## Overview

Security is paramount for AgentMarket. We're handling user funds, private keys, and sensitive transaction data. This document outlines security best practices across all layers of the application.

## Smart Contract Security

### Access Control

#### Creator-Only Operations
```rust
// Always verify the signer is the creator
pub fn update_agent(ctx: Context<UpdateAgent>, new_description: String) -> Result<()> {
    let agent = &ctx.accounts.agent;
    
    require!(
        ctx.accounts.signer.key() == agent.creator,
        ErrorCode::Unauthorized
    );
    
    // Update logic
    Ok(())
}
```

#### Admin Operations
```rust
// Use a dedicated admin account for platform operations
#[account]
pub struct PlatformConfig {
    pub admin: Pubkey,
    pub platform_wallet: Pubkey,
    pub treasury_wallet: Pubkey,
}

pub fn update_platform_fee(ctx: Context<UpdateFee>, new_fee: u8) -> Result<()> {
    require!(
        ctx.accounts.signer.key() == ctx.accounts.config.admin,
        ErrorCode::Unauthorized
    );
    
    require!(new_fee <= 20, ErrorCode::FeeTooHigh); // Max 20%
    
    Ok(())
}
```

### Input Validation

#### String Length Limits
```rust
const MAX_NAME_LENGTH: usize = 50;
const MAX_DESCRIPTION_LENGTH: usize = 500;
const MAX_URL_LENGTH: usize = 200;

pub fn register_agent(
    ctx: Context<RegisterAgent>,
    name: String,
    description: String,
    endpoint_url: String,
) -> Result<()> {
    // Validate all string inputs
    require!(
        name.len() > 0 && name.len() <= MAX_NAME_LENGTH,
        ErrorCode::InvalidNameLength
    );
    
    require!(
        description.len() > 0 && description.len() <= MAX_DESCRIPTION_LENGTH,
        ErrorCode::InvalidDescriptionLength
    );
    
    require!(
        endpoint_url.len() > 0 && endpoint_url.len() <= MAX_URL_LENGTH,
        ErrorCode::InvalidUrlLength
    );
    
    Ok(())
}
```

#### Numeric Validation
```rust
pub fn create_request(
    ctx: Context<CreateRequest>,
    amount: u64,
) -> Result<()> {
    // Ensure amount is reasonable
    require!(amount > 0, ErrorCode::InvalidAmount);
    require!(amount <= 1_000_000_000_000, ErrorCode::AmountTooHigh); // Max 1000 SOL
    
    Ok(())
}
```

### State Management

#### Prevent Reentrancy
```rust
// Use account constraints to prevent invalid state transitions
#[derive(Accounts)]
pub struct ApproveResult<'info> {
    #[account(
        mut,
        constraint = request.status == RequestStatus::Completed @ ErrorCode::InvalidStatus,
        constraint = request.user == user.key() @ ErrorCode::Unauthorized
    )]
    pub request: Account<'info, ServiceRequest>,
    
    pub user: Signer<'info>,
}

pub fn approve_result(ctx: Context<ApproveResult>) -> Result<()> {
    let request = &mut ctx.accounts.request;
    
    // Change state BEFORE transferring funds
    request.status = RequestStatus::Approved;
    
    // Transfer funds
    // ...
    
    Ok(())
}
```

#### Atomic Operations
```rust
// Ensure all operations in a transaction succeed or fail together
pub fn distribute_payment(ctx: Context<DistributePayment>, amount: u64) -> Result<()> {
    let creator_amount = amount * 85 / 100;
    let platform_amount = amount * 10 / 100;
    let treasury_amount = amount * 5 / 100;
    
    // All transfers must succeed
    transfer_sol(ctx.accounts.escrow, ctx.accounts.creator, creator_amount)?;
    transfer_sol(ctx.accounts.escrow, ctx.accounts.platform, platform_amount)?;
    transfer_sol(ctx.accounts.escrow, ctx.accounts.treasury, treasury_amount)?;
    
    Ok(())
}
```

### PDA Security

#### Proper PDA Derivation
```rust
// Use consistent seeds for PDA derivation
pub fn create_escrow(ctx: Context<CreateEscrow>, request_id: Pubkey) -> Result<()> {
    let (escrow_pda, bump) = Pubkey::find_program_address(
        &[
            b"escrow",
            request_id.as_ref(),
        ],
        ctx.program_id
    );
    
    // Verify the derived PDA matches the provided account
    require!(
        escrow_pda == ctx.accounts.escrow.key(),
        ErrorCode::InvalidPDA
    );
    
    Ok(())
}
```

### Integer Overflow Protection

```rust
// Use checked arithmetic operations
pub fn update_earnings(ctx: Context<UpdateEarnings>, amount: u64) -> Result<()> {
    let agent = &mut ctx.accounts.agent;
    
    // Use checked_add to prevent overflow
    agent.total_earnings = agent.total_earnings
        .checked_add(amount)
        .ok_or(ErrorCode::MathOverflow)?;
    
    agent.total_services = agent.total_services
        .checked_add(1)
        .ok_or(ErrorCode::MathOverflow)?;
    
    Ok(())
}
```

## Frontend Security

### Wallet Security

#### Never Expose Private Keys
```typescript
// NEVER do this
const privateKey = wallet.privateKey; // ❌ WRONG

// Use wallet adapter for signing
const { signTransaction, publicKey } = useWallet();

async function sendTransaction(tx: Transaction) {
  // Wallet adapter handles signing securely
  const signed = await signTransaction(tx);
  const signature = await connection.sendRawTransaction(signed.serialize());
  return signature;
}
```

#### Validate Wallet Connection
```typescript
function useRequireWallet() {
  const { connected, publicKey } = useWallet();
  
  useEffect(() => {
    if (!connected || !publicKey) {
      // Redirect to connect wallet page
      router.push('/connect');
    }
  }, [connected, publicKey]);
  
  return { publicKey };
}
```

### Input Validation

#### Sanitize User Inputs
```typescript
import DOMPurify from 'isomorphic-dompurify';

function sanitizeInput(input: string): string {
  // Remove HTML tags and scripts
  return DOMPurify.sanitize(input, { 
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: []
  });
}

// Use in forms
const handleSubmit = (data: FormData) => {
  const sanitized = {
    name: sanitizeInput(data.name),
    description: sanitizeInput(data.description),
  };
  
  // Submit sanitized data
};
```

#### Validate Solana Addresses
```typescript
import { PublicKey } from '@solana/web3.js';

function isValidSolanaAddress(address: string): boolean {
  try {
    new PublicKey(address);
    return true;
  } catch {
    return false;
  }
}

// Use in forms
const validateAddress = (value: string) => {
  if (!isValidSolanaAddress(value)) {
    return 'Invalid Solana address';
  }
  return true;
};
```

### XSS Prevention

#### Escape User Content
```typescript
// Use React's built-in escaping
function AgentCard({ agent }: { agent: AgentProfile }) {
  return (
    <div>
      {/* React automatically escapes these */}
      <h3>{agent.name}</h3>
      <p>{agent.description}</p>
    </div>
  );
}

// For dangerouslySetInnerHTML, sanitize first
function RichTextDisplay({ content }: { content: string }) {
  const sanitized = DOMPurify.sanitize(content);
  
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}
```

### CSRF Protection

#### Use CSRF Tokens for State-Changing Operations
```typescript
// API route with CSRF protection
import { getCsrfToken } from '@/lib/csrf';

export async function POST(request: NextRequest) {
  const token = request.headers.get('X-CSRF-Token');
  const expectedToken = await getCsrfToken(request);
  
  if (token !== expectedToken) {
    return NextResponse.json(
      { error: 'Invalid CSRF token' },
      { status: 403 }
    );
  }
  
  // Process request
}
```

### Rate Limiting

#### Implement Rate Limiting on API Routes
```typescript
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, '10 s'), // 10 requests per 10 seconds
});

export async function POST(request: NextRequest) {
  const ip = request.ip ?? '127.0.0.1';
  const { success } = await ratelimit.limit(ip);
  
  if (!success) {
    return NextResponse.json(
      { error: 'Too many requests' },
      { status: 429 }
    );
  }
  
  // Process request
}
```

## API Security

### Authentication

#### API Key Authentication
```typescript
// Validate API key for AI service requests
export async function POST(request: NextRequest) {
  const apiKey = request.headers.get('X-API-Key');
  
  if (!apiKey || apiKey !== process.env.AI_SERVICE_API_KEY) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }
  
  // Process request
}
```

#### Wallet Signature Verification
```typescript
import { PublicKey } from '@solana/web3.js';
import nacl from 'tweetnacl';
import bs58 from 'bs58';

function verifySignature(
  message: string,
  signature: string,
  publicKey: string
): boolean {
  try {
    const messageBytes = new TextEncoder().encode(message);
    const signatureBytes = bs58.decode(signature);
    const publicKeyBytes = new PublicKey(publicKey).toBytes();
    
    return nacl.sign.detached.verify(
      messageBytes,
      signatureBytes,
      publicKeyBytes
    );
  } catch {
    return false;
  }
}

// Use in API routes
export async function POST(request: NextRequest) {
  const { message, signature, publicKey } = await request.json();
  
  if (!verifySignature(message, signature, publicKey)) {
    return NextResponse.json(
      { error: 'Invalid signature' },
      { status: 401 }
    );
  }
  
  // Process authenticated request
}
```

### Input Validation

#### Validate Request Body
```typescript
import { z } from 'zod';

const AgentRegistrationSchema = z.object({
  name: z.string().min(1).max(50),
  description: z.string().min(1).max(500),
  capabilities: z.array(z.string()),
  pricing: z.object({
    model: z.enum(['per-query', 'subscription', 'custom']),
    amount: z.number().positive().max(1000),
  }),
  endpointUrl: z.string().url().max(200),
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Validate with Zod
    const validated = AgentRegistrationSchema.parse(body);
    
    // Process validated data
    const agent = await createAgent(validated);
    
    return NextResponse.json({ agent });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Validation failed', details: error.errors },
        { status: 400 }
      );
    }
    
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

### SQL Injection Prevention

#### Use Parameterized Queries
```typescript
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

// GOOD: Parameterized query
async function getAgent(agentId: string) {
  const result = await pool.query(
    'SELECT * FROM agents WHERE agent_id = $1',
    [agentId]
  );
  return result.rows[0];
}

// BAD: String concatenation (vulnerable to SQL injection)
async function getAgentBad(agentId: string) {
  const result = await pool.query(
    `SELECT * FROM agents WHERE agent_id = '${agentId}'` // ❌ NEVER DO THIS
  );
  return result.rows[0];
}
```

## Environment Variables Security

### Never Commit Secrets
```bash
# .env.local (NEVER commit this file)
DATABASE_URL=postgresql://user:password@localhost:5432/agentmarket
ANTHROPIC_API_KEY=sk-ant-...
AWS_SECRET_ACCESS_KEY=...

# .env.example (commit this as template)
DATABASE_URL=postgresql://user:password@localhost:5432/agentmarket
ANTHROPIC_API_KEY=your_api_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
```

### Use AWS Secrets Manager for Production
```typescript
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

async function getSecret(secretName: string): Promise<string> {
  const client = new SecretsManagerClient({ region: 'us-east-1' });
  
  const response = await client.send(
    new GetSecretValueCommand({ SecretId: secretName })
  );
  
  return response.SecretString!;
}

// Use in production
const apiKey = process.env.NODE_ENV === 'production'
  ? await getSecret('anthropic-api-key')
  : process.env.ANTHROPIC_API_KEY;
```

## Database Security

### Connection Security
```typescript
// Use SSL for database connections in production
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' 
    ? { rejectUnauthorized: true }
    : false,
});
```

### Principle of Least Privilege
```sql
-- Create read-only user for analytics
CREATE USER analytics_user WITH PASSWORD 'secure_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_user;

-- Create app user with limited permissions
CREATE USER app_user WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE ON agents, requests, ratings TO app_user;
-- No DELETE or DROP permissions
```

### Encrypt Sensitive Data
```typescript
import crypto from 'crypto';

const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY!; // 32 bytes
const IV_LENGTH = 16;

function encrypt(text: string): string {
  const iv = crypto.randomBytes(IV_LENGTH);
  const cipher = crypto.createCipheriv(
    'aes-256-cbc',
    Buffer.from(ENCRYPTION_KEY, 'hex'),
    iv
  );
  
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  
  return iv.toString('hex') + ':' + encrypted;
}

function decrypt(text: string): string {
  const parts = text.split(':');
  const iv = Buffer.from(parts[0], 'hex');
  const encrypted = parts[1];
  
  const decipher = crypto.createDecipheriv(
    'aes-256-cbc',
    Buffer.from(ENCRYPTION_KEY, 'hex'),
    iv
  );
  
  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  
  return decrypted;
}

// Use for sensitive data
const encryptedApiKey = encrypt(userApiKey);
await db.query('INSERT INTO user_keys (user_id, api_key) VALUES ($1, $2)', [
  userId,
  encryptedApiKey
]);
```

## AI Service Security

### Validate Transaction Data
```python
from solana.transaction import Transaction
import base64

def validate_transaction(tx_data: str) -> bool:
    """Validate transaction data before analysis."""
    try:
        # Decode base64
        decoded = base64.b64decode(tx_data)
        
        # Verify it's a valid transaction
        Transaction.deserialize(decoded)
        
        return True
    except Exception as e:
        logger.error(f"Invalid transaction data: {e}")
        return False

@app.post("/scan")
async def scan_transaction(request: ScanRequest):
    # Validate before processing
    if not validate_transaction(request.transaction):
        raise HTTPException(status_code=400, detail="Invalid transaction data")
    
    # Process scan
    result = await analyze_transaction(request.transaction)
    return result
```

### Rate Limit AI API Calls
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/scan")
@limiter.limit("10/minute")  # 10 scans per minute per IP
async def scan_transaction(request: ScanRequest):
    # Process scan
    pass
```

### Sanitize AI Responses
```python
import re

def sanitize_ai_response(response: str) -> str:
    """Remove potentially harmful content from AI responses."""
    # Remove any script tags
    response = re.sub(r'<script[^>]*>.*?</script>', '', response, flags=re.DOTALL)
    
    # Remove any HTML tags
    response = re.sub(r'<[^>]+>', '', response)
    
    # Limit length
    if len(response) > 5000:
        response = response[:5000] + '...'
    
    return response

async def generate_explanation(risk_data: dict) -> str:
    # Get AI response
    raw_response = await claude_api.generate(risk_data)
    
    # Sanitize before returning
    return sanitize_ai_response(raw_response)
```

## Monitoring & Incident Response

### Security Logging
```typescript
import winston from 'winston';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'security.log' }),
  ],
});

// Log security events
function logSecurityEvent(event: string, details: any) {
  logger.info('Security Event', {
    event,
    details,
    timestamp: new Date().toISOString(),
    ip: details.ip,
    userAgent: details.userAgent,
  });
}

// Use in code
export async function POST(request: NextRequest) {
  const apiKey = request.headers.get('X-API-Key');
  
  if (!apiKey || apiKey !== process.env.AI_SERVICE_API_KEY) {
    logSecurityEvent('unauthorized_api_access', {
      ip: request.ip,
      userAgent: request.headers.get('user-agent'),
      path: request.url,
    });
    
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  
  // Process request
}
```

### Error Handling (Don't Leak Information)
```typescript
// GOOD: Generic error message
export async function POST(request: NextRequest) {
  try {
    // Process request
  } catch (error) {
    console.error('Internal error:', error); // Log detailed error
    
    return NextResponse.json(
      { error: 'Internal server error' }, // Generic message to user
      { status: 500 }
    );
  }
}

// BAD: Leaks implementation details
export async function POST(request: NextRequest) {
  try {
    // Process request
  } catch (error) {
    return NextResponse.json(
      { error: error.message }, // ❌ Exposes internal details
      { status: 500 }
    );
  }
}
```

### Security Headers
```typescript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains',
          },
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
          },
        ],
      },
    ];
  },
};
```

## Security Checklist

Before deploying to production:

### Smart Contracts
- [ ] All inputs validated
- [ ] Access controls implemented
- [ ] PDAs properly derived and verified
- [ ] Integer overflow protection
- [ ] Reentrancy prevention
- [ ] State transitions validated
- [ ] Contracts audited

### Frontend
- [ ] No private keys exposed
- [ ] User inputs sanitized
- [ ] XSS prevention implemented
- [ ] CSRF protection enabled
- [ ] Wallet signatures verified
- [ ] Rate limiting on forms

### API
- [ ] Authentication required
- [ ] Input validation with Zod
- [ ] Rate limiting enabled
- [ ] SQL injection prevention
- [ ] Error messages don't leak info
- [ ] Security headers configured

### Infrastructure
- [ ] Environment variables secured
- [ ] Database connections encrypted
- [ ] Secrets in AWS Secrets Manager
- [ ] HTTPS enforced
- [ ] Security logging enabled
- [ ] Monitoring alerts configured

### AI Service
- [ ] Transaction data validated
- [ ] Rate limiting enabled
- [ ] AI responses sanitized
- [ ] API keys secured
- [ ] Error handling implemented
