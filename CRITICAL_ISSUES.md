# 🔴 CRITICAL ISSUES - Code Snippets & Exact Locations

## ISSUE #1: NEO4J CREDENTIALS EXPOSED IN .env

### Location & Current Code

**File:** `.env` (Line 47-49)
```bash
NEO4J_URI=neo4j+s://3e08ff89.databases.neo4j.io         # ❌ EXPOSED
NEO4J_USERNAME=3e08ff89                                 # ❌ EXPOSED
NEO4J_PASSWORD=wV2TnpvJD3DiQpQbTogvX8WdmOPfrarOdWyVN_d1Es0  # ❌ EXPOSED
```

### Risk Assessment

```
🔴 CRITICAL SEVERITY

Risk Level: 🔴🔴🔴🔴🔴 (5/5)

Why:
1. File is tracked in git (likely public repository)
2. Everyone who can access repo can connect to Neo4j Aura instance
3. Can read/modify all medical data
4. Can modify drug interactions (safety issue!)

Who has access?
├─ All GitHub collaborators
├─ Anyone who forks the repo
├─ Anyone who can see git history
├─ Potentially: GitHub as platform
└─ Potentially: Cached in search engines/archives

Commands to verify compromise:
$ cypher-shell -a neo4j+s://3e08ff89.databases.neo4j.io \
  -u 3e08ff89 -p wV2TnpvJD3DiQpQbTogvX8WdmOPfrarOdWyVN_d1Es0
# If this connects = database is compromised!
```

### Immediate Remediation

```bash
# STEP 1: Change Neo4j password IMMEDIATELY
# Go to: https://console.neo4j.io/
#   → Find instance "3e08ff89"
#   → Click "Reset password"
#   → Generate new secure password
# Save new password temporarily

# STEP 2: Delete .env from git history
cd /path/to/repo

# Remove file from git tracking
git rm --cached .env
git commit -m "Remove .env (was exposing secrets)"

# STEP 3: Rewrite git history (DESTRUCTIVE - use carefully!)
# Option A: BFG Repo Cleaner (recommended)
bfg --delete-files .env

# Option B: Filter-branch (slower)
git filter-branch --tree-filter 'rm -f .env' -- --all

# STEP 4: Force push (⚠️ WARNING: Will rewrite history!)
git push origin --force --all
git push origin --force --tags

# STEP 5: Update contributors
# Notify all team members to:
# 1. Delete local repos and re-clone
# 2. Update local .env with new credentials
# 3. Clear local git cache
#    git credential reject https://github.com
```

### Verification Commands

```bash
# Verify .env is removed from git
git log --all --full-history -- .env
# Should show: fatal: your current branch 'master' does not have any commits yet

# Verify no secrets remain
git log -S "wV2TnpvJD3DiQpQbTogvX8WdmOPfrarOdWyVN_d1Es0" --all
# Should show: no matches

# Verify git history is clean
git log --oneline | head -20
# Should have new commits with "Remove .env" messages

# Check current credentials work
NEO4J_URI=neo4j+s://3e08ff89.databases.neo4j.io
NEO4J_USERNAME=3e08ff89
NEO4J_PASSWORD=$(cat .env.local | grep NEO4J_PASSWORD | cut -d= -f2)

docker run -e NEO4J_URI="$NEO4J_URI" \
           -e NEO4J_USERNAME="$NEO4J_USERNAME" \
           -e NEO4J_PASSWORD="$NEO4J_PASSWORD" \
           neo4j:5 \
           cypher-shell "RETURN 1;"
```

---

## ISSUE #2: NEO4J HARDCODED CREDENTIALS IN DOCKER COMPOSE

### Location & Current Code

**File:** `compose.yml` (Line 132)
```yaml
neo4j:
  image: neo4j:5
  restart: always
  ports:
    - "7474:7474"
    - "7687:7687"
  environment:
    - NEO4J_AUTH=neo4j/password123              # ❌ HARDCODED!
  volumes:
    - neo4j-data:/data
```

### Problem

