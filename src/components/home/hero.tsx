'use client'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'
import { ArrowRight, Shield, Zap, Coins, Users } from 'lucide-react'
import { motion } from 'framer-motion'

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-primary/5 via-background to-secondary/5">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:50px_50px]" />
      <div className="absolute top-0 right-0 -translate-y-12 translate-x-12">
        <div className="h-96 w-96 rounded-full bg-primary/10 blur-3xl" />
      </div>
      <div className="absolute bottom-0 left-0 translate-y-12 -translate-x-12">
        <div className="h-96 w-96 rounded-full bg-secondary/10 blur-3xl" />
      </div>

      <div className="container relative">
        <div className="flex flex-col items-center text-center space-y-8 py-20 md:py-32">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Badge variant="secondary" className="px-4 py-2 text-sm">
              🏆 AWS Global Vibe Hackathon 2025 • Web3 AI Integration Track
            </Badge>
          </motion.div>

          {/* Main Headline */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="space-y-4"
          >
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight">
              The AI Agent
              <br />
              <span className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                Marketplace
              </span>
              <br />
              for Web3
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              Hire autonomous AI agents for crypto. Create agents and earn forever.
              <br />
              <strong className="text-foreground">SecurityGuard AI</strong> protects your transactions.
            </p>
          </motion.div>

          {/* Key Features */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-6 w-full max-w-4xl"
          >
            <div className="flex flex-col items-center space-y-2 p-4">
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                <Shield className="h-6 w-6 text-primary" />
              </div>
              <span className="text-sm font-medium">Security First</span>
            </div>
            <div className="flex flex-col items-center space-y-2 p-4">
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                <Zap className="h-6 w-6 text-primary" />
              </div>
              <span className="text-sm font-medium">Instant Payments</span>
            </div>
            <div className="flex flex-col items-center space-y-2 p-4">
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                <Coins className="h-6 w-6 text-primary" />
              </div>
              <span className="text-sm font-medium">Earn Forever</span>
            </div>
            <div className="flex flex-col items-center space-y-2 p-4">
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                <Users className="h-6 w-6 text-primary" />
              </div>
              <span className="text-sm font-medium">Decentralized</span>
            </div>
          </motion.div>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-4 w-full max-w-md"
          >
            <Button asChild size="lg" className="flex-1">
              <Link href="/marketplace">
                Explore Agents
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="flex-1">
              <Link href="/security">
                Try SecurityGuard
                <Shield className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </motion.div>

          {/* Value Proposition */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="text-sm text-muted-foreground max-w-2xl"
          >
            <p>
              Built on Solana with Claude Sonnet 4. Creators earn{' '}
              <span className="font-semibold text-primary">85% royalties</span> forever.
              SecurityGuard AI has prevented{' '}
              <span className="font-semibold text-foreground">$2B+ in exploits</span>.
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  )
}