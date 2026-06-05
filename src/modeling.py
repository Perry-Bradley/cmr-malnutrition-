"""Train + compare models for predicting child stunting rate."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

try:  # optional deps
    from xgboost import XGBRegressor
    _HAS_XGB = True
except Exception:  # noqa: BLE001
    _HAS_XGB = False

try:
    from lightgbm import LGBMRegressor
    _HAS_LGBM = True
except Exception:  # noqa: BLE001
    _HAS_LGBM = False

from .config import MODELS_DIR


RANDOM_STATE = 42


def build_model_zoo() -> dict[str, Any]:
    """Return the family of models we compare in the report."""
    zoo: dict[str, Any] = {
        "Baseline (mean)":     DummyRegressor(strategy="mean"),
        "Linear Regression":   Pipeline([("scale", StandardScaler()),
                                         ("model", LinearRegression())]),
        "Ridge":               Pipeline([("scale", StandardScaler()),
                                         ("model", Ridge(alpha=1.0, random_state=RANDOM_STATE))]),
        "Lasso":               Pipeline([("scale", StandardScaler()),
                                         ("model", Lasso(alpha=0.1, random_state=RANDOM_STATE))]),
        "Decision Tree":       DecisionTreeRegressor(max_depth=6, random_state=RANDOM_STATE),
        "Random Forest":       RandomForestRegressor(n_estimators=400, max_depth=None,
                                                      n_jobs=-1, random_state=RANDOM_STATE),
        "Gradient Boosting":   GradientBoostingRegressor(n_estimators=300, max_depth=3,
                                                          learning_rate=0.05,
                                                          random_state=RANDOM_STATE),
        "K-Nearest Neighbours": Pipeline([("scale", StandardScaler()),
                                          ("model", KNeighborsRegressor(n_neighbors=7))]),
    }
    if _HAS_XGB:
        zoo["XGBoost"] = XGBRegressor(
            n_estimators=400, max_depth=4, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9, random_state=RANDOM_STATE,
            verbosity=0, n_jobs=-1,
        )
    if _HAS_LGBM:
        zoo["LightGBM"] = LGBMRegressor(
            n_estimators=400, max_depth=-1, learning_rate=0.05,
            num_leaves=31, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1,
        )
    return zoo


@dataclass
class ModelResult:
    name: str
    rmse: float
    mae: float
    r2: float
    cv_rmse_mean: float
    cv_rmse_std: float


def _metrics(y_true, y_pred) -> tuple[float, float, float]:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    return rmse, mae, r2


def evaluate_all(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2,
                 cv_folds: int = 5) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Train each model, compute hold-out + cross-validated metrics."""
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=test_size, random_state=RANDOM_STATE
    )
    kf = KFold(n_splits=cv_folds, shuffle=True, random_state=RANDOM_STATE)

    rows, fitted = [], {}
    for name, mdl in build_model_zoo().items():
        mdl.fit(X_tr, y_tr)
        pred = mdl.predict(X_te)
        rmse, mae, r2 = _metrics(y_te, pred)
        cv_rmse = -cross_val_score(mdl, X, y, cv=kf,
                                    scoring="neg_root_mean_squared_error")
        rows.append(ModelResult(name, rmse, mae, r2,
                                float(cv_rmse.mean()), float(cv_rmse.std())))
        fitted[name] = mdl

    leaderboard = (pd.DataFrame([r.__dict__ for r in rows])
                     .sort_values("cv_rmse_mean")
                     .reset_index(drop=True))
    return leaderboard, fitted


def save_best(fitted: dict[str, Any], leaderboard: pd.DataFrame,
              path: Path | None = None) -> Path:
    best_name = leaderboard.iloc[0]["name"]
    path = path or (MODELS_DIR / "best_model.joblib")
    joblib.dump({"name": best_name, "model": fitted[best_name]}, path)
    return path


def predict_hotspots(model, X: pd.DataFrame, meta: pd.DataFrame,
                     top_n: int | None = None) -> pd.DataFrame:
    """Score every sub-region and return a ranked risk table."""
    meta = meta.reset_index(drop=True).copy()
    meta["predicted_stunting"] = model.predict(X)
    ranked = meta.sort_values("predicted_stunting", ascending=False).reset_index(drop=True)
    ranked.insert(0, "rank", ranked.index + 1)
    if top_n:
        ranked = ranked.head(top_n)
    return ranked
