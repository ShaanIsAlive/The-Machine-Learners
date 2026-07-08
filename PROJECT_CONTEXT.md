# PROJECT_CONTEXT.md


## How to use this document

- Current pipeline architecture, scripts, and commands
- Model selection, training results, and evaluation metrics
- API routes and frontend structure
- Data layout and file naming conventions
- Known issues, technical debt, and next actions

Use it to continue development, debug issues, update documentation, and make the project presentation-ready.

---

## Latest verified status

> **All data below was built from the live code, current data artifacts, and current configs on 2026-07-06. No older context files were trusted over current repo state.**

| Item                      | Current value                                                                                                            |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Project goal**          | Monthly urban flood vulnerability forecasting for Indian cities using public earth observation and environmental signals |
| **Output type**           | Relative vulnerability scores (0–1), not flood water depth                                                               |
| **Cities covered**        | Bengaluru, Hyderabad, Mumbai, Pune                                                                                       |
| **Date range**            | 2020-01 to 2024-12 (60 months per city)                                                                                  |
| **Selected model**        | `hist_gbrt` — `HistGradientBoostingRegressor` (scikit-learn)                                                             |
| **Selected model config** | `max_depth=12`, `learning_rate=0.03`, `max_iter=900`, `random_state=42`                                                  |
| **Baseline model**        | `Ridge(alpha=1.0)`                                                                                                       |

### Current model metrics (from `data/results/training_metrics.json`)

| Metric                        | Baseline (Ridge) | Temporal (HistGBRT) |
| ----------------------------- | ---------------- | ------------------- |
| MAE (test)                    | 0.1935           | 0.1053              |
| R² (test)                     | 0.3665           | 0.6797              |
| MAE improvement over baseline | —                | 0.0882              |
| R² improvement over baseline  | —                | 0.3133              |
| Validation MAE (selected)     | —                | 0.1395              |

### Current chronological split (from `training_metrics.json`)

| Partition  | Period             |
| ---------- | ------------------ |
| Train      | up to 2022-11      |
| Validation | 2022-12 to 2023-11 |
| Test       | 2023-12 to 2024-11 |

### Current evaluation metrics (from `data/results/evaluation.json`)

| Metric                        | Value  |
| ----------------------------- | ------ |
| Spearman rank correlation     | 0.3523 |
| High vs low vulnerability gap | 0.5728 |
| High vulnerability mean       | 0.6153 |
| Low vulnerability mean        | 0.0426 |
| Months evaluated              | 56     |

### Current feature importance

`data/results/feature_importance.json` is empty (`[]`). `training_metrics.json` also shows `"top_feature_importance": []`. This is because `HistGradientBoostingRegressor` does not expose a `feature_importances_` attribute by default in all scikit-learn versions (the code checks `hasattr(temporal_model, "feature_importances_")`).

### Current dataset files in `data/features/`

| File                                     | Size                                             |
| ---------------------------------------- | ------------------------------------------------ |
| `flood_dataset.parquet`                  | ~56 KB (single-city, Bengaluru only)             |
| `flood_dataset_multicity.parquet`        | ~254 KB (4-city combined, **used for training**) |
| `flood_dataset_multicity_backup.parquet` | ~193 KB (older backup)                           |

### Current result files in `data/results/`

| File                           | Description                               |
| ------------------------------ | ----------------------------------------- |
| `training_metrics.json`        | Model selection and training metrics      |
| `evaluation.json`              | Post-inference evaluation metrics         |
| `vulnerability_scores.parquet` | Scored vulnerability output (~158 KB)     |
| `feature_importance.json`      | Empty (`[]`) — see note above             |
| `models/baseline_model.joblib` | Trained Ridge baseline (~1 KB)            |
| `models/temporal_model.joblib` | Trained HistGBRT temporal model (~1.9 MB) |

### Current API routes (from `src/api/app.py`)

| Method | Route                       | Description                                                |
| ------ | --------------------------- | ---------------------------------------------------------- |
| GET    | `/vulnerability/latest`     | Latest-month tile scores, `?limit=` (default 200)          |
| GET    | `/vulnerability/by_zone`    | Zone-binned means, `?year_month=&bins_lat=&bins_lon=`      |
| GET    | `/vulnerability/timeseries` | Monthly average vulnerability trend                        |
| GET    | `/metadata`                 | Dataset coverage, months, sources, training + eval metrics |

