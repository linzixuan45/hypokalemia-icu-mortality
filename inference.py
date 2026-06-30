#!/usr/bin/env python3
"""8-feature research model inference for research demo."""
from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd

DEFAULT_FEATURES = [
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
_BUNDLE: dict | None = None


def load_bundle() -> dict:
    global _BUNDLE
    if _BUNDLE is None:
        with open(ROOT / "model_weights" / "8_features_model.pkl", "rb") as f:
            _BUNDLE = pickle.load(f)
    return _BUNDLE


def feature_names() -> list[str]:
    bundle = load_bundle()
    return list(bundle.get("features", DEFAULT_FEATURES))


def predict_proba(row: dict) -> float:
    bundle = load_bundle()
    features = feature_names()
    missing = [k for k in features if k not in row]
    if missing:
        raise ValueError(f"Missing required features: {missing}. Expected: {features}")

    model = bundle["model"]
    imp = bundle["imputer"]
    scaler = bundle["scaler"]
    df = pd.DataFrame([{k: row[k] for k in features}])
    df["is_noninvasive_ventilator"] = int(float(row["is_noninvasive_ventilator"]) >= 0.5)
    X = pd.DataFrame(imp.transform(df[features]), columns=features)
    Xs = pd.DataFrame(scaler.transform(X), columns=features)
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
    bundle = load_bundle()
    p = predict_proba(demo)
    print(f"7-day mortality probability: {p:.3f}")
    if "threshold" in bundle:
        print(f"Youden threshold (training OOF): {bundle['threshold']:.3f}")
        print(f"Binary class (prob >= threshold): {int(p >= bundle['threshold'])}")
