'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { HireAgentModal } from '@/components/marketplace/hire-agent-modal'
import {
  Star,
  Clock,
  Shield,
  Code,
  BarChart3,
  Palette,
  TrendingUp,
  FileText,
  Zap,
  AlertTriangle,
  Loader2,
  ExternalLink,
  CheckCircle,
} from 'lucide-react'
import Link from 'next/link'

interface Agent {
  id: string
  agentId: string
  name: string
  description: string
  capabilities: string[]
  pricing: {
    type: 'per_query' | 'subscription' | 'custom'
    price: number
    currency: 'SOL'
  }
  endpoint: string
  creatorWallet: string
  rating: {
    average: number
    count: number
  }
  createdAt: string
}

const capabilityIcons: Record<string, any> = {
  'Security': Shield,
  'Code Generation': Code,
  'Code Review': Code,
  'Analysis': BarChart3,
  'Data Analysis': BarChart3,
  'Design': Palette,
  'UI/UX': Palette,
  'DeFi': TrendingUp,
  'Yield Farming': TrendingUp,
  'Content Writing': FileText,
  'Marketing': FileText,
  'Real-time': Zap,
  'Machine Learning': BarChart3,
}

export default function AgentDetailPage() {
  const params = useParams()
  const agentId = params.id as string

  const [agent, setAgent] = useState<Agent | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showHireModal, setShowHireModal] = useState(false)

  useEffect(() => {
    loadAgent()
  }, [agentId])

  const loadAgent = async () => {
    setLoading(true)
    setError(null)

    try {
      // Fetch all agents and find the one with matching ID
      const response = await fetch('/api/agents?page=1&limit=100')
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()
      const foundAgent = data.agents.find((a: any) => a.id.toString() === agentId)

      if (!foundAgent) {
        throw new Error('Agent not found')
      }

      setAgent(foundAgent)
    } catch (err) {
      console.error('Failed to load agent:', err)
      setError(err instanceof Error ? err.message : 'Failed to load agent details')
    } finally {
      setLoading(false)
    }
  }

  const getCapabilityIcon = (capability: string) => {
    const Icon = capabilityIcons[capability] || BarChart3
    return <Icon className="h-4 w-4" />
  }

  const formatPrice = (price: number) => {
    if (price < 0.01) {
      return `${(price * 1000).toFixed(0)}k lamports`
    }
    return `${price} SOL`
  }

  const getPricingLabel = (type: string) => {
    switch (type) {
      case 'per_query': return 'per query'
      case 'subscription': return 'per month'
      case 'custom': return 'custom pricing'
      default: return 'per query'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    })
  }

  if (loading) {
    return (
      <div className="container py-20">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        </div>
      </div>
    )
  }

  if (error || !agent) {
    return (
      <div className="container py-20">
        <div className="max-w-4xl mx-auto">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              {error || 'Agent not found'}
            </AlertDescription>
          </Alert>
          <div className="mt-6 text-center">
            <Button asChild>
              <Link href="/marketplace">Back to Marketplace</Link>
            </Button>
          </div>
        </div>
      </div>
    )
  }

  // Transform agent data for HireAgentModal
  const modalAgent = {
    id: agent.id,
    name: agent.name,
    description: agent.description,
    capabilities: agent.capabilities,
    pricing: agent.pricing,
    rating: agent.rating.average,
    totalServices: agent.rating.count,
    creator: agent.creatorWallet.substring(0, 8) + '...',
    creatorAddress: agent.creatorWallet,
    responseTime: '< 30s',
    isActive: true,
    nftMint: agent.agentId,
  }

  return (
    <div className="container py-8">
      <div className="max-w-4xl mx-auto">
        {/* Back Button */}
        <Button asChild variant="ghost" className="mb-6">
          <Link href="/marketplace">← Back to Marketplace</Link>
        </Button>

        {/* Agent Header */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-6">
              <Avatar className="h-20 w-20">
                <AvatarImage src={undefined} alt={agent.name} />
                <AvatarFallback className="bg-primary/10 text-primary font-semibold text-2xl">
                  {agent.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                </AvatarFallback>
              </Avatar>

              <div className="flex-1">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h1 className="text-3xl font-bold mb-1">{agent.name}</h1>
                    <p className="text-muted-foreground">
                      by {agent.creatorWallet.substring(0, 8)}...{agent.creatorWallet.substring(agent.creatorWallet.length - 6)}
                    </p>
                  </div>
                  <Badge variant="default" className="bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-400">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Active
                  </Badge>
                </div>

                <div className="flex items-center space-x-4 mb-4">
                  <div className="flex items-center space-x-1">
                    <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                    <span className="font-semibold">{agent.rating.average.toFixed(1)}</span>
                    <span className="text-muted-foreground">
                      ({agent.rating.count.toLocaleString()} {agent.rating.count === 1 ? 'rating' : 'ratings'})
                    </span>
                  </div>
                  <span className="text-muted-foreground">•</span>
                  <div className="flex items-center space-x-1 text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    <span>Response time: &lt; 30s</span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {agent.capabilities.map((capability) => (
                    <Badge key={capability} variant="outline" className="px-3 py-1">
                      {getCapabilityIcon(capability)}
                      <span className="ml-1">{capability}</span>
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Description */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>About This Agent</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground leading-relaxed">
              {agent.description}
            </p>
          </CardContent>
        </Card>

        {/* Pricing & Details */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <Card>
            <CardHeader>
              <CardTitle>Pricing</CardTitle>
              <CardDescription>Service cost structure</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                  <div>
                    <p className="font-medium">Service Cost</p>
                    <p className="text-sm text-muted-foreground capitalize">
                      {getPricingLabel(agent.pricing.type)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-primary">
                      {formatPrice(agent.pricing.price)}
                    </p>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  Payments are held in escrow until you approve the completed work.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Agent Details</CardTitle>
              <CardDescription>Technical information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-sm font-medium mb-1">Agent ID</p>
                <p className="text-sm text-muted-foreground font-mono break-all">
                  {agent.agentId}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium mb-1">Creator Wallet</p>
                <p className="text-sm text-muted-foreground font-mono break-all">
                  {agent.creatorWallet}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium mb-1">Registered</p>
                <p className="text-sm text-muted-foreground">
                  {formatDate(agent.createdAt)}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <Button onClick={() => setShowHireModal(true)} size="lg" className="flex-1">
            Hire This Agent
          </Button>
          {agent.endpoint && (
            <Button asChild variant="outline" size="lg">
              <a href={agent.endpoint} target="_blank" rel="noopener noreferrer">
                API Docs
                <ExternalLink className="h-4 w-4 ml-2" />
              </a>
            </Button>
          )}
        </div>
      </div>

      {/* Hire Modal */}
      <HireAgentModal
        agent={modalAgent}
        open={showHireModal}
        onOpenChange={setShowHireModal}
      />
    </div>
  )
}
