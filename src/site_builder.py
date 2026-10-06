import html
import json
import logging
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.history_manager import HistoryManager
from src.post_formatter import (
    parse_markdown_with_frontmatter,
    HAS_MARKDOWN,
    _fallback_markdown_to_html,
)

if HAS_MARKDOWN:
    import markdown

logger = logging.getLogger(__name__)
JST = timezone(timedelta(hours=9))

DOCS_DIR = Path("docs")
STORIES_DIR = DOCS_DIR / "stories"
IMAGES_DIR = DOCS_DIR / "assets" / "images"


def _render_web_markdown(md_text: str) -> str:
    """
    Renders episode Markdown to clean semantic HTML for the GitHub Pages web reader,
    preserving clickable DOI links and removing any legacy system/preview lines.
    """
    cleaned = re.sub(r"^\s*\[(?:category|tags|status)[^\]]*\]\s*$", "", md_text, flags=re.MULTILINE)
    cleaned = re.sub(r"^#\s*(?:【?第\s*\d+\s*話】?\s*)?.*?\n+", "", cleaned)
    cleaned = re.sub(r"^###\s*(?:シーン|Scene|第\d+章|第\d+節|起|承|転|結).*?\n+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^[ \t]*[\*\_\-]*\s*執筆システム[:：][^\n]*\n?", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(
        r"\n*(?:---|✦ ✦ ✦|◆ ◆ ◆|\* \* \*)\s*\n+###\s*🌸\s*【次回エピソード予告】.*$",
        "",
        cleaned,
        flags=re.DOTALL,
    )
    cleaned = re.sub(r"^[ \t]*[-*_]{3,}[ \t]*$", "✦ ✦ ✦", cleaned, flags=re.MULTILINE)

    if HAS_MARKDOWN:
        rendered = markdown.markdown(cleaned, extensions=["extra", "sane_lists", "tables", "nl2br"])
    else:
        rendered = _fallback_markdown_to_html(cleaned)

    rendered = re.sub(
        r"<p>\s*(?:✦ ✦ ✦|◆ ◆ ◆|\* \* \*)\s*</p>|<hr\s*/?>",
        '<div class="scene-divider">✦ ✦ ✦</div>',
        rendered,
        flags=re.IGNORECASE,
    )
    rendered = re.sub(
        r"<a\b([^>]*?)>",
        r'<a\1 target="_blank" rel="noopener noreferrer">',
        rendered,
        flags=re.IGNORECASE,
    )
    return rendered


def _classify_field(faculty: str, theme: str) -> str:
    text = f"{faculty} {theme}"
    if any(k in text for k in ("数学", "数理", "トポロジー", "位相幾何", "統計")):
        return "数学・数理科学"
    if any(k in text for k in ("情報", "コンピュータ", "アルゴリズム", "暗号", "AI", "ネットワーク")):
        return "情報学・AI"
    if any(k in text for k in ("物理", "天文", "宇宙", "量子", "フォトニクス", "光学")):
        return "物理学・宇宙・光学"
    if any(k in text for k in ("化学", "薬学", "材料", "ナノ", "ペロブスカイト", "エネルギー")):
        return "化学・薬学・材料"
    return "生命科学・バイオ・医学"


def collect_all_stories(history_mgr: Optional[HistoryManager] = None) -> List[Dict[str, Any]]:
    """
    Collects all episodes in content/ matched against data/science_catalog.json.
    Orders episodes cleanly by catalog sequence.
    """
    if history_mgr is None:
        history_mgr = HistoryManager()

    stories: List[Dict[str, Any]] = []
    used_files = set()

    for idx, work in enumerate(history_mgr.catalog, start=1):
        wid = work["id"]
        md_path = history_mgr.find_stock_file_for_work(wid)
        if md_path is None or not md_path.exists():
            continue
        used_files.add(md_path.resolve())
        meta, body = parse_markdown_with_frontmatter(str(md_path))
        raw_title = meta.get("title", "").strip().strip("『』\"'") or work.get("title", "")
        full_title = re.sub(r"^【?第\s*\d+\s*話】?\s*", "", raw_title).strip()
        if "――" in full_title:
            main_title, subtitle = [p.strip() for p in full_title.split("――", 1)]
        else:
            main_title, subtitle = full_title, ""

        png_path = md_path.with_suffix(".png")
        has_image = png_path.exists()
        image_rel = f"assets/images/{wid}.png" if has_image else ""

        faculty = work.get("faculty", meta.get("faculty", ""))
        theme = work.get("theme", "")
        field_cat = _classify_field(faculty, theme)
        char_count = len(re.sub(r"\s+", "", body))

        stories.append({
            "no": len(stories) + 1,
            "catalog_no": work.get("episode_num", idx),
            "work_id": wid,
            "full_title": full_title,
            "main_title": main_title,
            "subtitle": subtitle,
            "faculty": faculty,
            "field_cat": field_cat,
            "protagonist": work.get("protagonist", ""),
            "mentor": work.get("mentor", ""),
            "theme": theme,
            "modern_tech": work.get("modern_tech", theme),
            "summary": work.get("summary", ""),
            "tags": meta.get("tags", ["理系女子", "サイエンス小説", field_cat]),
            "md_path": md_path,
            "png_path": png_path if has_image else None,
            "has_image": has_image,
            "image_rel": image_rel,
            "page_rel": f"stories/{wid}.html",
            "char_count": char_count,
            "body_md": body,
        })

    return stories


def _write_stylesheet(target_css: Path):
    css = """/* Rikejo Science Novel Library - GitHub Pages Stylesheet */
:root {
  --bg-primary: #fdf8fb;
  --bg-secondary: #f5edf3;
  --bg-card: #ffffff;
  --bg-reader: #ffffff;
  --text-primary: #1e293b;
  --text-secondary: #475569;
  --text-muted: #64748b;
  --accent: #be185d;
  --accent-soft: rgba(190, 24, 93, 0.1);
  --teal: #0369a1;
  --border: #e2d5e0;
  --reader-font-size: 17.5px;
}

[data-theme="dark"] {
  --bg-primary: #111622;
  --bg-secondary: #192132;
  --bg-card: #1e283c;
  --bg-reader: #161e2e;
  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-muted: #94a3b8;
  --accent: #f472b6;
  --accent-soft: rgba(244, 114, 182, 0.15);
  --teal: #38bdf8;
  --border: #2e3c56;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: "Hiragino Kaku Gothic ProN", "Yu Gothic", "Meiryo", sans-serif;
  line-height: 1.8;
  transition: background-color 0.25s ease, color 0.25s ease;
}

a {
  color: var(--accent);
  text-decoration: none;
}
a:hover {
  text-decoration: underline;
}

/* Header & Hero */
.site-header {
  background: linear-gradient(135deg, #3b0764 0%, #831843 55%, #0f172a 100%);
  border-bottom: 1px solid var(--border);
  padding: 2.8rem 1.5rem 2.2rem;
  text-align: center;
  color: #f8fafc;
}
.site-badge {
  display: inline-block;
  font-size: 0.78rem;
  letter-spacing: 0.12em;
  padding: 0.3rem 0.95rem;
  border-radius: 999px;
  background: rgba(244, 114, 182, 0.22);
  border: 1px solid rgba(244, 114, 182, 0.45);
  color: #fbcfe8;
  margin-bottom: 0.9rem;
}
.site-title {
  font-family: "Hiragino Mincho ProN", "Yu Mincho", "Noto Serif JP", serif;
  font-size: clamp(1.65rem, 3.5vw, 2.5rem);
  font-weight: 700;
  margin: 0 0 0.7rem;
  letter-spacing: 0.04em;
}
.site-subtitle {
  max-width: 800px;
  margin: 0 auto 1.5rem;
  color: #f1f5f9;
  font-size: 0.96rem;
  opacity: 0.92;
}
.stats-bar {
  display: flex;
  justify-content: center;
  gap: 1.1rem;
  flex-wrap: wrap;
  margin-top: 1rem;
}
.stat-pill {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  padding: 0.45rem 1rem;
  font-size: 0.86rem;
  color: #f8fafc;
}
.stat-pill strong {
  color: #f9a8d4;
  font-size: 1.05rem;
  margin-right: 0.25rem;
}

/* Controls & Toolbar */
.container {
  max-width: 1180px;
  margin: 0 auto;
  padding: 1.8rem 1.25rem 4rem;
}
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1rem 1.2rem;
  margin-bottom: 1.8rem;
}
.filter-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  align-items: center;
  flex: 1;
}
.search-input, .select-filter {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.55rem 0.85rem;
  font-size: 0.9rem;
}
.search-input {
  min-width: 220px;
  flex: 1;
}
.btn-toggle {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.5rem 0.85rem;
  font-size: 0.85rem;
  cursor: pointer;
}
.btn-toggle:hover {
  border-color: var(--accent);
}

/* Story Cards Grid with Container Queries */
.story-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));
  gap: 1.4rem;
}
.story-card-wrap {
  container-type: inline-size;
}
.story-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}
.story-card:hover {
  transform: translateY(-3px);
  border-color: var(--accent);
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.12);
}
@supports (container-type: inline-size) {
  @container (min-width: 560px) {
    .story-card {
      flex-direction: row;
    }
    .card-thumb-wrap {
      width: 220px;
      flex-shrink: 0;
    }
  }
}
.card-thumb-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  background: linear-gradient(135deg, #3b0764 0%, #1e293b 100%);
  overflow: hidden;
}
.card-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.card-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.2rem;
  text-align: center;
  color: #f1f5f9;
  font-family: "Hiragino Mincho ProN", "Yu Mincho", serif;
}
.card-no-badge {
  position: absolute;
  top: 0.65rem;
  left: 0.65rem;
  background: rgba(15, 23, 42, 0.84);
  color: #f9a8d4;
  border: 1px solid rgba(244, 114, 182, 0.45);
  font-size: 0.76rem;
  font-weight: 700;
  padding: 0.2rem 0.6rem;
  border-radius: 6px;
}
.card-body {
  padding: 1.2rem 1.25rem 1.35rem;
  display: flex;
  flex-direction: column;
  flex: 1;
}
.card-faculty {
  font-size: 0.8rem;
  color: var(--teal);
  font-weight: 600;
  margin-bottom: 0.35rem;
}
.card-title {
  font-family: "Hiragino Mincho ProN", "Yu Mincho", "Noto Serif JP", serif;
  font-size: 1.16rem;
  font-weight: 700;
  margin: 0 0 0.55rem;
  line-height: 1.45;
}
.card-title a {
  color: var(--text-primary);
}
.card-title a:hover {
  color: var(--accent);
  text-decoration: none;
}
.card-tech {
  font-size: 0.78rem;
  background: var(--accent-soft);
  color: var(--accent);
  padding: 0.28rem 0.65rem;
  border-radius: 6px;
  margin-bottom: 0.75rem;
  line-height: 1.45;
}
.card-summary {
  font-size: 0.87rem;
  color: var(--text-secondary);
  margin: 0 0 1rem;
  flex: 1;
}
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--border);
  padding-top: 0.75rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}
.read-link {
  font-weight: 600;
  color: var(--accent);
}

/* Story Reader Page */
.reader-nav {
  position: sticky;
  top: 0;
  z-index: 50;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  padding: 0.7rem 1.25rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.6rem;
}
.reader-controls {
  display: flex;
  gap: 0.45rem;
  align-items: center;
}
.reader-container {
  max-width: 820px;
  margin: 2rem auto 4.5rem;
  padding: 2.5rem 2.2rem;
  background: var(--bg-reader);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
}
@media (max-width: 640px) {
  .reader-container {
    margin: 0.75rem;
    padding: 1.4rem 1.15rem;
  }
}
.story-meta-box {
  background: var(--bg-secondary);
  border-left: 4px solid var(--accent);
  border-radius: 8px;
  padding: 1rem 1.2rem;
  margin-bottom: 1.8rem;
  font-size: 0.9rem;
}
.story-meta-box div {
  margin-bottom: 0.35rem;
}
.story-meta-box div:last-child {
  margin-bottom: 0;
}
.story-hero-image {
  width: 100%;
  max-width: 520px;
  margin: 0 auto 2rem;
  display: block;
  border-radius: 12px;
  border: 1px solid var(--border);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
}
.story-header-title {
  font-family: "Hiragino Mincho ProN", "Yu Mincho", "Noto Serif JP", serif;
  font-size: clamp(1.45rem, 3vw, 2.05rem);
  line-height: 1.45;
  margin: 0 0 1.2rem;
}
.story-content {
  font-family: "Hiragino Mincho ProN", "Yu Mincho", "Noto Serif JP", serif;
  font-size: var(--reader-font-size);
  line-height: 2.0;
  color: var(--text-primary);
}
.story-content p {
  margin: 0 0 1.45em;
  text-align: justify;
}
.story-content h2, .story-content h3, .story-content h4 {
  font-family: "Hiragino Kaku Gothic ProN", "Yu Gothic", sans-serif;
  margin-top: 2.2em;
  margin-bottom: 0.8em;
  padding-bottom: 0.35em;
  border-bottom: 2px solid var(--border);
  color: var(--accent);
}
.story-content blockquote {
  background: var(--bg-secondary);
  border-left: 4px solid var(--accent);
  margin: 1.5em 0;
  padding: 1em 1.3em;
  border-radius: 8px;
}
.story-content ul, .story-content ol {
  padding-left: 1.5em;
  margin-bottom: 1.5em;
}
.story-content li {
  margin-bottom: 0.65em;
  line-height: 1.8;
}
.scene-divider {
  text-align: center;
  margin: 2.4em 0;
  letter-spacing: 0.5em;
  color: var(--accent);
  font-size: 0.95rem;
}
.story-pager {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
  flex-wrap: wrap;
}
.pager-btn {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.8rem 1.1rem;
  color: var(--text-primary);
  font-size: 0.9rem;
  max-width: 48%;
}
.pager-btn:hover {
  border-color: var(--accent);
  text-decoration: none;
}
.site-footer {
  text-align: center;
  padding: 2.5rem 1rem;
  border-top: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 0.85rem;
}
"""
    target_css.write_text(css, encoding="utf-8")


def _build_story_page(
    story: Dict[str, Any],
    prev_story: Optional[Dict[str, Any]],
    next_story: Optional[Dict[str, Any]],
) -> str:
    rendered_body = _render_web_markdown(story["body_md"])
    hero_img_html = ""
    if story["has_image"]:
        hero_img_html = (
            f'<img class="story-hero-image" src="../{html.escape(story["image_rel"])}" '
            f'alt="{html.escape(story["full_title"])}" loading="lazy" />'
        )

    prev_html = (
        f'<a class="pager-btn" href="{html.escape(prev_story["work_id"])}.html">'
        f'← 前の作品：#{prev_story["no"]:02d} {html.escape(prev_story["main_title"])}</a>'
        if prev_story
        else "<span></span>"
    )
    next_html = (
        f'<a class="pager-btn" href="{html.escape(next_story["work_id"])}.html">'
        f'次の作品：#{next_story["no"]:02d} {html.escape(next_story["main_title"])} →</a>'
        if next_story
        else "<span></span>"
    )

    chars_line = ""
    if story.get("protagonist") or story.get("mentor"):
        chars_line = (
            f'<div><strong>👩‍🔬 登場人物：</strong>{html.escape(story.get("protagonist", ""))}'
            f' ／ {html.escape(story.get("mentor", ""))}</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="ja" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(story["full_title"])} | 放課後サイエンス・キャンパス 理系女子ライトノベル図書館</title>
  <link rel="stylesheet" href="../style.css" />
</head>
<body>
  <nav class="reader-nav">
    <a href="../index.html">← 作品一覧（キャンパス図書館トップ）へ戻る</a>
    <div class="reader-controls">
      <button class="btn-toggle" onclick="setFontSize('15.5px')">文字 小</button>
      <button class="btn-toggle" onclick="setFontSize('17.5px')">文字 中</button>
      <button class="btn-toggle" onclick="setFontSize('20px')">文字 大</button>
      <button class="btn-toggle" onclick="toggleTheme()" id="themeBtn">🌙 ダーク表示</button>
    </div>
  </nav>

  <main class="reader-container">
    <div class="site-badge">EPISODE ARCHIVE #{story["no"]:02d} ・ {html.escape(story["field_cat"])}</div>
    <h1 class="story-header-title">{html.escape(story["full_title"])}</h1>

    <div class="story-meta-box">
      <div><strong>🏛️ 舞台となる大学・研究室：</strong>{html.escape(story["faculty"])}</div>
      <div><strong>🔬 科学・数理・情報テーマ：</strong>{html.escape(story["theme"])}</div>
      {chars_line}
    </div>

    {hero_img_html}

    <article class="story-content">
      {rendered_body}
    </article>

    <div class="story-pager">
      {prev_html}
      {next_html}
    </div>
  </main>

  <footer class="site-footer">
    <p>『放課後サイエンス・キャンパス』理系女子ライトノベル図書館 — Powered by Local LLM (Qwen3.5 &amp; shosetsu) &amp; FLUX.2 on Mac mini M4</p>
  </footer>

  <script>
    function toggleTheme() {{
      const root = document.documentElement;
      const curr = root.getAttribute('data-theme') || 'light';
      const next = curr === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      localStorage.setItem('rikejo_theme', next);
      document.getElementById('themeBtn').textContent = next === 'dark' ? '☀️ ライト表示' : '🌙 ダーク表示';
    }}
    function setFontSize(size) {{
      document.documentElement.style.setProperty('--reader-font-size', size);
      localStorage.setItem('rikejo_font_size', size);
    }}
    (function initPrefs() {{
      const savedTheme = localStorage.getItem('rikejo_theme');
      if (savedTheme) {{
        document.documentElement.setAttribute('data-theme', savedTheme);
        document.getElementById('themeBtn').textContent = savedTheme === 'dark' ? '☀️ ライト表示' : '🌙 ダーク表示';
      }}
      const savedSize = localStorage.getItem('rikejo_font_size');
      if (savedSize) {{
        document.documentElement.style.setProperty('--reader-font-size', savedSize);
      }}
    }})();
  </script>
</body>
</html>
"""


def _build_index_page(stories: List[Dict[str, Any]]) -> str:
    total_count = len(stories)
    illustrated_count = sum(1 for s in stories if s["has_image"])
    fields = sorted({s["field_cat"] for s in stories if s["field_cat"]})
    updated_str = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")

    field_options = "\n".join(
        f'          <option value="{html.escape(f)}">{html.escape(f)}</option>' for f in fields
    )

    cards_html_list = []
    for s in reversed(stories):
        if s["has_image"]:
            thumb_inner = (
                f'<img class="card-thumb" src="{html.escape(s["image_rel"])}" '
                f'alt="{html.escape(s["full_title"])}" loading="lazy" />'
            )
        else:
            thumb_inner = (
                f'<div class="card-placeholder">'
                f'<div style="font-size:1.05rem;color:#fbcfe8;margin-bottom:0.35rem;">{html.escape(s["main_title"])}</div>'
                f'<div style="font-size:0.8rem;">{html.escape(s["faculty"])}</div>'
                f'</div>'
            )

        search_blob = (
            f"{s['full_title']} {s['faculty']} {s['field_cat']} {s['theme']} "
            f"{s['modern_tech']} {s['summary']} {s['protagonist']} {s['mentor']}"
        ).lower()

        cards_html_list.append(
            f"""      <div class="story-card-wrap" data-no="{s['no']}" data-field="{html.escape(s['field_cat'])}" data-illustrated="{'yes' if s['has_image'] else 'no'}" data-search="{html.escape(search_blob)}">
        <article class="story-card">
          <a href="{html.escape(s['page_rel'])}" class="card-thumb-wrap">
            {thumb_inner}
            <span class="card-no-badge">#{s['no']:02d}</span>
          </a>
          <div class="card-body">
            <div class="card-faculty">🏛️ {html.escape(s['faculty'])}</div>
            <h2 class="card-title"><a href="{html.escape(s['page_rel'])}">{html.escape(s['full_title'])}</a></h2>
            <div class="card-tech">🔬 {html.escape(s['theme'])}</div>
            <p class="card-summary">{html.escape(s['summary'])}</p>
            <div class="card-footer">
              <span>約 {s['char_count']:,} 文字 {'🎨 挿絵あり' if s['has_image'] else ''}</span>
              <a class="read-link" href="{html.escape(s['page_rel'])}">物語を読む →</a>
            </div>
          </div>
        </article>
      </div>"""
        )

    cards_block = "\n".join(cards_html_list)

    return f"""<!DOCTYPE html>
<html lang="ja" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>『放課後サイエンス・キャンパス』理系女子ライトノベル図書館</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <header class="site-header">
    <div class="site-badge">RIKEJO SCIENCE LIGHT NOVEL ARCHIVE</div>
    <h1 class="site-title">『放課後サイエンス・キャンパス』理系女子ライトノベル図書館</h1>
    <p class="site-subtitle">
      最先端の科学・数学・情報学の感動と、大学進学・研究者・数学／情報／理科の先生への道を優しい物語で描くサイエンス・ライトノベルシリーズ。<br/>
      外部生成AI APIは一切使用せず、Mac mini M4 ローカルAI（Ollama Qwen3.5 &amp; shosetsu ＋ Draw Things FLUX.2）で執筆・挿絵生成し、GitHub Pagesで公開しています。
    </p>
    <div class="stats-bar">
      <div class="stat-pill"><strong>{total_count}</strong> 収録エピソード</div>
      <div class="stat-pill"><strong>{illustrated_count}</strong> 挿絵付き作品</div>
      <div class="stat-pill"><strong>{len(fields)}</strong> 科学・数理・情報分野</div>
      <div class="stat-pill">最終更新: {updated_str}</div>
    </div>
  </header>

  <main class="container">
    <div class="toolbar">
      <div class="filter-group">
        <input type="search" id="searchInput" class="search-input" placeholder="タイトル・学部・科学テーマ・登場人物で検索..." oninput="filterCards()" />
        <select id="fieldFilter" class="select-filter" onchange="filterCards()">
          <option value="">すべての分野（{len(fields)}分野）</option>
{field_options}
        </select>
        <select id="imageFilter" class="select-filter" onchange="filterCards()">
          <option value="">すべて表示</option>
          <option value="yes">🎨 挿絵ありのみ ({illustrated_count})</option>
        </select>
        <select id="sortOrder" class="select-filter" onchange="sortCards()">
          <option value="desc">新しい順（#大 → #01）</option>
          <option value="asc">作品番号順（#01 → #大）</option>
        </select>
      </div>
      <button class="btn-toggle" onclick="toggleTheme()" id="themeBtn">🌙 ダーク表示</button>
    </div>

    <div class="story-grid" id="storyGrid">
{cards_block}
    </div>
  </main>

  <footer class="site-footer">
    <p>『放課後サイエンス・キャンパス』理系女子ライトノベル図書館 — Generated locally on Mac mini M4 &amp; Published on GitHub Pages</p>
  </footer>

  <script>
    function filterCards() {{
      const q = (document.getElementById('searchInput').value || '').trim().toLowerCase();
      const field = document.getElementById('fieldFilter').value;
      const imgOnly = document.getElementById('imageFilter').value;
      const cards = document.querySelectorAll('.story-card-wrap');
      cards.forEach(card => {{
        const matchQ = !q || (card.getAttribute('data-search') || '').includes(q);
        const matchField = !field || card.getAttribute('data-field') === field;
        const matchImg = !imgOnly || card.getAttribute('data-illustrated') === imgOnly;
        card.style.display = (matchQ && matchField && matchImg) ? '' : 'none';
      }});
    }}
    function sortCards() {{
      const order = document.getElementById('sortOrder').value;
      const grid = document.getElementById('storyGrid');
      const cards = Array.from(grid.querySelectorAll('.story-card-wrap'));
      cards.sort((a, b) => {{
        const na = parseInt(a.getAttribute('data-no'), 10);
        const nb = parseInt(b.getAttribute('data-no'), 10);
        return order === 'asc' ? na - nb : nb - na;
      }});
      cards.forEach(c => grid.appendChild(c));
    }}
    function toggleTheme() {{
      const root = document.documentElement;
      const curr = root.getAttribute('data-theme') || 'light';
      const next = curr === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      localStorage.setItem('rikejo_theme', next);
      document.getElementById('themeBtn').textContent = next === 'dark' ? '☀️ ライト表示' : '🌙 ダーク表示';
    }}
    (function initPrefs() {{
      const savedTheme = localStorage.getItem('rikejo_theme');
      if (savedTheme) {{
        document.documentElement.setAttribute('data-theme', savedTheme);
        document.getElementById('themeBtn').textContent = savedTheme === 'dark' ? '☀️ ライト表示' : '🌙 ダーク表示';
      }}
    }})();
  </script>
</body>
</html>
"""


def _write_root_readme(stories: List[Dict[str, Any]], target_readme: Path = Path("README.md")):
    """
    Generates the root README.md containing links to the GitHub Pages web library
    and a complete index table with direct links to every novel (Web Reader + Markdown + Illustration).
    """
    pages_base = "https://k518-2026.github.io/rikejo-science-novel"
    illustrated_count = sum(1 for s in stories if s["has_image"])
    updated_str = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")

    lines = [
        "# 『放課後サイエンス・キャンパス』理系女子ライトノベル図書館（Rikejo Science Novel Library）",
        "",
        f"🌐 **Webサイト（GitHub Pages）で読む**: **[{pages_base}/]({pages_base}/)**",
        "",
        "最先端の科学・数学・情報学の面白さと、大学進学・研究者・高校の「数学・情報・理科」教員へのキャリアパスを、女子高校生と大学研究室メンターの対話を通じて優しく正確に描くサイエンス・ライトノベルシリーズです。各話に実在する査読付き論文（DOI検証済み）の解説コラムを収録しています。",
        "",
        "- **執筆・挿絵生成（完全ローカルAI）**: Mac mini M4 ローカル環境（Ollama 構成作家 `qwen3.5:9b` × 執筆作家 `shosetsu` ＆ Draw Things `FLUX.2 [klein] 4B`）",
        "- **外部生成AI API不使用**: 外部の有料・商用生成AI APIは一切利用せず、Mac mini M4 上で文章と挿絵を作成して GitHub Pages に蓄積・公開しています。",
        f"- **収録作品数**: 全 **{len(stories)}** 話（うち挿絵付き **{illustrated_count}** 話 / 最終更新: {updated_str}）",
        "",
        "---",
        "",
        "## 📚 収録サイエンス・ライトノベル一覧（リンク集）",
        "",
        "| No. | タイトル | Webページで読む | 原稿 (Markdown) | 挿絵 | 舞台となる大学・研究室 | 科学・数理・情報テーマ | 文字数 |",
        "|:---:|:---|:---:|:---:|:---:|:---|:---|---:|",
    ]

    for s in stories:
        md_rel = s["md_path"].as_posix()
        web_url = f"{pages_base}/{s['page_rel']}"
        img_cell = f"[🎨挿絵]({s['png_path'].as_posix()})" if s["has_image"] and s["png_path"] else "—"
        lines.append(
            f"| {s['no']:02d} | **[{s['full_title']}]({web_url})** | [🌐Web版]({web_url}) | [📄原稿]({md_rel}) | {img_cell} | {s['faculty']} | {s['theme']} | {s['char_count']:,}字 |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 🛠️ ローカル執筆＆GitHub Pages更新コマンド（Mac mini M4連携）",
        "",
        "```powershell",
        "# 未生成の小説と挿絵をMac mini M4 (Ollama + Draw Things) で自動生成し、GitHub Pages (docs/) へ公開",
        "python -m src.main --auto-replenish --push",
        "",
        "# 指定話数をバッチ生成してGitHub Pagesへ反映",
        "python -m src.main --stock-count 2 --push",
        "",
        "# 既存小説のうち未生成の挿絵 (.png) を生成してGitHub Pagesへ反映",
        "python -m src.main --generate-images --push",
        "",
        "# Webサイト (docs/) と README.md のリンク一覧を再ビルド",
        "python -m src.site_builder",
        "```",
        "",
    ])

    target_readme.write_text("\n".join(lines), encoding="utf-8")


def build_github_pages(history_mgr: Optional[HistoryManager] = None) -> Dict[str, Any]:
    """
    Generates the static GitHub Pages site in `docs/` and updates root `README.md`
    from all Markdown stories and PNG illustrations in `content/`.
    """
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    STORIES_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    (DOCS_DIR / ".nojekyll").write_text("", encoding="utf-8")

    stories = collect_all_stories(history_mgr)
    _write_stylesheet(DOCS_DIR / "style.css")

    for idx, story in enumerate(stories):
        if story["has_image"] and story["png_path"] is not None:
            dest_img = IMAGES_DIR / f"{story['work_id']}.png"
            shutil.copy2(story["png_path"], dest_img)

        prev_story = stories[idx - 1] if idx > 0 else None
        next_story = stories[idx + 1] if idx + 1 < len(stories) else None
        page_html = _build_story_page(story, prev_story=prev_story, next_story=next_story)
        (STORIES_DIR / f"{story['work_id']}.html").write_text(page_html, encoding="utf-8")

    index_html = _build_index_page(stories)
    (DOCS_DIR / "index.html").write_text(index_html, encoding="utf-8")

    manifest = [
        {
            "no": s["no"],
            "work_id": s["work_id"],
            "title": s["full_title"],
            "faculty": s["faculty"],
            "field": s["field_cat"],
            "theme": s["theme"],
            "has_image": s["has_image"],
            "url": s["page_rel"],
            "image": s["image_rel"],
            "char_count": s["char_count"],
        }
        for s in stories
    ]
    (DOCS_DIR / "stories.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    _write_root_readme(stories, Path("README.md"))

    illustrated = sum(1 for s in stories if s["has_image"])
    logger.info(
        f"GitHub Pages site built in docs/ and README.md updated: {len(stories)} episodes ({illustrated} with illustrations)"
    )
    return {
        "total_stories": len(stories),
        "illustrated_stories": illustrated,
        "docs_dir": str(DOCS_DIR.resolve()),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    build_github_pages()
