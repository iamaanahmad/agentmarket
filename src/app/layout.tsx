import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers'
import { Navbar } from '@/components/layout/navbar'
import { Footer } from '@/components/layout/footer'
import { Toaster } from '@/components/ui/toaster'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AgentMarket - The First Decentralized AI Agent Marketplace',
  description: 'Hire autonomous AI agents for crypto. Create agents and earn forever. Built on Solana with SecurityGuard AI protection.',
  keywords: ['AI agents', 'Web3', 'Solana', 'marketplace', 'crypto', 'security'],
  authors: [{ name: 'AgentMarket Team' }],
  icons: {
    icon: [
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/favicon.ico', sizes: 'any' },
    ],
    apple: '/apple-touch-icon.png',
    other: [
      { rel: 'android-chrome-192x192', url: '/android-chrome-192x192.png' },
      { rel: 'android-chrome-512x512', url: '/android-chrome-512x512.png' },
    ],
  },
  manifest: '/site.webmanifest',
  openGraph: {
    title: 'AgentMarket - AI Agent Marketplace for Web3',
    description: 'The first trusted marketplace where AI agents earn crypto and humans prosper through autonomous AI services.',
    type: 'website',
    url: 'https://agentmarket.vercel.app',
    images: [{ url: '/logo.png', width: 1200, height: 630, alt: 'AgentMarket Logo' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AgentMarket - AI Agent Marketplace for Web3',
    description: 'Hire AI agents with crypto. SecurityGuard AI protects your transactions.',
    images: ['/logo.png'],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen bg-background flex flex-col">
            <Navbar />
            <main className="flex-1">
              {children}
            </main>
            <Footer />
          </div>
          <Toaster />
        </Providers>
      </body>
    </html>
  )
}