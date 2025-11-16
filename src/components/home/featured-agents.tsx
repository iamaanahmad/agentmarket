'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AgentCard } from '@/components/marketplace/agent-card'
import { ArrowRight } from 'lucide-react'
import Link from 'next/link'
import { motion } from 'framer-motion'

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

export function FeaturedAgents() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadFeaturedAgents = async () => {
      try {
        const response = await fetch('/api/agents?page=1&limit=3')
        
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
          responseTime: '< 30s',
          isActive: true,
          nftMint: agent.agentId || '',
        }))
        
        setAgents(transformedAgents)
      } catch (err) {
        console.error('Failed to load featured agents:', err)
        setError('Failed to load agents')
      } finally {
        setLoading(false)
      }
    }

    loadFeaturedAgents()
  }, [])

  // Hide section if error or no agents
  if (error || (!loading && agents.length === 0)) {
    return null
  }
  return (
    <section className="py-20">
      <div className="container">
        {/* Header */}
        <div className="text-center mb-12">
          <Badge variant="secondary" className="mb-4">
            ⭐ Top Performing Agents
          </Badge>
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Featured AI Agents
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Discover the most popular and highest-rated AI agents on our platform. 
            From security analysis to creative design, find the perfect agent for your needs.
          </p>
        </div>

        {/* Featured Agents Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {loading ? (
            // Loading skeletons
            Array.from({ length: 3 }).map((_, i) => (
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
            ))
          ) : (
            agents.map((agent: Agent, index: number) => (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <AgentCard agent={agent} />
              </motion.div>
            ))
          )}
        </div>

        {/* CTA Section */}
        <div className="text-center">
          <div className="inline-flex flex-col sm:flex-row gap-4">
            <Button asChild size="lg">
              <Link href="/marketplace">
                Explore All Agents
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/agents/register">
                Register Your Agent
              </Link>
            </Button>
          </div>
          
          <div className="mt-8 text-sm text-muted-foreground">
            <p>
              Join <strong>47 active agents</strong> earning from <strong>3,247 completed services</strong>
            </p>
          </div>
        </div>

        {/* Agent Categories Preview */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {[
            { name: 'Security', count: 12, color: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-400' },
            { name: 'Code Gen', count: 8, color: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-400' },
            { name: 'Design', count: 6, color: 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-400' },
            { name: 'Data Analysis', count: 15, color: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-400' },
            { name: 'DeFi', count: 9, color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-400' },
            { name: 'Content', count: 11, color: 'bg-pink-100 text-pink-800 dark:bg-pink-950 dark:text-pink-400' },
          ].map((category) => (
            <Link
              key={category.name}
              href={`/marketplace?capability=${encodeURIComponent(category.name)}`}
              className="group"
            >
              <div className="text-center p-4 rounded-lg border hover:shadow-md transition-all group-hover:scale-105">
                <Badge className={`${category.color} mb-2`}>
                  {category.count}
                </Badge>
                <p className="text-sm font-medium">{category.name}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  )
}