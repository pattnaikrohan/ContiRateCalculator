#test112
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import math
import requests
import jwt
import re, os, json
from datetime import datetime, timedelta
from typing import Optional, List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure CORS headers are present even on unhandled 500 errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"},
    )

# Security Configurations
SECRET_KEY = "conti-rate-calculator-secret-key-12345"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480 # 8 hours

# Power Automate Flow URLs 
FLOW_SIGNUP = "https://default9a3bb30112fd4106a7f7563f72cfdf.69.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/85d7f9c94a864cb793c1e9a3eef7b508/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=9OwdeE78IFsCXJ6aK-gNv-nYg8Tqb0gUxfKWc0w3H_Q"
FLOW_LOGIN = "https://default9a3bb30112fd4106a7f7563f72cfdf.69.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/6eeada90d2be4980a5254f8b84df358e/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=QcT-rQudcSFwt4oUD76mNshh9-VRtlYvSMMwIq-748I"
FLOW_REQUEST_ACCESS = FLOW_SIGNUP
FLOW_TARIFF_NOTIFY = os.environ.get("FLOW_TARIFF_NOTIFY", "")

ADMIN_EMAILS = os.environ.get("ADMIN_EMAILS", "").split(",")

# Paths
TARIFF_FILE     = os.path.join(os.path.dirname(__file__), "../server/data/tariffData.js")
OVERRIDES_FILE  = os.path.join(os.path.dirname(__file__), "tariff_overrides.json")

# Hardcoded defaults — used when tariffData.js cannot be found (e.g. on Azure)
DEFAULT_TARIFF_CONFIG = {
    "DEST_FUEL_SURCHARGE":   0.43,
    "ORIGIN_FUEL_SURCHARGE": 0.18,
    "CRANE_MEL_PER_REEL":    1975.0,
    "FREM_CRANE_LIGHT":      500.0,
    "FREM_CRANE_HEAVY":      700.0,
    "PORT_FEE_PER_REEL":     50.0,
    "WP_PERMIT_PER_REEL":    400.0,
    "GST_RATE":              0.10,
}

