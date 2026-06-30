#!/usr/bin/env python3
"""8-feature locked-model inference for research demo."""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd

FEATURES = [
    "rdw_mean",
    "wbc_min",
    "admission_age",
    "spo2_min",
    "lactate_min",
    "is_noninvasive_ventilator",
    "platelet_min",
    "aniongap_1st",
]

ROOT = Path(__file__).resolve().parent


def load_bundle():
    with open(ROOT / "model_weights" / "8_features_model.pkl", "rb") as f:
        return pickle.load(f)


def predict_proba(row: dict) -> float:
    bundle = load_bundle()
    model = bundle["model"]
    imp = bundle["imputer"]
    scaler = bundle["scaler"]
    df = pd.DataFrame([{k: row[k] for k in FEATURES}])
    df["is_noninvasive_ventilator"] = int(float(row["is_noninvasive_ventilator"]) >= 0.5)
    X = pd.DataFrame(imp.transform(df[FEATURES]), columns=FEATURES)
    Xs = pd.DataFrame(scaler.transform(X), columns=FEATURES)
    return float(model.predict_proba(Xs)[0, 1])


if __name__ == "__main__":
    demo = {
        "rdw_mean": 13.5,
        "wbc_min": 5.0,
        "admission_age": 65,
        "spo2_min": 95,
        "lactate_min": 1.0,
        "is_noninvasive_ventilator": 0,
        "platelet_min": 150,
        "aniongap_1st": 12,
    }
    p = predict_proba(demo)
    print(f"7-day mortality probability: {p:.3f}")
