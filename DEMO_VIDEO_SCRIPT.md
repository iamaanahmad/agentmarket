# 🎬 AgentMarket Demo Video Script
## AWS Global Vibe Hackathon 2025 - Official Submission Video

**Total Duration:** 4 minutes 30 seconds  
**Target Audience:** Hackathon judges  
**Goal:** Showcase innovation, functionality, and Kiro IDE usage

---

## 🎯 PRE-RECORDING CHECKLIST

### Environment Setup (Do this BEFORE recording!)

**1. Clean Your Browser**
- [ ] Open Chrome/Firefox in **Incognito/Private mode**
- [ ] Close all other tabs except AgentMarket
- [ ] Clear browser console (F12 → Console → Clear)
- [ ] Zoom to 100% (Ctrl+0)

**2. Prepare Demo Data**
- [ ] Have at least 3-5 agents in database (including SecurityGuard AI)
- [ ] Prepare test request text: "Please analyze this wallet for security risks: 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
- [ ] Prepare test transaction for scanner: "danger test transaction" (triggers DANGER result)
- [ ] Have demo wallet with devnet SOL connected (Phantom recommended)
- [ ] Test the full hire flow once before recording
- [ ] Live URL: https://main.d1qz5jyb1c9oee.amplifyapp.com

**Key UI Elements to Know:**
- Agent card has two buttons: "View Details" and "Hire Agent"
- Agent detail page has "Hire This Agent" button at bottom
- Hire modal steps: Details → Confirm → Processing → Success
- Security page scanner: type "danger" to get DANGER result, "caution" for CAUTION, anything else for SAFE

**3. Screen & Audio**
- [ ] Set screen resolution to 1920x1080 (Full HD)
- [ ] Close unnecessary desktop icons
- [ ] Hide taskbar notifications
- [ ] Test microphone levels (record 10 seconds, play back)
- [ ] Close Discord, Slack, email clients (no notifications!)

**4. Files to Have Open**
- [ ] Browser: http://localhost:3000
- [ ] VS Code: Open to .kiro folder
- [ ] Solana Explorer: Your program IDs bookmarked
- [ ] Script (this file) on second monitor or printed

**5. Test Run**
- [ ] Do a complete walkthrough once
- [ ] Time yourself (should be 4-5 minutes)
- [ ] Note any slow loading times
- [ ] Refresh page if needed

---

## 🎬 SCENE-BY-SCENE SCRIPT

---

### **SCENE 1: HOOK & PROBLEM STATEMENT**
**Duration:** 0:00 - 0:30 (30 seconds)

#### Visual:
- Show Google search: "crypto wallet hacks 2024"
- Quick scroll through news headlines about exploits
- Show statistic graphic: "$2 BILLION LOST"

#### What to Say:

"In 2024, cryptocurrency users lost over $2 billion to wallet exploits 
and malicious smart contracts. At the same time, despite $637 million 
invested in AI agents, there's no trusted marketplace where creators 
can monetize their AI models and users can find verified AI services.

What if we could solve both problems with one platform?"


#### Action Steps:
1. Open browser with Google search "crypto hacks 2024" visible
2. Scroll slowly through 2-3 headlines (3 seconds)
3. Switch to a prepared slide/image showing "$2B lost" statistic
4. Pause for 2 seconds on the statistic

**Timing Check:** Stop at 0:30

---

### **SCENE 2: INTRODUCING AGENTMARKET**
**Duration:** 0:30 - 1:00 (30 seconds)

#### Visual:
- Navigate to http://localhost:3000 (homepage)
- Show hero section
- Slow scroll to show featured agents section

#### Navigation:
```
Browser → localhost:3000 → Homepage loads
```

#### What to Say:

"Meet AgentMarket - the first decentralized AI agent marketplace 
built on Solana. Here, AI creators register their agents as NFTs, 
users hire them with cryptocurrency, and smart contracts ensure fair 
payment through on-chain reputation and automated escrow.

Let me show you how it works."


#### Action Steps:
1. Type "localhost:3000" in address bar (or click if already open)
2. Homepage loads - pause on hero section (3 seconds)
3. Slowly scroll down to show:
   - Stats section (Total Agents, Services, Earnings)
   - Featured agents carousel
   - "How It Works" section
4. Scroll back to top

**Timing Check:** Stop at 1:00

---

### **SCENE 3: BROWSE MARKETPLACE**
**Duration:** 1:00 - 1:40 (40 seconds)

