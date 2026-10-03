import os
import re
import json
import time
import logging
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable

from src.doi_verifier import (
    check_doi_validity,
    clean_doi_string,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_DIRECTOR_MODEL,
    DEFAULT_WRITER_MODEL,
)

logger = logging.getLogger(__name__)

LOREBOOK_FILE = Path("data/lorebook.json")

DIRECTOR_SYSTEM_PROMPT = """あなたは「構成作家（Director）」を務める科学ライトノベル専門のストーリーアーキテクト（Qwen 2.5 14B）です。
あなたの使命は、女子中高生（理系女子）が「大学の研究室に行ってみたい！」「最先端の科学ってこんなに美しくてワクワクするんだ！」と胸を躍らせるような、知的で温かい学園・キャンパス科学ライトノベルの【緻密なプロット構成】と【正確でやさしい科学解説】を作ることです。

【絶対ルール】
1. 科学的正確性の厳守：提供された実在の査読論文（Nature / Science / Cell / PNAS 等）の事実・メカニズムに100%忠実に構成し、架空の物質や誤った科学知識（ハルシネーション）を混ぜないこと。
2. キャラクターの一貫性：ロアブック（キャラクター設定）の口調・性格・関係性を正確に守ること。
3. 指示された出力フォーマットを厳格に守り、余計なメタ発言を入れないこと。"""

WRITER_SYSTEM_PROMPT = """あなたは「執筆作家（Writer）」を務める叙情的で表現力豊かな小説家（Gemma 2 9B）です。
構成作家が設計したプロットとキャラクター設定をもとに、読者の五感（光、色彩、音、香り、温度、手触り）に鮮やかに訴えかける、瑞々しく情緒豊かなライトノベルの本文（地の文と自然な会話劇）を執筆してください。

【執筆スタイルと絶対ルール】
1. 情景描写と心理描写：キャンパスの空気感、実験器具のガラスの煌めき、主人公の少女が科学の美しさに触れて目を輝かせる心の動きを、小説らしい美しい日本語で丁寧に描写してください。
2. 専門用語の噛み砕き：難しい数式や専門用語の羅列は避け、シャボン玉、ステンドグラス、折り紙、手紙などの日常の美しい比喩と会話劇のなかに科学の仕組みを自然に溶け込ませてください。
3. 見出しの禁止：小説本文の中に「第1シーン」「【起】」「シーン1」などのメタな見出しは書かず、純粋な小説の文章と `* * *`（シーン区切り）だけで構成してください。"""


def format_crossref_item(item: Dict[str, Any], tech_label: str = "") -> Optional[Dict[str, str]]:
    """
    Formats a Crossref work item into a clean bibliography dictionary and verifies its DOI.
    Returns None if the DOI is invalid or basic metadata is missing.
    """
    raw_doi = item.get("DOI", "")
    clean_doi = clean_doi_string(raw_doi)
    if not clean_doi or not check_doi_validity(clean_doi):
        return None

    titles = item.get("title", [])
    title = titles[0].strip() if titles else ""
    if not title:
        return None
    title = re.sub(r"<[^>]+>", "", title)

    authors_raw = item.get("author", [])
    author_names = []
    for a in authors_raw[:6]:
        family = a.get("family", "")
        given = a.get("given", "")
        if family and given:
            initials = ". ".join([p[0] for p in given.replace(".", " ").split() if p]) + "."
            author_names.append(f"{family}, {initials}")
        elif family:
            author_names.append(family)
        elif a.get("name"):
            author_names.append(a["name"])
    if len(authors_raw) > 6:
        author_names.append("et al.")
    authors_str = ", ".join(author_names) if author_names else "Research Collaboration"

    year = ""
    for date_field in ("published-print", "published-online", "issued", "created"):
        dp = item.get(date_field, {}).get("date-parts", [])
        if dp and dp[0] and dp[0][0]:
            year = str(dp[0][0])
            break
    if not year:
        year = "2020"

    containers = item.get("container-title", [])
    journal = containers[0].strip() if containers else item.get("publisher", "Scientific Journal")
    journal = re.sub(r"<[^>]+>", "", journal)

    volume = item.get("volume", "")
    issue = item.get("issue", "")
    page = item.get("page", "")

    vol_part = f", {volume}" if volume else ""
    if volume and issue:
        vol_part += f"({issue})"
    page_part = f", {page}" if page else ""

    doi_url = f"https://doi.org/{clean_doi}"
    citation_md = (
        f"{authors_str} ({year}). {title}. *{journal}*{vol_part}{page_part}.\n"
        f"   [{doi_url}]({doi_url})"
    )
    short_ref = f"{authors_str} ({year}). {title}. *{journal}*. [{doi_url}]({doi_url})"

    return {
        "tech_label": tech_label,
        "authors": authors_str,
        "year": year,
        "title": title,
        "journal": journal,
        "doi": clean_doi,
        "doi_url": doi_url,
        "citation_markdown": citation_md,
        "short_ref": short_ref,
    }


