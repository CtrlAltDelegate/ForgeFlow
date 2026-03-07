# ForgeFlow

**ForgeFlow** is an AI-assisted product research, CAD generation, and manufacturing simulation platform for discovering profitable **3D-printable products** before purchasing physical equipment.

The MVP simulates the “brain” of an AI-assisted micro-manufacturing business: research → scoring → CAD → simulation → listing.

---

## Local setup

### Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.11+ (for backend)
- **OpenSCAD** (optional, for Phase 3 CAD export)

### Backend

1. Create a virtual environment and install dependencies:

   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   ```

2. Run the API (from the `backend` directory):

   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

   The API will be at **http://127.0.0.1:8000**.  
   OpenAPI docs: **http://127.0.0.1:8000/docs**.

3. Seed demo data (12 products with research and opportunity scores):

   ```bash
   python seeds/seed_data.py
   ```

   From the `backend` directory. If the database already has products, the script skips seeding.

4. **OpenSCAD path** (optional): set `FORGEFLOW_OPENSCAD_PATH` or configure in Settings once that page is wired. Default is `openscad` on PATH.

### Frontend

1. Install and run:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. Open **http://localhost:5173**. The dev server proxies `/api` to the backend.

### Database

- **MVP**: SQLite. The file is created at `backend/forgeflow.db` when the API starts.
- Schema is created on first run via `init_db()`. To reset, delete `forgeflow.db` and restart the API, then re-run the seed script.

### CSV template (Data Imports)

- The **Data Imports** page and CSV template will be added in Phase 2. For now, use the seeded demo data or create products via the API.

---

## What’s implemented (Phase 1)

- **Backend**: FastAPI, SQLite, SQLAlchemy models (products, research_data, opportunity_scores, cad_models, manufacturing_simulations, listings, imports, product_notes).
- **API**: Dashboard summary, list products (filter/sort), get product by ID/slug.
- **Seed data**: 12 demo products across categories (cable organizers, vacuum adapters, pegboard mounts, desk accessories, gaming, appliance parts, etc.) with research data and opportunity scores.
- **Frontend**: Dark “mission control” dashboard with sidebar; Dashboard (metrics, pipeline stages, top opportunities, recent activity); Opportunities table (search, category, status, sort); Product Detail (overview, research, opportunity score breakdown, placeholders for CAD / simulation / listing).

---

## What’s mocked vs live

- **Live**: Database, product CRUD, dashboard aggregation, opportunity scores (stored from seed or future scoring engine).
- **Mocked / placeholder**: CAD generation, manufacturing simulation, listing generation, CSV import UI. These are scaffolded for later phases.

---

## Project structure

```
ForgeFlow/
├── backend/
│   ├── app/
│   │   ├── api/routes/     # API endpoints
│   │   ├── core/           # config, database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── main.py
│   ├── seeds/
│   │   └── seed_data.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── types/
│   │   └── App.tsx
│   └── package.json
└── README.md
```

---

## Deploy

### GitHub

1. Create a new repository on GitHub (see [New Repository](#new-repository-on-github) below).
2. Push this project to it (first time from your machine):

   ```bash
   git init
   git add .
   git commit -m "Initial commit: ForgeFlow Phase 1"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/ForgeFlow.git
   git push -u origin main
   ```

   Replace `YOUR_USERNAME` with your GitHub username (or org) and use the repo URL GitHub shows.

### Frontend (Netlify)

- **Build command:** `npm run build`  
- **Publish directory:** `frontend/dist`  
- **Base directory:** `frontend` (so Netlify runs `npm install` and `npm run build` inside `frontend`).

In Netlify **Site settings → Environment variables**, add:

- `VITE_API_URL` = your backend URL (e.g. `https://your-backend.onrender.com`).

In the frontend, use `VITE_API_URL` for API requests in production (and keep `/api` with proxy for local dev). The current proxy only works in dev; for production the app must call the real backend URL.

### Backend (e.g. Render or Railway)

- **Render**: New → Web Service → connect the same GitHub repo. Root directory: `backend`. Build: `pip install -r requirements.txt`. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Railway**: New project from repo, add a service, set root to `backend`, and use the same start command.
- Use a **Postgres** database add-on for production (Render/Railway provide one); change `database_url` in config to the provided URL. For MVP you can still use SQLite on a single instance, but it won’t persist across redeploys on most hosts.

---

## New repository on GitHub

1. **Sign in** to [github.com](https://github.com).
2. Click the **+** in the top-right → **New repository**.
3. **Repository name:** `ForgeFlow` (or e.g. `forgeflow`).
4. **Description (optional):** e.g. *AI-assisted product research & CAD for 3D-printable products*.
5. Choose **Public** (or Private if you prefer).
6. **Do not** check “Add a README”, “Add .gitignore”, or “Choose a license” — you already have a README and .gitignore in this project.
7. Click **Create repository**.
8. On the new repo page, GitHub will show **“…or push an existing repository from the command line.”** Use those commands (they look like the block in [Deploy → GitHub](#github) above). Run them from your project root (`ForgeFlow`) on your machine.

If you use SSH instead of HTTPS, the remote URL will be `git@github.com:YOUR_USERNAME/ForgeFlow.git`; use that in place of the `https://...` URL when you run `git remote add origin ...`.

---

## Next phases (from spec)

- **Phase 2**: Scoring engine, import flow (CSV + manual), CRUD for products/research.
- **Phase 3**: CAD generation service, save `.scad` files, optional OpenSCAD CLI export.
- **Phase 4**: Manufacturing simulation, listing generation.
- **Phase 5**: Polish UI, error handling, README and sample data refinements.
