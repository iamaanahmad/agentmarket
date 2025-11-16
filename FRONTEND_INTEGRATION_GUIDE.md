# 🎨 Frontend Integration Guide - Complete Step-by-Step

**Date:** November 9, 2025  
**Status:** Starting Frontend Integration Phase  
**Estimated Time:** 3-4 hours total  
**Goal:** Wire all frontend pages to working APIs

---

## 📋 Overview

Your APIs are all working and tested. Now we need to replace mock data with real API calls in your frontend components. This guide covers every page and component that needs updating.

---

## 🗺️ Frontend Structure

```
src/
├── app/
│   ├── page.tsx                          (Home page)
│   ├── marketplace/
│   │   └── page.tsx                      (Marketplace/Listing page)
│   ├── agents/
│   │   ├── [id]/
│   │   │   └── page.tsx                  (Agent detail page)
│   │   └── register/
│   │       └── page.tsx                  (Register agent page)
│   ├── dashboard/
│   │   └── page.tsx                      (User dashboard)
│   └── security/
│       └── page.tsx                      (Security scan page)
│
└── components/
    ├── marketplace/
    │   ├── agent-grid.tsx                ⚠️ NEEDS REAL API
    │   ├── agent-card.tsx
    │   ├── search-filters.tsx
    │   └── agent-detail.tsx
    ├── home/
    │   ├── featured-agents.tsx           ⚠️ NEEDS REAL API
    │   ├── hero.tsx
    │   └── stats.tsx
    ├── agents/
    │   ├── agent-form.tsx                ⚠️ NEEDS POST /api/agents
    │   └── agent-detail.tsx
    └── dashboard/
        └── requests-list.tsx             ⚠️ NEEDS REAL API
```

---

## 🎯 Priority Tasks

### Priority 1: Agent Listing (Highest Impact - 30 mins)
- [ ] Update `AgentGrid` to fetch from `/api/agents`
- [ ] Update `FeaturedAgents` to fetch from `/api/agents`

### Priority 2: Service Requests (High Impact - 45 mins)
- [ ] Create requests list component
- [ ] Create "Hire Agent" modal/form
- [ ] Wire to `/api/requests` endpoints

### Priority 3: Agent Details (Medium Impact - 30 mins)
- [ ] Create agent detail page
- [ ] Show agent stats
- [ ] Add hire button

### Priority 4: Security Scan (Medium Impact - 20 mins)
- [ ] Wire SecurityGuard scan page
- [ ] Show scan results

### Priority 5: Dashboard (Low Priority - 20 mins)
- [ ] Show user's requests
- [ ] Show user's ratings

---

## 📝 Task-by-Task Guide

---

## ✅ TASK 1: Update AgentGrid Component

**File:** `src/components/marketplace/agent-grid.tsx`  
**What it does:** Displays list of agents with search and filtering  
**Current state:** Uses mock data  
**New state:** Fetch from `/api/agents`

### Changes Needed:

```typescript
// REPLACE THIS (mock data):
useEffect(() => {
  const loadAgents = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 500))
      
      let filteredAgents = [...mockAgents]
      // ... filtering logic
      setAgents(filteredAgents)
      setHasMore(false)
    } catch (err) {
      setError('Failed to load agents. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  loadAgents()
}, [searchQuery, selectedCapability, sortBy])
```

### WITH THIS (real API):

```typescript
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
      
      // Apply client-side sorting (backend doesn't sort yet)
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
```

### Key Changes:
1. **Fetch from `/api/agents` endpoint**
2. **Use real pagination** with page parameter
3. **Transform API response** to match component interface
4. **Apply sorting** on client side
5. **Handle errors properly**

---

## ✅ TASK 2: Update FeaturedAgents Component

**File:** `src/components/home/featured-agents.tsx`  
**What it does:** Shows featured agents on homepage  
**Current state:** Uses mock data  
**New state:** Fetch first 3 agents from `/api/agents`

### Changes Needed:

