# Frontend Integration Requirements

## Introduction

This specification defines the requirements for integrating the AgentMarket frontend with the working backend APIs. The frontend currently uses mock data and needs to be connected to real API endpoints to enable full end-to-end functionality. This integration is critical for demonstrating the complete platform to hackathon judges and achieving the 1st prize goal.

## Glossary

- **Frontend**: The Next.js 14 application with React components that users interact with
- **Backend API**: The Next.js API routes that handle data operations and communicate with the database
- **AgentGrid**: The component that displays a list of AI agents in the marketplace
- **FeaturedAgents**: The component that shows top-rated agents on the homepage
- **HireAgentModal**: A dialog component that allows users to create service requests for agents
- **Dashboard**: The user interface showing a user's service requests and activity
- **Agent Detail Page**: A dedicated page showing comprehensive information about a specific agent
- **Mock Data**: Hardcoded sample data used during development
- **Real API Data**: Live data fetched from backend endpoints connected to the database
- **Service Request**: A user's request to hire an AI agent for a specific task
- **Wallet**: A Solana wallet (Phantom, Solflare, etc.) used for authentication and payments

## Requirements

### Requirement 1: Agent Listing Integration

**User Story:** As a marketplace visitor, I want to see real AI agents from the database, so that I can browse actual available services.

#### Acceptance Criteria

1. WHEN THE Frontend loads the marketplace page, THE AgentGrid component SHALL fetch agents from the `/api/agents` endpoint
2. WHEN THE AgentGrid receives the API response, THE AgentGrid SHALL transform the response data to match the component's interface
3. WHILE THE AgentGrid is fetching data, THE AgentGrid SHALL display loading skeletons
4. IF THE API request fails, THEN THE AgentGrid SHALL display an error message with a retry option
5. WHEN THE user applies search filters, THE AgentGrid SHALL send the search query as a parameter to the API endpoint

### Requirement 2: Featured Agents Display

**User Story:** As a homepage visitor, I want to see the top-performing agents, so that I can quickly discover high-quality services.

#### Acceptance Criteria

1. WHEN THE Frontend loads the homepage, THE FeaturedAgents component SHALL fetch the top 3 agents from the `/api/agents` endpoint with sorting by rating
2. WHILE THE FeaturedAgents is loading, THE FeaturedAgents component SHALL display skeleton placeholders
3. IF THE API returns no agents or fails, THEN THE FeaturedAgents component SHALL hide the section gracefully
4. WHEN THE FeaturedAgents receives data, THE FeaturedAgents component SHALL display agent cards with real information

### Requirement 3: Service Request Creation

**User Story:** As a connected wallet user, I want to hire an AI agent, so that I can request services and create transactions.

#### Acceptance Criteria

1. WHEN THE user clicks "Hire Agent", THE HireAgentModal SHALL open with a form to describe the service request
2. WHEN THE user submits the hire form, THE HireAgentModal SHALL send a POST request to `/api/requests` with the agent ID, user wallet, amount, and request description
3. IF THE user's wallet is not connected, THEN THE HireAgentModal SHALL display an error message prompting wallet connection
4. IF THE request creation succeeds, THEN THE HireAgentModal SHALL close and display a success message with the request ID
5. IF THE request creation fails, THEN THE HireAgentModal SHALL display the error message without closing the modal

### Requirement 4: User Dashboard

**User Story:** As a connected wallet user, I want to view my service requests, so that I can track my activity and request statuses.

#### Acceptance Criteria

1. WHEN THE user navigates to the dashboard, THE Dashboard page SHALL fetch requests from `/api/requests` filtered by the user's wallet address
2. WHEN THE Dashboard receives request data, THE Dashboard SHALL display a table with request details including agent name, amount, status, and creation date
3. WHILE THE Dashboard is loading, THE Dashboard SHALL display loading skeletons
4. IF THE user's wallet is not connected, THEN THE Dashboard SHALL display a message prompting wallet connection
5. WHEN THE Dashboard displays requests, THE Dashboard SHALL show summary statistics including total requests, active requests, completed requests, and disputed requests

### Requirement 5: Agent Detail View

**User Story:** As a marketplace visitor, I want to view detailed information about an agent, so that I can make informed decisions before hiring.

#### Acceptance Criteria

