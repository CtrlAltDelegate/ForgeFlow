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

- **MVP**: SQLite. The database file is always created at `backend/forgeflow.db` (absolute path), so your imports and products persist no matter which folder you start the server from.
- Schema is created on first run via `init_db()`. To reset, delete `backend/forgeflow.db` and restart the API, then re-run the seed script.
- Override the location with `FORGEFLOW_DATABASE_URL` in `.env` if needed.

### Import file types (Data Imports)

- Use the **Data Imports** page: **CSV:** download the template, fill name/category and optional research columns, then upload. **PDF:** upload a PDF to create one product (name from filename, notes = extracted text). Or add products manually (form on Data Imports or “Add product” on Opportunities).

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
| `FORGEFLOW_DATABASE_URL` | *(absolute path to backend/forgeflow.db)* | Database URL. Default uses backend folder so data persists; override for Postgres in production. |
| `FORGEFLOW_OPENSCAD_PATH` | `openscad` | Path to OpenSCAD executable for STL export. |
| `FORGEFLOW_DEBUG` | `false` | Enable SQL echo and debug. |
| `FORGEFLOW_CORS_ORIGINS` | (includes localhost + Netlify) | Comma-separated origins for CORS. |
| `FORGEFLOW_DEFAULT_MATERIAL_COST_PER_GRAM` | `0.02` | Used for simulation cost and scoring. |
| `FORGEFLOW_DEFAULT_PLATFORM_FEE_PERCENT` | `6.5` | Used in margin scoring. |
| `FORGEFLOW_DEFAULT_SHIPPING_ESTIMATE` | `4.0` | Used in margin scoring. |
| `FORGEFLOW_LISTING_LLM_API_KEY` | *(empty)* | API key for listing/review LLM (optional). |
| `FORGEFLOW_LISTING_LLM_MODEL` | `gpt-4o-mini` | Model for listing/review (e.g. OpenAI). |
| `FORGEFLOW_LISTING_LLM_PROVIDER` | `openai` | Provider: `openai`, `anthropic`, etc. |
| `FORGEFLOW_CAD_LLM_API_KEY` | *(empty)* | API key for CAD-generation LLM (optional). |
| `FORGEFLOW_CAD_LLM_MODEL` | `gpt-4o` | Model for CAD/code generation. |
| `FORGEFLOW_CAD_LLM_PROVIDER` | `openai` | Provider for CAD phase. |

Create a `.env` file in `backend/` to override (e.g. `FORGEFLOW_OPENSCAD_PATH=/usr/bin/openscad`).

---

## LLM / API keys (optional)

ForgeFlow is designed to use **two LLM “phases”** with separate API keys and model choices:

1. **Listing / review (simpler LLM)**  
   Use a **faster, cheaper** model for:
   - Review summarization and listing copy (title, bullets, description, tags).
   - Optional: extracting structured product data from PDF or freeform text.

   **Suggestions:** OpenAI `gpt-4o-mini`, Anthropic `claude-3-haiku`, or Google `gemini-1.5-flash`. One API key (e.g. `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`) is enough; set `FORGEFLOW_LISTING_LLM_API_KEY` and `FORGEFLOW_LISTING_LLM_MODEL` (and provider if you add provider-specific code).

2. **CAD generation (more capable LLM)**  
   Use a **more capable** model for:
   - Turning product descriptions or specs into OpenSCAD code or template parameters.
   - Choosing template type (bracket, clip, holder, etc.) and dimensions from natural language.

   **Suggestions:** OpenAI `gpt-4o`, Anthropic `claude-3-5-sonnet`, or Google `gemini-1.5-pro`. Set `FORGEFLOW_CAD_LLM_API_KEY` and `FORGEFLOW_CAD_LLM_MODEL`. You can use the same provider as listing with a different model, or a different provider.

**Current behavior:** Without these keys set, listing stays **template-based** and CAD stays **template + manual parameters**. The config and wiring are in place so you can plug in calls to your chosen provider when ready (e.g. in `listing_service.py` and `cad_service.py`).

---

## Troubleshooting

- **Dashboard / API shows nothing or errors**: Ensure the backend is running (`uvicorn app.main:app --reload` from `backend/`) and the frontend proxy targets `http://127.0.0.1:8000`. Run the seed script if the DB is empty: `python seeds/seed_data.py`.
- **“OpenSCAD not found” when exporting STL**:
  - **Running locally (Windows):** Install [OpenSCAD](https://openscad.org/) and set `FORGEFLOW_OPENSCAD_PATH=C:\Program Files\OpenSCAD\openscad.exe` in `backend/.env`. Start the server from the `backend` folder so it loads `.env`.
  - **Running in a container (Docker / Render / Railway / etc.):** The container does not use your PC’s `.env` or Windows paths. Use the repo’s `backend/Dockerfile`, which installs OpenSCAD inside the image so STL export works. Set `FORGEFLOW_OPENSCAD_PATH=openscad` (or `/usr/bin/openscad`) in the **deployment** environment if your platform doesn’t pick it up.
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

- `VITE_API_URL` = your **Railway** backend URL (e.g. `https://your-app.up.railway.app`).

The frontend uses `VITE_API_URL` for API requests in production; local dev uses the proxy to your backend.

### Backend (Railway)

- **Railway** runs the API; Netlify’s frontend calls it via `VITE_API_URL`.
- **Root directory:** `backend`.
- **Deploy with Dockerfile (recommended):** Railway will detect `backend/Dockerfile`, which installs OpenSCAD and uses `run.sh` so the app listens on Railway’s `PORT`. Don’t set a custom **Start Command** in Railway so the Dockerfile `CMD` is used.
- If you don’t use the Dockerfile: Build `pip install -r requirements.txt`, Start **`./run.sh`** (or `sh run.sh`) so `PORT` is read from the environment. Using `--port $PORT` directly can pass the literal `$PORT` and fail.
- **Database:** Add a Postgres add-on. To avoid "password authentication failed" (stale DATABASE_URL), use **variable references for each credential** on the ForgeFlow service so the app builds the URL from current values:
  - ForgeFlow → **Variables** → add these (use **Add reference** and pick your Postgres service for each):
    - `FORGEFLOW_PG_HOST` → `${{Postgres.PGHOST}}`
    - `FORGEFLOW_PG_PORT` → `${{Postgres.PGPORT}}`
    - `FORGEFLOW_PG_USER` → `${{Postgres.PGUSER}}`
    - `FORGEFLOW_PG_PASSWORD` → `${{Postgres.PGPASSWORD}}`
    - `FORGEFLOW_PG_DATABASE` → `${{Postgres.PGDATABASE}}`
  - Replace `Postgres` with your Postgres service name if different. The app will build the Postgres URL from these; each is resolved at runtime so the password is always current.
  - Alternatively you can set `FORGEFLOW_DATABASE_URL` to the full URL (or `${{Postgres.DATABASE_URL}}`), but if that keeps failing with invalid password, use the five PG_* variables above.
- **CORS:** Add your Netlify frontend origin to `FORGEFLOW_CORS_ORIGINS` (e.g. `https://forgeflow-dashboard.netlify.app`) so the browser can call the API.

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
