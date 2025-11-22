# AgentMarket - Testing Strategy

## Testing Philosophy

- Write tests that focus on core functionality
- Test user-facing features, not implementation details
- Prioritize integration tests over unit tests
- Keep tests simple and maintainable
- Test edge cases and error conditions
- Aim for confidence, not 100% coverage

## Testing Pyramid

```
        /\
       /  \
      / E2E \
     /--------\
    /Integration\
   /--------------\
  /   Unit Tests   \
 /------------------\
```

### Unit Tests (30%)
- Individual functions and utilities
- Pure logic without dependencies
- Fast execution (<1ms per test)

### Integration Tests (50%)
- API endpoints
- Smart contract instructions
- Database operations
- Component interactions

### End-to-End Tests (20%)
- Complete user flows
- Critical paths only
- Wallet connection → Transaction → Result

## Smart Contract Testing

### Anchor Test Framework

```typescript
// tests/agent-registry.ts
import * as anchor from '@coral-xyz/anchor';
import { Program } from '@coral-xyz/anchor';
import { AgentRegistry } from '../target/types/agent_registry';
import { expect } from 'chai';

describe('agent-registry', () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);
  
  const program = anchor.workspace.AgentRegistry as Program<AgentRegistry>;
  
  it('registers a new agent', async () => {
    const agent = anchor.web3.Keypair.generate();
    const creator = provider.wallet.publicKey;
    
    await program.methods
      .registerAgent(
        'Test Agent',
        'A test agent for security scanning',
        [1, 2], // capabilities
        { perQuery: { price: new anchor.BN(10000000) } },
        'https://api.example.com/agent',
        'QmHash123'
      )
      .accounts({
        agent: agent.publicKey,
        creator,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .signers([agent])
      .rpc();
    
    const agentAccount = await program.account.agentProfile.fetch(agent.publicKey);
    
    expect(agentAccount.name).to.equal('Test Agent');
    expect(agentAccount.creator.toString()).to.equal(creator.toString());
    expect(agentAccount.isActive).to.be.true;
  });
  
  it('prevents unauthorized agent updates', async () => {
    const agent = anchor.web3.Keypair.generate();
    const creator = provider.wallet.publicKey;
    const unauthorized = anchor.web3.Keypair.generate();
    
    // Register agent
    await program.methods
      .registerAgent('Test', 'Description', [1], { perQuery: { price: new anchor.BN(1000) } }, 'url', 'hash')
      .accounts({ agent: agent.publicKey, creator, systemProgram: anchor.web3.SystemProgram.programId })
      .signers([agent])
      .rpc();
    
    // Try to update with unauthorized signer
    try {
      await program.methods
        .updateAgent('New Description')
        .accounts({ agent: agent.publicKey, signer: unauthorized.publicKey })
        .signers([unauthorized])
        .rpc();
      
      expect.fail('Should have thrown error');
    } catch (error) {
      expect(error.message).to.include('Unauthorized');
    }
  });
});
```

### Test Coverage Goals
- All instructions tested
- Access control verified
- Input validation checked
- Error cases handled
- State transitions validated

## Frontend Testing

### Component Testing (React Testing Library)

```typescript
// __tests__/components/agent-card.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentCard } from '@/components/agents/agent-card';

describe('AgentCard', () => {
  const mockAgent = {
    id: 'agent123',
    name: 'SecurityGuard AI',
    description: 'Transaction security scanner',
    capabilities: ['security', 'analysis'],
    price: 0.01,
    rating: 4.8,
    totalServices: 1250,
  };
  
  it('renders agent information', () => {
    render(<AgentCard agent={mockAgent} onHire={jest.fn()} />);
    
    expect(screen.getByText('SecurityGuard AI')).toBeInTheDocument();
    expect(screen.getByText('Transaction security scanner')).toBeInTheDocument();
    expect(screen.getByText('0.01 SOL')).toBeInTheDocument();
  });
  
  it('calls onHire when hire button clicked', () => {
    const onHire = jest.fn();
    render(<AgentCard agent={mockAgent} onHire={onHire} />);
    
    const hireButton = screen.getByRole('button', { name: /hire/i });
    fireEvent.click(hireButton);
    
    expect(onHire).toHaveBeenCalledWith('agent123');
  });
});
```

### Hook Testing

```typescript
// __tests__/hooks/use-agents.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useAgents } from '@/hooks/use-agents';

describe('useAgents', () => {
  it('fetches agents successfully', async () => {
    const { result } = renderHook(() => useAgents());
    
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    
    expect(result.current.agents).toHaveLength(10);
    expect(result.current.error).toBeNull();
  });
  
  it('handles fetch errors', async () => {
    // Mock fetch to fail
    global.fetch = jest.fn(() => Promise.reject('API error'));
    
    const { result } = renderHook(() => useAgents());
    
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    
    expect(result.current.agents).toEqual([]);
    expect(result.current.error).toBeTruthy();
  });
});
```

## API Testing

### API Route Testing

```typescript
// __tests__/api/agents.test.ts
import { POST } from '@/app/api/agents/register/route';
import { NextRequest } from 'next/server';

describe('/api/agents/register', () => {
  it('registers agent with valid data', async () => {
    const request = new NextRequest('http://localhost:3000/api/agents/register', {
      method: 'POST',
      body: JSON.stringify({
        name: 'Test Agent',
        description: 'Test description',
        capabilities: ['security'],
        pricing: { model: 'per-query', amount: 0.01 },
        endpointUrl: 'https://api.example.com',
      }),
    });
    
    const response = await POST(request);
    const data = await response.json();
    
    expect(response.status).toBe(201);
    expect(data.agent).toBeDefined();
    expect(data.agent.name).toBe('Test Agent');
  });
  
  it('rejects invalid data', async () => {
    const request = new NextRequest('http://localhost:3000/api/agents/register', {
      method: 'POST',
      body: JSON.stringify({
        name: '', // Invalid: empty name
        description: 'Test',
      }),
    });
    
    const response = await POST(request);
    
    expect(response.status).toBe(400);
  });
});
```

