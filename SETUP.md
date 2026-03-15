# One-afternoon setup: full AI pipeline

ForgeFlow runs out of the box with templates and manual CAD parameters. To unlock the **full AI-driven pipeline** (Claude for CAD, LLM for listing copy), work through this checklist. SQLite is fine for local use; Postgres is only needed for cloud deploys.

| Step | What to do |
|------|------------|
| **1. App running** | Finish [Local setup](README.md#local-setup) in the README: backend + frontend + seed data. |
| **2. CAD (AI design)** | In `backend/.env` set **`FORGEFLOW_CAD_LLM_API_KEY`** to your **Anthropic** API key. CAD generation will use Claude to pick template + dimensions from product/category. Optionally set `FORGEFLOW_CAD_LLM_PROVIDER=anthropic` (this is the default). |
| **3. Listing (AI copy)** | In `backend/.env` set **`FORGEFLOW_LISTING_LLM_API_KEY`** and **`FORGEFLOW_LISTING_LLM_PROVIDER`** (e.g. `openai` or `anthropic`). Use a cheaper model: **`FORGEFLOW_LISTING_LLM_MODEL`** = `gpt-4o-mini` (OpenAI) or `claude-3-5-haiku` (Anthropic). Listing Studio will then generate title, bullets, description, and tags via the LLM instead of templates. |
| **4. OpenSCAD (STL export)** | Install [OpenSCAD](https://openscad.org/). If it's not on your PATH, set **`FORGEFLOW_OPENSCAD_PATH`** in `backend/.env` (e.g. Windows: `C:\Program Files\OpenSCAD\openscad.exe`). Required only for "Export STL" and "Download STL" from the CAD page. |
| **5. Postgres (optional)** | Only needed for **deploy** (e.g. Railway). For local use, the default SQLite DB at `backend/forgeflow.db` is enough. |

After step 2–4 you can: research products → score → **Generate CAD** (Claude) → run manufacturing sim → **Generate listing** (LLM) and use Export STL if OpenSCAD is configured.
