# Marketplace API - Implementation Tasks

## Overview

This implementation plan covers the backend API layer for AgentMarket, providing RESTful endpoints for agent management, service requests, payment processing, and security scanning. The API is built with Next.js 14 API Routes, PostgreSQL database, and integrates with SecurityGuard AI.

---

## Phase 1: Database Infrastructure ✅ COMPLETE

- [x] 1. Set up database connection utilities
  - Create `src/lib/db.ts` with connection pool configuration
  - Implement `createPool()` function with RDS configuration
  - Implement `query()` helper for simple queries
  - Implement `transaction()` helper for transactional operations
  - Implement pagination helpers (`buildPagination`, `calculatePagination`)
  - Add TypeScript interfaces for database types
  - _Requirements: Req 9, Req 10_

- [x] 2. Initialize database schema
  - Create `scripts/init_database.sql` with complete schema
  - Define all tables (agents, service_requests, ratings, disputes, security_scans, analytics_events, platform_config)
  - Create indexes for performance optimization (agents, requests, ratings, disputes, scans)
  - Create database views for statistics (agent_stats, user_stats)
  - Add triggers for updated_at timestamps
  - Document table relationships and constraints
  - _Requirements: Req 1, Req 2, Req 3, Req 4, Req 5, Req 6, Req 7, Req 8_

---

## Phase 2: Agent Management Endpoints ✅ COMPLETE

- [x] 3. Implement GET /api/agents (List Agents)
  - Create `src/app/api/agents/route.ts` with GET handler
  - Parse query parameters (page, limit, search)
  - Build dynamic SQL query with search filtering (name, description)
  - Join with ratings table to calculate average rating and count
  - Implement pagination with offset/limit
  - Format response with agent metadata and pagination info
  - Add error handling and logging
  - _Requirements: Req 1_

- [x] 4. Implement POST /api/agents (Register Agent)
  - Add POST handler to `src/app/api/agents/route.ts`
  - Validate required fields (name, creatorWallet)
  - Generate unique agent_id using timestamp and random string
  - Insert agent record into database with default values
  - Return created agent details (id, agentId, name, createdAt)
  - Handle database errors and duplicate entries
  - _Requirements: Req 2_

---

## Phase 3: Service Request Endpoints ✅ COMPLETE

- [x] 5. Implement POST /api/requests (Create Service Request)
  - Create `src/app/api/requests/route.ts` with POST handler
  - Validate required fields (agentId, userWallet, amount)
  - Verify agent exists and is active
  - Generate unique request_id
  - Insert service_request record with status 'pending'
  - Return request details with success message
  - _Requirements: Req 3_

- [x] 6. Implement GET /api/requests (List Service Requests)
  - Add GET handler to `src/app/api/requests/route.ts`
  - Parse query parameters (userWallet, agentId, status, page, limit)
  - Build filtered SQL query with dynamic WHERE clauses
  - Join with agents table to include agent name
  - Implement pagination
  - Return requests with pagination metadata
  - _Requirements: Req 4_

- [x] 7. Implement POST /api/requests/[id]/approve (Approve Request)
  - Create `src/app/api/requests/[id]/approve/route.ts`
  - Use database transaction for atomic operations
  - Verify request ownership (userWallet matches)
  - Verify request status is 'completed'
  - Update request status to 'approved'
  - Calculate payment splits (85% creator, 10% platform, 5% treasury)
  - Update agent total_earnings and total_services
  - Handle optional rating submission (stars, quality, speed, value, reviewText)
  - Recalculate agent average_rating if rating provided
  - Commit transaction or rollback on error
  - _Requirements: Req 5_

- [x] 8. Implement POST /api/requests/[id]/dispute (Create Dispute)
  - Create `src/app/api/requests/[id]/dispute/route.ts` with POST handler
  - Use database transaction for atomic operations
  - Validate required fields (userWallet, reason)
  - Verify request ownership
  - Verify request status is 'completed'
  - Update request status to 'disputed'
  - Store dispute_reason in request_data JSONB field
  - Create dispute record with generated dispute_id
  - Return dispute details
  - _Requirements: Req 6_

- [x] 9. Implement GET /api/requests/[id]/dispute (Get Dispute Details)
  - Add GET handler to `src/app/api/requests/[id]/dispute/route.ts`
  - Fetch dispute record by request_id
  - Join with agents table for agent name
  - Return dispute details (disputeId, status, reason, resolution, timestamps)
  - Handle not found case with 404 error
  - _Requirements: Req 6_

---

## Phase 4: Security Scan Endpoints ✅ COMPLETE

- [x] 10. Implement POST /api/security/scan (Scan Transaction)
  - Create `src/app/api/security/scan/route.ts` with POST handler
  - Validate transaction data in request body
  - Track scan start time for performance measurement
  - Forward request to SecurityGuard AI backend (FastAPI)
  - Handle SecurityGuard AI response
  - Save scan result to security_scans table (scanId, riskLevel, riskScore, scanTimeMs, confidence, threatsDetected)
  - Calculate and return scan time
  - Handle SecurityGuard AI unavailable with 503 error
  - Return formatted scan result with all details
  - _Requirements: Req 7_

- [x] 11. Implement GET /api/security/scan (Scan History)
  - Add GET handler to `src/app/api/security/scan/route.ts`
  - Parse query parameters (userWallet, riskLevel, page, limit)
  - Build filtered SQL query with dynamic WHERE clauses
  - Implement pagination
  - Calculate aggregate statistics (totalScans, threatsBlocked, avgScanTime, usersProtected)
  - Return scans with pagination and statistics
  - _Requirements: Req 8_

---

## Phase 5: Code Quality & Bug Fixes 🔧 IN PROGRESS

- [x] 12. Fix code quality issues across all API routes





  - Replace deprecated `.substr()` with `.substring()` in all files (agents, requests, approve, dispute, scan routes)
  - Fix SQL parameter placeholder syntax - replace string interpolation `${paramCount + 1}` with proper `$1, $2, $3` syntax
  - Refactor RDS_CONFIG duplication - import `RDS_CONFIG` from `@/lib/db` instead of redefining in each file
  - Import `Pool` from `@/lib/db` using `createPool()` instead of direct `pg` import
  - Fix unused variable warnings (remove `agent` variable in approve route, `request` in dispute GET)
  - Ensure consistent error handling patterns across all routes
  - _Requirements: Req 11_

- [x] 13. Standardize error responses





  - Review all endpoints for consistent error format `{ error: string, details?: string }`
  - Verify appropriate HTTP status codes (400 validation, 403 forbidden, 404 not found, 500 server error, 503 unavailable)
  - Add structured error logging with context (endpoint, error type, user info)
  - Remove sensitive information from error responses (no database credentials, stack traces)
  - Test error scenarios for each endpoint
  - _Requirements: Req 11_

---

## Phase 6: Performance & Optimization

- [ ] 14. Optimize database queries and performance





  - Review all SQL queries for efficiency
  - Verify indexes are being used (run EXPLAIN ANALYZE on key queries)
  - Optimize JOIN operations in agent listing and request listing
  - Test query performance with large datasets (1000+ agents, 10000+ requests)
  - Measure response times and ensure <500ms for GET, <1s for POST
  - _Requirements: Req 12_

---

## Phase 7: Testing & Validation

- [ ] 15. Perform end-to-end API testing
  - Test GET /api/agents with various search and pagination parameters
  - Test POST /api/agents with valid and invalid data
  - Test POST /api/requests with valid agent and invalid agent
  - Test GET /api/requests with different filters
  - Test POST /api/requests/[id]/approve with payment calculation
  - Test POST /api/requests/[id]/dispute flow
  - Test POST /api/security/scan integration with SecurityGuard AI
  - Test GET /api/security/scan with filters and statistics
  - Test error scenarios (404, 400, 403, 500)
  - Verify database transactions rollback on error
  - _Requirements: All_

---

## Phase 8: Documentation & Deployment

- [ ] 16. Create API documentation
  - Document all endpoints with request/response formats
  - Add example requests and responses for each endpoint
  - Document query parameters and validation rules
  - Document error codes and messages
  - Create OpenAPI/Swagger specification (optional)
  - _Requirements: All_

- [ ] 17. Configure environment variables for deployment
  - Create `.env.example` with all required variables (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, SECURITY_AI_URL)
  - Document each environment variable purpose
  - Set up environment variables in AWS Amplify console
  - Verify database connection in production environment
  - Test SecurityGuard AI integration in production
  - _Requirements: Req 9_

---

## Optional Tasks (Marked with *)

- [ ]* 2.1 Create database initialization script
  - Write Node.js script to execute init_database.sql
  - Add connection verification and health check
  - Handle existing tables gracefully
  - _Requirements: Req 9_

- [ ]* 4.1 Add Zod input validation
  - Create Zod schemas for agent registration
  - Validate Solana wallet address format
  - Validate pricing structure
  - Add custom error messages
  - _Requirements: Req 11_

- [ ]* 13.1 Create error handling middleware
  - Create reusable error handler function
  - Add error type detection (validation, database, external service)
  - Format errors consistently
  - _Requirements: Req 11_

- [ ]* 14.1 Add query performance monitoring
  - Log slow queries (>1 second)
  - Add query timing to responses in development mode
  - Create performance dashboard
  - _Requirements: Req 12_

- [ ]* 15.1 Write automated API tests
  - Create test suite with Jest or Vitest
  - Mock database connections
  - Test each endpoint with valid inputs
  - Test error handling
  - Test pagination logic
  - _Requirements: All_

- [ ]* 15.2 Load test API endpoints
  - Use k6 or Artillery for load testing
  - Test with 100 concurrent requests
  - Measure response times (p50, p95, p99)
  - Verify connection pool handles load
  - _Requirements: Req 12_

- [ ]* 17.1 Set up monitoring and logging
  - Configure CloudWatch logs for Lambda functions
  - Create CloudWatch alarms for errors and latency
  - Set up log aggregation
  - Create monitoring dashboard
  - _Requirements: Req 12_

---

## Implementation Notes

### Database Connection Pattern
```typescript
import { createPool } from '@/lib/db'

export async function GET(request: NextRequest) {
  const pool = createPool()
  let client
  try {
    client = await pool.connect()
    const result = await client.query('SELECT ...')
    return NextResponse.json({ data: result.rows })
  } catch (error) {
    console.error('Error:', error)
    return NextResponse.json({ error: 'Message' }, { status: 500 })
  } finally {
    if (client) client.release()
    await pool.end()
  }
}
```

### Transaction Pattern
```typescript
import { transaction } from '@/lib/db'

const result = await transaction(async (client) => {
  await client.query('UPDATE ...')
  await client.query('INSERT ...')
  return { success: true }
})
```

### SQL Parameter Syntax (IMPORTANT)
```typescript
// ✅ CORRECT: Use $1, $2, $3 placeholders
await client.query('SELECT * FROM agents WHERE id = $1 AND active = $2', [id, true])

// ❌ WRONG: String interpolation creates SQL injection risk
await client.query(`SELECT * FROM agents WHERE id = ${id}`)
```

---

## Success Criteria

- [x] All 6 endpoint groups implemented (agents, requests, disputes, security)
- [x] Database schema initialized with all tables and indexes
- [x] Database connection utilities with pooling and transactions
- [x] Transaction support for approve and dispute flows
- [x] SecurityGuard AI integration with error handling
- [x] Pagination and filtering for all list endpoints
- [ ] Code quality issues fixed (deprecated methods, SQL syntax)
- [ ] Error handling is consistent across all endpoints
- [ ] Response times meet requirements (<500ms GET, <1s POST)
- [ ] API documentation complete
- [ ] Environment variables configured for deployment

---

## Current Status Summary

**✅ Completed (Phases 1-4):**
- Complete database infrastructure with connection pooling, transactions, and pagination helpers
- All 6 API endpoint groups fully implemented
- Agent listing with search, filtering, and ratings aggregation
- Agent registration with validation
- Service request creation and listing with filters
- Request approval with payment splits and rating support
- Request dispute creation and retrieval
- Security scan integration with SecurityGuard AI
- Scan history with statistics

**🔧 In Progress (Phase 5):**
- Code quality fixes needed (deprecated methods, SQL syntax, imports)
- Error response standardization

**📋 Remaining (Phases 6-8):**
- Performance optimization and query analysis
- End-to-end testing
- API documentation
- Environment variable configuration

**Estimated Time Remaining:** 4-5 hours for core tasks (excluding optional tasks)
