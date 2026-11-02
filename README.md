# Multi-Agent Competitive Intelligence & Price Optimization System

An automated market analysis engine that monitors competitor offerings, audits dynamic pricing, verifies compliance, and generates predictive pricing proposals.

---

## 📖 Overview

This system implements a **four‑agent pipeline** that continuously scrapes market data, validates structured outputs, computes margin‑aware price proposals, and enforces business constraints before any price change is accepted.

The stack is divided into:

| Layer | Technology | Role |
|------|------------|------|
| **Backend** | Flask + APScheduler + MySQL | Hosts the agents, schedules runs, provides REST & WebSocket endpoints |
| **Agents** (Python) | `scraper`, `validator`, `pricing`, `critic` | Multi‑agent data flow (scrape → validate → propose → audit) |
| **Frontend** | React (Vite) + Nginx | Dashboard visualising live agent debates, price proposals, and audit logs |
| **Database** | MySQL | Stores catalog, competitor price history, margin rules, and an immutable decision log |

---

## 🏗️ Architecture

### Multi‑Agent Flow

1. **Scraper / Search Agent** – Uses web‑search tools (Tavily/Firecrawl) to gather pricing and product metadata.
2. **Validation Agent** – Normalises scraped data against **Pydantic** schemas; ensures clean, typed structures.
3. **Economics / Pricing Agent** – Queries MySQL for historical sales and margin data; proposes a revised price that respects target margins.
4. **Critic / Audit Agent** – Evaluates the proposal against safety constraints (e.g., “Margin cannot drop below 18%”). If a constraint is violated, the proposal is **revised** or **rejected**.

### Stack Integration

- **Flask** – Manages agent execution schedules (via Celery Beat), provides authenticated REST APIs, and exposes WebSocket/SSE connections for live multi‑agent debate feeds.
- **React** – Interactive dashboard with live market‑trend visualisations, agent‑disagreement logs, and batch price‑override controls.
- **MySQL** – Stores catalog data, competitors' price‑history tables, margin‑constraint rules, and an immutable log of agent decision trails.

---

## 🚀 Quick Start

### Option 1 – All‑in‑One with Docker (recommended)

```bash
# 1️⃣ Clone the repo
git clone https://github.com/hemateja566/multi-agent-competitive-intelligence.git
cd multi-agent-competitive-intelligence

# 2️⃣ (Optional) create a .env file for Docker secrets
cat > .env <<'EOF'
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_USER=appuser
MYSQL_PASSWORD=apppassword
TAVILY_API_KEY=your_tavily_key
FIRECRAWL_API_KEY=your_firecrawl_key
FLASK_ENV=development
EOF

# 3️⃣ Bring up the stack (MySQL + Flask backend + React UI)
docker compose up --build -d
```

- **MySQL** is exposed on `localhost:3306` (service name `db` inside the network).
- **Flask API** runs on `http://localhost:5000`.
- **React UI** is available at `http://localhost:80`.

#### Verify

```bash
curl http://localhost:5000/api/health
# → {"status":"ok","message":"Price Optimization System API"}

curl http://localhost:5000/api/margin/constraints
# → [{"id":1,"min_margin_percent":18,"description":"Margin cannot drop below 18%"}, …]
```

Open your browser at `http://localhost:80` to see the React dashboard.

---

### Option 2 – Local (non‑Docker) Development

#### Prerequisites

- Python 3.11+ 
- Node.js 20+ (for the React front‑end)
- MySQL 8.0+ server running locally (or via Docker `mysql` container)

#### 1️⃣ Install Backend Dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### 2️⃣ Create & Populate the Database

```sql
CREATE DATABASE price_optimization;
CREATE USER 'appuser'@'%' IDENTIFIED BY 'apppassword';
GRANT ALL PRIVILEGES ON price_optimization.* TO 'appuser'@'%';
FLUSH PRIVILEGES;

-- then run the schema script (see SQL section below)
```

