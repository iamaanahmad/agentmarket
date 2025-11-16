import { NextRequest, NextResponse } from 'next/server'
import { createPool } from '@/lib/db'
import { validationError, databaseError } from '@/lib/api-error'

export async function GET(request: NextRequest) {
  const pool = createPool()
  let client

  try {
    const searchParams = request.nextUrl.searchParams
    const page = Math.max(1, parseInt(searchParams.get('page') || '1'))
    const limit = Math.min(50, parseInt(searchParams.get('limit') || '10'))
    const search = searchParams.get('search') || ''
    const offset = (page - 1) * limit

    client = await pool.connect()

    let query = `
      SELECT 
        a.id, a.agent_id, a.name, a.description, a.capabilities, a.pricing,
        a.endpoint, a.creator_wallet, a.active, a.created_at,
        COALESCE(AVG(r.stars), 0)::float as avg_rating,
        COUNT(r.id) as rating_count
      FROM agents a
      LEFT JOIN ratings r ON a.agent_id = r.agent_id
      WHERE a.active = true
    `

    const params: any[] = []
    if (search) {
      query += ` AND (a.name ILIKE $1 OR a.description ILIKE $1)`
      params.push(`%${search}%`)
    }

    query += ` GROUP BY a.id ORDER BY a.created_at DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`
    params.push(limit, offset)

    const result = await client.query(query, params)

    let countQuery = 'SELECT COUNT(*) as total FROM agents WHERE active = true'
    if (search) {
      countQuery += ` AND (name ILIKE $1 OR description ILIKE $1)`
    }
    const countResult = await client.query(countQuery, search ? [`%${search}%`] : [])
    const total = parseInt((countResult.rows[0] as any).total)

    return NextResponse.json({
      agents: result.rows.map((row: any) => ({
        id: row.id,
        agentId: row.agent_id,
        name: row.name,
        description: row.description,
        capabilities: row.capabilities || [],
        pricing: row.pricing || {},
        endpoint: row.endpoint,
        creatorWallet: row.creator_wallet,
        rating: {
          average: parseFloat(row.avg_rating) || 0,
          count: parseInt(row.rating_count) || 0,
        },
        createdAt: row.created_at,
      })),
      pagination: { page, limit, total, pages: Math.ceil(total / limit) },
    })
  } catch (error: unknown) {
    return databaseError('GET /api/agents', error)
  } finally {
    if (client) client.release()
    await pool.end()
  }
}

export async function POST(request: NextRequest) {
  const pool = createPool({ max: 5 })
  let client

  try {
    const body = await request.json()
    const { name, description, capabilities, pricing, endpoint, creatorWallet } = body

    // Validation
    if (!name?.trim()) {
      return validationError('Agent name is required', 'POST /api/agents')
    }
    if (!creatorWallet?.trim()) {
      return validationError('Creator wallet address is required', 'POST /api/agents')
    }

    client = await pool.connect()
    const agentId = `agent-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`

    const result = await client.query(
      `INSERT INTO agents (agent_id, name, description, capabilities, pricing, endpoint, creator_wallet, active)
       VALUES ($1, $2, $3, $4, $5, $6, $7, true) RETURNING *`,
      [
        agentId,
        name,
        description || '',
        JSON.stringify(capabilities || []),
        JSON.stringify(pricing || { price: 0, currency: 'SOL' }),
        endpoint || '',
        creatorWallet,
      ]
    )

    const agent = result.rows[0] as any

    return NextResponse.json({
      success: true,
      agent: { id: agent.id, agentId: agent.agent_id, name: agent.name, createdAt: agent.created_at },
      message: 'Agent registered successfully',
    })
  } catch (error: unknown) {
    return databaseError('POST /api/agents', error)
  } finally {
    if (client) client.release()
    await pool.end()
  }
}