## AI Service Testing

### Transaction Analysis Testing

```python
# tests/test_security_scanner.py
import pytest
from security_ai.scanner import SecurityScanner

@pytest.fixture
def scanner():
    return SecurityScanner()

def test_safe_transaction(scanner):
    """Test that safe transactions are correctly identified."""
    safe_tx = load_test_transaction('safe_transfer.json')
    
    result = scanner.scan(safe_tx)
    
    assert result.risk_level == 'SAFE'
    assert result.risk_score < 30
    assert 'safe' in result.explanation.lower()

def test_malicious_transaction(scanner):
    """Test that malicious transactions are detected."""
    malicious_tx = load_test_transaction('wallet_drainer.json')
    
    result = scanner.scan(malicious_tx)
    
    assert result.risk_level == 'DANGER'
    assert result.risk_score > 70
    assert 'drain' in result.explanation.lower()

def test_scan_performance(scanner):
    """Test that scans complete within 2 seconds."""
    import time
    
    tx = load_test_transaction('safe_transfer.json')
    
    start = time.time()
    result = scanner.scan(tx)
    duration = time.time() - start
    
    assert duration < 2.0
    assert result is not None
```

## Integration Testing

### Complete User Flow Testing

```typescript
// __tests__/integration/agent-registration-flow.test.ts
import { Connection, Keypair } from '@solana/web3.js';
import { Program, AnchorProvider } from '@coral-xyz/anchor';

describe('Agent Registration Flow', () => {
  let connection: Connection;
  let program: Program;
  let creator: Keypair;
  
  beforeAll(async () => {
    connection = new Connection('http://localhost:8899', 'confirmed');
    // Setup program and provider
  });
  
  it('completes full registration flow', async () => {
    // 1. Create agent metadata
    const agentData = {
      name: 'Test Agent',
      description: 'Integration test agent',
      capabilities: ['security'],
      pricing: { perQuery: { price: 10000000 } },
      endpointUrl: 'https://api.test.com',
      ipfsHash: 'QmTest123',
    };
    
    // 2. Register on-chain
    const agent = Keypair.generate();
    const tx = await program.methods
      .registerAgent(
        agentData.name,
        agentData.description,
        [1],
        agentData.pricing,
        agentData.endpointUrl,
        agentData.ipfsHash
      )
      .accounts({
        agent: agent.publicKey,
        creator: creator.publicKey,
        systemProgram: SystemProgram.programId,
      })
      .signers([agent])
      .rpc();
    
    // 3. Verify on-chain data
    const agentAccount = await program.account.agentProfile.fetch(agent.publicKey);
    expect(agentAccount.name).toBe(agentData.name);
    
    // 4. Verify API can fetch agent
    const response = await fetch(`http://localhost:3000/api/agents/${agent.publicKey}`);
    const apiData = await response.json();
    expect(apiData.agent.name).toBe(agentData.name);
    
    // 5. Verify agent appears in marketplace
    const searchResponse = await fetch('http://localhost:3000/api/agents/search?query=Test');
    const searchData = await searchResponse.json();
    expect(searchData.agents.some(a => a.id === agent.publicKey.toString())).toBe(true);
  });
});
```

## Performance Testing

### Load Testing

```typescript
// __tests__/performance/api-load.test.ts
import autocannon from 'autocannon';

describe('API Performance', () => {
  it('handles 100 concurrent requests', async () => {
    const result = await autocannon({
      url: 'http://localhost:3000/api/agents',
      connections: 100,
      duration: 10,
    });
    
    expect(result.errors).toBe(0);
    expect(result.timeouts).toBe(0);
    expect(result.latency.p95).toBeLessThan(500); // 95th percentile < 500ms
  });
});
```

## Test Data Management

### Test Fixtures

```typescript
// __tests__/fixtures/agents.ts
export const mockAgents = [
  {
    id: 'agent1',
    name: 'SecurityGuard AI',
    description: 'Transaction security scanner',
    capabilities: ['security'],
    price: 0.01,
    rating: 4.8,
    totalServices: 1250,
  },
  {
    id: 'agent2',
    name: 'CodeCraft AI',
    description: 'Smart contract generator',
    capabilities: ['code-generation'],
    price: 0.05,
    rating: 4.6,
    totalServices: 850,
  },
];

export const mockTransactions = {
  safe: {
    serialized: 'base64_encoded_safe_transaction',
    instructions: [/* ... */],
  },
  malicious: {
    serialized: 'base64_encoded_malicious_transaction',
    instructions: [/* ... */],
  },
};
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run linter
        run: npm run lint
      
      - name: Run type check
        run: npm run type-check
      
      - name: Run unit tests
        run: npm run test:unit
      
      - name: Run integration tests
        run: npm run test:integration
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Testing Checklist

Before merging code:

### Smart Contracts
- [ ] All instructions tested
- [ ] Access control verified
- [ ] Error cases covered
- [ ] Integration tests pass

### Frontend
- [ ] Components render correctly
- [ ] User interactions work
- [ ] Error states handled
- [ ] Loading states shown

### API
- [ ] Endpoints return correct data
- [ ] Validation works
- [ ] Error handling tested
- [ ] Rate limiting verified

### AI Service
- [ ] Scan accuracy validated
- [ ] Performance targets met (<2s)
- [ ] Error handling tested
- [ ] Edge cases covered

### Integration
- [ ] Complete user flows work
- [ ] Data flows correctly between layers
- [ ] No race conditions
- [ ] Performance acceptable
