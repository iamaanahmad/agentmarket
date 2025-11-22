# AgentMarket - Coding Standards

## General Principles

### Code Quality
- Write clean, readable, maintainable code
- Follow DRY (Don't Repeat Yourself) principle
- Keep functions small and focused (single responsibility)
- Use meaningful variable and function names
- Comment complex logic, not obvious code
- Prefer composition over inheritance

### Performance
- Optimize for user experience first
- Avoid premature optimization
- Profile before optimizing
- Cache expensive operations
- Minimize network requests
- Use lazy loading where appropriate

### Security
- Never expose private keys or secrets
- Validate all user inputs
- Sanitize data before rendering
- Use parameterized queries for database
- Implement proper error handling
- Follow principle of least privilege

## TypeScript Standards

### General TypeScript
- Use TypeScript strict mode
- Avoid `any` type - use `unknown` if type is truly unknown
- Define interfaces for all data structures
- Use type inference where obvious
- Prefer `const` over `let`, never use `var`
- Use optional chaining (`?.`) and nullish coalescing (`??`)

### Naming Conventions
```typescript
// Interfaces and Types - PascalCase
interface AgentProfile { }
type PricingModel = 'per-query' | 'subscription';

// Variables and functions - camelCase
const agentId = 'abc123';
function calculateRiskScore() { }

// Constants - UPPER_SNAKE_CASE
const MAX_AGENTS_PER_PAGE = 20;
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

// Components - PascalCase
function AgentCard() { }
export default function MarketplacePage() { }

// Private functions/variables - prefix with underscore
function _internalHelper() { }
```

### File Organization
```typescript
// 1. Imports (grouped)
import React from 'react';
import { useState, useEffect } from 'react';

import { Button } from '@/components/ui/button';
import { AgentCard } from '@/components/agents/agent-card';

import { useWallet } from '@solana/wallet-adapter-react';
import { Connection } from '@solana/web3.js';

import { cn } from '@/lib/utils';

// 2. Types and Interfaces
interface AgentCardProps {
  agent: AgentProfile;
  onHire: (agentId: string) => void;
}

// 3. Constants
const DEFAULT_RATING = 0;

// 4. Component/Function
export function AgentCard({ agent, onHire }: AgentCardProps) {
  // Component logic
}

// 5. Exports
export default AgentCard;
```

### Error Handling
```typescript
// Use try-catch for async operations
async function fetchAgent(id: string): Promise<AgentProfile | null> {
  try {
    const response = await fetch(`/api/agents/${id}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch agent: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching agent:', error);
    return null;
  }
}

// Use Result type for operations that can fail
type Result<T, E = Error> = 
  | { success: true; data: T }
  | { success: false; error: E };

async function registerAgent(data: AgentData): Promise<Result<string>> {
  try {
    const agentId = await createAgent(data);
    return { success: true, data: agentId };
  } catch (error) {
    return { success: false, error: error as Error };
  }
}
```

## React/Next.js Standards

### Component Structure
```typescript
'use client'; // Only if client component

import { useState } from 'react';

interface ComponentProps {
  // Props interface
}

export function Component({ prop1, prop2 }: ComponentProps) {
  // 1. Hooks (in order: state, context, custom hooks)
  const [state, setState] = useState();
  const { wallet } = useWallet();
  const { data } = useAgents();

  // 2. Derived state
  const isLoading = !data;

  // 3. Effects
  useEffect(() => {
    // Effect logic
  }, [dependencies]);

  // 4. Event handlers
  const handleClick = () => {
    // Handler logic
  };

  // 5. Render helpers
  const renderContent = () => {
    // Render logic
  };

  // 6. Return JSX
  return (
    <div>
      {/* JSX */}
    </div>
  );
}
```

### Server vs Client Components
```typescript
// Server Component (default in Next.js 14)
// - No useState, useEffect, or browser APIs
// - Can directly fetch data
// - Better performance
export default async function AgentPage({ params }: { params: { id: string } }) {
  const agent = await fetchAgent(params.id);
  return <AgentProfile agent={agent} />;
}

// Client Component
// - Use 'use client' directive
// - Can use hooks and browser APIs
// - Interactive elements
'use client';
export function WalletButton() {
  const { connect } = useWallet();
  return <button onClick={connect}>Connect</button>;
}
```

### API Routes
```typescript
// app/api/agents/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get('query');
    
    // Business logic
    const agents = await searchAgents(query);
    
    return NextResponse.json({ agents }, { status: 200 });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Validate input
    if (!body.name || !body.description) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }
    
    // Business logic
    const agent = await createAgent(body);
    
    return NextResponse.json({ agent }, { status: 201 });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

## Solana/Anchor Standards

