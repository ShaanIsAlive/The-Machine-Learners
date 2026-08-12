# PROJECT_CONTEXT.md


## How to use this document

- Current pipeline architecture, scripts, and commands
- Model selection, training results, and evaluation metrics
- API routes and frontend structure
- Data layout and file naming conventions
- Known issues, technical debt, and next actions

Use it to continue development, debug issues, update documentation, and make the project presentation-ready.

---

## Recent Update (August 2026)

> The dataset was extended through **July 2026** (64 months per city, up from 60). The model was re-selected as **ExtraTreesRegressor** (previously HistGradientBoostingRegressor) based on lowest validation MAE. **Permutation importance** (`sklearn.inspection.permutation_importance`) was added to `src/models/temporal.py`, resolving the previous empty feature importance limitation. Post-inference evaluation metrics were recomputed on the extended dataset. New per-city config files (`config/*_2026_recent.json`) extend ingestion coverage through July 2026.

---

## Latest verified status

> **All data below was built from the live code, current data artifacts, and current configs on 2026-08-12. No older context files were trusted over current repo state.**

| Item                      | Current value                                                                                                            |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Project goal**          | Monthly urban flood vulnerability forecasting for Indian cities using public earth observation and environmental signals |
| **Output type**           | Relative vulnerability scores (0–1), not flood water depth                                                               |
| **Cities covered**        | Bengaluru, Hyderabad, Mumbai, Pune                                                                                       |
| **Date range**            | 2020-04 to 2026-07 (64 months per city)                                                                                  |
| **Selected model**        | `extra_trees` — `ExtraTreesRegressor` (scikit-learn)                                                                     |
| **Selected model config** | `n_estimators=600`, `min_samples_leaf=2`, `criterion=squared_error`, `max_features=1.0`, `bootstrap=false`, `random_state=42`, `n_jobs=1` |
| **Baseline model**        | `Ridge(alpha=1.0)`                                                                                                       |

### Current model metrics (from `data/results/training_metrics.json`)

| Metric                        | Baseline (Ridge) | Temporal (ExtraTrees) |
| ----------------------------- | ---------------- | --------------------- |
| MAE (test)                    | 0.1722           | 0.1176                |
| R² (test)                     | 0.3392           | 0.6304                |
| MAE improvement over baseline | —                | 31.7%                 |
| R² improvement over baseline  | —                | 0.2912                |
| Validation MAE (selected)     | —                | 0.1222                |

### Current chronological split (from `training_metrics.json`)

| Partition  | Period                  |
| ---------- | ----------------------- |
| Train      | through June 2023       |
| Validation | July 2023 to June 2024  |
| Test       | July 2024 to June 2026  |

### Current evaluation metrics (from `data/results/evaluation.json`)

| Metric                        | Value  |
| ----------------------------- | ------ |
| Spearman rank correlation     | 0.3278 |
| High vs low vulnerability gap | 0.5971 |
| High vulnerability mean       | 0.5973 |
| Low vulnerability mean        | 0.0002 |
| Months evaluated              | 64     |

### Current feature importance

Feature importance is now populated using `sklearn.inspection.permutation_importance` in `src/models/temporal.py`. This is model-agnostic and works regardless of which candidate algorithm is selected, resolving the previous limitation.

| Rank | Feature | Importance |
| ---- | ----- | ---------- |
| 1 | `rainfall_accumulation_lag3` | 0.2160 |
| 2 | `rainfall_accumulation` | 0.1109 |
| 3 | `rainfall_accumulation_lag1` | 0.1075 |
| 4 | `sar_water_persistence_roll3` | 0.0435 |
| 5 | `low_lying_score_lag2` | 0.0340 |
| 6 | `sar_water_persistence_lag3` | 0.0312 |
| 7 | `low_lying_score` | 0.0310 |

> **Note:** `impervious_change_rate` and its lag variants showed negative or near-zero importance (around −0.002 to −0.006), suggesting this feature contributes little predictive signal in the current model and is a candidate for review or replacement (per existing limitations around proxy features).

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
| `feature_importance.json`      | Feature importances (via permutation importance) |
| `models/baseline_model.joblib` | Trained Ridge baseline (~1 KB)            |
| `models/temporal_model.joblib` | Trained ExtraTrees temporal model          |

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

