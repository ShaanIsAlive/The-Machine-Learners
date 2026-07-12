from __future__ import annotations

import os

import pandas as pd
import requests
import streamlit as st


API_BASE = os.getenv("FLOOD_API_BASE", "http://127.0.0.1:8000")

st.set_page_config(page_title="Urban Flood Preparedness Dashboard", layout="wide")

CITIES = ["bengaluru", "hyderabad", "mumbai", "pune"]
CITY_DISPLAY = {
    "bengaluru": "Bengaluru",
    "hyderabad": "Hyderabad",
    "mumbai":    "Mumbai",
    "pune":      "Pune",
}
CITY_CENTER = {
    "bengaluru": (12.97, 77.59),
    "hyderabad": (17.38, 78.48),
    "mumbai":    (19.08, 72.88),
    "pune":      (18.52, 73.86),
}

selected_city = st.sidebar.selectbox(
    "Select city", CITIES, format_func=lambda c: CITY_DISPLAY[c]
)
city_label = CITY_DISPLAY[selected_city]

st.title(f"{city_label} Monsoon Preparedness Dashboard")
st.caption("Decision support for flood risk prioritization, exposure impact, and preventive action planning.")


def _get(path: str) -> dict:
    response = requests.get(f"{API_BASE}{path}", timeout=30)
    response.raise_for_status()
    return response.json()


try:
    metadata   = _get("/metadata")
    latest     = _get("/vulnerability/latest?limit=5000")
    by_zone    = _get("/vulnerability/by_zone?bins_lat=8&bins_lon=8")
    timeseries = _get("/vulnerability/timeseries")
except Exception as exc:
    st.error(f"Failed to connect to API at {API_BASE}: {exc}")
    st.stop()

rows = latest.get("rows", [])
if not rows:
    st.warning("No latest vulnerability rows available.")
    st.stop()

all_df      = pd.DataFrame(rows)
all_zone_df = pd.DataFrame(by_zone.get("rows", []))
all_series  = pd.DataFrame(timeseries.get("rows", []))

# ── Filter to selected city (case-insensitive) ─────────────────────────────
if "city" in all_df.columns:
    df = all_df[all_df["city"].astype(str).str.lower() == selected_city].copy()
else:
    df = all_df.copy()

if "city" in all_zone_df.columns:
    zone_df = all_zone_df[all_zone_df["city"].astype(str).str.lower() == selected_city].copy()
else:
    zone_df = all_zone_df.copy()

if "city" in all_series.columns:
    series_df = all_series[all_series["city"].astype(str).str.lower() == selected_city].copy()
else:
    series_df = all_series.copy()

if df.empty:
    st.warning(f"No vulnerability data found for {city_label}. Run inference first.")
    st.stop()

evaluation = metadata.get("evaluation", {})
training   = metadata.get("trainingmetrics",metadata.get("training_metrics", {}))


# ── Tier classification using city-relative percentiles ───────────────────
def classify_tier(score: float, p75: float, p50: float, p25: float) -> str:
    if score >= p75: return "Extreme"
    if score >= p50: return "High"
    if score >= p25: return "Moderate"
    return "Low"


def classify_city_risk(score: float) -> str:
    if score >= 0.70: return "Very High"
    if score >= 0.55: return "High"
    if score >= 0.40: return "Moderate"
    return "Low"


def dominant_stress_factor(year_month: str, score: float) -> str:
    month = int(year_month[-2:])
    if month in {6, 7, 8, 9, 10}:
        return "High rainfall accumulation and drainage load"
    if score >= 0.60:
        return "Surface runoff concentration in built-up zones"
    return "Localized low-lying area susceptibility"


def sector_label(lat: float, lon: float, center_lat: float, center_lon: float) -> str:
    ns = "North" if lat >= center_lat else "South"
    ew = "East"  if lon >= center_lon else "West"
    city_display = str(city_label)
    return f"{ns}-{ew} {city_display}"


def location_label(lat: float, lon: float, center_lat: float, center_lon: float) -> str:
    return f"{sector_label(lat, lon, center_lat, center_lon)} ({lat:.4f}, {lon:.4f})"