### Current runnable scripts in `scripts/`

| Script                 | Purpose                                |
| ---------------------- | -------------------------------------- |
| `run_ingestion.py`     | Fetch raw data from APIs               |
| `run_preprocessing.py` | Convert raw data to processed parquets |
| `run_feature_build.py` | Build model-ready dataset              |
| `run_training.py`      | Train baseline + temporal models       |
| `run_inference.py`     | Generate vulnerability scores          |
| `run_evaluation.py`    | Compute evaluation metrics             |
| `run_api.py`           | Start FastAPI server on port 8000      |
| `run_frontend.py`      | Launch Streamlit dashboard             |

### Current environment variables required

| Variable             | Purpose                                                                |
| -------------------- | ---------------------------------------------------------------------- |
| `CDS_API_KEY`        | Climate Data Store API key                                             |
| `CDSE_CLIENT_ID`     | Copernicus Data Space Ecosystem client ID                              |
| `CDSE_CLIENT_SECRET` | Copernicus Data Space Ecosystem client secret                          |
| `GEE_PROJECT_ID`     | Google Earth Engine project ID                                         |
| `FLOOD_API_BASE`     | (optional, frontend only) API URL, defaults to `http://127.0.0.1:8000` |

### Current known blockers and issues

1. **Feature importance is empty.** `HistGradientBoostingRegressor` in the installed scikit-learn version does not expose `feature_importances_`, so the importance JSON is `[]`.
2. **`mkdocs.yml` site_name says "Bengaluru"** — should be updated to reflect multi-city scope.
3. **Commented-out code in `src/inference/pipeline.py`** (lines 31–40) — dead code that should be removed.
4. **`bengaluru_2020_2024_operational.json`** — special config with most sources disabled; unclear whether it is still used or legacy.

---

## Source of truth priority

When resolving conflicting information, use this priority:

1. **Live code** in `src/` and `scripts/` — highest priority
2. **Current files** in `data/results/` and `data/features/` — actual training outputs
3. **Current `README.md`** — project overview and quick start
4. **Current `docs/` folder** — developer documentation
5. **Older generated context files** (e.g., previous `PROJECT_CONTEXT.md`) — background only, do not trust over items 1–4

---

## Project summary

**Problem:** Urban flood events in Indian cities cause significant damage. Decision-makers lack forward-looking, data-driven tools to prioritize drainage intervention, resource allocation, and preparedness actions before monsoon seasons.

**Solution:** A monthly vulnerability forecasting system that ingests public satellite imagery (Sentinel-1, Sentinel-2), climate reanalysis (ERA5 via Open-Meteo), terrain elevation (Copernicus DEM), built-up surface data (GHSL), population exposure (WorldPop), and road networks (OSM). It produces per-tile relative vulnerability scores for four Indian cities over a 5-year period.

**Cities:** Bengaluru, Hyderabad, Mumbai, Pune

**Date range:** January 2020 – December 2024

**Output:** Relative vulnerability scores (0 to 1) per spatial tile per month, **not** flood depth or inundation maps.

**Intended users:** Urban planners, municipal flood preparedness teams, disaster management agencies.

**What it does:**

- Ingests multi-source environmental data monthly
- Generates flood stress features per tile per month
- Trains a temporal regression model with lagged features
- Produces scored vulnerability outputs
- Exposes results through a REST API and Streamlit decision dashboard

**What it does NOT do:**

- Predict exact flood water depth or inundation extent
- Perform real-time flood detection
- Serve as an emergency alerting system

---

## Repository structure