DEFAULT_TARIFF_TABLE = [
  {"w":3.0,  "melCart":1050,"combined":148.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":5.0,  "melCart":1050,"combined":148.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":7.0,  "melCart":1050,"combined":148.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":10.0, "melCart":1050,"combined":148.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":15.0, "melCart":1150,"combined":148.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":17.0, "melCart":1150,"combined":148.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":18.0, "melCart":1150,"combined":148.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":20.0, "melCart":1150,"combined":131.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":22.0, "melCart":1150,"combined":131.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":24.0, "melCart":1300,"combined":131.86,"demurr":280,"mineRates":{"hz":1400,"bs":1960,"bd":2520,"mw":10270,"ji":10570,"sf":10120,"cc":11420,"tp":11920,"wa":10570,"ya":10120,"cl":11420,"el":12720,"ac":10120,"ap":12870,"so":11600}},
  {"w":26.0, "melCart":1300,"combined":131.86,"demurr":280,"mineRates":{"hz":1400,"bs":1960,"bd":2520,"mw":10270,"ji":10570,"sf":10120,"cc":11420,"tp":11920,"wa":10570,"ya":10120,"cl":11420,"el":12720,"ac":10120,"ap":12870,"so":11600}},
  {"w":28.0, "melCart":1300,"combined":131.86,"demurr":280,"mineRates":{"hz":1400,"bs":1960,"bd":2520,"mw":10270,"ji":10570,"sf":10120,"cc":11420,"tp":11920,"wa":10570,"ya":10120,"cl":11420,"el":12720,"ac":10120,"ap":12870,"so":11600}},
  {"w":30.0, "melCart":1300,"combined":131.86,"demurr":280,"mineRates":{"hz":1400,"bs":1960,"bd":2520,"mw":10270,"ji":10570,"sf":10120,"cc":11420,"tp":11920,"wa":10570,"ya":10120,"cl":11420,"el":12720,"ac":10120,"ap":12870,"so":11600}},
  {"w":32.0, "melCart":1300,"combined":131.86,"demurr":320,"mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":34.0, "melCart":1500,"combined":131.86,"demurr":320,"mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":36.0, "melCart":1500,"combined":131.86,"demurr":320,"mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":38.0, "melCart":1500,"combined":131.86,"demurr":320,"mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":41.0, "melCart":1500,"combined":131.86,"demurr":320,"mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":44.0, "melCart":1500,"combined":131.86,"demurr":320,"mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":46.0, "melCart":1950,"combined":131.86,"demurr":320,"mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":48.0, "melCart":1950,"combined":131.86,"demurr":350,"mineRates":{"hz":1750,"bs":2450,"bd":3150,"mw":12800,"ji":12100,"sf":12800,"cc":12900,"tp":13600,"wa":12800,"ya":13000,"cl":13100,"el":14500,"ac":12800,"ap":15700,"so":14200}},
  {"w":50.0, "melCart":1950,"combined":131.86,"demurr":350,"mineRates":{"hz":1750,"bs":2450,"bd":3150,"mw":12800,"ji":12100,"sf":12800,"cc":12900,"tp":13600,"wa":12800,"ya":13000,"cl":13100,"el":14500,"ac":12800,"ap":15700,"so":16200}},
  {"w":52.0, "melCart":1950,"combined":131.86,"demurr":400,"mineRates":{"hz":2000,"bs":2800,"bd":3600,"mw":14500,"ji":14500,"sf":15000,"cc":16200,"tp":16000,"wa":14500,"ya":14500,"cl":15750,"el":16000,"ac":15000,"ap":16500,"so":18500}},
  {"w":57.0, "melCart":2300,"combined":131.86,"demurr":450,"mineRates":{"hz":2000,"bs":2800,"bd":3600,"mw":16000,"ji":16000,"sf":16500,"cc":17250,"tp":17500,"wa":16000,"ya":17500,"cl":17500,"el":20000,"ac":17000,"ap":20500,"so":18500}},
  {"w":59.0, "melCart":2300,"combined":131.86,"demurr":450,"mineRates":{"hz":2000,"bs":2800,"bd":3600,"mw":16000,"ji":16000,"sf":16500,"cc":17250,"tp":17500,"wa":16000,"ya":17500,"cl":17500,"el":20000,"ac":17000,"ap":20500,"so":18500}},
]

# Runtime state — starts from defaults
_tariff_config = dict(DEFAULT_TARIFF_CONFIG)
_tariff_table  = list(DEFAULT_TARIFF_TABLE)

def save_overrides():
    """Write current state to tariff_overrides.json for persistence across restarts."""
    try:
        with open(OVERRIDES_FILE, "w") as f:
            json.dump({"constants": _tariff_config, "tariff_table": _tariff_table}, f, indent=2)
    except Exception as e:
        print(f"Could not write overrides file: {e}")

def load_tariff_config():
    global _tariff_config, _tariff_table
    # 1. Try loading from tariffData.js (local dev)
    try:
        with open(TARIFF_FILE, "r") as f:
            content = f.read()
        config = {}
        for match in re.finditer(r"export const (\w+)\s*=\s*([\d.]+);", content):
            config[match.group(1)] = float(match.group(2))
        if config:
            _tariff_config = config
        arr_match = re.search(r"export const TARIFF\s*=\s*(\[.*?\]);", content, re.DOTALL)
        if arr_match:
            js_arr = arr_match.group(1)
            js_arr = re.sub(r'(\w+):', r'"\1":', js_arr)
            js_arr = re.sub(r',\s*}', '}', js_arr)
            js_arr = re.sub(r',\s*]', ']', js_arr)
            parsed = json.loads(js_arr)
            if parsed:
                _tariff_table = parsed
    except Exception:
        pass  # Use defaults on Azure where the JS file isn't present

    # 2. Apply saved overrides on top (highest priority — persists admin changes)
    try:
        with open(OVERRIDES_FILE, "r") as f:
            overrides = json.load(f)
        if overrides.get("constants"):
            _tariff_config = overrides["constants"]
        if overrides.get("tariff_table"):
            _tariff_table = overrides["tariff_table"]
        print("Loaded tariff overrides from tariff_overrides.json")
    except FileNotFoundError:
        pass  # No overrides yet — use defaults/JS file
    except Exception as e:
        print(f"Could not load overrides file: {e}")

load_tariff_config()

DEFAULT_TARIFF_CONFIG = {
    "DEST_FUEL_SURCHARGE":   0.43,
    "ORIGIN_FUEL_SURCHARGE": 0.18,
    "CRANE_MEL_PER_REEL":    1975.0,
    "FREM_CRANE_LIGHT":      500.0,
    "FREM_CRANE_HEAVY":      700.0,
    "PORT_FEE_PER_REEL":     50.0,
    "WP_PERMIT_PER_REEL":    400.0,
    "GST_RATE":              0.10,
}

DEFAULT_TARIFF_TABLE = [
  {"w":3.0,  "melCart":1050,"combined":148.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":5.0,  "melCart":1050,"combined":148.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":7.0,  "melCart":1050,"combined":148.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":10.0, "melCart":1050,"combined":148.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":15.0, "melCart":1150,"combined":148.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":17.0, "melCart":1150,"combined":148.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":18.0, "melCart":1150,"combined":148.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":20.0, "melCart":1150,"combined":131.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":22.0, "melCart":1150,"combined":131.86,"demurr":195,"mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":24.0, "melCart":1300,"combined":131.86,"demurr":280,"mineRates":{"hz":1400,"bs":1960,"bd":2520,"mw":10270,"ji":10570,"sf":10120,"cc":11420,"tp":11920,"wa":10570,"ya":10120,"cl":11420,"el":12720,"ac":10120,"ap":12870,"so":11600}},
  {"w":26.0, "melCart":1300,"combined":131.86,"demurr":280,"mineRates":{"hz":1400,"bs":1960,"bd":2520,"mw":10270,"ji":10570,"sf":10120,"cc":11420,"tp":11920,"wa":10570,"ya":10120,"cl":11420,"el":12720,"ac":10120,"ap":12870,"so":11600}},
  {"w":28.0, "melCart":1300,"combined":131.86,"demurr":280,"mineRates":{"hz":1400,"bs":1960,"bd":2520,"mw":10270,"ji":10570,"sf":10120,"cc":11420,"tp":11920,"wa":10570,"ya":10120,"cl":11420,"el":12720,"ac":10120,"ap":12870,"so":11600}},
  {"w":30.0, "melCart":1300,"combined":131.86,"demurr":280,"mineRates":{"hz":1400,"bs":1960,"bd":2520,"mw":10270,"ji":10570,"sf":10120,"cc":11420,"tp":11920,"wa":10570,"ya":10120,"cl":11420,"el":12720,"ac":10120,"ap":12870,"so":11600}},
  {"w":32.0, "melCart":1300,"combined":131.86,"demurr":320,"mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":34.0, "melCart":1500,"combined":131.86,"demurr":320,"mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":36.0, "melCart":1500,"combined":131.86,"demurr":320,"mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":38.0, "melCart":1500,"combined":131.86,"demurr":320,"mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":41.0, "melCart":1500,"combined":131.86,"demurr":320,"mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":44.0, "melCart":1500,"combined":131.86,"demurr":320,"mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":46.0, "melCart":1950,"combined":131.86,"demurr":320,"mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":48.0, "melCart":1950,"combined":131.86,"demurr":350,"mineRates":{"hz":1750,"bs":2450,"bd":3150,"mw":12800,"ji":12100,"sf":12800,"cc":12900,"tp":13600,"wa":12800,"ya":13000,"cl":13100,"el":14500,"ac":12800,"ap":15700,"so":14200}},
  {"w":50.0, "melCart":1950,"combined":131.86,"demurr":350,"mineRates":{"hz":1750,"bs":2450,"bd":3150,"mw":12800,"ji":12100,"sf":12800,"cc":12900,"tp":13600,"wa":12800,"ya":13000,"cl":13100,"el":14500,"ac":12800,"ap":15700,"so":16200}},
  {"w":52.0, "melCart":1950,"combined":131.86,"demurr":400,"mineRates":{"hz":2000,"bs":2800,"bd":3600,"mw":14500,"ji":14500,"sf":15000,"cc":16200,"tp":16000,"wa":14500,"ya":14500,"cl":15750,"el":16000,"ac":15000,"ap":16500,"so":18500}},
  {"w":57.0, "melCart":2300,"combined":131.86,"demurr":450,"mineRates":{"hz":2000,"bs":2800,"bd":3600,"mw":16000,"ji":16000,"sf":16500,"cc":17250,"tp":17500,"wa":16000,"ya":17500,"cl":17500,"el":20000,"ac":17000,"ap":20500,"so":18500}},
  {"w":59.0, "melCart":2300,"combined":131.86,"demurr":450,"mineRates":{"hz":2000,"bs":2800,"bd":3600,"mw":16000,"ji":16000,"sf":16500,"cc":17250,"tp":17500,"wa":16000,"ya":17500,"cl":17500,"el":20000,"ac":17000,"ap":20500,"so":18500}},
]

def cfg(key, fallback):
    return _tariff_config.get(key, fallback)

# Authentication Models
# Authentication Models
class UserLogin(BaseModel):
    email: str
    password: str

class AccessRequest(BaseModel):
    name: str
    email: str
    company: Optional[str] = ""
    message: Optional[str] = ""

# Helper Functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(authorization: str = Header(None)):
    if not authorization:
        return None  # allow unauthenticated requests if needed

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # return full payload so callers can check claims
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
# Auth Endpoints
@app.post("/api/auth/login")
def login(user: UserLogin):
    # Call Power Automate Login Flow with BOTH email and password
    # This allows the Flow to filter/check both at once
    try:
        # Hardcoded Admin Login for Demonstration/Admin Panel access
        if user.email == "admin@conti.com" and user.password == "admin123":
            token = create_access_token(data={"sub": user.email, "is_admin": True})
            return {"access_token": token, "token_type": "bearer", "email": user.email, "is_admin": True}

        payload = {
            "email": user.email,
            "password": user.password
        }
        print(f"DEBUG: Calling Login Flow for {user.email}")
        response = requests.post(FLOW_LOGIN, json=payload, timeout=10)
        print(f"DEBUG: Login Flow Response: {response.status_code}")
        
        if response.status_code not in [200, 201, 202]:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        
        # If the Flow returns 200/201/202, we trust it has validated the email/password
        is_admin = user.email in ADMIN_EMAILS
        token = create_access_token(data={"sub": user.email, "is_admin": is_admin})
        return {"access_token": token, "token_type": "bearer", "email": user.email, "is_admin": is_admin}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"External Service Error: {str(e)}")