### Rust Naming Conventions
```rust
// Structs - PascalCase
pub struct AgentProfile { }

// Functions - snake_case
pub fn register_agent() { }

// Constants - UPPER_SNAKE_CASE
pub const MAX_NAME_LENGTH: usize = 50;

// Enums - PascalCase for enum, PascalCase for variants
pub enum RequestStatus {
    Pending,
    InProgress,
    Completed,
}
```

### Smart Contract Structure
```rust
use anchor_lang::prelude::*;

declare_id!("YourProgramIDHere");

#[program]
pub mod agent_registry {
    use super::*;

    // Instructions
    pub fn register_agent(
        ctx: Context<RegisterAgent>,
        name: String,
        description: String,
    ) -> Result<()> {
        // Validate inputs
        require!(name.len() <= MAX_NAME_LENGTH, ErrorCode::NameTooLong);
        
        // Business logic
        let agent = &mut ctx.accounts.agent;
        agent.name = name;
        agent.description = description;
        agent.creator = ctx.accounts.creator.key();
        
        Ok(())
    }
}

// Account structures
#[account]
pub struct AgentProfile {
    pub agent_id: Pubkey,
    pub creator: Pubkey,
    pub name: String,
    // ... other fields
}

// Context structures
#[derive(Accounts)]
pub struct RegisterAgent<'info> {
    #[account(
        init,
        payer = creator,
        space = 8 + AgentProfile::INIT_SPACE
    )]
    pub agent: Account<'info, AgentProfile>,
    
    #[account(mut)]
    pub creator: Signer<'info>,
    
    pub system_program: Program<'info, System>,
}

// Error codes
#[error_code]
pub enum ErrorCode {
    #[msg("Agent name is too long")]
    NameTooLong,
    #[msg("Unauthorized access")]
    Unauthorized,
}

// Constants
const MAX_NAME_LENGTH: usize = 50;
```

### Security Best Practices
```rust
// Always validate inputs
require!(name.len() <= MAX_NAME_LENGTH, ErrorCode::NameTooLong);
require!(price > 0, ErrorCode::InvalidPrice);

// Check authorization
require!(
    ctx.accounts.creator.key() == agent.creator,
    ErrorCode::Unauthorized
);

// Use PDAs for escrow accounts
let (escrow_pda, bump) = Pubkey::find_program_address(
    &[b"escrow", request_id.as_ref()],
    ctx.program_id
);

// Prevent reentrancy with proper account constraints
#[account(
    mut,
    constraint = escrow.status == RequestStatus::Pending @ ErrorCode::InvalidStatus
)]
pub escrow: Account<'info, ServiceRequest>,
```

## Python Standards (AI Service)

### General Python
```python
# Use type hints
def calculate_risk_score(transaction: dict) -> int:
    """Calculate risk score for a transaction.
    
    Args:
        transaction: Transaction data dictionary
        
    Returns:
        Risk score from 0-100
    """
    # Function logic
    return score

# Use dataclasses for structured data
from dataclasses import dataclass

@dataclass
class ScanResult:
    risk_level: str
    risk_score: int
    explanation: str
    details: dict

# Use async/await for I/O operations
async def scan_transaction(tx_data: str) -> ScanResult:
    async with httpx.AsyncClient() as client:
        response = await client.post(API_URL, json={"data": tx_data})
        return ScanResult(**response.json())
```

### FastAPI Structure
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Request/Response models
class ScanRequest(BaseModel):
    transaction: str
    user_wallet: str

class ScanResponse(BaseModel):
    risk_level: str
    risk_score: int
    explanation: str

