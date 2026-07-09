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