TARIFF = [
  {"w":3.0,  "melCart":1050, "combined":148.86, "demurr":195, "mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":5.0,  "melCart":1050, "combined":148.86, "demurr":195, "mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":7.0,  "melCart":1050, "combined":148.86, "demurr":195, "mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":10.0, "melCart":1050, "combined":148.86, "demurr":195, "mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":15.0, "melCart":1150, "combined":148.86, "demurr":195, "mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":17.0, "melCart":1150, "combined":148.86, "demurr":195, "mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":18.0, "melCart":1150, "combined":148.86, "demurr":195, "mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":20.0, "melCart":1150, "combined":131.86, "demurr":195, "mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":22.0, "melCart":1150, "combined":131.86, "demurr":195, "mineRates":{"hz":975,"bs":1365,"bd":1755,"mw":9930,"ji":10230,"sf":9780,"cc":11080,"tp":11580,"wa":10230,"ya":9780,"cl":11080,"el":12380,"ac":9780,"ap":12280,"so":10785}},
  {"w":24.0, "melCart":1300, "combined":131.86, "demurr":280, "mineRates":{"hz":1400,"bs":1960,"bd":2520,"mw":10270,"ji":10570,"sf":10120,"cc":11420,"tp":11920,"wa":10570,"ya":10120,"cl":11420,"el":12720,"ac":10120,"ap":12870,"so":11600}},
  {"w":26.0, "melCart":1300, "combined":131.86, "demurr":280, "mineRates":{"hz":1400,"bs":1960,"bd":2520,"mw":10270,"ji":10570,"sf":10120,"cc":11420,"tp":11920,"wa":10570,"ya":10120,"cl":11420,"el":12720,"ac":10120,"ap":12870,"so":11600}},
  {"w":28.0, "melCart":1300, "combined":131.86, "demurr":280, "mineRates":{"hz":1400,"bs":1960,"bd":2520,"mw":10270,"ji":10570,"sf":10120,"cc":11420,"tp":11920,"wa":10570,"ya":10120,"cl":11420,"el":12720,"ac":10120,"ap":12870,"so":11600}},
  {"w":30.0, "melCart":1300, "combined":131.86, "demurr":280, "mineRates":{"hz":1400,"bs":1960,"bd":2520,"mw":10270,"ji":10570,"sf":10120,"cc":11420,"tp":11920,"wa":10570,"ya":10120,"cl":11420,"el":12720,"ac":10120,"ap":12870,"so":11600}},
  {"w":32.0, "melCart":1300, "combined":131.86, "demurr":320, "mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":34.0, "melCart":1500, "combined":131.86, "demurr":320, "mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":36.0, "melCart":1500, "combined":131.86, "demurr":320, "mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":38.0, "melCart":1500, "combined":131.86, "demurr":320, "mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":41.0, "melCart":1500, "combined":131.86, "demurr":320, "mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":44.0, "melCart":1500, "combined":131.86, "demurr":320, "mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":46.0, "melCart":1950, "combined":131.86, "demurr":320, "mineRates":{"hz":1600,"bs":2240,"bd":2880,"mw":12680,"ji":11980,"sf":12680,"cc":12780,"tp":13480,"wa":12680,"ya":12880,"cl":12980,"el":14380,"ac":12680,"ap":14580,"so":14200}},
  {"w":48.0, "melCart":1950, "combined":131.86, "demurr":350, "mineRates":{"hz":1750,"bs":2450,"bd":3150,"mw":12800,"ji":12100,"sf":12800,"cc":12900,"tp":13600,"wa":12800,"ya":13000,"cl":13100,"el":14500,"ac":12800,"ap":15700,"so":14200}},
  {"w":50.0, "melCart":1950, "combined":131.86, "demurr":350, "mineRates":{"hz":1750,"bs":2450,"bd":3150,"mw":12800,"ji":12100,"sf":12800,"cc":12900,"tp":13600,"wa":12800,"ya":13000,"cl":13100,"el":14500,"ac":12800,"ap":15700,"so":16200}},
  {"w":52.0, "melCart":1950, "combined":131.86, "demurr":400, "mineRates":{"hz":2000,"bs":2800,"bd":3600,"mw":14500,"ji":14500,"sf":15000,"cc":16200,"tp":16000,"wa":14500,"ya":14500,"cl":15750,"el":16000,"ac":15000,"ap":16500,"so":18500}},
  {"w":57.0, "melCart":2300, "combined":131.86, "demurr":450, "mineRates":{"hz":2000,"bs":2800,"bd":3600,"mw":16000,"ji":16000,"sf":16500,"cc":17250,"tp":17500,"wa":16000,"ya":17500,"cl":17500,"el":20000,"ac":17000,"ap":20500,"so":18500}},
  {"w":59.0, "melCart":2300, "combined":131.86, "demurr":450, "mineRates":{"hz":2000,"bs":2800,"bd":3600,"mw":16000,"ji":16000,"sf":16500,"cc":17250,"tp":17500,"wa":16000,"ya":17500,"cl":17500,"el":20000,"ac":17000,"ap":20500,"so":18500}}
]

