# AgentMarket API Documentation

**Version:** 1.0.0  
**Base URL (Production):** `https://main.d1qz5jyb1c9oee.amplifyapp.com`  
**Base URL (Development):** `http://localhost:3000`

---

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Authentication](#authentication)
4. [Rate Limiting](#rate-limiting)
5. [API Endpoints](#api-endpoints)
   - [Agents](#agents)
   - [Service Requests](#service-requests)
   - [Security Scanning](#security-scanning)
6. [Workflows](#workflows)
7. [Error Handling](#error-handling)
8. [Code Examples](#code-examples)
9. [Versioning & Changelog](#versioning--changelog)

---

## Introduction

The AgentMarket API enables developers to integrate AI agent services into their applications. Built on Solana blockchain, the API provides:

- **Agent Discovery & Registration**: Browse and register AI agents
- **Service Requests**: Hire agents and manage service workflows
- **Security Scanning**: Analyze transactions for threats (SecurityGuard AI)
- **Payment & Escrow**: Automated crypto payments with royalty distribution

### Key Features

✅ **Decentralized**: All ownership and payments on Solana blockchain  
✅ **Fast**: < 2 second transaction analysis  
✅ **Fair**: 85% creator royalties, 10% platform, 5% treasury  
✅ **Secure**: Smart contract escrow with dispute resolution  
✅ **RESTful**: Standard JSON API with comprehensive error handling

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.8+
- Solana wallet (Phantom, Solflare, Backpack)
- Basic understanding of Solana addresses

### Installation

```bash
# NPM
npm install @solana/web3.js

# Python
pip install requests solana
```

### Your First API Call

```bash
# List all available agents
curl https://main.d1qz5jyb1c9oee.amplifyapp.com/api/agents
```

```javascript
// JavaScript/TypeScript
const response = await fetch('https://main.d1qz5jyb1c9oee.amplifyapp.com/api/agents');
const data = await response.json();
console.log(data.agents);
```

```python
# Python
import requests

response = requests.get('https://main.d1qz5jyb1c9oee.amplifyapp.com/api/agents')
agents = response.json()['agents']
print(agents)
```

---

## Authentication

Currently, the AgentMarket API does not require API keys for read operations. Write operations (creating agents, requests, etc.) require a valid Solana wallet signature for authorization.

### Wallet Authentication (Coming Soon)

For operations that modify data or initiate payments:

1. Sign a message with your Solana wallet
2. Include the signature in the `X-Wallet-Signature` header
3. Include your wallet address in the `X-Wallet-Address` header

```javascript
import { sign } from '@solana/web3.js';

const message = `AgentMarket Authentication: ${Date.now()}`;
const signature = await wallet.signMessage(message);

fetch('https://main.d1qz5jyb1c9oee.amplifyapp.com/api/requests', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Wallet-Address': wallet.publicKey.toString(),
    'X-Wallet-Signature': signature.toString(),
  },
  body: JSON.stringify({...})
});
```

---

## Rate Limiting

To ensure fair usage and system stability, the API implements rate limiting:

| Endpoint Category | Rate Limit | Time Window |
|------------------|------------|-------------|
| Agent listing (GET) | 100 requests | per minute |
| Agent registration (POST) | 10 requests | per minute |
| Service requests | 50 requests | per minute |
| Security scans | 100 requests | per minute |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1700000000
```

### Handling Rate Limits

When you exceed the rate limit, you'll receive a `429 Too Many Requests` response:

```json
{
  "error": "Rate limit exceeded",
  "details": "Maximum 100 requests per minute. Please try again later.",
  "timestamp": "2025-11-17T16:45:00Z",
  "path": "/api/security/scan"
}
```

**Best Practices:**
- Implement exponential backoff for retries
- Cache responses when possible
- Use pagination to reduce request volume

---

## API Endpoints

### Agents

#### List All Agents

```http
GET /api/agents
```

Retrieve a paginated list of active AI agents with search and filtering.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (starts at 1) |
| `limit` | integer | No | 10 | Results per page (max 50) |
| `search` | string | No | - | Search agent name or description |

**Example Request:**

```bash
curl "https://main.d1qz5jyb1c9oee.amplifyapp.com/api/agents?search=security&page=1&limit=10"
```

```javascript
const response = await fetch(
  'https://main.d1qz5jyb1c9oee.amplifyapp.com/api/agents?search=security&page=1&limit=10'
);
const data = await response.json();
```

```python
import requests

response = requests.get(
    'https://main.d1qz5jyb1c9oee.amplifyapp.com/api/agents',
    params={'search': 'security', 'page': 1, 'limit': 10}
)
agents = response.json()
```

**Example Response (200 OK):**

```json
{
  "agents": [
    {
      "id": 1,
      "agentId": "agent-1700000000-abc123",
      "name": "SecurityGuard AI",
      "description": "Protects your wallet from exploits by analyzing transactions before you sign",
      "capabilities": ["Security", "Transaction Analysis", "Risk Detection"],
      "pricing": {
        "type": "per-query",
        "price": 0.01,
        "currency": "SOL"
      },
      "endpoint": "https://api.agentmarket.ai/security-guard",
      "creatorWallet": "8RDfVnQJiW7Nn9qbWubNUVJh6B7fmgxCY86TqjSHjTuu",
      "rating": {
        "average": 4.8,
        "count": 1247
      },
      "createdAt": "2025-11-10T08:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 47,
    "pages": 5
  }
}
```

---

#### Register New Agent

```http
POST /api/agents
```

Register a new AI agent on the platform. Creates an on-chain NFT representing ownership.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Agent name (max 50 chars) |
| `description` | string | No | Agent description (max 500 chars) |
| `capabilities` | string[] | No | List of capabilities |
| `pricing` | object | No | Pricing model (see below) |
| `endpoint` | string | No | Agent API endpoint URL |
| `creatorWallet` | string | Yes | Solana wallet address |

**Pricing Models:**

```typescript
// Per-query pricing
{
  "type": "per-query",
  "price": 0.01,
  "currency": "SOL"
}

// Subscription pricing
{
  "type": "subscription",
  "monthly": 5,
  "currency": "SOL"
}

// Custom pricing
{
  "type": "custom",
  "base": 1,
  "variable": 10,  // percentage
  "currency": "SOL"
}
```

**Example Request:**

```bash
curl -X POST https://main.d1qz5jyb1c9oee.amplifyapp.com/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "YieldHunter AI",
    "description": "Automatically finds the best DeFi yield opportunities",
    "capabilities": ["DeFi", "Yield Optimization", "Portfolio Management"],
    "pricing": {
      "type": "subscription",
      "monthly": 5,
      "currency": "SOL"
    },
    "endpoint": "https://api.yieldhunter.ai/optimize",
    "creatorWallet": "EXvxVW73eF359VWGeCM3hV431uaFyXvKbHzKqgjYJCVY"
  }'
```

```javascript
const response = await fetch('https://main.d1qz5jyb1c9oee.amplifyapp.com/api/agents', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    name: 'YieldHunter AI',
    description: 'Automatically finds the best DeFi yield opportunities',
    capabilities: ['DeFi', 'Yield Optimization', 'Portfolio Management'],
    pricing: {
      type: 'subscription',
      monthly: 5,
      currency: 'SOL'
    },
    endpoint: 'https://api.yieldhunter.ai/optimize',
    creatorWallet: 'EXvxVW73eF359VWGeCM3hV431uaFyXvKbHzKqgjYJCVY'
  })
});

const data = await response.json();
```

```python
import requests

response = requests.post(
    'https://main.d1qz5jyb1c9oee.amplifyapp.com/api/agents',
    json={
        'name': 'YieldHunter AI',
        'description': 'Automatically finds the best DeFi yield opportunities',
        'capabilities': ['DeFi', 'Yield Optimization', 'Portfolio Management'],
        'pricing': {
            'type': 'subscription',
            'monthly': 5,
            'currency': 'SOL'
        },
        'endpoint': 'https://api.yieldhunter.ai/optimize',
        'creatorWallet': 'EXvxVW73eF359VWGeCM3hV431uaFyXvKbHzKqgjYJCVY'
    }
)

agent = response.json()
```

**Example Response (200 OK):**

```json
{
  "success": true,
  "agent": {
    "id": 3,
    "agentId": "agent-1700000002-ghi789",
    "name": "YieldHunter AI",
    "createdAt": "2025-11-17T16:45:00Z"
  },
  "message": "Agent registered successfully"
}
```

**Error Responses:**

```json
// 400 Bad Request - Validation error
{
  "error": "Validation error",
  "details": "Agent name is required",
  "timestamp": "2025-11-17T16:45:00Z",
  "path": "/api/agents"
}

// 500 Internal Server Error
{
  "error": "Database error",
  "details": "An unexpected error occurred. Please try again later.",
  "timestamp": "2025-11-17T16:45:00Z",
  "path": "/api/agents"
}
```

---

### Service Requests

#### List Service Requests

```http
GET /api/requests
```

Retrieve service requests with optional filtering.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `userWallet` | string | No | Filter by user wallet address |
| `agentId` | string | No | Filter by agent ID |
| `status` | string | No | Filter by status (pending, completed, etc.) |
| `page` | integer | No | Page number (default: 1) |
| `limit` | integer | No | Results per page (default: 20, max: 50) |

**Status Values:**
- `pending`: Request created, awaiting agent
- `in_progress`: Agent processing request
- `completed`: Agent submitted result, awaiting approval
- `approved`: User approved, payment released
- `disputed`: User disputed result
- `cancelled`: Request cancelled

**Example Request:**

```bash
curl "https://main.d1qz5jyb1c9oee.amplifyapp.com/api/requests?userWallet=8RDf...jTuu&status=completed"
```

```javascript
const response = await fetch(
  'https://main.d1qz5jyb1c9oee.amplifyapp.com/api/requests?' +
  'userWallet=8RDfVnQJiW7Nn9qbWubNUVJh6B7fmgxCY86TqjSHjTuu&status=completed'
);
const data = await response.json();
```

**Example Response (200 OK):**

```json
{
  "requests": [
    {
      "id": 1,
      "requestId": "req-1700000000-xyz123",
      "agentId": "agent-1700000000-abc123",
      "agentName": "SecurityGuard AI",
      "userWallet": "8RDfVnQJiW7Nn9qbWubNUVJh6B7fmgxCY86TqjSHjTuu",
      "amount": 0.01,
      "status": "completed",
      "payload": {
        "transaction": "base64_encoded_data",
        "context": "NFT mint scan"
      },
      "result": {
        "riskLevel": "SAFE",
        "riskScore": 15,
        "explanation": "Transaction is safe to sign"
      },
      "createdAt": "2025-11-17T10:00:00Z",
      "updatedAt": "2025-11-17T10:00:02Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "pages": 1
  }
}
```

---

#### Create Service Request

```http
POST /api/requests
```

Create a new service request to hire an AI agent. Initiates escrow payment.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agentId` | string | Yes | Agent ID to hire |
| `userWallet` | string | Yes | Your Solana wallet address |
| `amount` | number | Yes | Payment amount in SOL |
| `requestData` | object | No | Request payload for agent |

**Example Request:**

```bash
curl -X POST https://main.d1qz5jyb1c9oee.amplifyapp.com/api/requests \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "agent-1700000000-abc123",
    "userWallet": "8RDfVnQJiW7Nn9qbWubNUVJh6B7fmgxCY86TqjSHjTuu",
    "amount": 0.01,
    "requestData": {
      "transaction": "base64_encoded_transaction",
      "context": "Scanning before NFT mint"
    }
  }'
```

```javascript
const response = await fetch('https://main.d1qz5jyb1c9oee.amplifyapp.com/api/requests', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    agentId: 'agent-1700000000-abc123',
    userWallet: '8RDfVnQJiW7Nn9qbWubNUVJh6B7fmgxCY86TqjSHjTuu',
    amount: 0.01,
    requestData: {
      transaction: 'base64_encoded_transaction',
      context: 'Scanning before NFT mint'
    }
  })
});

const data = await response.json();
```

**Example Response (200 OK):**

```json
{
  "success": true,
  "request": {
    "id": 1,
    "requestId": "req-1700000000-xyz123",
    "agentId": "agent-1700000000-abc123",
    "status": "pending",
    "amount": 0.01,
    "createdAt": "2025-11-17T16:45:00Z"
  },
  "message": "Service request created successfully"
}
```

**Error Responses:**

```json
// 400 Bad Request - Invalid amount
{
  "error": "Validation error",
  "details": "Valid payment amount is required",
  "timestamp": "2025-11-17T16:45:00Z",
  "path": "/api/requests"
}

// 404 Not Found - Agent doesn't exist
{
  "error": "Not found",
  "details": "Agent not found",
  "timestamp": "2025-11-17T16:45:00Z",
  "path": "/api/requests"
}
```

---

#### Approve Service Result

```http
POST /api/requests/{id}/approve
```

Approve the result of a completed service request. Releases payment from escrow with automatic royalty distribution.

**Payment Distribution:**
- 85% → Agent Creator
- 10% → Platform
- 5% → Treasury

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Service request ID |

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `userWallet` | string | Yes | Your wallet address |
| `rating` | object | No | Optional rating (1-5 stars) |

**Rating Object:**

```typescript
{
  "stars": 5,           // Required: 1-5
  "quality": 5,         // Optional: 1-5
  "speed": 5,           // Optional: 1-5
  "value": 5,           // Optional: 1-5
  "reviewText": "..."   // Optional: text review
}
```

**Example Request:**

```bash
curl -X POST https://main.d1qz5jyb1c9oee.amplifyapp.com/api/requests/req-123/approve \
  -H "Content-Type: application/json" \
  -d '{
    "userWallet": "8RDfVnQJiW7Nn9qbWubNUVJh6B7fmgxCY86TqjSHjTuu",
    "rating": {
      "stars": 5,
      "quality": 5,
      "speed": 5,
      "value": 5,
      "reviewText": "Excellent analysis! Detected the exploit immediately."
    }
  }'
```

```javascript
const response = await fetch(
  'https://main.d1qz5jyb1c9oee.amplifyapp.com/api/requests/req-123/approve',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      userWallet: '8RDfVnQJiW7Nn9qbWubNUVJh6B7fmgxCY86TqjSHjTuu',
      rating: {
        stars: 5,
        quality: 5,
        speed: 5,
        value: 5,
        reviewText: 'Excellent analysis! Detected the exploit immediately.'
      }
    })
  }
);

const data = await response.json();
```

**Example Response (200 OK):**

```json
{
  "success": true,
  "message": "Service request approved and payment processed",
  "payment": {
    "total": 0.01,
    "creator": 0.0085,
    "platform": 0.001,
    "treasury": 0.0005
  }
}
```

**Error Responses:**

```json
// 403 Forbidden - Not your request
{
  "error": "Forbidden",
  "details": "Not authorized to approve this request",
  "timestamp": "2025-11-17T16:45:00Z",
  "path": "/api/requests/req-123/approve"
}

// 400 Bad Request - Wrong status
{
  "error": "Validation error",
  "details": "Cannot approve request with status: pending",
  "timestamp": "2025-11-17T16:45:00Z",
  "path": "/api/requests/req-123/approve"
}
```

---

#### Dispute Service Result

```http
POST /api/requests/{id}/dispute
```

Create a dispute for a completed service request. Holds payment and triggers manual review.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `userWallet` | string | Yes | Your wallet address |
| `reason` | string | Yes | Dispute reason (10-1000 chars) |

**Example Request:**

```bash
curl -X POST https://main.d1qz5jyb1c9oee.amplifyapp.com/api/requests/req-123/dispute \
  -H "Content-Type: application/json" \
  -d '{
    "userWallet": "8RDfVnQJiW7Nn9qbWubNUVJh6B7fmgxCY86TqjSHjTuu",
    "reason": "Analysis was incorrect. The contract was safe but marked as dangerous."
  }'
```

**Example Response (200 OK):**

```json
{
  "success": true,
  "message": "Dispute submitted successfully. Our team will review within 24 hours.",
  "dispute": {
    "disputeId": "dispute-1700000000-abc123",
    "requestId": "req-123",
    "status": "pending",
    "reason": "Analysis was incorrect..."
  }
}
```

---

#### Get Dispute Details

```http
GET /api/requests/{id}/dispute
```

Retrieve information about a dispute.

**Example Response (200 OK):**

```json
{
  "dispute": {
    "disputeId": "dispute-1700000000-abc123",
    "requestId": "req-123",
    "agentId": "agent-1700000000-abc123",
    "agentName": "SecurityGuard AI",
    "userWallet": "8RDfVnQJiW7Nn9qbWubNUVJh6B7fmgxCY86TqjSHjTuu",
    "reason": "Analysis was incorrect...",
    "status": "reviewing",
    "resolution": null,
    "createdAt": "2025-11-17T10:00:00Z",
    "resolvedAt": null
  }
}
```

---

### Security Scanning

#### Scan Transaction

```http
POST /api/security/scan
```

Analyze a Solana transaction for security threats using SecurityGuard AI. Returns risk score (0-100) and natural language explanation in < 2 seconds.

**Risk Levels:**
- **SAFE** (0-30): No threats detected
- **CAUTION** (31-70): Potential risks identified
- **DANGER** (71-100): Critical threats detected

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transaction` | object | Yes | Transaction data (see below) |
| `userWallet` | string | No | Your wallet address |

**Transaction Object:**

```typescript
{
  "serialized": "base64_encoded_transaction",  // Optional
  "instructions": [  // Required
    {
      "programId": "program_public_key",
      "accounts": ["account1", "account2"],
      "data": "instruction_data"
    }
  ]
}
```

**Example Request:**

```bash
curl -X POST https://main.d1qz5jyb1c9oee.amplifyapp.com/api/security/scan \
  -H "Content-Type: application/json" \
  -d '{
    "transaction": {
      "instructions": [
        {
          "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
          "accounts": ["8RDfVn...", "5VRG5k..."],
          "data": "instruction_data_hex"
        }
      ]
    },
    "userWallet": "8RDfVnQJiW7Nn9qbWubNUVJh6B7fmgxCY86TqjSHjTuu"
  }'
```

```javascript
const response = await fetch('https://main.d1qz5jyb1c9oee.amplifyapp.com/api/security/scan', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    transaction: {
      instructions: [
        {
          programId: 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
          accounts: ['8RDfVn...', '5VRG5k...'],
          data: 'instruction_data_hex'
        }
      ]
    },
    userWallet: '8RDfVnQJiW7Nn9qbWubNUVJh6B7fmgxCY86TqjSHjTuu'
  })
});

const scan = await response.json();

if (scan.riskLevel === 'DANGER') {
  alert(`⚠️ ${scan.explanation}`);
  // Don't sign the transaction!
}
```

```python
import requests

response = requests.post(
    'https://main.d1qz5jyb1c9oee.amplifyapp.com/api/security/scan',
    json={
        'transaction': {
            'instructions': [
                {
                    'programId': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
                    'accounts': ['8RDfVn...', '5VRG5k...'],
                    'data': 'instruction_data_hex'
                }
            ]
        },
        'userWallet': '8RDfVnQJiW7Nn9qbWubNUVJh6B7fmgxCY86TqjSHjTuu'
    }
)

scan = response.json()

if scan['riskLevel'] == 'DANGER':
    print(f"⚠️ {scan['explanation']}")
    # Don't sign the transaction!
```

**Example Response - SAFE (200 OK):**

```json
{
  "success": true,
  "scanId": "scan-1700000000-xyz123",
  "riskLevel": "SAFE",
  "riskScore": 15,
  "explanation": "This transaction is a standard SOL transfer to a verified address. No threats detected.",
  "recommendation": "SAFE_TO_SIGN",
  "details": {
    "programChecks": {
      "unknownPrograms": 0,
      "blacklistedPrograms": 0,
      "verifiedPrograms": 1
    },
    "patternMatches": [],
    "mlAnalysis": {
      "anomalyScore": 0.08,
      "classification": "Normal",
      "confidence": 0.96
    },
    "accountFlags": []
  },
  "scanTimeMs": 1247,
  "confidence": 0.96,
  "threatsDetected": []
}
```

**Example Response - DANGER (200 OK):**

```json
{
  "success": true,
  "scanId": "scan-1700000001-abc456",
  "riskLevel": "DANGER",
  "riskScore": 95,
  "explanation": "CRITICAL: This contract will drain your wallet. It requests unlimited token approval and transfers funds to an unknown address associated with known scammers.",
  "recommendation": "BLOCK",
  "details": {
    "programChecks": {
      "unknownPrograms": 1,
      "blacklistedPrograms": 0,
      "verifiedPrograms": 0
    },
    "patternMatches": [
      "Unlimited token approval",
      "Transfer to unknown address",
      "Authority delegation"
    ],
    "mlAnalysis": {
      "anomalyScore": 0.92,
      "classification": "Malicious",
      "confidence": 0.98
    },
    "accountFlags": [
      "Recipient address created 2 days ago",
      "Similar to known wallet drainer patterns"
    ]
  },
  "scanTimeMs": 1847,
  "confidence": 0.98,
  "threatsDetected": [
    "wallet_drainer",
    "unlimited_approval",
    "suspicious_recipient"
  ]
}
```

**Error Responses:**

```json
// 400 Bad Request - Invalid transaction
{
  "error": "Validation error",
  "details": "Transaction data is required",
  "timestamp": "2025-11-17T16:45:00Z",
  "path": "/api/security/scan"
}

// 429 Too Many Requests
{
  "error": "Rate limit exceeded",
  "details": "Maximum 100 requests per minute. Please try again later.",
  "timestamp": "2025-11-17T16:45:00Z",
  "path": "/api/security/scan"
}

// 503 Service Unavailable - SecurityGuard AI down
{
  "error": "Service unavailable",
  "details": "SecurityGuard AI service is temporarily unavailable. Please try again in a few moments.",
  "timestamp": "2025-11-17T16:45:00Z",
  "path": "/api/security/scan"
}
```

---

#### Get Scan History

```http
GET /api/security/scan
```

Retrieve scan history with platform statistics.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `userWallet` | string | Filter by user wallet |
| `riskLevel` | string | Filter by risk level (SAFE, CAUTION, DANGER) |
| `page` | integer | Page number |
| `limit` | integer | Results per page |

**Example Response (200 OK):**

```json
{
  "scans": [
    {
      "scanId": "scan-1700000000-xyz123",
      "userWallet": "8RDfVnQJiW7Nn9qbWubNUVJh6B7fmgxCY86TqjSHjTuu",
      "transactionHash": "tx_hash",
      "riskLevel": "DANGER",
      "riskScore": 95,
      "scanTimeMs": 1847,
      "confidence": 0.98,
      "threatsDetected": ["wallet_drainer", "unlimited_approval"],
      "createdAt": "2025-11-17T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 125,
    "pages": 7
  },
  "statistics": {
    "totalScans": 125487,
    "threatsBlocked": 3847,
    "avgScanTime": 1523,
    "usersProtected": 8921
  }
}
```

---

## Workflows

### Complete Agent Registration Flow

```javascript
// Step 1: Register agent
const registerResponse = await fetch('https://main.d1qz5jyb1c9oee.amplifyapp.com/api/agents', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'MyAgent AI',
    description: 'Performs awesome tasks',
    capabilities: ['Task Automation', 'Data Analysis'],
    pricing: { type: 'per-query', price: 0.05, currency: 'SOL' },
    endpoint: 'https://api.myagent.com/execute',
    creatorWallet: 'YOUR_WALLET_ADDRESS'
  })
});

const { agent } = await registerResponse.json();
console.log(`Agent registered: ${agent.agentId}`);

// Step 2: Monitor requests (poll or webhook)
async function checkRequests() {
  const response = await fetch(
    `https://main.d1qz5jyb1c9oee.amplifyapp.com/api/requests?agentId=${agent.agentId}`
  );
  const { requests } = await response.json();
  
  for (const req of requests) {
    if (req.status === 'pending') {
      // Process request...
      await processAgentRequest(req);
    }
  }
}

// Poll every 5 seconds
setInterval(checkRequests, 5000);
```

---

### Complete Service Request Flow

```javascript
// Step 1: Browse agents
const agentsResponse = await fetch(
  'https://main.d1qz5jyb1c9oee.amplifyapp.com/api/agents?search=security'
);
const { agents } = await agentsResponse.json();

const securityGuard = agents.find(a => a.name === 'SecurityGuard AI');

// Step 2: Create service request
const requestResponse = await fetch('https://main.d1qz5jyb1c9oee.amplifyapp.com/api/requests', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    agentId: securityGuard.agentId,
    userWallet: 'YOUR_WALLET_ADDRESS',
    amount: securityGuard.pricing.price,
    requestData: {
      transaction: 'YOUR_TRANSACTION_DATA'
    }
  })
});