```
The-Machine-Learners/
├── config/
│   ├── bengaluru_2020_2024.json
│   ├── bengaluru_2020_2024_operational.json
│   ├── hyderabad_2020_2024.json
│   ├── mumbai_2020_2024.json
│   └── pune_2020_2024.json
├── src/
│   ├── __init__.py
│   ├── common/
│   │   ├── settings.py          # AppSettings, env loading
│   │   └── time_utils.py        # MonthWindow iterator
│   ├── ingestion/
│   │   ├── adapters.py          # Source-specific fetch functions
│   │   ├── cdse_client.py       # Copernicus Data Space auth & search
│   │   ├── config.py            # IngestionConfig dataclass
│   │   └── pipeline.py          # IngestionPipeline orchestrator
│   ├── preprocessing/
│   │   └── pipeline.py          # PreprocessingPipeline (raw → processed)
│   ├── features/
│   │   └── dataset_builder.py   # FeatureBuilder (processed → dataset)
│   ├── models/
│   │   └── temporal.py          # TemporalTrainer (model training logic)
│   ├── training/
│   │   └── pipeline.py          # TrainingPipeline (orchestrator)
│   ├── inference/
│   │   └── pipeline.py          # InferencePipeline (scoring)
│   ├── evaluation/
│   │   └── pipeline.py          # EvaluationPipeline (metrics)
│   ├── api/
│   │   └── app.py               # FastAPI application
│   └── frontend/
│       └── app.py               # Streamlit dashboard
├── scripts/
│   ├── run_ingestion.py
│   ├── run_preprocessing.py
│   ├── run_feature_build.py
│   ├── run_training.py
│   ├── run_inference.py
│   ├── run_evaluation.py
│   ├── run_api.py
│   └── run_frontend.py
├── data/
│   ├── raw/                     # Per-city, per-source, per-month
│   │   ├── bengaluru/           # dem/, era5/, ghsl/, osm_roads/, sentinel_1/, sentinel_2/, worldpop/
│   │   ├── hyderabad/
│   │   ├── mumbai/
│   │   └── pune/
│   ├── processed/               # Per-city monthly parquets (YYYY_MM.parquet)
│   │   ├── bengaluru/ (60 files)
│   │   ├── hyderabad/ (60 files)
│   │   ├── mumbai/ (60 files)
│   │   └── pune/ (60 files)
│   ├── features/
│   │   ├── flood_dataset.parquet
│   │   ├── flood_dataset_multicity.parquet
│   │   └── flood_dataset_multicity_backup.parquet
│   └── results/
│       ├── evaluation.json
│       ├── feature_importance.json
│       ├── training_metrics.json
│       ├── vulnerability_scores.parquet
│       └── models/
│           ├── baseline_model.joblib
│           └── temporal_model.joblib
├── docs/                        # MkDocs documentation pages
│   ├── index.md
│   ├── architecture.md
│   ├── data-ingestion.md
│   ├── preprocessing-features.md
│   ├── modeling.md
│   ├── inference-scoring.md
│   ├── api.md
│   ├── ui.md
│   ├── operations.md
│   ├── troubleshooting.md
│   └── onboarding.md
├── .env / .env.example
├── .gitignore
├── mkdocs.yml
├── requirements.txt
└── README.md
```

---

## Pipeline architecture

### 1. Ingestion

**Script:** `python scripts/run_ingestion.py`  
**Code:** `src/ingestion/pipeline.py`, `src/ingestion/adapters.py`, `src/ingestion/cdse_client.py`  
**Input:** City config JSON from `config/`  
**Output:** Raw files per source per month in `data/raw/{city}/{source}/{year}/{month}/`

**What it does:**

- Iterates month windows from config date range
- For each enabled source, fetches data from external APIs:
  - **Sentinel-1/2:** CDSE OData catalog search → product list JSON
  - **ERA5:** Open-Meteo archive API → daily rainfall JSON
  - **DEM:** Copernicus DEM GLO-30 tiles → `.tif` rasters
  - **OSM Roads:** Overpass API → road network JSON
  - **WorldPop:** Reference metadata JSON (pointer to global raster)
  - **GHSL:** JRC GHSL built-up surface ZIP download
- Writes per-month `manifest.json` files for tracking
- Supports `--live-fetch` flag for Sentinel CDSE API calls
- Skips already-downloaded months (manifest check)
- Static sources (DEM, roads, worldpop, GHSL) are cached after first fetch

### 2. Preprocessing

