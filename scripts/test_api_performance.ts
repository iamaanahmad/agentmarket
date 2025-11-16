/**
 * API Performance Testing Script
 * 
 * Tests response times for all API endpoints to ensure:
 * - GET requests < 500ms (95th percentile)
 * - POST requests < 1s (95th percentile)
 * 
 * Usage: npx ts-node scripts/test_api_performance.ts
 */

interface PerformanceResult {
  endpoint: string
  method: string
  samples: number
  min: number
  max: number
  avg: number
  p50: number
  p95: number
  p99: number
  success: boolean
}

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:3000'
const SAMPLES_PER_ENDPOINT = 20

async function measureRequest(url: string, options: RequestInit = {}): Promise<number> {
  const start = Date.now()
  try {
    const response = await fetch(url, options)
    const end = Date.now()
    
    if (!response.ok) {
      console.warn(`Request failed: ${response.status} ${response.statusText}`)
    }
    
    return end - start
  } catch (error) {
    console.error(`Request error: ${error}`)
    return -1
  }
}

function calculatePercentile(values: number[], percentile: number): number {
  const sorted = values.filter(v => v > 0).sort((a, b) => a - b)
  if (sorted.length === 0) return 0
  
  const index = Math.ceil((percentile / 100) * sorted.length) - 1
  return sorted[index]
}

function analyzeResults(times: number[]): Omit<PerformanceResult, 'endpoint' | 'method' | 'success'> {
  const validTimes = times.filter(t => t > 0)
  
  return {
    samples: validTimes.length,
    min: Math.min(...validTimes),
    max: Math.max(...validTimes),
    avg: validTimes.reduce((a, b) => a + b, 0) / validTimes.length,
    p50: calculatePercentile(validTimes, 50),
    p95: calculatePercentile(validTimes, 95),
    p99: calculatePercentile(validTimes, 99),
  }
}

async function testEndpoint(
  endpoint: string,
  method: string,
  options: RequestInit = {}
): Promise<PerformanceResult> {
  console.log(`\nTesting ${method} ${endpoint}...`)
  
  const times: number[] = []
  
  for (let i = 0; i < SAMPLES_PER_ENDPOINT; i++) {
    const time = await measureRequest(`${API_BASE_URL}${endpoint}`, {
      method,
      ...options,
    })
    times.push(time)
    
    // Small delay between requests to avoid overwhelming the server
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  
  const stats = analyzeResults(times)
  
  // Determine success based on requirements
  const threshold = method === 'GET' ? 500 : 1000
  const success = stats.p95 < threshold
  
  const result: PerformanceResult = {
    endpoint,
    method,
    ...stats,
    success,
  }
  
  console.log(`  Min: ${stats.min}ms | Max: ${stats.max}ms | Avg: ${stats.avg.toFixed(0)}ms`)
  console.log(`  P50: ${stats.p50}ms | P95: ${stats.p95}ms | P99: ${stats.p99}ms`)
  console.log(`  Status: ${success ? '✅ PASS' : '❌ FAIL'} (P95 ${success ? '<' : '>='} ${threshold}ms)`)
  
  return result
}

async function runPerformanceTests() {
  console.log('='.repeat(60))
  console.log('API Performance Testing')
  console.log('='.repeat(60))
  console.log(`Base URL: ${API_BASE_URL}`)
  console.log(`Samples per endpoint: ${SAMPLES_PER_ENDPOINT}`)
  console.log(`Requirements: GET < 500ms (P95), POST < 1s (P95)`)
  
  const results: PerformanceResult[] = []
  
  // Test GET /api/agents (list agents)
  results.push(await testEndpoint('/api/agents?page=1&limit=10', 'GET'))
  
  // Test GET /api/agents with search
  results.push(await testEndpoint('/api/agents?page=1&limit=10&search=test', 'GET'))
  
  // Test POST /api/agents (register agent)
  results.push(await testEndpoint('/api/agents', 'POST', {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: `Test Agent ${Date.now()}`,
      description: 'Performance test agent',
      capabilities: ['test'],
      pricing: { price: 1000000, currency: 'SOL' },
      endpoint: 'https://example.com/webhook',
      creatorWallet: 'TestWallet123456789',
    }),
  }))
  
  // Test GET /api/requests (list requests)
  results.push(await testEndpoint('/api/requests?page=1&limit=20', 'GET'))
  
  // Test GET /api/requests with filters
  results.push(await testEndpoint('/api/requests?userWallet=test&status=pending', 'GET'))
  
  // Test GET /api/security/scan (scan history)
  results.push(await testEndpoint('/api/security/scan?page=1&limit=20', 'GET'))
  
  // Test GET /api/security/scan with filters
  results.push(await testEndpoint('/api/security/scan?riskLevel=DANGER', 'GET'))
  
  // Summary
  console.log('\n' + '='.repeat(60))
  console.log('Performance Test Summary')
  console.log('='.repeat(60))
  
  const passed = results.filter(r => r.success).length
  const failed = results.filter(r => !r.success).length
  
  console.log(`\nTotal Tests: ${results.length}`)
  console.log(`Passed: ${passed} ✅`)
  console.log(`Failed: ${failed} ❌`)
  
  if (failed > 0) {
    console.log('\nFailed Tests:')
    results.filter(r => !r.success).forEach(r => {
      const threshold = r.method === 'GET' ? 500 : 1000
      console.log(`  ${r.method} ${r.endpoint}: P95=${r.p95}ms (threshold: ${threshold}ms)`)
    })
  }
  
  // Export results to JSON
  const fs = require('fs')
  fs.writeFileSync(
    'performance_test_results.json',
    JSON.stringify({ timestamp: new Date().toISOString(), results }, null, 2)
  )
  
  console.log('\nResults saved to: performance_test_results.json')
  
  // Exit with error code if any tests failed
  process.exit(failed > 0 ? 1 : 0)
}

// Run tests
runPerformanceTests().catch(error => {
  console.error('Performance test failed:', error)
  process.exit(1)
})