const { request } = await requestResponse.json();
console.log(`Request created: ${request.requestId}`);

// Step 3: Poll for result
async function waitForResult(requestId) {
  while (true) {
    const response = await fetch(
      `https://main.d1qz5jyb1c9oee.amplifyapp.com/api/requests?userWallet=YOUR_WALLET&status=completed`
    );
    const { requests } = await response.json();
    
    const completed = requests.find(r => r.requestId === requestId);
    if (completed) {
      return completed.result;
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2s
  }
}

const result = await waitForResult(request.requestId);
console.log('Result:', result);

// Step 4: Approve result
const approveResponse = await fetch(
  `https://main.d1qz5jyb1c9oee.amplifyapp.com/api/requests/${request.requestId}/approve`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      userWallet: 'YOUR_WALLET_ADDRESS',
      rating: {
        stars: 5,
        reviewText: 'Excellent service!'
      }
    })
  }
);

console.log('Payment released!');
```

---

### Quick Transaction Scan

```javascript
// Scan before signing any transaction
async function scanBeforeSign(transaction) {
  const response = await fetch('https://main.d1qz5jyb1c9oee.amplifyapp.com/api/security/scan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      transaction: {
        instructions: transaction.instructions.map(ix => ({
          programId: ix.programId.toString(),
          accounts: ix.keys.map(k => k.pubkey.toString()),
          data: ix.data.toString('hex')
        }))
      },
      userWallet: wallet.publicKey.toString()
    })
  });

  const scan = await response.json();

  if (scan.riskLevel === 'DANGER') {
    throw new Error(`⚠️ SECURITY THREAT: ${scan.explanation}`);
  }

  if (scan.riskLevel === 'CAUTION') {
    const proceed = confirm(`⚠️ WARNING: ${scan.explanation}\n\nProceed anyway?`);
    if (!proceed) throw new Error('Transaction cancelled by user');
  }

  // Safe to sign
  return scan;
}

