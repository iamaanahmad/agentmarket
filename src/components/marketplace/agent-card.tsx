'use client'

import { useState } from 'react'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { HireAgentModal } from './hire-agent-modal'
import { 
  Star, 
  Clock, 
  Shield, 
  Code, 
  BarChart3, 
  Palette, 
  TrendingUp,
  FileText,
  Zap
} from 'lucide-react'
import Link from 'next/link'
import { cn } from '@/lib/utils'

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

interface AgentCardProps {
  agent: Agent
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

const capabilityColors: Record<string, string> = {
  'Security': 'capability-security',
  'Code Generation': 'capability-code',
  'Code Review': 'capability-code',
  'Analysis': 'capability-analysis',
  'Data Analysis': 'capability-analysis',
  'Design': 'capability-design',
  'UI/UX': 'capability-design',
  'DeFi': 'capability-data',
  'Yield Farming': 'capability-data',
  'Content Writing': 'capability-design',
  'Marketing': 'capability-design',
  'Real-time': 'capability-security',
  'Machine Learning': 'capability-analysis',
}

export function AgentCard({ agent }: AgentCardProps) {
  const [showHireModal, setShowHireModal] = useState(false)

  const getCapabilityIcon = (capability: string) => {
    const Icon = capabilityIcons[capability] || BarChart3
    return <Icon className="h-3 w-3" />
  }

  const getCapabilityColor = (capability: string) => {
    return capabilityColors[capability] || 'capability-analysis'
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
      case 'custom': return 'custom'
      default: return 'per query'
    }
  }

  return (
    <>
      <Card className="group hover:shadow-lg transition-all duration-200 hover:-translate-y-1 border-border/50 hover:border-primary/20">
        <CardContent className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-start space-x-3">
              <Avatar className="h-10 w-10">
                <AvatarImage src={agent.avatar} alt={agent.name} />
                <AvatarFallback className="bg-primary/10 text-primary font-semibold">
                  {agent.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                </AvatarFallback>
              </Avatar>
              <div className="min-w-0 flex-1">
                <Link 
                  href={`/agents/${agent.id}`}
                  className="font-semibold text-lg hover:text-primary transition-colors line-clamp-1"
                >
                  {agent.name}
                </Link>
                <p className="text-sm text-muted-foreground line-clamp-1">
                  by {agent.creator}
                </p>
              </div>
            </div>
            {!agent.isActive && (
              <Badge variant="secondary" className="text-xs">
                Inactive
              </Badge>
            )}
          </div>

          {/* Capabilities */}
          <div className="flex flex-wrap gap-1 mb-3">
            {agent.capabilities.slice(0, 3).map((capability) => (
              <Badge
                key={capability}
                variant="outline"
                className={cn(
                  "text-xs px-2 py-1 border",
                  getCapabilityColor(capability)
                )}
              >
                {getCapabilityIcon(capability)}
                <span className="ml-1">{capability}</span>
              </Badge>
            ))}
            {agent.capabilities.length > 3 && (
              <Badge variant="outline" className="text-xs px-2 py-1">
                +{agent.capabilities.length - 3}
              </Badge>
            )}
          </div>

          {/* Description */}
          <p className="text-sm text-muted-foreground line-clamp-3 mb-4 leading-relaxed">
            {agent.description}
          </p>

          {/* Stats */}
          <div className="flex items-center justify-between mb-4 text-sm">
            <div className="flex items-center space-x-1">
              <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
              <span className="font-medium">{agent.rating}</span>
              <span className="text-muted-foreground">
                ({agent.totalServices.toLocaleString()})
              </span>
            </div>
            <div className="flex items-center space-x-1 text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>{agent.responseTime}</span>
            </div>
          </div>

          {/* Pricing */}
          <div className="flex items-center justify-between">
            <div className="text-right">
              <p className="text-lg font-bold text-primary">
                {formatPrice(agent.pricing.price)}
              </p>
              <p className="text-xs text-muted-foreground">
                {getPricingLabel(agent.pricing.type)}
              </p>
            </div>
          </div>
        </CardContent>

        <CardFooter className="p-6 pt-0">
          <div className="flex gap-2 w-full">
            <Button 
              asChild 
              variant="outline" 
              size="sm" 
              className="flex-1"
            >
              <Link href={`/agents/${agent.id}`}>
                View Details
              </Link>
            </Button>
            <Button 
              onClick={() => setShowHireModal(true)}
              size="sm" 
              className="flex-1"
              disabled={!agent.isActive}
            >
              Hire Agent
            </Button>
          </div>
        </CardFooter>
      </Card>

      <HireAgentModal
        agent={agent}
        open={showHireModal}
        onOpenChange={setShowHireModal}
      />
    </>
  )
}