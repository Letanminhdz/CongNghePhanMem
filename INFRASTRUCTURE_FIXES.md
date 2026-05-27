# 🔍 QUICK REFERENCE - Infrastructure Issues & Code Snippets

## 📌 CRITICAL FINDINGS

### 1. NEO4J MISSING HEALTH CHECK

**Current Problem:**
```yaml
# compose.yml
neo4j:
  image: neo4j:5
  restart: always
  # ❌ NO HEALTHCHECK - backend may start before Neo4j is ready
```

**Fix:**
```yaml
neo4j:
  image: neo4j:5
  restart: always
  environment:
    - NEO4J_AUTH=${NEO4J_USERNAME}/${NEO4J_PASSWORD}  # Use env vars!
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:7474/db/neo4j/exec"]
    interval: 10s
    retries: 5
    start_period: 30s
    timeout: 10s
  ports:
    - "7474:7474"
    - "7687:7687"
  volumes:
    - neo4j-data:/data
```

---

### 2. NEO4J CREDENTIALS EXPOSED IN GIT

**Current Problem:**
```bash
# .env file (TRACKED IN GIT - CRITICAL!)
NEO4J_URI=neo4j+s://3e08ff89.databases.neo4j.io
NEO4J_USERNAME=3e08ff89
NEO4J_PASSWORD=wV2TnpvJD3DiQpQbTogvX8WdmOPfrarOdWyVN_d1Es0
# ^ ANYONE WITH ACCESS TO REPO CAN ACCESS NEO4J
```

**Fix:**

```bash
# Step 1: Create .gitignore (if not exists)
cat > .gitignore << 'EOF'
.env
.env.local
.env.*.local
secrets/
EOF

# Step 2: Create .env.example with placeholders
cat > .env.example << 'EOF'
# Neo4j - Replace with your credentials
NEO4J_URI=neo4j+s://YOUR_AURA_INSTANCE_ID.databases.neo4j.io
NEO4J_USERNAME=YOUR_USERNAME
NEO4J_PASSWORD=YOUR_PASSWORD_HERE

# Database
POSTGRES_PASSWORD=change_me_in_production
SECRET_KEY=generate_with_secrets.token_urlsafe(32)
FIRST_SUPERUSER_PASSWORD=change_me_in_production
EOF

# Step 3: Stop tracking .env
git rm --cached .env
git commit -m "Remove .env from tracking"

# Step 4: Rotate all exposed credentials immediately!
```

---

### 3. HARDCODED NEO4J_AUTH IN DOCKER COMPOSE

**Current Problem:**
```yaml
# compose.yml Line 132
environment:
  - NEO4J_AUTH=neo4j/password123  # ❌ Hardcoded!
```

**Current Impact:**
```
- Uses hardcoded "password123" instead of .env value
- Developer changes NEO4J_PASSWORD in .env but Neo4j still uses "password123"
- Connect string uses different password than Docker Compose sets up
```

**Fix:**
```yaml
# compose.yml
neo4j:
  image: neo4j:5
  restart: always
  environment:
    - NEO4J_AUTH=${NEO4J_USERNAME?Variable not set}/${NEO4J_PASSWORD?Variable not set}
    # Now uses variables from .env!
```

**Verify with:**
```bash
docker-compose config | grep NEO4J_AUTH
# Should show actual values from .env, not hardcoded
```

---

### 4. POSTGRES CONNECTION STRING IN DOCKER

**Current Setup:**
```python
# config.py defaults
POSTGRES_SERVER: str = "localhost"  # Wrong in Docker!

# But compose.yml overrides it:
POSTGRES_SERVER=db                  # Correct for Docker
```

**Potential Problem:**
```
If someone runs backend outside Docker:
- Will try localhost:5432 ✅ Correct for local dev

If someone forgets env in compose.yml:
- Backend tries localhost (~95 seconds timeout) ❌ Slow failure
```

**Robust Solution:**
```python
# config.py
POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "db")
# Default to "db" (Docker hostname) instead of "localhost"

# Then in production .env:
POSTGRES_SERVER=db              # For Docker
# Or in local .env:
POSTGRES_SERVER=localhost       # For local dev
```

---

## 🔧 RECOMMENDED FIXES

### Fix 1: Add Neo4j Health Check

