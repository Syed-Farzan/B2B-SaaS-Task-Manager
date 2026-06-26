# 🗂️ B2B SaaS Task Manager API

A **multi-tenant, production-grade backend API** built with FastAPI and PostgreSQL — designed to power corporate workspace collaboration platforms. Think Jira or Linear, but the engine underneath.

> **Portfolio Project** · Month 2 Flagship · Backend Engineering Roadmap

---

## 🔥 What Makes This Production-Grade

- **Logical Multi-Tenancy** — Single database, complete data isolation. A user from Company B querying Company A's resources gets a `404`, not a `403`. They can't even confirm the data exists.
- **JWT Auth with RBAC** — Short-lived access tokens + long-lived refresh tokens. Every protected route enforces role (`Admin` / `Member`) via FastAPI's dependency injection before hitting the database.
- **Tenant Injection at the Query Layer** — `organization_id` is extracted from the JWT and appended to every SQL query dynamically. No cross-tenant data leakage is architecturally possible.
- **Async SQLAlchemy 2.0** — Non-blocking database sessions throughout.
- **Alembic Migrations** — Schema changes are version-controlled and reproducible.
- **Dockerized** — Full `docker-compose` setup with health-checked DB startup sequencing.

---

## 🛠️ Tech Stack

| Layer            | Technology              |
| ---------------- | ----------------------- |
| Framework        | FastAPI                 |
| Database         | PostgreSQL 15           |
| ORM              | SQLAlchemy 2.0 (Async)  |
| Migrations       | Alembic                 |
| Auth             | JWT (PyJWT) + Bcrypt    |
| Validation       | Pydantic v2             |
| Containerization | Docker + Docker Compose |
| Runtime          | Uvicorn (ASGI)          |
| Language         | Python 3.11             |

---

## 📁 Project Structure

```
saas-task-manager/
│
├── alembic/                  # Migration scripts
│   ├── versions/             # Timestamped migration files
│   └── env.py                # Reads SQLAlchemy models
│
├── app/
│   ├── main.py               # App init, middleware, core routing
│   │
│   ├── api/                  # HTTP Routers (Interface Layer)
│   │   ├── auth.py           # Register, login, refresh
│   │   ├── users.py          # Invite members, profile management
│   │   ├── projects.py       # Project CRUD
│   │   └── tasks.py          # Tasks + comments pipeline
│   │
│   ├── core/
│   │   ├── config.py         # Pydantic BaseSettings (.env loader)
│   │   └── security.py       # Bcrypt hashing + JWT encode/decode
│   │
│   ├── db/
│   │   └── database.py       # Async engine + SessionLocal
│   │
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── organization.py
│   │   ├── user.py
│   │   ├── project.py
│   │   └── task.py
│   │
│   ├── schemas/              # Pydantic validation schemas
│   │   ├── token_schema.py
│   │   ├── user_schema.py
│   │   └── task_schema.py
│   │
│   └── crud/                 # Data Access Layer (multi-tenant safe)
│       ├── crud_organization.py
│       ├── crud_user.py
│       └── crud_task.py
│
├── .env.example
├── .gitignore
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## ⚙️ How Multi-Tenancy Works

```
POST /api/v1/projects  [Authorization: Bearer <JWT>]
         │
         ▼
  1. JWT Middleware       → Verifies signature + expiry
         │
         ▼
  2. RBAC Check           → role == "Admin"? else 403
         │
         ▼
  3. Tenant Injection     → Extracts organization_id from token
         │
         ▼
  4. DB Query             → INSERT ... WHERE organization_id = <extracted_id>
```

Every read query appends `WHERE organization_id = current_user.organization_id`. A cross-tenant request returns `404` — existence of data is never revealed.

---

## 🗃️ Database Schema

```
organizations
  └── id (UUID, PK)
  └── name (VARCHAR)
  └── created_at

users
  └── id (UUID, PK)
  └── organization_id (FK → organizations, CASCADE)
  └── email (UNIQUE, INDEX)
  └── hashed_password
  └── role ['Admin' | 'Member']

projects
  └── id (UUID, PK)
  └── organization_id (FK → organizations, CASCADE)
  └── title
  └── description (NULLABLE)