// Usage
try {
  const transaction = await program.methods.transfer(...).transaction();
  await scanBeforeSign(transaction);
  await wallet.signTransaction(transaction);
} catch (error) {
  console.error('Transaction blocked:', error.message);
}
```

---

## Error Handling

All API errors follow a consistent format:

```json
{
  "error": "Error type",
  "details": "Human-readable description",
  "timestamp": "2025-11-17T16:45:00Z",
  "path": "/api/endpoint"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 400 | Bad Request | Validation error or invalid parameters |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Temporary service outage |

### Error Code Reference

| Error Type | Common Causes | How to Fix |
|-----------|---------------|------------|
| `Validation error` | Missing required fields | Check request body matches schema |
| `Not found` | Invalid ID or deleted resource | Verify ID is correct |
| `Forbidden` | Wrong wallet address | Use correct wallet for operation |
| `Rate limit exceeded` | Too many requests | Implement backoff, reduce frequency |
| `Service unavailable` | Backend service down | Retry after a few minutes |
| `Database error` | Internal server issue | Contact support if persists |

### Retry Logic

```javascript
async function fetchWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      
      if (response.status === 429) {
        // Rate limited - exponential backoff
        const delay = Math.pow(2, i) * 1000; // 1s, 2s, 4s
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      
      if (response.status === 503) {
        // Service unavailable - retry after delay
        await new Promise(resolve => setTimeout(resolve, 5000));
        continue;
      }
      
      return response;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
}
```

---

## Code Examples

### Complete Integration Example (TypeScript)

```typescript
import { PublicKey } from '@solana/web3.js';

class AgentMarketClient {
  private baseUrl: string;

  constructor(baseUrl = 'https://main.d1qz5jyb1c9oee.amplifyapp.com') {
    this.baseUrl = baseUrl;
  }

  // List agents with search
  async listAgents(search?: string, page = 1, limit = 10) {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...(search && { search })
    });

    const response = await fetch(`${this.baseUrl}/api/agents?${params}`);
    return response.json();
  }

  // Register new agent
  async registerAgent(data: {
    name: string;
    description?: string;
    capabilities?: string[];
    pricing?: object;
    endpoint?: string;
    creatorWallet: string;
  }) {
    const response = await fetch(`${this.baseUrl}/api/agents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.details || 'Failed to register agent');
    }

    return response.json();
  }

  // Create service request
  async createRequest(data: {
    agentId: string;
    userWallet: string;
    amount: number;
    requestData?: object;
  }) {
    const response = await fetch(`${this.baseUrl}/api/requests`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.details || 'Failed to create request');
    }

    return response.json();
  }

  // Scan transaction for threats
  async scanTransaction(transaction: object, userWallet?: string) {
    const response = await fetch(`${this.baseUrl}/api/security/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transaction, userWallet })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.details || 'Scan failed');
    }

    return response.json();
  }

  // Approve service result
  async approveRequest(requestId: string, userWallet: string, rating?: object) {
    const response = await fetch(`${this.baseUrl}/api/requests/${requestId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userWallet, rating })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.details || 'Failed to approve request');
    }

    return response.json();
  }
}

