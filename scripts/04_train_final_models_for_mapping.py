#!/usr/bin/env python3
"""
04_train_final_models_for_mapping.py

Trains the FINAL production models for
wall-to-wall Sentinel-1 classification.

Uses:
 - All polygons
 - All features (VV+VH + Indices + GLCM)

Outputs (per model):
 - joblib model file
 - JSON metadata
 - ALL_FEATURES_ORDER.json
"""

import os
import re
import json
import argparse
import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from joblib import dump


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def extract_polygon(uid):
    m = re.search(r"_P(\d+)_", str(uid))
    return int(m.group(1)) if m else np.nan


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


# --------------------------------------------------
# Main training
# --------------------------------------------------
def train_final_models(
    data_path,
    out_dir,
    label_col="classname",
    id_col="unique_id"
):

    os.makedirs(out_dir, exist_ok=True)

    print(f"Loading training table: {data_path}")
    df = pd.read_excel(data_path)

    # polygon extraction (for consistency, not used directly)
    df["polygon"] = df[id_col].apply(extract_polygon)
    df = df.dropna(subset=["polygon"])
    df["polygon"] = df["polygon"].astype(int)

    feature_groups = build_feature_groups(df, label_col, id_col)

    FINAL_GROUP = "6) All Features (VV+VH + Indices + GLCM)"
    final_features = [
        f for f in feature_groups[FINAL_GROUP]
        if f in df.columns
    ]

    print(f"Final feature count: {len(final_features)}")

    y = df[label_col].astype("category")
    y_codes = y.cat.codes.values

    X_full = df[final_features].values

    # Save feature order (needed when applying model to rasters)
    feature_order_path = os.path.join(out_dir, "ALL_FEATURES_ORDER.json")
    with open(feature_order_path, "w") as f:
        json.dump(final_features, f, indent=2)

    print(f"Saved feature order → {feature_order_path}")

    final_models = {
        "RF": RandomForestClassifier(
            n_estimators=600,
            n_jobs=-1,
            class_weight="balanced_subsample",
            random_state=42,
        ),
        "XGB": XGBClassifier(
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
        ),
        "SVM": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    SVC(
                        C=10,
                        kernel="rbf",
                        gamma="scale",
                        class_weight="balanced",
                        probability=False,
                    ),
                ),
            ]
        ),
    }

    # Train & save
    for model_name, model in final_models.items():
        print(f"\nTraining FINAL {model_name}...")
        model.fit(X_full, y_codes)

        model_path = os.path.join(
            out_dir, f"{model_name}_ALL_FEATURES_FINAL.joblib"
        )
        dump(model, model_path)

        print(f"Saved model → {model_path}")

        meta = {
            "model": model_name,
            "feature_group": FINAL_GROUP,
            "n_features": len(final_features),
            "features": final_features,
            "label_column": label_col,
            "training_data": "All polygons (full dataset)",
            "intended_use": "Wall-to-wall mapping",
            "notes": "Trained after LOPO CV; production models",
        }

        meta_path = model_path.replace(".joblib", ".json")
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        print(f"Saved metadata → {meta_path}")


# --------------------------------------------------
# CLI
# --------------------------------------------------
def cli():
    parser = argparse.ArgumentParser(
        description="Train FINAL models for S1 wall-to-wall mapping."
    )

    parser.add_argument("--data", required=True,
                        help="Excel file containing S1 polygon features")
    parser.add_argument("--out_dir", required=True,
                        help="Where to save final models + metadata")
    parser.add_argument("--label_col", default="classname")
    parser.add_argument("--id_col", default="unique_id")

    args = parser.parse_args()

    train_final_models(
        data_path=args.data,
        out_dir=args.out_dir,
        label_col=args.label_col,
        id_col=args.id_col,
    )


if __name__ == "__main__":
    cli()
