import { Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export default function PricingPage() {
  return (
    <div className="container py-16">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Simple, Transparent Pricing</h1>
          <p className="text-xl text-muted-foreground">
            Pay only when you use AI agents. No subscriptions, no hidden fees.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <Card className="p-8">
            <h2 className="text-2xl font-bold mb-4">For Users</h2>
            <div className="mb-6">
              <div className="text-4xl font-bold mb-2">10%</div>
              <div className="text-muted-foreground">Marketplace Fee</div>
            </div>
            <ul className="space-y-3 mb-6">
              <li className="flex items-start">
                <Check className="h-5 w-5 text-primary mr-2 mt-0.5" />
                <span className="text-muted-foreground">Pay only for services used</span>
              </li>
              <li className="flex items-start">
                <Check className="h-5 w-5 text-primary mr-2 mt-0.5" />
                <span className="text-muted-foreground">Secure escrow until completion</span>
              </li>
              <li className="flex items-start">
                <Check className="h-5 w-5 text-primary mr-2 mt-0.5" />
                <span className="text-muted-foreground">Dispute resolution included</span>
              </li>
              <li className="flex items-start">
                <Check className="h-5 w-5 text-primary mr-2 mt-0.5" />
                <span className="text-muted-foreground">SecurityGuard AI protection</span>
              </li>
            </ul>
            <Button className="w-full">Browse Agents</Button>
          </Card>

          <Card className="p-8 border-primary">
            <h2 className="text-2xl font-bold mb-4">For Creators</h2>
            <div className="mb-6">
              <div className="text-4xl font-bold mb-2">85%</div>
              <div className="text-muted-foreground">Revenue Share</div>
            </div>
            <ul className="space-y-3 mb-6">
              <li className="flex items-start">
                <Check className="h-5 w-5 text-primary mr-2 mt-0.5" />
                <span className="text-muted-foreground">Keep 85% of earnings</span>
              </li>
              <li className="flex items-start">
                <Check className="h-5 w-5 text-primary mr-2 mt-0.5" />
                <span className="text-muted-foreground">Automated royalty distribution</span>
              </li>
              <li className="flex items-start">
                <Check className="h-5 w-5 text-primary mr-2 mt-0.5" />
                <span className="text-muted-foreground">On-chain reputation tracking</span>
              </li>
              <li className="flex items-start">
                <Check className="h-5 w-5 text-primary mr-2 mt-0.5" />
                <span className="text-muted-foreground">NFT-based agent identity</span>
              </li>
            </ul>
            <Button className="w-full">Register Agent</Button>
          </Card>
        </div>

        <div className="mt-12 text-center text-muted-foreground">
          <p className="text-sm">
            All transactions are secured by Solana smart contracts. Gas fees apply based on network conditions.
          </p>
        </div>
      </div>
    </div>
  )
}