MINE_KEYS = {'mtwhaleback':'mw','jimblebar':'ji','southflank':'sf','christmascreek':'cc','tomprice':'tp','westangeles':'wa','yandi':'ya','cloudbreak':'cl','eliwana':'el','areac':'ac','andersonpoint':'ap','solomon':'so'}
PERTH_METRO = {'hazelmere':'hz','bullsbrook':'bs','boddington':'bd'}
FUEL_SURCHARGE = 0.38

@app.get("/api/tariff")
def get_tariff():
    return {
        "tariff": _tariff_table,
        "mine_keys": MINE_KEYS,
        "perth_metro": PERTH_METRO,
        "constants": _tariff_config
    }

def find_row(w: float) -> dict:
    for r in _tariff_table:
        weight_val = r.get('w')
        if isinstance(weight_val, (int, float)) and float(weight_val) >= w:
            return r
    return _tariff_table[-1] if _tariff_table else {}
@app.post("/api/auth/request-access")
def request_access(req: AccessRequest):
    try:
        # Send to Power Automate
        payload = {
            "name": req.name,
            "email": req.email,
            "company": req.company,
            "message": req.message,
            "timestamp": datetime.utcnow().isoformat()
        }
        print(f"DEBUG: Calling Request Access Flow for {req.email}")
        # In a real scenario, this would call FLOW_REQUEST_ACCESS
        # For now, we'll log it and return success if the URL is a placeholder
        if "placeholder" in FLOW_REQUEST_ACCESS:
             print("DEBUG: Using placeholder flow - request logged successfully")
             return {"message": "Request sent successfully (Logged)"}
             
        response = requests.post(FLOW_REQUEST_ACCESS, json=payload, timeout=10)
        if response.status_code not in [200, 201, 202]:
            raise HTTPException(status_code=400, detail="Failed to send request")
            
        return {"message": "Request sent successfully"}
    except Exception as e:
        print(f"DEBUG Error in request_access: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")