#### Visual:
- Click "Explore Agents" or navigate to /marketplace
- Show agent grid with multiple agents
- Use search/filter briefly
- Click "View Details" on SecurityGuard agent card

#### Navigation:
```
Homepage → Click "Explore Agents" button → /marketplace
Marketplace → Click "View Details" on SecurityGuard AI card → /agents/[id]
```

#### What to Say:

"The marketplace displays all available AI agents. Each agent shows 
their capabilities, pricing, and on-chain reputation. You can search 
and filter by capability, price, or rating.

Let's look at SecurityGuard - our flagship agent that protects users 
from wallet exploits in real-time."


#### Action Steps:
1. Click "Explore Agents" button (or navigate to /marketplace)
2. Marketplace page loads - pause to show agent grid (3 seconds)
3. Hover over search bar briefly
4. Click "Security" filter in sidebar to show filtering works
5. Clear filter (click X on badge)
6. Scroll down slightly to show more agents
7. Find SecurityGuard AI card and click "View Details" button
8. Agent detail page loads at /agents/[id]

**Timing Check:** Stop at 1:40

---

### **SCENE 4: AGENT PROFILE & CAPABILITIES**
**Duration:** 1:40 - 2:10 (30 seconds)

#### Visual:
- SecurityGuard agent detail page (/agents/[id])
- Show header with avatar, name, rating, response time
- Show capability badges (Security, Analysis, Real-time)
- Show "About This Agent" description
- Show Pricing card and Agent Details card

#### Navigation:
```
/agents/[securityguard-id] - Stay on agent detail page
```

#### What to Say:

"Each agent has a detailed profile. SecurityGuard costs 0.01 SOL per 
scan - about $2. It has a 4.8-star rating from real users and shows 
response time under 30 seconds.

The capabilities show it specializes in Security, Analysis, and 
Real-time scanning. You can see the creator's wallet address and 
when the agent was registered - all transparent and on-chain."


#### Action Steps:
1. Point out the header section:
   - Agent avatar and name "SecurityGuard AI"
   - "Active" badge (green)
   - Rating: ⭐ 4.8 with rating count
   - Response time: < 30s
   - Capability badges: Security, Analysis, Real-time
2. Scroll down to show:
   - "About This Agent" card with description
   - "Pricing" card showing 0.01 SOL per query
   - "Agent Details" card with Agent ID, Creator Wallet, Registered date
3. Scroll back up to show "Hire This Agent" button

**Timing Check:** Stop at 2:10

---

### **SCENE 5: HIRE AGENT & WALLET CONNECTION**
**Duration:** 2:10 - 2:40 (30 seconds)

#### Visual:
- Click "Hire This Agent" button
- Hire agent modal appears with agent info
- Connect wallet (Phantom popup) if not connected
- Type/paste request description in textarea
- Click "Continue" then "Pay" to confirm

#### Navigation:
```
Agent Detail Page → Click "Hire This Agent" → Modal opens
Modal Step 1 (Details): Shows agent rating, capabilities, request textarea
Modal Step 2 (Confirm): Shows request summary and payment amount
Modal Step 3 (Processing): "Creating service request..."
Modal Step 4 (Success): Request ID displayed
```

#### What to Say:

"To hire an agent, I'll click 'Hire This Agent'. This opens a modal 
showing the agent's rating and capabilities.

I need to connect my Solana wallet first - using Phantom. Then I'll 
describe my request. For SecurityGuard, I'll paste a wallet address 
I want to analyze for security risks."


#### Action Steps:
1. Click "Hire This Agent" button (blue button at bottom)
2. Modal appears showing:
   - Agent rating (⭐ 4.8) and service count
   - Response time (< 30s)
   - Capability badges
   - "Describe your request" textarea
   - Service Cost: 0.01 SOL per query
3. If wallet not connected, click "Select Wallet" button
4. Phantom wallet popup appears → Click "Connect"
5. In textarea, type or paste:
   ```
   Please analyze this wallet for security risks: 
   7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU
   ```
6. Click "Continue" button
7. Confirm screen shows request summary and total cost
8. Click "Pay 0.01 SOL" button

**Timing Check:** Stop at 2:40

---

### **SCENE 6: SERVICE REQUEST CREATED & SECURITY SCANNER DEMO**
**Duration:** 2:40 - 3:20 (40 seconds)

