#!/usr/bin/env python3
"""
03_feature_importance_shap.py

Computes SHAP-based global feature importance for the
Sentinel-1 WPE classification pipeline.

Outputs:
- figures/global_shap_importance.png
- figures/seasonal_shap_importance.png
- tables/seasonal_shap_scores.csv
"""

import os
import re
import shap
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from xgboost import XGBClassifier


# ---------------------------------------------------
# Polygon extractor (same as ablation script)
# ---------------------------------------------------
def extract_polygon(uid):
    m = re.search(r"_P(\d+)_", str(uid))
    return int(m.group(1)) if m else np.nan


# ---------------------------------------------------
# Build feature groups
# ---------------------------------------------------
def build_feature_groups(df, label_col, id_col):
    all_cols = df.columns.tolist()

    baseline = [
        c for c in all_cols
        if ("VV_dB" in c or "VH_dB" in c) and ("GLCM" not in c)
    ]

    glcm = [c for c in all_cols if "GLCM" in c]

    exclude = {label_col, id_col, "polygon", "classvalue"}

    derived = [
        c for c in all_cols
        if (
            c not in baseline
            and c not in glcm
            and c not in exclude
            and pd.api.types.is_numeric_dtype(df[c])
        )
    ]

    groups = {
        "1) Baseline (VV+VH)": baseline,
        "2) Derived Indices": derived,
        "3) Texture (GLCM)": glcm,
        "4) VV+VH + Indices": baseline + derived,
        "5) VV+VH + GLCM": baseline + glcm,
        "6) All Features (VV+VH + Indices + GLCM)": baseline + derived + glcm,
    }

    return groups


# ---------------------------------------------------
# Pretty naming for SHAP plot labels
# ---------------------------------------------------
def pretty_feature_name(name):
    if not name or "_" not in name:
        return name

    season, rest = name.split("_", 1)
    season = season.capitalize()

    mapping = {
        "PROD": "Polarisation Product (VV×VH)",
        "SUM": "Polarisation Sum (VV+VH)",
        "DIFF": "Polarisation Difference (VV−VH)",
        "PR": "Polarisation Ratio (VV/VH)",
        "LOG_RATIO": "Log Ratio (VV/VH)",
        "RVI": "Radar Vegetation Index",

        "GLCM_ASM_VV": "GLCM ASM (VV)",
        "GLCM_VAR_VV": "GLCM Variance (VV)",
        "GLCM_CONTRAST_VV": "GLCM Contrast (VV)",
        "GLCM_CORR_VV": "GLCM Correlation (VV)",

        "GLCM_ASM_VH": "GLCM ASM (VH)",
        "GLCM_VAR_VH": "GLCM Variance (VH)",
        "GLCM_CONTRAST_VH": "GLCM Contrast (VH)",
        "GLCM_CORR_VH": "GLCM Correlation (VH)",
    }

    return f"{season} – {mapping.get(rest, rest)}"


# ---------------------------------------------------
# Main SHAP pipeline
# ---------------------------------------------------
def run_shap(data_path, out_dir, label_col="classname", id_col="unique_id"):

    os.makedirs(out_dir, exist_ok=True)
    figs_dir = os.path.join(out_dir, "figures")
    tables_dir = os.path.join(out_dir, "tables")

    os.makedirs(figs_dir, exist_ok=True)
    os.makedirs(tables_dir, exist_ok=True)

    print(f"Loading data: {data_path}")
    df = pd.read_excel(data_path)

    df["polygon"] = df[id_col].apply(extract_polygon)
    df = df.dropna(subset=["polygon"])
    df["polygon"] = df["polygon"].astype(int)

    feature_groups = build_feature_groups(df, label_col, id_col)

    # --- choose: All features ---
    features = feature_groups["6) All Features (VV+VH + Indices + GLCM)"]
    features = [f for f in features if f in df.columns]

    X = df[features]
    y = df[label_col].astype("category").cat.codes

    # ------------------------------
    # Train XGB on full dataset
    # ------------------------------
    model = XGBClassifier(
        n_estimators=800,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="multi:softprob",
        eval_metric="mlogloss",
        tree_method="hist",
        n_jobs=-1,
        random_state=42,
    )

    model.fit(X, y)

    # ------------------------------
    # SHAP
    # ------------------------------
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X)

    shap_abs = np.mean(np.abs(shap_values.values), axis=2)

    # ------------------------------
    # SHAP dot plot
    # ------------------------------
    shap.summary_plot(
        shap_abs,
        X,
        plot_type="dot",
        max_display=20,
        show=False,
    )

    ax = plt.gca()
    new_labels = [pretty_feature_name(t.get_text()) for t in ax.get_yticklabels()]
    ax.set_yticklabels(new_labels)

    ax.set_xlabel("SHAP value (impact on model output)", fontsize=11)

    plt.suptitle("Global SHAP Feature Importance", fontsize=14, y=0.98)
    plt.tight_layout()

    out_fig1 = os.path.join(figs_dir, "global_shap_importance.png")
    plt.savefig(out_fig1, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved: {out_fig1}")

    # ------------------------------
    # Seasonal aggregation
    # ------------------------------
    feat_to_idx = {f: i for i, f in enumerate(features)}

    seasons = ["autumn", "spring", "summer", "winter"]
    season_scores = {}

    for s in seasons:
        idx = [feat_to_idx[f] for f in features if f.startswith(f"{s}_")]
        season_scores[s.title()] = shap_abs[:, idx].mean()

    season_df = (
        pd.DataFrame({
            "Season": season_scores.keys(),
            "Mean_Absolute_SHAP": season_scores.values(),
        })
        .sort_values("Mean_Absolute_SHAP", ascending=False)
    )

    out_csv = os.path.join(tables_dir, "seasonal_shap_scores.csv")
    season_df.to_csv(out_csv, index=False)

    print(f"Saved: {out_csv}")

    # ------------------------------
    # Bar plot
    # ------------------------------
    plt.figure(figsize=(6, 4))
    plt.bar(
        season_df["Season"],
        season_df["Mean_Absolute_SHAP"],
        color=["#d95f02", "#1b9e77", "#7570b3", "#e7298a"],
        edgecolor="black",
    )

    plt.ylabel("Mean |SHAP|", fontsize=11)
    plt.xlabel("Season", fontsize=11)
    plt.title("Seasonal Importance for WPE Detection", fontsize=13)
    plt.grid(axis="y", linestyle="--", alpha=0.5)

    out_fig2 = os.path.join(figs_dir, "seasonal_shap_importance.png")
    plt.tight_layout()
    plt.savefig(out_fig2, dpi=300)
    plt.close()

    print(f"Saved: {out_fig2}")


# ---------------------------------------------------
# CLI
# ---------------------------------------------------
def cli():
    parser = argparse.ArgumentParser(description="Compute SHAP feature importance.")

    parser.add_argument("--data", required=True,
                        help="Path to Excel feature file.")
    parser.add_argument("--out_dir", required=True,
                        help="Output directory for figures + tables.")
    parser.add_argument("--label_col", default="classname")
    parser.add_argument("--id_col", default="unique_id")

    args = parser.parse_args()

    run_shap(
        data_path=args.data,
        out_dir=args.out_dir,
        label_col=args.label_col,
        id_col=args.id_col,
    )


if __name__ == "__main__":
    cli()