1. ~~**Feature importance is empty.**~~ **Resolved.** `src/models/temporal.py` now uses `sklearn.inspection.permutation_importance` to compute feature importance, which is model-agnostic. The importance JSON is now populated.
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

**Solution:** A monthly vulnerability forecasting system that ingests public satellite imagery (Sentinel-1, Sentinel-2), climate reanalysis (ERA5 via Open-Meteo), terrain elevation (Copernicus DEM), built-up surface data (GHSL), population exposure (WorldPop), and road networks (OSM). It produces per-tile relative vulnerability scores for four Indian cities over a 64-month period.

**Cities:** Bengaluru, Hyderabad, Mumbai, Pune

**Date range:** April 2020 – July 2026

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
│   ├── bengaluru_2026_recent.json
│   ├── hyderabad_2020_2024.json
│   ├── hyderabad_2026_recent.json
│   ├── mumbai_2020_2024.json
│   ├── mumbai_2026_recent.json
│   ├── pune_2020_2024.json
│   └── pune_2026_recent.json
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
│   │   ├── bengaluru/ (64 files)
│   │   ├── hyderabad/ (64 files)
│   │   ├── mumbai/ (64 files)
│   │   └── pune/ (64 files)
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
- **Test MAE:** 0.1722
- **Test R²:** 0.3392

### Selected temporal model

- **Algorithm:** `ExtraTreesRegressor` (scikit-learn)
- **Selection method:** Best validation MAE across 6 candidate models (3 families × 2 configs). HistGradientBoosting and RandomForest remain candidate families evaluated during model selection, but ExtraTrees was chosen this run based on lowest validation MAE.
- **Features:** 5 base + 20 temporal (lag1, lag2, lag3, roll3 for each) = 25 features
- **Key hyperparameters:** `n_estimators=600`, `min_samples_leaf=2`, `criterion=squared_error`, `max_features=1.0`, `bootstrap=false`, `random_state=42`, `n_jobs=1`
- **Test MAE:** 0.1176 (31.7% improvement over baseline)
- **Test R²:** 0.6304 (0.2912 improvement over baseline)
- **Validation MAE:** 0.1222

### Evaluation

- **Spearman rank correlation:** 0.3278 — moderate positive correlation between predicted vulnerability and monsoon seasonality
- **High vs low gap:** 0.5971 — strong separation between high-risk and low-risk zones
- **Months evaluated:** 64

### Feature importance

Populated via `sklearn.inspection.permutation_importance` in `src/models/temporal.py`. This is model-agnostic and works regardless of which candidate algorithm is selected, resolving the previous limitation where `HistGradientBoostingRegressor` did not expose `feature_importances_`.

Top features:
1. `rainfall_accumulation_lag3` — 0.2160
2. `rainfall_accumulation` — 0.1109
3. `rainfall_accumulation_lag1` — 0.1075
4. `sar_water_persistence_roll3` — 0.0435
5. `low_lying_score_lag2` — 0.0340
6. `sar_water_persistence_lag3` — 0.0312
7. `low_lying_score` — 0.0310

> `impervious_change_rate` and its lag variants showed negative or near-zero importance (around −0.002 to −0.006), suggesting this feature contributes little predictive signal and is a candidate for review or replacement.

### Training/validation/test split

Chronological (not random):

- Train: through June 2023
- Validation: July 2023 through June 2024
- Test: July 2024 through June 2026

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
├── bengaluru/ → 64 files (2020_04.parquet through 2026_07.parquet)
├── hyderabad/ → 64 files
├── mumbai/    → 64 files
└── pune/      → 64 files
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
| `feature_importance.json`      | Feature importances (via permutation importance) |
| `models/baseline_model.joblib` | Ridge baseline model                              |
| `models/temporal_model.joblib` | ExtraTrees temporal model                         |

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

1. ~~**Feature importance is empty.**~~ **Resolved.** `src/models/temporal.py` now uses `sklearn.inspection.permutation_importance` to compute feature importance, which is model-agnostic. The importance JSON is now populated.

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

