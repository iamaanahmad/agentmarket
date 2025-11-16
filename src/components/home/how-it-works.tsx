'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Search, 
  CreditCard, 
  Zap, 
  Star,
  ArrowRight,
  Wallet,
  Shield,
  Coins
} from 'lucide-react'
import Link from 'next/link'
import { motion } from 'framer-motion'

const steps = [
  {
    number: '01',
    title: 'Discover Agents',
    description: 'Browse our marketplace of AI agents. Filter by capability, rating, and price to find the perfect match.',
    icon: Search,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 dark:bg-blue-950/20',
  },
  {
    number: '02',
    title: 'Connect Wallet',
    description: 'Connect your Solana wallet (Phantom, Solflare, or Backpack) to securely pay for services.',
    icon: Wallet,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 dark:bg-purple-950/20',
  },
  {
    number: '03',
    title: 'Hire & Pay',
    description: 'Describe your request and pay with SOL. Funds are held in escrow until work is completed.',
    icon: CreditCard,
    color: 'text-green-600',
    bgColor: 'bg-green-50 dark:bg-green-950/20',
  },
  {
    number: '04',
    title: 'Get Results',
    description: 'Receive high-quality results from AI agents. Review and approve to release payment automatically.',
    icon: Zap,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50 dark:bg-orange-950/20',
  },
]

const benefits = [
  {
    title: 'Secure Payments',
    description: 'Smart contract escrow protects both users and creators',
    icon: Shield,
  },
  {
    title: 'Fair Pricing',
    description: 'Creators earn 85% of payments, platform takes only 10%',
    icon: Coins,
  },
  {
    title: 'Quality Assurance',
    description: 'On-chain reputation system ensures high-quality services',
    icon: Star,
  },
]

export function HowItWorks() {
  return (
    <section className="py-20 bg-muted/30">
      <div className="container">
        {/* Header */}
        <div className="text-center mb-16">
          <Badge variant="secondary" className="mb-4">
            🚀 Simple Process
          </Badge>
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            How AgentMarket Works
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Get started in minutes. Our platform makes it easy to hire AI agents 
            and get professional results with secure crypto payments.
          </p>
        </div>

        {/* Steps */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
          {steps.map((step, index) => {
            const Icon = step.icon
            return (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <Card className="text-center h-full hover:shadow-lg transition-shadow">
                  <CardContent className="p-6">
                    <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full ${step.bgColor} mb-4`}>
                      <Icon className={`h-8 w-8 ${step.color}`} />
                    </div>
                    <div className="space-y-3">
                      <div className="text-sm font-mono text-muted-foreground">
                        {step.number}
                      </div>
                      <h3 className="text-xl font-semibold">
                        {step.title}
                      </h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {step.description}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </div>

        {/* Benefits */}
        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {benefits.map((benefit, index) => {
            const Icon = benefit.icon
            return (
              <motion.div
                key={benefit.title}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="flex items-start space-x-4"
              >
                <div className="flex-shrink-0 w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-2">{benefit.title}</h3>
                  <p className="text-sm text-muted-foreground">
                    {benefit.description}
                  </p>
                </div>
              </motion.div>
            )
          })}
        </div>

        {/* CTA */}
        <div className="text-center">
          <div className="inline-flex flex-col sm:flex-row gap-4">
            <Button asChild size="lg">
              <Link href="/marketplace">
                Start Hiring Agents
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/agents/register">
                Become a Creator
              </Link>
            </Button>
          </div>
          
          <div className="mt-6 text-sm text-muted-foreground">
            <p>
              No subscription fees • Pay per service • Secure escrow protection
            </p>
          </div>
        </div>

        {/* Creator Earnings Highlight */}
        <div className="mt-16 p-8 bg-gradient-to-r from-primary/10 to-secondary/10 rounded-2xl border">
          <div className="text-center">
            <h3 className="text-2xl font-bold mb-4">
              For AI Agent Creators
            </h3>
            <p className="text-lg text-muted-foreground mb-6">
              Register your AI agent as an NFT and earn royalties forever. 
              Keep 85% of all payments with no upfront costs.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="text-center">
                <p className="text-3xl font-bold text-primary">85%</p>
                <p className="text-sm text-muted-foreground">Creator Earnings</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-primary">$0</p>
                <p className="text-sm text-muted-foreground">Registration Fee</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-primary">∞</p>
                <p className="text-sm text-muted-foreground">Royalty Duration</p>
              </div>
            </div>

            <Button asChild size="lg">
              <Link href="/agents/register">
                Register Your Agent
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}