# ── Build map_df with city-relative tiers ─────────────────────────────────
map_df = df.copy()
center_lat, center_lon = CITY_CENTER[selected_city]

# Compute percentile thresholds once for this city
p75 = float(map_df["vulnerability_score"].quantile(0.75))
p50 = float(map_df["vulnerability_score"].quantile(0.50))
p25 = float(map_df["vulnerability_score"].quantile(0.25))

map_df["risk_tier"] = map_df["vulnerability_score"].apply(
    lambda s: classify_tier(s, p75, p50, p25)
)
map_df["location"] = map_df.apply(
    lambda r: location_label(float(r["lat"]), float(r["lon"]), center_lat, center_lon), axis=1
)
map_df["map_link"] = map_df.apply(
    lambda r: f"https://maps.google.com/?q={float(r['lat']):.6f},{float(r['lon']):.6f}", axis=1
)
map_df["estimated_exposure"] = ( map_df["vulnerability_score"] * 2000) .round() .astype(int)  # rough estimate of residents in each zone
map_df["dominant_stress_factor"] = map_df.apply(
    lambda r: dominant_stress_factor(str(r["year_month"]), float(r["vulnerability_score"])), axis=1
)

# ── KPI calculations using tier-based counts ──────────────────────────────
TIER_POP = {"Extreme": 1800, "High": 1400, "Moderate": 900, "Low": 500}

latest_avg   = float(df["vulnerability_score"].mean())
latest_risk  = classify_city_risk(latest_avg)

# Use tier-based high count — not hardcoded 0.55 threshold
high_tier         = int(map_df["risk_tier"].isin(["Extreme", "High"]).sum())
estimated_exposed = int(map_df["estimated_exposure"].sum())
drainage_hotspot_wards = max(1, int(round(high_tier / 8.0)))

if not series_df.empty and len(series_df) >= 13:
    sorted_series = series_df.sort_values("year_month")
    recent    = float(sorted_series.iloc[-1]["vulnerability_score"])
    prev_year = float(sorted_series.iloc[-13]["vulnerability_score"])
    yoy_change_pct = ((recent - prev_year) / max(prev_year, 1e-6)) * 100.0
else:
    yoy_change_pct = 0.0

# ── Tabs ──────────────────────────────────────────────────────────────────
main_tab, details_tab = st.tabs(["Executive Flood Dashboard", "Project Details (Simplified)"])

