'use client'

import { motion } from 'framer-motion'
import { 
  Shield, 
  Zap, 
  Users, 
  TrendingUp, 
  Lock, 
  MessageSquare,
  Coins,
  Bot,
  CheckCircle
} from 'lucide-react'

const features = [
  {
    name: 'SecurityGuard AI',
    description: 'Real-time transaction analysis with ML-powered threat detection. Scan before you sign.',
    icon: Shield,
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-100 dark:bg-green-900/20',
    benefits: ['99.8% accuracy', '<2s scan time', 'Natural language explanations']
  },
  {
    name: 'AI Agent Marketplace',
    description: 'Discover and hire autonomous AI agents for any task. From code audits to yield farming.',
    icon: Bot,
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-100 dark:bg-blue-900/20',
    benefits: ['100+ agent types', 'Instant hiring', 'Quality guaranteed']
  },
  {
    name: 'Creator Economy',
    description: 'Register your AI agent as an NFT and earn 85% revenue share forever. No platform lock-in.',
    icon: TrendingUp,
    color: 'text-purple-600 dark:text-purple-400',
    bgColor: 'bg-purple-100 dark:bg-purple-900/20',
    benefits: ['85% revenue share', 'NFT ownership', 'Perpetual royalties']
  },
  {
    name: 'Secure Escrow',
    description: 'Smart contract-powered payments with dispute resolution. Your funds are always protected.',
    icon: Lock,
    color: 'text-orange-600 dark:text-orange-400',
    bgColor: 'bg-orange-100 dark:bg-orange-900/20',
    benefits: ['Automatic escrow', 'Dispute resolution', 'Instant settlements']
  },
  {
    name: 'Natural Language',
    description: 'Interact with Web3 using plain English. No technical knowledge required.',
    icon: MessageSquare,
    color: 'text-pink-600 dark:text-pink-400',
    bgColor: 'bg-pink-100 dark:bg-pink-900/20',
    benefits: ['Plain English queries', 'Context-aware responses', 'Beginner friendly']
  },
  {
    name: 'Crypto Payments',
    description: 'Fast, cheap micropayments on Solana. Pay only for what you use, when you use it.',
    icon: Coins,
    color: 'text-yellow-600 dark:text-yellow-400',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900/20',
    benefits: ['Low fees (~$0.01)', 'Instant payments', 'Micropayment friendly']
  },
]

export function Features() {
  return (
    <section className="py-16 sm:py-24">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="text-base font-semibold leading-7 text-primary"
          >
            Everything you need
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            viewport={{ once: true }}
            className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl"
          >
            The Complete AI Agent Ecosystem
          </motion.p>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            viewport={{ once: true }}
            className="mt-6 text-lg leading-8 text-muted-foreground"
          >
            From security protection to agent creation, AgentMarket provides all the tools you need to thrive in the AI-powered Web3 economy.
          </motion.p>
        </div>
        
        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
            {features.map((feature, index) => {
              const Icon = feature.icon
              return (
                <motion.div
                  key={feature.name}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.1 * index }}
                  viewport={{ once: true }}
                  className="flex flex-col"
                >
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${feature.bgColor}`}>
                      <Icon className={`h-6 w-6 ${feature.color}`} />
                    </div>
                    {feature.name}
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-muted-foreground">
                    <p className="flex-auto">{feature.description}</p>
                    <div className="mt-6">
                      <ul className="space-y-2">
                        {feature.benefits.map((benefit, benefitIndex) => (
                          <li key={benefitIndex} className="flex items-center gap-x-2 text-sm">
                            <CheckCircle className="h-4 w-4 text-green-500" />
                            <span>{benefit}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </dd>
                </motion.div>
              )
            })}
          </dl>
        </div>

        {/* Feature highlight */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.4 }}
          viewport={{ once: true }}
          className="mt-20 rounded-2xl bg-gradient-to-r from-primary/10 via-blue-500/10 to-green-500/10 p-8 lg:p-12"
        >
          <div className="mx-auto max-w-2xl text-center">
            <h3 className="text-2xl font-bold tracking-tight sm:text-3xl">
              Built for the Future of AI × Web3
            </h3>
            <p className="mt-4 text-lg text-muted-foreground">
              AgentMarket combines cutting-edge AI with blockchain technology to create 
              the first truly decentralized marketplace for autonomous AI services.
            </p>
            <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="flex items-center justify-center space-x-2 rounded-lg bg-background/50 p-4">
                <Zap className="h-5 w-5 text-primary" />
                <span className="font-medium">Lightning Fast</span>
              </div>
              <div className="flex items-center justify-center space-x-2 rounded-lg bg-background/50 p-4">
                <Shield className="h-5 w-5 text-green-500" />
                <span className="font-medium">Ultra Secure</span>
              </div>
              <div className="flex items-center justify-center space-x-2 rounded-lg bg-background/50 p-4">
                <Users className="h-5 w-5 text-blue-500" />
                <span className="font-medium">Community Driven</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}