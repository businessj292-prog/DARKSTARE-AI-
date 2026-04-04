"""
DARKSTARE AI TRADING BRAIN — BUSINESS EDITION v4.0
====================================================
Cloud-deployable SaaS backend.
Deploy FREE on: Render / Railway / Fly.io / Koyeb

FIXES in v4:
  - CORS bug fixed (was causing "Failed to fetch" on login)
  - API keys persist permanently to config.json (never auto-delete)
  - Password hashing secured
  - Token format fixed (colon-safe base64)
  - Environment variable support for cloud deployment

LOCAL:  python server.py  →  http://localhost:8000
CLOUD:  See README_DEPLOY.md for full guide
"""

import asyncio, json, os, socket, time, random, hashlib, hmac, re, base64
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx, uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

# ── Paths ─────────────────────────────────────────────────────────────────
BASE     = Path(__file__).parent
DB_FILE  = Path(os.environ.get("DB_PATH",  str(BASE / "database.json")))
CFG_FILE = Path(os.environ.get("CFG_PATH", str(BASE / "config.json")))
SIG_FILE = BASE / "darkstare_signal.txt"

# ── Secret (override with env var in production) ──────────────────────────
SECRET = os.environ.get("APP_SECRET", "DARKSTARE-SECRET-CHANGE-IN-PRODUCTION-2025")

# ── Tiers ─────────────────────────────────────────────────────────────────
TIERS = {
    "free":    {"name":"Free",    "price":0,  "analyses_per_day":3,   "pairs":2,  "chat":False,"ext_ai":False,"mt5":False, "history":10},
    "starter": {"name":"Starter", "price":5,  "analyses_per_day":20,  "pairs":5,  "chat":True, "ext_ai":False,"mt5":True,  "history":100},
    "pro":     {"name":"Pro",     "price":15, "analyses_per_day":100, "pairs":10, "chat":True, "ext_ai":True, "mt5":True,  "history":500},
    "elite":   {"name":"Elite",   "price":30, "analyses_per_day":9999,"pairs":99, "chat":True, "ext_ai":True, "mt5":True,  "history":9999},
}

# ── DB ────────────────────────────────────────────────────────────────────
def load_db() -> dict:
    try:
        if DB_FILE.exists():
            return json.loads(DB_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"users": {}}

def save_db(db: dict):
    DB_FILE.write_text(json.dumps(db, indent=2), encoding="utf-8")

# ── Config (keys NEVER auto-deleted) ─────────────────────────────────────
def load_cfg() -> dict:
    try:
        if CFG_FILE.exists():
            return json.loads(CFG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

def save_cfg_safe(updates: dict):
    """Merge updates INTO existing config — never overwrites unrelated keys."""
    cfg = load_cfg()
    if "keys" not in cfg:
        cfg["keys"] = {}
    for k, v in updates.items():
        if k == "mt5_path":
            cfg["mt5_path"] = str(v).strip()
        elif k == "admins":
            cfg["admins"] = v
        elif v and str(v).strip():
            # Only UPDATE a key if new value provided — never delete existing
            cfg["keys"][k] = str(v).strip()
    CFG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def get_key(name: str) -> str:
    # Check environment variables first (for cloud deployments)
    env_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai":    "OPENAI_API_KEY",
        "newsapi":   "NEWS_API_KEY",
        "av":        "AV_API_KEY",
        "twitter":   "TWITTER_BEARER",
        "stripe":    "STRIPE_SECRET_KEY",
    }
    env_val = os.environ.get(env_map.get(name, ""), "").strip()
    if env_val:
        return env_val
    return load_cfg().get("keys", {}).get(name, "").strip()

def local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except:
        return "localhost"

# ── Auth helpers ──────────────────────────────────────────────────────────
def hash_pw(pw: str) -> str:
    return hashlib.sha256((SECRET + pw + SECRET).encode()).hexdigest()

def make_token(uid: str) -> str:
    ts  = str(int(time.time()))
    raw = f"{uid}|{ts}"
    sig = hmac.new(SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()[:24]
    # Base64 encode to avoid colon issues
    payload = base64.urlsafe_b64encode(f"{raw}|{sig}".encode()).decode()
    return payload

def verify_token(token: str) -> Optional[str]:
    try:
        raw     = base64.urlsafe_b64decode(token.encode() + b"==").decode()
        parts   = raw.split("|")
        if len(parts) != 3: return None
        uid, ts, sig = parts
        if int(time.time()) - int(ts) > 86400 * 60: return None  # 60-day sessions
        expected = hmac.new(SECRET.encode(), f"{uid}|{ts}".encode(), hashlib.sha256).hexdigest()[:24]
        if hmac.compare_digest(sig, expected): return uid
    except:
        pass
    return None

def get_user(req: Request) -> Optional[dict]:
    auth  = req.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    if not token:
        token = req.cookies.get("ds_token", "")
    if not token: return None
    uid = verify_token(token)
    if not uid: return None
    return load_db()["users"].get(uid)

def require_user(req: Request) -> dict:
    u = get_user(req)
    if not u: raise HTTPException(401, "Not logged in")
    return u

def check_limit(user: dict) -> bool:
    t     = TIERS[user.get("tier", "free")]
    today = datetime.now().strftime("%Y-%m-%d")
    used  = user.get("usage", {}).get(today, 0)
    return used < t["analyses_per_day"]

def bump_usage(uid: str):
    db    = load_db()
    today = datetime.now().strftime("%Y-%m-%d")
    u     = db["users"].get(uid, {})
    if "usage" not in u: u["usage"] = {}
    u["usage"][today] = u["usage"].get(today, 0) + 1
    db["users"][uid]  = u
    save_db(db)

# ── App ───────────────────────────────────────────────────────────────────
app = FastAPI(title="DarkStare AI", version="4.0")

# ── CORS FIX: cannot use wildcard + credentials together ──────────────────
# Solution: reflect the request origin dynamically
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin   = request.headers.get("origin", "")
    response = await call_next(request)
    # Allow any origin but set it explicitly (fixes the wildcard+credentials bug)
    if origin:
        response.headers["Access-Control-Allow-Origin"]      = origin
    else:
        response.headers["Access-Control-Allow-Origin"]      = "*"
    response.headers["Access-Control-Allow-Credentials"]     = "true"
    response.headers["Access-Control-Allow-Methods"]         = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"]         = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Max-Age"]               = "86400"
    return response

