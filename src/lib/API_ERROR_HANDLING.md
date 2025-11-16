# API Error Handling Documentation

## Overview

All API endpoints in the AgentMarket platform use standardized error handling to ensure consistent error responses, proper HTTP status codes, and secure error logging.

## Error Response Format

All error responses follow this consistent structure:

```typescript
interface ApiErrorResponse {
  error: string        // Human-readable error message
  details?: string     // Optional additional context
}
```

## HTTP Status Codes

| Status Code | Usage | Function |
|-------------|-------|----------|
| 400 | Validation errors, missing required fields | `validationError()` |
| 403 | Authorization failures, forbidden access | `forbiddenError()` |
| 404 | Resource not found | `notFoundError()` |
| 500 | Database errors, internal server errors | `databaseError()`, `internalError()` |
| 503 | External service unavailable | `serviceUnavailableError()` |

## Error Handling Functions

### validationError(message, endpoint, userWallet?)

Returns a 400 error for validation failures.

**Example:**
```typescript
if (!name?.trim()) {
  return validationError('Agent name is required', 'POST /api/agents')
}
```

### notFoundError(resource, endpoint, userWallet?)

Returns a 404 error when a resource doesn't exist.

**Example:**
```typescript
if (agentCheck.rows.length === 0) {
  return notFoundError('Agent', 'POST /api/requests', userWallet)
}
```

### forbiddenError(message, endpoint, userWallet?)

Returns a 403 error for authorization failures.

**Example:**
```typescript
if (serviceRequest.user_wallet !== userWallet) {
  return forbiddenError('Not authorized to approve this request', 'POST /api/requests/[id]/approve', userWallet)
}
```

### databaseError(endpoint, originalError, userWallet?)

Returns a 500 error for database operation failures. Automatically sanitizes sensitive information.

**Example:**
```typescript
try {
  const result = await client.query('SELECT * FROM agents')
  return NextResponse.json({ agents: result.rows })
} catch (error: unknown) {
  return databaseError('GET /api/agents', error)
}
```

### serviceUnavailableError(serviceName, endpoint, userWallet?)

Returns a 503 error when an external service is unavailable.

**Example:**
```typescript
if (isFetchError(error)) {
  return serviceUnavailableError('SecurityGuard AI', 'POST /api/security/scan', userWallet)
}
```

### internalError(endpoint, originalError, userWallet?)

Returns a 500 error for unexpected internal errors. Never exposes internal details to clients.

**Example:**
```typescript
try {
  // Complex operation
} catch (error: unknown) {
  return internalError('POST /api/complex-operation', error)
}
```

## Security Features

### Automatic Sanitization

All error messages are automatically sanitized to remove:
- Database credentials (passwords)
- API keys (32+ character alphanumeric strings)
- File paths that expose system structure

### Structured Logging

All errors are logged with structured context:
```json
{
  "timestamp": "2025-11-08T10:30:00.000Z",
  "endpoint": "POST /api/agents",
  "errorType": "validation",
  "userWallet": "wallet123",
  "errorMessage": "Agent name is required"
}
```

### No Sensitive Data Exposure

- Stack traces are never sent to clients
- Database error details are sanitized
- Internal system information is hidden

## Helper Functions

### isFetchError(error)

Detects if an error is a fetch/network error.

**Example:**
```typescript
if (isFetchError(error)) {
  return serviceUnavailableError('External API', endpoint)
}
```

### isJsonError(error)

Detects if an error is a JSON parsing error.

**Example:**
```typescript
if (isJsonError(error)) {
  return validationError('Invalid JSON in request body', endpoint)
}
```

## Usage Examples

### Basic GET Endpoint

```typescript
import { databaseError } from '@/lib/api-error'

export async function GET(request: NextRequest) {
  const pool = createPool()
  let client

  try {
    client = await pool.connect()
    const result = await client.query('SELECT * FROM agents')
    return NextResponse.json({ agents: result.rows })
  } catch (error: unknown) {
    return databaseError('GET /api/agents', error)
  } finally {
    if (client) client.release()
    await pool.end()
  }
}
```

### POST Endpoint with Validation

