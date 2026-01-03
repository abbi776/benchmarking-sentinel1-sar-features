import os
import json
import joblib
import rasterio
import geopandas as gpd
import numpy as np
from rasterio.features import rasterize

# --------------------------------------------------
# FIXED CONFIG (2025 ONLY)
# --------------------------------------------------
YEAR = 2025
POLYGONS = [1, 2, 3, 4, 5]

MODEL_NAME = "XGB"      # RF | XGB | SVM

MODEL_DIR = "/content/drive/MyDrive/GEE_Sentinel_1_Analysis/Data/Models/wall_to_wall_mapping_models"
BASE_STACK_DIR = "/content/drive/MyDrive/GEE_Sentinel_1_Analysis/Data/Images/Yearly_stack"
WETLAND_DIR = "/content/drive/MyDrive/GEE_Sentinel_1_Analysis/Data/ANAE wetlands"
RESULTS_BASE = "/content/drive/MyDrive/GEE_Sentinel_1_Analysis/Results"

MODEL_PATH = f"{MODEL_DIR}/{MODEL_NAME}_ALL_FEATURES_FINAL.joblib"
FEATURE_SCHEMA = f"{MODEL_DIR}/ALL_FEATURES_ORDER.json"

OUT_DTYPE = "int16"
OUT_NODATA = -1

# Fix label ordering if needed
CLASS_REMAP = {
    0: 1,   # NFFP
    1: 0,   # RRG
    2: 2    # Water
}

print("🧠 Loading model...")
model = joblib.load(MODEL_PATH)

print("📑 Loading feature schema...")
with open(FEATURE_SCHEMA) as f:
    final_features = json.load(f)

assert model.n_features_in_ == len(final_features), \
    "❌ Feature count mismatch between model and schema"

print(f"✔ Model expects {model.n_features_in_} features")


def classify_yearly_stack_masked(stack_path, wetland_shp, out_path):
    print(f"\n🚀 Processing {os.path.basename(stack_path)}")

    # ---------- read raster ----------
    with rasterio.open(stack_path) as src:
        arr = src.read().astype("float32")
        band_names = list(src.descriptions)
        profile = src.profile.copy()
        transform = src.transform
        crs = src.crs

    # ---------- order safety ----------
    if band_names != final_features:
        raise RuntimeError("❌ Raster feature order does NOT match training schema")

    b, h, w = arr.shape
    flat = arr.reshape(b, -1).T

    # ---------- mask wetlands ----------
    wetland = gpd.read_file(wetland_shp).to_crs(crs)

    wet_mask = rasterize(
        [(geom, 1) for geom in wetland.geometry],
        out_shape=(h, w),
        transform=transform,
        fill=0,
        dtype="uint8"
    ).reshape(-1)

    valid = (wet_mask == 1) & np.all(np.isfinite(flat), axis=1)
    X = flat[valid]

    print(f"✔ Pixels classified: {X.shape[0]}")

    # ---------- classify ----------
    y = np.full(flat.shape[0], OUT_NODATA, dtype=OUT_DTYPE)

    if X.size > 0:
        raw_pred = model.predict(X)
        fixed_pred = np.vectorize(CLASS_REMAP.get)(raw_pred)
        y[valid] = fixed_pred.astype(OUT_DTYPE)

    classified = y.reshape(h, w)

    # ---------- write output ----------
    profile.update(
        count=1,
        dtype=OUT_DTYPE,
        nodata=OUT_NODATA,
        compress="lzw",
        tiled=True,
        blockxsize=256,
        blockysize=256,
    )

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(classified, 1)

    print(f"✅ Saved → {out_path}")


# --------------------------------------------------
STACK_DIR = f"{BASE_STACK_DIR}/{YEAR}_stack_tiled"
OUT_DIR = f"{RESULTS_BASE}/{MODEL_NAME}/{YEAR}_Predictions_FINAL"
os.makedirs(OUT_DIR, exist_ok=True)

for pid in POLYGONS:
    stack = f"{STACK_DIR}/P{pid}ANAE_YEARLY_{YEAR}_STACK.tif"
    wetland = f"{WETLAND_DIR}/P{pid}ANAEWetlands.shp"
    out = f"{OUT_DIR}/P{pid}ANAE_{YEAR}_{MODEL_NAME}_CLASSIFIED.tif"

    if not os.path.exists(stack):
        print(f"⚠️ Missing stack → {stack}")
        continue

    classify_yearly_stack_masked(stack, wetland, out)

print("\n🎉 2025 PREDICTIONS COMPLETE")
