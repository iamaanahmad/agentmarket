# Frontend Integration Design

## Overview

This design document outlines the architecture and implementation strategy for integrating the AgentMarket frontend with the backend APIs. The integration transforms the current mock-data-driven interface into a fully functional application that communicates with real database-backed endpoints.

The design follows a component-based architecture using Next.js 14 App Router, React hooks for state management, and a clear separation between presentation and data-fetching logic.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (Client)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  React Components (UI Layer)                           │ │
│  │  - AgentGrid, FeaturedAgents, Dashboard, etc.         │ │
│  └────────────────┬───────────────────────────────────────┘ │
│                   │                                           │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  Custom Hooks (Data Layer)                            │ │
│  │  - useAgents, useRequests, useAgentDetail            │ │
│  └────────────────┬───────────────────────────────────────┘ │
│                   │                                           │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  API Client (Fetch Layer)                             │ │
│  │  - fetch() calls to /api/* endpoints                  │ │
│  └────────────────┬───────────────────────────────────────┘ │
└───────────────────┼───────────────────────────────────────────┘
                    │ HTTP/HTTPS
┌───────────────────▼───────────────────────────────────────────┐
│                  Next.js Server (API Routes)                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  API Route Handlers                                    │  │
│  │  - /api/agents, /api/requests, /api/security/scan     │  │
│  └────────────────┬───────────────────────────────────────┘  │
│                   │                                            │
│  ┌────────────────▼───────────────────────────────────────┐  │
│  │  Database Layer (PostgreSQL)                           │  │
│  │  - agents, service_requests, ratings tables            │  │
│  └────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### Component Hierarchy

```
App Layout (src/app/layout.tsx)
├── Providers (Wallet, Theme)
├── Navbar
└── Page Content
    ├── Home Page (/)
    │   ├── Hero
    │   ├── FeaturedAgents ← API Integration
    │   ├── SecurityGuardSection
    │   ├── HowItWorks
    │   ├── Stats
    │   └── RecentActivity
    │
    ├── Marketplace Page (/marketplace)
    │   ├── SearchFilters
    │   └── AgentGrid ← API Integration
    │       └── AgentCard[] ← API Integration
    │           └── HireAgentModal ← API Integration
    │
    ├── Agent Detail Page (/agents/[id])
    │   ├── Agent Header
    │   ├── Agent Stats
    │   ├── Capabilities
    │   └── HireAgentModal ← API Integration
    │
    ├── Dashboard Page (/dashboard)
    │   ├── Stats Summary ← API Integration
    │   └── Requests Table ← API Integration
    │
    └── Register Agent Page (/agents/register)
        └── Agent Form ← API Integration
```

## Components and Interfaces

### 1. AgentGrid Component

**Purpose:** Display a paginated, searchable, filterable list of AI agents

**Props Interface:**
```typescript
interface AgentGridProps {
  searchQuery: string
  selectedCapability: string | null
  sortBy: 'rating' | 'services' | 'price_low' | 'price_high'
}
```

**State Management:**
```typescript
interface AgentGridState {
  agents: Agent[]
  loading: boolean
  error: string | null
  page: number
  hasMore: boolean
}
```

**Data Flow:**
1. Component receives search/filter props from parent
2. useEffect triggers on prop changes
3. Builds URLSearchParams with filters
4. Fetches from `/api/agents?page=X&limit=12&search=Y`
5. Transforms API response to component format
6. Applies client-side sorting
7. Updates state and re-renders

**API Integration:**
- Endpoint: `GET /api/agents`
- Query params: `page`, `limit`, `search`
- Response transformation: snake_case → camelCase
- Error handling: Display user-friendly message with retry

### 2. FeaturedAgents Component

**Purpose:** Display top 3 highest-rated agents on homepage

**State Management:**
```typescript
interface FeaturedAgentsState {
  agents: Agent[]
  loading: boolean
  error: string | null
}
```

**Data Flow:**
1. Component mounts
2. Fetches from `/api/agents?page=1&limit=3`
3. Transforms response
4. Displays in grid layout
5. Shows loading skeletons during fetch
6. Hides section if error or no agents

**API Integration:**
- Endpoint: `GET /api/agents`
- Query params: `page=1`, `limit=3`
- No search/filter needed
- Graceful degradation on error

### 3. HireAgentModal Component

**Purpose:** Allow users to create service requests for agents

**Props Interface:**
```typescript
interface HireAgentModalProps {
  agentId: string
  agentName: string
  price: number
  onSuccess?: () => void
}
```

**State Management:**
```typescript
interface HireAgentModalState {
  open: boolean
  loading: boolean
  error: string | null
  description: string
}
```

**Data Flow:**
1. User clicks "Hire Agent" button
2. Modal opens with form
3. User enters service description
4. User submits form
5. Validates wallet connection
6. POSTs to `/api/requests`
7. Shows success message or error
8. Closes modal on success
9. Calls onSuccess callback

**API Integration:**
- Endpoint: `POST /api/requests`
- Request body:
  ```json
  {
    "agentId": "agent-001",
    "userWallet": "wallet-address",
    "amount": 0.01,
    "requestData": {
      "description": "User's request description",
      "createdAt": "2025-11-09T..."
    }
  }
  ```
- Wallet validation before submission
- Error display without closing modal

### 4. Dashboard Page

**Purpose:** Display user's service requests and activity

**State Management:**
```typescript
interface DashboardState {
  requests: ServiceRequest[]
  loading: boolean
  error: string | null
}

interface ServiceRequest {
  id: number
  requestId: string
  agentId: string
  agentName: string
  amount: string
  status: 'pending' | 'completed' | 'disputed'
  createdAt: string
  updatedAt: string
}
```

**Data Flow:**
1. Component checks wallet connection
2. Fetches from `/api/requests?userWallet=X`
3. Displays summary statistics
4. Renders requests table
5. Shows loading skeletons during fetch
6. Prompts wallet connection if needed

**API Integration:**
- Endpoint: `GET /api/requests`
- Query params: `userWallet`
- Requires wallet connection
- Filters requests by user

### 5. Agent Detail Page

**Purpose:** Display comprehensive information about a specific agent

**State Management:**
```typescript
interface AgentDetailState {
  agent: AgentDetails | null
  loading: boolean
  error: string | null
}

interface AgentDetails {
  id: number
  agentId: string
  name: string
  description: string
  capabilities: string[]
  pricing: { price: number; currency: string }
  endpoint: string
  creatorWallet: string
  active: boolean
  rating: { average: number; count: number }
  createdAt: string
}
```

**Data Flow:**
1. Component receives agent ID from URL params
2. Fetches all agents from `/api/agents?limit=100`
3. Finds matching agent by ID
4. Displays agent information
5. Shows 404 if not found
6. Includes HireAgentModal

**API Integration:**
- Endpoint: `GET /api/agents`
- Query params: `limit=100`
- Client-side filtering by ID
- Future: Dedicated `/api/agents/[id]` endpoint

### 6. Register Agent Page

**Purpose:** Allow creators to register new AI agents

**State Management:**
```typescript
interface RegisterAgentState {
  loading: boolean
  error: string | null
  formData: {
    name: string
    description: string
    capabilities: string[]
    price: string
    endpoint: string
  }
}
```

**Data Flow:**
1. User fills out registration form
2. Validates required fields
3. Checks wallet connection
4. POSTs to `/api/agents`
5. Redirects to agent detail page on success
6. Shows error message on failure

**API Integration:**
- Endpoint: `POST /api/agents`
- Request body:
  ```json
  {
    "name": "Agent Name",
    "creatorWallet": "wallet-address",
    "description": "Agent description",
    "capabilities": ["security", "analysis"],
    "pricing": { "price": 0.01, "currency": "SOL" },
    "endpoint": "https://..."
  }
  ```
- Wallet validation required
- Form validation before submission

## Data Models

### Agent Interface (Frontend)

```typescript
interface Agent {
  id: string                    // Database ID as string
  name: string                  // Agent name
  description: string           // Agent description
  capabilities: string[]        // Array of capability tags
  pricing: {
    type: 'per_query' | 'subscription' | 'custom'
    price: number               // Price in SOL
    currency: 'SOL'
  }
  rating: number                // Average rating (0-5)
  totalServices: number         // Number of completed services
  creator: string               // Creator display name
  creatorAddress: string        // Creator wallet address
  responseTime: string          // Display string (e.g., "< 2s")
  isActive: boolean             // Agent availability status
  nftMint: string              // Solana NFT mint address (agent_id)
}
```

### API Response Transformation

**Backend Response (snake_case):**
```json
{
  "id": 1,
  "agent_id": "agent-001",
  "name": "SecurityGuard AI",
  "description": "...",
  "capabilities": ["security"],
  "pricing": {"price": 0.01, "currency": "SOL"},
  "endpoint": "https://...",
  "creator_wallet": "wallet...",
  "active": true,
  "created_at": "2025-11-08T...",
  "rating": {"average": 4.5, "count": 10}
}
```

**Frontend Format (camelCase):**
```typescript
{
  id: "1",
  name: "SecurityGuard AI",
  description: "...",
  capabilities: ["security"],
  pricing: { type: "per_query", price: 0.01, currency: "SOL" },
  rating: 4.5,
  totalServices: 10,
  creator: "wallet...",
  creatorAddress: "wallet...",
  responseTime: "< 2s",
  isActive: true,
  nftMint: "agent-001"
}
```

**Transformation Function:**
```typescript
function transformAgentResponse(apiAgent: any): Agent {
  return {
    id: apiAgent.id.toString(),
    name: apiAgent.name,
    description: apiAgent.description,
    capabilities: apiAgent.capabilities || [],
    pricing: apiAgent.pricing || { 
      type: 'per_query', 
      price: 0.01, 
      currency: 'SOL' 
    },
    rating: apiAgent.rating?.average || 0,
    totalServices: apiAgent.rating?.count || 0,
    creator: apiAgent.creator_wallet || 'Unknown',
    creatorAddress: apiAgent.creator_wallet,
    responseTime: '< 2s',
    isActive: apiAgent.active ?? true,
    nftMint: apiAgent.agent_id,
  }
}
```

## Error Handling

### Error Handling Strategy

**1. Network Errors:**
- Display user-friendly message
- Provide retry mechanism
- Log error to console for debugging

**2. API Errors:**
- Parse error response from backend
- Display specific error message
- Keep form data intact for retry

**3. Validation Errors:**
- Client-side validation before API call
- Display inline error messages
- Prevent submission until valid

**4. Wallet Errors:**
- Check wallet connection before operations
- Prompt user to connect wallet
- Clear error message about requirement

### Error Display Patterns

**Loading State:**
```typescript
if (loading) {
  return <Skeleton />
}
```

**Error State:**
```typescript
if (error) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertDescription>{error}</AlertDescription>
      <Button onClick={retry}>Try Again</Button>
    </Alert>
  )
}
```

**Empty State:**
```typescript
if (data.length === 0) {
  return (
    <EmptyState
      title="No agents found"
      description="Try adjusting your search"
    />
  )
}
```

## Testing Strategy

### Component Testing

**1. AgentGrid Component:**
- Test loading state displays skeletons
- Test successful data fetch and display
- Test error state displays error message
- Test search query updates trigger refetch
- Test pagination works correctly
- Test sorting applies correctly

**2. HireAgentModal Component:**
- Test modal opens and closes
- Test wallet validation
- Test form validation
- Test successful request creation
- Test error handling
- Test success callback

**3. Dashboard Page:**
- Test wallet connection check
- Test requests fetch and display
- Test statistics calculation
- Test empty state
- Test loading state

### Integration Testing

**End-to-End Flows:**
1. Browse marketplace → View agent → Hire agent → View in dashboard
2. Register agent → View in marketplace → Hire own agent
3. Search agents → Filter results → View details
4. Connect wallet → Create request → View request status

### Manual Testing Checklist

- [ ] Homepage loads with featured agents
- [ ] Marketplace displays all agents
- [ ] Search filters agents correctly
- [ ] Agent detail page shows correct information
- [ ] Hire agent modal creates request
- [ ] Dashboard shows user's requests
- [ ] Register agent creates new agent
- [ ] Error messages display correctly
- [ ] Loading states show appropriately
- [ ] Mobile responsive layout works

## Performance Considerations

### Optimization Strategies

**1. Data Fetching:**
- Implement pagination (12 agents per page)
- Use appropriate page limits
- Cache API responses where possible
- Debounce search input

**2. Rendering:**
- Use React.memo for expensive components
- Implement virtual scrolling for long lists
- Lazy load images
- Code split routes

**3. State Management:**
- Minimize re-renders with proper dependencies
- Use local state for UI-only state
- Lift state only when necessary

**4. API Calls:**
- Avoid redundant API calls
- Implement request deduplication
- Use loading states to prevent double-submission

### Performance Targets

- Initial page load: < 2 seconds
- API response time: < 500ms
- Search/filter update: < 1 second
- Modal open/close: < 100ms
- Smooth scrolling: 60 FPS

## Mobile Responsiveness

### Responsive Design Strategy

**Breakpoints:**
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

**Component Adaptations:**

**AgentGrid:**
- Mobile: 1 column
- Tablet: 2 columns
- Desktop: 3 columns

**Dashboard Table:**
- Mobile: Card layout
- Tablet: Horizontal scroll
- Desktop: Full table

**Modals:**
- Mobile: Full screen
- Tablet: 80% width
- Desktop: Fixed width (600px)

**Navigation:**
- Mobile: Hamburger menu
- Desktop: Full navigation bar

## Security Considerations

### Client-Side Security

**1. Wallet Integration:**
- Never expose private keys
- Validate wallet connection before operations
- Use Solana wallet adapter best practices

**2. Input Validation:**
- Validate all user inputs client-side
- Sanitize data before display
- Prevent XSS attacks

**3. API Communication:**
- Use HTTPS only
- Include CSRF tokens where needed
- Validate API responses

**4. Error Messages:**
- Don't expose sensitive information
- Use generic error messages for security issues
- Log detailed errors server-side only

## Deployment Considerations

### Build Configuration

**Environment Variables:**
```env
NEXT_PUBLIC_API_URL=https://api.agentmarket.com
NEXT_PUBLIC_SOLANA_NETWORK=devnet
NEXT_PUBLIC_RPC_ENDPOINT=https://...
```

**Build Optimization:**
- Enable production mode
- Minify JavaScript
- Optimize images
- Generate static pages where possible

### Monitoring

**Client-Side Monitoring:**
- Track API errors
- Monitor page load times
- Track user interactions
- Log wallet connection issues

**Metrics to Track:**
- API success/failure rates
- Average response times
- User engagement metrics
- Error rates by component

## Implementation Phases

### Phase 1: Core Listing (Priority 1)
**Time: 30 minutes**
- Update AgentGrid component
- Update FeaturedAgents component
- Test agent listing on marketplace and homepage

### Phase 2: Service Requests (Priority 2)
**Time: 45 minutes**
- Create HireAgentModal component
- Update AgentCard to include hire button
- Create Dashboard page
- Test request creation flow

### Phase 3: Detail Views (Priority 3)
**Time: 30 minutes**
- Create Agent Detail page
- Add navigation links
- Test navigation between pages

### Phase 4: Agent Registration (Priority 4)
**Time: 15 minutes**
- Update Register Agent page
- Wire to POST /api/agents
- Test agent creation

### Phase 5: Polish & Testing (Priority 5)
**Time: 30 minutes**
- Add error boundaries
- Improve loading states
- Test mobile responsiveness
- Fix any bugs

**Total Estimated Time: 2.5 hours**

## Future Enhancements

### Short-Term (Post-MVP)
- Implement real-time updates with WebSockets
- Add request status notifications
- Implement agent search autocomplete
- Add agent comparison feature

### Long-Term
- Implement caching layer (React Query)
- Add offline support
- Implement optimistic UI updates
- Add advanced filtering options
- Implement agent analytics dashboard

## Dependencies

### Required Packages
- `@solana/wallet-adapter-react` - Wallet integration
- `@solana/wallet-adapter-wallets` - Wallet providers
- `lucide-react` - Icons
- `framer-motion` - Animations
- `next` - Framework
- `react` - UI library

### UI Components (shadcn/ui)
- Button
- Dialog
- Input
- Textarea
- Badge
- Skeleton
- Alert
- Card

## API Endpoints Reference

### GET /api/agents
**Purpose:** Fetch list of agents
**Query Params:**
- `page` (number): Page number (default: 1)
- `limit` (number): Items per page (default: 10)
- `search` (string): Search query (optional)

**Response:**
```json
{
  "agents": [...],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 4,
    "pages": 1
  }
}
```

### POST /api/agents
**Purpose:** Register new agent
**Request Body:**
```json
{
  "name": "string",
  "creatorWallet": "string",
  "description": "string",
  "capabilities": ["string"],
  "pricing": { "price": number, "currency": "SOL" },
  "endpoint": "string"
}
```

### GET /api/requests
**Purpose:** Fetch service requests
**Query Params:**
- `userWallet` (string): Filter by user wallet
- `agentId` (string): Filter by agent ID
- `page` (number): Page number
- `limit` (number): Items per page

### POST /api/requests
**Purpose:** Create service request
**Request Body:**
```json
{
  "agentId": "string",
  "userWallet": "string",
  "amount": number,
  "requestData": { "description": "string" }
}
```

## Conclusion

This design provides a comprehensive blueprint for integrating the AgentMarket frontend with backend APIs. The architecture emphasizes:

- Clear separation of concerns
- Reusable components and hooks
- Robust error handling
- Performance optimization
- Mobile responsiveness
- Security best practices

By following this design, the implementation will result in a production-ready, user-friendly interface that seamlessly connects users with AI agents through a decentralized marketplace.
