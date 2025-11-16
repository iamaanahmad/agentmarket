# 🎯 Frontend Pages - Complete Implementation Guide

**Purpose:** Step-by-step instructions for updating each page/component  
**Estimated Total Time:** 2-3 hours  
**Priority Level:** CRITICAL - Blocking path to 1st prize

---

## 📑 Table of Contents

1. [Marketplace Page](#1-marketplace-page)
2. [Home Page](#2-home-page)
3. [Agent Detail Page](#3-agent-detail-page)
4. [Register Agent Page](#4-register-agent-page)
5. [Dashboard Page](#5-dashboard-page)
6. [Security Scan Page](#6-security-scan-page)

---

## 1️⃣ MARKETPLACE PAGE

**File:** `src/app/marketplace/page.tsx`  
**Current State:** Already has AgentGrid component (mock data)  
**What to do:** No changes needed - AgentGrid will be updated separately  
**Time:** 0 minutes (already complete)  
**Priority:** ⏳ WAIT for AgentGrid update

**What happens:**
- User sees list of agents with search/filter
- User can hire agents directly from cards
- User can click "View Details" to see agent page

---

## 2️⃣ HOME PAGE - FEATURED AGENTS

**File:** `src/components/home/featured-agents.tsx`  
**Current State:** Uses mock data  
**What to do:** Replace with real API data  
**Time:** 15 minutes  
**Priority:** 🔴 HIGH - Users see this first

### Step-by-Step Implementation:

**Step 1: Add imports**
```typescript
import { useState, useEffect } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
```

**Step 2: Add state**
```typescript
const [agents, setAgents] = useState<any[]>([])
const [loading, setLoading] = useState(true)
const [error, setError] = useState<string | null>(null)
```

**Step 3: Add useEffect to fetch data**
```typescript
useEffect(() => {
  const loadFeaturedAgents = async () => {
    try {
      // Fetch top 3 agents
      const response = await fetch('/api/agents?page=1&limit=3', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      })
      
      if (!response.ok) throw new Error('Failed to fetch')
      
      const data = await response.json()
      
      // Transform API response to match component format
      const transformed = data.agents.map((agent: any) => ({
        id: agent.id.toString(),
        name: agent.name,
        description: agent.description,
        capabilities: agent.capabilities || [],
        pricing: agent.pricing || { type: 'per_query', price: 0.01, currency: 'SOL' },
        rating: agent.rating?.average || 0,
        totalServices: agent.rating?.count || 0,
        creator: agent.creator_wallet || 'Unknown',
        creatorAddress: agent.creator_wallet,
        responseTime: '< 2s',
        isActive: agent.active ?? true,
        nftMint: agent.agent_id,
      }))
      
      setAgents(transformed)
    } catch (err) {
      console.error(err)
      setError('Failed to load agents')
    } finally {
      setLoading(false)
    }
  }

  loadFeaturedAgents()
}, [])
```

**Step 4: Show loading skeleton**
```typescript
if (loading) {
  return (
    <section className="py-20">
      <div className="container">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-64" />
          ))}
        </div>
      </div>
    </section>
  )
}
```

**Step 5: Handle error**
```typescript
if (error || agents.length === 0) {
  return null // Don't show section if error
}
```

**Step 6: Update render**
```typescript
// Remove hardcoded featuredAgents array
// Use agents state instead:
{agents.map((agent, index) => (
  <motion.div key={agent.id} ...>
    <AgentCard agent={agent} />
  </motion.div>
))}
```

### Testing:
1. Go to homepage
2. Scroll to "Featured Agents" section
3. Should show real agents from database
4. Click "Hire Agent" - should work

---

## 3️⃣ AGENT GRID COMPONENT

**File:** `src/components/marketplace/agent-grid.tsx`  
**Current State:** Uses mock data  
**What to do:** Replace with real API data  
**Time:** 20 minutes  
**Priority:** 🔴 CRITICAL - Core of marketplace

### Complete Replacement Code:

```typescript
'use client'

import { useState, useEffect } from 'react'
import { AgentCard } from './agent-card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle, RefreshCw } from 'lucide-react'

interface Agent {
  id: string
  name: string
  description: string
  capabilities: string[]
  pricing: {
    type: 'per_query' | 'subscription' | 'custom'
    price: number
    currency: 'SOL'
  }
  rating: number
  totalServices: number
  creator: string
  creatorAddress: string
  responseTime: string
  isActive: boolean
  nftMint: string
}

interface AgentGridProps {
  searchQuery: string
  selectedCapability: string | null
  sortBy: string
}

export function AgentGrid({ searchQuery, selectedCapability, sortBy }: AgentGridProps) {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)

  useEffect(() => {
    const loadAgents = async () => {
      setLoading(true)
      setError(null)
      
      try {
        // Build query parameters
        const params = new URLSearchParams()
        params.append('page', page.toString())
        params.append('limit', '12')
        if (searchQuery) params.append('search', searchQuery)
        
        // Call real API
        const response = await fetch(`/api/agents?${params}`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        })
        
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`)
        }
        
        const data = await response.json()
        
        // Transform API response to match component interface
        const transformedAgents = data.agents.map((agent: any) => ({
          id: agent.id.toString(),
          name: agent.name,
          description: agent.description,
          capabilities: agent.capabilities || [],
          pricing: agent.pricing || { type: 'per_query', price: 0.01, currency: 'SOL' },
          rating: agent.rating?.average || 0,
          totalServices: agent.rating?.count || 0,
          creator: agent.creator_wallet || 'Unknown',
          creatorAddress: agent.creator_wallet,
          responseTime: '< 2s',
          isActive: agent.active ?? true,
          nftMint: agent.agent_id,
        }))
        
        // Apply client-side sorting
        transformedAgents.sort((a, b) => {
          switch (sortBy) {
            case 'rating': return b.rating - a.rating
            case 'services': return b.totalServices - a.totalServices
            case 'price_low': return a.pricing.price - b.pricing.price
            case 'price_high': return b.pricing.price - a.pricing.price
            default: return b.rating - a.rating
          }
        })
        
        setAgents(transformedAgents)
        setHasMore(data.pagination.page < data.pagination.pages)
      } catch (err) {
        console.error('Failed to load agents:', err)
        setError('Failed to load agents. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    loadAgents()
  }, [searchQuery, selectedCapability, sortBy, page])

  if (loading && agents.length === 0) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-64" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <AlertCircle className="h-12 w-12 text-muted-foreground" />
        <h3 className="text-lg font-semibold">Failed to load agents</h3>
        <p className="text-muted-foreground">{error}</p>
        <Button onClick={() => window.location.reload()} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
      </div>
    )
  }

  if (agents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <h3 className="text-lg font-semibold">No agents found</h3>
        <p className="text-muted-foreground">Try adjusting your search or filters</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground">
        Showing {agents.length} agent{agents.length !== 1 ? 's' : ''}
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>

      {hasMore && (
        <div className="flex justify-center pt-6">
          <Button onClick={() => setPage(p => p + 1)} disabled={loading}>
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Loading...
              </>
            ) : (
              'Load More Agents'
            )}
          </Button>
        </div>
      )}
    </div>
  )
}
```

### Testing:
1. Go to `/marketplace`
2. Should show real agents
3. Search should work
4. Filtering should work
5. Load more should work

---

## 4️⃣ HIRE AGENT MODAL

**File:** Create `src/components/marketplace/hire-agent-modal.tsx`  
**Current State:** Doesn't exist yet  
**What to do:** Create new component  
**Time:** 20 minutes  
**Priority:** 🔴 CRITICAL - Enables hiring

### Create the file:

```typescript
'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { AlertCircle, Loader2 } from 'lucide-react'
import { useWallet } from '@solana/wallet-adapter-react'