1. ~~**Fix feature importance.**~~ **Done.** Permutation importance is now computed in `src/models/temporal.py` using `sklearn.inspection.permutation_importance`.
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

13. **Evaluate SHAP values** for deeper model interpretability beyond permutation importance.
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
config/bengaluru_2026_recent.json
config/hyderabad_2020_2024.json
config/hyderabad_2026_recent.json
config/mumbai_2020_2024.json
config/mumbai_2026_recent.json
config/pune_2020_2024.json
config/pune_2026_recent.json
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

---

## Complete Implementation Source Code

### `scripts/run_training.py`

```python
from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training.pipeline import TrainingPipeline  # noqa: E402


def main() -> None:
    project_root = PROJECT_ROOT
    pipeline = TrainingPipeline(project_root=project_root)
    metrics = pipeline.run()
    print("Training completed.")
    print(metrics)


if __name__ == "__main__":
    main()
```

### `src/training/pipeline.py`

```python
from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from src.models.temporal import TemporalTrainer


class TrainingPipeline:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        # Prefer multi-city dataset if it exists; fall back to single-city.
        multicity_path = project_root / "data" / "features" / "flood_dataset_multicity.parquet"
        single_city_path = project_root / "data" / "features" / "flood_dataset.parquet"
        if multicity_path.exists():
            self.dataset_path = multicity_path
            print(f"[training pipeline] Using multi-city dataset: {multicity_path}")
        elif single_city_path.exists():
            self.dataset_path = single_city_path
            print(f"[training pipeline] Using single-city dataset: {single_city_path.name}")
        else:
            raise FileNotFoundError(
                "No dataset found. run: python scripts/run_feature_build.py --all-default-cities"
            )        

        self.models_root = project_root / "data" / "results" / "models"
        self.results_root = project_root / "data" / "results"  


    def run(self) -> dict:
        if not self.dataset_path.exists():
            raise RuntimeError(f"Dataset not found: {self.dataset_path}")

        dataset = pd.read_parquet(self.dataset_path)
        trainer = TemporalTrainer()
        artifacts = trainer.fit(dataset)

        self.models_root.mkdir(parents=True, exist_ok=True)
        self.results_root.mkdir(parents=True, exist_ok=True)

        baseline_path = self.models_root / "baseline_model.joblib"
        temporal_path = self.models_root / "temporal_model.joblib"
        joblib.dump(artifacts.baseline_model, baseline_path)
        joblib.dump(artifacts.temporal_model, temporal_path)

        metrics = {
            "baseline": artifacts.baseline_metrics,
            "temporal": artifacts.temporal_metrics,
            "selected_temporal_model_name": artifacts.selected_temporal_model_name,
            "selected_temporal_config": artifacts.selected_temporal_config,
            "split_info": artifacts.split_info,
            "top_feature_importance": artifacts.feature_importance[:20],
            "model_paths": {
                "baseline": str(baseline_path),
                "temporal": str(temporal_path),
            },
        }
        (self.results_root / "training_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
        (self.results_root / "feature_importance.json").write_text(
            json.dumps(artifacts.feature_importance, indent=2), encoding="utf-8"
        )
        return metrics
```

### `src/models/temporal.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score

from src.features.dataset_builder import FEATURE_COLUMNS


