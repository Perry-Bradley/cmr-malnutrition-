"""Classification: re-cast stunting rate as a WHO public-health risk band.

WHO classifies population stunting as:
    <20%   low
    20-29% medium
    30-39% high
    >=40%  critical (very high public-health significance)

This complements the regression: instead of estimating a continuous percentage,
we predict which risk band a sub-region falls into -- often more useful for
programme targeting because the band determines the response protocol.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                              confusion_matrix, f1_score)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .config import RISK_BAND_BINS, RISK_BAND_LABELS, TARGET

RANDOM_STATE = 42


def add_risk_band(df: pd.DataFrame, target_col: str = TARGET,
                  band_col: str = "risk_band") -> pd.DataFrame:
    df = df.copy()
    df[band_col] = pd.cut(df[target_col], bins=RISK_BAND_BINS,
                          labels=RISK_BAND_LABELS).astype(str)
    return df


def build_classifier_zoo() -> dict:
    return {
        "Logistic Regression": Pipeline([
            ("scale", StandardScaler()),
            ("model", LogisticRegression(max_iter=2000,
                                          random_state=RANDOM_STATE)),
        ]),
        "Random Forest": RandomForestClassifier(
            n_estimators=400, max_depth=None, n_jobs=-1,
            random_state=RANDOM_STATE, class_weight="balanced",
        ),
    }


@dataclass
class ClassifierResult:
    name: str
    accuracy: float
    macro_f1: float
    cv_accuracy_mean: float
    cv_accuracy_std: float


def evaluate_all(X: pd.DataFrame, y: pd.Series,
                 test_size: float = 0.2, cv_folds: int = 5
                 ) -> tuple[pd.DataFrame, dict, dict]:
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=test_size, random_state=RANDOM_STATE, stratify=y
    )
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=RANDOM_STATE)

    rows, fitted, reports = [], {}, {}
    for name, mdl in build_classifier_zoo().items():
        mdl.fit(X_tr, y_tr)
        pred = mdl.predict(X_te)
        cv = cross_val_score(mdl, X, y, cv=skf, scoring="accuracy")
        rows.append(ClassifierResult(
            name=name,
            accuracy=float(accuracy_score(y_te, pred)),
            macro_f1=float(f1_score(y_te, pred, average="macro", zero_division=0)),
            cv_accuracy_mean=float(cv.mean()),
            cv_accuracy_std=float(cv.std()),
        ))
        fitted[name] = mdl
        reports[name] = {
            "confusion_matrix":      confusion_matrix(y_te, pred,
                                                       labels=RISK_BAND_LABELS).tolist(),
            "classification_report": classification_report(
                y_te, pred, labels=RISK_BAND_LABELS, zero_division=0, output_dict=True
            ),
            "labels": RISK_BAND_LABELS,
        }

    leaderboard = (pd.DataFrame([r.__dict__ for r in rows])
                     .sort_values("cv_accuracy_mean", ascending=False)
                     .reset_index(drop=True))
    return leaderboard, fitted, reports


def predict_risk_bands(model, X: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    meta = meta.reset_index(drop=True).copy()
    meta["predicted_band"] = model.predict(X)
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        classes = model.classes_
        for i, cls in enumerate(classes):
            meta[f"p_{cls}"] = proba[:, i].round(3)
    return meta
