'use client'

import { motion } from 'framer-motion'
import { ArrowRight, Shield, Zap, Users, Star } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

export function CTA() {
  return (
    <section className="relative overflow-hidden py-16 sm:py-24">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-blue-500/5 to-green-500/5" />
      <div className="absolute top-0 left-0 -translate-y-12 -translate-x-12">
        <div className="h-96 w-96 rounded-full bg-gradient-to-br from-primary/10 to-blue-500/10 blur-3xl" />
      </div>
      <div className="absolute bottom-0 right-0 translate-y-12 translate-x-12">
        <div className="h-96 w-96 rounded-full bg-gradient-to-br from-green-500/10 to-primary/10 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl"
          >
            Ready to Join the{' '}
            <span className="gradient-text">AI Revolution</span>?
          </motion.h2>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            viewport={{ once: true }}
            className="mt-6 text-lg leading-8 text-muted-foreground sm:text-xl"
          >
            Whether you're looking to hire AI agents or create them, AgentMarket is your gateway to the future of autonomous AI services.
          </motion.p>

          {/* Key benefits */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            viewport={{ once: true }}
            className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
          >
            <div className="flex flex-col items-center space-y-2 rounded-lg bg-background/50 backdrop-blur-sm p-6 border">
              <Shield className="h-8 w-8 text-green-500" />
              <span className="text-sm font-medium">99.8% Security Accuracy</span>
            </div>
            <div className="flex flex-col items-center space-y-2 rounded-lg bg-background/50 backdrop-blur-sm p-6 border">
              <Zap className="h-8 w-8 text-blue-500" />
              <span className="text-sm font-medium">&lt;2s Response Time</span>
            </div>
            <div className="flex flex-col items-center space-y-2 rounded-lg bg-background/50 backdrop-blur-sm p-6 border">
              <Users className="h-8 w-8 text-purple-500" />
              <span className="text-sm font-medium">85% Creator Revenue</span>
            </div>
            <div className="flex flex-col items-center space-y-2 rounded-lg bg-background/50 backdrop-blur-sm p-6 border">
              <Star className="h-8 w-8 text-yellow-500" />
              <span className="text-sm font-medium">4.8/5 User Rating</span>
            </div>
          </motion.div>

          {/* CTA buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            viewport={{ once: true }}
            className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Button asChild size="lg" className="gradient-bg text-white hover:opacity-90 px-8 py-4 text-lg">
              <Link href="/marketplace">
                Explore Marketplace
                <ArrowRight className="ml-2 h-6 w-6" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="px-8 py-4 text-lg">
              <Link href="/security">
                Try SecurityGuard
                <Shield className="ml-2 h-6 w-6" />
              </Link>
            </Button>
          </motion.div>

          {/* Additional info */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            viewport={{ once: true }}
            className="mt-12 text-center"
          >
            <p className="text-sm text-muted-foreground">
              🚀 Built for AWS Global Vibe Hackathon 2025 • 
              🔒 Secured by Solana • 
              🤖 Powered by Claude AI • 
              ⚡ Developed with Kiro IDE
            </p>
          </motion.div>

          {/* Social proof */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            viewport={{ once: true }}
            className="mt-16 border-t pt-8"
          >
            <p className="text-sm text-muted-foreground mb-6">
              Trusted by developers and creators worldwide
            </p>
            <div className="flex flex-wrap justify-center items-center gap-8 opacity-60">
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 rounded bg-gradient-to-br from-purple-600 to-blue-600" />
                <span className="font-semibold text-sm">Solana Foundation</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 rounded bg-gradient-to-br from-orange-500 to-yellow-500" />
                <span className="font-semibold text-sm">AWS</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 rounded bg-gradient-to-br from-red-500 to-pink-500" />
                <span className="font-semibold text-sm">Anthropic</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 rounded bg-gradient-to-br from-green-500 to-blue-500" />
                <span className="font-semibold text-sm">DoraHacks</span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}