class CalcRequest(BaseModel):
    origin: str
    dest: str
    weight: str
    reels: int = 1
    dimL: str = ""
    dimW: str = ""
    dimH: str = ""

@app.post("/api/calculate")
def calculate_rate(req: CalcRequest, user_payload = Depends(get_current_user)):
    email = user_payload.get("sub") if isinstance(user_payload, dict) else user_payload
    try:
        weight_raw = float(req.weight)
        num_reels = int(max(1, req.reels))
        L = float(req.dimL) if req.dimL else 0.0
        W = float(req.dimW) if req.dimW else 0.0
        H = float(req.dimH) if req.dimH else 0.0

        if not req.dest or weight_raw <= 0:
            raise HTTPException(status_code=400, detail="Invalid weight or destination")

        cbm_per_reel = 0.0
        frt_basis = weight_raw
        basis_label = f"{weight_raw}T (weight)"

        if L > 0 and W > 0 and H > 0:
            cbm_per_reel = (L / 100) * (W / 100) * (H / 100)
            if cbm_per_reel > weight_raw:
                frt_basis = cbm_per_reel
                basis_label = f"{cbm_per_reel:.3f} CBM (greater than {weight_raw}T)"
            else:
                basis_label = f"{weight_raw}T (greater than {cbm_per_reel:.3f} CBM)"

        # Configuration values from file
        dest_fuel     = cfg("DEST_FUEL_SURCHARGE",   0.43)
        origin_fuel   = cfg("ORIGIN_FUEL_SURCHARGE", 0.18)
        gst_rate      = cfg("GST_RATE",              0.10)
        wp_permit_fee = cfg("WP_PERMIT_PER_REEL",    400)
        port_fee_rate = cfg("PORT_FEE_PER_REEL",      50)
        crane_mel_rate = cfg("CRANE_MEL_PER_REEL",   1975)
        frem_light    = cfg("FREM_CRANE_LIGHT",      500)
        frem_heavy    = cfg("FREM_CRANE_HEAVY",      700)

        # Find appropriate rows in TARIFF
        row = find_row(float(frt_basis))
        row_w = find_row(float(weight_raw))
        
        is_mine = req.dest in MINE_KEYS
        is_metro = req.dest in PERTH_METRO
        is_perth_dest = is_mine or is_metro or req.dest == 'seafreight'

        lines = []
        total = 0.0

        # Melbourne Cartage
        mel_cart = float(row_w.get('melCart', 0)) * num_reels
        lines.append({"label": "Melbourne cartage", "value": float(mel_cart)})
        total += mel_cart

        # Fuel Surcharges split
        # Origin fuel — on Melbourne cartage
        origin_fuel_amt = mel_cart * origin_fuel
        lines.append({
            "label": f"Origin fuel surcharge ({origin_fuel*100:.0f}% of Mel cartage)",
            "value": float(origin_fuel_amt)
        })
        total += origin_fuel_amt

        # Crane Mel
        if weight_raw > 30:
            crane_mel = crane_mel_rate * num_reels
            lines.append({"label": f"Melbourne crane lift (avg. assumption, >30T)", "value": float(crane_mel)})
            total += crane_mel

        # Sea Freight
        combined_rate = float(row.get('combined', 0))
        seafrt_calc = float(frt_basis) * combined_rate * num_reels
        lines.append({"label": f"Sea freight — {basis_label} × ${combined_rate}/FRT", "value": float(seafrt_calc)})
        total += seafrt_calc

        # Perth / Fremantle Logic
        if is_perth_dest:
            frem_crane_rate = frem_light if weight_raw < 38 else frem_heavy
            frem_crane = frem_crane_rate * num_reels
            lines.append({"label": f"Fremantle crane ({'<38T @ $' + str(int(frem_light)) if weight_raw < 38 else '≥38T @ $' + str(int(frem_heavy))} per reel)", "value": float(frem_crane)})
            total += frem_crane

        if is_metro or is_mine:
            mkey = PERTH_METRO.get(req.dest) if is_metro else MINE_KEYS.get(req.dest)
            mine_rates_dict = row_w.get('mineRates', {})
            mine_rate = float(mine_rates_dict.get(str(mkey), 0)) if mkey else 0.0
            
            base_transport = mine_rate * num_reels
            lines.append({"label": "Transport base rate", "value": float(base_transport)})
            total += base_transport

            # Destination fuel — on transport rate
            dest_fuel_amt = base_transport * dest_fuel
            lines.append({
                "label": f"Destination fuel surcharge ({dest_fuel*100:.0f}% of transport)",
                "value": float(dest_fuel_amt)
            })
            total += dest_fuel_amt

            if H > 360:
                wp_cost = wp_permit_fee * num_reels
                lines.append({"label": f"Western Power permit (${int(wp_permit_fee)} per reel)", "value": float(wp_cost)})
                total += wp_cost

            if 34 <= weight_raw <= 52:
                pilot_cost = 400.0 * num_reels # Static 400 for pilot
                lines.append({"label": "Pilot vehicles ($400 per reel)", "value": float(pilot_cost)})
                total += pilot_cost

            port_fee = port_fee_rate * num_reels
            lines.append({"label": f"Port booking fee (${int(port_fee_rate)} per reel)", "value": float(port_fee)})
            total += port_fee

        return {
            "success": True,
            "lines": lines,
            "total": total,
            "reels": num_reels,
            "weightRaw": weight_raw,
            "basisLabel": basis_label,
            "demurr": float(row_w.get('demurr', 0)),
            "wp_applies": H > 360 if is_metro or is_mine else False,
            "pilot_applies": (34 <= weight_raw <= 52) if is_metro or is_mine else False,
            "crane_applies": weight_raw > 30
        }

    except Exception as e:
        print(f"Calculation Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error during calculation")

