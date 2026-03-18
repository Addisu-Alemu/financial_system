# Loan Portfolio — Status Report App

Track customer loan status, arrears, and overdue days. Export to Excel or PDF.

---

## For someone who just wants to use the app

You only need **Docker Desktop** installed. Nothing else — no Python, no PostgreSQL.

### Step 1 — Install Docker Desktop
- Windows / Mac: https://www.docker.com/products/docker-desktop/
- Ubuntu Linux: `sudo apt install docker.io docker-compose-plugin`

### Step 2 — Unzip the project
Unzip the file you received. You will have a folder called `loan-app`.

### Step 3 — Start the app
Open a terminal (Command Prompt on Windows), go into the folder, and run:

```bash
cd loan-app
docker compose up
```

Wait about 30 seconds the first time — it downloads what it needs.
When you see `Application startup complete` the app is ready.

### Step 4 — Open the app
Open your browser and go to: **http://localhost**

That is it. All 421 customers are already loaded.

### Stopping the app
Press `Ctrl + C` in the terminal, then:
```bash
docker compose down
```
Your data is saved. Next time just run `docker compose up` again.

---

## For developers

### Project structure
```
loan-app/
├── backend/
│   ├── main.py           ← FastAPI routes (logging + error handling)
│   ├── database.py       ← Connection pool with retry logic
│   ├── requirements.txt  ← Pinned Python dependencies
│   ├── schema.sql        ← DB table + indexes
│   ├── seed.sql          ← 421 customers (auto-loaded by Docker)
│   ├── Dockerfile        ← Backend container
│   └── tests/
│       ├── conftest.py   ← Shared fixtures (mocked DB)
│       └── test_api.py   ← 17 tests covering all endpoints + edge cases
├── frontend/
│   └── index.html        ← UI: search, filter, sort, export Excel/PDF
├── nginx/
│   └── nginx.conf        ← Serves frontend, proxies /api/ to backend
├── .github/
│   └── workflows/
│       └── ci.yml        ← GitHub Actions: tests + docker build on every push
├── docker-compose.yml    ← Runs db + backend + frontend together
├── .env                  ← Credentials (never commit this file)
├── .gitignore
└── README.md
```

### Running without Docker (local development)
```bash
# Terminal 1 — backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Open frontend/index.html in your browser
# Change API_BASE = "http://localhost:8000" for local dev (no nginx)
```

### Running tests
```bash
cd backend
pytest tests/ -v
```

### Git setup (first time)
```bash
cd loan-app
git init
git add .
git commit -m "Initial production setup"
git remote add origin https://github.com/YOUR_USERNAME/loan-app.git
git push -u origin main
```
After that every `git push` automatically runs all tests via GitHub Actions.

### API reference
| Endpoint | Description |
|---|---|
| `GET /health` | Health check (used by Docker) |
| `GET /api/summary` | Portfolio totals |
| `GET /api/customers` | All customers |
| `GET /api/customers?search=abebe` | Search by name / account / phone |
| `GET /api/customers?status=ARREARS` | Filter by status |
| `GET /api/customers?sort_by=days_overdue&sort_dir=desc` | Sort |

Interactive docs (when running): http://localhost/docs

### Deploying to a server
1. Copy `loan-app/` to the server
2. Edit `.env` with server credentials
3. Run `docker compose up -d`
4. Open the server IP in a browser

### Production checklist
| Feature | Done |
|---|---|
| Structured logging (timestamps, levels, request info) | ✅ |
| Error handling — proper HTTP status codes, never crashes | ✅ |
| Health check endpoint | ✅ |
| Connection pool (reuses DB connections efficiently) | ✅ |
| DB retry on startup (handles Docker timing) | ✅ |
| 17 tests — all endpoints, filters, SQL injection blocked | ✅ |
| Docker — one command, works on any PC | ✅ |
| Data persistence — volume survives restarts | ✅ |
| CI/CD — GitHub Actions runs tests on every push | ✅ |
| nginx security headers | ✅ |
| Non-root container user | ✅ |
| Pinned dependency versions | ✅ |
| .gitignore — credentials never committed | ✅ |