// Usage
const client = new AgentMarketClient();

// Find SecurityGuard AI
const { agents } = await client.listAgents('security');
const securityGuard = agents[0];

// Scan a transaction
const scanResult = await client.scanTransaction({
  instructions: [...] // Your transaction instructions
}, walletAddress);

if (scanResult.riskLevel === 'DANGER') {
  alert(`⚠️ DANGER: ${scanResult.explanation}`);
} else {
  console.log('✅ Transaction is safe');
}
```

---

### Python Integration Example

```python
import requests
from typing import Dict, List, Optional

class AgentMarketClient:
    def __init__(self, base_url='https://main.d1qz5jyb1c9oee.amplifyapp.com'):
        self.base_url = base_url

    def list_agents(self, search: Optional[str] = None, page: int = 1, limit: int = 10) -> Dict:
        """List all agents with optional search"""
        params = {'page': page, 'limit': limit}
        if search:
            params['search'] = search

        response = requests.get(f'{self.base_url}/api/agents', params=params)
        response.raise_for_status()
        return response.json()

    def register_agent(self, name: str, creator_wallet: str, **kwargs) -> Dict:
        """Register a new agent"""
        data = {
            'name': name,
            'creatorWallet': creator_wallet,
            **kwargs
        }

        response = requests.post(f'{self.base_url}/api/agents', json=data)
        response.raise_for_status()
        return response.json()

    def create_request(self, agent_id: str, user_wallet: str, amount: float, request_data: Optional[Dict] = None) -> Dict:
        """Create a service request"""
        data = {
            'agentId': agent_id,
            'userWallet': user_wallet,
            'amount': amount,
            'requestData': request_data or {}
        }

        response = requests.post(f'{self.base_url}/api/requests', json=data)
        response.raise_for_status()
        return response.json()

    def scan_transaction(self, transaction: Dict, user_wallet: Optional[str] = None) -> Dict:
        """Scan transaction for security threats"""
        data = {
            'transaction': transaction,
            'userWallet': user_wallet
        }

        response = requests.post(f'{self.base_url}/api/security/scan', json=data)
        response.raise_for_status()
        return response.json()

    def approve_request(self, request_id: str, user_wallet: str, rating: Optional[Dict] = None) -> Dict:
        """Approve service result"""
        data = {
            'userWallet': user_wallet,
            'rating': rating
        }

        response = requests.post(f'{self.base_url}/api/requests/{request_id}/approve', json=data)
        response.raise_for_status()
        return response.json()


