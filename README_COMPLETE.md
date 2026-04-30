# DarkStare AI v4.1 — Complete Integration

## ✨ What You Have Now

```
┌─────────────────────────────────────────────────────────┐
│                   DARKSTARE AI v4.1                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🔐 Authentication & User Management                   │
│     • Email/password registration                      │
│     • Token-based sessions                             │
│     • 4 tier system (Free/Starter/Pro/Elite)          │
│     • Admin dashboard                                  │
│                                                         │
│  🤖 Gold AI Trading Engine (NEW!)                      │
│     • Self-learning AI system                          │
│     • 5-timeframe analysis                             │
│     • 50+ pattern recognition                          │
│     • Automatic strategy discovery                     │
│     • Real-time trading signals                        │
│     • Risk & profit protection                         │
│                                                         │
│  📡 REST API + WebSocket                               │
│     • 15+ trading endpoints                            │
│     • Live log streaming                               │
│     • Position tracking                                │
│     • Trade history & stats                            │
│                                                         │
│  💾 Persistent Database                                │
│     • PostgreSQL on Render                             │
│     • Trade history                                    │
│     • Learning memory                                  │
│     • Strategy database                                │
│                                                         │
│  🚀 Production Deployment                              │
│     • Render.com integration                           │
│     • Docker containerization                          │
│     • Environment configuration                        │
│     • Health monitoring                                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🏗️ Project Structure

```
DARKSTARE-AI-/
├── 📜 Server & Config
│   ├── server.py              ← Main FastAPI app
│   ├── config.py              ← Gold AI parameters
│   ├── requirements.txt        ← Dependencies
│   ├── runtime.txt            ← Python 3.11
│   ├── Procfile               ← Render commands
│   └── render.yaml            ← Render config
│
├── 🤖 Gold AI Trading Engine
│   ├── mt5_connector.py       ← MetaTrader5 interface
│   ├── sessions.py            ← EAT session detection
│   ├── gold_indicators.py     ← 20+ technical indicators
│   ├── gold_patterns.py       ← Pattern recognition
│   ├── gold_ai_engine.py      ← Decision engine
│   ├── gold_brain.py          ← Learning system
│   ├── gold_news.py           ← Sentiment analysis
│   ├── gold_api.py            ← REST endpoints (NEW)
│   └── gold_db.py             ← Database layer (NEW)
│
├── 🐳 Docker
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── 📚 Documentation
│   ├── README.md
│   ├── README_DEPLOY.md
│   ├── DEPLOY_GUIDE.md        ← Step-by-step deployment
│   ├── GOLD_AI_SETUP.md       ← AI configuration guide
│   └── README_COMPLETE.md     ← This file
│
├── 💾 Data Files (auto-created)
│   └── data/
│       ├── gold_memory.json
│       ├── gold_weights.json
│       ├── gold_sequences.json
│       ├── gold_strategies.json
│       └── gold_trades.json
│
└── 🎨 Frontend
    └── index.html             ← Dashboard
```

---

## 🚀 Quick Deploy (3 Steps)

### 1️⃣ Render Setup
```bash
# Push to GitHub
git add .
git commit -m "Add complete Gold AI integration"
git push origin main

# Go to render.com → Dashboard → New Web Service
# Connect repo and select render.yaml
```

### 2️⃣ Environment Variables
In Render Dashboard → Settings → Environment:
```
APP_SECRET=<random-string>
MT5_LOGIN=<your-account>
MT5_PASSWORD=<your-password>
MT5_SERVER=MetaQuotes-Demo
AUTO_TRADE=false
DATABASE_URL=<auto-from-postgres>
```

### 3️⃣ Add Database
Render Dashboard → New → PostgreSQL
- Name: `gold-ai-db`
- Plan: Free
- **Done!** Auto-connected via `DATABASE_URL`

---

## 📡 API Endpoints

### Authentication
```bash
# Register
POST /api/auth/register
{"name": "User", "email": "user@example.com", "password": "pass"}

# Login
POST /api/auth/login
{"email": "user@example.com", "password": "pass"}

# Get current user
GET /api/auth/me
Authorization: Bearer TOKEN

# Logout
POST /api/auth/logout
```

### Trading (Gold AI)
```bash
# Get current signal
GET /api/trading/signal
Authorization: Bearer TOKEN

# Get AI stats
GET /api/trading/stats
Authorization: Bearer TOKEN

