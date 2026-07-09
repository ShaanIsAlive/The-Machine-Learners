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
