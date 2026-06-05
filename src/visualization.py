"""Plotting helpers shared between the notebook and the dashboard."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .config import ALL_FEATURES, FIGURES_DIR, TARGET

sns.set_theme(style="whitegrid", context="notebook")


def _save(fig, name: str | None) -> Path | None:
    if name is None:
        return None
    out = FIGURES_DIR / name
    fig.savefig(out, dpi=140, bbox_inches="tight")
    return out


def plot_target_distribution(df: pd.DataFrame, save: str | None = None):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.histplot(df[TARGET], bins=25, kde=True, ax=ax, color="#c0392b")
    ax.set_title("Distribution of sub-regional child stunting rate")
    ax.set_xlabel("Stunting rate (%)")
    _save(fig, save)
    return fig


def plot_region_boxplot(df: pd.DataFrame, save: str | None = None):
    order = df.groupby("region")[TARGET].median().sort_values(ascending=False).index
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=df, x="region", y=TARGET, order=order, ax=ax,
                hue="region", palette="RdYlGn_r", legend=False)
    ax.set_title("Child stunting rate by region (all survey years)")
    ax.set_xlabel(""); ax.set_ylabel("Stunting rate (%)")
    ax.tick_params(axis="x", rotation=30)
    _save(fig, save)
    return fig


def plot_correlation_heatmap(df: pd.DataFrame, save: str | None = None):
    cols = ALL_FEATURES + [TARGET]
    corr = df[cols].corr(method="spearman")
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, cmap="RdBu_r", center=0, annot=True, fmt=".2f",
                vmin=-1, vmax=1, ax=ax, cbar_kws={"shrink": 0.7},
                annot_kws={"size": 7})
    ax.set_title("Spearman correlation between features and stunting rate")
    _save(fig, save)
    return fig


def plot_feature_vs_target(df: pd.DataFrame, feature: str, save: str | None = None):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.regplot(data=df, x=feature, y=TARGET, ax=ax,
                scatter_kws={"alpha": 0.5}, line_kws={"color": "#c0392b"})
    ax.set_title(f"{feature} vs {TARGET}")
    _save(fig, save)
    return fig


def plot_model_leaderboard(leaderboard: pd.DataFrame, save: str | None = None):
    # Sort ascending so the best model is on top of a horizontal bar chart.
    lb = leaderboard.sort_values("cv_rmse_mean", ascending=False).reset_index(drop=True)
    colors = plt.cm.viridis(np.linspace(0.15, 0.85, len(lb)))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(lb["name"], lb["cv_rmse_mean"], xerr=lb["cv_rmse_std"],
            color=colors, edgecolor="black", linewidth=0.4,
            error_kw=dict(ecolor="black", capsize=3, lw=0.8))
    ax.set_title("Model comparison - 5-fold cross-validated RMSE (lower is better)")
    ax.set_xlabel("CV RMSE"); ax.set_ylabel("")
    _save(fig, save)
    return fig


def plot_feature_importance(importances: pd.Series, save: str | None = None):
    top = importances.sort_values(ascending=True).tail(15)
    fig, ax = plt.subplots(figsize=(8, 6))
    top.plot(kind="barh", ax=ax, color="#2c3e50")
    ax.set_title("Top-15 feature importances")
    ax.set_xlabel("Importance")
    _save(fig, save)
    return fig


def plot_hotspot_map(ranked: pd.DataFrame, top_n: int = 15, save: str | None = None):
    """Bar chart of top-N predicted-stunting sub-regions (used in place of a true map)."""
    top = ranked.head(top_n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(top["subregion"] + " (" + top["region"] + ")",
                   top["predicted_stunting"], color="#c0392b")
    ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9)
    ax.set_title(f"Top {top_n} predicted child-malnutrition hotspots in Cameroon")
    ax.set_xlabel("Predicted stunting rate (%)")
    _save(fig, save)
    return fig
