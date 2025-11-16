import { Pool } from 'pg'

const connectionString = process.env.DATABASE_URL

async function main() {
  console.log('🧪 Testing AgentMarket database connection...')
  
  if (!connectionString) {
    console.error('❌ DATABASE_URL is not set')
    process.exit(1)
  }

  const pool = new Pool({
    connectionString,
    ssl: { rejectUnauthorized: false },
  })

  try {
    const client = await pool.connect()
    const result = await client.query('SELECT NOW() as now')
    console.log('✅ Database connection successful!')
    console.log('   Server time:', result.rows[0].now)

    // List tables
    const tables = await client.query(
      "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
    )
    console.log('\n📊 Available tables:', (tables.rows as any[]).map(r => r.table_name).join(', '))

    client.release()
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err)
    console.error('❌ Connection failed:', errMsg)
    process.exit(1)
  } finally {
    await pool.end()
  }
}

main().catch(console.error)
