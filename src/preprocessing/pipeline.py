from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window, from_bounds

# pyrefly: ignore [missing-import]
from src.ingestion.config import IngestionConfig


def _json_or_none(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _sentinel_count(month_dir: Path) -> int:
    payload = _json_or_none(month_dir / "products.json")
    if isinstance(payload, dict) and isinstance(payload.get("value"), list):
        return len(payload["value"])
    return 0


def _rainfall_total_mm(month_dir: Path, month: int) -> float:
    payload = _json_or_none(month_dir / "rainfall_daily.json")
    if not payload:
        return 120.0 if month in {6, 7, 8, 9, 10} else 45.0
    daily = payload.get("daily", {})
    values = daily.get("precipitation_sum", [])
    if isinstance(values, list) and values:
        return float(np.nansum(np.array(values, dtype=float)))
    return 0.0


def _dem_low_lying_reference(month_dir: Path) -> float:
    """Legacy fallback: read dem_points.json or return 0.5 constant."""
    payload = _json_or_none(month_dir / "dem_points.json")
    if not payload:
        return 0.5
    elevations = []
    for item in payload.get("results", []):
        elev = item.get("elevation")
        if elev is not None:
            elevations.append(float(elev))
    if not elevations:
        return 0.5
    avg_elev = float(np.mean(elevations))
    # Bengaluru baseline elevation scaling to [0, 1] low-lying vulnerability proxy.
    return float(np.clip((980.0 - avg_elev) / 500.0 + 0.5, 0, 1))


def _dem_low_lying_from_raster(dem_dir: Path, tiles_df: pd.DataFrame, bbox_wgs84: tuple[float, float, float, float]) -> np.ndarray | None:
    """Read DEM .tif raster ONCE for the month, compute per-tile low-lying scores.

    Returns an ndarray of length len(tiles_df) with scores in [0, 1], or None
    if no readable .tif file is found (caller should fall back to legacy).
    """
    tif_files = sorted(dem_dir.glob("*.tif"))
    if not tif_files:
        return None

    # Try to open the first valid .tif (skip 0-byte files).
    dataset = None
    for tif_path in tif_files:
        if tif_path.stat().st_size == 0:
            continue
        try:
            dataset = rasterio.open(tif_path)
            break
        except Exception:
            continue
    if dataset is None:
        return None

    try:
        # Read the full raster once to compute city-wide median.
        full_data = dataset.read(1).astype(float)
        # Mask nodata values.
        nodata = dataset.nodata
        if nodata is not None:
            full_data[full_data == nodata] = np.nan
        city_median = float(np.nanmedian(full_data))

        # Compute tile grid step sizes from the bounding box.
        west, south, east, north = bbox_wgs84
        n_tiles = len(tiles_df)
        side = int(np.sqrt(n_tiles))
        tile_dx = (east - west) / side
        tile_dy = (north - south) / side

        scores = np.full(n_tiles, 0.5)  # fallback per-tile if window fails
        for idx in range(n_tiles):
            tile_lon = tiles_df.iloc[idx]["lon"]
            tile_lat = tiles_df.iloc[idx]["lat"]
            try:
                window = from_bounds(
                    tile_lon, tile_lat,
                    tile_lon + tile_dx, tile_lat + tile_dy,
                    transform=dataset.transform,
                )
                # Clamp to raster bounds.
                window = window.intersection(Window(0, 0, dataset.width, dataset.height))
                if window.width < 1 or window.height < 1:
                    continue
                tile_data = dataset.read(1, window=window).astype(float)
                if nodata is not None:
                    tile_data[tile_data == nodata] = np.nan
                valid = tile_data[~np.isnan(tile_data)]
                if len(valid) == 0:
                    continue
                scores[idx] = float(np.sum(valid < city_median) / len(valid))
            except Exception:
                continue

        return scores
    finally:
        dataset.close()


def _roads_density_reference(month_dir: Path) -> float:
    payload = _json_or_none(month_dir / "roads_overpass.json")
    if not payload:
        return 0.5
    elements = payload.get("elements", [])
    return float(np.clip(len(elements) / 5000.0, 0, 1))


def _build_city_tiles(config: IngestionConfig, n_tiles: int = 64) -> pd.DataFrame:
    west, south, east, north = config.roi.bbox_wgs84
    side = int(np.sqrt(n_tiles))
    xs = np.linspace(west, east, side, endpoint=False)
    ys = np.linspace(south, north, side, endpoint=False)
    rows: list[dict] = []
    idx = 0
    for y in ys:
        for x in xs:
            rows.append(
                {
                    "tile_id": f"{config.city}_tile_{idx:03d}",
                    "lon": float(x),
                    "lat": float(y),
                }
            )
            idx += 1
    return pd.DataFrame(rows)


class PreprocessingPipeline:
    def __init__(self, project_root: Path, config: IngestionConfig) -> None:
        self.project_root = project_root
        self.config = config
        self.raw_root = project_root / "data" / "raw" / config.city
        self.processed_root = project_root / "data" / "processed" / config.city

    def run(self) -> None:
        self.processed_root.mkdir(parents=True, exist_ok=True)
        tiles = _build_city_tiles(self.config)

        for year in range(self.config.date_range.start.year, self.config.date_range.end.year + 1):
            for month in range(1, 13):
                if year == self.config.date_range.start.year and month < self.config.date_range.start.month:
                    continue
                if year == self.config.date_range.end.year and month > self.config.date_range.end.month:
                    continue

                sentinel1_dir = self.raw_root / "sentinel_1" / str(year) / f"{month:02d}"
                sentinel2_dir = self.raw_root / "sentinel_2" / str(year) / f"{month:02d}"
                era5_dir = self.raw_root / "era5" / str(year) / f"{month:02d}"
                dem_dir = self.raw_root / "dem" / str(year) / f"{month:02d}"
                roads_dir = self.raw_root / "osm_roads" / str(year) / f"{month:02d}"

                s1_count = _sentinel_count(sentinel1_dir)
                s2_count = _sentinel_count(sentinel2_dir)
                rainfall_mm = _rainfall_total_mm(era5_dir, month)
                roads_ref = _roads_density_reference(roads_dir)

                df = tiles.copy()
                df["city"] = self.config.city
                df["year"] = year
                df["month"] = month
                df["year_month"] = f"{year:04d}_{month:02d}"
                df["sar_water_persistence"] = np.clip(
                    ((s1_count + s2_count) / 250.0)
                    + np.random.default_rng(year + month).normal(0, 0.01, len(df)),
                    0,
                    1,
                )
                df["rainfall_accumulation"] = np.maximum(
                    0.0, rainfall_mm + np.random.default_rng(year * 100 + month).normal(0, 4.5, len(df))
                )

                # Try real DEM raster; fall back to legacy reference.
                raster_scores = _dem_low_lying_from_raster(dem_dir, df, self.config.roi.bbox_wgs84)
                if raster_scores is not None:
                    df["low_lying_score"] = np.clip(raster_scores, 0, 1)
                else:
                    low_lying_ref = _dem_low_lying_reference(dem_dir)
                    df["low_lying_score"] = np.clip(
                        low_lying_ref + 0.12 * np.sin(df["lat"] * 3.0) + np.random.default_rng(month).normal(0, 0.03, len(df)),
                        0,
                        1,
                    )
                df["impervious_change_rate"] = np.clip(
                    (0.01 + 0.03 * roads_ref) * (year - self.config.date_range.start.year) / 4.0
                    + np.random.default_rng(year).normal(0.0, 0.003, len(df)),
                    0,
                    0.2,
                )
                df["population_exposure"] = np.clip(
                    0.35 + 0.3 * (df["lon"] - df["lon"].min()) / (df["lon"].max() - df["lon"].min() + 1e-9),
                    0,
                    1,
                )

                out_path = self.processed_root / f"{year:04d}_{month:02d}.parquet"
                df.to_parquet(out_path, index=False)
