# Benchmarking Sentinel-1 SAR Features for Floodplain Woody Vegetation Classification

Open-source framework for benchmarking Sentinel-1 SAR features and applying them to woody plant encroachment (WPE) mapping in floodplain wetlands using **multi-seasonal SAR backscatter, polarization indices, texture features, and machine learning (RF, SVM, XGBoost)**.

This repository contains all the scripts, environment requirements, and instructions needed to reproduce the analysis — from preprocessing Sentinel-1 data in Google Earth Engine to generating interpretable wall-to-wall classification maps.

---

## 🌱 Key Features
- **Sentinel-1 Preprocessing (GEE):** Standardized workflow including border-noise masking, Refined Lee speckle filtering, and Ellipsoidal Radiometric Terrain Correction (RTC).
- **Unified Feature Stack:** Integration of multi-seasonal Intensity (VV/VH), Polarization Indices, and GLCM Texture metrics.
- **Robust Validation:** Implementation of Leave-One-Region-Out (LORO) cross-validation to ensure spatial independence.
- **Model Benchmarking:** Systematic comparison of Random Forest (RF), Support Vector Machine (SVM), and Extreme Gradient Boosting (XGBoost).
- **Explainable AI:** Global feature importance analysis using SHAP (TreeExplainer).
- **Wall-to-Wall Mapping:** Scalable pixel-wise classification for floodplain monitoring (2016, 2018, 2025).

> **Note:** The preprocessing workflow builds upon the **Sentinel-1 SAR Backscatter Analysis Ready Data (ARD)** framework by Mullissa et al. (2021).  
> *Reference:* [https://github.com/adugnag/gee_s1_ard](https://github.com/adugnag/gee_s1_ard)

---

## 📂 Repository Structure