**File to edit:** `compose.yml` (Line 125-135)

```yaml
# Before:
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

# After:
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
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7474/db/neo4j/exec"]
      interval: 10s
      retries: 5
      start_period: 30s
      timeout: 10s
```

---

### Fix 2: Add Frontend Health Check

**File to edit:** `compose.yml` (Find frontend service)

```yaml
# Add health check to frontend:
  frontend:
    image: '${DOCKER_IMAGE_FRONTEND?Variable not set}:${TAG-latest}'
    restart: always
    ports:
      - "3000:80"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s
    build:
      context: .
      dockerfile: frontend/Dockerfile
```

---

### Fix 3: Update Backend Dockerfile

**File to edit:** `backend/Dockerfile`

**Current issues:**
1. Runs as root (security issue)
2. No health check in Dockerfile
3. No multi-stage build (includes build tools in final image)

**Recommended replacement:**
```dockerfile
# Multi-stage build
FROM python:3.11-slim-bookworm as builder

WORKDIR /app/backend

# Install only build requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install packages
COPY ../requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ============================================
# Final stage - minimal production image
# ============================================
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend

WORKDIR /app/backend

# Copy pip packages from builder (no build tools!)
COPY --from=builder /root/.local /root/.local

# Add non-root user
RUN useradd -m appuser && \
    chown -R appuser:appuser /app/backend

# Copy source code
COPY backend/ .

# Switch to non-root user
USER appuser

# Add local pip to PATH
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000

# Health check in Dockerfile (also in compose.yml)
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Benefits:**
```
- ✅ Runs as non-root (better security)
- ✅ Smaller image (no gcc/build tools in final stage)
- ✅ Health check in Dockerfile (independent of compose.yml)
- ✅ Better layer caching (code changes don't rebuild pip packages)
```

---

### Fix 4: Optimize PostgreSQL Connection Pool

**File to edit:** `backend/app/db/session.py`

```python
# Before:
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
)

# After:
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Choose pooling strategy based on environment
if settings.ENVIRONMENT == "production":
    # QueuePool: Standard pooling for production
    pool_class = QueuePool
    pool_size = 20
    max_overflow = 30
    pool_recycle = 300  # Recycle after 5 minutes
    pool_pre_ping = True
elif settings.ENVIRONMENT in ("staging", "local"):
    # Smaller pool for development
    pool_class = QueuePool
    pool_size = 5
    max_overflow = 10
    pool_recycle = 300
    pool_pre_ping = True
else:
    # NullPool for testing (no pooling)
    pool_class = NullPool

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    poolclass=pool_class,
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_recycle=pool_recycle,
    pool_pre_ping=pool_pre_ping,
    echo_pool=settings.DEBUG,  # Log pool events in debug mode
)

# Optional: Log pool events for monitoring
if settings.DEBUG:
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_connection, connection_record):
        logger.debug(f"Pool: New connection created")

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        logger.debug(f"Pool: Connection checked out (pool size: {engine.pool.checkedout()})")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

---

### Fix 5: Add Docker Logging Configuration

**File to edit:** `compose.yml` (Add to all services)

```yaml
# Add this to db, neo4j, backend, frontend services:
services:
  db:
    image: postgres:18
    # ... other config ...
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
        labels: "app=medical-chatbot,service=postgres"

  neo4j:
    image: neo4j:5
    # ... other config ...
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
        labels: "app=medical-chatbot,service=neo4j"

  backend:
    image: '${DOCKER_IMAGE_BACKEND?Variable not set}:${TAG-latest}'
    # ... other config ...
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
        labels: "app=medical-chatbot,service=backend"

  frontend:
    image: '${DOCKER_IMAGE_FRONTEND?Variable not set}:${TAG-latest}'
    # ... other config ...
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
        labels: "app=medical-chatbot,service=frontend"
```

**Benefits:**
- Prevents disk from filling up with logs
- Keeps only last 3 files (300MB total max per service)
- Labels for filtering with `docker logs --filter`

---

## 🧪 TESTING & VERIFICATION

### Test 1: Verify Neo4j Health Check Works