```typescript
'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AgentCard } from '@/components/marketplace/agent-card'
import { ArrowRight } from 'lucide-react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Skeleton } from '@/components/ui/skeleton'

export function FeaturedAgents() {
  const [agents, setAgents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadFeaturedAgents = async () => {
      try {
        const response = await fetch('/api/agents?page=1&limit=3&sortBy=rating', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        })
        
        if (!response.ok) throw new Error('Failed to fetch featured agents')
        
        const data = await response.json()
        
        // Transform API response
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
        console.error('Error loading featured agents:', err)
        setError('Failed to load featured agents')
      } finally {
        setLoading(false)
      }
    }

    loadFeaturedAgents()
  }, [])

  if (loading) {
    return (
      <section className="py-20">
        <div className="container">
          <div className="text-center mb-12">
            <Badge variant="secondary" className="mb-4">⭐ Top Performing Agents</Badge>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Featured AI Agents</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Discover the most popular and highest-rated AI agents on our platform.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="space-y-4 p-6 border rounded-lg">
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-10 w-full" />
              </div>
            ))}
          </div>
        </div>
      </section>
    )
  }

  if (error || agents.length === 0) {
    return null // Don't show section if error or no agents
  }

  return (
    <section className="py-20">
      <div className="container">
        <div className="text-center mb-12">
          <Badge variant="secondary" className="mb-4">⭐ Top Performing Agents</Badge>
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Featured AI Agents</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Discover the most popular and highest-rated AI agents on our platform.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {agents.map((agent, index) => (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <AgentCard agent={agent} />
            </motion.div>
          ))}
        </div>

        <div className="flex justify-center">
          <Button asChild size="lg" variant="outline">
            <Link href="/marketplace">
              View All Agents
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  )
}
```

### Key Changes:
1. **Fetch from `/api/agents?page=1&limit=3`**
2. **Add loading skeleton**
3. **Transform API response**
4. **Handle error gracefully**

---

## ✅ TASK 3: Create "Hire Agent" Modal/Form

**File:** Create `src/components/marketplace/hire-agent-modal.tsx`

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
      
      // Show success message
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
            Create a service request for {agentName}. Price: {price} SOL
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

---

## ✅ TASK 4: Create Agent Detail Page

**File:** Create `src/app/agents/[id]/page.tsx`

```typescript
'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle, Star, TrendingUp, Zap } from 'lucide-react'
import { HireAgentModal } from '@/components/marketplace/hire-agent-modal'

interface AgentDetails {
  id: number
  agentId: string
  name: string
  description: string
  capabilities: string[]
  pricing: {
    price: number
    currency: string
  }
  endpoint: string
  creatorWallet: string
  active: boolean
  rating: {
    average: number
    count: number
  }
  createdAt: string
}

export default function AgentDetailPage() {
  const params = useParams()
  const agentId = params.id as string
  const [agent, setAgent] = useState<AgentDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadAgent = async () => {
      try {
        // Try to find agent by ID from agents list
        const response = await fetch('/api/agents?limit=100', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        })

        if (!response.ok) throw new Error('Failed to fetch agent')

        const data = await response.json()
        const foundAgent = data.agents.find(
          (a: any) => a.agent_id === agentId || a.id.toString() === agentId
        )

        if (!foundAgent) {
          setError('Agent not found')
          return
        }

        setAgent(foundAgent)
      } catch (err: any) {
        setError(err.message || 'Failed to load agent details')
      } finally {
        setLoading(false)
      }
    }

    loadAgent()
  }, [agentId])

  if (loading) {
    return (
      <div className="container py-8">
        <div className="space-y-6">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="h-24 w-full" />
          <div className="grid md:grid-cols-3 gap-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error || !agent) {
    return (
      <div className="container py-8">
        <div className="flex items-center gap-3 p-4 bg-destructive/10 rounded-lg">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <p>{error || 'Agent not found'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
          <div className="flex-1">
            <h1 className="text-3xl md:text-4xl font-bold mb-3">{agent.name}</h1>
            <p className="text-lg text-muted-foreground mb-4">{agent.description}</p>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="p-3 bg-secondary rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Star className="h-4 w-4 text-yellow-500" />
                  <span className="text-sm text-muted-foreground">Rating</span>
                </div>
                <p className="text-2xl font-bold">
                  {agent.rating.average.toFixed(1)}
                </p>
                <p className="text-xs text-muted-foreground">
                  {agent.rating.count} reviews
                </p>
              </div>

              <div className="p-3 bg-secondary rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="h-4 w-4 text-green-500" />
                  <span className="text-sm text-muted-foreground">Price</span>
                </div>
                <p className="text-2xl font-bold">{agent.pricing.price}</p>
                <p className="text-xs text-muted-foreground">{agent.pricing.currency}</p>
              </div>

              <div className="p-3 bg-secondary rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Zap className="h-4 w-4 text-blue-500" />
                  <span className="text-sm text-muted-foreground">Status</span>
                </div>
                <p className="text-2xl font-bold">{agent.active ? '✓' : '✗'}</p>
                <p className="text-xs text-muted-foreground">
                  {agent.active ? 'Active' : 'Inactive'}
                </p>
              </div>
            </div>

            {/* Capabilities */}
            <div className="mb-6">
              <h3 className="font-semibold mb-3">Capabilities</h3>
              <div className="flex flex-wrap gap-2">
                {agent.capabilities?.map((cap) => (
                  <Badge key={cap}>{cap}</Badge>
                ))}
              </div>
            </div>
          </div>

          {/* Hire Button */}
          <div className="flex-shrink-0">
            <HireAgentModal
              agentId={agent.agentId}
              agentName={agent.name}
              price={agent.pricing.price}
            />
          </div>
        </div>
      </div>

      {/* Additional Info */}
      <div className="border-t pt-8">
        <h2 className="text-2xl font-bold mb-4">About This Agent</h2>
        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h3 className="font-semibold mb-2">Creator</h3>
            <p className="text-muted-foreground font-mono text-sm">
              {agent.creatorWallet}
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Agent ID</h3>
            <p className="text-muted-foreground font-mono text-sm">
              {agent.agentId}
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Endpoint</h3>
            <p className="text-muted-foreground font-mono text-sm">
              {agent.endpoint}
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Created</h3>
            <p className="text-muted-foreground">
              {new Date(agent.createdAt).toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
```

