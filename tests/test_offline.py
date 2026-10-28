"""离线单元测试：不联网，验证解析、清洗、存储与分析的正确性。

运行：
    python -m tests.test_offline
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import analyze, config, spider, store  # noqa: E402


class TestParseVotes(unittest.TestCase):
    def test_wan_with_plus(self) -> None:
        self.assertEqual(spider.parse_votes("120万+人评价"), 1_200_000)

    def test_decimal_wan(self) -> None:
        self.assertEqual(spider.parse_votes("1.2万人评价"), 12_000)

    def test_thousands_separator(self) -> None:
        self.assertEqual(spider.parse_votes("45,678人评价"), 45_678)

    def test_plain_number(self) -> None:
        self.assertEqual(spider.parse_votes("876人评价"), 876)

    def test_missing(self) -> None:
        self.assertEqual(spider.parse_votes("暂无"), 0)
        self.assertEqual(spider.parse_votes(""), 0)


class TestParsePage(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = config.FIXTURE.read_text(encoding="utf-8") if config.FIXTURE.exists() else ""
        if not cls.html:
            raise unittest.SkipTest("fixture 不存在，先运行 python -m tests.make_fixture")
        cls.records = spider.parse_page(cls.html)

    def test_count(self) -> None:
        self.assertEqual(len(self.records), 25)

    def test_rank_sequence(self) -> None:
        self.assertEqual([r["rank"] for r in self.records], list(range(1, 26)))

    def test_first_record_fields(self) -> None:
        first = self.records[0]
        self.assertEqual(first["title"], "示例专辑 No.01")
        self.assertEqual(first["artist"], "示例歌手甲")
        self.assertEqual(first["year"], "1994")
        self.assertEqual(first["genre"], "摇滚")
        self.assertAlmostEqual(first["rating"], 9.6)
        self.assertEqual(first["votes"], 1_200_000)

    def test_unknown_year_kept_as_unknown(self) -> None:
        record = self.records[23]
        self.assertEqual(record["year"], "未知")
        self.assertEqual(record["title"], "示例专辑 No.24")

    def test_multi_genre_preserved(self) -> None:
        self.assertIn(",", self.records[4]["genre"])

    def test_offset_shifts_rank(self) -> None:
        shifted = spider.parse_page(self.html, offset=25)
        self.assertEqual(shifted[0]["rank"], 26)

    def test_all_fields_present(self) -> None:
        for record in self.records:
            self.assertEqual(set(record), set(spider.FIELDS))


class TestCleanAndStats(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = config.FIXTURE.read_text(encoding="utf-8")
        cls.records = spider.parse_page(cls.html)
        cls.df = analyze.clean(analyze.load_frame(cls.records))

    def test_drop_zero_rating(self) -> None:
        dirty = [{"rank": 1, "title": "t", "artist": "a", "year": "2000", "genre": "流行", "rating": 0, "votes": 0}]
        self.assertTrue(analyze.clean(analyze.load_frame(dirty)).empty)

    def test_dedupe_by_rank(self) -> None:
        duplicated = self.records + [self.records[0]]
        self.assertEqual(len(analyze.clean(analyze.load_frame(duplicated))), 25)

    def test_stats_keys(self) -> None:
        stats = analyze.compute_stats(self.df)
        for key in ("count", "mean_rating", "top_genres", "top_artists", "decade_stats", "rating_votes_pearson"):
            self.assertIn(key, stats)
        self.assertEqual(stats["count"], 25)

    def test_mean_rating_range(self) -> None:
        stats = analyze.compute_stats(self.df)
        self.assertGreater(stats["mean_rating"], 8.0)
        self.assertLess(stats["mean_rating"], 10.0)

    def test_decade_grouping(self) -> None:
        stats = analyze.compute_stats(self.df)
        decades = [row["decade"] for row in stats["decade_stats"]]
        self.assertTrue(all(decade % 10 == 0 for decade in decades))
        self.assertIn(1990, decades)


class TestStore(unittest.TestCase):
    def test_upsert_is_idempotent(self) -> None:
        html = config.FIXTURE.read_text(encoding="utf-8")
        records = spider.parse_page(html)
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "t.db"
            with store.AlbumStore(db) as album_store:
                album_store.upsert_many(records)
                self.assertEqual(album_store.count(), 25)
                album_store.upsert_many(records)  # 重复写入不应新增行
                self.assertEqual(album_store.count(), 25)
                self.assertEqual(album_store.max_rank(), 25)
                self.assertEqual(len(album_store.fetch_all()), 25)

    def test_upsert_updates_changed_value(self) -> None:
        records = [{"rank": 1, "title": "a", "artist": "x", "year": "2000",
                    "genre": "流行", "rating": 8.0, "votes": 10}]
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "t.db"
            with store.AlbumStore(db) as album_store:
                album_store.upsert_many(records)
                album_store.upsert_many([{**records[0], "rating": 9.9}])
                self.assertAlmostEqual(album_store.fetch_all()[0]["rating"], 9.9)


if __name__ == "__main__":
    unittest.main(verbosity=2)