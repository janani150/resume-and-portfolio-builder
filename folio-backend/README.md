# Folio Backend — FastAPI + MongoDB + PostgreSQL

Production-grade backend for the Folio Resume & Portfolio Builder.

---

## Stack

| Layer | Technology |
|---|---|
| API Framework | **FastAPI** (async, auto-docs) |
| SQL Database | **PostgreSQL** via SQLAlchemy 2.0 |
| Document Store | **MongoDB** via Motor (async) |
| Auth | **JWT** (access + refresh tokens, rotation) |
| Password hashing | **bcrypt** via passlib |
| AI | **Anthropic Claude** (claude-sonnet-4) |
| PDF Generation | **WeasyPrint** + Jinja2 |
| Rate Limiting | **SlowAPI** + Redis |
| Migrations | **Alembic** |

---

## Project Structure

```
folio-backend/
├── app/
│   ├── main.py                  # FastAPI app factory + lifespan
│   ├── api/
│   │   ├── deps.py              # Auth dependencies (get_current_user etc.)
│   │   └── v1/
│   │       ├── router.py        # Wires all sub-routers
│   │       └── endpoints/
│   │           ├── auth.py      # Register, Login, Refresh, Logout, Me
│   │           ├── resumes.py   # Full resume CRUD + public share link
│   │           ├── portfolios.py# Portfolio CRUD + publish + templates
│   │           ├── ai.py        # AI enhance, ATS check, skill suggest
│   │           └── pdf.py       # PDF generation + download
│   ├── core/
│   │   ├── config.py            # Pydantic settings from .env
│   │   ├── database.py          # PostgreSQL + MongoDB connections
│   │   └── security.py          # JWT + bcrypt helpers
│   ├── models/
│   │   └── models.py            # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── schemas.py           # Pydantic v2 request/response schemas
│   ├── services/
│   │   ├── ai_service.py        # Claude API integration
│   │   └── pdf_service.py       # WeasyPrint PDF generation
│   └── templates/
│       └── resume/
│           └── modern.html      # Jinja2 PDF template
├── alembic/                     # DB migrations
├── tests/                       # pytest test suite
├── .env.example
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Clone & install

```bash
git clone <repo>
cd folio-backend

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your DB credentials, Anthropic API key, etc.
```

### 3. Set up databases

```bash
# PostgreSQL
createdb folio_db

# Run Alembic migrations
alembic upgrade head

# MongoDB — no setup needed, Motor creates collections automatically
```

### 4. Run the server

```bash
# Development (hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Open API docs

- Swagger UI: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc

---

## API Reference

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Sign in → get tokens |
| POST | `/api/v1/auth/refresh` | Rotate refresh token |
| POST | `/api/v1/auth/logout` | Revoke refresh token |
| GET | `/api/v1/auth/me` | Get current user |
| PUT | `/api/v1/auth/me` | Update profile |

### Resumes

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/resumes` | List user's resumes |
| POST | `/api/v1/resumes` | Create resume |
| GET | `/api/v1/resumes/{id}` | Get resume + full data |
| PUT | `/api/v1/resumes/{id}` | Update resume |
| DELETE | `/api/v1/resumes/{id}` | Delete resume |
| POST | `/api/v1/resumes/{id}/clone` | Duplicate resume |
| GET | `/api/v1/r/{slug}` | Public share link |

### AI Enhancement

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/ai/enhance` | Enhance/rewrite text |
| POST | `/api/v1/ai/ats-check` | Score resume vs job description |
| POST | `/api/v1/ai/generate-summary` | Auto-generate professional summary |
| POST | `/api/v1/ai/suggest-skills` | Suggest missing skills |

**AI Enhance modes:** `enhance` | `quantify` | `summary` | `keywords`

