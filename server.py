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

# ── Paths ────────────────────────────────────────────────────────────────
BASE     = Path(__file__).parent
DB_FILE  = Path(os.environ.get("DB_PATH",  str(BASE / "database.json")))
CFG_FILE = Path(os.environ.get("CFG_PATH", str(BASE / "config.json")))
SIG_FILE = BASE / "darkstare_signal.txt"

# ── Secret (override with env var in production) ──────────────────────────
SECRET = os.environ.get("APP_SECRET", "DARKSTARE-SECRET-CHANGE-IN-PRODUCTION-2025")

# ── Tiers ────────────────────────────────────────────────────────────────
TIERS = {
    "free":    {"name":"Free",    "price":0,  "analyses_per_day":3,   "pairs":2,  "chat":False,"ext_ai":False,"mt5":False, "history":10},
    "starter": {"name":"Starter", "price":5,  "analyses_per_day":20,  "pairs":5,  "chat":True, "ext_ai":False,"mt5":True,  "history":100},
    "pro":     {"name":"Pro",     "price":15, "analyses_per_day":100, "pairs":10, "chat":True, "ext_ai":True, "mt5":True,  "history":500},
    "elite":   {"name":"Elite",   "price":30, "analyses_per_day":9999,"pairs":99, "chat":True, "ext_ai":True, "mt5":True,  "history":9999},
}

def load_db() -> dict:
    try:
        if DB_FILE.exists():
            return json.loads(DB_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"users": {}}

def save_db(db: dict):
    DB_FILE.write_text(json.dumps(db, indent=2), encoding="utf-8")

def load_cfg() -> dict:
    try:
        if CFG_FILE.exists():
            return json.loads(CFG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

def save_cfg_safe(updates: dict):
    cfg = load_cfg()
    if "keys" not in cfg:
        cfg["keys"] = {}
    for k, v in updates.items():
        if k == "mt5_path":
            cfg["mt5_path"] = str(v).strip()
        elif k == "admins":
            cfg["admins"] = v
        elif v and str(v).strip():
            cfg["keys"][k] = str(v).strip()
    CFG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def get_key(name: str) -> str:
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
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def hash_pw(pw: str) -> str:
    return hashlib.sha256((SECRET + pw + SECRET).encode()).hexdigest()

def make_token(uid: str) -> str:
    ts  = str(int(time.time()))
    raw = f"{uid}|{ts}"
    sig = hmac.new(SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()[:24]
    payload = base64.urlsafe_b64encode(f"{raw}|{sig}".encode()).decode()
    return payload

def verify_token(token: str) -> Optional[str]:
    try:
        raw     = base64.urlsafe_b64decode(token.encode() + b"==").decode()
        parts   = raw.split("|")
        if len(parts) != 3: return None
        uid, ts, sig = parts
        if int(time.time()) - int(ts) > 86400 * 60: return None
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

app = FastAPI(title="DarkStare AI", version="4.0")

@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin   = request.headers.get("origin", "")
    response = await call_next(request)
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

@app.get("/", response_class=HTMLResponse)
async def index():
    f = BASE / "index.html"
    if f.exists(): return HTMLResponse(f.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>index.html missing — place it next to server.py</h1>", 404)

@app.get("/manifest.json")
async def manifest():
    base_url = os.environ.get("APP_URL", "http://localhost:8000")
    return JSONResponse({"name": "DarkStare AI", "short_name": "DarkStare"})

@app.get("/sw.js")
async def sw():
    return Response("const CACHE='ds-v4';\n", media_type="application/javascript")

@app.post("/api/auth/register")
async def register(req: Request):
    data = await req.json()
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    pw = str(data.get("password", "")).strip()
    
    if not name or not email or not pw:
        return JSONResponse({"error": "Name, email and password are required"})
    if len(pw) < 6:
        return JSONResponse({"error": "Password must be at least 6 characters"})
    
    db = load_db()
    for u in db["users"].values():
        if u.get("email") == email:
            return JSONResponse({"error": "Email already registered"})
    
    uid = hashlib.sha256(email.encode()).hexdigest()[:16]
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
    
    if is_first:
        save_cfg_safe({"admins": [email]})
    
    token = make_token(uid)
    return JSONResponse({"success": True, "token": token, "user": {"id": uid, "name": name, "email": email, "tier": db["users"][uid]["tier"], "is_admin": is_first}})

@app.post("/api/auth/login")
async def login(req: Request):
    data = await req.json()
    email = str(data.get("email", "")).strip().lower()
    pw = str(data.get("password", "")).strip()
    
    if not email or not pw:
        return JSONResponse({"error": "Email and password required"})
    
    db = load_db()
    for uid, u in db["users"].items():
        if u.get("email") == email:
            if not u.get("active", True):
                return JSONResponse({"error": "Account suspended"})
            if u.get("password") != hash_pw(pw):
                return JSONResponse({"error": "Incorrect password"})
            token = make_token(uid)
            return JSONResponse({"success": True, "token": token, "user": {"id": uid, "name": u["name"], "email": email, "tier": u.get("tier", "free"), "is_admin": u.get("is_admin", False)}})
    
    return JSONResponse({"error": "No account found"})

@app.get("/api/auth/me")
async def me(req: Request):
    u = get_user(req)
    if not u:
        return JSONResponse({"logged_in": False})
    tier_info = TIERS[u.get("tier", "free")]
    return JSONResponse({"logged_in": True, "user": u, "tier_info": tier_info})

@app.post("/api/auth/logout")
async def logout():
    return JSONResponse({"success": True})

@app.get("/api/status")
async def status(req: Request):
    ip = local_ip()
    return JSONResponse({"running": True, "version": "4.0", "time": datetime.now().isoformat(), "local_ip": ip})

# FIXED: Proper route decorators without semicolons
@app.get("/api/news")
async def r_news():
    return JSONResponse({"data": "Ready"})

@app.get("/api/prices")
async def r_prices():
    return JSONResponse({"data": "Ready"})

@app.get("/api/polymarket")
async def r_poly():
    return JSONResponse({"data": "Ready"})

@app.get("/api/x")
async def r_x():
    return JSONResponse({"data": "Ready"})

if __name__ == "__main__":
    ip = local_ip()
    port = int(os.environ.get("PORT", 8000))
    print(f"DARKSTARE AI v4.0 starting on http://{ip}:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
