# Stockroom | Full-stack Inventory

React interface backed by a transactional FastAPI and SQLAlchemy service. SQLite is the default, with optional PostgreSQL configuration. Supports item creation, inventory balances, reorder alerts and stock history. No authentication; local demonstration only.

```bash
pip install -r requirements.txt
uvicorn inventory:app --reload --port 8000
# In a second terminal:
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. API docs at http://localhost:8000/docs. Backend tests: python -m pytest -q. Optional PostgreSQL: install requirements-postgres.txt, set POSTGRES_PASSWORD locally, run docker compose up -d and set DATABASE_URL to a PostgreSQL SQLAlchemy connection string. Never commit credentials. PostgreSQL and frontend build require verification. Independent AI-assisted demonstration.
