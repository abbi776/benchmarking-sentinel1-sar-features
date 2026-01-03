# 🌳 Benchmarking Sentinel-1 SAR Features for Woody Plant Encroachment Mapping

Open-source framework for benchmarking Sentinel-1 SAR features and applying them to woody plant encroachment (WPE) mapping in floodplain wetlands.

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
└── README.md

⚙️ Installation (Python)

git clone https://github.com/YOURNAME/benchmarking-sentinel1-sar-features.git
cd benchmarking-sentinel1-sar-features

python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt
