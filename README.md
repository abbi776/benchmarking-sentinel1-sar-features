# 🌳 Benchmarking Sentinel-1 SAR Features for Woody Plant Encroachment Mapping

This repository provides an open-source, end-to-end framework for benchmarking Sentinel-1 SAR features and applying them to woody plant encroachment (WPE) mapping in floodplain wetlands.

The workflow integrates:

- Google Earth Engine (Sentinel-1 preprocessing & feature generation)
- Polarisation indices and SAR backscatter transformations
- GLCM texture metrics
- Machine learning (Random Forest, SVM, XGBoost)
- Spatial cross-validation (Leave-One-Polygon-Out)
- SHAP model interpretability
- Wall-to-wall mapping across multiple years

The goal is to evaluate which SAR feature groups best discriminate woody vegetation in floodplain environments.

---

## 🌱 Key Highlights

- GEE Sentinel-1 preprocessing (border noise masking, speckle filtering, ellipsoidal RTC)
- Unified SAR feature stack (indices + textures)
- Polygon-based feature extraction
- Structured feature ablation experiments
- RF vs SVM vs XGB benchmarking
- SHAP interpretability
- Wall-to-wall classification (2016 / 2018 / 2025)
- Reproducible, script-driven workflow

> Parts of the preprocessing pipeline build upon  
> **Mullissa et al. (2021) – Sentinel-1 ARD (GEE)**  
> https://github.com/adugnag/gee_s1_ard  
>  
> Proper credit is provided inside relevant scripts.

---

## 📂 Repository Structure

```text
benchmarking-sentinel1-sar-features/
│
├── gee/                         # GEE SAR preprocessing + feature scripts
│   ├── 00_utils_sar.js
│   ├── 01_border_noise.js
│   ├── 02_speckle_filter.js
│   ├── 03_rtc.js
│   ├── 04_feature_extraction.js
│   └── main_workflow.js
│
├── scripts/                     # Python analysis pipeline
│   ├── 00_prepare_feature_rasters.py
│   ├── 01_extract_training_features.py
│   ├── 02_model_ablation_experiments.py
│   ├── 03_feature_importance_shap.py
│   ├── 04_train_final_models_for_mapping.py
│   ├── 05_build_yearly_stacks.py
│   └── 06_apply_models_to_yearly_stacks.py
│
├── requirements.txt
├── LICENSE
├── .gitignore

⚙️ Installation (Python)
git clone https://github.com/YOURNAME/benchmarking-sentinel1-sar-features.git
cd benchmarking-sentinel1-sar-features

python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt

└── README.md
