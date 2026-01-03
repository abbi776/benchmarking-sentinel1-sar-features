#!/usr/bin/env python3
"""
02_model_ablation_experiments.py

Runs Sentinel-1 feature ablation experiments with:
- Random Forest
- SVM (RBF)
- XGBoost

Using:
- LOPO cross-validation via polygon groups
- Six feature groups (VV/VH, indices, GLCM, and combinations)

Outputs:
- ablation_summary.csv   (mean + std metrics per model × feature-group)
- ablation_folds.csv     (per-fold metrics)
- Optional: trained models + JSON metadata for each ablation group
"""

import os
import re
import json
import argparse
import numpy as np
import pandas as pd

from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, cohen_kappa_score

from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from joblib import dump


# -------------------------------------------------------------------
# Polygon ID extraction from unique_id string
# -------------------------------------------------------------------
def extract_polygon(uid: str) -> int:
    """
    Example:
    'Redgum_P1_82' -> 1
    'Water_P2_146' -> 2
    """
    m = re.search(r"_P(\d+)_", str(uid))
    return int(m.group(1)) if m else np.nan


# -------------------------------------------------------------------
# Feature group builder
# -------------------------------------------------------------------
def build_feature_groups(df: pd.DataFrame,
                         label_col: str,
                         id_col: str) -> dict:
    all_cols = df.columns.tolist()

    # Baseline: VV / VH backscatter (exclude GLCM)
    baseline = [
        c for c in all_cols
        if (
            ("VV_dB" in c or "VH_dB" in c) and
            ("GLCM" not in c)
        )
    ]

    # Texture-only (GLCM)
    glcm = [c for c in all_cols if "GLCM" in c]

    # Columns to exclude from derived search
    exclude = {
        label_col,
        id_col,
        "polygon",
        "classvalue",
    }

    # Derived indices: everything numeric that is not baseline / GLCM / excluded
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

    print("Ablation feature counts:")
    for k, v in groups.items():
        print(f"{k:<45} -> {len(v)}")

    return groups


# -------------------------------------------------------------------
# Model factory
# -------------------------------------------------------------------
def get_models(random_state: int = 42) -> dict:
    rf = RandomForestClassifier(
        n_estimators=600,
        n_jobs=-1,
        class_weight="balanced_subsample",
        random_state=random_state,
    )

    xgb = XGBClassifier(
        n_estimators=800,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="multi:softprob",
        eval_metric="mlogloss",
        tree_method="hist",
        n_jobs=-1,
        random_state=random_state,
    )

    svm = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                SVC(
                    C=10,
                    kernel="rbf",
                    gamma="scale",
                    class_weight="balanced",
                ),
            ),
        ]
    )

    return {"RF": rf, "SVM": svm, "XGB": xgb}