# Admin Logic & Endpoints

def get_current_admin(payload = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=401, detail="Not authenticated")
    email = payload.get("sub") if isinstance(payload, dict) else payload
    is_admin = payload.get("is_admin", False) if isinstance(payload, dict) else False
    if not is_admin and email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    return email

def notify_pa(updated_by, changes=None, previous=None, diffs=None, is_table=False):
    if not FLOW_TARIFF_NOTIFY:
        return
        
    payload = {
        "updated_by": updated_by,
        "updated_at": datetime.utcnow().isoformat(),
        "type": "tariff_table" if is_table else "surcharges",
        "changes": diffs if is_table else [
            {"field": k, "from": previous.get(k) if previous else None, "to": v}
            for k, v in changes.items()
        ]
    }
    try:
        requests.post(FLOW_TARIFF_NOTIFY, json=payload, timeout=10)
    except:
        pass  # don't fail the save if email fails

def rewrite_constants(changes: dict):
    global _tariff_config
    _tariff_config = {**_tariff_config, **changes}
    save_overrides()  # persist to JSON — survives restarts
    # Also try to update tariffData.js for local dev
    try:
        with open(TARIFF_FILE, "r") as f:
            content = f.read()
        for key, value in changes.items():
            content = re.sub(
                rf"(const {key}\s*=\s*)[\d.]+;",
                rf"\g<1>{value};",
                content
            )
        with open(TARIFF_FILE, "w") as f:
            f.write(content)
    except Exception:
        pass