---

## ✅ TASK 5: Create User Dashboard

**File:** Create `src/app/dashboard/page.tsx`

```typescript
'use client'

import { useState, useEffect } from 'react'
import { useWallet } from '@solana/wallet-adapter-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle, Loader2 } from 'lucide-react'

interface ServiceRequest {
  id: number
  requestId: string
  agentId: string
  agentName: string
  amount: string
  status: string
  createdAt: string
  updatedAt: string
}

export default function DashboardPage() {
  const { publicKey } = useWallet()
  const [requests, setRequests] = useState<ServiceRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!publicKey) {
      setError('Please connect your wallet')
      setLoading(false)
      return
    }

    const loadRequests = async () => {
      try {
        const response = await fetch(
          `/api/requests?userWallet=${publicKey.toString()}`,
          {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
          }
        )

        if (!response.ok) throw new Error('Failed to fetch requests')

        const data = await response.json()
        setRequests(data.requests)
      } catch (err: any) {
        setError(err.message || 'Failed to load requests')
      } finally {
        setLoading(false)
      }
    }

    loadRequests()
  }, [publicKey])

  if (!publicKey) {
    return (
      <div className="container py-8">
        <div className="flex items-center gap-3 p-4 bg-yellow-500/10 rounded-lg">
          <AlertCircle className="h-5 w-5 text-yellow-600" />
          <p>Please connect your wallet to view your dashboard</p>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="container py-8">
        <h1 className="text-3xl font-bold mb-8">My Dashboard</h1>
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container py-8">
        <h1 className="text-3xl font-bold mb-8">My Dashboard</h1>
        <div className="flex items-center gap-3 p-4 bg-destructive/10 rounded-lg">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container py-8">
      <h1 className="text-3xl font-bold mb-8">My Dashboard</h1>

      {/* Stats */}
      <div className="grid md:grid-cols-4 gap-4 mb-8">
        <div className="p-4 bg-secondary rounded-lg">
          <p className="text-sm text-muted-foreground">Total Requests</p>
          <p className="text-2xl font-bold">{requests.length}</p>
        </div>
        <div className="p-4 bg-secondary rounded-lg">
          <p className="text-sm text-muted-foreground">Active</p>
          <p className="text-2xl font-bold">
            {requests.filter((r) => r.status === 'pending').length}
          </p>
        </div>
        <div className="p-4 bg-secondary rounded-lg">
          <p className="text-sm text-muted-foreground">Completed</p>
          <p className="text-2xl font-bold">
            {requests.filter((r) => r.status === 'completed').length}
          </p>
        </div>
        <div className="p-4 bg-secondary rounded-lg">
          <p className="text-sm text-muted-foreground">Disputed</p>
          <p className="text-2xl font-bold">
            {requests.filter((r) => r.status === 'disputed').length}
          </p>
        </div>
      </div>

      {/* Requests List */}
      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-secondary">
            <tr>
              <th className="px-6 py-4 text-left text-sm font-semibold">Agent</th>
              <th className="px-6 py-4 text-left text-sm font-semibold">Amount</th>
              <th className="px-6 py-4 text-left text-sm font-semibold">Status</th>
              <th className="px-6 py-4 text-left text-sm font-semibold">Created</th>
              <th className="px-6 py-4 text-left text-sm font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {requests.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-muted-foreground">
                  No service requests yet
                </td>
              </tr>
            ) : (
              requests.map((request) => (
                <tr key={request.id} className="border-t hover:bg-secondary/50">
                  <td className="px-6 py-4">{request.agentName}</td>
                  <td className="px-6 py-4 font-mono">{request.amount} SOL</td>
                  <td className="px-6 py-4">
                    <Badge
                      variant={
                        request.status === 'completed'
                          ? 'default'
                          : request.status === 'disputed'
                          ? 'destructive'
                          : 'secondary'
                      }
                    >
                      {request.status}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    {new Date(request.createdAt).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    <Button variant="outline" size="sm">
                      View Details
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
```

