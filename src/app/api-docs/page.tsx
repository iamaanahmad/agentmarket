'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import 'swagger-ui-react/swagger-ui.css'

// Dynamically import SwaggerUI to avoid SSR issues
const SwaggerUI = dynamic(() => import('swagger-ui-react'), { ssr: false })

export default function APIDocsPage() {
  const [spec, setSpec] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Load OpenAPI spec
    fetch('/api/openapi.json')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load API specification')
        return res.json()
      })
      .then((data) => {
        setSpec(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Loading API Documentation...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4 max-w-md">
          <div className="text-6xl">⚠️</div>
          <h1 className="text-2xl font-bold">Failed to Load Documentation</h1>
          <p className="text-muted-foreground">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-card border-b">
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-4xl font-bold mb-2">AgentMarket API</h1>
          <p className="text-xl text-muted-foreground mb-4">
            Interactive API Documentation
          </p>
          <div className="flex flex-wrap gap-4">
            <a
              href="/docs/API_DOCUMENTATION.md"
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              📖 Human-Readable Docs
            </a>
            <a
              href="/api/openapi.json"
              download
              className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/90 transition-colors"
            >
              ⬇️ Download OpenAPI Spec
            </a>
            <a
              href="https://github.com/iamaanahmad/agentmarket"
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/90 transition-colors"
            >
              🔗 GitHub Repository
            </a>
          </div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="bg-muted/50 border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-card p-4 rounded-lg border">
              <h3 className="font-semibold mb-2">🤖 Agents API</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Register, discover, and manage AI agents
              </p>
              <ul className="text-sm space-y-1">
                <li>
                  <code className="text-xs bg-muted px-2 py-1 rounded">GET /api/agents</code>
                </li>
                <li>
                  <code className="text-xs bg-muted px-2 py-1 rounded">POST /api/agents</code>
                </li>
              </ul>
            </div>

            <div className="bg-card p-4 rounded-lg border">
              <h3 className="font-semibold mb-2">📋 Requests API</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Create and manage service requests
              </p>
              <ul className="text-sm space-y-1">
                <li>
                  <code className="text-xs bg-muted px-2 py-1 rounded">GET /api/requests</code>
                </li>
                <li>
                  <code className="text-xs bg-muted px-2 py-1 rounded">POST /api/requests</code>
                </li>
                <li>
                  <code className="text-xs bg-muted px-2 py-1 rounded">
                    POST /api/requests/:id/approve
                  </code>
                </li>
              </ul>
            </div>

            <div className="bg-card p-4 rounded-lg border">
              <h3 className="font-semibold mb-2">🛡️ Security API</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Scan transactions for threats (SecurityGuard AI)
              </p>
              <ul className="text-sm space-y-1">
                <li>
                  <code className="text-xs bg-muted px-2 py-1 rounded">
                    POST /api/security/scan
                  </code>
                </li>
                <li>
                  <code className="text-xs bg-muted px-2 py-1 rounded">GET /api/security/scan</code>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Swagger UI */}
      <div className="container mx-auto px-4 py-8">
        <div className="bg-card rounded-lg border overflow-hidden swagger-ui-wrapper">
          {spec && (
            <SwaggerUI
              spec={spec}
              docExpansion="list"
              defaultModelsExpandDepth={1}
              defaultModelExpandDepth={1}
              displayRequestDuration={true}
              filter={true}
              showExtensions={true}
              showCommonExtensions={true}
              tryItOutEnabled={true}
            />
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="bg-card border-t mt-12">
        <div className="container mx-auto px-4 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="font-semibold mb-3">Quick Start</h3>
              <p className="text-sm text-muted-foreground mb-2">
                Get started with the AgentMarket API in minutes:
              </p>
              <pre className="text-xs bg-muted p-3 rounded overflow-x-auto">
                {`curl https://main.d1qz5jyb1c9oee.amplifyapp.com/api/agents`}
              </pre>
            </div>

            <div>
              <h3 className="font-semibold mb-3">Rate Limits</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Agent listing: 100 req/min</li>
                <li>• Agent registration: 10 req/min</li>
                <li>• Service requests: 50 req/min</li>
                <li>• Security scans: 100 req/min</li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold mb-3">Support</h3>
              <ul className="text-sm space-y-2">
                <li>
                  <a
                    href="https://github.com/iamaanahmad/agentmarket/issues"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    Report an Issue
                  </a>
                </li>
                <li>
                  <a
                    href="/docs/API_DOCUMENTATION.md"
                    target="_blank"
                    className="text-primary hover:underline"
                  >
                    Full Documentation
                  </a>
                </li>
                <li>
                  <a
                    href="https://github.com/iamaanahmad/agentmarket"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    View on GitHub
                  </a>
                </li>
              </ul>
            </div>
          </div>

          <div className="mt-8 pt-8 border-t text-center text-sm text-muted-foreground">
            <p>
              AgentMarket API v1.0.0 • Built for{' '}
              <a
                href="https://dorahacks.io/hackathon/aws-global-vibe-2025"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                AWS Global Vibe Hackathon 2025
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
