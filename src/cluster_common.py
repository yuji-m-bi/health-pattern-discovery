from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

# NHANESサイクル差異を考慮した候補列
COLUMN_CANDIDATES: dict[str, list[str]] = {
    "basic": ["RIDAGEYR", "RIAGENDR", "RIDRETH1", "INDFMPIR"],
    "body": ["BMXBMI", "BPXSY1", "BPXDI1"],
    "glucose": ["LBXGLU", "LBDGLUSI", "LBXGH", "LBDGLTSI"],
    "hdl": ["LBDHDD", "LBXHDD", "LBDHDDSI"],
    "triglycerides": ["LBXTR", "LBDTRSI", "LBXTRSI"],
    "physical_activity": ["PAQ605", "PAQ620", "PAQ650", "PAQ665"],
    "sleep": ["SLD010H", "SLD012", "SLQ050"],
    "smoking": ["SMQ020", "SMD641", "SMQ040"],
    "alcohol": ["ALQ101", "ALQ110", "ALQ130"],
    "dietary": ["DR1TKCAL", "DR1TCARB", "DR1TSUGR", "DR1TTFAT", "DR1TPROT", "DR1TFIBE", "DR1TSODI"],
}


@dataclass
class PreparedData:
    scenario_name: str
    feature_columns: list[str]
    cleaned_df: pd.DataFrame
    X_scaled: np.ndarray
    pca_coords: np.ndarray
    pca_model: PCA


def select_existing_columns(df: pd.DataFrame, candidates: dict[str, list[str]] | None = None) -> dict[str, list[str]]:
    base = candidates or COLUMN_CANDIDATES
    return {group: [c for c in cols if c in df.columns] for group, cols in base.items()}


def flatten_column_groups(column_groups: dict[str, list[str]], exclude_groups: Iterable[str] | None = None) -> list[str]:
    exclude = set(exclude_groups or [])
    merged: list[str] = []
    for group, cols in column_groups.items():
        if group in exclude:
            continue
        merged.extend(cols)
    return list(dict.fromkeys(merged))


def handle_missing_values(df: pd.DataFrame, columns: list[str], strategy: str = "drop") -> tuple[pd.DataFrame, np.ndarray]:
    sub = df[columns].copy()
    if strategy == "drop":
        cleaned = sub.dropna(axis=0, how="any")
        return cleaned, cleaned.values
    if strategy == "median":
        imputer = SimpleImputer(strategy="median")
        X = imputer.fit_transform(sub)
        cleaned = pd.DataFrame(X, columns=columns, index=sub.index)
        return cleaned, X
    raise ValueError(f"Unknown missing strategy: {strategy}")


def prepare_features_for_clustering(
    df: pd.DataFrame,
    scenario_name: str,
    feature_columns: list[str],
    missing_strategy: str = "drop",
    pca_dim: int = 2,
) -> PreparedData:
    cleaned_df, X = handle_missing_values(df, feature_columns, strategy=missing_strategy)
    if cleaned_df.empty:
        raise ValueError(f"{scenario_name}: 欠損処理後データが空です")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=pca_dim)
    pca_coords = pca.fit_transform(X_scaled)

    return PreparedData(
        scenario_name=scenario_name,
        feature_columns=feature_columns,
        cleaned_df=cleaned_df,
        X_scaled=X_scaled,
        pca_coords=pca_coords,
        pca_model=pca,
    )
