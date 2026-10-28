"""生成测试用 HTML fixture（合成数据，非真实豆瓣页面）。

固定种子 + 固定数据表，保证每次生成结果一致，测试断言才能稳定。
"""

from __future__ import annotations

from pathlib import Path

# (标题, 演唱者, 年份, 风格, 评分, 评价人数原文)
ALBUMS: tuple[tuple[str, str, str, str, float, str], ...] = (
    ("示例专辑 No.01", "示例歌手甲", "1994", "摇滚", 9.6, "120万+人评价"),
    ("示例专辑 No.02", "示例歌手乙", "2001", "流行", 9.4, "98万+人评价"),
    ("示例专辑 No.03", "示例歌手丙", "1987", "摇滚", 9.5, "1.2万人评价"),
    ("示例专辑 No.04", "示例歌手丁", "2010", "民谣", 8.9, "45,678人评价"),
    ("示例专辑 No.05", "示例歌手戊", "1999", "流行,电子", 9.1, "23万人评价"),
    ("示例专辑 No.06", "示例歌手己", "1983", "古典", 9.3, "8,901人评价"),
    ("示例专辑 No.07", "示例歌手庚", "2015", "说唱", 8.4, "1.1万人评价"),
    ("示例专辑 No.08", "示例歌手辛", "1979", "爵士", 9.0, "5,432人评价"),
    ("示例专辑 No.09", "示例歌手壬", "2008", "流行", 8.7, "暂无"),
    ("示例专辑 No.10", "示例歌手癸", "1992", "摇滚", 9.2, "67万人评价"),
    ("示例专辑 No.11", "示例歌手甲", "2018", "电子", 8.2, "3,210人评价"),
    ("示例专辑 No.12", "示例歌手乙", "1971", "摇滚", 9.4, "2.3万人评价"),
    ("示例专辑 No.13", "示例歌手丙", "2005", "民谣", 8.8, "12万人评价"),
    ("示例专辑 No.14", "示例歌手丁", "1997", "流行,摇滚", 9.0, "9.9万人评价"),
    ("示例专辑 No.15", "示例歌手戊", "1988", "古典", 9.5, "4,567人评价"),
    ("示例专辑 No.16", "示例歌手己", "2019", "说唱", 7.9, "876人评价"),
    ("示例专辑 No.17", "示例歌手庚", "1969", "爵士", 9.1, "1,234人评价"),
    ("示例专辑 No.18", "示例歌手辛", "2003", "电子", 8.5, "7.7万人评价"),
    ("示例专辑 No.19", "示例歌手壬", "1995", "民谣", 9.2, "34万人评价"),
    ("示例专辑 No.20", "示例歌手癸", "2020", "流行", 7.8, "5,678人评价"),
    ("示例专辑 No.21", "示例歌手甲", "1985", "摇滚", 9.3, "2.1万人评价"),
    ("示例专辑 No.22", "示例歌手乙", "2007", "古典", 8.6, "6,789人评价"),
    ("示例专辑 No.23", "示例歌手丙", "1990", "电子", 8.9, "15万人评价"),
    ("示例专辑 No.24", "示例歌手丁", "未知", "民谣", 8.0, "9,012人评价"),
    ("示例专辑 No.25", "示例歌手戊", "2013", "流行", 8.3, "4.4万人评价"),
)

ITEM_TEMPLATE = """      <div class="list-item">
        <div class="pic"><a href="https://music.douban.com/subject/1/" target="_blank"><img src="cover.jpg"></a></div>
        <div class="content">
          <div class="title-row"><a class="title" href="https://music.douban.com/subject/1/">{title}</a></div>
          <div class="subtitle">{artist} / {year} / {genre}</div>
          <div class="rating"><span class="rating-star"></span><span class="rating_num">{rating}</span>
            <span class="rating_people">{votes}</span></div>
        </div>
      </div>
"""

PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>豆瓣音乐 Top250 · 测试 Fixture</title></head>
<body>
  <div class="article">
    <div class="list">
{items}    </div>
  </div>
</body>
</html>
"""


def build_html() -> str:
    items = "".join(
        ITEM_TEMPLATE.format(title=title, artist=artist, year=year, genre=genre, rating=rating, votes=votes)
        for title, artist, year, genre, rating, votes in ALBUMS
    )
    return PAGE.format(items=items)


def main() -> None:
    target = Path(__file__).with_name("fixtures") / "top250_page.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_html(), encoding="utf-8")
    print(f"wrote {target} ({len(ALBUMS)} items, {target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()