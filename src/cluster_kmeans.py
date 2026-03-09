from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from cluster_common import (
    flatten_column_groups,
    prepare_features_for_clustering,
    select_existing_columns,
)

sns.set(style="whitegrid", context="notebook")


# ==============================
# 調整ポイント
# ==============================
RANDOM_STATE = 42
PCA_DIM = 2
K_MIN = 2
K_MAX = 6
MISSING_STRATEGY = "drop"  # "drop" or "median"
PREDIABETES_GLUCOSE_LOW = 100
PREDIABETES_GLUCOSE_HIGH = 125


@dataclass
class KMeansResult:
    scenario_name: str
    analyzed_df: pd.DataFrame
    pca_coords: pd.DataFrame
    k_scores: pd.DataFrame
    best_k: int
    summary: pd.DataFrame


def run_kmeans(prepared, k_values: list[int], random_state: int) -> KMeansResult:
    rows = []
    for k in k_values:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=20)
        labels = km.fit_predict(prepared.X_scaled)
        score = silhouette_score(prepared.X_scaled, labels)
        rows.append({"k": k, "silhouette": score})

    scores = pd.DataFrame(rows).sort_values("silhouette", ascending=False).reset_index(drop=True)
    best_k = int(scores.iloc[0]["k"])

    best_model = KMeans(n_clusters=best_k, random_state=random_state, n_init=20)
    best_labels = best_model.fit_predict(prepared.X_scaled)

    analyzed_df = prepared.cleaned_df.copy()
    analyzed_df["cluster"] = best_labels

    pca_df = pd.DataFrame(prepared.pca_coords, columns=["PC1", "PC2"])
    pca_df["cluster"] = best_labels

    mean_df = analyzed_df.groupby("cluster")[prepared.feature_columns].mean().add_suffix("_mean")
    median_df = analyzed_df.groupby("cluster")[prepared.feature_columns].median().add_suffix("_median")
    n_df = analyzed_df.groupby("cluster").size().to_frame("n")
    summary = n_df.join(mean_df).join(median_df)

    return KMeansResult(prepared.scenario_name, analyzed_df, pca_df, scores, best_k, summary)