def query_crossref_verified_paper(
    query_str: str,
    tech_label: str = "",
    used_dois: Optional[set] = None
) -> Optional[Dict[str, str]]:
    """
    Searches Crossref REST API for a query string and returns the top authentic paper
    whose DOI passes live handle resolution (`check_doi_validity`).
    """
    if used_dois is None:
        used_dois = set()

    params = urllib.parse.urlencode({
        "query.bibliographic": query_str,
        "rows": 8,
        "select": "DOI,title,author,container-title,publisher,published-print,published-online,issued,volume,issue,page",
        "mailto": "kouy@outlook.com",
    })
    url = f"https://api.crossref.org/works?{params}"
    for attempt in range(3):
        try:
            time.sleep(0.8 * (attempt + 1))
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "RikejoSciNovelBot/1.0 (https://github.com/k518-2026/rikejo-science-novel; mailto:kouy@outlook.com)"}
            )
            with urllib.request.urlopen(req, timeout=12) as res:
                if res.getcode() == 200:
                    payload = json.loads(res.read().decode("utf-8", errors="ignore"))
                    items = payload.get("message", {}).get("items", [])
                    for item in items:
                        cand_doi = clean_doi_string(item.get("DOI", ""))
                        if not cand_doi or cand_doi in used_dois:
                            continue
                        titles = item.get("title", [])
                        t_str = titles[0] if titles else ""
                        if any(skip in t_str.lower() for skip in ("author correction", "erratum", "corrigendum")):
                            continue
                        formatted = format_crossref_item(item, tech_label=tech_label)
                        if formatted:
                            used_dois.add(cand_doi)
                            return formatted
                    break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(2.5 * (attempt + 1))
                continue
            logger.warning(f"Crossref search error for '{query_str}': {e}")
            break
        except Exception as e:
            logger.warning(f"Crossref search error for '{query_str}': {e}")
            break
    return None


