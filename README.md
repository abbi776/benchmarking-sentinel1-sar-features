# 🌳 Benchmarking Sentinel-1 SAR Features for Woody Plant Encroachment Mapping

Open-source framework for benchmarking Sentinel-1 SAR features and applying them to woody plant encroachment (WPE) mapping in floodplain wetlands using **multi-seasonal SAR backscatter, polarization indices, texture features, and machine learning (RF, SVM, XGBoost)**.

This repository contains all the scripts, environment requirements, and instructions needed to reproduce the analysis, from preprocessing Sentinel-1 data in Google Earth Engine to generating interpretable wall-to-wall classification maps.

---

## 🌱 Key Features
- **Sentinel-1 Preprocessing (GEE):** Standardized workflow including border-noise masking, Refined Lee speckle filtering, and Ellipsoidal Radiometric Terrain Correction (RTC).
- **Unified Feature Stack:** Integration of multi-seasonal Intensity (VV/VH), Polarization Indices, and GLCM Texture metrics.
- **Robust Validation:** Implementation of Leave-One-Region-Out (LORO) cross-validation to ensure spatial independence.
- **Model Benchmarking:** Systematic comparison of Random Forest (RF), Support Vector Machine (SVM), and Extreme Gradient Boosting (XGBoost).
- **Explainable AI:** Global feature importance analysis using SHAP (TreeExplainer).
- **Wall-to-Wall Mapping:** Scalable pixel-wise classification for floodplain monitoring (2025).

> **Note:** The sentinel-1 preprocessing workflow builds upon the **Sentinel-1 SAR Backscatter Analysis Ready Data (ARD)** framework by Mullissa et al. (2021).  
> *Reference:* [https://github.com/adugnag/gee_s1_ard](https://github.com/adugnag/gee_s1_ard)

---

## 📂 Repository Structure
```
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
├── scripts/                    # Python analysis pipeline 
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
└── README.md
```

## ⚙️ Installation
```bash
git clone https://github.com/abbi776/benchmarking-sentinel1-sar-features.git
cd benchmarking-sentinel1-sar-features

python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

---
## 🚀 Pipeline Steps
1️⃣ Sentinel-1 preprocessing (Google Earth Engine)

Run scripts inside ```/gee``` in order:
- Utilities
- Border-noise masking
- Refined Lee speckle filter
- Ellipsoidal RTC
- SAR indices + GLCM textures
- Export seasonal mosaics

**Output:** seasonal multi-band SAR feature rasters.
```
S1_WPE_FEATURES_{SEASON}_{YEAR}.tif
```

2️⃣ **Prepare feature rasters**
```bash
python scripts/00_prepare_feature_rasters.py
```
Mosaics tiles, clips wetlands, fixes band names.

3️⃣ **Extract polygon training features**
```bash
python scripts/01_extract_training_features.py
```
Produces LOPO-ready tables.
```
s1_features_all_LOPO.xlsx
```

4️⃣ **Feature ablation & model benchmarking**
```bash
python scripts/02_model_ablation_experiments.py
```
Benchmarks:

- VV/VH only

- Indices only

- Textures only

- Combined sets

- Full stack

Across **RF / SVM / XGB**.

5️⃣ **SHAP feature importance**
```bash
python scripts/03_feature_importance_shap.py
```
Outputs ranking of most important SAR features.

6️⃣ **Train final mapping models**
```bash
python scripts/04_train_final_models_for_mapping.py
```
Saves:

- trained RF / SVM / XGB models

- JSON feature schema (band order safety)

7️⃣ **Build yearly stacks**
```bash
python scripts/05_build_yearly_stacks.py
```
Creates stack for:
- 2025
```
P1ANAE_YEARLY_2025_STACK.tif
```

...


8️⃣ Wall-to-wall mapping  
```bash
python scripts/06_apply_models_to_yearly_stacks.py
```

## 📁 Data & Results Organization
data/
  ├── s1_features/
  ├── wetlands/
  ├── labels/
  └── yearly_stacks/

results/
  ├── models/
  ├── shap/
  ├── predictions/
  └── figures/

## 📊 Outputs
- Yearly prediction maps ```(.tif)```

- Feature tables (Excel)

- SHAP importance figures

- Model accuracy summaries

- Wall-to-wall maps


## 🙏 Attribution & Credits
Portions of SAR preprocessing draw on concepts from:
**Sentinel-1 SAR Backscatter Analysis Ready Data (ARD)** framework by Mullissa et al. (2021).  
> *Reference:* [https://github.com/adugnag/gee_s1_ard](https://github.com/adugnag/gee_s1_ard)
