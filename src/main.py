"""命令行入口：采集 → 落库 → 分析 → 出图。

用法：
    python -m src.main              # 真实抓取 10 页
    python -m src.main --pages 2    # 只抓前 2 页
    python -m src.main --offline    # 用内置 fixture 跑通全流程（无需联网）
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import analyze, config, spider, store, visualize


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="豆瓣音乐 Top250 数据采集与分析流水线")
    parser.add_argument("--offline", action="store_true", help="使用内置 HTML fixture，不联网")
    parser.add_argument("--pages", type=int, default=config.TOTAL_PAGES, help="抓取页数（默认 10）")
    parser.add_argument("--db", type=Path, default=config.DB_PATH, help="SQLite 数据库路径")
    parser.add_argument("--outdir", type=Path, default=config.OUTPUT_DIR, help="图表输出目录")
    return parser.parse_args(argv)


def collect_offline() -> list[dict]:
    html = config.FIXTURE.read_text(encoding="utf-8")
    return spider.parse_page(html, offset=0)


def collect_online(pages: int) -> list[dict]:
    records: list[dict] = []
    for page_records in spider.crawl(pages=pages):
        records.extend(page_records)
    return records


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.offline:
        print("[info] 离线模式：解析内置 fixture")
        records = collect_offline()
    else:
        if not config.DOUBAN_BID:
            print("[warn] 未设置 DOUBAN_BID 环境变量，豆瓣可能返回验证页", file=sys.stderr)
        records = collect_online(args.pages)

    if not records:
        print("[error] 未采集到任何数据", file=sys.stderr)
        return 1

    with store.AlbumStore(args.db) as album_store:
        inserted = album_store.upsert_many(records)
        total = album_store.count()
        print(f"[info] 本次写入 {inserted} 条，库内共 {total} 条")

    stats = analyze.export(records, stats_path=config.STATS_PATH)
    chart = visualize.build_charts(records, out_path=args.outdir / config.CHART_PATH.name)

    print("\n===== 数据概览 =====")
    print(f"专辑数        : {stats['count']}")
    print(f"平均评分      : {stats['mean_rating']}")
    print(f"评分区间      : {stats['min_rating']} ~ {stats['max_rating']}")
    print(f"评价人数总计  : {stats['total_votes']:,}")
    print(f"评分-人气相关 : r = {stats['rating_votes_pearson']}")
    print(f"风格 Top3     : {list(stats['top_genres'].items())[:3]}")
    print(f"歌手 Top3     : {list(stats['top_artists'].items())[:3]}")
    print(f"\nCSV  : {config.CSV_PATH}")
    print(f"JSON : {config.STATS_PATH}")
    print(f"图表 : {chart}")
    print("\n" + json.dumps(stats["decade_stats"], ensure_ascii=False)[:300])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())