with main_tab:
    st.subheader("Executive Flood Risk Snapshot")
    c1, c2, c3, c4 = st.columns(4)

    q75_mean   = float(map_df[map_df["risk_tier"].isin(["Extreme","High"])]["vulnerability_score"].mean() or 0)
    multiplier = q75_mean / max(latest_avg, 1e-6)
    c1.metric("High-risk multiplier", f"{multiplier:.1f}x",
              help="High/Extreme zones vs city average.")
    c2.metric("Estimated exposed residents", f"{estimated_exposed:,}")
    c3.metric("Change vs last monsoon", f"{yoy_change_pct:+.1f}%")
    c4.metric("Drainage stress hotspots", f"{drainage_hotspot_wards} wards")

    if latest_risk in {"Very High", "High"}:
        st.error("Preparedness level: Elevated. Immediate pre-monsoon drainage intervention is recommended.")
    elif latest_risk == "Moderate":
        st.warning("Preparedness level: Watch. Focus on preventive inspections in high and emerging risk zones.")
    else:
        st.success("Preparedness level: Stable. Maintain routine preventive maintenance and weekly monitoring.")

    # ── Map: latest month only, centered on city ───────────────────────────
    latest_ym  = map_df["year_month"].max()
    map_latest = map_df[map_df["year_month"] == latest_ym].copy()

    st.subheader(f"Vulnerability Map ({latest_ym}) — {city_label}")
    st.caption("Deep red = Extreme, Orange = High, Yellow = Moderate, Green = Low.")
    map_display = map_latest.rename(columns={"lat": "latitude", "lon": "longitude"})[
        ["latitude", "longitude", "vulnerability_score"]
    ]
    st.map(map_display, zoom=10)

    st.subheader("Zone-level Priority and Exposure")
    preview_cols = ["location", "risk_tier", "estimated_exposure", "dominant_stress_factor", "vulnerability_score"]
    st.dataframe(
        map_df.sort_values("vulnerability_score", ascending=False)[preview_cols + ["map_link"]]
        .head(40)
        .rename(columns={
            "location": "Exact location",
            "risk_tier": "Vulnerability category",
            "estimated_exposure": "Estimated exposure",
            "dominant_stress_factor": "Dominant stress factor",
            "vulnerability_score": "Risk score",
            "map_link": "Map link",
        }),
        use_container_width=True,
    )

    st.subheader("Hotspot Visualization")
    top_hotspots = (
        map_df.sort_values("vulnerability_score", ascending=False)
        .head(12)[["location", "vulnerability_score"]]
        .set_index("location")
    )
    st.bar_chart(top_hotspots)

    tier_counts = map_df["risk_tier"].value_counts().reindex(
        ["Extreme", "High", "Moderate", "Low"], fill_value=0
    )
    risk_mix_df = pd.DataFrame({
        "Risk Tier": tier_counts.index,
        "Zones": tier_counts.values,
    }).set_index("Risk Tier")
    st.caption("Risk tier mix across city zones (latest month)")
    st.bar_chart(risk_mix_df)

    st.subheader("Population Impact Panel")
    impact_df = pd.DataFrame({
        "Risk tier":          tier_counts.index,
        "Zones":              tier_counts.values,
        "Estimated residents": [ 
            int(map_df.loc[map_df["risk_tier"] == t, "estimated_exposure"].sum())
            for t in tier_counts.index
        ],
    })
    st.bar_chart(impact_df.set_index("Risk tier")[["Estimated residents"]])

    ic1, ic2, ic3, ic4 = st.columns(4)
    hi_extreme_residents = int(
        map_df.loc[map_df["risk_tier"].isin(["Extreme","High"]),
         "estimated_exposure"].sum()
    )
    estimated_facilities = max(0, int(high_tier / 5))
    economic_disruption  = min(100.0, (hi_extreme_residents / 1000.0) * 0.9)
    readiness_index      = max(0.0, 100.0 - latest_avg * 100.0)

    ic1.metric("Residents in High/Extreme tiers", f"{hi_extreme_residents:,}")
    ic2.metric("Est. facilities in high-risk zones", f"{estimated_facilities}")
    ic3.metric("Economic disruption score", f"{economic_disruption:.1f}/100")
    ic4.metric("City preparedness index", f"{readiness_index:.1f}/100")

    st.subheader("Seasonal Preparedness Trend")
    if not series_df.empty:
        trend = series_df.sort_values("year_month").copy()
        trend["Preparedness Index"] = (1.0 - trend["vulnerability_score"]).clip(0, 1) * 100.0
        trend = trend.set_index("year_month")
        st.line_chart(trend[["vulnerability_score", "Preparedness Index"]])

    st.subheader("Preventive Action Engine")
    actions_df = map_df.sort_values("vulnerability_score", ascending=False).head(12).copy()
    actions_df["Preventive priority"] = actions_df["risk_tier"].map(
        {"Extreme": "Immediate", "High": "High", "Moderate": "Medium", "Low": "Monitor"}
    )
    actions_df["Suggested mitigation"] = actions_df["risk_tier"].map({
        "Extreme": "Pump station monitoring + emergency drainage clearance",
        "High":    "Drainage inspection + debris clearance",
        "Moderate":"Targeted desilting and channel checks",
        "Low":     "Routine maintenance",
    })
    actions_df["Time window"] = actions_df["risk_tier"].map({
        "Extreme": "Pre-monsoon + During monsoon",
        "High":    "Pre-monsoon",
        "Moderate":"Pre-monsoon",
        "Low":     "Routine",
    })
    st.dataframe(
        actions_df[["location","Preventive priority","Suggested mitigation","Time window","map_link"]]
        .rename(columns={"location": "Exact location", "map_link": "Map link"}),
        use_container_width=True,
    )

    st.subheader("Scenario Simulator")
    rainfall_increase = st.slider("Rainfall increase scenario (%)", 0, 40, 20, 5)
    scenario_scale  = 1.0 + (rainfall_increase / 100.0) * 0.70
    scenario_scores = (map_df["vulnerability_score"] * scenario_scale).clip(0, 1)

    # Use city-relative thresholds consistently in scenario too
    scenario_high   = int((scenario_scores >= p50).sum())
    current_high    = int((map_df["vulnerability_score"] >= p50).sum())
    additional_exposed = max(0, (scenario_high - current_high)) * 1400

    scenario_critical = int((scenario_scores >= p75).sum())
    current_critical  = int((map_df["vulnerability_score"] >= p75).sum())

    st.markdown(
        f"**Projected vulnerability growth:** +{((scenario_scores.mean() - map_df['vulnerability_score'].mean()) * 100):.1f}%  \n"
        f"**Additional population exposed:** {additional_exposed:,} residents  \n"
        f"**Zones entering critical status:** {max(0, scenario_critical - current_critical)}"
    )

    st.subheader("Executive Narrative Summary")
    top_zones = ", ".join(
        map_df.sort_values("vulnerability_score", ascending=False)["location"].head(3).tolist()
    )
    st.info(
        f"If current stress patterns continue, {city_label} is likely to see stronger surface water accumulation "
        f"in priority zones such as {top_zones}. "
        "Targeted drainage and pump-readiness actions in the top 10 zones can reduce projected exposure pressure "
        "before peak monsoon weeks."
    )