# Endpoints
@app.post("/scan", response_model=ScanResponse)
async def scan_transaction(request: ScanRequest):
    try:
        # Validate input
        if not request.transaction:
            raise HTTPException(status_code=400, detail="Transaction data required")
        
        # Business logic
        result = await analyze_transaction(request.transaction)
        
        return ScanResponse(**result)
    except Exception as e:
        logger.error(f"Scan error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## CSS/Styling Standards

### TailwindCSS
```typescript
// Use cn() utility for conditional classes
import { cn } from '@/lib/utils';

<div className={cn(
  "base-classes",
  isActive && "active-classes",
  isDisabled && "disabled-classes"
)} />

// Group related utilities
<div className="
  flex items-center justify-between
  px-4 py-2
  bg-white dark:bg-gray-900
  border border-gray-200 dark:border-gray-800
  rounded-lg shadow-sm
" />

// Use design tokens consistently
// Colors: primary, secondary, accent, muted, destructive
// Spacing: 0, 1, 2, 4, 6, 8, 12, 16, 24, 32
// Border radius: sm, md, lg, xl
```

### Component Styling
```typescript
// Use shadcn/ui components as base
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

// Extend with custom variants
<Button variant="default" size="lg">
  Connect Wallet
</Button>

// Use consistent spacing
<div className="space-y-4">
  <Card />
  <Card />
</div>
```

## Testing Standards

### Unit Tests
```typescript
// Use descriptive test names
describe('calculateRiskScore', () => {
  it('should return 0 for safe transactions', () => {
    const result = calculateRiskScore(safeTx);
    expect(result).toBe(0);
  });

  it('should return 100 for known malicious programs', () => {
    const result = calculateRiskScore(maliciousTx);
    expect(result).toBe(100);
  });
});

// Test edge cases
it('should handle empty transaction data', () => {
  expect(() => calculateRiskScore(null)).toThrow();
});
```

### Integration Tests
```typescript
// Test complete user flows
describe('Agent Registration Flow', () => {
  it('should register agent and mint NFT', async () => {
    // Setup
    const wallet = await createTestWallet();
    
    // Execute
    const result = await registerAgent({
      name: 'Test Agent',
      description: 'Test description',
      wallet
    });
    
    // Assert
    expect(result.success).toBe(true);
    expect(result.nftMint).toBeDefined();
  });
});
```

## Git Standards

### Commit Messages
```
feat: add agent registration form
fix: resolve wallet connection issue
docs: update API documentation
style: format code with prettier
refactor: simplify risk calculation logic
test: add tests for escrow contract
chore: update dependencies
```

### Branch Naming
```
feature/agent-registration
fix/wallet-connection-bug
refactor/risk-scoring
docs/api-documentation
```

### Pull Request Guidelines
- Clear title describing the change
- Description of what changed and why
- Link to related issues/tasks
- Screenshots for UI changes
- Test results
- Request review from team members

## Documentation Standards

### Code Comments
```typescript
// Good: Explain WHY, not WHAT
// Calculate risk score using weighted average of all signals
// Blacklist hits are weighted highest (100) to ensure dangerous transactions are caught
const riskScore = calculateWeightedScore(signals);

// Bad: Obvious comment
// Set risk score to result
const riskScore = result;
```

### Function Documentation
```typescript
/**
 * Scans a Solana transaction for security risks.
 * 
 * @param transaction - Base64 encoded transaction data
 * @param userWallet - User's wallet public key
 * @returns Promise resolving to scan result with risk level and explanation
 * @throws {ValidationError} If transaction data is invalid
 * @throws {APIError} If external API calls fail
 * 
 * @example
 * const result = await scanTransaction(txData, walletKey);
 * if (result.risk_level === 'DANGER') {
 *   alert('Do not sign this transaction!');
 * }
 */
async function scanTransaction(
  transaction: string,
  userWallet: string
): Promise<ScanResult> {
  // Implementation
}
```

### README Documentation
- Clear project description
- Setup instructions
- Usage examples
- API documentation
- Contributing guidelines
- License information

## Performance Guidelines

### Frontend Performance
- Use React.memo() for expensive components
- Implement virtual scrolling for long lists
- Lazy load images and components
- Minimize bundle size (code splitting)
- Use Web Workers for heavy computations

### Backend Performance
- Cache frequently accessed data (Redis)
- Use database indexes
- Implement pagination for large datasets
- Use connection pooling
- Monitor and optimize slow queries

### Smart Contract Performance
- Minimize account allocations
- Use efficient data structures
- Batch operations where possible
- Optimize instruction data size

## Accessibility Standards

### ARIA Labels
```typescript
<button aria-label="Connect wallet">
  <WalletIcon />
</button>

<input
  type="text"
  aria-label="Search agents"
  aria-describedby="search-help"
/>
```

### Keyboard Navigation
- All interactive elements must be keyboard accessible
- Implement proper focus management
- Use semantic HTML elements
- Test with keyboard only

### Color Contrast
- Ensure WCAG AA compliance (4.5:1 for normal text)
- Don't rely on color alone to convey information
- Test with color blindness simulators

## Environment Variables

### Naming Convention
```bash
# Public variables (exposed to browser) - prefix with NEXT_PUBLIC_
NEXT_PUBLIC_SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
NEXT_PUBLIC_CLUSTER=mainnet-beta

# Private variables (server-side only)
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=sk-...
AWS_SECRET_ACCESS_KEY=...
```

### Usage
```typescript
// Access in code
const rpcUrl = process.env.NEXT_PUBLIC_SOLANA_RPC_URL;
const apiKey = process.env.ANTHROPIC_API_KEY; // Server-side only
```

## Code Review Checklist

Before submitting code for review:
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] No console.log() or debugging code
- [ ] Error handling implemented
- [ ] Input validation added
- [ ] Documentation updated
- [ ] No hardcoded values (use constants/env vars)
- [ ] Accessibility considered
- [ ] Performance optimized
- [ ] Security best practices followed