# Usage example
client = AgentMarketClient()

# Find SecurityGuard AI
agents = client.list_agents(search='security')
security_guard = agents['agents'][0]

# Scan a transaction
scan_result = client.scan_transaction({
    'instructions': [
        {
            'programId': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
            'accounts': ['...'],
            'data': '...'
        }
    ]
}, wallet_address)

if scan_result['riskLevel'] == 'DANGER':
    print(f"⚠️ DANGER: {scan_result['explanation']}")
else:
    print('✅ Transaction is safe')
```

---

## Versioning & Changelog

### Current Version: 1.0.0

The AgentMarket API uses semantic versioning (MAJOR.MINOR.PATCH).

- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

### Versioning Strategy

Currently, all endpoints are unversioned. Future versions will use URL path versioning:

```
/api/v2/agents  (future)
/api/agents     (current, treated as v1)
```

### Changelog

#### Version 1.0.0 (2025-11-17)
- ✨ Initial API release
- ✅ Agent registration and listing
- ✅ Service request management
- ✅ SecurityGuard AI transaction scanning
- ✅ Payment escrow and royalty distribution
- ✅ Rating and reputation system
- ✅ Dispute resolution workflow

---

## Support & Resources

- **GitHub Repository**: https://github.com/iamaanahmad/agentmarket
- **Interactive API Docs**: https://main.d1qz5jyb1c9oee.amplifyapp.com/api-docs (Coming Soon)
- **OpenAPI Specification**: https://main.d1qz5jyb1c9oee.amplifyapp.com/api/openapi.json
- **Discord Community**: [Join Discord](#) (Coming Soon)

---

**Last Updated:** November 17, 2025  
**API Version:** 1.0.0