@app.options("/{rest:path}")
async def preflight(rest: str):
    return Response(status_code=200)

# ── Static ────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index():
    f = BASE / "index.html"
    if f.exists(): return HTMLResponse(f.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>index.html missing — place it next to server.py</h1>", 404)

@app.get("/manifest.json")
async def manifest():
    base_url = os.environ.get("APP_URL", "http://localhost:8000")
    return JSONResponse({
        "name": "DarkStare AI",
        "short_name": "DarkStare",
        "description": "Dual-AI Forex & Gold Trading Brain",
        "start_url": "/", "display": "standalone",
        "background_color": "#050a0f", "theme_color": "#d4a017",
        "orientation": "any",
        "icons": [{"src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' fill='%23050a0f' rx='20'/%3E%3Ctext y='.88em' font-size='72' x='12'%3E%E2%9A%A1%3C/text%3E%3C/svg%3E","sizes":"512x512","type":"image/svg+xml","purpose":"any maskable"}],
        "share_target": {"action": "/", "method": "GET", "params": {"title": "title"}}
    })

@app.get("/sw.js")
async def sw():
    return Response(
        "const CACHE='ds-v4';\n"
        "self.addEventListener('install',e=>self.skipWaiting());\n"
        "self.addEventListener('activate',e=>clients.claim());\n"
        "self.addEventListener('fetch',e=>{\n"
        "  if(e.request.method!=='GET')return;\n"
        "  e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));\n"
        "});\n",
        media_type="application/javascript"
    )

# ── Auth ──────────────────────────────────────────────────────────────────
@app.post("/api/auth/register")
async def register(req: Request):
    data  = await req.json()
    name  = str(data.get("name",  "")).strip()
    email = str(data.get("email", "")).strip().lower()
    pw    = str(data.get("password", "")).strip()

    if not name or not email or not pw:
        return JSONResponse({"error": "Name, email and password are required"})
    if len(pw) < 6:
        return JSONResponse({"error": "Password must be at least 6 characters"})
    if not re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return JSONResponse({"error": "Please enter a valid email address"})

    db  = load_db()
    for u in db["users"].values():
        if u.get("email") == email:
            return JSONResponse({"error": "Email already registered — please sign in"})

    uid = hashlib.sha256(email.encode()).hexdigest()[:16]
    # First user becomes admin
    is_first = len(db["users"]) == 0
    db["users"][uid] = {
        "id": uid, "name": name, "email": email,
        "password": hash_pw(pw),
        "tier": "elite" if is_first else "free",
        "joined": datetime.now().isoformat(),
        "usage": {}, "history": [],
        "feedback": {"good": 0, "bad": 0, "total": 0},
        "active": True,
        "is_admin": is_first,
    }
    save_db(db)

    # Save first user as admin in config
    if is_first:
        save_cfg_safe({"admins": [email]})

    token = make_token(uid)
    u     = db["users"][uid]
    return JSONResponse({
        "success": True, "token": token,
        "user": {"id": uid, "name": name, "email": email,
                 "tier": u["tier"], "is_admin": is_first}
    })

@app.post("/api/auth/login")
async def login(req: Request):
    data  = await req.json()
    email = str(data.get("email",    "")).strip().lower()
    pw    = str(data.get("password", "")).strip()

    if not email or not pw:
        return JSONResponse({"error": "Email and password required"})

    db = load_db()
    for uid, u in db["users"].items():
        if u.get("email") == email:
            if not u.get("active", True):
                return JSONResponse({"error": "Account suspended — contact support"})
            if u.get("password") != hash_pw(pw):
                return JSONResponse({"error": "Incorrect password"})
            token = make_token(uid)
            return JSONResponse({
                "success": True, "token": token,
                "user": {"id": uid, "name": u["name"], "email": email,
                         "tier": u.get("tier","free"), "is_admin": u.get("is_admin",False)}
            })
    return JSONResponse({"error": "No account found with that email"})

@app.get("/api/auth/me")
async def me(req: Request):
    u = get_user(req)
    if not u: return JSONResponse({"logged_in": False})
    tier_info = TIERS[u.get("tier","free")]
    today     = datetime.now().strftime("%Y-%m-%d")
    used      = u.get("usage", {}).get(today, 0)
    return JSONResponse({
        "logged_in":   True,
        "user":        {"id":u["id"],"name":u["name"],"email":u["email"],"tier":u.get("tier","free"),"is_admin":u.get("is_admin",False)},
        "tier_info":   tier_info,
        "usage_today": used,
        "usage_limit": tier_info["analyses_per_day"],
    })

@app.post("/api/auth/logout")
async def logout(): return JSONResponse({"success": True})

# ── Keys (SAFE — never deletes existing keys) ─────────────────────────────
@app.post("/api/keys")
async def save_keys(req: Request):
    data = await req.json()
    save_cfg_safe(data)  # merges, never overwrites unset keys
    return JSONResponse({"success": True, "message": "Keys saved permanently"})

@app.get("/api/keys/load")
async def load_keys_endpoint():
    """Return masked existing keys so UI can show what's saved"""
    cfg  = load_cfg()
    keys = cfg.get("keys", {})
    masked = {}
    for k, v in keys.items():
        if v:
            # Show first 4 and last 4 chars, mask middle
            if len(v) > 10:
                masked[k] = v[:4] + "•" * (len(v) - 8) + v[-4:]
            else:
                masked[k] = "•" * len(v)
    masked["mt5_path"] = cfg.get("mt5_path", "")
    return JSONResponse({"saved_keys": masked, "has_keys": {k: bool(v) for k,v in keys.items()}})

@app.get("/api/keys/status")
async def keys_status():
    names = ["anthropic","openai","newsapi","av","twitter","stripe"]
    return JSONResponse({n: bool(get_key(n)) for n in names})

@app.post("/api/keys/test")
async def test_key(req: Request):
    data  = await req.json()
    ktype = data.get("type","")
    kval  = get_key(ktype)
    if not kval: return JSONResponse({"status":"not_set","message":"Key not saved yet"})
    try:
        async with httpx.AsyncClient(timeout=14) as c:
            if ktype == "newsapi":
                r = await c.get(f"https://newsapi.org/v2/top-headlines?category=business&pageSize=1&apiKey={kval}")
                d = r.json()
                if d.get("status")=="ok": return JSONResponse({"status":"ok","message":f"✓ NewsAPI live — {d.get('totalResults',0)} articles"})
                return JSONResponse({"status":"error","message":d.get("message","Invalid key")})
            elif ktype == "openai":
                r = await c.get("https://api.openai.com/v1/models",headers={"Authorization":f"Bearer {kval}"})
                if r.status_code==200: return JSONResponse({"status":"ok","message":"✓ OpenAI valid — GPT-4o ready"})
                return JSONResponse({"status":"error","message":r.json().get("error",{}).get("message","Invalid")})
            elif ktype == "anthropic":
                r = await c.post("https://api.anthropic.com/v1/messages",headers={"x-api-key":kval,"Content-Type":"application/json","anthropic-version":"2023-06-01"},json={"model":"claude-haiku-4-5-20251001","max_tokens":5,"messages":[{"role":"user","content":"hi"}]})
                if r.status_code==200: return JSONResponse({"status":"ok","message":"✓ Anthropic valid — Claude ready"})
                return JSONResponse({"status":"error","message":r.json().get("error",{}).get("message","Invalid")})
            elif ktype == "av":
                r = await c.get(f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=EUR&apikey={kval}")
                d = r.json(); rate = d.get("Realtime Currency Exchange Rate",{})
                if rate: return JSONResponse({"status":"ok","message":f"✓ Alpha Vantage live — USDEUR={float(rate.get('5. Exchange Rate',0)):.5f}"})
                return JSONResponse({"status":"error","message":d.get("Note",d.get("Information","Rate limited"))})
            elif ktype == "twitter":
                r = await c.get("https://api.twitter.com/2/tweets/search/recent?query=gold&max_results=10",headers={"Authorization":f"Bearer {kval}"})
                if r.status_code==200: return JSONResponse({"status":"ok","message":"✓ X/Twitter valid"})
                return JSONResponse({"status":"error","message":f"HTTP {r.status_code}"})
            elif ktype == "stripe":
                r = await c.get("https://api.stripe.com/v1/account",headers={"Authorization":f"Bearer {kval}"})
                if r.status_code==200: return JSONResponse({"status":"ok","message":"✓ Stripe valid — payments ready"})
                return JSONResponse({"status":"error","message":"Invalid Stripe key"})
    except Exception as e:
        return JSONResponse({"status":"error","message":str(e)})
    return JSONResponse({"status":"error","message":"Unknown key type"})

# ── Tiers & subscription ──────────────────────────────────────────────────
@app.get("/api/tiers")
async def get_tiers():
    return JSONResponse(TIERS)

@app.post("/api/subscribe")
async def subscribe(req: Request):
    data = await req.json()
    u    = get_user(req)
    if not u: return JSONResponse({"error":"Not logged in"})
    tier = data.get("tier","free")
    code = data.get("payment_code","").strip().upper()
    if tier not in TIERS: return JSONResponse({"error":"Invalid tier"})

    # Stripe checkout
    stripe_key = get_key("stripe")
    if stripe_key and tier != "free":
        price_ids = {"starter":"price_starter","pro":"price_pro","elite":"price_elite"}
        pid = price_ids.get(tier)
        app_url = os.environ.get("APP_URL","http://localhost:8000")
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post("https://api.stripe.com/v1/checkout/sessions",
                    headers={"Authorization":f"Bearer {stripe_key}"},
                    data={"payment_method_types[]":"card","mode":"subscription",
                          "line_items[0][price]":pid,"line_items[0][quantity]":"1",
                          "success_url":f"{app_url}/?upgraded={tier}",
                          "cancel_url":f"{app_url}/","client_reference_id":u["id"]})
                d = r.json()
                if "url" in d: return JSONResponse({"checkout_url":d["url"]})
        except:
            pass

    # Demo / promo codes
    demo_map = {"DEMO-FREE":"free","DEMO-STARTER":"starter","DEMO-PRO":"pro","DEMO-ELITE":"elite",
                "FREE":"free","STARTER":"starter","PRO":"pro","ELITE":"elite"}
    if code in demo_map:
        new_tier = demo_map[code]
        db = load_db()
        db["users"][u["id"]]["tier"] = new_tier
        save_db(db)
        return JSONResponse({"success":True,"tier":new_tier,"message":f"✓ Upgraded to {new_tier.title()} plan!"})

    return JSONResponse({
        "info":"Add your Stripe price IDs to activate real payments",
        "demo":"Test codes: DEMO-STARTER  DEMO-PRO  DEMO-ELITE",
        "error":"Payment not fully configured yet"
    })

# ── Admin ─────────────────────────────────────────────────────────────────
@app.get("/api/admin/stats")
async def admin_stats(req: Request):
    u = require_user(req)
    if not u.get("is_admin"): raise HTTPException(403,"Admin only")
    db    = load_db()
    users = list(db["users"].values())
    tiers = {t:sum(1 for x in users if x.get("tier")==t) for t in TIERS}
    today = datetime.now().strftime("%Y-%m-%d")
    return JSONResponse({
        "total_users": len(users),
        "active_today": sum(1 for x in users if x.get("usage",{}).get(today,0)>0),
        "tiers": tiers,
        "revenue_est_monthly": tiers.get("starter",0)*5+tiers.get("pro",0)*15+tiers.get("elite",0)*30,
        "analyses_today": sum(x.get("usage",{}).get(today,0) for x in users),
    })

@app.post("/api/admin/set_tier")
async def admin_set_tier(req: Request):
    u = require_user(req)
    if not u.get("is_admin"): raise HTTPException(403,"Admin only")
    data = await req.json()
    db   = load_db()
    uid  = data.get("user_id","")
    tier = data.get("tier","free")
    if uid in db["users"] and tier in TIERS:
        db["users"][uid]["tier"] = tier
        save_db(db)
        return JSONResponse({"success":True})
    return JSONResponse({"error":"User not found"})

# ── Built-in AI Engine ────────────────────────────────────────────────────
class DarkStareEngine:
    BULL=["rise","rising","surge","gains","rally","bullish","buy","strong","boom","growth","up","high","breakout","recovery","increase","demand","positive","jump","soar","climb"]
    BEAR=["fall","falling","drop","decline","crash","bearish","sell","weak","recession","negative","down","low","selloff","fear","risk","crisis","inflation","loss","plunge","tumble"]
    GOLD_BULL=["war","conflict","tension","inflation","uncertainty","sanctions","safe haven","geopolitical","rate cut","dollar weak","fed pause","uncertainty","unrest"]
    GOLD_BEAR=["rate hike","dollar strong","economy good","growth","optimism","risk on","stability","peace","recovery","strong dollar"]

    def score_news(self, text:str, pair:str)->dict:
        t=text.lower()
        b=sum(t.count(w) for w in self.BULL)
        s=sum(t.count(w) for w in self.BEAR)
        if "XAU" in pair or "GOLD" in pair:
            b+=sum(t.count(w) for w in self.GOLD_BULL)*2
            s+=sum(t.count(w) for w in self.GOLD_BEAR)*2
        tot=b+s
        if tot==0: return {"bull":0,"bear":0,"sentiment":"NEUTRAL","score":0.0}
        score=(b-s)/tot
        sent="BULLISH" if score>0.1 else "BEARISH" if score<-0.1 else "NEUTRAL"
        return {"bull":b,"bear":s,"sentiment":sent,"score":round(score,3)}

    def score_prices(self, prices:dict, pair:str)->dict:
        p=prices.get(pair,{})
        if not p: return {"price":0,"spread_pct":0,"quality":0.5,"score":0.25}
        price=p.get("price",0)
        bid=p.get("bid",price); ask=p.get("ask",price)
        spread_pct=((ask-bid)/price*100) if price>0 else 0
        quality=max(0,1-spread_pct*10)
        return {"price":price,"bid":bid,"ask":ask,"spread_pct":round(spread_pct,4),"quality":round(quality,2),"score":round(quality*0.5,3)}

    def score_poly(self, text:str)->dict:
        lines=[l for l in text.split("\n") if "%" in l]
        pcts=[]
        for l in lines:
            m=re.search(r"(\d+)%",l)
            if m: pcts.append(int(m.group(1)))
        avg=sum(pcts)/len(pcts) if pcts else 50
        return {"avg_yes":round(avg,1),"score":round((avg-50)/100,3)}

    def get_session(self)->dict:
        h=datetime.utcnow().hour
        if 8<=h<17:   return {"session":"LONDON","mult":1.2}
        elif 13<=h<22: return {"session":"NEW_YORK","mult":1.3}
        elif 0<=h<8:   return {"session":"TOKYO","mult":0.9}
        else:          return {"session":"OFF-HOURS","mult":0.7}

    def analyze(self, pair:str, news:str, prices_obj:dict, poly:str, x_data:str, feedback:dict)->dict:
        ts=datetime.now().strftime("%H:%M:%S")
        ns=self.score_news(news,pair)
        ps=self.score_prices(prices_obj,pair)
        ls=self.score_poly(poly)
        sess=self.get_session()
        xs=0.3 if "BULLISH" in x_data.upper() else -0.3 if "BEARISH" in x_data.upper() else 0
        total=feedback.get("total",0)
        lm=0.7 if total>5 and feedback.get("good",0)/total<0.5 else 1.1 if total>5 and feedback.get("good",0)/total>0.7 else 1.0
        comp=(ns["score"]*0.35+ps["score"]*0.25+ls["score"]*0.20+xs*0.20)*sess["mult"]*lm
        direction="BUY" if comp>0.12 else "SELL" if comp<-0.12 else "WAIT"
        conf=min(92,max(40,int(abs(comp)*200+40)))
        if direction=="WAIT": conf=max(40,conf-15)
        risk="LOW" if conf>75 else "MEDIUM" if conf>58 else "HIGH"
        price=ps.get("price",0)
        if price>0:
            atr=price*0.003
            if direction=="BUY":
                entry=f"{price:.5f}–{price*1.0005:.5f}"; sl=f"{price-atr*1.5:.5f}"; tp=f"{price+atr*2.5:.5f}"; rr="1:1.7"
            elif direction=="SELL":
                entry=f"{price:.5f}–{price*0.9995:.5f}"; sl=f"{price+atr*1.5:.5f}"; tp=f"{price-atr*2.5:.5f}"; rr="1:1.7"
            else:
                entry=f"Near {price:.5f}"; sl="—"; tp="—"; rr="—"
        else:
            entry="Add Alpha Vantage key for live entry"; sl="—"; tp="—"; rr="—"
        factors=[
            f"News: {ns['bull']} bullish vs {ns['bear']} bearish signals detected",
            f"Polymarket crowd: {ls['avg_yes']}% avg YES probability",
            f"Session: {sess['session']} (activity multiplier ×{sess['mult']})",
        ]
        if xs!=0: factors.append(f"X/Twitter: {'bullish' if xs>0 else 'bearish'} sentiment")
        return {"signal":direction,"pair":pair,"confidence":conf,"entry":entry,"stopLoss":sl,"takeProfit":tp,"riskReward":rr,"riskLevel":risk,"timeframe":"H1","sentiment":ns["sentiment"],"keyFactors":factors,"reasoning":f"DarkStare Engine ({ts}): composite={comp:.3f} → {direction}. News score={ns['score']:.2f}, price quality={ps.get('quality',0):.0%}, polymarket={ls['avg_yes']}%, session={sess['session']}×{sess['mult']}, self-learn×{lm}","marketContext":f"Analyzing {pair} with live composite scoring across {len(factors)} data dimensions.","warnings":f"{'Low confidence — wait for clearer setup.' if conf<55 else 'Always use stop loss. Past performance ≠ future results.'} Risk: {risk}.","dataSource":"BUILT-IN ENGINE","engine":"DarkStare v4","signalTime":ts,"scores":{"composite":round(comp,4),"news":ns["score"],"price":ps.get("quality",0),"poly":ls["score"],"x":xs,"session":sess["mult"]}}

engine = DarkStareEngine()

# ── Live data ─────────────────────────────────────────────────────────────
async def fetch_news()->dict:
    k=get_key("newsapi")
    if not k: return {"data":"[NewsAPI key not set — add in Settings]","source":"none","articles":[],"ts":None}
    q=random.choice(["gold USD forex inflation federal reserve","war geopolitics commodities oil","central bank currency interest rates"])
    try:
        async with httpx.AsyncClient(timeout=12) as c:
            r=await c.get(f"https://newsapi.org/v2/everything?q={q}&sortBy=publishedAt&language=en&pageSize=12&apiKey={k}")
            d=r.json()
        if d.get("status")!="ok": return {"data":f"[NewsAPI: {d.get('message','Error')}]","source":"error","articles":[],"ts":None}
        arts=d.get("articles",[])[:10]
        lines=[f"• [{a.get('publishedAt','')[:16].replace('T',' ')}] {a.get('title','')} ({a.get('source',{}).get('name','')})" for a in arts]
        return {"data":"\n".join(lines),"source":"newsapi","articles":arts,"count":len(arts),"ts":datetime.now().strftime("%H:%M:%S")}
    except Exception as e:
        return {"data":f"[News error: {e}]","source":"error","articles":[],"ts":None}

async def fetch_prices()->dict:
    k=get_key("av")
    if not k: return {"data":"[Alpha Vantage key not set]","prices":{},"source":"none","ts":None}
    pairs_list=[("USD","XAU"),("EUR","USD"),("GBP","USD"),("USD","JPY")]
    prices={}
    async with httpx.AsyncClient(timeout=25) as c:
        for fc,tc in pairs_list:
            try:
                r=await c.get(f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={fc}&to_currency={tc}&apikey={k}")
                d=r.json(); rate=d.get("Realtime Currency Exchange Rate",{})
                if rate: prices[f"{fc}{tc}"]={"price":float(rate.get("5. Exchange Rate",0)),"bid":float(rate.get("8. Bid Price") or 0),"ask":float(rate.get("9. Ask Price") or 0),"updated":rate.get("6. Last Refreshed","")}
                elif "Note" in d or "Information" in d: break
            except: pass
            await asyncio.sleep(0.3)
    lines=[f"• {p}: {v['price']:.5f} bid={v['bid']:.5f} ask={v['ask']:.5f}" for p,v in prices.items()]
    ts=datetime.now().strftime("%H:%M:%S")
    return {"data":"\n".join(lines) if lines else "[Rate limited — wait 60s]","prices":prices,"source":"alphavantage" if prices else "ratelimited","ts":ts}

async def fetch_poly()->dict:
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r=await c.get("https://gamma-api.polymarket.com/markets?limit=12&active=true")
            d=r.json()
        items=d[:8] if isinstance(d,list) else []
        lines=[f"• {m.get('question','')} → {round(float((m.get('outcomePrices') or ['.5'])[0])*100)}% YES" for m in items]
        return {"data":"\n".join(lines) or "[No markets]","source":"polymarket","ts":datetime.now().strftime("%H:%M:%S")}
    except Exception as e:
        return {"data":f"[Polymarket unavailable: {e}]","source":"error"}

async def fetch_x()->dict:
    k=get_key("twitter")
    if not k: return {"data":"[X/Twitter key optional]","source":"none","sentiment":"NEUTRAL"}
    q=random.choice(["XAUUSD OR gold bullish bearish","forex USD dollar","Fed interest rates"])
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r=await c.get(f"https://api.twitter.com/2/tweets/search/recent?query={q}&max_results=25&tweet.fields=text",headers={"Authorization":f"Bearer {k}"})
            d=r.json()
        tweets=[t.get("text","") for t in d.get("data",[])]
        if not tweets: return {"data":"[No tweets found]","source":"twitter","sentiment":"NEUTRAL"}
        bw=["bullish","buy","long","moon","strong","up","rise"]; sw=["bearish","sell","short","crash","weak","down","fall"]
        b=sum(any(w in t.lower() for w in bw) for t in tweets)
        s=sum(any(w in t.lower() for w in sw) for t in tweets)
        sent="BULLISH" if b>s else "BEARISH" if s>b else "NEUTRAL"
        return {"data":f"X: {sent} ({b} bull/{s} bear of {len(tweets)} tweets)\n"+"".join(f"  ▸ {t[:100]}\n" for t in tweets[:4]),"source":"twitter","sentiment":sent}
    except Exception as e:
        return {"data":f"[X error: {e}]","source":"error","sentiment":"NEUTRAL"}

@app.get("/api/intel")
async def full_intel():
    news,prices,poly,x=await asyncio.gather(fetch_news(),fetch_prices(),fetch_poly(),fetch_x())
    combined=f"PRICES:\n{prices['data']}\n\nNEWS:\n{news['data']}\n\nPOLYMARKET:\n{poly['data']}\n\nX:\n{x['data']}"
    return JSONResponse({"news":news,"prices":prices,"polymarket":poly,"x":x,"combined":combined,"ts":datetime.now().strftime("%H:%M:%S")})

@app.get("/api/news");       async def r_news():   return JSONResponse(await fetch_news())
@app.get("/api/prices");     async def r_prices():  return JSONResponse(await fetch_prices())
@app.get("/api/polymarket"); async def r_poly():    return JSONResponse(await fetch_poly())
@app.get("/api/x");          async def r_x():       return JSONResponse(await fetch_x())

# ── Analyze ───────────────────────────────────────────────────────────────
@app.post("/api/analyze")
async def analyze(req: Request):
    body      = await req.json()
    ai_model  = body.get("ai","darkstare")
    news      = body.get("news","[no news]")
    prices_d  = body.get("prices","[no prices]")
    prices_o  = body.get("prices_obj",{})
    poly      = body.get("polymarket","[no poly]")
    x_data    = body.get("x","[no x]")
    pairs     = body.get("pairs",["XAUUSD","EURUSD"])
    feedback  = body.get("feedback",{"good":0,"bad":0,"total":0})
    pair      = pairs[0] if pairs else "XAUUSD"
    ts        = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    u         = get_user(req)

    if u:
        if not check_limit(u):
            t=TIERS[u.get("tier","free")]
            return JSONResponse({"error":f"Daily limit ({t['analyses_per_day']}/day on {t['name']}). Upgrade for more."})
        if ai_model in ["claude","gpt"] and not TIERS[u.get("tier","free")]["ext_ai"]:
            return JSONResponse({"error":"Claude/GPT requires Pro plan. Use Built-in Engine or upgrade."})
        bump_usage(u["id"])

    if ai_model=="darkstare":
        return JSONResponse(engine.analyze(pair,news,prices_o,poly,x_data,feedback))

    prompt=f"""You are DARKSTARE, elite quantitative trading analyst. Time: {ts}
LIVE DATA — PRICES: {prices_d} | NEWS: {news} | POLYMARKET: {poly} | X: {x_data}
PAIRS: {', '.join(pairs)}
Respond ONLY with JSON (no markdown): {{"signal":"BUY","pair":"{pair}","confidence":76,"entry":"0","stopLoss":"0","takeProfit":"0","riskReward":"1:2","riskLevel":"MEDIUM","timeframe":"H1","sentiment":"BULLISH","keyFactors":["f1","f2","f3"],"reasoning":"...","marketContext":"...","warnings":"...","dataSource":"LIVE","signalTime":"{datetime.now().strftime('%H:%M:%S')}"}}"""

    try:
        txt=""
        if ai_model=="claude":
            k=get_key("anthropic")
            if not k: return JSONResponse({"error":"Anthropic key not configured in Settings"})
            async with httpx.AsyncClient(timeout=55) as c:
                r=await c.post("https://api.anthropic.com/v1/messages",headers={"x-api-key":k,"Content-Type":"application/json","anthropic-version":"2023-06-01"},json={"model":"claude-sonnet-4-6","max_tokens":1200,"messages":[{"role":"user","content":prompt}]})
            d=r.json()
            if "error" in d: return JSONResponse({"error":d["error"].get("message","Anthropic error")})
            txt=next((b["text"] for b in d.get("content",[]) if b.get("type")=="text"),"")
        elif ai_model=="gpt":
            k=get_key("openai")
            if not k: return JSONResponse({"error":"OpenAI key not configured in Settings"})
            async with httpx.AsyncClient(timeout=55) as c:
                r=await c.post("https://api.openai.com/v1/chat/completions",headers={"Content-Type":"application/json","Authorization":f"Bearer {k}"},json={"model":"gpt-4o-mini","max_tokens":1200,"messages":[{"role":"system","content":"Respond ONLY with valid JSON. No markdown."},{"role":"user","content":prompt}]})
            d=r.json()
            if "error" in d: return JSONResponse({"error":d["error"].get("message","OpenAI error")})
            txt=d["choices"][0]["message"]["content"]
        txt=txt.strip()
        if txt.startswith("```"): txt=txt.split("\n",1)[-1]
        if txt.endswith("```"): txt=txt[:-3]
        return JSONResponse(json.loads(txt.strip()))
    except json.JSONDecodeError as e:
        return JSONResponse({"error":f"JSON parse failed: {e}"})
    except Exception as e:
        return JSONResponse({"error":str(e)})

# ── Chat ──────────────────────────────────────────────────────────────────
@app.post("/api/chat")
async def chat(req: Request):
    body=await req.json()
    ai=body.get("ai","darkstare")
    messages=body.get("messages",[])
    live_ctx=body.get("live_context","")
    u=get_user(req)
    system=f"You are DARKSTARE, elite AI trading analyst. Sharp, direct, actionable. Time: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}."
    if live_ctx: system+=f"\n\nLIVE MARKET DATA:\n{live_ctx[:800]}"

    if ai=="darkstare" or (u and not TIERS[u.get("tier","free")]["ext_ai"]):
        last=messages[-1]["content"].lower() if messages else ""
        if any(w in last for w in ["gold","xau"]):
            resp="GOLD (XAUUSD): Safe-haven driven by USD strength, inflation, geopolitics, and central bank demand. Key drivers: Fed rate decisions, geopolitical events, DXY index. Use ANALYZE for a live signal."
        elif any(w in last for w in ["eur","euro"]):
            resp="EURUSD: Driven by ECB vs Fed policy divergence, European economic data, risk sentiment. Watch ECB meetings, German PMI, US NFP. Currently in a macro-driven range."
        elif any(w in last for w in ["btc","bitcoin","crypto"]):
            resp="Bitcoin: Driven by institutional flows, ETF inflows, regulatory news, and macro risk appetite. Correlates with tech stocks. Watch for ETF flow data and Fed pivot signals."
        elif any(w in last for w in ["upgrade","plan","pro","price","cost","pay"]):
            resp="Plans: Free (3/day) → Starter $5/mo (20/day + MT5) → Pro $15/mo (100/day + Claude + GPT) → Elite $30/mo (unlimited). Use promo code DEMO-PRO to test Pro features."
        elif any(w in last for w in ["how","work","engine","built"]):
            resp="DarkStare Engine scores: news sentiment keywords (35%), live price spread quality (25%), Polymarket prediction odds (20%), X/Twitter sentiment (20%). Adjusted by trading session timing and your win-rate feedback. No external AI API needed."
        else:
            resp="I'm DARKSTARE, your AI trading analyst. Ask me about any currency pair, market condition, or trading strategy. For live AI signals, click ANALYZE NOW on the dashboard."
        return JSONResponse({"response":resp,"engine":"DarkStare Built-in"})

    try:
        if ai=="claude":
            k=get_key("anthropic")
            if not k: return JSONResponse({"error":"Anthropic key not set"})
            async with httpx.AsyncClient(timeout=40) as c:
                r=await c.post("https://api.anthropic.com/v1/messages",headers={"x-api-key":k,"Content-Type":"application/json","anthropic-version":"2023-06-01"},json={"model":"claude-sonnet-4-6","max_tokens":900,"system":system,"messages":messages})
            d=r.json()
            if "error" in d: return JSONResponse({"error":d["error"].get("message","Error")})
            return JSONResponse({"response":next((b["text"] for b in d.get("content",[]) if b.get("type")=="text"),"")})
        elif ai=="gpt":
            k=get_key("openai")
            if not k: return JSONResponse({"error":"OpenAI key not set"})
            async with httpx.AsyncClient(timeout=40) as c:
                r=await c.post("https://api.openai.com/v1/chat/completions",headers={"Content-Type":"application/json","Authorization":f"Bearer {k}"},json={"model":"gpt-4o-mini","max_tokens":800,"messages":[{"role":"system","content":system}]+messages})
            d=r.json()
            if "error" in d: return JSONResponse({"error":d["error"].get("message","Error")})
            return JSONResponse({"response":d["choices"][0]["message"]["content"]})
    except Exception as e:
        return JSONResponse({"error":str(e)})

# ── Feedback & History ────────────────────────────────────────────────────
@app.post("/api/feedback")
async def save_feedback(req: Request):
    data=await req.json()
    u=get_user(req)
    if u:
        db=load_db()
        fb=db["users"][u["id"]].get("feedback",{"good":0,"bad":0,"total":0})
        fb["good"]+=data.get("good",0); fb["bad"]+=data.get("bad",0); fb["total"]+=data.get("total",0)
        db["users"][u["id"]]["feedback"]=fb; save_db(db)
        return JSONResponse({"success":True,"feedback":fb})
    cfg=load_cfg()
    fb=cfg.get("feedback",{"good":0,"bad":0,"total":0})
    fb["good"]+=data.get("good",0); fb["bad"]+=data.get("bad",0); fb["total"]+=data.get("total",0)
    cfg["feedback"]=fb; CFG_FILE.write_text(json.dumps(cfg,indent=2),encoding="utf-8")
    return JSONResponse({"success":True,"feedback":fb})

@app.get("/api/feedback")
async def get_feedback(req: Request):
    u=get_user(req)
    if u:
        db=load_db(); return JSONResponse(db["users"][u["id"]].get("feedback",{"good":0,"bad":0,"total":0}))
    return JSONResponse(load_cfg().get("feedback",{"good":0,"bad":0,"total":0}))

@app.post("/api/history/add")
async def add_history(req: Request):
    data=await req.json(); entries=data.get("entries",[])
    u=get_user(req)
    if u:
        db=load_db(); h=db["users"][u["id"]].get("history",[])
        limit=TIERS[u.get("tier","free")]["history"]
        h=h+entries; h=h[-limit:]; db["users"][u["id"]]["history"]=h; save_db(db)
    return JSONResponse({"success":True})

@app.get("/api/history")
async def get_history(req: Request):
    u=get_user(req)
    if u:
        db=load_db(); return JSONResponse({"history":db["users"][u["id"]].get("history",[])})
    return JSONResponse({"history":[]})

@app.delete("/api/history")
async def clear_history(req: Request):
    u=get_user(req)
    if u:
        db=load_db(); db["users"][u["id"]]["history"]=[]; save_db(db)
    return JSONResponse({"success":True})

# ── MT5 ───────────────────────────────────────────────────────────────────
@app.post("/api/mt5/signal")
async def mt5_write(req: Request):
    body=await req.json()
    u=get_user(req)
    if u and not TIERS[u.get("tier","free")]["mt5"]:
        return JSONResponse({"error":"MT5 requires Starter plan or above"})
    sig=f"SIGNAL:{body.get('signal','NONE')}|PAIR:{body.get('pair','')}|ENTRY:{body.get('entry','')}|SL:{body.get('stopLoss','')}|TP:{body.get('takeProfit','')}|CONF:{body.get('confidence',0)}|TF:{body.get('timeframe','H1')}|T:{int(time.time())}"
    written,errors=[],[]
    try: SIG_FILE.write_text(sig,encoding="utf-8"); written.append(str(SIG_FILE))
    except Exception as e: errors.append(str(e))
    mt5_path=load_cfg().get("mt5_path","").strip()
    if mt5_path:
        try: Path(mt5_path).write_text(sig,encoding="utf-8"); written.append(mt5_path)
        except Exception as e: errors.append(str(e))
    return JSONResponse({"success":bool(written),"signal":sig,"written_to":written,"errors":errors})

@app.get("/api/mt5/read")
async def mt5_read():
    sig=SIG_FILE.read_text(encoding="utf-8") if SIG_FILE.exists() else "SIGNAL:NONE"
    return JSONResponse({"signal":sig,"exists":SIG_FILE.exists()})

@app.post("/api/mt5/clear")
async def mt5_clear():
    try: SIG_FILE.write_text("SIGNAL:NONE",encoding="utf-8"); return JSONResponse({"success":True})
    except Exception as e: return JSONResponse({"success":False,"error":str(e)})

# ── Status ────────────────────────────────────────────────────────────────
@app.get("/api/status")
async def status(req: Request):
    ip=local_ip(); u=get_user(req)
    return JSONResponse({"running":True,"version":"4.0","time":datetime.now().isoformat(),"local_ip":ip,"mobile_url":f"http://{ip}:8000","app_url":os.environ.get("APP_URL",f"http://localhost:8000"),"built_in_engine":"ready","logged_in":bool(u),"keys":{"anthropic":bool(get_key("anthropic")),"openai":bool(get_key("openai")),"newsapi":bool(get_key("newsapi")),"av":bool(get_key("av")),"stripe":bool(get_key("stripe"))}})

@app.get("/api/admin/stats")
async def a_stats(req: Request):
    u=require_user(req)
    if not u.get("is_admin"): raise HTTPException(403,"Admin only")
    db=load_db(); users=list(db["users"].values())
    tiers={t:sum(1 for x in users if x.get("tier")==t) for t in TIERS}
    today=datetime.now().strftime("%Y-%m-%d")
    return JSONResponse({"total_users":len(users),"tiers":tiers,"revenue_est":tiers.get("starter",0)*5+tiers.get("pro",0)*15+tiers.get("elite",0)*30,"analyses_today":sum(x.get("usage",{}).get(today,0) for x in users)})

# ── Launch ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ip=local_ip()
    port=int(os.environ.get("PORT",8000))
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║   DARKSTARE AI TRADING BRAIN v4.0 — BUSINESS EDITION     ║
╠═══════════════════════════════════════════════════════════╣
║  Local:    http://localhost:{port}                           ║
║  Network:  http://{ip}:{port}
╠═══════════════════════════════════════════════════════════╣
║  Built-in AI: READY — no API keys needed                  ║
║  First user registered = auto Admin + Elite tier          ║
╠═══════════════════════════════════════════════════════════╣
║  Cloud deploy: see README_DEPLOY.md                       ║
╚═══════════════════════════════════════════════════════════╝
""")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