#### 3️⃣ Configure Environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your MySQL host/password and API keys
```

#### 4️⃣ Run the Flask Server

```bash
cd backend
python app.py   # runs on http://127.0.0.1:5000
```

#### 5️⃣ Install & Run the Frontend

```bash
cd ../frontend
npm install
npm run dev     # Vite dev server, usually http://localhost:5173
```

#### 6️⃣ Test the API

```bash
curl http://127.0.0.1:5000/api/health
curl http://127.0.0.1:5000/api/margin/constraints
```

---

## 📦 API Reference (Flask)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | `GET` | Basic health‑check; returns `{"status":"ok"}`. |
| `/api/agents/status` | `GET` | Returns current status of the four agents (`idle`/`running`). |
| `/api/agents/run` | `POST` | Trigger the full 4‑agent pipeline (optionally specify `agent` = `scraper|validation|pricing|critic`). |
| `/api/pricing/proposal` | `GET` | Returns a predictive pricing proposal for a given ASIN (query `?asin=B0XYZ123`). |
| `/api/margin/constraints` | `GET` | Lists all active margin‑constraint rules stored in MySQL. |
| `/api/logs/decision` | `GET` | (Future) Returns the `agent_decision_log` table for audit purposes. |

*All responses are JSON. 4xx/5xx errors also return JSON with an `error` field.*

---

## 🛠️ Adding / Running Agents Manually

The repo ships four Python modules under `agents/`:

| Module | Key Function |
|--------|--------------|
| `scraper.py` | `scrape_and_validate(query)` – returns list of `ProductMetadata` Pydantic objects. |
| `validator.py` | `validate_product_list(dicts)` – validates/normalises raw dicts. |
| `pricing.py` | `compute_recommended_price(asin, current_price)` – uses MySQL history to suggest a price. |
| `critic.py` | `evaluate_proposal(proposal)` – returns `{"verdict":"APPROVE"|"REJECT"|"REVISE", "violations":[…]}`. |

You can invoke them from the command line or from the `/api/agents/run` endpoint, which simply dispatches the requested agent name.

---

## 🐳 Docker Development Details

- **`Dockerfile.backend`** – builds a Python‑slim image with Flask, MySQL driver, and the agents package.
- **`Dockerfile.frontend`** – multi‑stage build: `node:20-alpine` compiles the React app, then `nginx:alpine` serves the static `dist`.
- **`docker-compose.yml`** orchestrates three services (`db`, `backend`, `frontend`) and creates a MySQL volume `db_data` for persistence.

To rebuild or restart:

```bash
docker compose down -v          # removes anonymous volumes
docker compose up --build -d    # fresh start
```

---

## 🗄️ SQL Schema (run once)

The following script creates the tables the app expects and seeds a default **18 % margin floor**. Execute it against your MySQL instance (or let Docker Compose run it automatically via `/docker-entrypoint-initdb.d/init_db.sql`).

```sql
CREATE DATABASE IF NOT EXISTS price_optimization;
USE price_optimization;

-- products catalog
CREATE TABLE IF NOT EXISTS products (
    asin VARCHAR(20) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    price DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    retailer VARCHAR(100) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    last_scraped DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- competitor price history
CREATE TABLE IF NOT EXISTS competitor_price_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    asin VARCHAR(20) NOT NULL,
    price DECIMAL(12,2) NOT NULL,
    date_recorded DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    margin_percent DECIMAL(5,2),
    INDEX idx_asin_date (asin, date_recorded DESC)
);

-- margin constraints (business rules)
CREATE TABLE IF NOT EXISTS margin_constraints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    min_margin_percent DECIMAL(5,2) NOT NULL,
    description VARCHAR(255) NOT NULL
);

-- immutable agent decision log
CREATE TABLE IF NOT EXISTS agent_decision_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    asin VARCHAR(20) NOT NULL,
    requested_price DECIMAL(12,2) NOT NULL,
    approved_price DECIMAL(12,2),
    margin_percent DECIMAL(5,2),
    verdict VARCHAR(20) NOT NULL,
    decided_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- default rule: margin cannot drop below 18%
INSERT IGNORE INTO margin_constraints (min_margin_percent, description)
VALUES (18.00, 'Margin cannot drop below 18%');
```

---

## 🤝 Contributing

1. **Fork** the repository and create a feature branch (`git checkout -b feature/xxx`).
2. Make your changes, adhering to the existing code style (PEP 8 for Python, functional components + hooks for React).
3. Add or update tests as appropriate.
4. Commit (`git commit -m "Add …"`), push (`git push origin feature/xxx`), and open a Pull Request.
5. Ensure the CI (GitHub Actions) passes – a basic workflow is included in `.github/workflows/ci.yml` (you can extend it).

---

## 📜 License

This project is licensed under the **MIT License**. See the `LICENSE` file for full text.

---

## 📬 Contact / Issues

- **GitHub Issues**: use the repository’s issue tracker for bugs or feature requests.
- **Discussions**: ask questions or share use‑cases in the Discussions tab.
- **Email**: (optional) add your preferred contact if you wish.

---

*Happy pricing! 🎯*