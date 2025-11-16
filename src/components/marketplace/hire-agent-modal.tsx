'use client'

import { useState } from 'react'
import { useWallet } from '@solana/wallet-adapter-react'
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useToast } from '@/hooks/use-toast'
import { 
  Loader2, 
  Wallet, 
  Shield, 
  Clock, 
  Star,
  AlertTriangle,
  CheckCircle
} from 'lucide-react'

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
  responseTime: string
  isActive: boolean
  nftMint: string
}

interface HireAgentModalProps {
  agent: Agent
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function HireAgentModal({ agent, open, onOpenChange }: HireAgentModalProps) {
  const { connected, publicKey } = useWallet()
  const { toast } = useToast()
  const [requestData, setRequestData] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [step, setStep] = useState<'details' | 'confirm' | 'processing' | 'success'>('details')

  const handleSubmit = async () => {
    if (!connected || !publicKey) {
      toast({
        title: "Wallet not connected",
        description: "Please connect your wallet to hire an agent.",
        variant: "destructive",
      })
      return
    }

    if (!requestData.trim()) {
      toast({
        title: "Request required",
        description: "Please describe what you need the agent to do.",
        variant: "destructive",
      })
      return
    }

    setStep('confirm')
  }

  const handleConfirm = async () => {
    if (!publicKey) {
      toast({
        title: "Wallet not connected",
        description: "Please connect your wallet to proceed.",
        variant: "destructive",
      })
      return
    }

    setIsSubmitting(true)
    setStep('processing')

    try {
      // Create service request via API
      const response = await fetch('/api/requests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agentId: agent.nftMint,
          userWallet: publicKey.toString(),
          amount: agent.pricing.price,
          requestData: {
            description: requestData,
            timestamp: new Date().toISOString(),
          },
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to create request')
      }

      const data = await response.json()
      
      setStep('success')
      
      toast({
        title: "Service request created!",
        description: `Request ID: ${data.request.requestId}. ${agent.name} will start working on it.`,
      })

      // Auto-close after success
      setTimeout(() => {
        onOpenChange(false)
        resetModal()
      }, 3000)

    } catch (error) {
      console.error('Failed to create service request:', error)
      toast({
        title: "Request failed",
        description: error instanceof Error ? error.message : "Failed to create service request. Please try again.",
        variant: "destructive",
      })
      setStep('details')
    } finally {
      setIsSubmitting(false)
    }
  }

  const resetModal = () => {
    setStep('details')
    setRequestData('')
    setIsSubmitting(false)
  }

  const handleClose = () => {
    if (!isSubmitting) {
      onOpenChange(false)
      resetModal()
    }
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
      case 'custom': return 'custom pricing'
      default: return 'per query'
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <span>Hire {agent.name}</span>
            {step === 'success' && <CheckCircle className="h-5 w-5 text-green-500" />}
          </DialogTitle>
          <DialogDescription>
            {step === 'details' && "Describe your request and confirm payment details."}
            {step === 'confirm' && "Review your request and confirm payment."}
            {step === 'processing' && "Creating your service request..."}
            {step === 'success' && "Your request has been submitted successfully!"}
          </DialogDescription>
        </DialogHeader>

        {step === 'details' && (
          <div className="space-y-6">
            {/* Agent Info */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                  <span className="font-medium">{agent.rating}</span>
                  <span className="text-sm text-muted-foreground">
                    ({agent.totalServices.toLocaleString()} services)
                  </span>
                </div>
                <div className="flex items-center space-x-1 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  <span>{agent.responseTime}</span>
                </div>
              </div>

              <div className="flex flex-wrap gap-1">
                {agent.capabilities.map((capability) => (
                  <Badge key={capability} variant="secondary" className="text-xs">
                    {capability}
                  </Badge>
                ))}
              </div>
            </div>

            <Separator />

            {/* Request Input */}
            <div className="space-y-2">
              <Label htmlFor="request">Describe your request</Label>
              <Textarea
                id="request"
                placeholder="Please describe what you need the agent to do. Be as specific as possible to get the best results..."
                value={requestData}
                onChange={(e) => setRequestData(e.target.value)}
                rows={4}
                className="resize-none"
              />
              <p className="text-xs text-muted-foreground">
                {requestData.length}/1000 characters
              </p>
            </div>

            {/* Pricing */}
            <div className="space-y-3">
              <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                <div>
                  <p className="font-medium">Service Cost</p>
                  <p className="text-sm text-muted-foreground">
                    {getPricingLabel(agent.pricing.type)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-primary">
                    {formatPrice(agent.pricing.price)}
                  </p>
                </div>
              </div>

              {!connected && (
                <Alert>
                  <Wallet className="h-4 w-4" />
                  <AlertDescription>
                    Connect your wallet to proceed with payment.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </div>
        )}

        {step === 'confirm' && (
          <div className="space-y-6">
            <div className="space-y-4">
              <div>
                <Label className="text-sm font-medium">Your Request</Label>
                <div className="mt-1 p-3 bg-muted/50 rounded-md text-sm">
                  {requestData}
                </div>
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Total Cost</p>
                  <p className="text-sm text-muted-foreground">
                    Payment will be held in escrow until completion
                  </p>
                </div>
                <p className="text-xl font-bold text-primary">
                  {formatPrice(agent.pricing.price)}
                </p>
              </div>
            </div>

            <Alert>
              <Shield className="h-4 w-4" />
              <AlertDescription>
                Your payment is protected by smart contract escrow. Funds are only released when you approve the completed work.
              </AlertDescription>
            </Alert>
          </div>
        )}

        {step === 'processing' && (
          <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <div className="text-center">
              <p className="font-medium">Creating service request...</p>
              <p className="text-sm text-muted-foreground">
                This may take a few seconds
              </p>
            </div>
          </div>
        )}

        {step === 'success' && (
          <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <CheckCircle className="h-12 w-12 text-green-500" />
            <div className="text-center">
              <p className="font-medium">Request submitted successfully!</p>
              <p className="text-sm text-muted-foreground">
                {agent.name} will start working on your request. You'll receive updates in your dashboard.
              </p>
            </div>
          </div>
        )}

        <DialogFooter>
          {step === 'details' && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              {connected ? (
                <Button onClick={handleSubmit} disabled={!requestData.trim()}>
                  Continue
                </Button>
              ) : (
                <WalletMultiButton className="!bg-primary hover:!bg-primary/90 !rounded-md !h-9 !px-4 !text-sm" />
              )}
            </>
          )}

          {step === 'confirm' && (
            <>
              <Button variant="outline" onClick={() => setStep('details')}>
                Back
              </Button>
              <Button onClick={handleConfirm} disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  `Pay ${formatPrice(agent.pricing.price)}`
                )}
              </Button>
            </>
          )}

          {step === 'processing' && (
            <Button disabled className="w-full">
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Processing...
            </Button>
          )}

          {step === 'success' && (
            <Button onClick={handleClose} className="w-full">
              Close
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}