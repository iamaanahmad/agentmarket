'use client'

import { useState, useEffect } from 'react'
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
  BookOpen
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
  const [isScanning, setIsScanning] = useState(false)
  const [scanResult, setScanResult] = useState<RiskAnalysis | null>(null)
  const [currentView, setCurrentView] = useState<'scanner' | 'history' | 'chat' | 'dashboard' | 'education'>('scanner')
  const [isMobile, setIsMobile] = useState(false)

  // Check for mobile device
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const handleTransactionSubmit = async (data: string, type?: 'paste' | 'file' | 'wallet' | 'qr' | 'camera') => {
    setIsScanning(true)
    setScanResult(null)
    
    // Simulate API call to SecurityGuard AI
    try {
      // Simulate different scan results based on input type and content
      await new Promise(resolve => setTimeout(resolve, 3000))
      
      // Mock scan result with comprehensive data
      const mockResult: RiskAnalysis = {
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
      }
      
      setScanResult(mockResult)
    } catch (error) {
      console.error('Scan failed:', error)
    } finally {
      setIsScanning(false)
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

            {/* Pricing Info */}
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
                  <div>
                    <p className="font-medium text-red-800">Scan Cost</p>
                    <p className="text-sm text-red-600">
                      Pay per scan, no subscription
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold text-red-600">0.01 SOL</p>
                    <p className="text-xs text-red-600">~$2 per scan</p>
                  </div>
                </div>
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