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

- Use the **Data Imports** page: download the CSV template, fill it, then upload. Or add products manually (form on Data Imports or “Add product” on Opportunities).

---

## What’s implemented

### Phase 1

- **Backend**: FastAPI, SQLite, SQLAlchemy models (products, research_data, opportunity_scores, cad_models, manufacturing_simulations, listings, imports, product_notes).
- **API**: Dashboard summary, list products (filter/sort), get product by ID/slug.
- **Seed data**: 12 demo products with research data and opportunity scores.
- **Frontend**: Dashboard, Opportunities table, Product Detail (overview, research, score breakdown).

### Phase 2

- **Scoring engine**: `app/services/scoring_service.py` computes ForgeFlow Opportunity Score (demand, competition, manufacturing, margin, differentiation) from research data. Weights configurable; defaults 30% demand, 20% competition, 20% manufacturing, 20% margin, 10% differentiation.
- **API**: `POST /api/products/{id}/score` to compute and save score; `POST /api/products/{id}/research` to add research data; full CRUD for products. Imports: `GET /api/imports/template`, `POST /api/imports/preview`, `POST /api/imports/upload`, `GET /api/imports`.
- **CSV import**: Parse and validate CSV (name, category, optional research columns), create products + research rows, log to `imports` table. Template download on Data Imports page.
- **Frontend**: Data Imports page (CSV upload, preview, template download, manual entry form, import history). Opportunities: “Add product” → Product Create form. Product Detail: “Score opportunity” button, “Add research data” form.

### Phase 3 (CAD)

- **CAD service** (`app/services/cad_service.py`): Template-based OpenSCAD code generation for **bracket**, **clip**, **holder**, **spacer**, **mount**, **tray**, **cable_organizer**. Each template accepts dimensions (width, height, thickness, hole_diameter, etc.). Saves `.scad` files under `data/scad/` and records paths + code in DB. **OpenSCAD CLI** integration: runs `openscad -o output.stl input.scad` for STL export (set `FORGEFLOW_OPENSCAD_PATH` if not on PATH).
- **API**: `GET /api/products/model-types`, `GET/POST /api/products/{id}/cad`, `GET /api/products/{id}/cad/{cad_id}`, `POST /api/products/{id}/cad/{cad_id}/export-stl`.
- **Frontend**: **CAD Generator** page (`/cad`): product selector, template type, parameter inputs (mm), “Generate & save”, generated code view, list of saved models per product, “Export STL” per model, activity log. Product Detail “Generate CAD” links to `/cad?product={slug}`.

### Phase 4 (Manufacturing + Listings)

- **Manufacturing simulation** (`app/services/simulation_service.py`): **Heuristic engine** estimates print time (min), material (g), filament cost, supports (yes/no), recommended orientation, and difficulty score (0–100) from part volume (from CAD parameters or default) and material/layer height/infill. Designed so a future **slicer CLI** (OrcaSlicer, Bambu Studio) can be plugged in without changing API or UI. **Warnings** for long print time, supports, large part, or high material cost.
- **API**: `GET/POST /api/products/{id}/simulations`, `GET /api/products/{id}/simulations/{sim_id}`.
- **Listing generation** (`app/services/listing_service.py`): **Template-based** marketplace content: title, short pitch, 3–5 bullet points, description, 10–15 tags, suggested price (from research or default), photo prompt, “why it could sell”, differentiation angle. AI-ready for future LLM swap.
- **API**: `GET/POST /api/products/{id}/listings`, `GET/PATCH /api/products/{id}/listings/{listing_id}`.
- **Frontend**: **Manufacturing Simulator** (`/simulator`): product + optional CAD model, material/layer height/infill/nozzle, “Run simulation”, result card + warnings, history. **Listing Studio** (`/listings`): product selector, “Generate listing”, view title/pitch/bullets/description/price/tags/photo prompt/why it could sell/differentiation, version switcher. Product Detail “Run simulation” and “Generate listing” link to these pages with `?product={slug}`.

### Phase 5 (Polish)

- **Error handling**: Reusable `ErrorBanner` with Retry/Dismiss; inline errors on forms; API failures show clear messages.
- **Loading states**: `LoadingSpinner` (spinner + message) on Dashboard, Opportunities, Product Detail, CAD, Simulator, Listing Studio, Data Imports.
- **Empty states**: Dashboard and Opportunities show friendly copy and primary action (e.g. “No products yet” → “Go to Data Imports” or “Add product”).
- **Toasts**: Success toasts for product create, CSV import, manual entry (auto-dismiss).
- **Product Detail**: CAD / Manufacturing / Listing sidebar cards link to the right tool when empty (“Generate CAD →”, etc.).

---

## What’s mocked vs live

- **Live**: Full pipeline: database, product/research CRUD, opportunity scoring, CSV import, dashboard, **CAD** (templates + SCAD save + optional OpenSCAD STL), **manufacturing simulation** (heuristic), **listing generation** (templates), all UI pages.
- **Optional / future**: OpenSCAD CLI (STL export). Slicer CLI (replace heuristic with real slicer). LLM provider (replace template listing with AI-generated copy).

---

## Environment variables (backend)

| Variable | Default | Description |
|----------|---------|-------------|
| `FORGEFLOW_DATABASE_URL` | `sqlite+aiosqlite:///./forgeflow.db` | Database URL (use Postgres URL in production). |
| `FORGEFLOW_OPENSCAD_PATH` | `openscad` | Path to OpenSCAD executable for STL export. |
| `FORGEFLOW_DEBUG` | `false` | Enable SQL echo and debug. |
| `FORGEFLOW_DEFAULT_MATERIAL_COST_PER_GRAM` | `0.02` | Used for simulation cost and scoring. |
| `FORGEFLOW_DEFAULT_PLATFORM_FEE_PERCENT` | `6.5` | Used in margin scoring. |
| `FORGEFLOW_DEFAULT_SHIPPING_ESTIMATE` | `4.0` | Used in margin scoring. |

Create a `.env` file in `backend/` to override (e.g. `FORGEFLOW_OPENSCAD_PATH=/usr/bin/openscad`).

---

## Troubleshooting

- **Dashboard / API shows nothing or errors**: Ensure the backend is running (`uvicorn app.main:app --reload` from `backend/`) and the frontend proxy targets `http://127.0.0.1:8000`. Run the seed script if the DB is empty: `python seeds/seed_data.py`.
- **“OpenSCAD not found” when exporting STL**: Install [OpenSCAD](https://openscad.org/) and add it to your PATH, or set `FORGEFLOW_OPENSCAD_PATH` in `backend/.env` to the full path to the executable. CAD generation and saving still work without OpenSCAD; only STL export is affected.
- **CSV import fails**: Ensure the file has `name` and `category` columns. Download the template from Data Imports and match the header names (case-insensitive, spaces normalized to underscores).
- **Product not found (404)**: The product may have been deleted, or the slug/ID in the URL is wrong. Use the Opportunities list to open products by name.

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

## Roadmap (post-MVP)

- Slicer CLI integration (OrcaSlicer / Bambu Studio) for real print-time and material estimates.
- LLM provider integration for AI-generated listing copy.
- Settings page: wire OpenSCAD path, material defaults, fee assumptions.
- Optional: user auth, team collaboration, cloud deploy.