**Script:** `python scripts/run_preprocessing.py`  
**Code:** `src/preprocessing/pipeline.py`  
**Input:** Raw data in `data/raw/{city}/`, city config JSON  
**Output:** Monthly processed parquets `data/processed/{city}/{YYYY_MM}.parquet`

**What it does:**

- Generates a fixed 64-tile (8×8) spatial grid for each city based on config bounding box
- For each month, computes five flood stress features per tile:
  - `sar_water_persistence` — derived from Sentinel-1/2 product counts
  - `rainfall_accumulation` — from ERA5 daily precipitation sum
  - `low_lying_score` — from DEM raster (fraction of tile area below city median elevation), with legacy fallback
  - `impervious_change_rate` — from OSM road density proxy, scaled by year
  - `population_exposure` — longitude-based spatial proxy
- Outputs one parquet per city per month

### 3. Feature build

**Script:** `python scripts/run_feature_build.py`  
**Code:** `src/features/dataset_builder.py`  
**Input:** Processed parquets in `data/processed/{city}/`  
**Output:** `data/features/flood_dataset.parquet` (single city) or `data/features/flood_dataset_multicity.parquet` (multi-city)

**What it does:**

- Concatenates all processed monthly parquets for selected cities
- Adds `city` column if missing
- Adds `time_window` and `imagery_reference` columns
- Computes threshold-based `target_flood_risk` label:
  - 0.0 for low risk
  - 0.4 if either (low_lying_score > city median) OR (rainfall > city 75th percentile)
  - 1.0 if both conditions met
- Feature columns: `sar_water_persistence`, `rainfall_accumulation`, `low_lying_score`, `impervious_change_rate`, `population_exposure`

### 4. Training

**Script:** `python scripts/run_training.py`  
**Code:** `src/training/pipeline.py`, `src/models/temporal.py`  
**Input:** `data/features/flood_dataset_multicity.parquet` (preferred) or `flood_dataset.parquet`  
**Output:** `data/results/models/*.joblib`, `data/results/training_metrics.json`, `data/results/feature_importance.json`

**What it does:**

- Adds temporal lag features (lag1, lag2, lag3, roll3) for each of the 5 base features → 25 temporal features total
- Target: `target_next_month` (shifted `target_flood_risk`)
- Chronological train/val/test split (oldest → train, middle 12 months → val, last 12 months → test)
- Trains Ridge baseline on raw features (train+val → test)
- Trains candidates across 3 model families × 2 configs each:
  - RandomForest (400 trees / 700 trees)
  - ExtraTrees (600 trees / 900 trees)
  - HistGradientBoosting (depth 8 / depth 12)
- Selects best by validation MAE
- Re-trains selected model on train+val, evaluates on test
- Saves both baseline and temporal models as joblib

### 5. Inference

**Script:** `python scripts/run_inference.py`  
**Code:** `src/inference/pipeline.py`  
**Input:** Feature dataset + trained model (`temporal_model.joblib`)  
**Output:** `data/results/vulnerability_scores.parquet`

**What it does:**

- Loads dataset and builds inference frame with lag/roll features
- Loads trained temporal model
- Predicts raw scores, then min-max normalizes to [0, 1]
- Adds `vulnerability_rank` (per city+month if multi-city)
- Preserves city, tile_id, year, month, year_month, lat, lon columns

### 6. Evaluation

**Script:** `python scripts/run_evaluation.py`  
**Code:** `src/evaluation/pipeline.py`  
**Input:** `data/results/vulnerability_scores.parquet`  
**Output:** `data/results/evaluation.json`

**What it does:**

- Computes monthly average vulnerability score
- Compares against seasonal historical event proxy (monsoon months scored higher)
- Outputs Spearman rank correlation between scores and historical proxy
- Computes high vs low vulnerability gap (Q80 mean − Q20 mean)

### 7. API

**Script:** `python scripts/run_api.py`  
**Code:** `src/api/app.py`  
**Input:** `data/results/vulnerability_scores.parquet`, `evaluation.json`, `training_metrics.json`  
**Output:** REST JSON responses on port 8000

### 8. Frontend