def save_k_comparison_plots(prepared, k_values: list[int], output_dir: Path, random_state: int) -> None:
    """kごとのクラスタ結果を1枚にまとめて保存 + 各k個別画像も保存。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    n = len(k_values)
    ncols = 3
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 5 * nrows), squeeze=False)

    for idx, k in enumerate(k_values):
        r, c = divmod(idx, ncols)
        ax = axes[r][c]
        km = KMeans(n_clusters=k, random_state=random_state, n_init=20)
        labels = km.fit_predict(prepared.X_scaled)

        ax.scatter(prepared.pca_coords[:, 0], prepared.pca_coords[:, 1], c=labels, cmap="tab10", s=14, alpha=0.75)
        ax.set_title(f"{prepared.scenario_name} / k={k}")
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")

        # 個別保存
        fig_single = plt.figure(figsize=(8, 6))
        plt.scatter(prepared.pca_coords[:, 0], prepared.pca_coords[:, 1], c=labels, cmap="tab10", s=18, alpha=0.8)
        plt.title(f"{prepared.scenario_name}: KMeans k={k}")
        plt.xlabel("PC1")
        plt.ylabel("PC2")
        plt.tight_layout()
        plt.savefig(output_dir / f"{prepared.scenario_name}_kmeans_k{k}.png", dpi=150)
        plt.close(fig_single)

    for idx in range(n, nrows * ncols):
        r, c = divmod(idx, ncols)
        axes[r][c].axis("off")

    fig.suptitle(f"KMeans k comparison ({prepared.scenario_name})", fontsize=14)
    fig.tight_layout()
    fig.savefig(output_dir / f"{prepared.scenario_name}_kmeans_all_k.png", dpi=180)
    plt.close(fig)


def print_risk_table(result: KMeansResult, glucose_col: str) -> None:
    marker_candidates = [glucose_col, "BMXBMI", "LBXTR", "LBDTRSI", "LBXHDD", "LBDHDD", "BPXSY1", "BPXDI1"]
    markers = [c for c in marker_candidates if c in result.analyzed_df.columns]
    print(f"\n=== {result.scenario_name}: リスク指標クラスタ平均 ===")
    print(result.analyzed_df.groupby("cluster")[markers].mean().round(2))


def compare_prediabetes_ratio(with_result: KMeansResult, without_result: KMeansResult, glucose_col: str) -> None:
    for result in [with_result, without_result]:
        if glucose_col not in result.analyzed_df.columns:
            print(f"[{result.scenario_name}] {glucose_col} が無いため比較不可")
            continue

        comp = result.analyzed_df.copy()
        comp = comp.dropna(subset=[glucose_col])
        if comp.empty:
            print(f"[{result.scenario_name}] {glucose_col} は存在しますが有効値がありません")
            continue

        comp["predm_flag"] = (
            (comp[glucose_col] >= PREDIABETES_GLUCOSE_LOW)
            & (comp[glucose_col] <= PREDIABETES_GLUCOSE_HIGH)
        ).astype(int)
        out = comp.groupby("cluster").agg(
            n=(glucose_col, "size"),
            glucose_mean=(glucose_col, "mean"),
            prediabetes_ratio=("predm_flag", "mean"),
        )
        out["prediabetes_ratio"] = (out["prediabetes_ratio"] * 100).round(2)
        out["glucose_mean"] = out["glucose_mean"].round(2)
        print(f"\n--- {result.scenario_name} ---")
        print(out.sort_values("prediabetes_ratio", ascending=False))


def run_analysis(df: pd.DataFrame, output_dir: str = "outputs/kmeans") -> tuple[KMeansResult, KMeansResult]:
    existing = select_existing_columns(df)
    print("=== 候補列のうち利用可能な列 ===")
    for g, cols in existing.items():
        print(f"[{g}] {len(cols)}列: {cols}")

    glucose_cols = existing.get("glucose", [])
    if not glucose_cols:
        raise ValueError("血糖列候補がありません")
    glucose_col = glucose_cols[0]

    with_cols = flatten_column_groups(existing)
    without_cols = flatten_column_groups(existing, exclude_groups=["glucose"])

    prepared_with = prepare_features_for_clustering(df, "with_glucose", with_cols, MISSING_STRATEGY, PCA_DIM)
    prepared_without = prepare_features_for_clustering(df, "without_glucose", without_cols, MISSING_STRATEGY, PCA_DIM)

    # 血糖除外シナリオでも比較用に血糖列を保持する（インデックスで復元）
    if glucose_col not in prepared_without.cleaned_df.columns and glucose_col in df.columns:
        prepared_without.cleaned_df[glucose_col] = df.loc[prepared_without.cleaned_df.index, glucose_col]

    k_values = list(range(K_MIN, K_MAX + 1))
    out_dir = Path(output_dir)
    save_k_comparison_plots(prepared_with, k_values, out_dir, RANDOM_STATE)
    save_k_comparison_plots(prepared_without, k_values, out_dir, RANDOM_STATE)

    result_with = run_kmeans(prepared_with, k_values, RANDOM_STATE)
    result_without = run_kmeans(prepared_without, k_values, RANDOM_STATE)

    print("\n=== PCA寄与率 ===")
    print("with_glucose:", prepared_with.pca_model.explained_variance_ratio_)
    print("without_glucose:", prepared_without.pca_model.explained_variance_ratio_)

    print("\n=== シルエット結果 with_glucose ===")
    print(result_with.k_scores)
    print("best_k:", result_with.best_k)

    print("\n=== シルエット結果 without_glucose ===")
    print(result_without.k_scores)
    print("best_k:", result_without.best_k)

    print("\n=== クラスタ要約 with_glucose ===")
    print(result_with.summary.head(20))
    print("\n=== クラスタ要約 without_glucose ===")
    print(result_without.summary.head(20))

    print_risk_table(result_with, glucose_col)
    print_risk_table(result_without, glucose_col)

    print("\n=== 血糖平均と前糖尿病域割合の比較 ===")
    compare_prediabetes_ratio(result_with, result_without, glucose_col)

    print(f"\n図を保存しました: {out_dir.resolve()}")
    return result_with, result_without


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NHANESの健康クラスタ探索 (KMeans)")
    parser.add_argument("--input", default="data/merged/nhanes_2017_2018.csv", help="merge_nhanes.pyで作ったCSV")
    parser.add_argument("--output-dir", default="outputs/kmeans", help="図の保存先")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.input)
    print(f"Loaded: {args.input} shape={df.shape}")
    run_analysis(df, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
