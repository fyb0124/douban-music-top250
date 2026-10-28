"""可视化层：一张四联图覆盖分布、结构、趋势与相关性。"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # 无界面环境也能出图

import matplotlib.pyplot as plt
import pandas as pd

from . import analyze, config

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

ACCENT = "#2F7D6D"
ACCENT_LIGHT = "#8FC1B5"


def build_charts(records: list[dict], out_path: Path = config.CHART_PATH) -> Path:
    df = analyze.clean(analyze.load_frame(records))
    if df.empty:
        raise ValueError("没有可可视化的数据")

    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))
    fig.suptitle("豆瓣音乐 Top250 专辑数据画像", fontsize=16, fontweight="bold")

    # 1. 评分分布
    ax = axes[0][0]
    ax.hist(df["rating"], bins=12, color=ACCENT, alpha=0.85, edgecolor="white")
    ax.axvline(df["rating"].mean(), color="#C0392B", linestyle="--", linewidth=1.2,
               label=f"均值 {df['rating'].mean():.2f}")
    ax.set_title("评分分布")
    ax.set_xlabel("豆瓣评分")
    ax.set_ylabel("专辑数量")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25, linestyle=":")

    # 2. 风格 TOP10
    ax = axes[0][1]
    genres = (
        df.assign(genre=df["genre"].str.split(","))
        .explode("genre")["genre"].str.strip()
        .replace("未知风格", pd.NA).dropna().value_counts().head(10)
    )
    ax.barh(genres.index[::-1], genres.values[::-1], color=ACCENT_LIGHT, edgecolor="white")
    for i, value in enumerate(genres.values[::-1]):
        ax.text(value, i, f" {value}", va="center", fontsize=9)
    ax.set_title("风格分布 Top10")
    ax.set_xlabel("专辑数量")
    ax.grid(axis="x", alpha=0.25, linestyle=":")

    # 3. 年代趋势
    ax = axes[1][0]
    decades = df.dropna(subset=["year_num"]).copy()
    if not decades.empty:
        decades["decade"] = (decades["year_num"] // 10 * 10).astype(int)
        grouped = decades.groupby("decade")["rating"].agg(["mean", "size"])
        ax.plot(grouped.index, grouped["mean"], marker="o", color=ACCENT, linewidth=2)
        for decade, row in grouped.iterrows():
            ax.annotate(f"n={int(row['size'])}", (decade, row["mean"]),
                        textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
        ax.set_title("各年代平均评分")
        ax.set_xlabel("发行年代")
        ax.set_ylabel("平均评分")
        ax.grid(alpha=0.25, linestyle=":")
    else:
        ax.text(0.5, 0.5, "年份数据缺失", ha="center", va="center")
        ax.set_axis_off()

    # 4. 评分与人气相关性
    ax = axes[1][1]
    ax.scatter(df["votes"], df["rating"], s=28, color=ACCENT, alpha=0.7, edgecolor="white")
    ax.set_title(f"评分 vs 评价人数（Pearson r={df['rating'].corr(df['votes']):.2f}）")
    ax.set_xlabel("评价人数")
    ax.set_ylabel("豆瓣评分")
    ax.grid(alpha=0.25, linestyle=":")

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path