# Database Setup (dev)

This file explains how to finish provisioning the AWS RDS instance and connect the Next.js app to it.

1) AWS Credentials (on your local machine)

In PowerShell run:

```powershell
aws configure
# Enter your AWS Access Key ID, Secret Access Key, default region (e.g. us-east-1) and default output (json)
```

2) RDS creation (✅ COMPLETED)

Your RDS instance has been successfully created!

**Instance Details:**
- Identifier: `agentmarket-dev-db`
- Engine: PostgreSQL 17.6
- Class: `db.t3.micro` (free tier eligible)
- Region: `ap-south-1` (Mumbai)
- Storage: 20 GB
- Publicly accessible: Yes (for dev only; restrict to your IP)
- Status: Creating (will be available in ~5 minutes)

**Credentials:**
- Master username: `agentadmin`
- Master password: `AgentMarket2025Secure`
- Port: 5432

⚠️ **Security reminder:** Rotate the password immediately and store in AWS Secrets Manager. For production, place RDS in a private VPC and access from Lambda/EC2 only.

3) Security Group / Networking

- Open port 5432 only to the IPs you trust (or to your VPC). If using public access for dev, consider limiting it to your current IP with the AWS Console.
- If you run into VPC/subnet errors, create an RDS subnet group that includes at least two subnets in different AZs.

4) Setting `DATABASE_URL` in Next.js

Once the RDS instance is available (check AWS Console → RDS Instances), you'll see the endpoint. It looks like:
`agentmarket-dev-db.c3kqxjvz9qwz.ap-south-1.rds.amazonaws.com`

Set an environment variable in your local `.env.local` (Next.js) or in your deployment environment:

```
DATABASE_URL=postgres://agentadmin:AgentMarket2025Secure@agentmarket-dev-db.c3kqxjvz9qwz.ap-south-1.rds.amazonaws.com:5432/agentmarket_dev
```

Replace the endpoint with your actual RDS endpoint from the AWS Console.

5) Create the database and run schema (once RDS is available)

Once the RDS instance is in "Available" state in the AWS Console, create the initial database:

```powershell
# First, create the database if it doesn't exist
psql "postgres://agentadmin:AgentMarket2025Secure@agentmarket-dev-c3kqxjvz9qwz.ap-south-1.rds.amazonaws.com:5432/postgres" -c "CREATE DATABASE agentmarket_dev;"
```

Then run the schema to create tables:

```powershell
psql "postgres://agentadmin:AgentMarket2025Secure@agentmarket-dev-c3kqxjvz9qwz.ap-south-1.rds.amazonaws.com:5432/agentmarket_dev" -f src/lib/db/schema.sql
```

6) Seed initial data (optional, for testing)

```powershell
psql "postgres://agentadmin:AgentMarket2025Secure@agentmarket-dev-c3kqxjvz9qwz.ap-south-1.rds.amazonaws.com:5432/agentmarket_dev" -f src/lib/db/seed.sql
```

This will insert sample agents, users, requests, and ratings for testing the API.

7) Next steps

Update your `.env.local` with `DATABASE_URL`, then install the `pg` package:

```powershell
npm install pg
npm install -D @types/node @types/pg
```

Test the connection from Next.js:

```powershell
# Create a simple route to test, or run directly:
npm install -D ts-node
npx ts-node src/lib/db/test-connection.ts
```

You should see:
```
✅ Database connection successful!
📊 Available tables: users, agents, service_requests, ratings, analytics_events
```

8) Alternative (faster): Supabase

If you prefer a managed hosted Postgres with instant setup, Supabase offers a free tier. Just sign up, create a project, and use the connection string instead of `DATABASE_URL`.

## Quick Reference

**Check RDS Status:**
```powershell
aws rds describe-db-instances --db-instance-identifier agentmarket-dev-db --region ap-south-1
```

**Update Security Group to allow your IP:**
```powershell
aws ec2 authorize-security-group-ingress --group-id sg-0e2fa07271c6f98d8 --protocol tcp --port 5432 --cidr YOUR_IP/32 --region ap-south-1
```

**Connect directly from psql (once available):**
```powershell
psql "postgres://agentadmin:AgentMarket2025Secure@agentmarket-dev.c3kqxjvz9qwz.ap-south-1.rds.amazonaws.com:5432/agentmarket_dev"
```

**Next phase: Backend API Routes**

Once DATABASE_URL is set and connection tested, proceed to create the first API endpoint:
- `src/app/api/agents/route.ts` - GET agents, POST register agent
- Uses `src/lib/db/client.ts` to query database
- Uses `src/lib/solana/program.ts` to call smart contracts