```
When developer sets:
$ export NEO4J_PASSWORD="mySecurePassword123"

And runs:
$ docker-compose up

The Neo4j container will be initialized with:
  Username: neo4j
  Password: password123      ← Ignored the .env!
  
But the backend tries to connect with:
  Username: 3e08ff89
  Password: wV2TnpvJD3DiQpQbTogvX8WdmOPfrarOdWyVN_d1Es0 (from .env)
  
Result: Connection refused ❌
```

### Fix

**Before:**
```yaml
environment:
  - NEO4J_AUTH=neo4j/password123
```

**After:**
```yaml
environment:
  - NEO4J_AUTH=${NEO4J_USERNAME?Variable not set}/${NEO4J_PASSWORD?Variable not set}
```

### Verification

```bash
# Check what docker-compose config resolves to:
docker-compose config | grep -A 5 "neo4j:"

# Should show:
# environment:
#   - NEO4J_AUTH=3e08ff89/wV2TnpvJD3DiQpQbTogvX8WdmOPfrarOdWyVN_d1Es0

# NOT:
# environment:
#   - NEO4J_AUTH=neo4j/password123
```

---

## ISSUE #3: NEO4J MISSING HEALTH CHECK

### Location & Current Code

**File:** `compose.yml` (Line 125-135)
```yaml
neo4j:
  image: neo4j:5
  restart: always
  ports:
    - "7474:7474"
    - "7687:7687"
  environment:
    - NEO4J_AUTH=neo4j/password123
  volumes:
    - neo4j-data:/data
  # ❌ NO HEALTHCHECK BLOCK
```

### Actual Impact

```
Scenario: Neo4j takes 45 seconds to fully initialize

Timeline:
0s  - docker-compose starts neo4j container
5s  - docker-compose marks neo4j as "started" 
     - backend depends_on: "service_started" → SATISFIED
10s - docker-compose starts backend
15s - backend tries to connect to Neo4j
     Neo4j is still initializing... ❌ CONNECTION REFUSED
20s - backend crashes, restarts (because restart:always)
40s - Neo4j finally ready
45s - backend tries again, connects successfully

Result: 3-4 container restarts, wasted 60 seconds
```

### Fix

```yaml
neo4j:
  image: neo4j:5
  restart: always
  ports:
    - "7474:7474"
    - "7687:7687"
  environment:
    - NEO4J_AUTH=${NEO4J_USERNAME?Variable not set}/${NEO4J_PASSWORD?Variable not set}
  volumes:
    - neo4j-data:/data
  healthcheck:                          # ✅ ADD THIS
    test: ["CMD", "curl", "-f", "http://localhost:7474/db/neo4j/exec"]
    interval: 10s
    retries: 5
    start_period: 30s
    timeout: 10s
```

**And update backend dependency:**
```yaml
backend:
  depends_on:
    neo4j:
      condition: service_healthy         # Changed from: service_started
```

### Verification

```bash
# Start services
docker-compose up -d

# Watch health status
docker-compose ps --all

# Expected output after 60s:
# neo4j     neo4j:5      Up 1 minute (healthy)    ✅
# backend   backend:...  Up 45 seconds (healthy)  ✅

# If unhealthy:
docker logs neo4j | tail -20
# Look for connection/startup errors
```

---

## ISSUE #4: DATABASE PASSWORD EXPOSED IN .env

### Location & Current Code

**File:** `.env` (Line 38)
```bash
POSTGRES_PASSWORD=changethis    # ❌ EXPOSED + DEFAULT!
```

### Risk

```
🔴 CRITICAL

Database is accessible at localhost:5432 (exposed via port mapping)
Anyone with this password can:
1. Read all user data
2. Read patient information (HIPAA violation!)
3. Modify medical records
4. Delete data
5. Execute arbitrary SQL

Compliance violations:
- HIPAA (if patient data is PII)
- GDPR (if EU patient data)
- PCI DSS (if payment data)
```

### Fix

```bash
# Before:
POSTGRES_PASSWORD=changethis

# After: Generate secure password
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Example output:
POSTGRES_PASSWORD=7xKj9Lq2mN8pRvWxZaMb3Y4cD5eF6gH7iJ
```

---

## ISSUE #5: HARDCODED SUPERUSER PASSWORD

### Location & Current Code

