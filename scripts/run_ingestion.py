from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.settings import AppSettings, explain_loaded_keys  # noqa: E402
from src.ingestion.config import IngestionConfig  # noqa: E402
from src.ingestion.pipeline import IngestionPipeline  # noqa: E402

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
    parser = argparse.ArgumentParser(description="Run flood project ingestion pipeline")
    parser.add_argument(
        "--config",
        action="append",
        default=[],
        help="Path to ingestion config json (repeatable)",
    )
    parser.add_argument(
        "--city",
        action="append",
        choices=sorted(DEFAULT_CITY_CONFIGS.keys()),
        default=[],
        help="City shortcut for default config (repeatable)",
    )
    parser.add_argument(
        "--all-default-cities",
        action="store_true",
        help="Run ingestion for all default city configs.",
    )
    parser.add_argument(
        "--live-fetch",
        action="store_true",
        help="If set, calls CDSE API for Sentinel sources.",
    )
    return parser.parse_args()


def resolve_config_paths(args: argparse.Namespace) -> list[Path]:
    selected: list[str] = []
    selected.extend(args.config)
    selected.extend(DEFAULT_CITY_CONFIGS[city] for city in args.city)
    if args.all_default_cities:
        selected.extend(DEFAULT_CITY_CONFIGS.values())
    if not selected:
        selected.append(DEFAULT_CITY_CONFIGS["bengaluru"])

    unique: list[Path] = []
    seen: set[Path] = set()
    for value in selected:
        path = (PROJECT_ROOT / value).resolve()
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def main() -> None:
    args = parse_args()
    project_root = PROJECT_ROOT
    settings = AppSettings.from_env(project_root=project_root)
    print(
        "Loaded env keys: "
        + explain_loaded_keys(["CDS_API_KEY", "CDSE_CLIENT_ID", "CDSE_CLIENT_SECRET", "GEE_PROJECT_ID"])
    )
    config_paths = resolve_config_paths(args)
    print(f"Config count: {len(config_paths)}")

    for config_path in config_paths:
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        config = IngestionConfig.from_json(config_path)
        print(
            f"Running ingestion for {config.city} from "
            f"{config.date_range.start.isoformat()} to {config.date_range.end.isoformat()} "
            f"using {config_path.relative_to(project_root)}"
        )
        pipeline = IngestionPipeline(settings=settings, config=config, live_fetch=args.live_fetch)
        pipeline.run()
    print("Ingestion completed for all requested configs.")


if __name__ == "__main__":
    main()