# Get open positions
GET /api/trading/positions
Authorization: Bearer TOKEN

# Get trade history
GET /api/trading/history?limit=50
Authorization: Bearer TOKEN

# Manual analysis scan
POST /api/trading/scan
Authorization: Bearer TOKEN

# Account info
GET /api/trading/account
Authorization: Bearer TOKEN

# Enable/disable auto-trading
POST /api/trading/toggle-trading
{"enabled": true}
Authorization: Bearer TOKEN

# Health status
GET /api/trading/health

# Stream logs
WebSocket /ws/trading/logs
Authorization: Bearer TOKEN
```

### System
```bash
# Server status
GET /api/status

# Manifest
GET /manifest.json
```

---

## 🎮 Usage Examples

### JavaScript (Browser)
```javascript
// Login
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password'
  })
});
const {token} = await response.json();

// Get signal
const signal = await fetch('/api/trading/signal', {
  headers: {'Authorization': `Bearer ${token}`}
}).then(r => r.json());
console.log(signal.signal.action);  // BUY, SELL, or HOLD

// Stream logs
const ws = new WebSocket(`wss://your-domain.com/ws/trading/logs?token=${token}`);
ws.onmessage = (event) => {
  const {logs} = JSON.parse(event.data);
  console.log(logs);
};
```

### Python
```python
import requests

# Login
resp = requests.post('https://your-domain.com/api/auth/login', json={
    'email': 'user@example.com',
    'password': 'password'
})
token = resp.json()['token']

# Get signal
signal = requests.get(
    'https://your-domain.com/api/trading/signal',
    headers={'Authorization': f'Bearer {token}'}
).json()

# Get stats
stats = requests.get(
    'https://your-domain.com/api/trading/stats',
    headers={'Authorization': f'Bearer {token}'}
).json()

print(f"Win Rate: {stats['win_rate']}")
print(f"Total P&L: ${stats['total_pnl']}")
```

### cURL
```bash
# Register
curl -X POST https://your-domain.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "password123"
  }'

# Get signal
curl https://your-domain.com/api/trading/signal \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## ⚙️ Configuration

### Critical Settings (config.py)
```python
# MT5 Account
MT5_LOGIN = 12345678
MT5_PASSWORD = "your_password"
MT5_SERVER = "MetaQuotes-Demo"

# Risk
BASE_RISK_PCT = 0.5        # Risk 0.5% per trade
MAX_RISK_PCT = 3.0         # Never risk >3%
MAX_OPEN_TRADES = 5

# Sessions to trade
TRADE_SESSIONS = ["london", "newyork", "overlap"]
GOLD_KILLZONE = (14, 16)   # High prob zone

# Learning
LEARNING_ENABLE = True
MIN_TRADES_TO_LEARN = 10
LEARNING_RATE = 0.02

# Auto-trading (start FALSE)
AUTO_TRADE = False
```

### Render Environment
```
APP_SECRET          → Auto-generated, never commit
AUTO_TRADE          → false (start here)
DATABASE_URL        → Auto-connected PostgreSQL
MT5_LOGIN           → Your account number
MT5_PASSWORD        → Your password (secrets only!)
MT5_SERVER          → MetaQuotes-Demo or broker
PORT                → 10000 (Render default)
```

---

## 🧠 How Gold AI Works

### 1. Analysis
```
Market Data (M5, M15, H1, H4, D1)
    ↓
Indicators (MA, RSI, MACD, BB, ATR, Stoch)
    ↓
Patterns (50+ candlestick, chart, SMC)
    ↓
AI Decision Engine (multi-factor scoring)
    ↓
Signal: BUY / SELL / HOLD
```

### 2. Learning
```
Trade executed
    ↓
Trade closes (Win/Loss)
    ↓
Brain records outcome
    ↓
Sequence patterns updated
    ↓
Strategy discovered if 6+ similar trades
    ↓
Weights adjusted (learning rate: 0.02)
    ↓
Next signal uses updated knowledge
```

### 3. Protection
```
Position Open
    ↓
Every 30s: Update SL/TP
    ↓
At 1.0 RR: Move to breakeven
    ↓
At 1.5 RR: Partial close 50%
    ↓
At 2.0 RR: Lock 50% of profit
    ↓
Profit locked, let rest run
```

---

## 🔍 Monitoring