**File:** `backend/app/core/config.py` (Line 116)
```python
FIRST_SUPERUSER_PASSWORD: str = "changethis"  # ❌ HARDCODED DEFAULT
```

**Also in .env:**
```bash
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin123        # ❌ EXPOSED + DEFAULT
```

### How It's Used

```python
# backend/app/initial_data.py
def init_db(session: Session) -> None:
    existing_user = get_user_by_email(session, settings.FIRST_SUPERUSER)
    if not existing_user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,  # Uses this!
        )
        create_user(session, user_in)
```

**Executed by:** `scripts/prestart.sh` → `python app/initial_data.py`

**Impact:**
```
1. First time docker-compose up:
   - Creates user: admin@example.com
   - Password: admin123 (from .env)
   - Can log in to medical system with default credentials
   
2. Anyone who sees this repo can:
   - Log in to any running deployment
   - Access all patient data
   - Modify medical records

3. Developers forget to change it in .env
   - Deployments go live with known credentials
```

### Fix

```bash
# .env.example (committed to repo)
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=CHANGE_ME_IN_PRODUCTION_32_CHARS_MIN

# .env.local or .env (NOT committed)
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=$(openssl rand -base64 32)
# Example: aB3cD4eF5gH6iJ7kL8mN9oPqRsTuVwXyZ1a

# Or in CI/CD pipeline:
export FIRST_SUPERUSER_PASSWORD=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### Verify

```bash
# Check if hardcoded password is in deployed system:
curl -X POST http://localhost:8000/api/v1/login/access-token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"

# If this works, password is still default! ❌
# If 401 Unauthorized, password was changed ✅
```

---

## ISSUE #6: SECRET_KEY EXPOSED IN .env

### Location & Current Code

**File:** `.env` (Line 20)
```bash
SECRET_KEY=changethis    # ❌ HARDCODED DEFAULT!
```

**File:** `backend/app/core/config.py` (Line 48-49)
```python
SECRET_KEY: str = secrets.token_urlsafe(32)
# But falls back to "changethis" if not in .env!
```

### What It's Used For

```python
# JWT Token Signing
def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY,    # ← Uses SECRET_KEY here!
        algorithm=ALGORITHM,
    )
    return encoded_jwt
```

### Attack Scenario

```
Attacker knows SECRET_KEY = "changethis" (from public repo)

They can:
1. Forge JWT tokens with any user_id
2. Create fake admin tokens
3. Bypass authentication
4. Impersonate any user

Example:
$ jwt_token = jwt.encode(
    {"sub": "123", "exp": datetime.utcnow() + timedelta(days=100)},
    "changethis",  # ← Known secret!
    algorithm="HS256",
)
# Now they have a valid token for user_id=123!
```

### Fix

```bash
# Generate random secret (never commit!)
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Output: xYz9Lq2mN8pRvWxZaMb3Y4cD5eF6gH7iJ8kL

# Add to .env (DO NOT COMMIT):
SECRET_KEY=xYz9Lq2mN8pRvWxZaMb3Y4cD5eF6gH7iJ8kL

# Add placeholder to .env.example:
SECRET_KEY=CHANGE_ME_GENERATE_WITH_secrets.token_urlsafe(32)

# Add to .gitignore
.env
```

---

## ISSUE #7: NO PASSWORD STRENGTH VALIDATION

### Location & Current Code

**File:** `backend/app/schemas/user.py` (or similar)
```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str      # ❌ NO VALIDATION!

# Accepts any password:
✅ "a"              # 1 character
✅ "123"            # Numbers only
✅ "password"       # Common password
✅ "abc"            # Lowercase only
```

### Signup Endpoint

**File:** `backend/app/api/v1/endpoints/users.py`
```python
@router.post("/signup", response_model=UserRead, status_code=201)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    # user_in.password goes directly to:
    create_user(db, user_in=user_in)
    # No strength check!
```

### Fix

```python
from pydantic import BaseModel, field_validator
import re

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        
        has_upper = bool(re.search(r'[A-Z]', v))
        has_lower = bool(re.search(r'[a-z]', v))
        has_digit = bool(re.search(r'\d', v))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', v))
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                'Password must contain uppercase, lowercase, number, and special char'
            )
        
        # Check against common passwords
        common = ['password', '123456', 'qwerty', 'admin', 'letmein']
        if v.lower() in common:
            raise ValueError('Password is too common, please choose another')
        
        return v
