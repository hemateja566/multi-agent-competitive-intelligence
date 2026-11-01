# Multi-Agent Competitive Intelligence & Price Optimization System

An automated market analysis engine that monitors competitor offerings, audits dynamic pricing, verifies compliance, and generates predictive pricing proposals.

## Architecture

### Multi-Agent Flow
- **Scraper/Search Agent**: Gathers pricing and product metadata using web search tools (Tavily/Firecrawl).
- **Validation Agent**: Audits the scraped structured data against Pydantic schemas to ensure clean normalization.
- **Economics/Pricing Agent**: Evaluates margin limits and historical sales data stored in MySQL to propose revised prices.
- **Critic/Audit Agent**: Evaluates the proposed change against business safety constraints (e.g., "Margin cannot drop below 18%") before finalizing.

### Stack Integration
- **React**: Interactive price-adjustment dashboard with live market trend visualizations, agent disagreement logs, and batch price override controls.
- **Flask**: Manages agent execution schedules (via Celery Beat), provides authenticated REST APIs, and exposes WebSocket/SSE connections for live multi-agent debate feeds.
- **MySQL**: Stores catalog data, competitors' price history tables, margin constraint rules, and an immutable log of agent decision trails.

## Setup

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your MySQL connection details and API keys

# Initialize the database
python backend/init_db.py

# Start the Flask server
cd backend
python app.py

# Start the React development server
cd ../frontend
npm start
```