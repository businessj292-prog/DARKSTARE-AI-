# DARKSTARE AI TRADING BRAIN v4.0 — DEPLOYMENT GUIDE
## Business Edition · Cloud + Local

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## WHAT WAS FIXED IN v4.0

✅ "Failed to fetch" on login — FIXED (CORS bug with credentials)
✅ API keys now save permanently — never auto-deleted
✅ Show/hide password on all password fields
✅ Share link + Install button in Settings
✅ Beautiful intro/landing page before login
✅ Cloud deployment ready (Render, Railway, Fly.io)
✅ Environment variables for production secrets
✅ First user auto-gets Admin + Elite plan

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## FILES IN THIS PACKAGE

  server.py            Python backend (all APIs, auth, AI engine)
  index.html           Web app (all screens, all tabs)
  START.bat            Windows one-click launcher
  start_mac_linux.sh   Mac/Linux launcher
  make_shortcut.py     Windows desktop icon creator
  requirements.txt     Python packages
  Procfile             Heroku/Render/Railway process file
  runtime.txt          Python version specification
  render.yaml          Render.com auto-deploy config
  railway.json         Railway.app config
  DarkStare_AI_EA.mq5  MetaTrader 5 Expert Advisor
  README_DEPLOY.md     This file

Auto-created at runtime:
  database.json        All users, sessions, history
  config.json          API keys (saved permanently)
  darkstare_signal.txt MT5 signal file

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## OPTION 1: RUN LOCALLY (PC/Mac/Linux)

### Windows
  Double-click: START.bat

### Mac / Linux
  chmod +x start_mac_linux.sh
  ./start_mac_linux.sh

### Manual
  pip install fastapi uvicorn httpx
  python server.py
  Open: http://localhost:8000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## OPTION 2: DEPLOY FREE ON RENDER.COM (RECOMMENDED)
### Users access it 24/7 from any device worldwide

**Step 1 — Push to GitHub**
  1. Create account at github.com (free)
  2. Click "New repository" → name it "darkstare-ai"
  3. Upload all these files to the repository
     (drag and drop into the GitHub web interface)

**Step 2 — Deploy on Render**
  1. Create account at render.com (free)
  2. Click "New +" → "Web Service"
  3. Connect your GitHub account
  4. Select your "darkstare-ai" repository
  5. Settings:
       Name:         darkstare-ai
       Runtime:      Python 3
       Build Command: pip install -r requirements.txt
       Start Command: python server.py
       Plan:         Free (or Starter $7/mo for always-on)
  6. Click "Create Web Service"
  7. Wait 2-3 minutes for deployment

**Step 3 — Set Environment Variables on Render**
  In your Render service → "Environment" tab → Add:

    APP_SECRET        = [generate a random 32-char string]
    APP_URL           = https://your-app-name.onrender.com
    PORT              = 10000

  Optional (or add in app Settings instead):
    ANTHROPIC_API_KEY = sk-ant-...
    OPENAI_API_KEY    = sk-proj-...
    NEWS_API_KEY      = your-newsapi-key
    AV_API_KEY        = your-alphavantage-key

**Step 4 — Share with users**
  Your app URL: https://your-app-name.onrender.com
  Share this link — users can register and login from anywhere!

⚠ FREE TIER NOTE: Render free tier spins down after 15min of inactivity.
  First load takes ~30 seconds. Upgrade to Starter ($7/mo) for always-on.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## OPTION 3: DEPLOY ON RAILWAY.APP
### $5/mo credit free, always-on, very fast

**Step 1 — Push to GitHub** (same as above)

**Step 2 — Deploy on Railway**
  1. Create account at railway.app (free)
  2. Click "New Project" → "Deploy from GitHub repo"
  3. Select your "darkstare-ai" repository
  4. Railway auto-detects Python and deploys

**Step 3 — Set Variables**
  In Railway → your service → "Variables" tab:
    APP_SECRET  = [random 32-char string]
    APP_URL     = https://[your-app].railway.app
    PORT        = 8080

**Step 4 — Get your URL**
  Railway → Settings → "Generate Domain"
  Share this link with users!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## OPTION 4: DEPLOY ON FLY.IO
### Global edge, fastest option, $0 for small apps

  1. Install flyctl: https://fly.io/docs/flyctl/install/
  2. Login: flyctl auth login
  3. In app folder: flyctl launch
     (accepts all defaults, name your app)
  4. Set secrets:
       flyctl secrets set APP_SECRET="your-secret-here"
       flyctl secrets set APP_URL="https://your-app.fly.dev"
  5. Deploy: flyctl deploy
  6. Open: flyctl open

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## OPTION 5: KOYEB (Free forever, always-on)

  1. Create account at koyeb.com
  2. "Create App" → "GitHub" → select repo
  3. Set run command: python server.py
  4. Add env vars: APP_SECRET, APP_URL, PORT=8000
  5. Deploy — get a free always-on URL

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## FIRST-TIME SETUP AFTER DEPLOYMENT

  1. Open your app URL in a browser
  2. Click "Get Started Free" on the landing page
  3. Register your account (first account = auto Admin + Elite)
  4. Go to ⚙ Settings → add your API keys
  5. Click "Save All Keys" (keys saved permanently)
  6. Click TEST next to each key to verify
  7. Go to DASH → click ANALYZE NOW

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## MOBILE INSTALLATION

  ANY platform (iOS/Android) — no app store needed:

  iPhone / iPad:
    1. Open app URL in Safari (must be Safari, not Chrome)
    2. Tap the Share button (square with arrow)
    3. Tap "Add to Home Screen"
    4. Tap "Add" — icon appears on home screen
    5. Opens full-screen like a native app!

  Android:
    1. Open app URL in Chrome
    2. Tap ⋮ menu (top right)
    3. Tap "Add to Home Screen"
    4. Tap "Add" — icon appears on home screen

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## API KEYS — WHERE TO GET THEM

  REQUIRED FOR AI ANALYSIS (one or both):
  ┌──────────────────┬────────────────────────────────────────┐
  │ Anthropic Claude │ console.anthropic.com/keys             │
  │                  │ ~$0.003 per analysis · $5 free credit  │
  ├──────────────────┼────────────────────────────────────────┤
  │ OpenAI GPT-4o    │ platform.openai.com/api-keys           │
  │                  │ ~$0.001 per analysis · $5 free credit  │
  └──────────────────┴────────────────────────────────────────┘

  FREE DATA SOURCES:
  ┌──────────────────┬────────────────────────────────────────┐
  │ NewsAPI          │ newsapi.org/register                   │
  │                  │ FREE · 1000 requests/day               │
  ├──────────────────┼────────────────────────────────────────┤
  │ Alpha Vantage    │ alphavantage.co/support/#api-key       │
  │                  │ FREE · 25 requests/day                 │
  └──────────────────┴────────────────────────────────────────┘

  OPTIONAL:
  ┌──────────────────┬────────────────────────────────────────┐
  │ X/Twitter        │ developer.twitter.com                  │
  │                  │ Free tier · 500k tweets/month          │
  ├──────────────────┼────────────────────────────────────────┤
  │ Stripe           │ dashboard.stripe.com/apikeys           │
  │                  │ For real payment processing            │
  └──────────────────┴────────────────────────────────────────┘

  Built-in AI engine works WITHOUT any API keys!
  Polymarket data is always free with no key needed!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## SUBSCRIPTION TIERS & STRIPE SETUP

  Test codes (work immediately):
    DEMO-STARTER  →  Starter plan
    DEMO-PRO      →  Pro plan
    DEMO-ELITE    →  Elite plan
    DEMO-FREE     →  Back to Free

  To enable real Stripe payments:
  1. Create account at stripe.com
  2. Create 3 products with monthly prices:
       Starter: $5/month
       Pro:     $15/month
       Elite:   $30/month
  3. Copy each product's Price ID (starts with price_...)
  4. Update server.py line ~230: price_ids dict
  5. Add your Stripe secret key (sk_live_...) in Settings
  6. Set up Stripe webhook → /api/webhook/stripe
       Events to listen for: checkout.session.completed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## PLAN FEATURES

  ┌─────────┬───────┬───────────┬────────┬──────────┐
  │ Plan    │ Price │ Analyses  │ AI     │ MT5      │
  │         │       │ /day      │ Engine │          │
  ├─────────┼───────┼───────────┼────────┼──────────┤
  │ Free    │  $0   │     3     │ Built- │    ✗     │
  │         │       │           │ in AI  │          │
  ├─────────┼───────┼───────────┼────────┼──────────┤
  │ Starter │  $5   │    20     │ Built- │    ✓     │
  │         │       │           │ in AI  │          │
  ├─────────┼───────┼───────────┼────────┼──────────┤
  │ Pro     │  $15  │   100     │ Claude │    ✓     │
  │         │       │           │ + GPT  │          │
  ├─────────┼───────┼───────────┼────────┼──────────┤
  │ Elite   │  $30  │ Unlimited │ All AI │    ✓     │
  └─────────┴───────┴───────────┴────────┴──────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## MT5 EXPERT ADVISOR SETUP

  1. Open MetaTrader 5
  2. File → Open Data Folder
  3. Navigate to: MQL5 → Experts
  4. Copy DarkStare_AI_EA.mq5 into that folder
  5. Open MetaEditor (F4) → find DarkStare_AI_EA → Compile (F7)
  6. Back in MT5 → drag EA onto any chart
  7. Enable AutoTrading (green play button top toolbar)
  8. In DarkStare Settings: paste the full path to:
     C:\Users\YourName\AppData\Roaming\MetaQuotes\
     Terminal\XXXXX\MQL5\Files\darkstare_signal.txt

  EA checks for new signals every 5 seconds.
  Auto-trades when signal confidence ≥ 70%.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ADMIN FEATURES

  The first user to register automatically becomes admin.
  Admin gets Elite plan for free.

  Admin API endpoints:
    GET  /api/admin/stats      - user counts, revenue estimate
    POST /api/admin/set_tier   - manually upgrade/downgrade users
         body: {"user_id":"xxx","tier":"pro"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## TROUBLESHOOTING

  "Failed to fetch" on login:
    → Make sure server.py is running
    → Open browser console (F12) → check for errors
    → Try: python server.py in terminal

  Black screen on load:
    → Clear browser cache (Ctrl+Shift+Delete)
    → Try incognito/private window
    → Make sure index.html is in the same folder as server.py

  Keys not saving:
    → Click "Save All Keys" — they now persist permanently
    → Check config.json was created in the same folder

  Rate limit on prices:
    → Alpha Vantage free = 25 requests/day
    → Wait until next day or upgrade Alpha Vantage account

  MT5 signal not working:
    → Check the file path is exactly correct
    → Ensure EA is compiled and AutoTrading is enabled

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DARKSTARE AI v4.0 — Business Edition
Trading involves risk. For educational use.
