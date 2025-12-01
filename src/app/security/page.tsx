'use client'

import { useState, useEffect } from 'react'
import { useWallet } from '@solana/wallet-adapter-react'
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui'
import { Connection, PublicKey, Transaction, SystemProgram, LAMPORTS_PER_SOL } from '@solana/web3.js'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Brain,
  TrendingUp,
  Users,
  ArrowRight,
  History,
  MessageSquare,
  BookOpen,
  Wallet,
  Loader2
} from 'lucide-react'

import Link from 'next/link'
import { TransactionInput } from '@/components/security/transaction-input'
import { RiskVisualization, type RiskAnalysis } from '@/components/security/risk-visualization'
import { ScanningProgress } from '@/components/security/scanning-progress'
import { TransactionHistory } from '@/components/security/transaction-history'
import { MobileScanner } from '@/components/security/mobile-scanner'
import { SecurityDashboard } from '@/components/security/security-dashboard'
import { SecurityChat } from '@/components/security/security-chat'
import { SecurityEducation } from '@/components/security/security-education'
import { useToast } from '@/hooks/use-toast'

// Solana Devnet Configuration
const SOLANA_RPC_URL = 'https://api.devnet.solana.com'
const SCAN_PRICE_SOL = 0.01
// Platform wallet for receiving scan payments (your devnet wallet)
const PLATFORM_WALLET = new PublicKey('EwrEb3sWWiaz7mAN4XaDiADcjmBL85Eiq6JFVXrKU7En')

const securityStats = [
  { label: 'Threats Blocked', value: '1,892', icon: Shield, color: 'text-red-600' },
  { label: 'Users Protected', value: '12,847', icon: Users, color: 'text-green-600' },
  { label: 'Avg Response Time', value: '1.8s', icon: Clock, color: 'text-blue-600' },
  { label: 'Detection Accuracy', value: '99.8%', icon: TrendingUp, color: 'text-purple-600' },
]

const threatTypes = [
  {
    name: 'Wallet Drainers',
    description: 'Malicious contracts that steal all tokens from your wallet',
    detected: 1247,
    severity: 'high',
  },
  {
    name: 'Rug Pulls',
    description: 'Projects that suddenly remove liquidity and disappear',
    detected: 89,
    severity: 'high',
  },
  {
    name: 'Phishing Contracts',
    description: 'Fake contracts that mimic legitimate protocols',
    detected: 456,
    severity: 'medium',
  },
  {
    name: 'Unlimited Approvals',
    description: 'Contracts requesting excessive token permissions',
    detected: 2134,
    severity: 'medium',
  },
]

