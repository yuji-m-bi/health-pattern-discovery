from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def choose_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def add_risk_flags(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    out = df.copy()

    glucose_col = choose_column(df, ["LBXGLU", "LBDGLUSI"])
    bmi_col = choose_column(df, ["BMXBMI"])
    sbp_col = choose_column(df, ["BPXSY1"])
    dbp_col = choose_column(df, ["BPXDI1"])
    tg_col = choose_column(df, ["LBXTR", "LBDTRSI"])
    hdl_col = choose_column(df, ["LBDHDD", "LBXHDD", "LBDHDDSI"])

    used = {
        "glucose": glucose_col,
        "bmi": bmi_col,
        "sbp": sbp_col,
        "dbp": dbp_col,
        "tg": tg_col,
        "hdl": hdl_col,
    }

    if glucose_col:
        out["risk_prediabetes"] = ((out[glucose_col] >= 100) & (out[glucose_col] <= 125)).astype("Int64")
        out["risk_diabetes_range"] = (out[glucose_col] >= 126).astype("Int64")
    if bmi_col:
        out["risk_obesity"] = (out[bmi_col] >= 30).astype("Int64")
    if sbp_col and dbp_col:
        out["risk_high_bp"] = ((out[sbp_col] >= 130) | (out[dbp_col] >= 80)).astype("Int64")
    if tg_col:
        out["risk_hypertriglyceridemia"] = (out[tg_col] >= 150).astype("Int64")
    if hdl_col:
        out["risk_low_hdl"] = (out[hdl_col] < 40).astype("Int64")

    risk_cols = [c for c in out.columns if c.startswith("risk_")]
    if risk_cols:
        out["risk_count"] = out[risk_cols].fillna(0).sum(axis=1).astype("Int64")

    return out, used


def summarize_risk_prevalence(df: pd.DataFrame) -> pd.DataFrame:
    risk_cols = [c for c in df.columns if c.startswith("risk_") and c != "risk_count"]
    rows = []
    for col in risk_cols:
        valid = df[col].dropna()
        if valid.empty:
            continue
        rows.append(
            {
                "risk_flag": col,
                "n_valid": int(valid.shape[0]),
                "n_positive": int(valid.sum()),
                "prevalence_pct": round(float(valid.mean() * 100), 2),
            }
        )
    return pd.DataFrame(rows).sort_values("prevalence_pct", ascending=False)


def summarize_by_group(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    risk_cols = [c for c in df.columns if c.startswith("risk_") and c != "risk_count"]
    if group_col not in df.columns or not risk_cols:
        return pd.DataFrame()

    agg_map = {c: "mean" for c in risk_cols}
    out = df.groupby(group_col).agg(agg_map)
    out = (out * 100).round(2).add_suffix("_pct")
    out["n"] = df.groupby(group_col).size()
    return out.sort_values("n", ascending=False)


def risk_combo_table(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    risk_cols = [c for c in df.columns if c.startswith("risk_") and c != "risk_count"]
    if not risk_cols:
        return pd.DataFrame()

    tmp = df[risk_cols].fillna(0).astype(int)
    combo = tmp.apply(lambda row: ",".join([c.replace("risk_", "") for c in risk_cols if row[c] == 1]) or "none", axis=1)
    out = combo.value_counts().head(top_n).to_frame("n")
    out["ratio_pct"] = (out["n"] / len(df) * 100).round(2)
    out.index.name = "risk_combo"
    return out.reset_index()


def glucose_correlation_table(df: pd.DataFrame, glucose_col: str | None) -> pd.DataFrame:
    if glucose_col is None:
        return pd.DataFrame()

    numeric = df.select_dtypes(include=[np.number]).copy()
    if glucose_col not in numeric.columns:
        return pd.DataFrame()

    corr = numeric.corr(numeric_only=True)[glucose_col].dropna().sort_values(ascending=False)
    corr = corr.drop(labels=[glucose_col], errors="ignore")
    return corr.head(15).to_frame("corr_with_glucose").reset_index(names="feature")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NHANESの初心者向け意思決定サマリーを作成")
    parser.add_argument("--input", default="data/merged/nhanes_2017_2018.csv", help="merge_nhanes.pyで作成したCSV")
    parser.add_argument("--output-dir", default="outputs/decision_guide", help="出力先")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)
    print(f"Loaded: {args.input} shape={df.shape}")

    scored, used_cols = add_risk_flags(df)
    prevalence = summarize_risk_prevalence(scored)
    by_sex = summarize_by_group(scored, "RIAGENDR")
    if "RIDAGEYR" in scored.columns:
        scored_with_age = scored.assign(
            age_band=pd.cut(
                scored["RIDAGEYR"],
                bins=[0, 29, 44, 59, 120],
                labels=["18-29", "30-44", "45-59", "60+"],
            )
        )
        by_age = summarize_by_group(scored_with_age, "age_band")
    else:
        by_age = pd.DataFrame()
    combos = risk_combo_table(scored)
    glucose_corr = glucose_correlation_table(scored, used_cols["glucose"])

    scored.to_csv(out_dir / "nhanes_with_risk_flags.csv", index=False)
    prevalence.to_csv(out_dir / "risk_prevalence.csv", index=False)
    by_sex.to_csv(out_dir / "risk_by_sex.csv")
    by_age.to_csv(out_dir / "risk_by_age_band.csv")
    combos.to_csv(out_dir / "risk_combo_top10.csv", index=False)
    glucose_corr.to_csv(out_dir / "top_glucose_correlations.csv", index=False)

    print("\n=== 利用した主要列 ===")
    print(pd.Series(used_cols))

    print("\n=== リスク有病率(%) ===")
    print(prevalence)

    print("\n=== 性別ごとのリスク割合(%) ===")
    print(by_sex)

    print("\n=== 年代ごとのリスク割合(%) ===")
    print(by_age)

    print("\n=== よく出るリスク組み合わせ ===")
    print(combos)

    if not glucose_corr.empty:
        print("\n=== 血糖と相関が高い上位特徴 ===")
        print(glucose_corr.head(10))

    print(f"\n出力先: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