# -------------------------------------------------------------------
# Main ablation experiment
# -------------------------------------------------------------------
def run_ablation(
    data_path: str,
    out_dir: str,
    label_col: str = "classname",
    id_col: str = "unique_id",
    save_models: bool = True,
    models_dir: str | None = None,
) -> None:
    os.makedirs(out_dir, exist_ok=True)
    if models_dir is None:
        models_dir = os.path.join(out_dir, "models")
    if save_models:
        os.makedirs(models_dir, exist_ok=True)

    # -------------------------
    # Load data
    # -------------------------
    print(f"Loading features from: {data_path}")
    df = pd.read_excel(data_path)
    print("Data shape:", df.shape)

    # -------------------------
    # Polygon group column (LOPO)
    # -------------------------
    df["polygon"] = df[id_col].apply(extract_polygon)
    df = df.dropna(subset=["polygon"])
    df["polygon"] = df["polygon"].astype(int)

    print("Polygons found:", sorted(df["polygon"].unique()))

    # -------------------------
    # Feature groups & models
    # -------------------------
    feature_groups = build_feature_groups(df, label_col, id_col)
    models = get_models()

    # Labels & group vector
    y = df[label_col].astype("category")
    y_codes = y.cat.codes.values
    groups = df["polygon"].values

    gkf = GroupKFold(n_splits=len(np.unique(groups)))

    summary_rows = []
    fold_rows = []

    # -------------------------
    # CV for each model × feature-group
    # -------------------------
    for model_name, model in models.items():
        print(f"\nRunning model: {model_name}")

        for ablation_name, feats in feature_groups.items():
            # Keep only existing columns
            feats = [f for f in feats if f in df.columns]
            if len(feats) == 0:
                print(f"  SKIP {ablation_name} (0 features)")
                continue

            X = df[feats].values
            accs, f1s, kaps = [], [], []

            for fold, (tr, te) in enumerate(
                gkf.split(X, y_codes, groups), start=1
            ):
                model.fit(X[tr], y_codes[tr])
                preds = model.predict(X[te])

                acc = accuracy_score(y_codes[te], preds)
                f1m = f1_score(y_codes[te], preds, average="macro")
                kap = cohen_kappa_score(y_codes[te], preds)

                accs.append(acc)
                f1s.append(f1m)
                kaps.append(kap)

                fold_rows.append(
                    {
                        "model": model_name,
                        "ablation": ablation_name,
                        "fold": fold,
                        "test_polygon": int(np.unique(groups[te])[0]),
                        "n_features": len(feats),
                        "accuracy": acc,
                        "macro_f1": f1m,
                        "kappa": kap,
                    }
                )

            summary_rows.append(
                {
                    "model": model_name,
                    "ablation": ablation_name,
                    "n_features": len(feats),
                    "mean_accuracy": float(np.mean(accs)),
                    "std_accuracy": float(np.std(accs, ddof=1)),
                    "mean_macro_f1": float(np.mean(f1s)),
                    "mean_kappa": float(np.mean(kaps)),
                }
            )

    # -------------------------
    # Save summary & fold-level CSVs
    # -------------------------
    summary_df = pd.DataFrame(summary_rows)
    fold_df = pd.DataFrame(fold_rows)

    summary_path = os.path.join(out_dir, "ablation_summary.csv")
    folds_path = os.path.join(out_dir, "ablation_folds.csv")

    summary_df.to_csv(summary_path, index=False)
    fold_df.to_csv(folds_path, index=False)

    print(f"\n✅ Saved summary: {summary_path}")
    print(f"✅ Saved per-fold metrics: {folds_path}")

    # -------------------------
    # Train final models on full data (optional)
    # -------------------------
    if save_models:
        print(f"\nTraining final models on full dataset (saving to {models_dir})")
        final_models = get_models()

        for model_name, model in final_models.items():
            for ablation_name, feats in feature_groups.items():

                feats = [f for f in feats if f in df.columns]
                if len(feats) == 0:
                    continue

                print(f"  FINAL {model_name} | {ablation_name}")

                X_full = df[feats].values
                y_full = y_codes

                model.fit(X_full, y_full)

                safe_ablation = (
                    ablation_name.replace(" ", "_")
                    .replace(")", "")
                    .replace("(", "")
                )
                model_path = os.path.join(
                    models_dir, f"{model_name}_{safe_ablation}.joblib"
                )

                dump(model, model_path)

                meta = {
                    "model": model_name,
                    "ablation": ablation_name,
                    "n_features": len(feats),
                    "features": feats,
                    "label_column": label_col,
                    "grouping": "polygon (LOPO)",
                    "note": "Trained on full dataset after LOPO CV",
                }

                meta_path = model_path.replace(".joblib", ".json")
                with open(meta_path, "w") as f:
                    json.dump(meta, f, indent=2)

        print("✅ Final models + metadata saved.")


# -------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------
def cli():
    parser = argparse.ArgumentParser(
        description="Run Sentinel-1 feature ablation experiments."
    )

    parser.add_argument(
        "--data",
        required=True,
        help="Path to feature Excel file (e.g., s1_features_all_LOPO.xlsx)",
    )
    parser.add_argument(
        "--out_dir",
        required=True,
        help="Output directory for CSVs (and models if enabled)",
    )
    parser.add_argument(
        "--label_col",
        default="classname",
        help="Column name for class label",
    )
    parser.add_argument(
        "--id_col",
        default="unique_id",
        help="Column name with unique IDs containing polygon info",
    )
    parser.add_argument(
        "--no_save_models",
        action="store_true",
        help="If set, do NOT save trained models",
    )
    parser.add_argument(
        "--models_dir",
        default=None,
        help="Directory to save models (defaults to <out_dir>/models)",
    )

    args = parser.parse_args()

    run_ablation(
        data_path=args.data,
        out_dir=args.out_dir,
        label_col=args.label_col,
        id_col=args.id_col,
        save_models=not args.no_save_models,
        models_dir=args.models_dir,
    )


if __name__ == "__main__":
    cli()