---

## ✅ TASK 6: Update Agent Card Component

**File:** `src/components/marketplace/agent-card.tsx`

Add navigation and hire button:

```typescript
import Link from 'next/link'
import { HireAgentModal } from './hire-agent-modal'

// In the card, add:
<div className="flex gap-2 mt-6">
  <Button asChild variant="outline" className="flex-1">
    <Link href={`/agents/${agent.agentId}`}>
      View Details
    </Link>
  </Button>
  <HireAgentModal
    agentId={agent.agentId}
    agentName={agent.name}
    price={agent.pricing.price}
  />
</div>
```

---

## 📊 API Response Format Reference

### GET /api/agents Response:
```json
{
  "agents": [
    {
      "id": 1,
      "agent_id": "agent-001",
      "name": "SecurityGuard AI",
      "description": "...",
      "capabilities": ["security", "analysis"],
      "pricing": {"price": 0.01, "currency": "SOL"},
      "endpoint": "https://...",
      "creator_wallet": "wallet...",
      "active": true,
      "created_at": "2025-11-08T...",
      "rating": {"average": 4.5, "count": 10}
    }
  ],
  "pagination": {"page": 1, "limit": 10, "total": 4, "pages": 1}
}
```

### POST /api/requests Response:
```json
{
  "success": true,
  "request": {
    "id": 3,
    "requestId": "req-123-abc",
    "agentId": "agent-001",
    "status": "pending",
    "amount": "0.010000",
    "createdAt": "2025-11-09T05:16:03.137Z"
  },
  "message": "Service request created successfully"
}
```

### GET /api/requests Response:
```json
{
  "requests": [
    {
      "id": 1,
      "requestId": "req-001",
      "agentId": "agent-001",
      "agentName": "SecurityGuard AI",
      "userWallet": "wallet...",
      "amount": "0.010000",
      "status": "pending",
      "payload": {...},
      "result": null,
      "createdAt": "2025-11-08T16:33:03.773Z",
      "updatedAt": "2025-11-08T16:33:03.773Z"
    }
  ],
  "pagination": {"page": 1, "limit": 10, "total": 2, "pages": 1}
}
```

---

## 🔧 Helper Hook - useAgents

**File:** Create `src/hooks/useAgents.ts`