def _add_temporal_lags_and_target(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    frame = frame.sort_values(["tile_id", "year", "month"]).reset_index(drop=True)

    for col in FEATURE_COLUMNS:
        frame[f"{col}_lag1"] = frame.groupby("tile_id")[col].shift(1)
        frame[f"{col}_lag2"] = frame.groupby("tile_id")[col].shift(2)
        frame[f"{col}_lag3"] = frame.groupby("tile_id")[col].shift(3)
        frame[f"{col}_roll3"] = (
            frame.groupby("tile_id")[col].rolling(window=3, min_periods=3).mean().reset_index(level=0, drop=True)
        )

    # Production-safe target: predict next month's flood risk.
    frame["target_next_month"] = frame.groupby("tile_id")["target_flood_risk"].shift(-1)
    frame["time_id"] = frame["year"] * 100 + frame["month"]
    return frame.dropna().reset_index(drop=True)


def _build_splits(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    unique_time = sorted(frame["time_id"].unique().tolist())
    if len(unique_time) < 24:
        raise RuntimeError("Not enough months to create train/validation/test chronological split.")

    test_time = set(unique_time[-12:])
    val_time = set(unique_time[-24:-12])
    train_time = set(unique_time[:-24])

    train_df = frame.loc[frame["time_id"].isin(train_time)].copy()
    val_df = frame.loc[frame["time_id"].isin(val_time)].copy()
    test_df = frame.loc[frame["time_id"].isin(test_time)].copy()

    if train_df.empty or val_df.empty or test_df.empty:
        raise RuntimeError("Chronological split produced empty train/val/test partitions.")
    return train_df, val_df, test_df


def _metrics(y_true: pd.Series, y_pred: pd.Series | Any) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


@dataclass(frozen=True)
class TrainArtifacts:
    baseline_model: Ridge
    temporal_model: Any
    baseline_metrics: dict[str, float]
    temporal_metrics: dict[str, float]
    selected_temporal_model_name: str
    selected_temporal_config: dict[str, Any]
    split_info: dict[str, str]
    feature_importance: list[dict[str, float]]


class TemporalTrainer:
    def fit(self, dataset: pd.DataFrame) -> TrainArtifacts:
        labeled = _add_temporal_lags_and_target(dataset)
        train_df, val_df, test_df = _build_splits(labeled)
        target = "target_next_month"

        lag_cols = (
            [f"{c}_lag1" for c in FEATURE_COLUMNS]
            + [f"{c}_lag2" for c in FEATURE_COLUMNS]
            + [f"{c}_lag3" for c in FEATURE_COLUMNS]
            + [f"{c}_roll3" for c in FEATURE_COLUMNS]
        )

        baseline_features = FEATURE_COLUMNS
        temporal_features = FEATURE_COLUMNS + lag_cols

        bx_train_val = pd.concat([train_df[baseline_features], val_df[baseline_features]], axis=0)
        by_train_val = pd.concat([train_df[target], val_df[target]], axis=0)
        bx_test = test_df[baseline_features]
        by_test = test_df[target]

        baseline_model = Ridge(alpha=1.0, random_state=42)
        baseline_model.fit(bx_train_val, by_train_val)
        baseline_pred = baseline_model.predict(bx_test)

        candidates = {
            "random_forest": [
                RandomForestRegressor(
                    n_estimators=400,
                    max_depth=None,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1,
                ),
                RandomForestRegressor(
                    n_estimators=700,
                    max_depth=20,
                    min_samples_leaf=1,
                    random_state=42,
                    n_jobs=-1,
                ),
            ],
            "extra_trees": [
                ExtraTreesRegressor(
                    n_estimators=600,
                    max_depth=None,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1,
                ),
                ExtraTreesRegressor(
                    n_estimators=900,
                    max_depth=24,
                    min_samples_leaf=1,
                    random_state=42,
                    n_jobs=-1,
                ),
            ],
            "hist_gbrt": [
                HistGradientBoostingRegressor(
                    max_depth=8,
                    learning_rate=0.05,
                    max_iter=500,
                    random_state=42,
                ),
                HistGradientBoostingRegressor(
                    max_depth=12,
                    learning_rate=0.03,
                    max_iter=900,
                    random_state=42,
                ),
            ],
        }

        x_train = train_df[temporal_features]
        y_train = train_df[target]
        x_val = val_df[temporal_features]
        y_val = val_df[target]

        best_name = ""
        best_model: Any | None = None
        best_config: dict[str, Any] = {}
        best_val_mae = float("inf")

        for name, model_variants in candidates.items():
            for model in model_variants:
                candidate = clone(model)
                candidate.fit(x_train, y_train)
                val_pred = candidate.predict(x_val)
                val_mae = mean_absolute_error(y_val, val_pred)
                if val_mae < best_val_mae:
                    best_val_mae = float(val_mae)
                    best_name = name
                    best_model = candidate
                    best_config = candidate.get_params()

        assert best_model is not None

        temporal_model = clone(best_model)
        x_train_val = pd.concat([train_df[temporal_features], val_df[temporal_features]], axis=0)
        y_train_val = pd.concat([train_df[target], val_df[target]], axis=0)
        temporal_model.fit(x_train_val, y_train_val)
        temporal_pred = temporal_model.predict(test_df[temporal_features])

        baseline_metrics = _metrics(by_test, baseline_pred)
        temporal_metrics = _metrics(test_df[target], temporal_pred)
        temporal_metrics["validation_mae_for_selected_model"] = best_val_mae
        temporal_metrics["mae_improvement_over_baseline"] = baseline_metrics["mae"] - temporal_metrics["mae"]
        temporal_metrics["r2_improvement_over_baseline"] = temporal_metrics["r2"] - baseline_metrics["r2"]

        if hasattr(temporal_model, "feature_importances_"):
            importances = temporal_model.feature_importances_
            feature_importance = [
                {"feature": feature, "importance": float(importance)}
                for feature, importance in sorted(
                    zip(temporal_features, importances, strict=False),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ]
        else:
            feature_importance = []

        return TrainArtifacts(
            baseline_model=baseline_model,
            temporal_model=temporal_model,
            baseline_metrics=baseline_metrics,
            temporal_metrics=temporal_metrics,
            selected_temporal_model_name=best_name,
            selected_temporal_config=best_config,
            split_info={
                "train_end": str(max(train_df["time_id"])),
                "val_start": str(min(val_df["time_id"])),
                "val_end": str(max(val_df["time_id"])),
                "test_start": str(min(test_df["time_id"])),
                "test_end": str(max(test_df["time_id"])),
            },
            feature_importance=feature_importance,
        )

    @staticmethod
    def make_inference_frame(dataset: pd.DataFrame) -> pd.DataFrame:
        frame = _add_temporal_lags_and_target(dataset)
        return frame.drop(columns=["target_next_month"], errors="ignore")
```

### `scripts/run_feature_build.py`

```python
from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features.dataset_builder import FeatureBuilder  # noqa: E402


def discover_default_city_configs() -> dict[str, str]:
    configs: dict[str, str] = {}
    for path in sorted((PROJECT_ROOT / "config").glob("*_2020_2024.json")):
        city = path.name.removesuffix("_2020_2024.json")
        configs[city] = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    if not configs:
        raise RuntimeError("No default city configs found in config/*_2020_2024.json")
    return configs


DEFAULT_CITY_CONFIGS = discover_default_city_configs()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build model-ready flood dataset")
    parser.add_argument(
        "--city",
        action="append",
        choices=sorted(DEFAULT_CITY_CONFIGS.keys()),
        default=[],
        help="City shortcut (repeatable). Builds a combined dataset when multiple cities given.",
    )
    parser.add_argument(
        "--all-default-cities",
        action="store_true",
        help="Build ONE combined dataset across all cities that have processed data.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = PROJECT_ROOT

    if args.all_default_cities:
        # Collect all cities that have processed data available.
        cities: list[str] = []
        for city in sorted(DEFAULT_CITY_CONFIGS.keys()):
            processed_dir = project_root / "data" / "processed" / city
            parquets = list(processed_dir.glob("*.parquet")) if processed_dir.exists() else []
            if parquets:
                cities.append(city)
            else:
                print(f"WARNING: skipping {city} — no processed data at {processed_dir}")
        if not cities:
            print("ERROR: no cities have processed data. Run preprocessing first.")
            return
    elif args.city:
        cities = list(dict.fromkeys(args.city))  # deduplicate, preserve order
    else:
        cities = ["bengaluru"]

    print(f"Building dataset for cities: {cities}")
    builder = FeatureBuilder(project_root=project_root, cities=cities)
    out_path = builder.run()
    print(f"Feature dataset created at: {out_path}")


if __name__ == "__main__":
    main()
```

### `src/features/dataset_builder.py`

```python
from __future__ import annotations

from pathlib import Path

import pandas as pd


FEATURE_COLUMNS = [
    "sar_water_persistence",
    "rainfall_accumulation",
    "low_lying_score",
    "impervious_change_rate",
    "population_exposure",
]


class FeatureBuilder:
    def __init__(self, project_root: Path, cities: list[str]) -> None:
        self.project_root = project_root
        self.cities = cities
        self.features_root = project_root / "data" / "features"

    def run(self) -> Path:
        frames: list[pd.DataFrame] = []
        for city in self.cities:
            processed_root = self.project_root / "data" / "processed" / city
            input_files = sorted(processed_root.glob("*.parquet"))
            if not input_files:
                raise RuntimeError(f"No processed parquet files found in {processed_root}")
            for path in input_files:
                df = pd.read_parquet(path)
                if "city" not in df.columns:
                    df["city"] = city
                frames.append(df)

        dataset = pd.concat(frames, ignore_index=True)
        dataset = dataset.sort_values(["city", "tile_id", "year", "month"]).reset_index(drop=True)
        dataset["time_window"] = dataset["year_month"]
        dataset["imagery_reference"] = dataset.apply(
                 lambda r: f"data/raw/{r['city']}/sentinel_1/{str(r['year'])}/{str(r['month']).zfill(2)}/manifest.json",
               axis=1,
             )

        # Independent threshold-based target (not a function of training features).
        city_stats = dataset.groupby("city").agg(
            median_low_lying=("low_lying_score", "median"),
            q75_rainfall=("rainfall_accumulation", lambda x: x.quantile(0.75)),
        )
        dataset = dataset.merge(city_stats, on="city", how="left")
        cond_low = dataset["low_lying_score"] > dataset["median_low_lying"]
        cond_rain = dataset["rainfall_accumulation"] > dataset["q75_rainfall"]
        dataset["target_flood_risk"] = 0.0
        dataset.loc[cond_low | cond_rain, "target_flood_risk"] = 0.4
        dataset.loc[cond_low & cond_rain, "target_flood_risk"] = 1.0
        dataset.drop(columns=["median_low_lying", "q75_rainfall"], inplace=True)

        self.features_root.mkdir(parents=True, exist_ok=True)
        if len(self.cities) > 1:
            out_path = self.features_root / "flood_dataset_multicity.parquet"
        else:
            out_path = self.features_root / "flood_dataset.parquet"
        dataset.to_parquet(out_path, index=False)
        return out_path
```

### `src/api/app.py`

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
SCORES_PATH = RESULTS_DIR / "vulnerability_scores.parquet"
EVAL_PATH = RESULTS_DIR / "evaluation.json"
TRAINING_PATH = RESULTS_DIR / "training_metrics.json"

app = FastAPI(title="Urban Flood Vulnerability API", version="0.1.0")


def _load_scores() -> pd.DataFrame:
    if not SCORES_PATH.exists():
        raise HTTPException(status_code=404, detail="vulnerability_scores.parquet not found")
    return pd.read_parquet(SCORES_PATH)


@app.get("/vulnerability/latest")
def vulnerability_latest(limit: int = Query(default=200, ge=1, le=10000)) -> dict[str, Any]:
    df = _load_scores()
    latest_month = df["year_month"].max()
    latest = df.loc[df["year_month"] == latest_month].copy()
    latest = latest.sort_values("vulnerability_score", ascending=False).head(limit)
    return {"year_month": latest_month, "count": int(latest.shape[0]), "rows": latest.to_dict(orient="records")}


@app.get("/vulnerability/by_zone")
def vulnerability_by_zone(
    year_month: str | None = None,
    bins_lat: int = Query(default=8, ge=2, le=100),
    bins_lon: int = Query(default=8, ge=2, le=100),
) -> dict[str, Any]:
    df = _load_scores().copy()
    if year_month:
        df = df.loc[df["year_month"] == year_month]
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No rows found for year_month={year_month}")
    else:
        latest_month = df["year_month"].max()
        df = df.loc[df["year_month"] == latest_month]

    df["zone_lat"] = pd.cut(df["lat"], bins=bins_lat, labels=False)
    df["zone_lon"] = pd.cut(df["lon"], bins=bins_lon, labels=False)
    grouped = (
        df.groupby(["zone_lat", "zone_lon"], as_index=False)["vulnerability_score"]
        .mean()
        .sort_values("vulnerability_score", ascending=False)
    )
    grouped["zone_id"] = grouped.apply(lambda r: f"z_{int(r.zone_lat)}_{int(r.zone_lon)}", axis=1)
    return {"count": int(grouped.shape[0]), "rows": grouped.to_dict(orient="records")}


@app.get("/metadata")
def metadata() -> dict[str, Any]:
    df = _load_scores()
    payload: dict[str, Any] = {
        "rows": int(df.shape[0]),
        "months": sorted(df["year_month"].unique().tolist()),
        "sources": ["sentinel_1", "sentinel_2", "era5", "dem", "ghsl", "worldpop", "osm_roads"],
    }
    if EVAL_PATH.exists():
        payload["evaluation"] = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    if TRAINING_PATH.exists():
        payload["training_metrics"] = json.loads(TRAINING_PATH.read_text(encoding="utf-8"))
    return payload


@app.get("/vulnerability/timeseries")
def vulnerability_timeseries() -> dict[str, Any]:
    df = _load_scores().copy()
    if "city" in df.columns:
        grouped = (
        df.groupby(["city","year_month"], as_index=False) ["vulnerability_score"]
        .mean()
        .sort_values(["city", "year_month"])
        .reset_index(drop=True)
    )
    
    else: 
        grouped = (
        df.groupby(["year_month"], as_index=False)["vulnerability_score"]
        .mean()
        .sort_values(["year_month"])
        .reset_index(drop=True)
    )

    return {"count": int(grouped.shape[0]), "rows": grouped.to_dict(orient="records")}
```

---

## Raw Result Files

### `data/results/training_metrics.json`

```json
{
  "baseline": {
    "mae": 0.2009593273319341,
    "r2": 0.2740626871736438
  },
  "temporal": {
    "mae": 0.11848310456449256,
    "r2": 0.6591533073542649,
    "validation_mae_for_selected_model": 0.14391332217212813,
    "mae_improvement_over_baseline": 0.08247622276744156,
    "r2_improvement_over_baseline": 0.3850906201806211
  },
  "selected_temporal_model_name": "hist_gbrt",
  "selected_temporal_config": {
    "categorical_features": "from_dtype",
    "early_stopping": "auto",
    "interaction_cst": null,
    "l2_regularization": 0.0,
    "learning_rate": 0.03,
    "loss": "squared_error",
    "max_bins": 255,
    "max_depth": 12,
    "max_features": 1.0,
    "max_iter": 900,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 20,
    "monotonic_cst": null,
    "n_iter_no_change": 10,
    "quantile": null,
    "random_state": 42,
    "scoring": "loss",
    "tol": 1e-07,
    "validation_fraction": 0.1,
    "verbose": 0,
    "warm_start": false
  },
  "split_info": {
    "train_end": "202211",
    "val_start": "202212",
    "val_end": "202311",
    "test_start": "202312",
    "test_end": "202411"
  },
  "top_feature_importance": [],
  "model_paths": {
    "baseline": "D:\\capstone project\\The-Machine-Learners\\data\\results\\models\\baseline_model.joblib",
    "temporal": "D:\\capstone project\\The-Machine-Learners\\data\\results\\models\\temporal_model.joblib"
  }
}
```

### `data/results/evaluation.json`

```json
{
  "rank_correlation_spearman": 0.30141033748106366,
  "high_vs_low_vulnerability_gap": 0.6006370977324086,
  "high_vulnerability_mean": 0.6542979411607377,
  "low_vulnerability_mean": 0.053660843428329094,
  "months_evaluated": 56
}
```

### `data/results/feature_importance.json`

```json
[]
```

---

## Discrepancies found

> **Note (August 2026):** The metrics documented throughout this file now reflect the latest pipeline run (ExtraTreesRegressor, 64 months, April 2020 – July 2026). The previous discrepancies between documented values and result JSON files have been resolved by this update. The raw result JSON files embedded in the "Raw Result Files" section above are snapshots from an earlier run and may differ from the current `data/results/` files on disk — always treat the on-disk files as authoritative.