**Script:** `python scripts/run_frontend.py`  
**Code:** `src/frontend/app.py`  
**Input:** API endpoints via `FLOOD_API_BASE` env var  
**Output:** Streamlit web dashboard

**What it does:**

- City selector (Bengaluru, Hyderabad, Mumbai, Pune)
- Executive flood risk snapshot with KPIs
- Vulnerability map (latest month)
- Zone-level priority table with Google Maps links
- Hotspot bar chart and risk tier mix
- Population impact panel
- Seasonal preparedness trend line chart
- Preventive action engine with mitigation suggestions
- Rainfall scenario simulator
- Executive narrative summary
- Project details tab with model quality explanation

---

## Current scripts and commands

### `run_ingestion.py`

**Purpose:** Fetch raw data from external APIs.

**Flags:**

- `--city {bengaluru,hyderabad,mumbai,pune}` — city shortcut (repeatable)
- `--config <path>` — explicit config JSON path (repeatable)
- `--all-default-cities` — run for all 4 cities
- `--live-fetch` — enable live CDSE API calls for Sentinel sources

**Default:** Bengaluru only if no flags given.

```bash
# Single city
python scripts/run_ingestion.py --city bengaluru

# All cities
python scripts/run_ingestion.py --all-default-cities

# With live Sentinel API
python scripts/run_ingestion.py --city bengaluru --live-fetch
```

### `run_preprocessing.py`

**Purpose:** Convert raw data to processed monthly parquets.

**Flags:**

- `--city {bengaluru,hyderabad,mumbai,pune}` (repeatable)
- `--config <path>` (repeatable)
- `--all-default-cities`

**Default:** Bengaluru only.

```bash
python scripts/run_preprocessing.py --all-default-cities
```

### `run_feature_build.py`

**Purpose:** Build model-ready dataset from processed parquets.

**Flags:**

- `--city {bengaluru,hyderabad,mumbai,pune}` (repeatable)
- `--all-default-cities` — builds ONE combined multi-city dataset

**Default:** Bengaluru only (single-city dataset).

```bash
# Multi-city (recommended)
python scripts/run_feature_build.py --all-default-cities

# Single city
python scripts/run_feature_build.py --city bengaluru
```

### `run_training.py`

**Purpose:** Train baseline + temporal models.  
**Flags:** None. Auto-selects multi-city dataset if available.

```bash
python scripts/run_training.py
```

### `run_inference.py`

**Purpose:** Generate vulnerability scores using trained model.  
**Flags:** None.

```bash
python scripts/run_inference.py
```

### `run_evaluation.py`

**Purpose:** Compute evaluation metrics from scored output.  
**Flags:** None.

```bash
python scripts/run_evaluation.py
```

### `run_api.py`

**Purpose:** Start FastAPI server.  
**Flags:** None. Runs on `0.0.0.0:8000`.

```bash
python scripts/run_api.py
```

### `run_frontend.py`

**Purpose:** Launch Streamlit dashboard.  
**Flags:** None.

```bash
python scripts/run_frontend.py
```

---

## Current model and evaluation

### Baseline model

- **Algorithm:** Ridge regression (`alpha=1.0`)
- **Features:** 5 raw features only
- **Test MAE:** 0.1935
- **Test R²:** 0.3665

### Selected temporal model

- **Algorithm:** `HistGradientBoostingRegressor` (scikit-learn)
- **Selection method:** Best validation MAE across 6 candidate models (3 families × 2 configs)
- **Features:** 5 base + 20 temporal (lag1, lag2, lag3, roll3 for each) = 25 features
- **Key hyperparameters:** `max_depth=12`, `learning_rate=0.03`, `max_iter=900`
- **Test MAE:** 0.1053 (45.6% improvement over baseline)
- **Test R²:** 0.6797 (0.3133 improvement over baseline)
- **Validation MAE:** 0.1395

### Evaluation

- **Spearman rank correlation:** 0.3523 — moderate positive correlation between predicted vulnerability and monsoon seasonality
- **High vs low gap:** 0.5728 — strong separation between high-risk and low-risk zones
- **Months evaluated:** 56

### Feature importance

Empty (`[]`) in current outputs. The `HistGradientBoostingRegressor` does not expose `feature_importances_` under the current scikit-learn version/configuration. This is a known gap.