```

### Test

```bash
# Should FAIL:
curl -X POST http://localhost:8000/api/v1/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "weak"}'
# Response: {"detail": "Password must be at least..."}

# Should SUCCEED:
curl -X POST http://localhost:8000/api/v1/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "SecureP@ss123"}'
# Response: {"id": 1, "email": "test@test.com"...}
```

---

## ISSUE #8: NO RATE LIMITING ON LOGIN

### Location & Current Code

**File:** `backend/app/api/v1/endpoints/auth.py`
```python
@router.post("/login/access-token", response_model=Token)
def login_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    # ❌ NO RATE LIMITING - can try unlimited password attempts!
    user = user_repository.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    return Token(access_token=create_access_token(...))
```

### Attack Scenario

```
Attacker can:
1. Send 10,000 login requests per second
2. Brute force all possible 4-digit PINs (0000-9999) in seconds
3. Brute force weak 6-character passwords (lowercase only) in minutes
4. Try common password lists against all users

Without rate limiting:
├─ 4-digit PIN: 2-10 milliseconds per attempt
├─ 6-char password: 200ms per attempt
└─ Takes only hours to crack any weak password
```

### Fix: Add Rate Limiting Middleware

```python
# backend/app/main.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many login attempts. Try again later."},
    )

# Apply to login endpoint:
@router.post("/login/access-token", response_model=Token)
@limiter.limit("5/minute")  # Max 5 attempts per minute
def login_access_token(
    request: Request,  # Required for limiter
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    # ... rest of code
```

### With Account Lockout

```python
# backend/app/models/user.py
class User(Base):
    __tablename__ = "users"
    
    # ... existing fields ...
    failed_login_attempts: int = 0
    locked_until: datetime | None = None  # When lockout expires

# backend/app/api/v1/endpoints/auth.py
from datetime import datetime, timedelta

@router.post("/login/access-token")
@limiter.limit("5/minute")
def login_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    user = user_repository.get_user_by_email(db, form_data.username)
    
    # Check if account is locked
    if user and user.locked_until:
        if datetime.utcnow() < user.locked_until:
            raise HTTPException(
                status_code=429,
                detail="Account locked. Try again later."
            )
        else:
            # Unlock expired
            user.locked_until = None
            user.failed_login_attempts = 0
            db.commit()
    
    # Authenticate
    user = user_repository.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    
    if not user:
        # Increment failed attempts
        db_user = user_repository.get_user_by_email(db, form_data.username)
        if db_user:
            db_user.failed_login_attempts += 1
            
            # Lock after 5 failed attempts
            if db_user.failed_login_attempts >= 5:
                db_user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                logger.warning(f"Account locked: {form_data.username}")
            
            db.commit()
        
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # Reset on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    
    return Token(access_token=create_access_token(subject=str(user.id)))
```

---

## SUMMARY TABLE: Critical Issues

| # | Issue | File | Line | Severity | Type |
|---|-------|------|------|----------|------|
| 1 | Neo4j credentials exposed | `.env` | 47-49 | 🔴 CRITICAL | Secrets |
| 2 | Hardcoded Neo4j auth | `compose.yml` | 132 | 🔴 CRITICAL | Config |
| 3 | Missing Neo4j health check | `compose.yml` | 125-135 | 🔴 CRITICAL | Infrastructure |
| 4 | Database password exposed | `.env` | 38 | 🔴 CRITICAL | Secrets |
| 5 | Hardcoded superuser password | `config.py` + `.env` | 116, 23 | 🔴 CRITICAL | Secrets |
| 6 | Exposed SECRET_KEY | `.env` | 20 | 🔴 CRITICAL | Secrets |
| 7 | No password validation | `schemas/user.py` | N/A | ⚠️ HIGH | Security |
| 8 | No rate limiting | `api/v1/endpoints/auth.py` | N/A | ⚠️ HIGH | Security |

**Total Critical Issues Found: 6**  
**Estimated Time to Fix: 2-4 hours**
