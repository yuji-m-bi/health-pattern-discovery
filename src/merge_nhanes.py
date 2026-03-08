from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


KEY_COLUMN = "SEQN"


def load_xpt_files(data_dir: Path) -> list[tuple[str, pd.DataFrame]]:
    """指定フォルダ内のすべてのXPTファイルを読み込む。"""
    files = sorted(data_dir.glob("*.xpt"))
    if not files:
        raise FileNotFoundError(f"XPTファイルが見つかりません: {data_dir}")

    loaded: list[tuple[str, pd.DataFrame]] = []
    for file_path in files:
        df = pd.read_sas(file_path, format="xport", encoding="utf-8")

        # 列名を文字列へ統一（バイト列対応）
        df.columns = [
            col.decode("utf-8") if isinstance(col, bytes) else str(col)
            for col in df.columns
        ]

        if KEY_COLUMN not in df.columns:
            print(f"[skip] {file_path.name}: {KEY_COLUMN}列がないため結合対象外")
            continue

        loaded.append((file_path.stem, df))

    if not loaded:
        raise ValueError(f"{KEY_COLUMN}列を持つXPTファイルがありません: {data_dir}")

    return loaded


def merge_dataframes(dataframes: list[tuple[str, pd.DataFrame]]) -> pd.DataFrame:
    """SEQNで順番に外部結合し、列名衝突はファイル名サフィックスで解消する。"""
    name, merged = dataframes[0]

    for name, df in dataframes[1:]:
        overlap_cols = [
            col for col in merged.columns.intersection(df.columns) if col != KEY_COLUMN
        ]
        if overlap_cols:
            df = df.rename(columns={col: f"{col}_{name}" for col in overlap_cols})

        merged = merged.merge(df, on=KEY_COLUMN, how="outer")

    return merged


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="指定フォルダ内のNHANES XPTファイルをSEQNで結合して表示します。"
    )
    parser.add_argument(
        "--data-dir",
        default="data/2017_2018",
        help="XPTファイルが置かれているフォルダパス (default: data/2017_2018)",
    )
    parser.add_argument(
        "--output",
        default="",
        help="CSV保存先パス（省略時は保存しない）",
    )
    parser.add_argument(
        "--head",
        type=int,
        default=5,
        help="表示する先頭行数 (default: 5)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = Path(args.data_dir)

    dataframes = load_xpt_files(data_dir)
    merged = merge_dataframes(dataframes)

    print(f"読み込みファイル数: {len(dataframes)}")
    print(f"結合後の形状: {merged.shape}")
    print(merged.head(args.head))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(output_path, index=False)
        print(f"CSVを保存しました: {output_path}")


if __name__ == "__main__":
    main()
