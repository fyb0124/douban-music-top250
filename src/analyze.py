"""分析层：pandas 多维统计，输出结构化 JSON 供可视化与报告复用。"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import config


def load_frame(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    if df.empty:
        return df
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)
    df["year_num"] = pd.to_numeric(df["year"], errors="coerce")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """去重（排名唯一）、剔除无效评分、补齐缺失字段。"""
    if df.empty:
        return df
    df = df.drop_duplicates(subset=["rank"]).sort_values("rank").reset_index(drop=True)
    df = df[df["rating"] > 0]
    for column in ("title", "artist", "genre"):
        df[column] = df[column].fillna("未知").replace("", "未知")
    return df


def compute_stats(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"count": 0}

    # 风格字段可能是「流行,摇滚」，按逗号拆开做多标签统计
    exploded = (
        df.assign(genre=df["genre"].str.split(","))
        .explode("genre")["genre"]
        .str.strip()
        .replace("未知风格", pd.NA)
        .dropna()
    )
    genre_counts = exploded.value_counts().head(10).to_dict()

    # 年代分布：按发行年份整除 10 取整
    decades = df.dropna(subset=["year_num"]).assign(
        decade=lambda d: (d["year_num"] // 10 * 10).astype(int)
    )
    decade_stats = (
        decades.groupby("decade")
        .agg(count=("rank", "size"), mean_rating=("rating", "mean"))
        .round(2)
        .reset_index()
        .to_dict("records")
    )

    correlation = 0.0
    if len(df) >= 3 and df["votes"].std() > 0 and df["rating"].std() > 0:
        correlation = round(float(df["rating"].corr(df["votes"])), 4)

    return {
        "count": int(len(df)),
        "mean_rating": round(float(df["rating"].mean()), 2),
        "median_rating": round(float(df["rating"].median()), 2),
        "min_rating": round(float(df["rating"].min()), 2),
        "max_rating": round(float(df["rating"].max()), 2),
        "total_votes": int(df["votes"].sum()),
        "median_votes": int(df["votes"].median()),
        "rating_votes_pearson": correlation,
        "top_genres": genre_counts,
        "top_artists": df["artist"].value_counts().head(10).to_dict(),
        "decade_stats": decade_stats,
    }


def export(records: list[dict], csv_path: Path = config.CSV_PATH, stats_path: Path = config.STATS_PATH) -> dict:
    df = clean(load_frame(records))
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.drop(columns=["year_num"], errors="ignore").to_csv(csv_path, index=False, encoding="utf-8-sig")

    stats = compute_stats(df)
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats