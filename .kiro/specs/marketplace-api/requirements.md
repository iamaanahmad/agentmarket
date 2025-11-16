# Marketplace API Requirements

## Introduction

The Marketplace API provides the backend services for AgentMarket's core functionality, enabling agent registration, service requests, payment processing, and security scanning. This API layer connects the Next.js frontend with the PostgreSQL database and Solana blockchain, while integrating with SecurityGuard AI for transaction analysis.

## Glossary

- **Marketplace_API**: The RESTful API layer providing backend services for the AgentMarket platform
- **Agent_Endpoint**: API routes for agent registration, listing, and management
- **Request_Endpoint**: API routes for creating and managing service requests
- **Security_Endpoint**: API routes for transaction security scanning via SecurityGuard AI
- **RDS_Database**: Amazon RDS PostgreSQL database storing off-chain metadata
- **API_Route**: Next.js API route handler (serverless function)
- **Service_Request**: A paid request from a user to hire an AI agent
- **Escrow_Payment**: Payment held in smart contract until service completion
- **Dispute_Resolution**: Process for handling disputed service requests

## Requirements

### Requirement 1: Agent Listing API

**User Story:** As a frontend developer, I want to fetch a paginated list of agents with search and filtering, so that users can discover available AI agents in the marketplace.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/agents`, THE system SHALL return a paginated list of active agents
2. THE API SHALL support search by agent name or description using the `search` query parameter
3. THE API SHALL support filtering by capability, rating, and price range
4. THE response SHALL include agent metadata, average rating, and total services completed
5. THE API SHALL return results within 500ms for queries under 1000 agents

### Requirement 2: Agent Registration API

**User Story:** As an agent creator, I want to register my AI agent via API, so that it appears in the marketplace and can receive service requests.

#### Acceptance Criteria

1. WHEN a POST request is made to `/api/agents`, THE system SHALL validate all required fields
2. THE system SHALL generate a unique agent_id for the new agent
3. THE system SHALL store agent metadata in the PostgreSQL database
4. THE API SHALL return the created agent details including agent_id
5. IF validation fails, THE system SHALL return a 400 error with specific field errors

### Requirement 3: Service Request Creation API

**User Story:** As a platform user, I want to create service requests via API, so that I can hire AI agents programmatically.

#### Acceptance Criteria

1. WHEN a POST request is made to `/api/requests`, THE system SHALL validate agent existence and user wallet
2. THE system SHALL create a service request record with status "pending"
3. THE system SHALL generate a unique request_id for tracking
4. THE API SHALL return the request details including request_id and status
5. THE system SHALL support webhook notification to the agent endpoint (future enhancement)

### Requirement 4: Service Request Listing API

**User Story:** As a platform user, I want to view my service request history, so that I can track the status of my hired agents.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/requests`, THE system SHALL return a paginated list of service requests
2. THE API SHALL support filtering by userWallet, agentId, and status
3. THE response SHALL include request details, agent name, and timestamps
4. THE API SHALL return results ordered by creation date (newest first)
5. THE pagination SHALL support page and limit parameters with sensible defaults

### Requirement 5: Request Approval API

**User Story:** As a platform user, I want to approve completed service requests, so that payment is released to the agent creator.

#### Acceptance Criteria

1. WHEN a POST request is made to `/api/requests/[id]/approve`, THE system SHALL verify request ownership
2. THE system SHALL validate that the request status is "completed"
3. THE system SHALL update the request status to "approved"
4. THE system SHALL calculate and record payment splits (85% creator, 10% platform, 5% treasury)
5. IF a rating is provided, THE system SHALL create a rating record and update agent average rating

### Requirement 6: Request Dispute API

**User Story:** As a platform user, I want to dispute unsatisfactory service results, so that I can request manual review and potential refund.

#### Acceptance Criteria

1. WHEN a POST request is made to `/api/requests/[id]/dispute`, THE system SHALL verify request ownership
2. THE system SHALL validate that the request status is "completed"
3. THE system SHALL update the request status to "disputed"
4. THE system SHALL create a dispute record with the user's reason
5. THE system SHALL support GET requests to retrieve dispute details

### Requirement 7: Security Scan API

**User Story:** As a Solana user, I want to scan transactions for security threats via API, so that I can protect my wallet from exploits.

#### Acceptance Criteria

1. WHEN a POST request is made to `/api/security/scan`, THE system SHALL forward the request to SecurityGuard AI backend
2. THE system SHALL record the scan result in the database with risk level and score
3. THE API SHALL return scan results within 2 seconds for 95% of requests
4. THE response SHALL include risk_level, risk_score, explanation, and threats_detected
5. IF SecurityGuard AI is unavailable, THE system SHALL return a 503 error with graceful message

### Requirement 8: Security Scan History API

**User Story:** As a platform user, I want to view my scan history, so that I can review past security analyses.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/security/scan`, THE system SHALL return paginated scan history
2. THE API SHALL support filtering by userWallet and riskLevel
3. THE response SHALL include aggregate statistics (total scans, threats blocked, avg scan time)
4. THE API SHALL return results ordered by creation date (newest first)
5. THE statistics SHALL be calculated efficiently without impacting response time

### Requirement 9: Database Connection Management

**User Story:** As a backend developer, I want efficient database connection pooling, so that the API can handle concurrent requests without connection exhaustion.

#### Acceptance Criteria

1. THE system SHALL use PostgreSQL connection pooling with configurable pool size
2. THE system SHALL automatically release connections after query completion
3. THE system SHALL handle connection errors gracefully with retry logic
4. THE connection configuration SHALL support environment variables for different environments
5. THE system SHALL log connection pool metrics for monitoring

### Requirement 10: Transaction Support

**User Story:** As a backend developer, I want database transaction support, so that multi-step operations maintain data consistency.

#### Acceptance Criteria

1. THE system SHALL support BEGIN/COMMIT/ROLLBACK transaction control
2. WHEN an error occurs during a transaction, THE system SHALL automatically rollback changes
3. THE approve and dispute endpoints SHALL use transactions for data consistency
4. THE system SHALL provide a transaction helper function for reusable transaction logic
5. THE transaction timeout SHALL be configurable to prevent long-running locks

### Requirement 11: Error Handling and Validation

**User Story:** As a frontend developer, I want consistent error responses, so that I can handle errors predictably in the UI.

#### Acceptance Criteria

1. THE API SHALL return standardized error responses with error message and details
2. THE system SHALL validate all input parameters before processing
3. THE API SHALL return appropriate HTTP status codes (400 for validation, 404 for not found, 500 for server errors)
4. THE system SHALL log all errors with sufficient context for debugging
5. THE API SHALL never expose sensitive information (database credentials, stack traces) in error responses

### Requirement 12: Performance and Scalability

**User Story:** As a platform operator, I want the API to handle high load efficiently, so that users have a responsive experience.

#### Acceptance Criteria

1. THE API SHALL respond to GET requests within 500ms for 95% of requests
2. THE API SHALL respond to POST requests within 1 second for 95% of requests
3. THE system SHALL support at least 100 concurrent requests without degradation
4. THE database queries SHALL use proper indexes for efficient data retrieval
5. THE system SHALL implement pagination for all list endpoints to prevent large result sets

## Technical Constraints

- **Framework**: Next.js 14 API Routes with TypeScript
- **Database**: PostgreSQL via node-postgres (pg) library
- **Connection Pooling**: Maximum 10 connections per pool
- **Response Format**: JSON with consistent structure
- **Authentication**: JWT tokens with Solana wallet signatures (future enhancement)
- **Rate Limiting**: 60 requests per minute per IP (future enhancement)

## Success Metrics

- All 6 API endpoint groups implemented and tested
- Response times meet performance requirements (95th percentile)
- Zero SQL injection vulnerabilities
- 100% of endpoints have error handling
- Database connection pool operates without exhaustion
- API documentation complete and accurate

## Dependencies

- PostgreSQL database with schema initialized
- SecurityGuard AI FastAPI service running
- Environment variables configured for database connection
- Next.js 14 with App Router

This API layer is critical for the hackathon submission, providing the backend foundation that connects the frontend user experience with blockchain smart contracts and AI services.
