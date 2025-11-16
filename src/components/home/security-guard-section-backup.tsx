'use client'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Shield, 
  Zap, 
  Brain, 
  CheckCircle, 
  ArrowRight,
  AlertTriangle,
  TrendingUp
} from 'lucide-react'
import Link from 'next/link'
import { motion } from 'framer-motion'

const features = [
  {
    icon: Zap,
    title: 'Real-time Analysis',
    description: 'Scan transactions in under 2 seconds with 99.8% accuracy',
  },
  {
    icon: Brain,
    title: 'AI-Powered Detection',
    description: 'Advanced ML models trained on millions of exploit patterns',
  },
  {
    icon: Shield,
    title: 'Comprehensive Protection',
    description: 'Detects wallet drainers, rug pulls, and malicious contracts',
  },
]

const threatStats = [
  { label: 'Wallet Drainers Blocked', value: '1,247', color: 'text-red-600' },
  { label: 'Rug Pulls Prevented', value: '89', color: 'text-orange-600' },
  { label: 'Malicious Contracts', value: '456', color: 'text-yellow-600' },
  { label: 'Users Protected', value: '12,847', color: 'text-green-600' },
]

export function SecurityGuardSection() {
  return (
    <div className="py-20 bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-950/20 dark:to-orange-950/20">
      <div className="container">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-8">
            <div>
              <Badge variant="destructive" className="mb-4">
                🚨 Security Crisis: $2B Lost in 2024
              </Badge>
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-6">
                <span className="text-red-600">SecurityGuard AI</span>
                <br />
                Protects Your Transactions
              </h2>
              <p className="text-lg text-muted-foreground leading-relaxed">
                Our flagship AI agent provides real-time transaction security analysis, 
                protecting Solana users from wallet exploits and malicious contracts. 
                Built with advanced ML models and trained on millions of threat patterns.
              </p>
            </div>

            <div className="space-y-4">
              {features.map((feature, index) => {
                const Icon = feature.icon
                return (
                  <motion.div
                    key={feature.title}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5, delay: index * 0.1 }}
                    className="flex items-start space-x-4"
                  >
                    <div className="flex-shrink-0 w-10 h-10 bg-red-100 dark:bg-red-950/50 rounded-lg flex items-center justify-center">
                      <Icon className="h-5 w-5 text-red-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold mb-1">{feature.title}</h3>
                      <p className="text-sm text-muted-foreground">
                        {feature.description}
                      </p>
                    </div>
                  </motion.div>
                )
              })}
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Button asChild size="lg" className="bg-red-600 hover:bg-red-700">
                <Link href="/security">
                  Try SecurityGuard AI
                  <Shield className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link href="/security/demo">
                  Watch Demo
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>

            <div className="p-4 bg-muted/50 rounded-lg border">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">SecurityGuard AI Pricing</p>
                  <p className="text-sm text-muted-foreground">
                    Pay per scan, no subscription required
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-red-600">0.01 SOL</p>
                  <p className="text-xs text-muted-foreground">~$2 per scan</p>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <Card className="border-red-200 dark:border-red-800">
              <CardContent className="p-6">
                <div className="flex items-center space-x-2 mb-6">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                  <h3 className="font-semibold">Threats Detected & Blocked</h3>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  {threatStats.map((stat, index) => (
                    <motion.div
                      key={stat.label}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                      className="text-center p-4 bg-muted/30 rounded-lg"
                    >
                      <p className={`text-2xl font-bold ${stat.color}`}>
                        {stat.value}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {stat.label}
                      </p>
                    </motion.div>
                  ))}
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Detection Accuracy</span>
                    <span className="font-medium">99.8%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-green-600 h-2 rounded-full w-[99.8%]"></div>
                  </div>
                </div>

                <div className="space-y-3 mt-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Response Time</span>
                    <span className="font-medium">&#60; 2 seconds</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full w-[95%]"></div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-950/20 dark:to-orange-950/20 border-red-200 dark:border-red-800">
              <CardContent className="p-6">
                <div className="flex items-center space-x-2 mb-4">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium">Live Protection Active</span>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-background/50 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="text-sm">Transaction Scanned</span>
                    </div>
                    <Badge variant="secondary" className="text-xs">
                      SAFE
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-background/50 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <AlertTriangle className="h-4 w-4 text-red-600" />
                      <span className="text-sm">Wallet Drainer Blocked</span>
                    </div>
                    <Badge variant="destructive" className="text-xs">
                      DANGER
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-background/50 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="h-4 w-4 text-blue-600" />
                      <span className="text-sm">Analysis Complete</span>
                    </div>
                    <span className="text-xs text-muted-foreground">1.2s</span>
                  </div>
                </div>

                <Button asChild className="w-full mt-4" variant="outline">
                  <Link href="/security/scan">
                    Scan Your Transaction
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
