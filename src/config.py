"""全局配置：反爬参数、请求头池、路径约定。"""

from __future__ import annotations

import os
from pathlib import Path

BASE_URL = "https://music.douban.com/top250?start={start}"
PAGE_SIZE = 25
TOTAL_PAGES = 10

# 反爬策略：请求头池 + 随机间隔 + 指数退避
USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Edge/128.0.0.0 Safari/537.36",
)

MIN_DELAY, MAX_DELAY = 5.0, 8.0
MAX_RETRIES = 3
TIMEOUT = 15

# 豆瓣对未登录请求会返回验证页；如需抓取，从浏览器复制 bid Cookie 到环境变量
DOUBAN_BID = os.environ.get("DOUBAN_BID", "")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
FIXTURE = ROOT / "tests" / "fixtures" / "top250_page.html"
DB_PATH = DATA_DIR / "douban_music.db"

CSV_PATH = DATA_DIR / "douban_top250.csv"
STATS_PATH = DATA_DIR / "stats.json"
CHART_PATH = OUTPUT_DIR / "douban_top250_report.png"