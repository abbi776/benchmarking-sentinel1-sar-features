# 🌳 Benchmarking Sentinel-1 SAR Features for Woody Plant Encroachment Mapping

This repository provides an open-source, end-to-end framework for benchmarking Sentinel-1 SAR features and applying them to woody plant encroachment (WPE) mapping in floodplain wetlands.

The workflow integrates:

- Google Earth Engine (Sentinel-1 preprocessing & feature generation)
- Polarisation indices and SAR backscatter transformations
- GLCM texture metrics
- Machine learning (Random Forest, SVM, XGBoost)
- Spatial cross-validation (Leave-One-Polygon-Out)
- Model interpretability using SHAP
- Wall-to-wall mapping across multiple years

The goal is to evaluate which SAR feature groups provide the strongest discriminatory power for floodplain woody vegetation.

---

## 🌱 Key Highlights

✔️ GEE Sentinel-1 preprocessing (border noise masking, speckle filtering, ellipsoidal RTC)  
✔️ Unified SAR feature stack (indices + textures)  
✔️ Polygon-based feature extraction for ML  
✔️ Structured feature ablation experiments  
✔️ Model comparison (RF, SVM, XGB)  
✔️ Global SHAP interpretability  
✔️ Wall-to-wall classification (2016 / 2018 / 2025)  
✔️ Reproducible, script-driven workflow  

> Parts of the preprocessing pipeline build upon:  
> Mullissa et al. (2021) – Sentinel-1 ARD in GEE  
> https://github.com/adugnag/gee_s1_ard  
>  
> Proper credit is attributed inside relevant scripts.

---
benchmarking-sentinel1-sar-features/
│
├── gee/ # GEE SAR preprocessing + feature scripts
│ ├── 00_utils_sar.js
│ ├── 01_border_noise.js
│ ├── 02_speckle_filter.js
│ ├── 03_rtc.js
│ ├── 04_feature_extraction.js
│ └── main_workflow.js
│
├── scripts/ # Python analysis pipeline (numbered)
│ ├── 00_prepare_feature_rasters.py
│ ├── 01_extract_training_features.py
│ ├── 02_model_ablation_experiments.py
│ ├── 03_feature_importance_shap.py
│ ├── 04_train_final_models_for_mapping.py
│ ├── 05_build_yearly_stacks.py
│ └── 06_apply_models_to_yearly_stacks.py
│
├── requirements.txt
├── LICENSE
├── .gitignore
└── README.md


---

## ⚙️ Installation (Python)

```bash
git clone https://github.com/YOURNAME/benchmarking-sentinel1-sar-features.git
cd benchmarking-sentinel1-sar-features

python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt

🚀 Workflow Overview
1️⃣ Sentinel-1 preprocessing (Google Earth Engine)

Run scripts in /gee in order:

Utilities & conversions

Border noise masking

Refined Lee speckle filtering

Ellipsoidal RTC

SAR indices + GLCM textures

Export seasonal feature mosaics

Output: multi-band seasonal SAR feature rasters.


2️⃣ Prepare feature rasters
python scripts/00_prepare_feature_rasters.py


Mosaics, clip wetlands, fix band labels.

2️⃣ Prepare feature rasters
python scripts/00_prepare_feature_rasters.py


Mosaics, clip wetlands, fix band labels.

3️⃣ Extract polygon training features
python scripts/01_extract_training_features.py


Produces an Excel feature table (LOPO-ready).

4️⃣ Feature ablation & model benchmarking
python scripts/02_model_ablation_experiments.py


Benchmarks:

VV + VH only

Derived indices

GLCM textures

Combinations

Full feature set

Across:

RF

SVM

XGB

Using Leave-One-Polygon-Out (LOPO).

5️⃣ SHAP interpretability
python scripts/03_feature_importance_shap.py


Outputs:

Global SHAP plots

Seasonal importance rankings

6️⃣ Train final mapping models
python scripts/04_train_final_models_for_mapping.py


Saves final model + metadata.

7️⃣ Build yearly stacks
python scripts/05_build_yearly_stacks.py


Creates consistent feature stacks for:

2016

2018

2025

8️⃣ Apply models wall-to-wall
python scripts/06_apply_models_to_yearly_stacks.py


Outputs:

Classified woody vegetation maps per wetland & year.

📁 Data Organization

Large Sentinel-1 rasters are not stored in the repo.

Recommended structure:

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
.gitignore prevents large rasters from uploading.

🙌 Attribution

If you use or adapt this workflow, please cite:

Mullissa et al. (2021) – Sentinel-1 ARD in Google Earth Engine

This repository (once published)

🧑‍🤝‍🧑 Contributing

Pull requests are welcome — especially improvements related to:

SAR feature engineering

Validation strategies

Model generalization

📜 License

This project is licensed under the MIT License.

📧 Contact

Abdullah Toqeer
PhD Candidate — Charles Sturt University
📩 toqeerabdullah776@gmail.com


## 📂 Repository Structure

