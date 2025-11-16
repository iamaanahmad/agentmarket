# AWS Amplify Deployment Guide - AgentMarket

## Quick Start: Deploy in 15 Minutes ⚡

This guide walks you through deploying AgentMarket to AWS Amplify with a custom domain and automatic CI/CD.

---

## Prerequisites

- ✅ GitHub account with repo pushed
- ✅ AWS Account (free tier eligible)
- ✅ Domain name (optional, but recommended)
- ✅ Your environment variables ready

---

## Step 1: Prepare Your GitHub Repository

### 1a. Push Your Code to GitHub

```bash
# If not already done
git init
git add .
git commit -m "Initial AgentMarket deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/agentmarket.git
git push -u origin main
```

### 1b. Verify amplify.yml exists in root
```bash
# Check from project root
ls -la amplify.yml
# Should show the file we created
```

---

## Step 2: Connect to AWS Amplify

### 2a. Login to AWS Console

1. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/home)
2. Click **"Create App"** → **"Deploy"**
3. Choose **"GitHub"** as source

### 2b. Authorize GitHub

1. Click **"GitHub"** option
2. Click **"Authorize AWS Amplify"**
3. Approve the authorization in GitHub
4. Select your repository: `agentmarket`
5. Select branch: `main`
6. Click **"Next"**

### 2c. Configure Build Settings

1. **App name:** `agentmarket`
2. **Environment name:** `production`
3. Leave other settings as default
4. Click **"Next"**

---

## Step 3: Configure Environment Variables

In the Amplify console, under "App settings" → "Environment variables":

Add all these variables:

```
NEXT_PUBLIC_SOLANA_NETWORK = devnet
NEXT_PUBLIC_SOLANA_RPC_ENDPOINT = https://api.devnet.solana.com
NEXT_PUBLIC_AGENT_REGISTRY_PROGRAM_ID = 8RDfVnQJiW7Nn9qbWubNUVJh6B7fmgxCY86TqjSHjTuu
NEXT_PUBLIC_MARKETPLACE_ESCROW_PROGRAM_ID = 8HQ4FBCBjf5jqCW6DNYjpAK4BGujAHD9MWH8bitVK2EV
NEXT_PUBLIC_REPUTATION_SYSTEM_PROGRAM_ID = EXvxVW73eF359VWGeCM3hV431uaFyXvKbHzKqgjYJCVY
NEXT_PUBLIC_ROYALTY_SPLITTER_PROGRAM_ID = 5VRG5k7ad2DgyMFYfZ7QCN3AJPtuoH7WiJukc8ueddHL
DATABASE_URL = postgresql://agentadmin:AgentMarket2025Secure@agentmarket-dev-db.c76o0iokgzxb.ap-south-1.rds.amazonaws.com:5432/agentmarket_dev
```

⚠️ **Important:** Database URL should be set as "Secret" for security

---

## Step 4: Deploy

1. Review all settings
2. Click **"Save and Deploy"**
3. Watch the deployment progress in Amplify console
4. Wait 5-10 minutes for the build to complete

---

## Step 5: Verify Deployment

Once deployment succeeds:

1. Go to the Amplify app console
2. Click the **URL** displayed (e.g., `https://main.xxxxx.amplifyapp.com`)
3. Test the application:
   - ✅ Homepage loads
   - ✅ Marketplace displays agents
   - ✅ Can connect wallet
   - ✅ API endpoints respond

---

## Step 6: Connect Custom Domain (Optional but Recommended)

### If you have a domain:

1. In Amplify console, click **"Domain management"**
2. Click **"Add domain"**
3. Enter your domain (e.g., `agentmarket.com`)
4. Click **"Configure domain"**
5. Update DNS records as instructed:
   - CNAME: `_xxxxx.agentmarket.com` → `_xxxxx.amplifyapp.com`
6. Wait 24-48 hours for DNS propagation

### To buy a domain:
- Use Route 53 in AWS console
- Or buy from GoDaddy, Namecheap, etc.

---

## Troubleshooting