#### Visual:
- Modal shows "Creating service request..." with spinner
- Success screen appears with green checkmark
- Toast notification shows Request ID
- Close modal → Navigate to /security page
- Demo the live SecurityGuard scanner with risk visualization

#### Navigation:
```
Hire Modal → "Creating service request..." → Success with checkmark
Toast: "Service request created! Request ID: req-XXXXX. SecurityGuard AI will start working on it."
Close modal → Click "Security" in navbar → /security page
Security page → Paste transaction → Scan → See results
```

#### What to Say:

"The system creates a service request and shows me the Request ID. 
SecurityGuard AI will now process my request. The payment is held 
in escrow until the work is complete.

Let me also show you the SecurityGuard scanner directly. On the 
Security page, anyone can paste a transaction and get instant 
analysis. Watch how it detects a dangerous wallet drainer..."


#### Action Steps:
1. Watch modal show "Creating service request..." with spinner
2. Success screen appears:
   - Green checkmark icon
   - "Request submitted successfully!"
   - "SecurityGuard AI will start working on your request. You'll receive updates in your dashboard."
3. Toast notification appears: "Service request created! Request ID: req-XXXXX..."
4. Click "Close" button
5. Navigate to /security page (click "Security" in navbar)
6. Security page loads showing:
   - Stats: Threats Blocked, Users Protected, Avg Response Time, Detection Accuracy
   - Scanner tab is active by default
7. In the transaction input area, paste:
   ```
   danger test transaction
   ```
   (The word "danger" triggers the mock dangerous result)
8. Click "Scan Transaction" button
9. Watch scanning animation with progress steps (3 seconds)
10. Results appear showing:
    - DANGER risk level (red badge)
    - Risk Score: 85/100
    - Explanation: "This transaction contains patterns matching known wallet drainer exploits..."
    - Recommendation: "DO NOT SIGN this transaction..."

**Timing Check:** Stop at 3:20

---

### **SCENE 7: DASHBOARD & REQUEST TRACKING**
**Duration:** 3:20 - 3:40 (20 seconds)

#### Visual:
- Navigate to /dashboard
- Show statistics cards (Total Requests, Pending, Completed, Disputed, Total Spent)
- Show Service Requests list with the request we just created
- Show request details with Request ID, status, and amount

#### Navigation:
```
/security → Click "Dashboard" in navbar → /dashboard
Dashboard shows statistics and request history
```

#### What to Say:

"All requests are tracked in your dashboard. You can see statistics 
at a glance - total requests, pending, completed, and total spent.

Here's the request we just created with its Request ID and status. 
You can click 'View Agent' to go back to the agent profile. This 
transparent tracking builds trust in the marketplace."


#### Action Steps:
1. Click "Dashboard" in the navigation bar
2. Dashboard loads - wallet should already be connected
3. Point out the statistics cards:
   - Total Requests: shows count
   - Pending: yellow number
   - Completed: green number
   - Disputed: red number (likely 0)
   - Total Spent: shows SOL amount
4. Scroll to "Service Requests" section
5. Find the SecurityGuard request we just created:
   - Shows agent name "SecurityGuard AI"
   - Status badge (pending/completed)
   - Request ID: req-XXXXX
   - Created date and Amount: 0.01 SOL
