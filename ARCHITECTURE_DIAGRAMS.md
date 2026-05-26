# 🏗️ ARCHITECTURE DIAGRAM - Docker Compose Infrastructure

## Docker Compose Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE NETWORK                        │
│  (created automatically: cong-ngh-ph-n-m_default)               │
└─────────────────────────────────────────────────────────────────┘

   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
   │  PostgreSQL  │      │   Neo4j      │      │   Adminer    │
   │  (Port 5432) │      │ (Port 7687)  │      │ (Port 8080)  │
   │              │      │              │      │              │
   │  ✅ Health   │      │ ❌ No Health │      │              │
   │  Check       │      │ Check        │      │              │
   └──────────────┘      └──────────────┘      └──────────────┘
        │                      │
        │                      │
        └──────────┬───────────┘
                   │
              TIER 1: Databases
                   │
        ┌──────────┴──────────┐
        │                     │
    depends_on            depends_on
    service_healthy       service_started
        │                     │
        └──────────┬──────────┘
                   ▼
        ┌─────────────────────┐
        │   Prestart Task     │
        │ (Init Container)    │
        │                     │
        │ - Wait for DB       │
        │ - Run migrations    │
        │ - Create user       │
        │                     │
        │ ✅ Success Check    │
        └─────────────────────┘
                   │
              TIER 2: Initialization
                   │
        ┌──────────┴──────────┐
        │                     │
    depends_on            depends_on
    service_healthy       prestart_success
        │                     │
        └──────────┬──────────┘
                   ▼
        ┌─────────────────────┐
        │   Backend (FastAPI) │
        │   (Port 8000)       │
        │                     │
        │ ✅ Health Check     │
        │ at /health          │
        │                     │
        │ - Neo4j check       │
        │ - OpenFDA import    │
        └─────────────────────┘
                   │
              TIER 3: Backend API
                   │
                   │
                   ▼
        ┌─────────────────────┐
        │   Frontend (nginx)  │
        │   (Port 3000/5173)  │
        │                     │
        │ ❌ No Health Check  │
        │                     │
        │ - React app         │
        │ - API proxy         │
        └─────────────────────┘

              TIER 4: Frontend
```

---

## Database Connection Routes

```
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              SQLAlchemy Session Pool                 │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Pool Size: 5 (default)                        │  │  │
│  │  │  Max Overflow: 10                              │  │  │
│  │  │  Pool Pre-Ping: ✅ YES                         │  │  │
│  │  │  Pool Recycle: Default (1 hour)                │  │  │
│  │  │                                                │  │  │
│  │  │  Connections: ●●●                             │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                     │                                  │  │
│  │                     │ TCP                              │  │
│  │     ┌───────────────┼───────────────┐                 │  │
│  │     │               │               │                 │  │
│  │     ▼               │               ▼                 │  │
│  │  [Session]      [Session]      [Session]             │  │
│  └──────────────────────────────────────────────────────┘  │
│                     │                                       │
│      Docker Bridge Network (internal: "db:5432")           │
│                     │                                       │
└─────────────────────┼───────────────────────────────────────┘
                      │
                      │        ┌──────────────────────────┐
                      │        │  Host Port Mapping       │
                      │        │  localhost:5432 ←→ 5432  │
                      │        └──────────────────────────┘
                      │
            ┌─────────▼─────────┐
            │   PostgreSQL 18   │
            │                   │
            │ User: postgres    │
            │ Password: *****   │
            │ Database: app     │
            │ Port: 5432 (TCP)  │
            │                   │
            │ Data Volume:      │
            │ app-db-data:/...  │
            └───────────────────┘