tasks
  └── id (UUID, PK)
  └── project_id (FK → projects, CASCADE)
  └── assignee_id (FK → users, SET NULL)
  └── title
  └── status [default: 'To Do']
  └── priority [default: 'Medium']
```

---

## 🔌 API Endpoints

### Auth & Workspace

| Method | Endpoint                | Access | Description                                           |
| ------ | ----------------------- | ------ | ----------------------------------------------------- |
| `POST` | `/api/v1/auth/register` | Public | Creates a new tenant org + root Admin user atomically |
| `POST` | `/api/v1/auth/login`    | Public | Returns access JWT + refresh JWT                      |
| `POST` | `/api/v1/users/invite`  | Admin  | Registers a new member into the caller's organization |

### Projects

| Method | Endpoint           | Access         | Description                                |
| ------ | ------------------ | -------------- | ------------------------------------------ |
| `GET`  | `/api/v1/projects` | Admin & Member | Lists all projects scoped to caller's org  |
| `POST` | `/api/v1/projects` | Admin          | Creates a project bound to caller's tenant |

### Tasks

| Method  | Endpoint                              | Access         | Description                                       |
| ------- | ------------------------------------- | -------------- | ------------------------------------------------- |
| `POST`  | `/api/v1/projects/{project_id}/tasks` | Admin          | Creates a task inside a validated project         |
| `PATCH` | `/api/v1/tasks/{task_id}/status`      | Admin & Member | Advances task status (To Do → In Progress → Done) |
| `POST`  | `/api/v1/tasks/{task_id}/comments`    | Admin & Member | Appends a comment after validating tenant context |

---

## 🚀 Local Setup

### Prerequisites

- Docker & Docker Compose installed
- That's it.

### 1. Clone the repo

```bash
git clone https://github.com/Syed-Farzan/saas-task-manager.git
cd saas-task-manager
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your values
```

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/taskmanager
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 3. Start the containers

```bash
docker-compose up --build
```

The API container waits for PostgreSQL to pass its health check before starting Uvicorn. No race conditions.

### 4. Run migrations

```bash
docker-compose exec api alembic upgrade head
```

### 5. Access the API

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Testing the Flow

```bash
# 1. Register a new organization + Admin user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"org_name": "Acme Corp", "email": "admin@acme.com", "password": "strongpass123"}'

# 2. Login and grab the access token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@acme.com", "password": "strongpass123"}'

# 3. Create a project (Admin only)
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Q3 Roadmap", "description": "Product work for Q3"}'

# 4. Invite a team member
curl -X POST http://localhost:8000/api/v1/users/invite \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"email": "dev@acme.com", "password": "memberpass123"}'
```

---

## 🐳 Docker Services

| Service | Image                | Port          |
| ------- | -------------------- | ------------- |
| `api`   | `python:3.11-slim`   | `8000:8000`   |
| `db`    | `postgres:15-alpine` | Internal only |

Data persists across restarts via the `postgres_data` named volume mapped to `/var/lib/postgresql/data`.

---

## 🔐 Security Design

- Passwords hashed with **bcrypt** (never stored in plaintext)
- JWT signed with `HS256` — secret stored in `.env`, never committed
- Access tokens expire in **30 minutes**
- Refresh tokens expire in **7 days**
- `organization_id` is bound at registration — never user-supplied in request bodies post-auth
- Cross-tenant isolation enforced at the **query layer**, not the application layer

---

## 📌 Key Concepts Demonstrated

- Multi-tenant SaaS architecture with logical data isolation
- JWT authentication with refresh token rotation
- Role-Based Access Control (RBAC) via FastAPI `Depends()`
- Async database sessions with SQLAlchemy 2.0
- Alembic migrations with autogenerate
- Docker Compose orchestration with health check dependencies
- Pydantic v2 schema validation
- Clean layered architecture (Router → Service → CRUD → DB)

---

## 📬 Author

**Syed Farzan**  
Backend Engineering · FastAPI · PostgreSQL  
[GitHub](https://github.com/Syed-Farzan) · [LinkedIn](https://www.linkedin.com/in/syed-arhan-6b1bb327b?utm_source=share_via&utm_content=profile&utm_medium=member_ios)
