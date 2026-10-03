import unittest
from pathlib import Path
from src.config import get_config
from src.post_formatter import format_post_content
from src.mail_sender import WordPressMailSender
from src.history_manager import HistoryManager


class TestRikejoSystem(unittest.TestCase):
    def test_catalog_and_lorebook_loaded(self):
        hm = HistoryManager()
        self.assertGreaterEqual(len(hm.catalog), 10)
        self.assertEqual(hm.catalog[0]["id"], "ep01-bioluminescence-plant")

    def test_post_formatter_and_dry_run_sender(self):
        tmp_md = Path("tests/_tmp_test_ep.md")
        tmp_md.write_text(
            '---\ntitle: "【第1話】テスト光るペチュニア"\ncategories: ["理系女子サイエンス小説"]\ntags: ["理系女子", "合成生物学"]\n---\n\n本文テストです。\n\n* * *\n\n第2シーンです。\n',
            encoding="utf-8",
        )
        try:
            formatted = format_post_content(str(tmp_md))
            self.assertEqual(formatted.title, "【第1話】テスト光るペチュニア")
            self.assertIn("✦ ✦ ✦", formatted.content_html)
            self.assertNotIn("<hr", formatted.content_html.lower())

            cfg = get_config()
            sender = WordPressMailSender(cfg)
            res = sender.send_post(formatted, dry_run=True)
            self.assertTrue(res["success"])
            self.assertTrue(res["dry_run"])
        finally:
            if tmp_md.exists():
                tmp_md.unlink()


if __name__ == "__main__":
    unittest.main()
