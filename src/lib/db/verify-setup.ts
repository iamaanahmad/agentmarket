import { Pool } from 'pg'

async function main() {
  console.log('🧪 Testing AgentMarket RDS connection...\n')
  
  const pool = new Pool({
    host: 'agentmarket-dev-db.c76o0iokgzxb.ap-south-1.rds.amazonaws.com',
    port: 5432,
    user: 'agentadmin',
    password: 'AgentMarket2025Secure',
    database: 'agentmarket_dev',
    ssl: { rejectUnauthorized: false },
  })

  try {
    const client = await pool.connect()
    console.log('✅ Connected to RDS')

    // Server time
    const timeRes = await client.query('SELECT NOW() as now')
    console.log('📅 Server time:', (timeRes.rows[0] as any).now)

    // List tables
    const tables = await client.query(
      "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
    )
    console.log('\n📊 Tables:', (tables.rows as any[]).map(r => r.table_name).join(', '))

    // Count data
    const agents = await client.query('SELECT COUNT(*) as count FROM agents')
    const users = await client.query('SELECT COUNT(*) as count FROM users')
    const requests = await client.query('SELECT COUNT(*) as count FROM service_requests')

    console.log('\n📈 Data:')
    console.log(`   Agents: ${(agents.rows[0] as any).count}`)
    console.log(`   Users: ${(users.rows[0] as any).count}`)
    console.log(`   Requests: ${(requests.rows[0] as any).count}`)

    // Sample agent
    const agentRes = await client.query('SELECT * FROM agents LIMIT 1')
    if ((agentRes.rows as any[]).length > 0) {
      const agent = (agentRes.rows[0] as any)
      console.log('\n🤖 Sample Agent:')
      console.log(`   Name: ${agent.name}`)
      console.log(`   ID: ${agent.agent_id}`)
      console.log(`   Active: ${agent.active}`)
    }

    client.release()
    console.log('\n✅ All tests passed!')
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err)
    console.error('❌ Test failed:', errMsg)
    process.exit(1)
  } finally {
    await pool.end()
  }
}

main().catch(console.error)
