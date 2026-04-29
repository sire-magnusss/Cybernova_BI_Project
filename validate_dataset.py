"""
CyberNova Synthetic Dataset Validator

This script checks whether the generated dataset is realistic enough for BI dashboard use.
"""

from __future__ import annotations

import pandas as pd


ENRICHED_PATH = "data/output/cybernova_enriched_logs.csv"
SUMMARY_PATH = "data/output/generation_summary.csv"


def validate_dataset() -> None:
    df = pd.read_csv(ENRICHED_PATH, parse_dates=["timestamp"])
    summary = pd.read_csv(SUMMARY_PATH)

    print("\n==============================")
    print("CYBERNOVA DATASET VALIDATION")
    print("==============================")

    print(f"\nTotal requests: {len(df):,}")
    print(f"Unique sessions: {df['session_id'].nunique():,}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")

    print("\nTop countries:")
    print(df["country"].value_counts(normalize=True).mul(100).round(2).head(10).astype(str) + "%")

    print("\nTop services:")
    print(df["service_name"].value_counts().head(10))

    print("\nStatus code distribution:")
    print(df["status_code"].value_counts(normalize=True).mul(100).round(2).astype(str) + "%")

    print("\nSegment distribution:")
    print(df.drop_duplicates("session_id")["segment"].value_counts(normalize=True).mul(100).round(2).astype(str) + "%")

    human_sessions = df.loc[~df["is_bot"]].drop_duplicates("session_id")
    warm_lead_events = df["is_warm_lead"].sum()
    warm_lead_rate = warm_lead_events / max(len(human_sessions), 1)

    print(f"\nWarm lead events: {warm_lead_events:,}")
    print(f"Warm lead rate per human session: {warm_lead_rate:.2%}")

    bot_ratio = df["is_bot"].mean()
    print(f"Bot request ratio: {bot_ratio:.2%}")

    print("\nCampaign periods generated:")
    print(df.loc[df["is_campaign_period"], ["date", "campaign_name"]].drop_duplicates().head(20))

    print("\nAnomalies generated:")
    print(df.loc[df["is_anomaly"], ["date", "anomaly_name", "uri", "status_code"]].drop_duplicates().head(30))

    print("\nDaily request summary:")
    print(summary[["date", "actual_requests", "campaign_name", "anomaly_names"]].head())
    print("...")
    print(summary[["date", "actual_requests", "campaign_name", "anomaly_names"]].tail())

    print("\nValidation notes:")
    if 0.01 <= warm_lead_rate <= 0.08:
        print("PASS: Warm lead rate is plausible for a B2B SaaS-style website.")
    else:
        print("CHECK: Warm lead rate may be too low/high. Adjust demo probabilities in config.yaml.")

    if 0.05 <= bot_ratio <= 0.18:
        print("PASS: Bot traffic ratio is realistic.")
    else:
        print("CHECK: Bot traffic ratio may be unrealistic. Adjust bot_ratio_min/max.")

    print("\nValidation complete.")


if __name__ == "__main__":
    validate_dataset()