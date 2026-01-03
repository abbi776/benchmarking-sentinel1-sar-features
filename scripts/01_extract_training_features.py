#!/usr/bin/env python3
"""
01_extract_training_features.py

Polygon-based Sentinel-1 SAR feature extraction.

Creates a single feature table (LORO-ready) with:
- unique_id
- class labels
- seasonal Sentinel-1 features

Assumes all rasters are already projected to EPSG:3577.
"""

import os
import argparse
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import rasterio.mask
from shapely.geometry import mapping


REFERENCE_CRS = "EPSG:3577"

BAND_KEYS = [
    "VV_dB","VH_dB","NDPI","NRPB","PR","XPR","RVI",
    "SUM","DIFF","PROD","VDDPI","LOG_RATIO",
    "GLCM_ASM_VV","GLCM_CORR_VV","GLCM_VAR_VV",
    "GLCM_IDM_VV","GLCM_SUMAVE_VV","GLCM_ENTROPY_VV","GLCM_CONTRAST_VV",
    "GLCM_ASM_VH","GLCM_CORR_VH","GLCM_VAR_VH",
    "GLCM_IDM_VH","GLCM_SUMAVE_VH","GLCM_ENTROPY_VH","GLCM_CONTRAST_VH",
]


def assert_crs_3577(src, path):
    """Ensure raster CRS matches reference CRS."""
    if src.crs is None:
        raise RuntimeError(f"{path} has no CRS defined")

    if src.crs.to_string() != REFERENCE_CRS:
        raise RuntimeError(
            f"{path} CRS is {src.crs}, expected {REFERENCE_CRS}. "
            "Reproject upstream (GEE or GDAL)."
        )


def zonal_mean(src, geom):
    """Return zonal mean across all bands."""
    out, _ = rasterio.mask.mask(src, [geom], crop=True)
    arr = out.astype("float32")

    if src.nodata is not None:
        arr[arr == src.nodata] = np.nan

    means = np.nanmean(arr, axis=(1, 2))

    return None if np.all(np.isnan(means)) else means


def extract_features(labels_path, seasons, out_path,
                     id_col, class_col, classval_col, valid_frac):

    gdf = gpd.read_file(labels_path).to_crs(REFERENCE_CRS)
    rows = {}

    for season, tif in seasons.items():

        if not os.path.exists(tif):
            print(f"⚠️ Missing raster: {tif}")
            continue

        with rasterio.open(tif) as src:
            assert_crs_3577(src, tif)

            for _, r in gdf.iterrows():
                uid = r[id_col]
                geom = mapping(r.geometry)

                try:
                    means = zonal_mean(src, geom)
                    if means is None:
                        continue

                    # skip mostly-nodata polygons
                    if np.isfinite(means).sum() < valid_frac * len(means):
                        continue

                    if uid not in rows:
                        rows[uid] = {
                            id_col: uid,
                            class_col: r[class_col],
                            classval_col: r[classval_col],
                        }

                    for i, key in enumerate(BAND_KEYS):
                        rows[uid][f"{season}_{key}"] = (
                            float(means[i]) if i < len(means) else np.nan
                        )

                except Exception as e:
                    print(f"❌ {uid} / {season}: {e}")

    df = pd.DataFrame.from_dict(rows, orient="index").reset_index(drop=True)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_excel(out_path, index=False)

    print(f"✅ Saved: {out_path}")
    print(f"Rows: {len(df)} | Columns: {len(df.columns)}")


def cli():
    parser = argparse.ArgumentParser()

    parser.add_argument("--labels", required=True, help="Training polygons shapefile")
    parser.add_argument("--out", required=True, help="Output Excel file")

    parser.add_argument("--autumn")
    parser.add_argument("--spring")
    parser.add_argument("--summer")
    parser.add_argument("--winter")

    parser.add_argument("--id_col", default="unique_id")
    parser.add_argument("--class_col", default="classname")
    parser.add_argument("--classval_col", default="classvalue")
    parser.add_argument("--valid_frac", type=float, default=0.7)

    args = parser.parse_args()

    seasons = {
        k: v for k, v in dict(
            autumn=args.autumn,
            spring=args.spring,
            summer=args.summer,
            winter=args.winter,
        ).items() if v
    }

    extract_features(
        labels_path=args.labels,
        seasons=seasons,
        out_path=args.out,
        id_col=args.id_col,
        class_col=args.class_col,
        classval_col=args.classval_col,
        valid_frac=args.valid_frac,
    )


if __name__ == "__main__":
    cli()