### PDF

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/pdf/generate/{resume_id}` | Generate + download PDF |
| GET | `/api/v1/pdf/preview/{resume_id}` | Preview PDF inline |

### Portfolios

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/portfolios` | List portfolios |
| POST | `/api/v1/portfolios` | Create portfolio |
| GET | `/api/v1/portfolios/{id}` | Get portfolio + data |
| PUT | `/api/v1/portfolios/{id}` | Update portfolio |
| DELETE | `/api/v1/portfolios/{id}` | Delete portfolio |
| POST | `/api/v1/portfolios/{id}/publish` | Publish with subdomain |

### Templates

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/templates?kind=resume` | List resume templates |
| GET | `/api/v1/templates?kind=portfolio` | List portfolio templates |
| GET | `/api/v1/templates/{id}` | Get template by ID |

---

## Example Requests

### Register
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Janani",
    "last_name": "Priya",
    "email": "janani@example.com",
    "password": "SecurePass1"
  }'
```

### Create Resume
```bash
curl -X POST http://localhost:8000/api/v1/resumes \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Software Engineer Resume",
    "data": {
      "first_name": "Janani",
      "last_name": "Priya",
      "professional_title": "Full Stack Developer",
      "email": "janani@example.com",
      "summary": "Experienced developer...",
      "skills": ["React", "Python", "Flask"],
      "experience": [{
        "job_title": "Software Engineer",
        "company": "Acme Corp",
        "start_date": "2022-01",
        "end_date": "Present",
        "description": "• Built real-time dashboard\n• Reduced latency by 40%"
      }],
      "education": [{
        "institution": "XYZ University",
        "degree": "B.Tech Computer Science",
        "start_year": 2020,
        "end_year": 2024
      }],
      "contact": {
        "phone": "+91 98765 43210",
        "github": "github.com/janani"
      },
      "projects": []
    }
  }'
```

### AI Enhance
```bash
curl -X POST http://localhost:8000/api/v1/ai/enhance \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "worked on a dashboard that many users used",
    "mode": "enhance"
  }'
```

### Download PDF
```bash
curl -X POST http://localhost:8000/api/v1/pdf/generate/<resume_id> \
  -H "Authorization: Bearer <token>" \
  --output resume.pdf
```

---

## Data Architecture

```
PostgreSQL (relational metadata)          MongoDB (document data)
─────────────────────────────────         ────────────────────────────
users                                     resume_data collection
  id, email, hashed_password                { first_name, last_name,
  first_name, last_name                       professional_title,
  plan (free/pro/team)                        summary, experience[],
  is_active, is_verified                      education[], skills[],
                                              projects[], contact{} }
resumes
  id, user_id, title                      portfolio_data collection
  template_id                               { resume_data{},
  mongo_doc_id → ObjectId                    customisation{},
  ats_score, is_public                       template_id }
  public_slug, pdf_url

portfolios
  id, user_id, title
  template_id
  mongo_doc_id → ObjectId
  is_published, subdomain

refresh_tokens
  id, user_id, token_hash
  expires_at, revoked
```

---

## Environment Variables

See `.env.example` for the full list. Key ones:

```env
DATABASE_URL=postgresql+psycopg2://user:pass@localhost/folio_db
MONGO_URI=mongodb://localhost:27017
ANTHROPIC_API_KEY=sk-ant-...
JWT_SECRET_KEY=<random 32+ char string>
SECRET_KEY=<another random 32+ char string>
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Deployment (Render / Railway)

1. Set all environment variables in your hosting dashboard
2. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Use managed PostgreSQL + MongoDB Atlas
4. Add Redis for rate limiting

---

## Frontend → Backend Connection

Update your frontend's API base URL:
```javascript
// In your frontend config
const API_BASE = "http://localhost:8000/api/v1"; // dev
const API_BASE = "https://your-backend.onrender.com/api/v1"; // prod
```

Store tokens in memory (not localStorage) for security:
```javascript
// After login
const { access_token, refresh_token } = await loginAPI(email, password);
// Use access_token in Authorization header for all requests
```