1. WHEN THE user clicks "View Details" on an agent card, THE Frontend SHALL navigate to the agent detail page at `/agents/[id]`
2. WHEN THE Agent Detail Page loads, THE Agent Detail Page SHALL fetch the agent's information from the `/api/agents` endpoint
3. WHEN THE Agent Detail Page displays the agent, THE Agent Detail Page SHALL show comprehensive information including name, description, capabilities, pricing, rating, creator wallet, and endpoint
4. WHEN THE Agent Detail Page is displayed, THE Agent Detail Page SHALL include a "Hire Agent" button that opens the HireAgentModal
5. IF THE agent is not found, THEN THE Agent Detail Page SHALL display a "not found" error message

### Requirement 6: Agent Registration

**User Story:** As an AI agent creator, I want to register my agent on the platform, so that I can offer services and earn revenue.

#### Acceptance Criteria

1. WHEN THE creator submits the registration form, THE Register Agent Page SHALL send a POST request to `/api/agents` with agent details
2. WHEN THE registration succeeds, THE Register Agent Page SHALL redirect to the newly created agent's detail page
3. IF THE creator's wallet is not connected, THEN THE Register Agent Page SHALL display an error message
4. IF THE registration fails, THEN THE Register Agent Page SHALL display the error message and keep the form data
5. WHEN THE registration form is displayed, THE Register Agent Page SHALL validate required fields including name, description, capabilities, pricing, and endpoint

### Requirement 7: Error Handling and User Feedback

**User Story:** As a user, I want clear feedback when operations succeed or fail, so that I understand what's happening and can take appropriate action.

#### Acceptance Criteria

1. WHEN ANY API request fails, THE Frontend SHALL display a user-friendly error message
2. WHEN ANY API request is in progress, THE Frontend SHALL display loading indicators
3. WHEN ANY operation succeeds, THE Frontend SHALL display a success message or confirmation
4. IF THE Backend is unavailable, THEN THE Frontend SHALL display a message indicating the service is temporarily unavailable
5. WHEN THE user encounters an error, THE Frontend SHALL provide actionable next steps (e.g., "Try again", "Connect wallet")

### Requirement 8: Data Transformation and Compatibility

**User Story:** As a developer, I want the frontend to correctly transform API responses, so that components receive data in the expected format.

#### Acceptance Criteria

1. WHEN THE Frontend receives agent data from the API, THE Frontend SHALL transform field names from snake_case to camelCase
2. WHEN THE Frontend transforms agent data, THE Frontend SHALL map `agent_id` to `nftMint`, `creator_wallet` to `creatorAddress`, and `rating.average` to `rating`
3. WHEN THE Frontend transforms agent data, THE Frontend SHALL provide default values for missing optional fields
4. WHEN THE Frontend sends data to the API, THE Frontend SHALL use the correct field names expected by the backend
5. WHEN THE Frontend handles pagination, THE Frontend SHALL correctly parse and use pagination metadata from API responses

### Requirement 9: Performance and User Experience

**User Story:** As a user, I want the interface to be responsive and fast, so that I have a smooth browsing experience.

#### Acceptance Criteria

1. WHEN THE Frontend loads any page, THE Frontend SHALL display initial content within 2 seconds
2. WHEN THE user performs search or filtering, THE Frontend SHALL update results within 1 second
3. WHEN THE Frontend displays lists, THE Frontend SHALL implement pagination or infinite scroll to handle large datasets
4. WHEN THE Frontend makes API calls, THE Frontend SHALL implement proper caching to avoid redundant requests
5. WHEN THE Frontend displays images or heavy content, THE Frontend SHALL implement lazy loading

### Requirement 10: Mobile Responsiveness

**User Story:** As a mobile user, I want the interface to work well on my device, so that I can use the platform anywhere.

#### Acceptance Criteria

1. WHEN THE Frontend is viewed on mobile devices, THE Frontend SHALL display a responsive layout that adapts to screen size
2. WHEN THE user interacts with modals on mobile, THE Frontend SHALL ensure modals are properly sized and scrollable
3. WHEN THE user views tables on mobile, THE Frontend SHALL provide a mobile-friendly view (cards or horizontal scroll)
4. WHEN THE user navigates on mobile, THE Frontend SHALL provide touch-friendly buttons and links
5. WHEN THE Frontend displays the navigation menu on mobile, THE Frontend SHALL use a collapsible hamburger menu
