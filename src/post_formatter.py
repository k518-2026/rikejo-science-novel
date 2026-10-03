import re
import html
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


@dataclass
class FormattedPost:
    title: str
    categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    status: str = "publish"
    content_raw: str = ""
    content_html: str = ""
    content_plain: str = ""
    content_html_clean: str = ""
    content_plain_clean: str = ""


def _fallback_yaml_parser(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            if val.startswith("[") and val.endswith("]"):
                items = [item.strip().strip("'\"") for item in val[1:-1].split(",") if item.strip()]
                data[key] = items
            else:
                data[key] = val
    return data


def _format_inline_markdown(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.*?)`", r"<code style='background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:0.9em;'>\1</code>", text)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', text)
    return text


def _fallback_markdown_to_html(md_text: str) -> str:
    """
    Lightweight Markdown to HTML converter safe for WordPress Post-via-Email
    (never outputs <hr> which triggers email signature truncation).
    """
    lines = md_text.splitlines()
    html_lines = []
    in_code_block = False
    in_list = False
    in_blockquote = False
    bq_lines: List[str] = []
    in_table = False
    table_rows: List[List[str]] = []

    def flush_blockquote():
        nonlocal in_blockquote, bq_lines
        if not bq_lines:
            in_blockquote = False
            return
        inner = "<br>".join(_format_inline_markdown(l) for l in bq_lines)
        html_lines.append(
            f'<div style="background: linear-gradient(135deg, #f0f9ff 0%, #fdf2f8 100%); '
            f'border-left: 4px solid #ec4899; padding: 14px 18px; margin: 1.5em 0; '
            f'border-radius: 8px; color: #334155; font-size: 15px; line-height: 1.7;">{inner}</div>'
        )
        in_blockquote = False
        bq_lines = []

    def flush_table():
        nonlocal in_table, table_rows
        if not table_rows:
            in_table = False
            return
        tbl_html = [
            '<table style="width: 100%; border-collapse: collapse; margin: 1.5em 0; font-size: 14px; line-height: 1.7; background-color: #ffffff; border: 1px solid #e2e8f0;">'
        ]
        start_idx = 0
        if len(table_rows) >= 2 and all(c.strip().replace(":", "").replace("-", "") == "" for c in table_rows[1]):
            tbl_html.append('  <thead>\n    <tr style="background-color: #fce7f3;">')
            for cell in table_rows[0]:
                cell_fmt = _format_inline_markdown(cell.strip())
                tbl_html.append(f'      <th style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: bold; text-align: left; color: #831843;">{cell_fmt}</th>')
            tbl_html.append('    </tr>\n  </thead>')
            start_idx = 2

        tbl_html.append('  <tbody>')
        for r_idx, row in enumerate(table_rows[start_idx:]):
            bg = "#ffffff" if r_idx % 2 == 0 else "#fdf2f8"
            tbl_html.append(f'    <tr style="background-color: {bg};">')
            for cell in row:
                cell_fmt = _format_inline_markdown(cell.strip())
                tbl_html.append(f'      <td style="padding: 10px 14px; border: 1px solid #e2e8f0; color: #334155;">{cell_fmt}</td>')
            tbl_html.append('    </tr>')
        tbl_html.append('  </tbody>\n</table>')
        html_lines.append("\n".join(tbl_html))
        in_table = False
        table_rows = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_blockquote:
                flush_blockquote()
            if in_table:
                flush_table()
            if in_code_block:
                html_lines.append("</code></pre>")
                in_code_block = False
            else:
                html_lines.append("<pre><code>")
                in_code_block = True
            continue

        if in_code_block:
            html_lines.append(html.escape(line))
            continue

        if stripped.startswith(">"):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            if in_table:
                flush_table()
            in_blockquote = True
            bq_lines.append(stripped.lstrip(">").strip())
            continue
        elif in_blockquote:
            flush_blockquote()

        if stripped.startswith("|") and stripped.endswith("|") and len(stripped) > 2:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            in_table = True
            cells = [c for c in stripped.split("|")[1:-1]]
            table_rows.append(cells)
            continue
        elif in_table:
            flush_table()

        if stripped in ("---", "***", "___", "* * *", "- - -", "◆ ◆ ◆", "✽ ✽ ✽"):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append('<div style="text-align: center; margin: 2.2em 0; letter-spacing: 0.6em; color: #db2777; font-size: 14px;">✦ ✦ ✦</div>')
            continue

        if stripped.startswith("# "):
            html_lines.append(f"<h1 style='margin-top: 1.5em; margin-bottom: 0.8em; color: #1e293b;'>{html.escape(stripped[2:])}</h1>")
            continue
        if stripped.startswith("## "):
            html_lines.append(f"<h2 style='margin-top: 1.5em; margin-bottom: 0.8em; color: #1e293b;'>{html.escape(stripped[3:])}</h2>")
            continue
        if stripped.startswith("### "):
            html_lines.append(f"<h3 style='margin-top: 1.8em; margin-bottom: 0.8em; padding-bottom: 6px; border-bottom: 2px solid #fbcfe8; color: #9d174d;'>{html.escape(stripped[4:])}</h3>")
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            item = _format_inline_markdown(stripped[2:])
            if not in_list:
                html_lines.append('<ul style="margin: 1em 0; padding-left: 1.5em;">')
                in_list = True
            html_lines.append(f"<li style='margin-bottom: 0.5em;'>{item}</li>")
            continue
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False

        if not stripped:
            continue

        p_text = _format_inline_markdown(stripped)
        html_lines.append(f"<p style='margin-bottom: 1.4em; line-height: 1.95;'>{p_text}</p>")

    if in_blockquote:
        flush_blockquote()
    if in_table:
        flush_table()
    if in_list:
        html_lines.append("</ul>")
    if in_code_block:
        html_lines.append("</code></pre>")

    return "\n".join(html_lines)


def build_next_work_preview(next_work: Dict[str, Any]) -> str:
    ep_num = next_work.get("episode_num", "")
    title = next_work.get("title", "")
    faculty = next_work.get("faculty", "")
    theme = next_work.get("theme", "")
    summary = next_work.get("summary", "")

    return f"""

---

### 🌸 【次回エピソード予告】

| 項目 | 内容 |
|:---|:---|
| **次回タイトル** | 第{ep_num}話『{title}』 |
| **訪れる大学・研究室** | {faculty} |
| **学ぶ最新科学テーマ** | {theme} |
| **あらすじ** | {summary} |
"""


def parse_markdown_with_frontmatter(file_path: str) -> Tuple[Dict[str, Any], str]:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    frontmatter: Dict[str, Any] = {}
    body = text

    match_dash = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if match_dash:
        yaml_text = match_dash.group(1)
        body = match_dash.group(2)
        if HAS_YAML:
            try:
                frontmatter = yaml.safe_load(yaml_text) or {}
            except Exception:
                frontmatter = _fallback_yaml_parser(yaml_text)
        else:
            frontmatter = _fallback_yaml_parser(yaml_text)

    if "title" not in frontmatter:
        title_m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if title_m:
            frontmatter["title"] = title_m.group(1).strip()

    return frontmatter, body


def format_post_content(
    file_path: str,
    status_override: Optional[str] = None,
    include_jetpack_shortcodes: bool = True,
    next_work: Optional[Dict[str, Any]] = None,
) -> FormattedPost:
    meta, body = parse_markdown_with_frontmatter(file_path)

    title = meta.get("title", "放課後サイエンス・キャンパス")
    categories = meta.get("categories", ["理系女子サイエンス小説"])
    if isinstance(categories, str):
        categories = [c.strip() for c in categories.split(",")]

    tags = meta.get("tags", ["理系女子", "ライトノベル", "最新科学"])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]

    status = status_override or meta.get("status", "publish")

    cleaned_body = re.sub(r"\[(category|tags|status|title|excerpt)[^\]]*\]", "", body).strip()

    if next_work and "次回エピソード予告" not in cleaned_body:
        cleaned_body += build_next_work_preview(next_work)

    # Replace --- lines with safe scene dividers to avoid WordPress email truncation
    cleaned_body = re.sub(r"^[ \t]*[-*_]{3,}[ \t]*$", "✦ ✦ ✦", cleaned_body, flags=re.MULTILINE)

    html_body = _fallback_markdown_to_html(cleaned_body)

    # Ensure all links open in new tab and format DOI anchor text cleanly
    html_body = re.sub(
        r'(<a\b[^>]*href=["\']https?://(?:dx\.)?doi\.org/(10\.[^"\']+)["\'][^>]*>)\s*https?://(?:dx\.)?doi\.org/[^<]+\s*(</a>)',
        r"\1DOI: \2\3",
        html_body,
        flags=re.IGNORECASE,
    )

    styled_html = f"""<div class="rikejo-novel-container" style="font-family: 'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', sans-serif; line-height: 1.95; font-size: 16px; color: #1e293b; max-width: 780px; margin: 0 auto;">
{html_body}
</div>"""

    sc_lines = []
    if status:
        sc_lines.append(f"[status {status}]")
    if categories:
        sc_lines.append(f"[category {', '.join(categories)}]")
    if tags:
        sc_lines.append(f"[tags {', '.join(tags)}]")

    final_plain = cleaned_body
    if include_jetpack_shortcodes and sc_lines:
        shortcode_block = "\n".join(sc_lines)
        final_plain = f"{final_plain}\n\n{shortcode_block}"
        shortcodes_html_list = [f"<p style='color: #94a3b8; font-size: 12px; margin: 0.3em 0;'>{sc}</p>" for sc in sc_lines]
        final_html = f"{styled_html}\n<div class='wp-meta-shortcodes' style='margin-top: 2em;'>\n" + "\n".join(shortcodes_html_list) + "\n</div>"
    else:
        final_html = styled_html

    return FormattedPost(
        title=title,
        categories=categories,
        tags=tags,
        status=status,
        content_raw=cleaned_body,
        content_html=final_html,
        content_plain=final_plain,
        content_html_clean=styled_html,
        content_plain_clean=cleaned_body,
    )
