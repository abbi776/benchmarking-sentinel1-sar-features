#!/usr/bin/env python3
# ============================================================
# YEARLY STACK BUILDER — FEATURE-ORDER SAFE VERSION
# ============================================================

"""
Builds yearly Sentinel-1 feature stacks by merging:

    autumn + spring + summer + winter

into a single multi-band raster — with the **exact same band order**
used during model training.

Output:
    Data/Images/Yearly_stack/<YEAR>_stack_tiled/PxANAE_YEARLY_YEAR_STACK.tif
"""

import os
import json
import argparse
import rasterio
from collections import OrderedDict


SEASONS = ["autumn", "spring", "summer", "winter"]


# ------------------------------------------------------------
# main
# ------------------------------------------------------------
def build_yearly_stacks(base_images, model_dir, year, polygons, out_dir):

    os.makedirs(out_dir, exist_ok=True)

    print("📖 Loading feature schema (model band order)...")

    with open(os.path.join(model_dir, "ALL_FEATURES_ORDER.json")) as f:
        final_features = json.load(f)

    print(f"✔ Loaded {len(final_features)} features")

    # ---- build season lookup ----
    season_features = OrderedDict()
    for s in SEASONS:
        season_features[s] = [
            f for f in final_features if f.startswith(s + "_")
        ]

    print("\n📊 Feature count per season:")
    for s, feats in season_features.items():
        print(f"  {s:<7}: {len(feats)}")

    assert (
        sum(len(v) for v in season_features.values()) == len(final_features)
    ), "❌ Seasonal split does not sum to total feature count"

    # ========================================================
    # build stacks per polygon
    # ========================================================
    for pid in polygons:
        print("\n" + "=" * 60)
        print(f"🔄 Processing Polygon {pid}")

        season_src = {}

        for s in SEASONS:
            path = os.path.join(
                base_images,
                str(year),
                f"Polygon {pid} Wetlands",
                f"P{pid}ANAE_{s}_{year}.tif",
            )

            if not os.path.exists(path):
                raise FileNotFoundError(path)

            season_src[s] = rasterio.open(path)
            print(f"✔ Loaded {os.path.basename(path)}")

        out_path = os.path.join(
            out_dir, f"P{pid}ANAE_YEARLY_{year}_STACK.tif"
        )

        profile = season_src["autumn"].profile.copy()
        profile.update(
            count=len(final_features),
            dtype="float32",
            compress="lzw",
            tiled=True,
            blockxsize=256,
            blockysize=256,
            BIGTIFF="YES",
        )

        with rasterio.open(out_path, "w", **profile) as dst:
            for out_idx, feat in enumerate(final_features):

                season = feat.split("_")[0]
                band_idx = season_features[season].index(feat) + 1

                data = season_src[season].read(band_idx)

                dst.write(data, out_idx + 1)
                dst.set_band_description(out_idx + 1, feat)

        for src in season_src.values():
            src.close()

        print(f"✅ Written yearly stack → {out_path}")

    print("\n🎉 ALL YEARLY STACKS COMPLETED SUCCESSFULLY")


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
def cli():
    parser = argparse.ArgumentParser(
        description="Build yearly Sentinel-1 feature stacks."
    )

    parser.add_argument("--images_dir", required=True)
    parser.add_argument("--model_dir", required=True)
    parser.add_argument("--year", required=True, type=int)
    parser.add_argument(
        "--polygons",
        nargs="+",
        type=int,
        default=[1, 2, 3, 4, 5],
    )
    parser.add_argument("--out", required=True)

    args = parser.parse_args()

    build_yearly_stacks(
        base_images=args.images_dir,
        model_dir=args.model_dir,
        year=args.year,
        polygons=args.polygons,
        out_dir=args.out,
    )


if __name__ == "__main__":
    cli()
