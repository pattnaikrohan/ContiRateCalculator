#test11
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import math
import requests
import jwt
from datetime import datetime, timedelta
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Configurations
SECRET_KEY = "conti-rate-calculator-secret-key-12345"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480 # 8 hours

# Power Automate Flow URLs (Dataverse Proxies)
FLOW_SIGNUP = "https://default9a3bb30112fd4106a7f7563f72cfdf.69.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/85d7f9c94a864cb793c1e9a3eef7b508/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=9OwdeE78IFsCXJ6aK-gNv-nYg8Tqb0gUxfKWc0w3H_Q"
FLOW_LOGIN = "https://default9a3bb30112fd4106a7f7563f72cfdf.69.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/6eeada90d2be4980a5254f8b84df358e/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=QcT-rQudcSFwt4oUD76mNshh9-VRtlYvSMMwIq-748I"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication Models
class UserRegister(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# Helper Functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(authorization: str = Header(...)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    parts = authorization.split(" ")
    if len(parts) != 2:
        raise HTTPException(status_code=401, detail="Malformed token")
        
    token = parts[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return email
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# Auth Endpoints
@app.post("/api/auth/register")
def register(user: UserRegister):
    # FIRST: Check if user already exists using the Login/Lookup flow
    try:
        check_payload = {"email": user.email}
        print(f"DEBUG: Checking existence for {user.email}")
        check_res = requests.post(FLOW_LOGIN, json=check_payload, timeout=10)
        
        # If Login flow finds the user (200 OK), then they are already registered
        if check_res.status_code == 200:
            data = check_res.json()
            user_found = False
            if "value" in data and isinstance(data["value"], list) and len(data["value"]) > 0:
                user_found = True
            elif "email" in data and data["email"] == user.email:
                user_found = True
            
            if user_found:
                print("DEBUG: User already exists")
                raise HTTPException(status_code=400, detail="Email already registered")

        # SECOND: If not found (often 401 or 200 with empty list), proceed to register
        payload = {
            "email": user.email,
            "password": user.password
        }
        print(f"DEBUG: Calling Signup Flow for {user.email}")
        response = requests.post(FLOW_SIGNUP, json=payload, timeout=10)
        print(f"DEBUG: Signup Flow Response: {response.status_code}")
        
        if response.status_code not in [200, 201, 202]:
            raise HTTPException(status_code=400, detail="Registration failed at Dataverse")
            
        return {"message": "User registered successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"DEBUG Error in register: {str(e)}")
        raise HTTPException(status_code=500, detail=f"External Service Error: {str(e)}")

@app.post("/api/auth/login")
def login(user: UserLogin):
    # Call Power Automate Login Flow with BOTH email and password
    # This allows the Flow to filter/check both at once
    try:
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
        token = create_access_token(data={"sub": user.email})
        return {"access_token": token, "token_type": "bearer", "email": user.email}
        
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

def find_row(w: float) -> dict:
    # Explicitly cast to ensure type safety for linter
    for r in TARIFF:
        weight_val = r.get('w')
        if isinstance(weight_val, (int, float)) and float(weight_val) >= w:
            return r
    return TARIFF[-1]

class CalcRequest(BaseModel):
    origin: str
    dest: str
    weight: str
    reels: int = 1
    dimL: str = ""
    dimW: str = ""
    dimH: str = ""
    gst: bool = False

@app.post("/api/calculate")
def calculate_rate(req: CalcRequest, email: str = Depends(get_current_user)):
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

        # Crane Mel
        if weight_raw > 30:
            crane_mel = 1975.0 * num_reels
            lines.append({"label": "Melbourne crane lift (avg. assumption, >30T)", "value": float(crane_mel)})
            total += crane_mel

        # Sea Freight
        combined_rate = float(row.get('combined', 0))
        seafrt_calc = float(frt_basis) * combined_rate * num_reels
        lines.append({"label": f"Sea freight — {basis_label} × ${combined_rate}/FRT", "value": float(seafrt_calc)})
        total += seafrt_calc

        # Perth / Fremantle Logic
        if is_perth_dest:
            frem_crane_rate = 500.0 if weight_raw < 38 else 700.0
            frem_crane = frem_crane_rate * num_reels
            lines.append({"label": f"Fremantle crane ({'<38T @ $500' if weight_raw < 38 else '≥38T @ $700'} per reel)", "value": float(frem_crane)})
            total += frem_crane

        if is_metro or is_mine:
            mkey = PERTH_METRO.get(req.dest) if is_metro else MINE_KEYS.get(req.dest)
            mine_rates_dict = row_w.get('mineRates', {})
            
            # Ensure mkey is a valid string for dict lookup
            mine_rate = float(mine_rates_dict.get(str(mkey), 0)) if mkey else 0.0
            
            base_transport = mine_rate * num_reels
            fuel_amt = base_transport * FUEL_SURCHARGE
            dest_label = "Perth metro transport (base rate)" if is_metro else "Mine site transport (base rate)"

            lines.append({"label": dest_label, "value": float(base_transport)})
            total += base_transport

            lines.append({"label": "Fuel surcharge (38% of transport)", "value": float(fuel_amt)})
            total += fuel_amt

            wp_cost = 400.0 * num_reels
            lines.append({"label": "Western Power permit ($400 per reel)", "value": float(wp_cost)})
            total += wp_cost

            port_fee = 50.0 * num_reels
            lines.append({"label": "Port booking fee ($50 per reel)", "value": float(port_fee)})
            total += port_fee

        if req.gst:
            gst_amt = total * 0.10
            lines.append({"label": "GST (10%)", "value": float(gst_amt)})
            total += gst_amt

        return {
            "success": True,
            "lines": lines,
            "total": total,
            "reels": num_reels,
            "weightRaw": weight_raw,
            "basisLabel": basis_label,
            "demurr": float(row_w.get('demurr', 0))
        }

    except Exception as e:
        print(f"Calculation Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error during calculation")