### Training/validation/test split

Chronological (not random):

- Train: all months before 2022-12
- Validation: 2022-12 through 2023-11
- Test: 2023-12 through 2024-11

---

## Data and storage layout

### Raw data (`data/raw/`)

```
data/raw/
├── bengaluru/
│   ├── dem/         → DEM .tif rasters per month (copied from first fetch)
│   ├── era5/        → rainfall_daily.json per month
│   ├── ghsl/        → GHSL built-up ZIP per month
│   ├── osm_roads/   → roads_overpass.json per month
│   ├── sentinel_1/  → products.json per month
│   ├── sentinel_2/  → products.json per month
│   └── worldpop/    → worldpop_metadata.json per month
├── hyderabad/       → same structure
├── mumbai/          → same structure
└── pune/            → same structure
```

Each source within each city has subdirectories: `{year}/{month:02d}/` containing source-specific files and `manifest.json`.

Additionally, `data/raw/` contains top-level source directories (`dem/`, `era5/`, `ghsl/`, `osm_roads/`, `sentinel_1/`, `sentinel_2/`, `worldpop/`) which appear to be older per-source directories not scoped to a city.

### Processed data (`data/processed/`)

```
data/processed/
├── bengaluru/ → 60 files (2020_01.parquet through 2024_12.parquet)
├── hyderabad/ → 60 files
├── mumbai/    → 60 files
└── pune/      → 60 files
```

Each parquet contains 64 rows (one per tile) with columns: `tile_id`, `lon`, `lat`, `city`, `year`, `month`, `year_month`, `sar_water_persistence`, `rainfall_accumulation`, `low_lying_score`, `impervious_change_rate`, `population_exposure`.

### Features data (`data/features/`)

| File                                     | Description                                             |
| ---------------------------------------- | ------------------------------------------------------- |
| `flood_dataset.parquet`                  | Single-city dataset (Bengaluru, ~57 KB)                 |
| `flood_dataset_multicity.parquet`        | 4-city combined dataset (~254 KB, **used by training**) |
| `flood_dataset_multicity_backup.parquet` | Older backup (~193 KB)                                  |

### Results data (`data/results/`)

| File                           | Description                                       |
| ------------------------------ | ------------------------------------------------- |
| `training_metrics.json`        | Training/validation/test metrics and model config |
| `evaluation.json`              | Post-inference evaluation metrics                 |
| `vulnerability_scores.parquet` | Final scored output (~158 KB)                     |
| `feature_importance.json`      | Feature importances (currently empty)             |
| `models/baseline_model.joblib` | Ridge baseline model                              |
| `models/temporal_model.joblib` | HistGBRT temporal model (~1.9 MB)                 |

---

## API and frontend

### FastAPI routes (from `src/api/app.py`)

```python
@app.get("/vulnerability/latest")
# Params: limit: int = Query(default=200, ge=1, le=10000)
# Returns: { year_month, count, rows: [...] }
# Reads: data/results/vulnerability_scores.parquet

@app.get("/vulnerability/by_zone")
# Params: year_month: str | None, bins_lat: int = 8, bins_lon: int = 8
# Returns: { count, rows: [{zone_lat, zone_lon, vulnerability_score, zone_id}] }
# Reads: data/results/vulnerability_scores.parquet

@app.get("/vulnerability/timeseries")
# Returns: { count, rows: [{year_month, vulnerability_score}] }
# Reads: data/results/vulnerability_scores.parquet

@app.get("/metadata")
# Returns: { rows, months, sources, evaluation?, training_metrics? }
# Reads: vulnerability_scores.parquet, evaluation.json, training_metrics.json
```

**API design rule:** API is read-only over `data/results/`. No model training or inference runs inside request handling.

**Run:** `python scripts/run_api.py` → `uvicorn` on `0.0.0.0:8000`

### Frontend (Streamlit)

**Code:** `src/frontend/app.py`  
**Run:** `python scripts/run_frontend.py`  
**Connects to:** `FLOOD_API_BASE` env var (default `http://127.0.0.1:8000`)

**Dashboard features:**