6. Point out "View Agent" button (don't click)

**Timing Check:** Stop at 3:40

---

### **SCENE 8: KIRO IDE & SPEC-DRIVEN DEVELOPMENT**
**Duration:** 3:40 - 4:10 (30 seconds)

#### Visual:
- Switch to VS Code
- Show .kiro folder structure in sidebar
- Open .kiro/requirements.md
- Scroll through user stories
- Open .kiro/design.md
- Show architecture diagram
- Open .kiro/tasks.md briefly

#### Navigation:
```
Browser → Alt+Tab → VS Code
VS Code: File Explorer → .kiro folder expanded
Open files: requirements.md, design.md, tasks.md
```

#### What to Say:

"AgentMarket was built using spec-driven development with Kiro IDE. 
Every feature started as a detailed specification.

Here in our requirements.md, you can see user stories written in 
professional EARS notation with clear acceptance criteria.

The design.md contains our complete technical architecture, including 
system diagrams and component interactions.

And tasks.md breaks down the implementation into 40+ granular tasks, 
all tracked from specification to completion. This systematic approach 
ensured quality and made the complex simple."


#### Action Steps:
1. **Switch to VS Code** (Alt+Tab or click taskbar)
2. **Show .kiro folder** in file explorer (expand if collapsed)
3. **Open requirements.md:**
   - Scroll slowly through 2-3 user stories (5 seconds)
   - Show EARS notation format
   - Show acceptance criteria
4. **Open design.md:**
   - Scroll to architecture section (3 seconds)
   - Show system diagram or technical specs
5. **Open tasks.md:**
   - Quick scroll showing task list (3 seconds)
   - Show checkmarks for completed tasks
6. **Keep VS Code open** for next transition

**Timing Check:** Stop at 4:10

---

### **SCENE 9: TECHNICAL ARCHITECTURE**
**Duration:** 4:10 - 4:30 (20 seconds)

#### Visual:
- Open Solana Explorer in browser
- Show all 4 deployed smart contracts
- Show program IDs and verification
- Quick view of transaction history

#### Navigation:
```
VS Code → Alt+Tab → Browser
Open new tab → Solana Explorer
Show: agent-registry, marketplace-escrow, reputation-system, royalty-splitter
```

#### What to Say:

"Under the hood, AgentMarket runs on four Solana smart contracts: 
Agent Registry for NFT-based agent ownership, Marketplace Escrow for 
secure payments, Reputation System for on-chain ratings, and Royalty 
Splitter for automatic payment distribution.

All contracts are deployed and verified on Solana devnet."


#### Action Steps:
1. **Switch back to browser** (Alt+Tab)
2. **Open new tab** → Solana Explorer
3. **Show program IDs** (have them bookmarked):
   - Agent Registry: `Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS`
   - Marketplace Escrow: `2ZuJbvYqvhXq7N7WjKw3r4YqkU3r7CmLGjXXvKhGz3xF`
   - Reputation System: `8L8pDf3jutdpdr4m3np68CL9ZroLActrqwxi6s9Sk5ML`
   - Royalty Splitter: `5xot9PVkphiX2adznghwrAuxGs2zeWisNSxMW6hU6Hkj`
4. **Click on one contract** to show it's verified
5. **Scroll briefly** to show transaction history
6. **Return to AgentMarket homepage** for closing

**Timing Check:** Stop at 4:30

---

### **SCENE 10: IMPACT & CALL TO ACTION**
**Duration:** 4:30 - 5:00 (30 seconds)

#### Visual:
- Return to AgentMarket homepage
- Show stats section highlighting growth
- Fade to black with text overlay:
  - "AgentMarket.xyz"
  - "Built with Solana, AWS, and Kiro IDE"
  - "GitHub: github.com/iamaanahmad/agentmarket"

#### Navigation:
```
Stay on homepage
Scroll to stats section
Prepare for fade to closing screen
```

#### What to Say:

"AgentMarket solves real problems. It prevents billions in wallet 
exploits, empowers AI creators to monetize their work, and makes 
Web3 accessible to everyone through natural language interfaces.

This is day one of the AI agent economy. AgentMarket is the 
marketplace that makes it possible - built on Solana for speed and 
low fees, deployed on AWS for reliability, and developed systematically 
with Kiro IDE.

Visit our GitHub to explore the code, or try the demo yourself. 
Thank you."


#### Action Steps:
1. **Navigate back** to AgentMarket homepage
2. **Scroll to stats section:**
   - Highlight: Total Agents, Services Completed, Total Earned
3. **Hold on homepage** (3 seconds)
4. **Prepare closing screen** (can be simple black screen with text):
   ```
   AgentMarket
   The First Decentralized AI Agent Marketplace
   
   Built with:
   ⚡ Solana | ☁️ AWS | 🤖 Kiro IDE
   
   🔗 github.com/iamaanahmad/agentmarket
   🌐 main.d1qz5jyb1c9oee.amplifyapp.com
   ```
5. **Fade to black** with text overlay
6. **Hold for 3 seconds**
7. **End recording**

**Timing Check:** Total time: ~5:00

---

## 🎤 VOICEOVER TIPS

### Delivery Style:
- **Pace:** Moderate - not too fast, not too slow
- **Tone:** Professional but enthusiastic
- **Energy:** Confident and clear
- **Pauses:** Use natural pauses between sections

### Recording Tips:
1. **Read through script 3-4 times** before recording
2. **Record in a quiet room** (no background noise)
3. **Stand while recording** (better vocal projection)
4. **Smile while speaking** (it changes your tone positively)
5. **Take multiple takes** of each section
6. **Keep a glass of water nearby**

### Technical Settings:
- Microphone distance: 6-8 inches from mouth
- Recording level: Peak at -6dB to -12dB (not hitting red)
- Format: WAV or high-quality MP3 (320kbps)
- Remove background noise in post-production

---

## 🎬 RECORDING WORKFLOW

### Option 1: Record Everything at Once (Easier)
```
1. Start recording (OBS Studio or similar)
2. Follow script from Scene 1 → Scene 10
3. Speak live while navigating
4. Stop recording
5. Edit out mistakes
```

**Pros:** Natural flow, less editing  
**Cons:** Harder to get perfect, may need multiple full takes

### Option 2: Record Sections Separately (Better Quality)
```
1. Record video of each scene WITHOUT audio
2. Record voiceover separately for each scene
3. Combine in video editor (DaVinci Resolve, etc.)
4. Add transitions between scenes
```

**Pros:** Better quality, can perfect each section  
**Cons:** More editing work

### Recommended: Hybrid Approach
```
1. Record Scenes 1-7 with live audio (main demo)
2. Record Scenes 8-10 separately (technical showcase)
3. Combine in editor
4. Add background music (low volume)
5. Add captions/subtitles
```

---

## 📝 SCENE TIMING SUMMARY

| Scene | Duration | Description | Key Action |
|-------|----------|-------------|------------|
| 1 | 0:00-0:30 | Hook & Problem | Show $2B statistic |
| 2 | 0:30-1:00 | Introduce AgentMarket | Homepage tour |
| 3 | 1:00-1:40 | Browse Marketplace | Click "View Details" on agent |
| 4 | 1:40-2:10 | Agent Profile | Show SecurityGuard details |
| 5 | 2:10-2:40 | Hire Agent | "Hire This Agent" → Modal flow |
| 6 | 2:40-3:20 | Request Created + Scanner | Toast with Request ID → /security demo |
| 7 | 3:20-3:40 | Dashboard | Show request tracking |
| 8 | 3:40-4:10 | Kiro IDE | Show .kiro folder |
| 9 | 4:10-4:30 | Smart Contracts | Solana Explorer |
| 10 | 4:30-5:00 | Impact & Close | Call to action |

**Total:** ~5 minutes

### 🔄 ACTUAL USER FLOW SUMMARY
```
Homepage → "Explore Agents" → /marketplace
         → Click "View Details" → /agents/[id]
         → Click "Hire This Agent" → Modal opens
         → Describe request → "Continue" → "Pay X SOL"
         → "Creating service request..." → Success + Request ID
         → Close → /security (demo scanner)
         → /dashboard (see request tracking)
```

---

## ✅ POST-RECORDING CHECKLIST

### Immediately After Recording:
- [ ] Watch full video to check for errors
- [ ] Note timestamps of any mistakes
- [ ] Check audio quality (no static, clear voice)
- [ ] Verify screen is visible (not too small text)
- [ ] Confirm all navigation worked as planned

### Video Editing:
- [ ] Cut out long pauses or mistakes
- [ ] Add smooth transitions between scenes
- [ ] Add text overlays for key points:
  - "$2 Billion Lost to Exploits"
  - "85% to Creator, 10% Platform, 5% Treasury"
  - "4 Solana Smart Contracts"
  - Program IDs on screen when showing contracts
- [ ] Add background music (low volume, royalty-free)
- [ ] Add captions/subtitles (YouTube auto-caption works)
- [ ] Color grade for professional look (if needed)

### Final Export:
- [ ] Resolution: 1920x1080 (1080p HD)
- [ ] Frame rate: 30fps or 60fps
- [ ] Format: MP4 (H.264 codec)
- [ ] Bitrate: 8-10 Mbps for high quality
- [ ] File size: Aim for under 500MB

### Upload to YouTube:
- [ ] Title: "AgentMarket - Decentralized AI Agent Marketplace | AWS Hackathon 2025"
- [ ] Description: Include GitHub link, tech stack, problem/solution
- [ ] Tags: AWS, Hackathon, Solana, AI, Web3, Blockchain, Marketplace
- [ ] Visibility: Unlisted (or Public)
- [ ] Thumbnail: Custom image with AgentMarket logo

### Test Before Submitting:
- [ ] Watch uploaded video completely
- [ ] Verify link works in incognito window
- [ ] Check audio/video quality on YouTube
- [ ] Confirm captions are readable

---

## 🎨 OPTIONAL ENHANCEMENTS

### Visual Polish (If Time Permits):
1. **Opening Title Card** (5 seconds)
   ```
   AgentMarket
   The First Decentralized AI Agent Marketplace
   Built on Solana
   ```

2. **Section Title Cards** (2-3 seconds each)
   - "The Problem" (before Scene 1)
   - "The Solution" (before Scene 2)
   - "Live Demo" (before Scene 3)
   - "Technical Architecture" (before Scene 8)
   - "Impact" (before Scene 10)

3. **Key Statistics Overlays:**
   - "$2B lost to exploits" (Scene 1)
   - "0.01 SOL per scan" (Scene 4)
   - "Risk Score: 95/100" (Scene 6)
   - "85/10/5 split" (Scene 6)

4. **Highlight Important UI Elements:**
   - Circle or arrow pointing to "Hire Now" button
   - Highlight risk score in red
   - Zoom into .kiro folder in VS Code

5. **Background Music:**
   - Upbeat, modern, tech-focused
   - Low volume (don't overpower voice)
   - Fade in at start, fade out at end
   - Suggested: "Tech Innovation" from YouTube Audio Library

### Advanced Editing (If Experienced):
- Picture-in-picture for Phantom wallet popup
- Split screen showing code + UI simultaneously
- Animated transitions between scenes
- Sound effects for clicks and actions
- Zoom in/out for emphasis

---

## 🚀 QUICK START GUIDE

### If You're Short on Time:
**Minimum Viable Video (3 hours):**
1. Record all 10 scenes in one take (1 hour)
2. Basic editing - cut mistakes only (1 hour)
3. Add simple title card and closing (30 min)
4. Export and upload (30 min)

**Good Quality Video (6 hours):**
1. Record scenes 1-2 times each (2 hours)
2. Edit, add transitions (2 hours)
3. Add text overlays and music (1 hour)
4. Polish and export (1 hour)

**Professional Video (10+ hours):**
1. Record multiple takes (3 hours)
2. Professional editing (4 hours)
3. Motion graphics and polish (2 hours)
4. Review and refinement (1 hour)

**Recommendation:** Aim for "Good Quality" - it's the sweet spot!

---

## 💡 FINAL TIPS

### Do's:
✅ Rehearse multiple times before recording  
✅ Have all URLs/data ready beforehand  
✅ Keep energy up throughout  
✅ Show real functionality (not mocked)  
✅ Highlight Kiro IDE usage clearly  
✅ End with strong call to action  

### Don'ts:
❌ Don't rush through sections  
❌ Don't show errors or bugs  
❌ Don't have notifications pop up  
❌ Don't use poor audio quality  
❌ Don't go over 5 minutes  
❌ Don't forget to show .kiro folder  

---

## 🎯 SUCCESS CRITERIA

Your video is ready to submit when:
- [ ] Total duration is 3-5 minutes
- [ ] Audio is clear and professional
- [ ] All key features demonstrated
- [ ] .kiro folder shown prominently
- [ ] No personal information visible
- [ ] No errors or bugs shown
- [ ] Uploaded to YouTube successfully
- [ ] Link works in incognito mode

---

**Good luck with your recording! You've got an amazing project - now show it off! 🌟**

**Questions while recording?** Refer back to this script and follow it step-by-step.

**Remember:** It doesn't have to be perfect! Judges want to see functionality and innovation, not Hollywood production quality. Just be clear, confident, and show your working project!

---

**Script Version:** 2.0 (Updated to match actual UI flow)  
**Last Updated:** November 27, 2025  
**Estimated Recording Time:** 2-4 hours (including retakes)  
**Estimated Editing Time:** 2-4 hours  
**Total Time Investment:** 4-8 hours  

### 📋 QUICK REFERENCE - ACTUAL BUTTON NAMES
| Location | Button Text | Action |
|----------|-------------|--------|
| Homepage | "Explore Agents" | Goes to /marketplace |
| Agent Card | "View Details" | Goes to /agents/[id] |
| Agent Card | "Hire Agent" | Opens hire modal directly |
| Agent Detail | "Hire This Agent" | Opens hire modal |
| Hire Modal | "Continue" | Goes to confirm step |
| Hire Modal | "Pay X SOL" | Submits request |
| Hire Modal | "Close" | Closes modal |
| Navbar | "Security" | Goes to /security |
| Navbar | "Dashboard" | Goes to /dashboard |

🎬 **NOW GO RECORD YOUR WINNING VIDEO!** 🚀
