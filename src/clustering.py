"""Unsupervised clustering: group sub-regions by socio-economic profile.

Stunting itself is the *outcome*; clusters built from the *drivers* reveal
how sub-regions naturally segment irrespective of their current stunting.
This is useful for tailoring intervention packages (a cluster with low
education + poor WASH needs a different programme than a cluster with
high malaria + good education).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from .config import ALL_FEATURES, TARGET

RANDOM_STATE = 42


def fit_kmeans(df: pd.DataFrame, k: int = 4, features: list[str] | None = None
               ) -> tuple[KMeans, StandardScaler, np.ndarray, float]:
    """Fit standardised K-Means and return (model, scaler, labels, silhouette)."""
    features = features or ALL_FEATURES
    X = df[features].values
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)

    km = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE).fit(Xs)
    sil = float(silhouette_score(Xs, km.labels_)) if k > 1 else float("nan")
    return km, scaler, km.labels_, sil


def choose_k(df: pd.DataFrame, k_range: range = range(2, 9),
             features: list[str] | None = None) -> pd.DataFrame:
    """Elbow + silhouette analysis -- returns one row per candidate k."""
    features = features or ALL_FEATURES
    X = df[features].values
    Xs = StandardScaler().fit_transform(X)

    rows = []
    for k in k_range:
        km = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE).fit(Xs)
        sil = silhouette_score(Xs, km.labels_) if k > 1 else float("nan")
        rows.append({"k": k, "inertia": float(km.inertia_),
                     "silhouette": float(sil)})
    return pd.DataFrame(rows)


def profile_clusters(df: pd.DataFrame, labels: np.ndarray,
                     features: list[str] | None = None) -> pd.DataFrame:
    """Mean values of every feature within each cluster, plus the mean stunting."""
    features = features or ALL_FEATURES
    df = df.copy()
    df["cluster"] = labels
    profile = (df.groupby("cluster")[features + [TARGET]]
                 .mean()
                 .round(2)
                 .reset_index())
    profile["n_subregions"] = df.groupby("cluster").size().values
    return profile


def label_clusters(profile: pd.DataFrame) -> dict[int, str]:
    """Give each cluster a human label based on its stunting + education profile."""
    profile = profile.sort_values(TARGET).reset_index(drop=True)
    n = len(profile)
    labels = {}
    for rank, row in profile.iterrows():
        cid = int(row["cluster"])
        if n == 1:
            labels[cid] = "All"
        elif rank == 0:
            labels[cid] = "Urban-affluent (low risk)"
        elif rank == n - 1:
            labels[cid] = "Northern-rural (critical risk)"
        elif rank < n / 2:
            labels[cid] = "Transitioning (medium-low risk)"
        else:
            labels[cid] = "Vulnerable (medium-high risk)"
    return labels


def pca_2d(df: pd.DataFrame, features: list[str] | None = None
           ) -> tuple[np.ndarray, PCA]:
    features = features or ALL_FEATURES
    Xs = StandardScaler().fit_transform(df[features].values)
    pca = PCA(n_components=2, random_state=RANDOM_STATE).fit(Xs)
    return pca.transform(Xs), pca