```typescript
import { validationError, notFoundError, databaseError } from '@/lib/api-error'

export async function POST(request: NextRequest) {
  const pool = createPool()
  let client
  let body: any

  try {
    body = await request.json()
    const { agentId, userWallet, amount } = body

    // Validation
    if (!agentId?.trim()) {
      return validationError('Agent ID is required', 'POST /api/requests', userWallet)
    }
    if (!amount || amount <= 0) {
      return validationError('Valid payment amount is required', 'POST /api/requests', userWallet)
    }

    client = await pool.connect()

    // Check if resource exists
    const agentCheck = await client.query('SELECT id FROM agents WHERE agent_id = $1', [agentId])
    if (agentCheck.rows.length === 0) {
      return notFoundError('Agent', 'POST /api/requests', userWallet)
    }

    // Create request
    const result = await client.query('INSERT INTO service_requests ...')
    return NextResponse.json({ success: true, request: result.rows[0] })
  } catch (error: unknown) {
    return databaseError('POST /api/requests', error, body?.userWallet)
  } finally {
    if (client) client.release()
    await pool.end()
  }
}
```

### Endpoint with Authorization

```typescript
import { validationError, notFoundError, forbiddenError, databaseError } from '@/lib/api-error'

export async function POST(request: NextRequest, { params }: { params: { id: string } }) {
  const pool = createPool()
  let client
  let body: any

  try {
    body = await request.json()
    const { userWallet } = body

    if (!userWallet?.trim()) {
      return validationError('User wallet address is required', 'POST /api/requests/[id]/approve')
    }

    client = await pool.connect()

    const requestResult = await client.query('SELECT * FROM service_requests WHERE request_id = $1', [params.id])
    
    if (requestResult.rows.length === 0) {
      return notFoundError('Service request', 'POST /api/requests/[id]/approve', userWallet)
    }

    const serviceRequest = requestResult.rows[0]

    // Authorization check
    if (serviceRequest.user_wallet !== userWallet) {
      return forbiddenError('Not authorized to approve this request', 'POST /api/requests/[id]/approve', userWallet)
    }

    // Process approval
    await client.query('UPDATE service_requests SET status = $1 WHERE request_id = $2', ['approved', params.id])
    return NextResponse.json({ success: true })
  } catch (error: unknown) {
    return databaseError('POST /api/requests/[id]/approve', error, body?.userWallet)
  } finally {
    if (client) client.release()
    await pool.end()
  }
}
```

### External Service Integration

```typescript
import { validationError, serviceUnavailableError, databaseError, isFetchError } from '@/lib/api-error'

export async function POST(request: NextRequest) {
  let body: any

  try {
    body = await request.json()
    const { transaction, userWallet } = body

    if (!transaction) {
      return validationError('Transaction data is required', 'POST /api/security/scan', userWallet)
    }

    // Call external service
    const scanResponse = await fetch(`${SECURITY_AI_URL}/api/security/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transaction, user_wallet: userWallet }),
    })

    if (!scanResponse.ok) {
      const errorData = await scanResponse.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'SecurityGuard AI scan failed', details: errorData.error || 'Service error' },
        { status: scanResponse.status }
      )
    }

    const scanResult = await scanResponse.json()
    return NextResponse.json({ success: true, ...scanResult })
  } catch (error: unknown) {
    if (isFetchError(error)) {
      return serviceUnavailableError('SecurityGuard AI', 'POST /api/security/scan', body?.userWallet)
    }
    return databaseError('POST /api/security/scan', error, body?.userWallet)
  }
}
```

## Testing Error Scenarios

When testing API endpoints, verify:

1. **Validation errors return 400** with clear messages
2. **Missing resources return 404** with resource name
3. **Authorization failures return 403** with reason
4. **Database errors return 500** without sensitive details
5. **External service failures return 503** with service name
6. **All errors are logged** with structured context
7. **No stack traces** are exposed to clients
8. **Sensitive data is sanitized** in logs

## CloudWatch Integration

All error logs are structured JSON for easy CloudWatch Insights queries:

```
fields @timestamp, endpoint, errorType, userWallet, errorMessage
| filter errorType = "database"
| sort @timestamp desc
| limit 100
```

## Best Practices

1. **Always use error helper functions** instead of manual NextResponse.json()
2. **Include endpoint name** in all error calls for traceability
3. **Pass userWallet** when available for user-specific debugging
4. **Catch errors at the top level** of each route handler
5. **Never expose internal details** to clients
6. **Log errors with context** for debugging
7. **Use appropriate HTTP status codes** for each error type
8. **Sanitize all error messages** before logging

## Compliance

This error handling system ensures:
- **GDPR compliance**: No PII in error responses
- **Security best practices**: No credential exposure
- **Audit trail**: All errors logged with context
- **User privacy**: Wallet addresses only logged when relevant
- **Production readiness**: Consistent error handling across all endpoints
