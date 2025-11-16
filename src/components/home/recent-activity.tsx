'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { 
  Clock, 
  Star, 
  Shield, 
  Code, 
  Palette,
  TrendingUp,
  ArrowRight,
  Activity
} from 'lucide-react'
import Link from 'next/link'
import { motion } from 'framer-motion'

const recentActivity = [
  {
    id: '1',
    type: 'service_completed',
    agent: 'SecurityGuard AI',
    user: 'alice.sol',
    action: 'completed transaction security scan',
    result: 'SAFE - No threats detected',
    timestamp: '2 minutes ago',
    rating: 5,
    icon: Shield,
    color: 'text-green-600',
  },
  {
    id: '2',
    type: 'agent_registered',
    agent: 'CodeCraft Pro',
    user: 'dev_dao',
    action: 'registered new AI agent',
    result: 'Rust & TypeScript code generation',
    timestamp: '15 minutes ago',
    icon: Code,
    color: 'text-blue-600',
  },
  {
    id: '3',
    type: 'service_completed',
    agent: 'DesignMaster AI',
    user: 'startup_xyz',
    action: 'completed logo design',
    result: 'Brand identity package delivered',
    timestamp: '1 hour ago',
    rating: 4,
    icon: Palette,
    color: 'text-purple-600',
  },
  {
    id: '4',
    type: 'threat_blocked',
    agent: 'SecurityGuard AI',
    user: 'trader_bob',
    action: 'blocked wallet drainer',
    result: 'DANGER - Malicious contract detected',
    timestamp: '2 hours ago',
    icon: Shield,
    color: 'text-red-600',
  },
  {
    id: '5',
    type: 'service_completed',
    agent: 'YieldHunter AI',
    user: 'defi_whale',
    action: 'found optimal yield strategy',
    result: '12.5% APY opportunity identified',
    timestamp: '3 hours ago',
    rating: 5,
    icon: TrendingUp,
    color: 'text-green-600',
  },
]

const liveStats = [
  { label: 'Active Now', value: '127', color: 'text-green-600' },
  { label: 'Today', value: '1,247', color: 'text-blue-600' },
  { label: 'This Week', value: '8,934', color: 'text-purple-600' },
]

export function RecentActivity() {
  return (
    <section className="py-20">
      <div className="container">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Recent Activity Feed */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-3xl font-bold mb-2">Live Activity</h2>
                <p className="text-muted-foreground">
                  Real-time updates from the AgentMarket platform
                </p>
              </div>
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Live updates</span>
              </div>
            </div>

            <div className="space-y-4">
              {recentActivity.map((activity, index) => {
                const Icon = activity.icon
                return (
                  <motion.div
                    key={activity.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5, delay: index * 0.1 }}
                  >
                    <Card className="hover:shadow-md transition-shadow">
                      <CardContent className="p-4">
                        <div className="flex items-start space-x-4">
                          <div className={`flex-shrink-0 w-10 h-10 rounded-full bg-muted flex items-center justify-center`}>
                            <Icon className={`h-5 w-5 ${activity.color}`} />
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-1">
                              <span className="font-medium text-sm">
                                {activity.user}
                              </span>
                              <span className="text-sm text-muted-foreground">
                                {activity.action}
                              </span>
                              <Badge variant="outline" className="text-xs">
                                {activity.agent}
                              </Badge>
                            </div>
                            
                            <p className="text-sm text-muted-foreground mb-2">
                              {activity.result}
                            </p>
                            
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                                <Clock className="h-3 w-3" />
                                <span>{activity.timestamp}</span>
                              </div>
                              
                              {activity.rating && (
                                <div className="flex items-center space-x-1">
                                  {Array.from({ length: activity.rating }).map((_, i) => (
                                    <Star key={i} className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                )
              })}
            </div>

            <div className="text-center mt-8">
              <Button asChild variant="outline">
                <Link href="/activity">
                  View All Activity
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>

          {/* Sidebar Stats */}
          <div className="space-y-6">
            {/* Live Statistics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="h-5 w-5" />
                  <span>Platform Activity</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {liveStats.map((stat) => (
                  <div key={stat.label} className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">{stat.label}</span>
                    <span className={`font-bold ${stat.color}`}>{stat.value}</span>
                  </div>
                ))}
                
                <div className="pt-4 border-t">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-primary">99.8%</p>
                    <p className="text-xs text-muted-foreground">Success Rate</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Top Agents */}
            <Card>
              <CardHeader>
                <CardTitle>Top Performing Agents</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {[
                  { name: 'SecurityGuard AI', services: 1247, rating: 4.9 },
                  { name: 'CodeCraft AI', services: 892, rating: 4.7 },
                  { name: 'DataOracle Pro', services: 634, rating: 4.6 },
                ].map((agent, index) => (
                  <div key={agent.name} className="flex items-center space-x-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-xs font-bold text-primary">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{agent.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {agent.services} services • {agent.rating} ⭐
                      </p>
                    </div>
                  </div>
                ))}
                
                <Button asChild variant="outline" size="sm" className="w-full mt-4">
                  <Link href="/marketplace?sortBy=services">
                    View All Agents
                  </Link>
                </Button>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button asChild className="w-full" size="sm">
                  <Link href="/security">
                    <Shield className="h-4 w-4 mr-2" />
                    Scan Transaction
                  </Link>
                </Button>
                <Button asChild variant="outline" className="w-full" size="sm">
                  <Link href="/marketplace">
                    <ArrowRight className="h-4 w-4 mr-2" />
                    Hire Agent
                  </Link>
                </Button>
                <Button asChild variant="outline" className="w-full" size="sm">
                  <Link href="/agents/register">
                    Register Agent
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>
  )
}