```bash
# Start services
docker-compose up -d

# Wait 60 seconds for everything to boot
sleep 60

# Check health status
docker-compose ps

# Expected output:
# neo4j    neo4j:5    Up X minutes (healthy)    <-- Check this!

# If showing "unhealthy":
docker-compose logs neo4j | tail -50
# Look for connection refused errors

# Test connectivity manually:
curl -f http://localhost:7474/db/neo4j/exec
# Should return 200 or 401 (not 000 connection error)
```

---

### Test 2: Verify PostgreSQL Connection Pooling

```bash
# Watch pool events (if debugging enabled)
docker-compose logs backend | grep "Pool:"

# Example output:
# backend    | 2024-05-26 10:15:23 - Pool: New connection created
# backend    | 2024-05-26 10:15:24 - Pool: Connection checked out
```

---

### Test 3: Verify Docker Logging Limits

```bash
# Check log file size
docker inspect --format='{{.LogPath}}' cong-ngh-ph-n-m-backend-1

# Check actual size
ls -lh /var/lib/docker/containers/.../\*-json.log

# Should not grow larger than 100MB
```

---

### Test 4: Verify Environment Variables

```bash
# Check compose resolves variables correctly
docker-compose config | grep -A 10 "neo4j:"

# Should show actual values:
# environment:
#   - NEO4J_AUTH=3e08ff89/wV2TnpvJD...
```

---

## 🎯 STARTUP SEQUENCE VERIFICATION

### Expected Startup (with all fixes):

```
$ docker-compose up
Creating postgres ... done
Creating neo4j ... done
Creating adminer ... done

[db] - postgres is ready to accept connections
[db] ✅ status: healthy

[neo4j] - Neo4j is ready
[neo4j] ✅ status: healthy after ~30 seconds

[prestart] - Waiting for db (healthy) ✅
[prestart] - Running migrations...
[prestart] - Creating initial data...
[prestart] ✅ exited with code 0

[backend] - Initializing service...
[backend] - Neo4j connected successfully
[backend] - Starting automatic openFDA import...
[backend] - Imported 20 drugs
[backend] ✅ status: healthy

[frontend] - Starting nginx...
[frontend] ✅ status: healthy
```

**Total expected time: 60-90 seconds**

---

## 🔐 SECURITY CHECKLIST

- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` has placeholder values (no real credentials)
- [ ] All credentials are in environment variables (not hardcoded)
- [ ] Backend runs as non-root user
- [ ] HTTPS enabled in production (not HTTP)
- [ ] Database passwords are changed from defaults
- [ ] Secret key is generated (not "changethis")
- [ ] Neo4j password is rotated
- [ ] All exposed credentials on GitHub are revoked

---

## 📊 PERFORMANCE NOTES

### PostgreSQL Connection Pooling

```
Current (default): 5 connections + 10 overflow
Recommended for low load: 10 connections + 15 overflow
Recommended for medium load: 20 connections + 30 overflow
Recommended for high load: 50+ connections + 100+ overflow

Pool recycle: 300 seconds (5 minutes)
- Recycles connections to handle idle timeouts
- Important for cloud databases (AWS RDS, etc)
```

### Neo4j Session Management

```
Current: New session per query (acceptable)
Better: Connection pool with reusable sessions

The Neo4j Python driver handles pooling internally:
- Default max connections: 500
- Default connection timeout: 30 seconds
- Connections are acquired per session
```

---

## 🚀 DEPLOYMENT CONSIDERATIONS

### For Production:

1. **Remove .env from git entirely**
   ```bash
   git rm .env
   git commit -m "Remove .env"
   ```

2. **Use external secrets management:**
   - GitHub Secrets (CI/CD)
   - AWS Secrets Manager (EC2/ECS)
   - Google Secret Manager (GCP)
   - HashiCorp Vault
   - Azure Key Vault

3. **Change all default passwords:**
   ```bash
   # Use `openssl rand -base64 32` to generate
   SECRET_KEY=$(openssl rand -base64 32)
   POSTGRES_PASSWORD=$(openssl rand -base64 32)
   NEO4J_PASSWORD=$(openssl rand -base64 32)
   ```

4. **Enable TLS/HTTPS:**
   - Use Let's Encrypt (free certificates)
   - Configure Traefik or nginx as reverse proxy

5. **Add database backups:**
   - Daily backups to S3/GCS
   - Automated restore testing

6. **Monitor and alert:**
   - Setup Prometheus + Grafana
   - Alert on service unhealthy status
   - Alert on disk space usage