def rewrite_tariff_array(new_rows: list):
    global _tariff_table
    _tariff_table = new_rows
    save_overrides()  # persist to JSON — survives restarts
    # Also try to update tariffData.js for local dev
    def fmt_row(r):
        mine = ",".join(f"{k}:{v}" for k, v in r["mineRates"].items())
        return (
            f"  {{w:{r['w']}, melCart:{r['melCart']}, "
            f"combined:{r['combined']}, demurr:{r['demurr']}, "
            f"mineRates:{{{mine}}}}}"
        )
    try:
        new_array = "export const TARIFF = [\n"
        new_array += ",\n".join(fmt_row(r) for r in new_rows)
        new_array += "\n];"
        with open(TARIFF_FILE, "r") as f:
            content = f.read()
        content = re.sub(
            r"export const TARIFF\s*=\s*\[.*?\];",
            new_array, content, flags=re.DOTALL
        )
        with open(TARIFF_FILE, "w") as f:
            f.write(content)
    except Exception:
        pass

@app.get("/api/admin/tariff-config")
def get_tariff_config(email: str = Depends(get_current_admin)):
    return {
        "constants": _tariff_config,
        "tariff_table": _tariff_table
    }

class SurchargesSaveRequest(BaseModel):
    changes:  dict   # { "DEST_FUEL_SURCHARGE": 0.43, ... }
    previous: dict   # { "DEST_FUEL_SURCHARGE": 0.38, ... }

@app.post("/api/admin/save-surcharges")
def save_surcharges(payload: SurchargesSaveRequest, email: str = Depends(get_current_admin)):
    rewrite_constants(payload.changes)
    notify_pa(email, payload.changes, payload.previous)
    return {"success": True}

class TariffTableSaveRequest(BaseModel):
    rows:     list   # full updated TARIFF array
    previous: list   # full previous TARIFF array

@app.post("/api/admin/save-tariff-table")
def save_tariff_table(payload: TariffTableSaveRequest, email: str = Depends(get_current_admin)):
    rewrite_tariff_array(payload.rows)
    # Build diff — only rows/fields that actually changed
    diffs = []
    for i, (old, new) in enumerate(zip(payload.previous, payload.rows)):
        for field in ["melCart","combined","demurr"]:
            if old[field] != new[field]:
                diffs.append({"row": f"{new['w']}T", "field": field, "from": old[field], "to": new[field]})
        for k in old["mineRates"]:
            if old["mineRates"][k] != new["mineRates"][k]:
                diffs.append({"row": f"{new['w']}T", "field": k, "from": old["mineRates"][k], "to": new["mineRates"][k]})
    notify_pa(email, diffs=diffs, is_table=True)
    return {"success": True}