```typescript
import { useState, useEffect } from 'react'

interface AgentsResponse {
  agents: any[]
  pagination: {
    page: number
    limit: number
    total: number
    pages: number
  }
}

export function useAgents(page = 1, limit = 10, search = '') {
  const [agents, setAgents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pagination, setPagination] = useState({ page: 1, limit: 10, total: 0, pages: 0 })

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const params = new URLSearchParams()
        params.append('page', page.toString())
        params.append('limit', limit.toString())
        if (search) params.append('search', search)

        const response = await fetch(`/api/agents?${params}`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        })

        if (!response.ok) throw new Error('Failed to fetch agents')

        const data: AgentsResponse = await response.json()
        setAgents(data.agents)
        setPagination(data.pagination)
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchAgents()
  }, [page, limit, search])

  return { agents, loading, error, pagination }
}
```

---

## 🔧 Helper Hook - useRequests

**File:** Create `src/hooks/useRequests.ts`

```typescript
import { useState, useEffect } from 'react'
import { useWallet } from '@solana/wallet-adapter-react'

export function useRequests(agentId?: string) {
  const { publicKey } = useWallet()
  const [requests, setRequests] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!publicKey) return

    const fetchRequests = async () => {
      try {
        const params = new URLSearchParams()
        params.append('userWallet', publicKey.toString())
        if (agentId) params.append('agentId', agentId)

        const response = await fetch(`/api/requests?${params}`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        })

        if (!response.ok) throw new Error('Failed to fetch requests')

        const data = await response.json()
        setRequests(data.requests)
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchRequests()
  }, [publicKey, agentId])

  return { requests, loading, error }
}
```

---

## 📋 Implementation Checklist

### Phase 1: Core Listing (Do First - 30 mins)
- [ ] Update `AgentGrid` to fetch from `/api/agents`
- [ ] Update `FeaturedAgents` to fetch from `/api/agents`
- [ ] Test agents list loading on marketplace page
- [ ] Test featured agents on homepage

### Phase 2: Service Requests (Do Second - 45 mins)
- [ ] Create `HireAgentModal` component
- [ ] Update `AgentCard` to include hire button
- [ ] Create dashboard page with requests list
- [ ] Test creating service request

### Phase 3: Details & Polish (Do Third - 30 mins)
- [ ] Create agent detail page
- [ ] Add navigation links
- [ ] Test navigation between pages
- [ ] Polish UI and error messages

### Phase 4: Security Scan (Optional - 20 mins)
- [ ] Wire security scan page to `/api/security/scan`
- [ ] Show scan results
- [ ] Handle backend unavailable state

---

## ⏱️ Time Breakdown

| Task | Time | Status |
|------|------|--------|
| Update AgentGrid | 15 min | ⏳ |
| Update FeaturedAgents | 15 min | ⏳ |
| Create HireAgentModal | 20 min | ⏳ |
| Create Dashboard | 25 min | ⏳ |
| Create Agent Detail | 20 min | ⏳ |
| Create Helper Hooks | 15 min | ⏳ |
| Testing & Polish | 30 min | ⏳ |
| **TOTAL** | **140 min (2.3 hrs)** | ⏳ |

---

## 🚀 Next Steps

1. **Start with AgentGrid** - Most important, used on marketplace
2. **Update FeaturedAgents** - Shows data on homepage
3. **Create HireAgentModal** - Enables service requests
4. **Create Dashboard** - Shows user's requests
5. **Create Detail Pages** - Nice to have
6. **Test Everything** - Verify end-to-end flows

---

## 💡 Pro Tips

1. **Use React DevTools** to inspect API responses
2. **Test with real wallet address** when creating requests
3. **Check console for errors** - will show API issues
4. **Start with localhost testing** before deployment
5. **Keep error messages user-friendly**

---

## ❓ Common Issues & Fixes

### "Failed to fetch agents"
- Check if API is running: `npm run dev`
- Check browser console for CORS errors
- Verify API endpoints are correct

### "Please connect your wallet"
- Ensure wallet adapter is configured in layout.tsx
- Check if wallet provider is wrapping components

### Empty agent list
- Check if database has data: Run seed script
- Check API response in browser network tab
- Verify search query parameters

---

**Status: Ready to start implementation! Follow checklist above. 🚀**

