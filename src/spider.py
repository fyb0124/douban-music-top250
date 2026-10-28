"""采集层：HTML 解析与网络请求分离，解析函数可离线单测。"""

from __future__ import annotations

import random
import re
import time
from typing import Iterable

import requests
from bs4 import BeautifulSoup

from . import config

# 单页解析结果字段
FIELDS = ("rank", "title", "artist", "year", "genre", "rating", "votes")


def parse_votes(text: str) -> int:
    """把「1.2万」「12,345」「120万+人评价」统一转成整数。"""
    if not text:
        return 0
    cleaned = text.replace("人评价", "").replace(",", "").replace("+", "").strip()
    if "万" in cleaned:
        number = cleaned.replace("万", "").strip()
        try:
            return int(float(number) * 10000)
        except ValueError:
            return 0
    digits = re.sub(r"\D", "", cleaned)
    return int(digits) if digits else 0


def parse_page(html: str, offset: int = 0) -> list[dict]:
    """解析一页 HTML，返回专辑记录列表。

    offset 是该页第一条记录的全局偏移量（第 2 页 offset=25），
    用于还原真实排名。
    """
    soup = BeautifulSoup(html, "lxml")
    items = soup.select("div.list-item")
    records: list[dict] = []

    for index, item in enumerate(items, start=1):
        title_tag = item.select_one("a.title")
        subtitle_tag = item.select_one("div.subtitle")
        rating_tag = item.select_one("span.rating_num")
        people_tag = item.select_one("span.rating_people")

        title = title_tag.get_text(strip=True) if title_tag else f"未知专辑_{offset + index}"

        artist, year, genre = "未知歌手", "未知", "未知风格"
        if subtitle_tag:
            parts = [p.strip() for p in subtitle_tag.get_text(" ", strip=True).split(" / ")]
            if parts:
                artist = parts[0] or artist
            if len(parts) >= 2 and re.fullmatch(r"\d{4}", parts[1]):
                year = parts[1]
            if len(parts) >= 3:
                genre = parts[-1] or genre

        rating = 0.0
        if rating_tag:
            try:
                rating = float(rating_tag.get_text(strip=True))
            except ValueError:
                rating = 0.0

        records.append(
            {
                "rank": offset + index,
                "title": title,
                "artist": artist,
                "year": year,
                "genre": genre,
                "rating": rating,
                "votes": parse_votes(people_tag.get_text() if people_tag else ""),
            }
        )
    return records


def _headers() -> dict[str, str]:
    headers = {
        "User-Agent": random.choice(config.USER_AGENTS),
        "Referer": "https://music.douban.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    if config.DOUBAN_BID:
        headers["Cookie"] = f"bid={config.DOUBAN_BID};"
    return headers


def fetch_page(session: requests.Session, start: int) -> str:
    """抓取一页，失败按指数退避重试。"""
    url = config.BASE_URL.format(start=start)
    last_error: Exception | None = None

    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            resp = session.get(url, headers=_headers(), timeout=config.TIMEOUT)
            resp.encoding = "utf-8"
            # 未登录时豆瓣会跳验证页，用页面标题做有效性校验
            if "豆瓣音乐" not in resp.text:
                raise RuntimeError("命中反爬验证页")
            return resp.text
        except Exception as exc:  # noqa: BLE001 - 需要覆盖网络与解析异常
            last_error = exc
            backoff = config.MIN_DELAY * (2 ** (attempt - 1))
            print(f"[warn] 第 {start // config.PAGE_SIZE + 1} 页第 {attempt} 次失败：{exc}，{backoff:.0f}s 后重试")
            time.sleep(backoff)

    raise RuntimeError(f"抓取失败：{url}") from last_error


def crawl(pages: int = config.TOTAL_PAGES, session: requests.Session | None = None) -> Iterable[list[dict]]:
    """逐页抓取，每页之间随机休眠，产出解析好的记录列表。"""
    sess = session or requests.Session()
    for page_no in range(pages):
        start = page_no * config.PAGE_SIZE
        html = fetch_page(sess, start)
        records = parse_page(html, offset=start)
        print(f"[info] 第 {page_no + 1}/{pages} 页解析 {len(records)} 条")
        yield records
        if page_no < pages - 1:
            time.sleep(random.uniform(config.MIN_DELAY, config.MAX_DELAY))