```

---

## Neo4j Connection Routes

```
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                       │
│                                                              │
│  neo4j_service (Singleton)                                  │
│      │                                                       │
│      └─→ Neo4jRepository._driver                            │
│          │                                                   │
│          └─→ GraphDatabase.driver(NEO4J_URI, auth)          │
│              ├─ Neo4j Connection Pool (internal)             │
│              └─ Sessions (per query)                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Query Examples:                                      │  │
│  │  - Search drugs: MATCH (d:Drug) WHERE ...            │  │
│  │  - Create drugs: MERGE (d:Drug {name: $name})        │  │
│  │  - Health check: RETURN 1 AS result                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                     │                                        │
│                     │ Bolt Protocol (Port 7687)              │
│                     │ TLS Encrypted (neo4j+s://)             │
│      Docker Bridge or External                             │
│                     │                                        │
└─────────────────────┼────────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         │ Local Dev: │ Production:│
         │        neo4j:7687      neo4j+s://aura...
         │            │            │
         │            ▼            ▼
         │    ┌──────────────┐ ┌──────────────┐
         │    │ Neo4j Local  │ │ Neo4j Aura   │
         │    │              │ │ (Cloud)      │
         │    │ Port: 7687   │ │ Port: 443    │
         │    │ Password: *** │ │ TLS: ✅      │
         │    │ Auth: neo4j/ │ │              │
         │    │ Volume: ...  │ │ Managed      │
         │    └──────────────┘ └──────────────┘
         │
         └─ HTTP Console: 7474
            (Admin UI, not for queries)
```

---

## Startup Sequence Timeline

```
Time  Component      Action                          Status
────────────────────────────────────────────────────────────────

0s    PostgreSQL     docker run postgres:18
1-2s  PostgreSQL     Starting background processes
3s    PostgreSQL     Accepting connections READY! ✅

0s    Neo4j          docker run neo4j:5
5s    Neo4j          Loading database...
15s   Neo4j          Ready for connections READY! ✅
                     (but no health check to verify)

0s    Adminer        docker run adminer
2s    Adminer        Ready ✅
      (depends on db:healthy)

30s   Prestart       Starts (when db:healthy ✅)
35s   Prestart       - Running backend_pre_start.py
         └─ Retries 300 times (wait for SELECT 1)
36s   Prestart       - Running migrations (alembic upgrade head)
40s   Prestart       - Creating initial data
42s   Prestart       SUCCESS! ✅

43s   Backend        Starts (depends on prestart:success)
44s   Backend        - Loading FastAPI
45s   Backend        - Testing Neo4j connectivity (non-blocking)
45s   Backend        - Running openFDA import (non-blocking)
        └─ Fetches 20 drugs from api.fda.gov (network time!)
        └─ Inserts into Neo4j
55s   Backend        Ready to receive requests ✅
55s   Backend        /health returns {"status": "ok"} ✅

50s   Frontend       docker run frontend:nginx
52s   Frontend       Ready to serve React app ✅

────────────────────────────────────────────────────────────────
FINAL: All services up and healthy (~55-90 seconds)
```

---

## Database Schema & Relationships

```
┌─────────────────────────┐
│    PostgreSQL (SQL)     │
└─────────────────────────┘

  users (RELATIONAL)
  ┌──────────────────────────┐
  │ id: INTEGER (PK)         │
  │ email: VARCHAR (UNIQUE)  │
  │ hashed_password: VARCHAR │
  │ full_name: VARCHAR       │
  │ is_active: BOOLEAN       │
  │ created_at: DATETIME     │
  └──────────────────────────┘

        ↓ Relationships via ORM
        
┌─────────────────────────┐
│   Neo4j (Graph DB)      │
└─────────────────────────┘

Nodes:
  ├─ Drug
  │  ├── name
  │  ├── generic_name
  │  ├── purpose
  │  ├── warnings
  │  └── dosage
  │
  ├─ Ingredient
  │  └── name
  │
  ├─ Manufacturer
  │  └── name
  │
  ├─ Disease
  │  ├── name
  │  └── description
  │
  └─ Test (for health checks)

Relationships:
  ├─ Drug -[CONTAINS]-> Ingredient
  ├─ Drug -[MADE_BY]-> Manufacturer
  ├─ Drug -[INTERACTS_WITH]-> Drug
  ├─ Drug -[TREATS]-> Disease
  └─ Drug -[WARNING_FOR]-> Disease

Search Performance:
  ├─ Drug name search: O(n) or O(1) if indexed
  ├─ Graph traversal: Fast for relationship queries
  └─ Full-text search: Good for symptom discovery
```

---

## Environment Variable Flow

```
┌──────────────────────────────────────┐
│          .env File                   │
│ ┌────────────────────────────────┐   │
│ │ POSTGRES_PASSWORD=changethis   │   │
│ │ NEO4J_URI=neo4j+s://3...       │   │
│ │ SECRET_KEY=changethis          │   │
│ │ ...                            │   │
│ └────────────────────────────────┘   │
└──────────────────────────────────────┘
           │ Load (priority #1)
           ▼
┌──────────────────────────────────────┐
│     compose.yml env_file             │
│ env_file:                            │
│   - .env                             │
└──────────────────────────────────────┘
           │ Override (priority #2)
           ▼
┌──────────────────────────────────────┐
│    compose.yml environment           │
│ environment:                         │
│   - POSTGRES_SERVER=db               │
│   - NEO4J_USERNAME=${NEO4J_USERNAME} │
│   ...                                │
└──────────────────────────────────────┘
           │ Pass to container
           ▼
┌──────────────────────────────────────┐
│      Backend Container               │
│ app.core.config.Settings             │
│ ├─ POSTGRES_SERVER = "db"            │
│ ├─ POSTGRES_PASSWORD = "changethis"  │
│ ├─ NEO4J_URI = "neo4j+s://3..."     │
│ ├─ SECRET_KEY = "changethis"         │
│ └─ ...                               │
└──────────────────────────────────────┘
           │ Build connection strings
           ▼
┌──────────────────────────────────────┐
│   SQLAlchemy Database URIs           │
│                                      │
│ postgresql+psycopg://                │
│   postgres:changethis@db:5432/app   │
│                                      │
│ GraphDatabase.driver:                │
│   neo4j+s://3...                    │
│   auth=(3e08ff89, wV2Tnpv...)       │
└──────────────────────────────────────┘
```

---

## Health Check Status Flow

```
Docker Compose Health Checks:

┌─────────────────┐
│  PostgreSQL     │  Status: 'healthy'
├─────────────────┤
│ pg_isready ✅   │  Interval: 10s
│ Retries: 5      │  Start: 30s
│ Timeout: 10s    │  Consecutive: 5 failures = unhealthy
└─────────────────┘

┌─────────────────┐
│  Neo4j          │  Status: ❌ 'unknown' (no check!)
├─────────────────┤
│ No check        │  ⚠️ SHOULD HAVE:
│ (missing!)      │     curl http://localhost:7474/.../exec
└─────────────────┘

┌─────────────────┐
│  Backend        │  Status: 'healthy'
├─────────────────┤
│ curl /health ✅ │  Interval: 10s
│ Retries: 5      │  Timeout: 5s
│ Test: 200 OK    │
└─────────────────┘

┌─────────────────┐
│  Frontend       │  Status: ❌ 'unknown' (no check!)
├─────────────────┤
│ No check        │  ⚠️ SHOULD HAVE:
│ (missing!)      │     curl http://localhost/
└─────────────────┘

Service Start Order Enforcement:

┌─ start db ─→ (wait healthy) ─→ start prestart ─→ (wait success) ─→ start backend
├─ start neo4j ─→ (wait started) ─→ start backend
└─ start frontend ─→ (no dependencies)

⚠️ Issue: backend depends on neo4j "started" (not "healthy")
        Could still be initializing when backend tries to connect!
```

---

## Code Flow - Request to Database

```
REQUEST: GET /api/v1/neo4j/drugs/search?query=aspirin

┌───────────────────────────────────────┐
│  Frontend (React)                     │
│  axios.get("/api/v1/neo4j/drugs...")  │
└───────────────────────────────────────┘
           │ HTTP
           ▼
┌───────────────────────────────────────┐
│  Backend (FastAPI)                    │
│  @router.get("/drugs/search")         │
│  def search_drugs(query: str):        │
│    return neo4j_service.search_drugs()│
└───────────────────────────────────────┘
           │
           ▼
┌───────────────────────────────────────┐
│  Neo4j Service (Singleton)            │
│  neo4j_service.search_drugs("aspirin")│
│    └─ Calls: repository.execute_read()│
└───────────────────────────────────────┘
           │
           ▼
┌───────────────────────────────────────┐
│  Neo4j Repository                     │
│  execute_read(query, **params)        │
│    └─ _ensure_driver()                │
│    └─ with driver.session():          │
│         result = session.run(query)   │
│         return [record.data()]        │
└───────────────────────────────────────┘
           │ Bolt Protocol (7687)
           │ TLS Encrypted
           ▼
┌───────────────────────────────────────┐
│  Neo4j Database                       │
│  MATCH (d:Drug)                       │
│  WHERE toLowerCase(d.name)            │
│        CONTAINS toLowerCase($search)  │
│  RETURN {id, name, ...}               │
│                                       │
│  Response: [Record1, Record2, ...]    │
└───────────────────────────────────────┘
           │
           ▼ [dict, dict, ...]
┌───────────────────────────────────────┐
│  Backend Response                     │
│  {                                    │
│    "status": "success",               │
│    "drugs": [                         │
│      {"id": 123, "name": "Aspirin"...}│
│    ]                                  │
│  }                                    │
└───────────────────────────────────────┘
           │ HTTP/JSON
           ▼
┌───────────────────────────────────────┐
│  Frontend Receives & Displays         │
│  UI shows search results              │
└───────────────────────────────────────┘
```

---

## PostgreSQL Request Flow

```
REQUEST: GET /api/v1/users/me

┌───────────────────────────────────────┐
│  Backend Dependency Injection         │
│  Depends(get_db) → Session            │
├───────────────────────────────────────┤
│  def get_db():                        │
│    with Session(engine) as session:   │
│      yield session                    │
│                                       │
│  engine.pool gets connection:         │
│  ├─ Check if connection available     │
│  ├─ If not: Create new (if < 5)      │
│  ├─ Test connection (pool_pre_ping)   │
│  └─ Return to endpoint                │
└───────────────────────────────────────┘
           │
           ▼
┌───────────────────────────────────────┐
│  Endpoint Handler                     │
│  def get_current_user(                │
│      session: SessionDep,             │
│      token: TokenDep                  │
│  ) -> User:                           │
│    user = session.query(User)         │
│      .filter(User.id == user_id)      │
│      .first()                         │
└───────────────────────────────────────┘
           │ SQL Query
           │ SELECT * FROM users
           │ WHERE id = $1
           ▼
┌───────────────────────────────────────┐
│  PostgreSQL (Port 5432)               │
│  Executes query                       │
│  Returns user row                     │
└───────────────────────────────────────┘
           │ Result row
           ▼
┌───────────────────────────────────────┐
│  SQLAlchemy                           │
│  Converts row to User model instance  │
│  Returns ORM object to handler        │
└───────────────────────────────────────┘
           │
           └─→ Pydantic serialization
               ─→ JSON response
               ─→ Frontend
```

---

## Summary: Data Flow Diagram

```
┌──────────────┐
│  Frontend    │ (React)
│  Port 3000   │
└──────┬───────┘
       │ HTTP/JSON
       ▼
┌──────────────────────────────┐
│      Backend                 │
│   FastAPI                    │
│   Port 8000                  │
│                              │
│  ┌──────────────────────┐    │
│  │ SQLAlchemy + ORM     │    │
│  │   (PostgreSQL)       │    │
│  └────────┬─────────────┘    │
│           │                  │
│  ┌────────▼─────────────┐    │
│  │ Neo4j Service        │    │
│  │   (Graph queries)    │    │
│  └────────┬─────────────┘    │
└───────────┼──────────────────┘
            │
   ┌────────┴────────┐
   │                 │
   ▼                 ▼
┌─────────┐     ┌──────────┐
│PostgreSQL    Neo4j      │
│Port 5432│     │Port 7687 │
│         │     │          │
│Users    │     │Drugs     │
│Reports  │     │Diseases  │
│Etc      │     │Interactions│
└─────────┘     └──────────┘
```