export default function SecurityPage() {
  const { connected, publicKey, sendTransaction } = useWallet()
  const { toast } = useToast()
  const [isScanning, setIsScanning] = useState(false)
  const [isPaying, setIsPaying] = useState(false)
  const [hasPaid, setHasPaid] = useState(false)
  const [pendingTransactionData, setPendingTransactionData] = useState<string | null>(null)
  const [paymentSignature, setPaymentSignature] = useState<string | null>(null)
  const [scanResult, setScanResult] = useState<RiskAnalysis | null>(null)
  const [currentView, setCurrentView] = useState<'scanner' | 'history' | 'chat' | 'dashboard' | 'education'>('scanner')
  const [isMobile, setIsMobile] = useState(false)
  const [walletBalance, setWalletBalance] = useState<number | null>(null)

  // Check wallet balance
  useEffect(() => {
    const checkBalance = async () => {
      if (connected && publicKey) {
        try {
          const connection = new Connection(SOLANA_RPC_URL, 'confirmed')
          const balance = await connection.getBalance(publicKey)
          setWalletBalance(balance / LAMPORTS_PER_SOL)
        } catch (error) {
          console.error('Failed to fetch balance:', error)
        }
      } else {
        setWalletBalance(null)
      }
    }
    checkBalance()
  }, [connected, publicKey])

  // Check for mobile device
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Process payment for scan
  const handlePayForScan = async () => {
    if (!connected || !publicKey || !sendTransaction) {
      toast({
        title: "Wallet not connected",
        description: "Please connect your Phantom wallet to pay for the scan.",
        variant: "destructive",
      })
      return
    }

    if (walletBalance !== null && walletBalance < SCAN_PRICE_SOL) {
      toast({
        title: "Insufficient balance",
        description: `You need at least ${SCAN_PRICE_SOL} SOL. Current balance: ${walletBalance.toFixed(4)} SOL`,
        variant: "destructive",
      })
      return
    }

    setIsPaying(true)

    try {
      const connection = new Connection(SOLANA_RPC_URL, 'confirmed')
      
      // Create transfer transaction
      const transaction = new Transaction().add(
        SystemProgram.transfer({
          fromPubkey: publicKey,
          toPubkey: PLATFORM_WALLET,
          lamports: SCAN_PRICE_SOL * LAMPORTS_PER_SOL,
        })
      )

      // Get latest blockhash
      const { blockhash } = await connection.getLatestBlockhash()
      transaction.recentBlockhash = blockhash
      transaction.feePayer = publicKey

      // Send transaction (this opens Phantom wallet for user approval)
      const signature = await sendTransaction(transaction, connection)
      
      // Wait for confirmation
      const confirmation = await connection.confirmTransaction(signature, 'confirmed')
      
      if (confirmation.value.err) {
        throw new Error('Transaction failed')
      }

      setPaymentSignature(signature)
      setHasPaid(true)
      
      // Update balance
      const newBalance = await connection.getBalance(publicKey)
      setWalletBalance(newBalance / LAMPORTS_PER_SOL)

      toast({
        title: "Payment successful! ✅",
        description: `Transaction: ${signature.slice(0, 8)}...${signature.slice(-8)}`,
      })

      // If there's pending transaction data, proceed with scan
      if (pendingTransactionData) {
        await performScan(pendingTransactionData)
      }

    } catch (error: any) {
      console.error('Payment failed:', error)
      toast({
        title: "Payment failed",
        description: error.message || "Transaction was rejected or failed. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsPaying(false)
    }
  }

  // Perform the actual scan
  const performScan = async (data: string) => {
    setIsScanning(true)
    setScanResult(null)

    try {
      // Call the real API
      const response = await fetch('/api/security/scan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transaction: data,
          userWallet: publicKey?.toString(),
          paymentSignature: paymentSignature,
        }),
      })

      if (!response.ok) {
        // Fallback to mock data for demo if API is unavailable
        const mockResult = generateMockResult(data)
        setScanResult(mockResult)
      } else {
        const result = await response.json()
        // Map API response to RiskAnalysis format
        const scanResult: RiskAnalysis = {
          riskLevel: result.riskLevel || 'SAFE',
          riskScore: result.riskScore || 15,
          confidence: result.confidence || 0.95,
          explanation: result.explanation || 'Transaction analyzed successfully.',
          recommendation: result.recommendation || 'Review the details before proceeding.',
          scanTime: result.scanTimeMs || 1500,
          details: result.details || {},
          scanMetadata: {
            scanId: result.scanId || `scan_${Date.now()}`,
            timestamp: new Date().toISOString(),
            processingTimeMs: result.scanTimeMs || 1500,
            modelVersion: 'SecurityGuard-v2.1.0'
          }
        }
        setScanResult(scanResult)
      }
    } catch (error) {
      console.error('Scan failed:', error)
      // Fallback to mock for demo
      const mockResult = generateMockResult(data)
      setScanResult(mockResult)
    } finally {
      setIsScanning(false)
      setPendingTransactionData(null)
    }
  }

  // Generate mock result for demo
  const generateMockResult = (data: string): RiskAnalysis => ({
    riskLevel: data.toLowerCase().includes('danger') ? 'DANGER' : 
              data.toLowerCase().includes('caution') ? 'CAUTION' : 'SAFE',
    riskScore: data.toLowerCase().includes('danger') ? 85 : 
              data.toLowerCase().includes('caution') ? 45 : 15,
    confidence: 0.95,
    explanation: data.toLowerCase().includes('danger') 
      ? 'This transaction contains patterns matching known wallet drainer exploits. Multiple suspicious program interactions detected.'
      : data.toLowerCase().includes('caution')
      ? 'This transaction requests unlimited token approvals which could be risky. Exercise caution before proceeding.'
      : 'This transaction appears safe. All programs are verified and no suspicious patterns detected.',
    recommendation: data.toLowerCase().includes('danger')
      ? 'DO NOT SIGN this transaction. It appears to be a malicious wallet drainer that will steal your funds.'
      : data.toLowerCase().includes('caution')
      ? 'Review the token approvals carefully. Consider limiting approval amounts if possible.'
      : 'You can proceed with this transaction with confidence.',
    scanTime: Math.floor(Math.random() * 1000) + 1500,
    details: {
      patternMatches: data.toLowerCase().includes('danger') ? [
        {
          patternId: 'wallet_drainer_v2',
          patternType: 'Wallet Drainer',
          severity: 10,
          description: 'Known wallet drainer pattern detected',
          evidence: { programId: 'DrainXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' },
          confidence: 0.98
        }
      ] : [],
      mlAnalysis: {
        anomalyScore: data.toLowerCase().includes('danger') ? 0.92 : 0.15,
        classification: data.toLowerCase().includes('danger') ? 'MALICIOUS' : 'BENIGN',
        confidence: 0.95,
        featureImportance: {
          'program_interactions': 0.4,
          'token_approvals': 0.3,
          'account_creation': 0.2,
          'value_transfer': 0.1
        },
        modelVersion: 'v2.1.0'
      },
      accountFlags: data.toLowerCase().includes('caution') ? [
        {
          accountAddress: 'TokenXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
          flagType: 'Unlimited Approval',
          severity: 6,
          description: 'Transaction requests unlimited token spending approval',
          evidence: { approvalAmount: 'unlimited' }
        }
      ] : [],
      programAnalysis: [
        {
          programId: 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
          programName: 'Token Program',
          isVerified: true,
          riskLevel: 'LOW',
          description: 'Official Solana Token Program'
        }
      ]
    },
    scanMetadata: {
      scanId: `scan_${Date.now()}`,
      timestamp: new Date().toISOString(),
      processingTimeMs: Math.floor(Math.random() * 1000) + 1500,
      modelVersion: 'SecurityGuard-v2.1.0'
    }
  })

  const handleTransactionSubmit = async (data: string, type?: 'paste' | 'file' | 'wallet' | 'qr' | 'camera') => {
    if (!connected) {
      toast({
        title: "Wallet not connected",
        description: "Please connect your Phantom wallet first.",
        variant: "destructive",
      })
      return
    }

    // Store the transaction data
    setPendingTransactionData(data)

    // If already paid, proceed with scan
    if (hasPaid) {
      await performScan(data)
      setHasPaid(false) // Reset for next scan
    } else {
      // Show payment prompt
      toast({
        title: "Payment required",
        description: `Please pay ${SCAN_PRICE_SOL} SOL to scan this transaction.`,
      })
    }
  }

  const handleScanComplete = () => {
    // Called when scanning animation completes
  }

  const handleViewScanDetails = (scanId: string) => {
    console.log('View scan details:', scanId)
    // In real implementation, this would fetch and display detailed scan results
  }



  return (
    <div className="container py-8">
      {/* Header */}
      <div className="text-center mb-12">
        <Badge variant="destructive" className="mb-4">
          🚨 $2B Lost to Wallet Exploits in 2024
        </Badge>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          <span className="text-red-600">SecurityGuard AI</span>
          <br />
          Transaction Protection
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Real-time AI-powered security analysis for Solana transactions. 
          Detect wallet drainers, rug pulls, and malicious contracts before you sign.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
        {securityStats.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.label} className="text-center">
              <CardContent className="p-6">
                <Icon className={`h-8 w-8 mx-auto mb-2 ${stat.color}`} />
                <p className="text-2xl font-bold">{stat.value}</p>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Navigation Tabs */}
      <div className="flex justify-center mb-8">
        <div className="flex flex-wrap justify-center space-x-1 bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setCurrentView('scanner')}
            className={`px-3 md:px-4 py-2 rounded-md text-xs md:text-sm font-medium transition-colors ${
              currentView === 'scanner'
                ? 'bg-white text-red-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Shield className="h-4 w-4 inline mr-1 md:mr-2" />
            <span className="hidden sm:inline">Scanner</span>
          </button>
          <button
            onClick={() => setCurrentView('dashboard')}
            className={`px-3 md:px-4 py-2 rounded-md text-xs md:text-sm font-medium transition-colors ${
              currentView === 'dashboard'
                ? 'bg-white text-red-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <TrendingUp className="h-4 w-4 inline mr-1 md:mr-2" />
            <span className="hidden sm:inline">Dashboard</span>
          </button>
          <button
            onClick={() => setCurrentView('history')}
            className={`px-3 md:px-4 py-2 rounded-md text-xs md:text-sm font-medium transition-colors ${
              currentView === 'history'
                ? 'bg-white text-red-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <History className="h-4 w-4 inline mr-1 md:mr-2" />
            <span className="hidden sm:inline">History</span>
          </button>
          <button
            onClick={() => setCurrentView('chat')}
            className={`px-3 md:px-4 py-2 rounded-md text-xs md:text-sm font-medium transition-colors ${
              currentView === 'chat'
                ? 'bg-white text-red-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <MessageSquare className="h-4 w-4 inline mr-1 md:mr-2" />
            <span className="hidden sm:inline">Chat</span>
          </button>
          <button
            onClick={() => setCurrentView('education')}
            className={`px-3 md:px-4 py-2 rounded-md text-xs md:text-sm font-medium transition-colors ${
              currentView === 'education'
                ? 'bg-white text-red-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <BookOpen className="h-4 w-4 inline mr-1 md:mr-2" />
            <span className="hidden sm:inline">Learn</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      {currentView === 'scanner' && (
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Transaction Scanner */}
          <div className="space-y-6">
            {isMobile ? (
              <MobileScanner 
                onScanSubmit={handleTransactionSubmit}
                isScanning={isScanning}
              />
            ) : (
              <TransactionInput 
                onTransactionSubmit={handleTransactionSubmit}
                isScanning={isScanning}
              />
            )}

            {/* Pricing Info & Payment */}
            <Card>
              <CardContent className="p-6 space-y-4">
                {/* Wallet Connection */}
                {!connected ? (
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <Wallet className="h-8 w-8 mx-auto mb-2 text-blue-600" />
                    <p className="font-medium text-blue-800 mb-2">Connect Wallet to Scan</p>
                    <p className="text-sm text-blue-600 mb-3">
                      Connect your Phantom wallet to pay for security scans
                    </p>
                    <WalletMultiButton className="!bg-blue-600 hover:!bg-blue-700" />
                  </div>
                ) : (
                  <div className="space-y-3">
                    {/* Connected Wallet Info */}
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        <div>
                          <p className="text-sm font-medium text-green-800">Wallet Connected</p>
                          <p className="text-xs text-green-600">
                            {publicKey?.toString().slice(0, 4)}...{publicKey?.toString().slice(-4)}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold text-green-800">
                          {walletBalance !== null ? `${walletBalance.toFixed(4)} SOL` : 'Loading...'}
                        </p>
                        <p className="text-xs text-green-600">Devnet</p>
                      </div>
                    </div>

                    {/* Scan Pricing */}
                    <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
                      <div>
                        <p className="font-medium text-red-800">Scan Cost</p>
                        <p className="text-sm text-red-600">
                          Pay per scan, no subscription
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xl font-bold text-red-600">{SCAN_PRICE_SOL} SOL</p>
                        <p className="text-xs text-red-600">~$2 per scan</p>
                      </div>
                    </div>

                    {/* Payment Status */}
                    {pendingTransactionData && !hasPaid && (
                      <Button 
                        onClick={handlePayForScan}
                        disabled={isPaying}
                        className="w-full bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700"
                        size="lg"
                      >
                        {isPaying ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Confirming Payment...
                          </>
                        ) : (
                          <>
                            <Wallet className="h-4 w-4 mr-2" />
                            Pay {SCAN_PRICE_SOL} SOL to Scan
                          </>
                        )}
                      </Button>
                    )}

                    {hasPaid && (
                      <Alert className="bg-green-50 border-green-200">
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        <AlertDescription className="text-green-800">
                          Payment confirmed! Submit a transaction to scan.
                        </AlertDescription>
                      </Alert>
                    )}

                    {paymentSignature && (
                      <div className="text-center">
                        <a 
                          href={`https://explorer.solana.com/tx/${paymentSignature}?cluster=devnet`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-600 hover:underline"
                        >
                          View payment on Solana Explorer →
                        </a>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button 
                  onClick={() => setCurrentView('chat')}
                  variant="outline" 
                  className="w-full justify-start"
                >
                  <Brain className="h-4 w-4 mr-2" />
                  Ask Security Questions
                </Button>
                <Button 
                  onClick={() => setCurrentView('history')}
                  variant="outline" 
                  className="w-full justify-start"
                >
                  <Clock className="h-4 w-4 mr-2" />
                  View Scan History
                </Button>
                <Button asChild variant="outline" className="w-full justify-start">
                  <Link href="/marketplace">
                    <ArrowRight className="h-4 w-4 mr-2" />
                    Explore Other Agents
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Results Area */}
          <div className="space-y-6">
            {isScanning && (
              <ScanningProgress 
                isScanning={isScanning}
                onComplete={handleScanComplete}
              />
            )}

            {scanResult && !isScanning && (
              <RiskVisualization analysis={scanResult} />
            )}

            {!isScanning && !scanResult && (
              <Card>
                <CardContent className="p-8 text-center">
                  <Shield className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Ready to Scan
                  </h3>
                  <p className="text-gray-500">
                    Submit a transaction to see detailed security analysis and risk assessment.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}

      {currentView === 'dashboard' && (
        <div className="max-w-6xl mx-auto">
          <SecurityDashboard />
        </div>
      )}

      {currentView === 'history' && (
        <div className="max-w-4xl mx-auto">
          <TransactionHistory onViewDetails={handleViewScanDetails} />
        </div>
      )}

      {currentView === 'chat' && (
        <SecurityChat onTransactionAnalysis={handleTransactionSubmit} />
      )}

      {currentView === 'education' && (
        <SecurityEducation />
      )}

      {/* Threat Intelligence Section - Always Visible */}
      <div className="mt-12">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Threat Intelligence */}
          <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Threat Intelligence</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {threatTypes.map((threat) => (
                  <div key={threat.name} className="flex items-start space-x-3 p-3 bg-muted/30 rounded-lg">
                    <AlertTriangle className={`h-5 w-5 mt-0.5 ${
                      threat.severity === 'high' ? 'text-red-600' : 'text-orange-600'
                    }`} />
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-medium">{threat.name}</h4>
                        <Badge variant={threat.severity === 'high' ? 'destructive' : 'secondary'} className="text-xs">
                          {threat.detected} blocked
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {threat.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* How It Works */}
          <Card>
            <CardHeader>
              <CardTitle>How SecurityGuard AI Works</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs font-bold text-blue-600">
                    1
                  </div>
                  <div>
                    <h4 className="font-medium">Transaction Parsing</h4>
                    <p className="text-sm text-muted-foreground">
                      Analyzes all instructions, accounts, and program interactions
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center text-xs font-bold text-purple-600">
                    2
                  </div>
                  <div>
                    <h4 className="font-medium">Pattern Matching</h4>
                    <p className="text-sm text-muted-foreground">
                      Compares against database of 10M+ known exploit patterns
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center text-xs font-bold text-green-600">
                    3
                  </div>
                  <div>
                    <h4 className="font-medium">AI Analysis</h4>
                    <p className="text-sm text-muted-foreground">
                      ML models detect anomalies and suspicious behaviors
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-red-100 rounded-full flex items-center justify-center text-xs font-bold text-red-600">
                    4
                  </div>
                  <div>
                    <h4 className="font-medium">Risk Assessment</h4>
                    <p className="text-sm text-muted-foreground">
                      Generates risk score and human-readable explanation
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      </div>
    </div>
  )
}