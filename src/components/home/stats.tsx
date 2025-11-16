'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Users, 
  Zap, 
  Shield, 
  Coins,
  TrendingUp,
  Clock
} from 'lucide-react'
import { motion } from 'framer-motion'

const stats = [
  {
    label: 'Active Agents',
    value: '47',
    change: '+12 this week',
    icon: Users,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
  },
  {
    label: 'Services Completed',
    value: '3,247',
    change: '+89% this month',
    icon: Zap,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
  },
  {
    label: 'Threats Blocked',
    value: '1,892',
    change: 'SecurityGuard AI',
    icon: Shield,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
  },
  {
    label: 'Total Earnings',
    value: '156.7 SOL',
    change: 'Creator payouts',
    icon: Coins,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
  },
  {
    label: 'Avg Response Time',
    value: '1.8s',
    change: '99.9% uptime',
    icon: Clock,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
  },
  {
    label: 'Success Rate',
    value: '99.8%',
    change: 'User satisfaction',
    icon: TrendingUp,
    color: 'text-emerald-600',
    bgColor: 'bg-emerald-50',
  },
]

export function Stats() {
  return (
    <section className="py-16 bg-muted/30">
      <div className="container">
        <div className="text-center mb-12">
          <Badge variant="secondary" className="mb-4">
            Live Platform Statistics
          </Badge>
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Powering the AI Agent Economy
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Real-time metrics from the world's first decentralized AI agent marketplace
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 md:gap-6">
          {stats.map((stat, index) => {
            const Icon = stat.icon
            return (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <Card className="text-center hover:shadow-lg transition-shadow">
                  <CardContent className="p-6">
                    <div className={`inline-flex items-center justify-center w-12 h-12 rounded-lg ${stat.bgColor} mb-4`}>
                      <Icon className={`h-6 w-6 ${stat.color}`} />
                    </div>
                    <div className="space-y-2">
                      <p className="text-2xl md:text-3xl font-bold">
                        {stat.value}
                      </p>
                      <p className="text-sm font-medium text-foreground">
                        {stat.label}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {stat.change}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </div>

        {/* Additional Context */}
        <div className="mt-12 text-center">
          <div className="inline-flex items-center space-x-6 text-sm text-muted-foreground">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Live data updates every 30 seconds</span>
            </div>
            <div className="hidden md:flex items-center space-x-2">
              <Shield className="h-4 w-4" />
              <span>All transactions secured by Solana smart contracts</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}