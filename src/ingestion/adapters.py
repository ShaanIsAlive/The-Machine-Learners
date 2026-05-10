from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
import math
from pathlib import Path
from typing import Any

import requests

from src.common.time_utils import MonthWindow
from src.ingestion.cdse_client import CDSEClient, CopernicusQuery


def _bbox_center(bbox_wgs84: tuple[float, float, float, float]) -> tuple[float, float]:
    west, south, east, north = bbox_wgs84
    return ((south + north) / 2.0, (west + east) / 2.0)


def _download_binary(url: str, out_path: Path, timeout: int = 180) -> int:
    if url.startswith("s3://"):
        no_scheme = url.replace("s3://", "", 1)
        bucket, _, key = no_scheme.partition("/")
        url = f"https://{bucket}.s3.amazonaws.com/{key}"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        total_bytes = 0
        with out_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
                total_bytes += len(chunk)
    return total_bytes


def fetch_sentinel1_monthly_preprocessed(
    client: CDSEClient,
    bbox_wgs84: tuple[float, float, float, float],
    window: MonthWindow,
    out_dir: Path,
) -> dict[str, Any]:
    try:
        products = client.search_products(
            CopernicusQuery(
                collection="SENTINEL-1",
                start_date=window.start_date,
                end_date=window.end_date,
                bbox_wgs84=bbox_wgs84,
                max_records=100,
            )
        )
    except Exception as exc:
        products = {
            "value": [],
            "fallback": "catalog_query_failed",
            "error": str(exc),
            "start_date": window.start_date.isoformat(),
            "end_date": window.end_date.isoformat(),
        }
    payload = write_sentinel_products(products, out_dir)
    payload["ingestion_mode"] = "catalog_products"
    return payload


def fetch_sentinel2_monthly_preprocessed(
    client: CDSEClient,
    bbox_wgs84: tuple[float, float, float, float],
    window: MonthWindow,
    out_dir: Path,
) -> dict[str, Any]:
    try:
        products = client.search_products(
            CopernicusQuery(
                collection="SENTINEL-2",
                start_date=window.start_date,
                end_date=window.end_date,
                bbox_wgs84=bbox_wgs84,
                max_records=100,
            )
        )
    except Exception as exc:
        products = {
            "value": [],
            "fallback": "catalog_query_failed",
            "error": str(exc),
            "start_date": window.start_date.isoformat(),
            "end_date": window.end_date.isoformat(),
        }
    payload = write_sentinel_products(products, out_dir)
    payload["ingestion_mode"] = "catalog_products"
    return payload


def fetch_era5_equivalent_timeseries(
    bbox_wgs84: tuple[float, float, float, float],
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    lat, lon = _bbox_center(bbox_wgs84)
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": f"{lat:.5f}",
        "longitude": f"{lon:.5f}",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "precipitation_sum",
        "timezone": "UTC",
    }
    response = requests.get(url, params=params, timeout=90)
    response.raise_for_status()
    return response.json()


def write_era5_month_from_timeseries(
    full_payload: dict[str, Any],
    window: MonthWindow,
    out_dir: Path,
) -> dict[str, Any]:
    daily = full_payload.get("daily", {})
    times = daily.get("time", [])
    prec = daily.get("precipitation_sum", [])
    selected_time: list[str] = []
    selected_prec: list[float | None] = []
    start_iso = window.start_date.isoformat()
    end_iso = window.end_date.isoformat()
    for t, p in zip(times, prec):
        if start_iso <= t <= end_iso:
            selected_time.append(t)
            selected_prec.append(p)

    payload = {
        "latitude": full_payload.get("latitude"),
        "longitude": full_payload.get("longitude"),
        "daily": {
            "time": selected_time,
            "precipitation_sum": selected_prec,
        },
    }
    out_path = out_dir / "rainfall_daily.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {
        "status": "downloaded",
        "file": out_path.name,
        "provider": "open-meteo-archive-era5-equivalent",
    }