class DualLLMStoryGenerator:
    """
    Collaborative Dual-LLM Novel Writing Engine:
    - Director LLM (`qwen2.5:14b`): Plot Architecture, Character Consistency, Scientific Commentary
    - Writer LLM (`gemma2:9b`): Expressive Sensory Prose, Emotional Dialogue, Light Novel Storytelling
    Connected to Mac mini Ollama server (`http://192.168.128.59:11434`).
    """

    def __init__(
        self,
        ollama_host: Optional[str] = None,
        director_model: Optional[str] = None,
        writer_model: Optional[str] = None,
        lorebook_path: Path = LOREBOOK_FILE,
    ):
        self.ollama_host = (ollama_host or os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)).rstrip("/")
        self.director_model = director_model or os.getenv("OLLAMA_DIRECTOR_MODEL", DEFAULT_DIRECTOR_MODEL)
        self.writer_model = writer_model or os.getenv("OLLAMA_WRITER_MODEL", DEFAULT_WRITER_MODEL)
        self.lorebook_path = lorebook_path
        self.lorebook = self._load_lorebook()

    def _load_lorebook(self) -> Dict[str, Any]:
        if self.lorebook_path.exists():
            try:
                return json.loads(self.lorebook_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Failed to load lorebook: {e}")
        return {"series_title": "放課後サイエンス・キャンパス", "world_setting": "", "writing_rules": [], "characters": []}

    def save_lorebook(self, lorebook_data: Dict[str, Any]):
        self.lorebook = lorebook_data
        self.lorebook_path.parent.mkdir(parents=True, exist_ok=True)
        self.lorebook_path.write_text(
            json.dumps(lorebook_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def check_connection(self) -> Dict[str, Any]:
        """Checks connection to Mac mini Ollama server and returns available models."""
        try:
            req = urllib.request.Request(f"{self.ollama_host}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as res:
                if res.getcode() == 200:
                    data = json.loads(res.read().decode("utf-8", errors="ignore"))
                    models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                    return {
                        "online": True,
                        "host": self.ollama_host,
                        "models": models,
                        "director_ready": self.director_model in models,
                        "writer_ready": self.writer_model in models,
                    }
        except Exception as e:
            return {
                "online": False,
                "host": self.ollama_host,
                "models": [],
                "error": str(e),
                "director_ready": False,
                "writer_ready": False,
            }
        return {"online": False, "host": self.ollama_host, "models": []}

    def call_ollama_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        num_predict: int = 3000,
        num_ctx: int = 8192,
        timeout: int = 900,
    ) -> str:
        """Calls Ollama /api/chat on the Mac mini with the specified model."""
        url = f"{self.ollama_host}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
                "num_ctx": num_ctx,
                "repeat_penalty": 1.12,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as res:
            body = json.loads(res.read().decode("utf-8", errors="ignore"))
            return body.get("message", {}).get("content", "").strip()

    def _clean_llm_output(self, text: str) -> str:
        """Removes <think> blocks, markdown code fences, unwanted meta scene headers, and repetition loops."""
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        if text.startswith("```markdown"):
            text = text[len("```markdown"):].strip()
        if text.startswith("```"):
            text = text[3:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
        text = re.sub(r"^[ \t]*#+[ \t]*(\*\s*\*\s*\*)[ \t]*$", r"\1", text, flags=re.MULTILINE)
        text = re.sub(r"^[ \t]*#+[ \t]*\*+[ \t]*$", "* * *", text, flags=re.MULTILINE)
        text = re.sub(
            r"^[ \t]*(?:#+[ \t]*)?[【\[（(]?(?:第\s*[0-9一二三四五六七八九十]+\s*(?:シーン|幕|章|部|節)|シーン\s*[0-9一二三四五六七八九十]+)[】\]）)]?(?:[：:\s—―-].*)?$",
            "",
            text,
            flags=re.MULTILINE,
        )
        seen_long_lines = set()
        deduped_lines = []
        for line in text.splitlines():
            s = line.strip()
            if len(s) >= 35 and s not in ("* * *", "---"):
                if s in seen_long_lines:
                    continue
                seen_long_lines.add(s)
            deduped_lines.append(line)
        return "\n".join(deduped_lines).strip()

    def _build_character_context(self, work: Dict[str, Any]) -> str:
        """Extracts matching character profiles from lorebook or falls back to work metadata."""
        chars = self.lorebook.get("characters", [])
        protag_name = work.get("protagonist", "").split("（")[0].strip()
        mentor_name = work.get("mentor", "").split("（")[0].strip()

        matched = []
        for c in chars:
            cname = c.get("name", "")
            if (protag_name and protag_name in cname) or (mentor_name and mentor_name in cname):
                matched.append(
                    f"- **{c['name']}**（{c.get('role', '')} / {c.get('affiliation', '')}）\n"
                    f"  ・性格: {c.get('personality', '')}\n"
                    f"  ・外見: {c.get('appearance', '')}\n"
                    f"  ・話し方・口調サンプル: {c.get('speech_style', '')}"
                )

        if not matched:
            matched.append(
                f"- **主人公（女子高校生）**: {work.get('protagonist', '天野 陽葵（高校2年生）')}\n"
                f"  ・好奇心旺盛で素直な高校生。理系進学や大学の研究室に憧れと少しの不安を抱いている。\n"
                f"- **メンター（大学の先輩・女性研究者）**: {work.get('mentor', '白石 凛（大学院生）')}（{work.get('faculty', '理学部')}）\n"
                f"  ・研究を心から楽しむ知的で優しいお姉さん。専門知識を日常の美しい比喩でわかりやすく教えてくれる。"
            )
        return "\n".join(matched)

    def fetch_verified_references_for_work(self, work: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Pre-fetches 3 100% real, DOI-verified scientific papers from Crossref for the episode.
        """
        queries = work.get("crossref_queries", [])
        verified_papers: List[Dict[str, str]] = []
        used_dois: set = set()

        for q_item in queries:
            tech_label = q_item.get("label", work.get("theme", "先端科学"))
            query_str = q_item.get("query", "")
            if not query_str:
                continue
            logger.info(f"Pre-fetching verified Crossref paper for [{tech_label}]...")
            paper = query_crossref_verified_paper(query_str, tech_label=tech_label, used_dois=used_dois)
            if paper:
                logger.info(
                    f"  -> Verified real paper: {paper['authors']} ({paper['year']}) "
                    f"'{paper['title'][:55]}...' [{paper['doi_url']}]"
                )
                verified_papers.append(paper)
            else:
                short_q = " ".join(query_str.split()[:4])
                paper = query_crossref_verified_paper(short_q, tech_label=tech_label, used_dois=used_dois)
                if paper:
                    verified_papers.append(paper)

        if not verified_papers:
            # Fallback universal query
            fallback_p = query_crossref_verified_paper(
                "Jumper Hassabis Highly accurate protein structure prediction with AlphaFold Nature 2021",
                tech_label=work.get("theme", "先端科学"),
                used_dois=used_dois,
            )
            if fallback_p:
                verified_papers.append(fallback_p)

        return verified_papers

    def generate_plot_with_director(
        self,
        work: Dict[str, Any],
        verified_papers: List[Dict[str, str]],
        custom_instruction: str = "",
    ) -> str:
        """
        Step 1: Uses `qwen2.5:14b` (Director) to create a detailed 4-scene plot blueprint
        ensuring scientific accuracy, character consistency, and narrative arc.
        """
        char_context = self._build_character_context(work)
        tech_lines = []
        for idx, p in enumerate(verified_papers, start=1):
            tech_lines.append(
                f"{idx}. 【科学要素{idx}: {p['tech_label']}】\n"
                f"   - 根拠論文: {p['authors']} ({p['year']}) \"{p['title']}\" (*{p['journal']}*)"
            )
        tech_block = "\n".join(tech_lines)

        world_setting = self.lorebook.get("world_setting", "")
        custom_block = f"\n【追加オーダー・特記事項】\n{custom_instruction}\n" if custom_instruction else ""

        prompt = f"""あなたは構成作家（Qwen 2.5 14B）です。以下のエピソード設定・キャラクター設定・実在の科学論文にもとづき、執筆作家（Gemma 2 9B）が情緒豊かなライトノベルを執筆するための**【緻密な4シーン構成プロット設計図】**を作成してください。

【シリーズ世界観】
{world_setting}

【今回のエピソード情報】
- エピソードタイトル案: {work.get('title')}
- 舞台となる大学・学部・研究室: {work.get('faculty')}
- 科学テーマ: {work.get('theme')}
- キーワード: {work.get('modern_tech')}
- あらすじ概要: {work.get('summary')}

【登場キャラクター設定（ロアブック）】
{char_context}

【作中に組み込む実在の査読論文・科学ファクト（3点）】
{tech_block}
{custom_block}
【出力してほしい構成案のフォーマット】
1. **TITLE**: 『{work.get('title')}』をベースにした、理系女子が思わず読みたくなる魅力的で詩的な本編タイトル（副題つき）
2. **第1シーン（日常の疑問とキャンパスへの訪問）**:
   - 季節・時間帯・キャンパスの風景（光や音、匂いなどの五感要素）
   - 主人公の抱える小さな悩みや素朴な疑問、研究室・実験室へ足を踏み入れるきっかけ
3. **第2シーン（先輩・先生との出会いと最初の実験デモ）**:
   - メンター（先輩/研究者）の登場シーンと印象的な第一声
   - 科学要素1・2を目で見て体験する実験や観察の描写、日常の身近な比喩（なぜその現象が起きるのかの直感的な説明）
4. **第3シーン（科学の核心への驚きとセンス・オブ・ワンダー）**:
   - 主人公の「どうして？」という質問から、科学要素3（分子・遺伝子・物理の仕組み）の核心に触れる対話
   - 「科学って暗記じゃなくて、世界の秘密を解き明かす魔法なんだ！」と主人公の認識が鮮やかに変わる瞬間
5. **第4シーン（未来への一歩と爽やかな余韻）**:
   - 実験室を出た後の夕暮れ（または星空・帰り道）の情景
   - 「私、この大学に来てこの研究をしてみたい！」という主人公の前向きな決意と、先輩からの温かいエール
"""
        logger.info(f"[Director: {self.director_model}] Creating structured 4-scene plot for '{work.get('title')}'...")
        raw_plot = self.call_ollama_chat(
            model=self.director_model,
            messages=[
                {"role": "system", "content": DIRECTOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            num_predict=2200,
            num_ctx=8192,
        )
        return self._clean_llm_output(raw_plot)

    def generate_prose_with_writer(
        self,
        work: Dict[str, Any],
        plot_blueprint: str,
        verified_papers: List[Dict[str, str]],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[str, str]:
        """
        Step 2: Uses `gemma2:9b` (Writer) to write the actual sensory-rich light novel prose
        in two parts (Part 1: Scenes 1-2, Part 2: Scenes 3-4) following the Director's plot.
        Returns (story_body, episode_title).
        """
        char_context = self._build_character_context(work)

        # Extract title if present in plot_blueprint
        episode_title = work.get("title", "放課後サイエンス・キャンパス")
        for line in plot_blueprint.splitlines()[:8]:
            if "TITLE" in line or "タイトル" in line:
                m = re.search(r"[:：]\s*(.+)$", line)
                if m:
                    cand = m.group(1).strip(" 『』\"'*")
                    if len(cand) >= 4:
                        episode_title = cand
                        break

        part1_prompt = f"""あなたは表現力豊かな執筆作家（Gemma 2 9B）です。
構成作家（Qwen 2.5 14B）が作成した以下の【プロット設計図】と【キャラクター設定】をもとに、理系女子が大学に行きたくなる爽やかで情緒豊かな科学ライトノベルの**【前半パート（第1シーン・第2シーン：目標1,800〜2,200文字）】**を執筆してください。

※重要：物語全体を前半・後半の2回に分けて執筆します。今回の出力では**絶対に物語を完結させず（『（了）』と書かず）**、第2シーンの実験や観察で不思議な現象が目の前に現れ、主人公が「えっ、どうしてこんなことが起きるんですか！？」と目を輝かせた場面で後半へバトンを渡してください。

【エピソード基本設定】
- タイトル: {episode_title}
- 舞台: {work.get('faculty')}
- 科学テーマ: {work.get('theme')}

【キャラクター設定】
{char_context}

【構成作家（Qwen 2.5 14B）によるプロット設計図】
{plot_blueprint}

【前半パート（第1シーン・第2シーン）の執筆ルール】
1. 1行目には `TITLE: {episode_title}` の形式でタイトルのみを出力してください。
2. 続けて、小説本文（第1シーン：キャンパスの風景と主人公の訪問）を書き始めてください。「第1シーン」「【起】」などの見出しは絶対に入れず、美しい地の文とセリフだけで紡いでください。
3. 第1シーンと第2シーンの間には `* * *` を1行入れてください。
4. 五感（光の粒、ガラス器具の透明な輝き、白衣の揺れる音、紅茶や薬品のほのかな香り）を豊かに描写し、登場人物の掛け合いを生き生きと書いてください。"""

        if progress_callback:
            progress_callback(f"執筆作家 ({self.writer_model}) が前半パート（第1・第2シーン）を執筆中...")
        logger.info(f"[Writer: {self.writer_model}] Writing Novel Prose Part 1 (Scenes 1 & 2)...")
        raw_part1 = self.call_ollama_chat(
            model=self.writer_model,
            messages=[
                {"role": "system", "content": WRITER_SYSTEM_PROMPT},
                {"role": "user", "content": part1_prompt},
            ],
            temperature=0.78,
            num_predict=3000,
            num_ctx=8192,
        )
        cleaned_part1 = self._clean_llm_output(raw_part1)

        p1_lines = []
        for idx, line in enumerate(cleaned_part1.splitlines()):
            stripped = line.strip()
            if idx < 4 and (stripped.startswith("TITLE:") or stripped.startswith("# ")):
                cand = re.sub(r"^(?:TITLE:|#+)\s*", "", stripped).strip(" 『』\"'*")
                if cand:
                    episode_title = cand
                continue
            if stripped in ("（了）", "(了)", "（完）"):
                continue
            p1_lines.append(line)
        part1_body = "\n".join(p1_lines).strip()

        part2_prompt = f"""素晴らしい前半パートです！続けて、構成作家のプロット設計図に沿って、この小説『{episode_title}』の**【後半パート（第3シーン・第4シーン：目標1,800〜2,200文字）】**を執筆し、物語を感動的に完結させてください。

【後半パート（第3シーン・第4シーン）の執筆ルール】
1. タイトルは書かず、前半パートの直後に続く小説本文（第3シーン：科学の仕組みのやさしい解き明かしと主人公の感動）から自然に書き始めてください。
2. 前半の登場人物の口調・一人称・名前を100%維持してください。
3. 難しい科学の仕組みを、先輩（または先生）が日常の美しい比喩でやさしく解き明かし、主人公が「科学って、世界の隠れたお手紙を読むことなんだ……！」と深く感動する瞬間（センス・オブ・ワンダー）を鮮やかに描いてください。
4. 第3シーンと第4シーンの間には `* * *` を1行入れてください（「第3シーン」等の見出しは禁止）。
5. 第4シーンでは、主人公が「私、この大学に来て、ここで研究がしたい！」と未来への一歩を踏み出す爽やかで温かい余韻を描き、最後は必ず `（了）` で締めくくってください。"""

        if progress_callback:
            progress_callback(f"執筆作家 ({self.writer_model}) が後半パート（第3・第4シーン）を執筆中...")
        logger.info(f"[Writer: {self.writer_model}] Writing Novel Prose Part 2 (Scenes 3 & 4)...")
        raw_part2 = self.call_ollama_chat(
            model=self.writer_model,
            messages=[
                {"role": "system", "content": WRITER_SYSTEM_PROMPT},
                {"role": "user", "content": part1_prompt},
                {"role": "assistant", "content": f"TITLE: {episode_title}\n\n{part1_body}"},
                {"role": "user", "content": part2_prompt},
            ],
            temperature=0.78,
            num_predict=3000,
            num_ctx=8192,
        )
        cleaned_part2 = self._clean_llm_output(raw_part2)
        p2_lines = []
        for line in cleaned_part2.splitlines():
            stripped = line.strip()
            if "【高校生のための" in stripped or "【作中科学の" in stripped or "【引用・参考文献" in stripped:
                break
            if stripped.startswith("TITLE:"):
                continue
            p2_lines.append(line)
        part2_body = "\n".join(p2_lines).strip()

        story_body = f"{part1_body}\n\n* * *\n\n{part2_body}".strip()
        story_body = re.sub(r"(\*\s*\*\s*\*\s*\n+){2,}", "* * *\n\n", story_body)
        story_body = re.sub(r"https?://\S+", "", story_body)
        if not story_body.endswith("（了）"):
            story_body = story_body.rstrip() + "\n\n（了）"

        return story_body, episode_title

    def generate_science_guide_with_director(
        self,
        work: Dict[str, Any],
        episode_title: str,
        verified_papers: List[Dict[str, str]],
    ) -> str:
        """
        Step 3: Uses `qwen2.5:14b` (Director) to write an accurate, inspiring
        "Science Column & University Lab Guide for High School Girls" grounded in the 3 papers.
        """
        tech_lines = []
        for idx, p in enumerate(verified_papers, start=1):
            tech_lines.append(
                f"{idx}. **{p['tech_label']}**\n"
                f"   - 実在根拠論文: {p['authors']} ({p['year']}) \"{p['title']}\" (*{p['journal']}*)"
            )
        tech_block = "\n".join(tech_lines)

        prompt = f"""先ほど完成した科学ライトノベル『{episode_title}』（舞台：{work.get('faculty')}／テーマ：{work.get('theme')}）の読者（理系に興味がある女子中高生）に向けて、構成作家（Qwen 2.5 14B）として**【理系女子のためのやさしい最新科学コラム＆大学研究室ガイド】**を執筆してください。

【解説する3つの最新科学トピックと実在根拠論文】
{tech_block}

【出力フォーマット（以下の形式のみを出力し、URLや参考文献リストは書かないでください）】
物語に登場した『{work.get('theme')}』は、魔法ではなくすべて実際の大学や研究機関で進められている本物の最先端科学です。高校の生物・化学・物理とどう繋がっているのか、一緒に見てみましょう！

1. **{verified_papers[0]['tech_label']}**
   - **どんな科学？（やさしい仕組み）**: （専門知識がなくてもワクワクしながら理解できるように、仕組みを平易かつ正確に解説）
   - **高校の科目とのつながり＆未来への応用**: （高校のどの分野の発展か、将来どんな社会や未来をつくる技術かを解説）

2. **{verified_papers[min(1, len(verified_papers)-1)]['tech_label']}**
   - **どんな科学？（やさしい仕組み）**: （平易でわかりやすい解説）
   - **高校の科目とのつながり＆未来への応用**: （将来への応用と魅力）

3. **{verified_papers[min(2, len(verified_papers)-1)]['tech_label']}**
   - **どんな科学？（やさしい仕組み）**: （平易でわかりやすい解説）
   - **高校の科目とのつながり＆未来への応用**: （将来への応用と魅力）

- **🎓 この研究に出会える大学の学部・学科ガイド（{work.get('faculty')}）**:
  （この研究を大学で学びたい高校生が、どんな学部・学科を目指せばよいか、大学の研究室ではどんな楽しいキャンパスライフや実験が待っているかを温かく具体的に紹介）"""

        logger.info(f"[Director: {self.director_model}] Writing Science Column & University Lab Guide...")
        raw_guide = self.call_ollama_chat(
            model=self.director_model,
            messages=[
                {"role": "system", "content": DIRECTOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            num_predict=2200,
            num_ctx=8192,
        )
        guide_body = self._clean_llm_output(raw_guide)
        guide_body = re.sub(r"^#+.*最新科学コラム.*?\n", "", guide_body).strip()
        guide_body = re.sub(r"###\s*【引用・参考文献.*", "", guide_body, flags=re.DOTALL).strip()
        guide_body = re.sub(r"https?://\S+", "", guide_body)
        return guide_body

    def generate_complete_episode(
        self,
        work: Dict[str, Any],
        custom_plot_override: Optional[str] = None,
        custom_instruction: str = "",
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[str, str, List[str], str]:
        """
        Runs the full Collaborative Dual-LLM Pipeline:
        1) Pre-fetches 3 DOI-verified scientific papers via Crossref REST API.
        2) Director (`qwen2.5:14b`) creates the 4-scene plot blueprint (or uses custom_plot_override).
        3) Writer (`gemma2:9b`) writes the emotional, sensory-rich light novel prose.
        4) Director (`qwen2.5:14b`) writes the Science Column & University Lab Guide.
        5) Assembles the publication-ready Markdown with YAML frontmatter and verified DOI links.
        Returns: (full_markdown, episode_title, short_refs, plot_blueprint)
        """
        if progress_callback:
            progress_callback("Crossref API から実在する査読付き科学論文（DOI）を検索・検証中...")
        verified_papers = self.fetch_verified_references_for_work(work)

        if custom_plot_override and custom_plot_override.strip():
            plot_blueprint = custom_plot_override.strip()
            logger.info("Using user-edited custom plot blueprint.")
        else:
            if progress_callback:
                progress_callback(f"構成作家 ({self.director_model}) がプロットと章構成を作成中...")
            plot_blueprint = self.generate_plot_with_director(
                work=work,
                verified_papers=verified_papers,
                custom_instruction=custom_instruction,
            )

        story_body, episode_title = self.generate_prose_with_writer(
            work=work,
            plot_blueprint=plot_blueprint,
            verified_papers=verified_papers,
            progress_callback=progress_callback,
        )

        if progress_callback:
            progress_callback(f"構成作家 ({self.director_model}) が最新科学コラム＆大学研究室ガイドを執筆中...")
        guide_body = self.generate_science_guide_with_director(
            work=work,
            episode_title=episode_title,
            verified_papers=verified_papers,
        )

        ref_lines = []
        short_refs = []
        for idx, p in enumerate(verified_papers, start=1):
            ref_lines.append(f"{idx}. {p['citation_markdown']}")
            short_refs.append(p["short_ref"])
        references_block = "\n".join(ref_lines)

        full_markdown = self.assemble_markdown(
            work=work,
            episode_title=episode_title,
            story_body=story_body,
            guide_body=guide_body,
            references_block=references_block,
        )

        logger.info(
            f"[Dual-LLM Complete] '{episode_title}' | Director: {self.director_model} × Writer: {self.writer_model} | "
            f"Total chars: {len(full_markdown)} (Novel body: {len(story_body)} chars)"
        )
        return full_markdown, episode_title, short_refs, plot_blueprint

    def assemble_markdown(
        self,
        work: Dict[str, Any],
        episode_title: str,
        story_body: str,
        guide_body: str,
        references_block: str,
    ) -> str:
        clean_title = re.sub(r"^【第\s*\d+\s*話】\s*", "", episode_title).strip()
        safe_title = clean_title.replace('"', '\\"')
        faculty = work.get("faculty", "理学部")
        theme = work.get("theme", "最先端科学")
        protag = work.get("protagonist", "女子高校生")
        mentor = work.get("mentor", "大学院生")

        return f"""---
title: "{safe_title}"
categories: ["理系女子サイエンス小説", "大学研究室ガイド"]
tags: ["理系女子", "ライトノベル", "最新科学", "{faculty.split('・')[0]}", "Qwen2.5×Gemma2"]
---

> **📖 『放課後サイエンス・キャンパス』**
> - **舞台となる研究室**: {faculty}
> - **今回の科学テーマ**: {theme}
> - **登場人物**: {protag} ／ {mentor}

{story_body}

---

### 🔬 【理系女子のためのやさしい最新科学コラム＆大学研究室ガイド】

{guide_body}

---

### 📚 【引用・参考文献（Verified Scientific References）】

{references_block}
"""