- City selector sidebar (Bengaluru, Hyderabad, Mumbai, Pune)
- Executive Flood Dashboard tab:
  - KPIs: High-risk multiplier, estimated exposed residents, YoY change, drainage hotspots
  - Preparedness alert banner
  - Vulnerability map (Streamlit `st.map`)
  - Zone-level priority table with Google Maps links
  - Hotspot bar chart
  - Risk tier mix chart
  - Population impact panel
  - Seasonal preparedness trend
  - Preventive action engine
  - Rainfall scenario simulator
  - Executive narrative summary
- Project Details tab:
  - Model quality explanation
  - Evaluation summary
  - Trust/caution guidelines

---

## Known issues and technical debt

### Code issues

1. **Feature importance is empty.** `HistGradientBoostingRegressor` does not expose `feature_importances_` in the current environment. The code has a `hasattr` guard but produces an empty list. Consider using permutation importance or SHAP as an alternative.

2. **Dead commented-out code in `src/inference/pipeline.py`** (lines 31–40). Old implementation left as comments. Should be removed.

3. **`bengaluru_2020_2024_operational.json`** config has most sources disabled (`sentinel_1: false`, `sentinel_2: false`, `ghsl: false`, `worldpop: false`, `osm_roads: false`). Its purpose and usage context are unclear — it may be a testing convenience or a deprecated file.

4. **Top-level source directories in `data/raw/`** (`dem/`, `era5/`, `ghsl/`, etc. at `data/raw/` root, not under a city). These appear to be from an older non-city-scoped layout and may be stale.

### Documentation issues

5. **`mkdocs.yml` `site_name` says "Bengaluru Flood Vulnerability Docs"** — should reflect multi-city scope since the project now covers 4 cities.

6. **`docs/api.md` is accurate** for current routes but is minimal and lacks query parameter details (e.g., `limit`, `bins_lat`, `bins_lon` ranges).

7. 7. **README.md is mostly accurate** and matches the current API routes and pipeline flow. It could still be improved by documenting `FLOOD_API_BASE`, clarifying optional script shortcuts, and noting which dataset file training prefers when both single-city and multi-city datasets exist.

### Data/pipeline issues

8. **`flood_dataset_multicity_backup.parquet`** exists alongside the main file. Its provenance and whether it should be kept or removed is unclear.

9. **No pinned versions in `requirements.txt`.** All dependencies are unpinned (`numpy`, `pandas`, etc.), which may cause reproducibility issues.

10. **No automated tests.** There is no test suite, `pytest` configuration, or CI/CD pipeline.

11. **`GEE_PROJECT_ID` is required but never used in code.** The environment variable is loaded and validated in `AppSettings` but no code path uses `gee_project_id`. This is likely a planned but unimplemented integration.

12. **Preprocessing uses random noise injection** (`np.random.default_rng(...)`) in feature computation. This is seeded deterministically but may produce unexpected variability if seeds are changed.

---

## Documentation alignment check

### Accurate ✅

- README.md pipeline step list matches actual scripts
- README.md API endpoint list matches `src/api/app.py` decorators exactly
- README.md cities list matches config files and frontend code
- `docs/architecture.md` execution order matches script names
- `docs/api.md` endpoints match code

### Outdated ⚠️

- `mkdocs.yml` `site_name` says "Bengaluru" — should say multi-city
- README.md does not mention `FLOOD_API_BASE` env var for frontend

### Needs manual verification 🔍

- Whether `bengaluru_2020_2024_operational.json` is actively used or deprecated
- Whether top-level directories in `data/raw/` (not under any city) contain data that is still relevant
- Whether `flood_dataset_multicity_backup.parquet` should be kept or removed
- Whether `GEE_PROJECT_ID` integration is planned or abandoned

---

## Next best actions

### Priority 1: Presentation readiness

1. **Fix feature importance.** Add permutation importance or use `model.feature_importances_` from a scikit-learn version that supports it for `HistGradientBoostingRegressor`, to populate `feature_importance.json`.
2. **Remove dead code** in `src/inference/pipeline.py` (commented-out lines 31–40).
3. **Update `mkdocs.yml` `site_name`** to reflect multi-city scope.
4. **Pin dependency versions** in `requirements.txt` for reproducibility.