### Build Fails: "Cannot find module"

**Solution:**
```bash
# Ensure all dependencies installed locally first
npm install

# Then test build
npm run build

# Push changes
git add .
git commit -m "Fix dependencies"
git push
```

### Build Fails: "DATABASE_URL is required"

**Solution:**
1. Check environment variables in Amplify console
2. Verify DATABASE_URL is set and not marked as "Secret" for build
3. Rebuild deployment

### Deployed App Shows Blank Page

**Solution:**
1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify environment variables loaded (check Network tab)
4. Trigger Amplify rebuild

---

## Continuous Deployment Setup

Once connected to GitHub:

1. **Automatic builds on push:** Every `git push` triggers a build
2. **Preview environments:** Create branches for testing
3. **Rollback:** Revert to previous deployments in Amplify console

---

## Post-Deployment Tasks

### 1. Update Production Config

Edit `.env.local` for production:

```dotenv
# Use mainnet for production (later)
NEXT_PUBLIC_SOLANA_NETWORK=devnet  # Keep devnet for hackathon demo

# Update other configs as needed
```

Then push changes:
```bash
git add .env.local
git commit -m "Update production config"
git push
```

### 2. Setup Monitoring

In AWS Amplify console:
1. Go to "Monitoring"
2. Enable CloudWatch monitoring
3. Set up alerts for build failures

### 3. Configure Redirects (if needed)

In `public/_redirects` (if using redirects):
```
/api/* 200
/security/* 200
```

---

## Production Checklist

- [ ] Code pushed to GitHub main branch
- [ ] amplify.yml configured
- [ ] Environment variables set in Amplify
- [ ] Database URL configured
- [ ] Build succeeds without errors
- [ ] App loads at Amplify URL
- [ ] Wallet connection works
- [ ] API endpoints respond
- [ ] Custom domain configured (optional)
- [ ] Monitoring enabled
- [ ] Backup & disaster recovery planned

---

## Scaling & Performance

### Auto-scaling (Automatic)
- Amplify handles auto-scaling automatically
- No configuration needed for typical traffic

### Performance Optimization

To improve performance:

1. **Enable caching:**
   - In Amplify console → "Cache settings"
   - Set cache to 1 hour for static assets

2. **Use CloudFront:**
   - Automatically enabled with Amplify
   - Distributes content globally

3. **Monitor performance:**
   - Amplify console shows performance metrics
   - Check CloudWatch for detailed logs

---

## Cost Estimation (AWS Free Tier)

| Component | Free Tier | Cost/Month |
|-----------|-----------|-----------|
| Amplify Hosting | ✅ 15 GB/mo | $0.00 |
| Data Transfer | ✅ 1 GB/mo | $0.15/GB over |
| Build Minutes | ✅ 1000 min/mo | $0.01/min over |
| **Total for typical project** | | **~$5-15/mo** |

---

## Advanced: Custom Build Configuration

If you need more control, edit `amplify.yml`:

```yaml
version: 1

frontend:
  phases:
    preBuild:
      commands:
        - npm ci
        - npm run type-check
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: .next
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
      - .next/cache/**/*
```

---

## Next Steps

1. ✅ Deploy on Amplify (today)
2. ⏳ Deploy smart contracts to mainnet (tomorrow)
3. ⏳ Record demo video (this week)
4. ⏳ Submit to DoraHacks (Nov 30)

---

## Support

**If deployment fails:**

1. Check Amplify console for error messages
2. Review build logs (click "Build" → "View logs")
3. Verify all environment variables are set
4. Test build locally first: `npm run build`

**AWS Amplify Docs:**
- https://docs.aws.amazon.com/amplify/
- https://docs.aws.amazon.com/amplify/latest/userguide/

---

## Summary

**What we've done:**
- ✅ Created `amplify.yml` for build configuration
- ✅ Created deployment guide
- ✅ Ready for Amplify deployment

**Next action:**
Go to AWS Amplify console and start deployment! 🚀

---

*Deployment Guide v1.0 - November 16, 2025*
