"""
00_prepare_feature_rasters.py

Prepare Sentinel-1 ML feature rasters.

Pipeline:
1. Mosaic exported GEE tiles
2. Clip mosaic to wetland polygons
3. Remove alpha band
4. Assign descriptive band names

Run:
python 00_prepare_feature_rasters.py \
  --tiles data/tiles/*.tif \
  --roi_dir data/wetlands \
  --out_dir data/processed/2025_winter
"""

import argparse
import glob
import os

import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
import fiona


BAND_NAMES = [
    "VV_dB",
    "VH_dB",
    "NDPI",
    "NRPB",
    "PR",
    "XPR",
    "RVI",
    "SUM",
    "DIFF",
    "PROD",
    "VDDPI",
    "LOG_RATIO",
    "GLCM_ASM_VV",
    "GLCM_CORR_VV",
    "GLCM_VAR_VV",
    "GLCM_IDM_VV",
    "GLCM_SUMAVE_VV",
    "GLCM_ENTROPY_VV",
    "GLCM_CONTRAST_VV",
    "GLCM_ASM_VH",
    "GLCM_CORR_VH",
    "GLCM_VAR_VH",
    "GLCM_IDM_VH",
    "GLCM_SUMAVE_VH",
    "GLCM_ENTROPY_VH",
    "GLCM_CONTRAST_VH",
]


def mosaic_tiles(tile_paths):
    """Mosaic multiple rasters into a single raster."""
    sources = [rasterio.open(p) for p in tile_paths]
    mosaic, transform = merge(sources)

    profile = sources[0].profile
    profile.update(
        height=mosaic.shape[1],
        width=mosaic.shape[2],
        transform=transform,
        compress="lzw",
        tiled=True,
        bigtiff="YES",
    )

    for src in sources:
        src.close()

    return mosaic, profile


def write_raster(path, array, profile):
    """Save array to GeoTIFF."""
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(array)

        if array.shape[0] == len(BAND_NAMES):
            dst.descriptions = tuple(BAND_NAMES)


def clip_to_polygon(mosaic, profile, shp_path, out_path):
    """Clip mosaic to shapefile extent."""
    with fiona.open(shp_path, "r") as shp:
        geoms = [feat["geometry"] for feat in shp]

    out, out_transform = mask(
        mosaic,
        geoms,
        crop=True,
        nodata=0,
        filled=True
    )

    clipped_profile = profile.copy()
    clipped_profile.update(
        height=out.shape[1],
        width=out.shape[2],
        transform=out_transform,
    )

    write_raster(out_path, out, clipped_profile)


def main(args):
    os.makedirs(args.out_dir, exist_ok=True)

    tile_paths = sorted(glob.glob(args.tiles))
    if not tile_paths:
        raise FileNotFoundError(f"No tiles found for pattern: {args.tiles}")

    print(f"Found {len(tile_paths)} tiles. Creating mosaic…")
    mosaic, mosaic_profile = mosaic_tiles(tile_paths)

    # Force dropping alpha if present
    if mosaic.shape[0] > len(BAND_NAMES):
        mosaic = mosaic[: len(BAND_NAMES), :, :]

    # Process polygons
    shp_files = sorted(glob.glob(os.path.join(args.roi_dir, "*.shp")))
    if not shp_files:
        raise FileNotFoundError(f"No shapefiles found in {args.roi_dir}")

    print(f"Found {len(shp_files)} polygons")

    for shp in shp_files:
        name = os.path.splitext(os.path.basename(shp))[0]
        out_path = os.path.join(args.out_dir, f"{name}.tif")
        print(f"Clipping → {name}")

        clip_to_polygon(mosaic, mosaic_profile, shp, out_path)

    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--tiles",
        required=True,
        help="Glob pattern for Sentinel-1 exported tiles (e.g., data/tiles/*.tif)",
    )

    parser.add_argument(
        "--roi_dir",
        required=True,
        help="Directory containing shapefiles",
    )

    parser.add_argument(
        "--out_dir",
        required=True,
        help="Output directory",
    )

    args = parser.parse_args()
    main(args)