### Priority 2: Documentation accuracy

5. **Update README.md** quick start to show `--city` and `--all-default-cities` flags for preprocessing and feature build.
6. **Document `FLOOD_API_BASE`** env var in README.md and `.env.example`.
7. **Expand `docs/api.md`** with full query parameter documentation (types, defaults, ranges).
8. **Clarify or remove** `bengaluru_2020_2024_operational.json`.

### Priority 3: Engineering quality

9. **Add basic test suite** (at minimum: config loading, feature builder, model training smoke test, API route tests).
10. **Clean up stale data** — remove or document `flood_dataset_multicity_backup.parquet` and top-level `data/raw/` source directories.
11. **Remove or implement `GEE_PROJECT_ID`** — either remove from required env vars or implement the planned integration.
12. **Add CI/CD** — GitHub Actions for linting, testing, and build verification.

### Priority 4: Model improvements

13. **Evaluate SHAP values** for model interpretability since feature importance is empty.
14. **Add cross-validation** or expanding-window validation for more robust model comparison.
15. **Explore city-specific models** vs. the current pooled multi-city model to assess whether per-city performance improves.

---

## Appendix

### Exact current API routes

```
GET  /vulnerability/latest       ?limit=200
GET  /vulnerability/by_zone      ?year_month=&bins_lat=8&bins_lon=8
GET  /vulnerability/timeseries
GET  /metadata
```

### Exact current environment variables

```
CDS_API_KEY           (required for ingestion)
CDSE_CLIENT_ID        (required for ingestion)
CDSE_CLIENT_SECRET    (required for ingestion)
GEE_PROJECT_ID        (required by settings validation, but unused in code)
FLOOD_API_BASE        (optional, frontend only, default: http://127.0.0.1:8000)
```

### Exact output artifact names

```
data/results/training_metrics.json
data/results/evaluation.json
data/results/feature_importance.json
data/results/vulnerability_scores.parquet
data/results/models/baseline_model.joblib
data/results/models/temporal_model.joblib
data/features/flood_dataset.parquet
data/features/flood_dataset_multicity.parquet
```

### Exact important file paths

```
config/bengaluru_2020_2024.json
config/hyderabad_2020_2024.json
config/mumbai_2020_2024.json
config/pune_2020_2024.json
src/api/app.py
src/frontend/app.py
src/models/temporal.py
src/training/pipeline.py
src/inference/pipeline.py
src/evaluation/pipeline.py
src/features/dataset_builder.py
src/preprocessing/pipeline.py
src/ingestion/pipeline.py
src/ingestion/adapters.py
src/ingestion/cdse_client.py
src/common/settings.py
```

### Feature columns (defined in `src/features/dataset_builder.py`)

```python
FEATURE_COLUMNS = [
    "sar_water_persistence",
    "rainfall_accumulation",
    "low_lying_score",
    "impervious_change_rate",
    "population_exposure",
]
```

### Full temporal feature set (25 features used by temporal model)

```
5 base features
+ 5 × lag1
+ 5 × lag2
+ 5 × lag3
+ 5 × roll3
= 25 total temporal features
```

### Example commands for full pipeline run

```bash
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Ensure .env has: CDS_API_KEY, CDSE_CLIENT_ID, CDSE_CLIENT_SECRET, GEE_PROJECT_ID

# 3. Full multi-city pipeline
python scripts/run_ingestion.py --all-default-cities
python scripts/run_preprocessing.py --all-default-cities
python scripts/run_feature_build.py --all-default-cities
python scripts/run_training.py
python scripts/run_inference.py
python scripts/run_evaluation.py

# 4. Start services
python scripts/run_api.py         # API on port 8000
python scripts/run_frontend.py    # Streamlit dashboard
```

### Example commands for single-city run

```bash
python scripts/run_ingestion.py --city bengaluru
python scripts/run_preprocessing.py --city bengaluru
python scripts/run_feature_build.py --city bengaluru
python scripts/run_training.py
python scripts/run_inference.py
python scripts/run_evaluation.py
```
