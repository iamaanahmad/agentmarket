import { Pool } from 'pg'
import * as fs from 'fs'
import * as path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const RDS_ENDPOINT = 'agentmarket-dev-db.c76o0iokgzxb.ap-south-1.rds.amazonaws.com'
const RDS_PORT = 5432
const RDS_USER = 'agentadmin'
const RDS_PASSWORD = 'AgentMarket2025Secure'
const DB_NAME = 'agentmarket_dev'

async function seedDatabase() {
  const pool = new Pool({
    host: RDS_ENDPOINT,
    port: RDS_PORT,
    user: RDS_USER,
    password: RDS_PASSWORD,
    database: DB_NAME,
    ssl: { rejectUnauthorized: false },
  })

  try {
    console.log('🔗 Connecting to agentmarket_dev database...')
    const client = await pool.connect()
    console.log('✅ Connected')

    // Read and execute seed.sql
    const seedPath = path.join(__dirname, 'seed.sql')
    const seed = fs.readFileSync(seedPath, 'utf-8')
    
    console.log('\n🌱 Running seed.sql...')
    await client.query(seed)
    console.log('✅ Seed data inserted successfully')

    // Verify data
    const agents = await client.query('SELECT COUNT(*) as count FROM agents')
    const users = await client.query('SELECT COUNT(*) as count FROM users')
    const requests = await client.query('SELECT COUNT(*) as count FROM service_requests')
    const ratings = await client.query('SELECT COUNT(*) as count FROM ratings')

    console.log('\n📊 Data summary:')
    console.log(`   Users: ${(users.rows[0] as any).count}`)
    console.log(`   Agents: ${(agents.rows[0] as any).count}`)
    console.log(`   Requests: ${(requests.rows[0] as any).count}`)
    console.log(`   Ratings: ${(ratings.rows[0] as any).count}`)

    client.release()
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err)
    console.error('❌ Error seeding database:', errMsg)
    process.exit(1)
  } finally {
    await pool.end()
  }

  console.log('\n✅ Database seeding complete!')
}

seedDatabase().catch(console.error)
