🌳 Benchmarking Sentinel-1 SAR Features for Woody Plant Encroachment Mapping

This repository provides an open-source, end-to-end framework for benchmarking Sentinel-1 SAR features and applying them to woody plant encroachment (WPE) mapping in floodplain wetlands.

The workflow integrates:

Google Earth Engine (Sentinel-1 preprocessing & feature generation)

Polarisation indices & SAR backscatter transformations

GLCM texture metrics

Machine learning (Random Forest, SVM, XGBoost)

Leave-One-Polygon-Out (LOPO) cross-validation

SHAP model interpretability

Wall-to-wall mapping across multiple years

The goal is to evaluate which SAR feature groups best discriminate woody vegetation in floodplain environments.

🌱 Key Highlights

✔️ Border-noise masking, speckle filtering, ellipsoidal RTC

✔️ Unified SAR feature stack (indices + textures)

✔️ Polygon-based feature extraction

✔️ Structured feature ablation experiments

✔️ RF vs SVM vs XGB benchmarking

✔️ SHAP interpretability

✔️ Wall-to-wall mapping (2016 / 2018 / 2025)

✔️ Fully script-driven and reproducible

Parts of the preprocessing pipeline build upon:
Mullissa et al. (2021) — Sentinel-1 ARD (GEE)
https://github.com/adugnag/gee_s1_ard

Credit is included in relevant scripts.

📂 Repository Structure
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
└── README.md

⚙️ Installation (Python)
git clone https://github.com/YOURNAME/benchmarking-sentinel1-sar-features.git
cd benchmarking-sentinel1-sar-features

python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt

🚀 Workflow Overview
1️⃣ Sentinel-1 preprocessing (in Google Earth Engine)

Run scripts in /gee in order:

Utilities

Border noise masking

Refined Lee speckle filter

Ellipsoidal RTC

SAR indices + GLCM textures

Export seasonal mosaics

Output: seasonal multi-band SAR feature rasters

2️⃣ Prepare feature rasters
python scripts/00_prepare_feature_rasters.py

3️⃣ Extract polygon training features
python scripts/01_extract_training_features.py


Produces LOPO-ready training tables.

4️⃣ Model benchmarking (feature ablation)
python scripts/02_model_ablation_experiments.py


Benchmarks:

VV + VH

Derived indices

GLCM textures

Combined sets

Full stack

Across RF / SVM / XGB using Leave-One-Polygon-Out.

5️⃣ SHAP interpretability
python scripts/03_feature_importance_shap.py


Outputs:

Global SHAP plots

Seasonal importance rankings

6️⃣ Train final mapping models
python scripts/04_train_final_models_for_mapping.py

7️⃣ Build yearly stacks
python scripts/05_build_yearly_stacks.py


Creates stacks for:

2016

2018

2025

8️⃣ Wall-to-wall mapping
python scripts/06_apply_models_to_yearly_stacks.py


Produces classified woody vegetation maps.

📁 Data Organization
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


Large rasters are excluded using .gitignore.

🙌 Attribution

Please cite:

Mullissa et al. (2021) — Sentinel-1 ARD in GEE

This repository (when used in publications)

🧑‍🤝‍🧑 Contributing

Pull requests welcome — especially improvements in:

SAR feature engineering

Validation strategies

Model transferability

📜 License

MIT License.

📧 Contact

Abdullah Toqeer
PhD Candidate — Charles Sturt University
📩 toqeerabdullah776@gmail.com
