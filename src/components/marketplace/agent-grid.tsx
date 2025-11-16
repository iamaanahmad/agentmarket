'use client'

import { useState, useEffect } from 'react'
import { AgentCard } from './agent-card'
import { Button } from '@/components/ui/button'
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
  avatar?: string
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

  // Fetch agents from API
  useEffect(() => {
    const loadAgents = async () => {
      setLoading(true)
      setError(null)
      
      try {
        // Build query parameters
        const params = new URLSearchParams({
          page: page.toString(),
          limit: '20',
        })
        
        if (searchQuery) {
          params.append('search', searchQuery)
        }
        
        // Fetch from API
        const response = await fetch(`/api/agents?${params.toString()}`)
        
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`)
        }
        
        const data = await response.json()
        
        // Transform API response to component format
        const transformedAgents: Agent[] = data.agents.map((agent: any) => ({
          id: agent.id.toString(),
          name: agent.name,
          description: agent.description,
          capabilities: agent.capabilities || [],
          pricing: agent.pricing || { type: 'per_query', price: 0, currency: 'SOL' },
          rating: agent.rating?.average || 0,
          totalServices: agent.rating?.count || 0,
          creator: agent.creatorWallet?.substring(0, 8) + '...' || 'Unknown',
          creatorAddress: agent.creatorWallet || '',
          responseTime: '< 30s', // Default value
          isActive: true,
          nftMint: agent.agentId || '',
          avatar: undefined,
        }))
        
        // Apply capability filter (client-side)
        let filteredAgents = transformedAgents
        if (selectedCapability) {
          filteredAgents = transformedAgents.filter(agent =>
            agent.capabilities.some(cap => 
              cap.toLowerCase().includes(selectedCapability.toLowerCase())
            )
          )
        }
        
        // Apply sorting (client-side)
        filteredAgents.sort((a, b) => {
          switch (sortBy) {
            case 'rating':
              return b.rating - a.rating
            case 'services':
              return b.totalServices - a.totalServices
            case 'price_low':
              return a.pricing.price - b.pricing.price
            case 'price_high':
              return b.pricing.price - a.pricing.price
            case 'newest':
              return b.id.localeCompare(a.id)
            default:
              return b.rating - a.rating
          }
        })
        
        // Handle pagination
        if (page === 1) {
          setAgents(filteredAgents)
        } else {
          setAgents(prev => [...prev, ...filteredAgents])
        }
        
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

  const handleRetry = () => {
    setPage(1)
    setAgents([])
    setError(null)
  }

  if (loading && agents.length === 0) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="space-y-4 p-6 border rounded-lg">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="h-5 w-32 bg-muted animate-pulse rounded" />
                <div className="h-4 w-24 bg-muted animate-pulse rounded" />
              </div>
              <div className="h-6 w-16 bg-muted animate-pulse rounded" />
            </div>
            <div className="h-16 w-full bg-muted animate-pulse rounded" />
            <div className="flex items-center justify-between">
              <div className="h-4 w-20 bg-muted animate-pulse rounded" />
              <div className="h-4 w-16 bg-muted animate-pulse rounded" />
            </div>
            <div className="h-10 w-full bg-muted animate-pulse rounded" />
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <AlertCircle className="h-12 w-12 text-muted-foreground" />
        <div className="text-center">
          <h3 className="text-lg font-semibold">Failed to load agents</h3>
          <p className="text-muted-foreground">{error}</p>
        </div>
        <Button onClick={handleRetry} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
      </div>
    )
  }

  if (agents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <div className="text-center">
          <h3 className="text-lg font-semibold">No agents found</h3>
          <p className="text-muted-foreground">
            Try adjusting your search or filters to find more agents.
          </p>
        </div>
        <Button onClick={() => window.location.reload()} variant="outline">
          Clear Filters
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Results Count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Showing {agents.length} agent{agents.length !== 1 ? 's' : ''}
        </p>
        {loading && (
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Loading...</span>
          </div>
        )}
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>

      {/* Load More */}
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