def fetch_dem_points(
    bbox_wgs84: tuple[float, float, float, float],
    out_dir: Path,
) -> dict[str, Any]:
    west, south, east, north = bbox_wgs84
    lat_degrees = range(math.floor(south), math.ceil(north))
    lon_degrees = range(math.floor(west), math.ceil(east))

    downloaded_tiles: list[dict[str, Any]] = []
    for lat in lat_degrees:
        for lon in lon_degrees:
            ns = "N" if lat >= 0 else "S"
            ew = "E" if lon >= 0 else "W"
            lat_abs = abs(lat)
            lon_abs = abs(lon)
            tile_name = f"Copernicus_DSM_COG_10_{ns}{lat_abs:02d}_00_{ew}{lon_abs:03d}_00_DEM"
            url = f"https://copernicus-dem-30m.s3.amazonaws.com/{tile_name}/{tile_name}.tif"
            out_path = out_dir / f"{tile_name}.tif"
            try:
                bytes_written = _download_binary(url, out_path)
                downloaded_tiles.append({"file": out_path.name, "bytes": bytes_written})
            except Exception as exc:
                downloaded_tiles.append({"file": out_path.name, "error": str(exc)})

    return {
        "status": "downloaded",
        "provider": "copernicus-dem-glo30",
        "tiles": downloaded_tiles,
    }


def fetch_osm_roads(
    bbox_wgs84: tuple[float, float, float, float],
    out_dir: Path,
) -> dict[str, Any]:
    west, south, east, north = bbox_wgs84
    query = (
        "[out:json][timeout:90];"
        f'way["highway"]({south},{west},{north},{east});'
        "out body geom;"
    )
    endpoints = (
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    )
    headers = {
        "Accept": "application/json",
        "User-Agent": "the-machine-learners-ingestion/1.0",
    }

    last_error: Exception | None = None
    payload: dict[str, Any] | None = None
    for endpoint in endpoints:
        try:
            # Some Overpass instances reject form-encoded bodies with 406.
            response = requests.post(
                endpoint,
                data=query.encode("utf-8"),
                headers={**headers, "Content-Type": "text/plain; charset=utf-8"},
                timeout=120,
            )
            response.raise_for_status()
            payload = response.json()
            break
        except Exception as exc:
            last_error = exc

    if payload is None:
        assert last_error is not None
        raise last_error

    out_path = out_dir / "roads_overpass.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {
        "status": "downloaded",
        "file": out_path.name,
        "provider": "openstreetmap-overpass",
    }


def write_sentinel_products(payload: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_path = out_dir / "products.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    product_count = len(payload.get("value", [])) if isinstance(payload, dict) else 0
    return {
        "status": "downloaded",
        "file": out_path.name,
        "products": product_count,
    }


def write_worldpop_reference(window: MonthWindow, out_dir: Path) -> dict[str, Any]:
    meta_path = out_dir / "worldpop_metadata.json"
    meta_path.write_text(
        json.dumps(
            {
                "reference_url": "https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/IND/ind_ppp_2020.tif",
                "year": window.year,
                "note": "Large static global raster referenced; reuse this URL for population extraction.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "status": "downloaded",
        "file": meta_path.name,
        "provider": "worldpop-reference",
    }


def write_ghsl_reference(window: MonthWindow, out_dir: Path) -> dict[str, Any]:
    # GHSL built-up surface distribution, 30 arc-second global layer.
    url = (
        "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/"
        "GHS_BUILT_S_GLOBE_R2023A/GHS_BUILT_S_E2020_GLOBE_R2023A_4326_30ss/"
        "V1-0/GHS_BUILT_S_E2020_GLOBE_R2023A_4326_30ss_V1_0.zip"
    )
    out_path = out_dir / "GHS_BUILT_S_E2020_GLOBE_R2023A_4326_30ss_V1_0.zip"
    bytes_written = _download_binary(url, out_path, timeout=240)

    meta_path = out_dir / "ghsl_proxy_metadata.json"
    meta_path.write_text(
        json.dumps(
            {
                "note": "GHSL built-up dataset downloaded (zipped raster package).",
                "source_url": url,
                "year": window.year,
                "bytes": bytes_written,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "status": "downloaded",
        "file": out_path.name,
        "provider": "ghsl-jrc",
        "bytes": bytes_written,
    }


def build_manifest(
    city: str,
    country: str,
    source_name: str,
    window: MonthWindow,
    roi_name: str,
    bbox_wgs84: tuple[float, float, float, float],
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "city": city,
        "country": country,
        "source": source_name,
        "window": asdict(window),
        "roi": {"name": roi_name, "bbox_wgs84": list(bbox_wgs84)},
        "payload": payload,
    }