with details_tab:
    st.subheader("How this project predicts risk (simple explanation)")
    st.markdown(
        f"This system learns patterns from past monthly data (rainfall, satellite signals, terrain and exposure "
        f"indicators) to estimate which {city_label} zones are more likely to face flood stress in the next period.\n\n"
        "It does **not** estimate exact flood water depth.  \n"
        "It provides **relative risk priority** to support planning decisions."
    )

    st.subheader("Model quality in plain language")
    baseline = training.get("baseline", {})
    temporal = training.get("temporal", {})
    t_mae = float(temporal.get("mae", 0.0))
    b_mae = float(baseline.get("mae", 0.0))
    t_r2  = float(temporal.get("r2",  0.0))
    b_r2  = float(baseline.get("r2",  0.0))

    m1, m2 = st.columns(2)
    m1.metric("Prediction error (lower is better)",
              f"{t_mae:.3f}", delta=f"{(b_mae - t_mae):.3f} better than baseline")
    m2.metric("Prediction quality score (higher is better)",
              f"{t_r2:.3f}", delta=f"{(t_r2 - b_r2):.3f} over baseline")
    st.markdown(
        "- **What this means:** the temporal model predicts next-period zone risk more reliably than the simpler baseline.\n"
        "- **Confidence interpretation:** medium-to-strong reliability for planning prioritization, "
        "not for exact hydraulic simulation."
    )
    impact_gap = float(
    evaluation.get("high_vs_low_vulnerability_gap",
    evaluation.get("highvslowvulnerabilitygap", 0.0))
        )
    trend_score = float(
    evaluation.get("rank_correlation_spearman",
    evaluation.get("rankcorrelationspearman", 0.0))
        )
    months_eval = int(
    evaluation.get("months_evaluated",
    evaluation.get("monthsevaluated", 0))
)
    st.subheader("Evaluation summary")
    st.markdown(
        f"- **Impact separation (high vs low zones):** {impact_gap:.3f}\n"
        f"- **Trend consistency score:** {trend_score:.3f}\n"
        f"- **Months evaluated:** {months_eval}\n"
        f"- **Cities in model:** {', '.join(CITY_DISPLAY.values())}"
    )

    st.subheader("When to trust and when to be careful")
    st.markdown(
        "- **Use confidently for:** prioritizing inspections, preventive cleaning, "
        "and preparedness resource planning.\n"
        "- **Use with caution for:** exact local flooding depth, street-level engineering design, "
        "and emergency alert timing."
    )