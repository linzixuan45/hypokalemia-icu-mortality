#!/usr/bin/env python3
"""Export locked 8-feature bundle for github_release/."""
from __future__ import annotations

import pickle
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "result" / "r2_locked" / "model_weight" / "9_features" / "model_weight.pkl"
DEST_DIR = ROOT / "model_weights"
DEST = DEST_DIR / "8_features_model.pkl"


def main():
    bundle = pickle.load(open(SRC, "rb"))
    out = {
        "model": bundle["Ensemble_Stacking"],
        "imputer": bundle["imputer"],
        "scaler": bundle["scaler"],
        "features": bundle["features"],
        "threshold": bundle["threshold"],
    }
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    with open(DEST, "wb") as f:
        pickle.dump(out, f)
    for doc in ("MODEL_CARD.md", "data_dictionary.md", "README.md", "inference.py", "requirements.txt"):
        src = Path(__file__).resolve().parent / "github_release" / doc
        if src.exists():
            pass  # already in place
    print(f"Exported -> {DEST}")


if __name__ == "__main__":
    main()