### Real-Time Dashboard
Visit: https://your-domain.com/
- Current signal & confidence
- Open positions
- P&L stats
- Strategy performance
- Learning progress

### API Monitoring
```bash
# Health check
curl https://your-domain.com/api/status | jq .

# Trading stats
curl https://your-domain.com/api/trading/stats -H "Authorization: Bearer TOKEN" | jq .

# Positions
curl https://your-domain.com/api/trading/positions -H "Authorization: Bearer TOKEN" | jq .
```

### Render Logs
1. Go to Render Dashboard
2. Select your service
3. Click "Logs"
4. Stream live deployment & trading logs

---

## 🐛 Troubleshooting

### MT5 Connection Error
```
Error: "MT5 not connected"
```
**Fix:**
- Verify MT5 running on accessible server
- Check credentials (MT5_LOGIN, MT5_PASSWORD)
- Verify network connectivity
- Check broker server name (MT5_SERVER)

### Database Error
```
Error: "could not connect to server: Connection refused"
```
**Fix:**
- Verify DATABASE_URL set in Render
- Wait 2 minutes after adding PostgreSQL
- Check if Render PostgreSQL add-on running

### No Gold Data
```
Error: "No data available" when requesting signal
```
**Fix:**
- Verify XAUUSD symbol in MT5
- Gold trades 24/5 (closed weekends)
- Ensure enough candle history loaded

### WebSocket Disconnects
**Fix:**
- Normal on weekly Render restart
- Implement automatic reconnection logic
- Logs preserved in database

---

## 📊 Production Checklist

Before enabling AUTO_TRADE:

- [ ] Account registered & verified
- [ ] MT5 credentials confirmed working
- [ ] Test signal generation (analysis only)
- [ ] Review 10+ signals for quality
- [ ] Check historical win rate
- [ ] Verify risk calculations
- [ ] Set AUTO_TRADE=false initially
- [ ] Monitor for 1 week
- [ ] Review all stats
- [ ] Then enable AUTO_TRADE=true
- [ ] Start with small 0.01 lot
- [ ] Increase gradually after 50+ trades

---

## 💾 Backup & Recovery

### Export Trade History
```bash
curl https://your-domain.com/api/trading/history?limit=10000 \
  -H "Authorization: Bearer TOKEN" > backup.json
```

### Database Backup
Render automatically backs up PostgreSQL. To manual backup:
```bash
pg_dump $DATABASE_URL > backup.sql
```

### Restore Database
```bash
psql $DATABASE_URL < backup.sql
```

---

## 🎯 Next Steps

1. **Deploy:** Follow DEPLOY_GUIDE.md
2. **Configure:** Update config.py with your MT5 account
3. **Test:** Run analysis-only mode for 1 week
4. **Verify:** Check signal quality & win rates
5. **Scale:** Enable auto-trading with small lots
6. **Optimize:** Adjust risk & parameters based on results
7. **Monitor:** Check daily stats & logs

---

## 📞 Support Resources

- **Deployment Issues:** DEPLOY_GUIDE.md
- **Gold AI Config:** GOLD_AI_SETUP.md
- **API Docs:** This README_COMPLETE.md
- **Logs:** Render Dashboard → Logs
- **Status:** `GET /api/status`
- **GitHub Issues:** Report bugs

---

## 📈 Success Metrics

Track these KPIs:

```
Win Rate        → Target: >55%
Profit Factor   → Target: >1.5
Sharpe Ratio    → Target: >1.0
Max Drawdown    → Target: <10%
ROI/Month       → Target: 3-5%
Trades/Week     → Target: 20-40
```

---

## 🔐 Security Notes

✅ **Secure:**
- Passwords hashed (SHA256)
- Tokens time-limited (60 days)
- CORS enabled safely
- HTTPS on Render
- Secrets in environment variables

⚠️ **Never:**
- Commit MT5_PASSWORD to Git
- Share APP_SECRET
- Use demo credentials in production
- Disable security on Render

---

## 📜 License & Disclaimer

**DISCLAIMER:** Gold AI is for educational purposes. Past performance ≠ future results. 
Test thoroughly on demo before using real money. Trading involves substantial risk of loss.

Use entirely at your own risk. We take no responsibility for trading losses.

---

**DarkStare AI v4.1**  
**Production Ready | 2026-04-30**  
**🚀 Ready to Deploy!**