interface HireAgentModalProps {
  agentId: string
  agentName: string
  price: number
  onSuccess?: () => void
}

export function HireAgentModal({
  agentId,
  agentName,
  price,
  onSuccess,
}: HireAgentModalProps) {
  const { publicKey } = useWallet()
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [description, setDescription] = useState('')

  const handleHire = async () => {
    if (!publicKey) {
      setError('Please connect your wallet first')
      return
    }

    if (!description.trim()) {
      setError('Please describe what you need')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agentId,
          userWallet: publicKey.toString(),
          amount: price,
          requestData: {
            description,
            createdAt: new Date().toISOString(),
          },
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to create request')
      }

      const data = await response.json()
      setOpen(false)
      setDescription('')
      onSuccess?.()
      
      alert(`✅ Service request created!\nRequest ID: ${data.request.requestId}`)
    } catch (err: any) {
      setError(err.message || 'Failed to hire agent')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Hire Agent</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Hire {agentName}</DialogTitle>
          <DialogDescription>
            Service price: {price} SOL
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {error && (
            <div className="flex items-start gap-3 p-3 bg-destructive/10 rounded-lg">
              <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          <div>
            <label className="text-sm font-medium">
              Describe what you need
            </label>
            <Textarea
              placeholder="Describe the task or service you need..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-2"
              rows={4}
            />
          </div>

          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button onClick={handleHire} disabled={loading || !description}>
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating Request...
                </>
              ) : (
                `Hire for ${price} SOL`
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

### Add to AgentCard:

Update `src/components/marketplace/agent-card.tsx` to import and use:

```typescript
import { HireAgentModal } from './hire-agent-modal'

// In the card's button section, add:
<HireAgentModal
  agentId={agent.nftMint}
  agentName={agent.name}
  price={agent.pricing.price}
  onSuccess={() => {
    // Optionally refresh data or show message
  }}
/>
```

---

## 5️⃣ AGENT DETAIL PAGE

**File:** Create `src/app/agents/[id]/page.tsx`  
**Current State:** Doesn't exist yet  
**What to do:** Create new page  
**Time:** 20 minutes  
**Priority:** 🟡 MEDIUM - Nice detail view

### Create the file with full implementation (see FRONTEND_INTEGRATION_GUIDE.md for complete code)

---

## 6️⃣ DASHBOARD PAGE

**File:** Create `src/app/dashboard/page.tsx`  
**Current State:** Doesn't exist yet  
**What to do:** Create new page  
**Time:** 25 minutes  
**Priority:** 🟡 MEDIUM - Shows user requests

### Create the file with full implementation (see FRONTEND_INTEGRATION_GUIDE.md for complete code)

### Key Features:
- Show all user's service requests
- Filter by status
- Show request details
- Action buttons for each request

---

## 7️⃣ REGISTER AGENT PAGE

**File:** `src/app/agents/register/page.tsx`  
**Current State:** Exists but uses mock  
**What to do:** Update to call POST /api/agents  
**Time:** 15 minutes  
**Priority:** 🟡 MEDIUM - For agent creators

### Update to use POST /api/agents:

```typescript
const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault()
  setLoading(true)
  setError(null)

  try {
    const response = await fetch('/api/agents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: formData.name,
        creatorWallet: publicKey?.toString(),
        description: formData.description,
        capabilities: formData.capabilities,
        pricing: {
          price: parseFloat(formData.price),
          currency: 'SOL',
        },
        endpoint: formData.endpoint,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || 'Failed to register agent')
    }

    const data = await response.json()
    alert(`✅ Agent registered!\nAgent ID: ${data.agent.agentId}`)
    // Redirect to agent page
    router.push(`/agents/${data.agent.agentId}`)
  } catch (err: any) {
    setError(err.message)
  } finally {
    setLoading(false)
  }
}
```

---

## 🧪 Testing Checklist

### Test Marketplace:
- [ ] Visit `/marketplace`
- [ ] See real agents loading
- [ ] Search works
- [ ] Filters work
- [ ] Can click "Hire Agent"
- [ ] Request creation succeeds

### Test Homepage:
- [ ] Visit `/`
- [ ] Featured agents load
- [ ] Can click "Hire Agent"
- [ ] Featured agents are real

### Test Dashboard:
- [ ] Connect wallet
- [ ] Visit `/dashboard`
- [ ] See user's requests
- [ ] Can view request details

### Test Agent Detail:
- [ ] Click "View Details" on any agent
- [ ] See agent information
- [ ] Can hire from detail page

---

## 🎯 Implementation Order

1. **AgentGrid** (20 min) - Most critical
2. **FeaturedAgents** (15 min) - Homepage
3. **HireAgentModal** (20 min) - Core functionality
4. **Dashboard** (25 min) - User experience
5. **Agent Detail** (20 min) - Polish
6. **Register Agent** (15 min) - For creators

**Total Time: ~115 minutes (1.9 hours)**

---

## ✅ When Complete

- ✅ All pages showing real data
- ✅ Users can browse agents
- ✅ Users can hire agents
- ✅ Users can track requests
- ✅ End-to-end flow works
- ✅ Ready for smart contract integration

---

**Next: Pick any component above and start implementing! Start with AgentGrid for maximum impact.** 🚀

