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
            '---\ntitle: "テスト光るペチュニア"\ncategories: ["理系女子サイエンス小説"]\ntags: ["理系女子", "合成生物学"]\n---\n\n本文テストです。\n\n* * *\n\n第2シーンです。\n',
            encoding="utf-8",
        )
        try:
            formatted = format_post_content(str(tmp_md))
            self.assertEqual(formatted.title, "テスト光るペチュニア")
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

    def test_sanitize_html_for_blogger_preserves_closing_tags_on_urls(self):
        raw_html = (
            '<ul>\n'
            '  <li style="margin-bottom: 0.5em;">Kulkarni, S. (2024). <em>Nature</em>. <a href="https://doi.org/10.1038/d41586-024-01332-w">https://doi.org/10.1038/d41586-024-01332-w</a></li>\n'
            '  <li style="margin-bottom: 0.5em;">URL: <a href="https://example.com/paper">https://example.com/paper</a></li>\n'
            '</ul>'
        )
        sanitized = WordPressMailSender._sanitize_html_for_blogger(raw_html)
        self.assertIn("DOI: 10.1038/d41586-024-01332-w</li>", sanitized)
        self.assertNotIn("https://", sanitized)
        self.assertEqual(sanitized.count("<li>"), sanitized.count("</li>"))
        self.assertEqual(sanitized.count("<ul>"), sanitized.count("</ul>"))


if __name__ == "__main__":
    unittest.main()
