import os
import re
import json
import time
import base64
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
    SECONDARY_LLM_HOST,
    FALLBACK_OLLAMA_HOSTS,
    DEFAULT_DIRECTOR_MODEL,
    DEFAULT_WRITER_MODEL,
    DEFAULT_LM_STUDIO_MODEL,
    DEFAULT_DRAW_THINGS_HOST,
)

logger = logging.getLogger(__name__)

LOREBOOK_FILE = Path("data/lorebook.json")

DIRECTOR_SYSTEM_PROMPT = """あなたは「構成作家（Director）」を務める科学・数理・情報ライトノベル専門のストーリーアーキテクト（Qwen 3.5 9B）です。
あなたの使命は、女子中高生（理系女子）が「大学の研究室に行ってみたい！」「数学や情報学、理科の世界ってこんなに美しくてワクワクするんだ！」「将来は研究者やエンジニアだけでなく、この面白さを伝える『数学・情報・理科の先生（教員）』になる道も素敵だな！」と胸を躍らせるような、知的で温かい学園・キャンパス科学ライトノベルの【緻密なプロット構成】と【正確でやさしい科学・進路解説】を作ることです。

【絶対ルール】
1. 科学的・数理的正確性の厳守：提供された実在の査読論文（Nature / Science / Cell / PNAS 等）の事実・メカニズムに100%忠実に構成し、架空の物質や誤った科学知識（ハルシネーション）を混ぜないこと。
2. キャラクターの一貫性：ロアブック（キャラクター設定）の口調・性格・関係性を正確に守ること。
3. 多様な理系キャリアの肯定：大学での研究や企業エンジニアだけでなく、「教職課程を履修して数学・情報・理科の教員（先生）になり、次世代の子どもたちに科学の感動を届ける道」も誇り高い理系のキャリアとして温かく描くこと。
4. 指示された出力フォーマットを厳格に守り、余計なメタ発言を入れないこと。"""

WRITER_SYSTEM_PROMPT = """あなたは「執筆作家（Writer）」を務める叙情的で表現力豊かな小説家（shosetsu）です。
構成作家が設計したプロットとキャラクター設定をもとに、読者の五感（光、色彩、音、香り、温度、手触り）に鮮やかに訴えかける、瑞々しく情緒豊かなライトノベルの本文（地の文と自然な会話劇）を執筆してください。

【執筆スタイルと絶対ルール】
1. 情景描写と心理描写：キャンパスの空気感、黒板にチョークで描かれる美しい数式やグラフ、PCモニターに広がる3D構造、実験器具のガラスの煌めき、主人公の少女が数学・情報学・科学の美しさに触れて目を輝かせる心の動きを、小説らしい美しい日本語で丁寧に描写してください。
2. 専門用語の噛み砕き：難しい数式や専門用語の羅列は避け、シャボン玉、ステンドグラス、折り紙、編み物、星座、手紙などの日常の美しい比喩と会話劇のなかに数学・情報・科学の仕組みを自然に溶け込ませてください。
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
                        if any(
                            skip in t_str.lower()
                            for skip in (
                                "author correction",
                                "publisher correction",
                                "erratum",
                                "corrigendum",
                                "faculty opinions",
                                "f1000prime",
                                "reply to",
                            )
                        ):
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
    - Primary Node (`http://rtx5060lp:11434`): Ollama `qwen3.5:9b` (Director) × `shosetsu` (Writer)
    - Secondary Node (`http://sff7020:1234`): LM Studio `google/gemma-4-26b-a4b-qat` (Dramatic / Expressive Writer & Director)
    - Illustration Node (`http://kenomac-mini:7860`): Draw Things `FLUX.2 [klein] 4B`
    Supports alternating episode assignment between Primary (`rtx5060lp`) and Secondary (`sff7020`) with automatic failover.
    """

    PRIMARY_HOSTS = ["http://rtx5060lp:11434", "http://192.168.128.62:11434"]
    SECONDARY_HOSTS = ["http://sff7020:1234", "http://192.168.128.16:1234"]

    def __init__(
        self,
        ollama_host: Optional[str] = None,
        director_model: Optional[str] = None,
        writer_model: Optional[str] = None,
        draw_things_host: Optional[str] = None,
        lorebook_path: Path = LOREBOOK_FILE,
        alternate_hosts: bool = True,
    ):
        raw_host = (ollama_host or os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)).strip()
        primary_hosts = [h.strip().rstrip("/") for h in raw_host.split(",") if h.strip()]
        self.ollama_host = primary_hosts[0] if primary_hosts else DEFAULT_OLLAMA_HOST
        self.ollama_hosts: List[str] = list(primary_hosts)
        for fb in FALLBACK_OLLAMA_HOSTS:
            fb_clean = fb.rstrip("/")
            if fb_clean not in self.ollama_hosts:
                self.ollama_hosts.append(fb_clean)
        self.director_model = director_model or os.getenv("OLLAMA_DIRECTOR_MODEL", DEFAULT_DIRECTOR_MODEL)
        self.writer_model = writer_model or os.getenv("OLLAMA_WRITER_MODEL", DEFAULT_WRITER_MODEL)
        self.lm_studio_model = os.getenv("LM_STUDIO_MODEL", DEFAULT_LM_STUDIO_MODEL)
        self.draw_things_host = (draw_things_host or os.getenv("DRAW_THINGS_HOST", DEFAULT_DRAW_THINGS_HOST)).rstrip("/")
        self.lorebook_path = lorebook_path
        self.lorebook = self._load_lorebook()
        self.alternate_hosts = alternate_hosts
        self.last_used_node: Optional[str] = None

    @staticmethod
    def _is_openai_compatible_host(host: str) -> bool:
        h = host.lower()
        return ":1234" in h or "sff7020" in h or "192.168.128.16" in h

    @staticmethod
    def _node_name_for_host(host: str) -> str:
        h = host.lower()
        if "sff7020" in h or "192.168.128.16" in h or ":1234" in h:
            return "sff7020"
        return "rtx5060lp"

    def select_alternating_host_for_work(
        self,
        work: Dict[str, Any],
        preferred_node: Optional[str] = None,
    ) -> str:
        """
        Alternates episode assignment between Primary (`rtx5060lp:11434`) and Secondary (`sff7020:1234`):
        - If `preferred_node` is provided ('rtx5060lp' or 'sff7020'), uses that node first.
        - Otherwise, if `self.last_used_node` is set in the current batch, switches to the other node.
        - Otherwise, alternates by `episode_num` (odd episodes -> `sff7020`, even episodes -> `rtx5060lp`).
        Automatic failover to the other node remains active if the preferred node is offline.
        """
        if not self.alternate_hosts and not preferred_node:
            return self.ollama_host

        target_node = preferred_node or work.get("assigned_writer")
        if target_node not in ("rtx5060lp", "sff7020"):
            if self.last_used_node == "rtx5060lp":
                target_node = "sff7020"
            elif self.last_used_node == "sff7020":
                target_node = "rtx5060lp"
            else:
                ep_num = int(work.get("episode_num", 1) or 1)
                target_node = "sff7020" if (ep_num % 2 == 1) else "rtx5060lp"

        if target_node == "sff7020":
            ordered = self.SECONDARY_HOSTS + self.PRIMARY_HOSTS
        else:
            ordered = self.PRIMARY_HOSTS + self.SECONDARY_HOSTS

        for h in self.ollama_hosts:
            if h not in ordered:
                ordered.append(h)
        self.ollama_hosts = ordered
        self.ollama_host = ordered[0]
        logger.info(
            f"[Alternating LLM Scheduler] Episode #{work.get('episode_num', '?')} ('{work.get('id', '')}') "
            f"assigned to '{target_node}' (primary URL: {self.ollama_host}, fallback ready)"
        )
        return target_node

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

    def check_draw_things_connection(self) -> Dict[str, Any]:
        """Checks connection to Mac mini Draw Things HTTP API server (/sdapi/v1/options)."""
        for candidate in [self.draw_things_host, "http://kenomac-mini:7860", "http://192.168.128.59:7860"]:
            cand = candidate.rstrip("/")
            try:
                req = urllib.request.Request(f"{cand}/sdapi/v1/options")
                with urllib.request.urlopen(req, timeout=5) as res:
                    if res.getcode() == 200:
                        data = json.loads(res.read().decode("utf-8", errors="ignore"))
                        self.draw_things_host = cand
                        return {
                            "online": True,
                            "host": self.draw_things_host,
                            "model": data.get("model", "flux_2_klein_base_4b_i8x.ckpt"),
                        }
            except Exception:
                continue
        return {
            "online": False,
            "host": self.draw_things_host,
            "error": "Unreachable",
        }

    def check_connection(self) -> Dict[str, Any]:
        """Checks connection to Primary (rtx5060lp:11434) and Secondary (sff7020:1234) LLM servers and returns status."""
        dt_status = self.check_draw_things_connection()
        last_err = None
        for candidate_host in self.ollama_hosts:
            try:
                if self._is_openai_compatible_host(candidate_host):
                    req = urllib.request.Request(f"{candidate_host}/v1/models")
                    with urllib.request.urlopen(req, timeout=5) as res:
                        if res.getcode() == 200:
                            data = json.loads(res.read().decode("utf-8", errors="ignore"))
                            models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
                            if candidate_host != self.ollama_host:
                                logger.info(f"Switched active LLM host from {self.ollama_host} to {candidate_host}")
                                self.ollama_host = candidate_host
                            return {
                                "online": True,
                                "host": self.ollama_host,
                                "models": models,
                                "director_ready": len(models) > 0,
                                "writer_ready": len(models) > 0,
                                "draw_things_online": dt_status.get("online", False),
                                "draw_things_host": self.draw_things_host,
                                "draw_things_model": dt_status.get("model", ""),
                            }
                else:
                    req = urllib.request.Request(f"{candidate_host}/api/tags")
                    with urllib.request.urlopen(req, timeout=5) as res:
                        if res.getcode() == 200:
                            data = json.loads(res.read().decode("utf-8", errors="ignore"))
                            models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                            if candidate_host != self.ollama_host:
                                logger.info(f"Switched active Ollama host from {self.ollama_host} to {candidate_host}")
                                self.ollama_host = candidate_host
                            model_lookup = set(models) | {m.split(":")[0] for m in models}
                            if self.director_model not in model_lookup:
                                for cand in ("qwen3.5:9b", "ronbun", "qwen2.5:14b"):
                                    if cand in model_lookup:
                                        self.director_model = cand
                                        break
                            if self.writer_model not in model_lookup:
                                for cand in ("shosetsu", "gemma4:12b", "gemma2:9b"):
                                    if cand in model_lookup:
                                        self.writer_model = cand
                                        break
                            return {
                                "online": True,
                                "host": self.ollama_host,
                                "models": models,
                                "director_ready": self.director_model in model_lookup,
                                "writer_ready": self.writer_model in model_lookup,
                                "draw_things_online": dt_status.get("online", False),
                                "draw_things_host": self.draw_things_host,
                                "draw_things_model": dt_status.get("model", ""),
                            }
            except Exception as e:
                last_err = e
                logger.debug(f"LLM check failed on {candidate_host}: {e}")
        return {
            "online": False,
            "host": self.ollama_host,
            "models": [],
            "error": str(last_err) if last_err else "Unreachable",
            "director_ready": False,
            "writer_ready": False,
            "draw_things_online": dt_status.get("online", False),
            "draw_things_host": self.draw_things_host,
            "draw_things_model": dt_status.get("model", ""),
        }

    def call_ollama_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        num_predict: int = 2000,
        num_ctx: int = 4096,
        timeout: int = 900,
        max_retries: int = 3,
        keep_alive: Optional[Any] = None,
    ) -> str:
        """
        Calls either Ollama (/api/chat on rtx5060lp:11434) or LM Studio OpenAI API
        (/v1/chat/completions on sff7020:1234 with reasoning_effort='none'), with automatic failover.
        """
        if model.split(":")[0] == "shosetsu":
            opts: Dict[str, Any] = {"num_predict": num_predict}
        else:
            opts = {
                "temperature": temperature,
                "num_predict": num_predict,
                "num_ctx": num_ctx,
                "repeat_penalty": 1.12,
            }
        ollama_payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": opts,
        }
        if keep_alive is not None:
            ollama_payload["keep_alive"] = keep_alive

        hosts_to_try = [self.ollama_host] + [h for h in self.ollama_hosts if h != self.ollama_host]
        last_err: Optional[Exception] = None
        for attempt in range(1, max_retries + 1):
            for host in hosts_to_try:
                try:
                    if self._is_openai_compatible_host(host):
                        url = f"{host}/v1/chat/completions"
                        oai_messages = list(messages)
                        if not any(m.get("role") == "system" for m in oai_messages):
                            oai_messages.insert(0, {"role": "system", "content": WRITER_SYSTEM_PROMPT})
                        oai_payload = {
                            "model": self.lm_studio_model,
                            "messages": oai_messages,
                            "temperature": temperature,
                            "max_tokens": num_predict,
                            "reasoning_effort": "none",
                            "stream": False,
                        }
                        req = urllib.request.Request(
                            url,
                            data=json.dumps(oai_payload).encode("utf-8"),
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        )
                        with urllib.request.urlopen(req, timeout=timeout) as res:
                            body = json.loads(res.read().decode("utf-8", errors="ignore"))
                            if host != self.ollama_host:
                                logger.info(f"Switched active LLM host to {host} (LM Studio: {self.lm_studio_model})")
                                self.ollama_host = host
                            self.last_used_node = self._node_name_for_host(host)
                            choices = body.get("choices", [])
                            if choices:
                                msg_obj = choices[0].get("message", {})
                                content = (msg_obj.get("content") or "").strip()
                                if content:
                                    return content
                            raise RuntimeError(f"Empty content from LM Studio @ {host}")
                    else:
                        url = f"{host}/api/chat"
                        req = urllib.request.Request(
                            url,
                            data=json.dumps(ollama_payload).encode("utf-8"),
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        )
                        with urllib.request.urlopen(req, timeout=timeout) as res:
                            body = json.loads(res.read().decode("utf-8", errors="ignore"))
                            if host != self.ollama_host:
                                logger.info(f"Switched active Ollama host to {host}")
                                self.ollama_host = host
                            self.last_used_node = self._node_name_for_host(host)
                            return body.get("message", {}).get("content", "").strip()
                except Exception as e:
                    last_err = e
                    logger.warning(f"LLM chat call ({model} @ {host}) attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(5 * attempt)
        raise RuntimeError(f"LLM chat call ({model}) failed after {max_retries} attempts across {hosts_to_try}: {last_err}")

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
                f"  ・好奇心旺盛で素直な高校生。理系進学や大学の研究室、または将来「数学・情報・理科の先生（教員）」や研究者になる道に憧れと少しの不安を抱いている。\n"
                f"- **メンター（大学の先輩・女性研究者・教職課程履修生）**: {work.get('mentor', '白石 凛（大学院生）')}（{work.get('faculty', '理学部')}）\n"
                f"  ・研究と教育を心から楽しむ知的で優しいお姉さん。専門知識を日常の美しい比喩でわかりやすく教えてくれる。"
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
        Step 1: Uses `qwen3.5:9b` (Director) to create a detailed 4-scene plot blueprint
        ensuring scientific accuracy, character consistency, and narrative arc.
        """
        char_context = self._build_character_context(work)
        tech_lines = []
        for idx, p in enumerate(verified_papers, start=1):
            tech_lines.append(
                f"{idx}. 【科学・数理・情報要素{idx}: {p['tech_label']}】\n"
                f"   - 根拠論文: {p['authors']} ({p['year']}) \"{p['title']}\" (*{p['journal']}*)"
            )
        tech_block = "\n".join(tech_lines)

        world_setting = self.lorebook.get("world_setting", "")
        custom_block = f"\n【追加オーダー・特記事項】\n{custom_instruction}\n" if custom_instruction else ""

        prompt = f"""あなたは構成作家（{self.director_model}）です。以下のエピソード設定・キャラクター設定・実在の科学論文にもとづき、執筆作家（{self.writer_model}）が情緒豊かなライトノベルを執筆するための**【緻密な4シーン構成プロット設計図】**を作成してください。

【シリーズ世界観】
{world_setting}

【今回のエピソード情報】
- エピソードタイトル案: {work.get('title')}
- 舞台となる大学・学部・研究室: {work.get('faculty')}
- テーマ（数学・情報学・自然科学・教職など）: {work.get('theme')}
- キーワード: {work.get('modern_tech')}
- あらすじ概要: {work.get('summary')}

【登場キャラクター設定（ロアブック）】
{char_context}

【作中に組み込む実在の査読論文・学術ファクト（3点）】
{tech_block}
{custom_block}
【出力してほしい構成案のフォーマット】
1. **TITLE**: 『{work.get('title')}』をベースにした、理系女子が思わず読みたくなる魅力的で詩的な本編タイトル（副題つき。第？話はつけないこと）
2. **第1シーン（日常の疑問とキャンパス・研究室への訪問）**:
   - 季節・時間帯・キャンパスの風景（光や音、匂いなどの五感要素）
   - 主人公の抱える小さな悩みや進路の迷い（研究者になるか、数学・情報・理科の先生になるか等）、研究室へ足を踏み入れるきっかけ
3. **第2シーン（先輩・先生との出会いと最初のデモ・体験）**:
   - メンター（先輩/研究者/教職課程の学生）の登場シーンと印象的な第一声
   - 要素1・2を目で見て体験する実験・数理パズル・シミュレーションの描写、日常の身近な比喩（なぜその現象や数理が成り立つのかの直感的な説明）
4. **第3シーン（学問の核心への驚きとセンス・オブ・ワンダー）**:
   - 主人公の「どうして？」という質問から、要素3（数理・アルゴリズム・分子・物理の仕組み）の核心に触れる対話
   - 「数学や情報、科学って暗記じゃなくて、世界の秘密を解き明かし、誰かに伝えるための言葉なんだ！」と主人公の認識が鮮やかに変わる瞬間
5. **第4シーン（未来への一歩と爽やかな余韻）**:
   - 研究室を出た後の夕暮れ（または星空・帰り道）の情景
   - 「私、この大学で学んで、研究や教育（先生になる道）に挑戦してみたい！」という主人公の前向きな決意と、先輩からの温かいエール
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
        Step 2: Uses `gemma4:12b` (Writer) to write the actual sensory-rich light novel prose
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
                    cand = re.sub(r"^【第\s*\d+\s*話】\s*", "", cand).strip()
                    if len(cand) >= 4:
                        episode_title = cand
                        break

        part1_prompt = f"""あなたは表現力豊かな執筆作家（{self.writer_model}）です。
構成作家（{self.director_model}）が作成した以下の【プロット設計図】と【キャラクター設定】をもとに、理系女子が大学に行きたくなる爽やかで情緒豊かな科学・数理・情報ライトノベルの**【前半パート（第1シーン・第2シーン：目標1,800〜2,200文字）】**を執筆してください。

※重要：物語全体を前半・後半の2回に分けて執筆します。今回の出力では**絶対に物語を完結させず（『（了）』と書かず）**、第2シーンの実験・数理モデル・シミュレーションで美しい現象が目の前に現れ、主人公が「えっ、どうしてこんなことが起きるんですか！？」と目を輝かせた場面で後半へバトンを渡してください。

【エピソード基本設定】
- タイトル: {episode_title}
- 舞台: {work.get('faculty')}
- テーマ: {work.get('theme')}
- あらすじ: {work.get('summary')}

【キャラクター設定】
{char_context}

【構成作家（{self.director_model}）によるプロット設計図】
{plot_blueprint}

【前半パート（第1シーン・第2シーン）の執筆ルール】
1. 1行目には `TITLE: {episode_title}` の形式でタイトルのみを出力してください（第？話はつけないこと）。
2. 続けて、小説本文（第1シーン：キャンパスの風景と主人公の訪問）を書き始めてください。「第1シーン」「【起】」などの見出しは絶対に入れず、美しい地の文とセリフだけで紡いでください。
3. 第1シーンと第2シーンの間には `* * *` を1行入れてください。
4. 五感（光の粒、黒板のチョークの音、モニターの輝き、ガラス器具の透明感、紅茶の香り）を豊かに描写し、登場人物の掛け合いを生き生きと書いてください。"""

        if progress_callback:
            progress_callback(f"執筆作家 ({self.writer_model}) が前半パート（第1・第2シーン）を執筆中...")
        logger.info(f"[Writer: {self.writer_model}] Writing Novel Prose Part 1 (Scenes 1 & 2)...")
        is_shosetsu = self.writer_model.split(":")[0] == "shosetsu"
        part1_messages = (
            [{"role": "user", "content": part1_prompt}]
            if is_shosetsu
            else [
                {"role": "system", "content": WRITER_SYSTEM_PROMPT},
                {"role": "user", "content": part1_prompt},
            ]
        )
        raw_part1 = self.call_ollama_chat(
            model=self.writer_model,
            messages=part1_messages,
            temperature=0.78,
            num_predict=1800,
            num_ctx=4096,
        )
        cleaned_part1 = self._clean_llm_output(raw_part1)

        p1_lines = []
        for idx, line in enumerate(cleaned_part1.splitlines()):
            stripped = line.strip()
            if idx < 4 and (stripped.startswith("TITLE:") or stripped.startswith("# ")):
                cand = re.sub(r"^(?:TITLE:|#+)\s*", "", stripped).strip(" 『』\"'*")
                cand = re.sub(r"^【第\s*\d+\s*話】\s*", "", cand).strip()
                if cand:
                    episode_title = cand
                continue
            if stripped in ("（了）", "(了)", "（完）"):
                continue
            p1_lines.append(line)
        part1_body = "\n".join(p1_lines).strip()
        part1_tail = part1_body[-450:] if len(part1_body) > 450 else part1_body

        part2_prompt = f"""以下の設定・プロット設計図・直前の本文（前半の末尾）を引き継ぎ、小説『{episode_title}』の**【後半パート（第3シーン・第4シーン：1,200〜1,600文字）】**を執筆し、物語を感動的に完結させてください。

【キャラクター設定】
{char_context}

【プロット設計図】
{plot_blueprint}

【直前の本文（前半の末尾）】
{part1_tail}

【後半パート（第3シーン・第4シーン）の執筆ルール】
1. タイトルは書かず、直前の本文のすぐ後に続く小説本文（第3シーン：数理・情報・科学の仕組みのやさしい解き明かしと主人公の感動）から自然に書き始めてください。
2. 前半の登場人物の口調・一人称・名前を維持してください。
3. 第3シーンと第4シーンの間には `* * *` を1行入れてください（「第3シーン」等の見出しは禁止）。
4. 第4シーンでは、主人公が未来への一歩を踏み出す爽やかで温かい余韻を描き、最後は必ず `（了）` で締めくくってください。"""

        if progress_callback:
            progress_callback(f"執筆作家 ({self.writer_model}) が後半パート（第3・第4シーン）を執筆中...")
        logger.info(f"[Writer: {self.writer_model}] Writing Novel Prose Part 2 (Scenes 3 & 4)...")
        part2_messages = (
            [{"role": "user", "content": part2_prompt}]
            if is_shosetsu
            else [
                {"role": "system", "content": WRITER_SYSTEM_PROMPT},
                {"role": "user", "content": part2_prompt},
            ]
        )
        raw_part2 = self.call_ollama_chat(
            model=self.writer_model,
            messages=part2_messages,
            temperature=0.78,
            num_predict=1800,
            num_ctx=4096,
            keep_alive=0,
        )
        cleaned_part2 = self._clean_llm_output(raw_part2)
        p2_lines = []
        for line in cleaned_part2.splitlines():
            stripped = line.strip()
            if "【高校生のための" in stripped or "【作中科学の" in stripped or "【引用・参考文献" in stripped or "【理系女子のための" in stripped:
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
        Step 3: Uses `qwen3.5:9b` (Director) to write an accurate, inspiring
        "Science Column, University Lab & Career Guide (including Teaching License path) for High School Girls"
        grounded in the 3 verified papers.
        """
        tech_lines = []
        for idx, p in enumerate(verified_papers, start=1):
            tech_lines.append(
                f"{idx}. **{p['tech_label']}**\n"
                f"   - 実在根拠論文: {p['authors']} ({p['year']}) \"{p['title']}\" (*{p['journal']}*)"
            )
        tech_block = "\n".join(tech_lines)

        prompt = f"""先ほど完成したライトノベル『{episode_title}』（舞台：{work.get('faculty')}／テーマ：{work.get('theme')}）の読者（理系に興味がある女子中高生）に向けて、構成作家（{self.director_model}）として**【理系女子のためのやさしい最新科学・数理・情報コラム＆大学研究室・キャリアガイド】**を執筆してください。

【解説する3つの最新トピックと実在根拠論文】
{tech_block}

【出力フォーマット（以下の形式のみを出力し、URLや参考文献リストは書かないでください）】
物語に登場した『{work.get('theme')}』は、すべて実際の大学や研究機関で進められている本物の最先端の学問です。高校の数学・情報・理科（物理・化学・生物・地学）とどう繋がっているのか、一緒に見てみましょう！

1. **{verified_papers[0]['tech_label']}**
   - **どんな仕組み？（やさしい解説）**: （専門知識がなくてもワクワクしながら理解できるように、仕組みを平易かつ正確に解説）
   - **高校の科目（数学・情報・理科）とのつながり＆未来への応用**: （高校のどの分野の発展か、将来どんな社会や未来をつくるかを解説）

2. **{verified_papers[min(1, len(verified_papers)-1)]['tech_label']}**
   - **どんな仕組み？（やさしい解説）**: （平易でわかりやすい解説）
   - **高校の科目（数学・情報・理科）とのつながり＆未来への応用**: （将来への応用と魅力）

3. **{verified_papers[min(2, len(verified_papers)-1)]['tech_label']}**
   - **どんな仕組み？（やさしい解説）**: （平易でわかりやすい解説）
   - **高校の科目（数学・情報・理科）とのつながり＆未来への応用**: （将来への応用と魅力）

- **🎓 この学問に出会える大学の学部・学科と、広がる未来のキャリア（研究者・エンジニア・そして『教員（先生）』になる道）**:
  （『{work.get('faculty')}』などの学部・学科でどんな楽しいキャンパスライフや研究が待っているかに加え、大学で本格的な研究に触れながら**「教職課程」を履修して中学校・高校の『数学・情報・理科の先生（教員免許）』を取得し、本物の学問の面白さを次の世代の生徒たちに伝える教員になる道**や、研究者・データサイエンティスト・エンジニアなど多様な理系キャリアの魅力を温かく具体的に紹介）"""

        logger.info(f"[Director: {self.director_model}] Writing Science Column & University/Teacher Career Guide...")
        raw_guide = self.call_ollama_chat(
            model=self.director_model,
            messages=[
                {"role": "system", "content": DIRECTOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            num_predict=1800,
            num_ctx=8192,
        )
        guide_body = self._clean_llm_output(raw_guide)
        guide_body = re.sub(r"^#+.*最新科学.*?\n", "", guide_body).strip()
        guide_body = re.sub(r"###\s*【引用・参考文献.*", "", guide_body, flags=re.DOTALL).strip()
        guide_body = re.sub(r"https?://\S+", "", guide_body)
        return guide_body

    @staticmethod
    def _koma(p1: str, p2: str, p3: str, p4: str) -> str:
        return (
            "Vertical four-panel comic strip, Japanese yonkoma manga layout, 4 rectangular panels stacked vertically from top to bottom with clean white borders separating the panels, full color Japanese anime art style. "
            f"Top panel 1 (Introduction): {p1.strip()} "
            f"Second panel 2 (Development): {p2.strip()} "
            f"Third panel 3 (Climax): {p3.strip()} "
            f"Bottom panel 4 (Resolution): {p4.strip()} "
            "Masterpiece anime comic strip, clean panel division, rich deep colors, high contrast, crisp lines, completely pure illustration, NO speech bubbles, NO text, NO words, NO letters, NO Japanese characters, NO sound effects."
        )

    CURATED_EPISODE_IMAGE_PROMPTS: Dict[str, str] = {
        "ep01-bioluminescence-plant": _koma.__func__(
            "a high school girl arriving at a sunlit university science campus with curiosity.",
            "the girl meets a warmly smiling female researcher in a botany laboratory with emerald petunias.",
            "close-up of both smiling happily as they examine the glowing bioluminescent plant in a glass flask.",
            "both the high school girl and female researcher smiling joyfully together under the evening starry sky, looking toward the future.",
        ),
        "ep02-crispr-butterfly-structural-color": _koma.__func__(
            "a high school girl entering a university biology lab filled with warm afternoon sunlight.",
            "a smiling female researcher introduces optical microscope slides and butterfly specimens.",
            "both smiling in wonder at an iridescent metallic-blue Morpho butterfly structural color shimmering near an optical prism.",
            "both smiling warmly side by side with hopeful expressions by the twilight window.",
        ),
        "ep03-mrna-lipid-nanoparticle-delivery": _koma.__func__(
            "a high school girl visiting a modern pharmaceutical science building.",
            "a female researcher in a lab coat enthusiastically demonstrating microfluidic glass tubes.",
            "both smiling brightly at translucent glowing spherical lipid nanoparticle molecular models on the workbench.",
            "both smiling together looking toward the future of medicine under soft evening lights.",
        ),
        "ep04-math-topology-knot-teacher": _koma.__func__(
            "a high school girl looking puzzled at geometric diagrams in a math seminar room.",
            "a smiling female mathematics mentor researcher offering colorful braided ribbons with an encouraging smile.",
            "both smiling happily as they manipulate colorful topological knot loops and Möbius strip rings.",
            "both smiling warmly in front of the sunlit blackboard with newfound love for mathematics.",
        ),
        "ep05-alphafold-informatics-teacher": _koma.__func__(
            "a high school girl arriving at a university bioinformatics computer workstation studio.",
            "a female researcher enthusiastically pointing toward an open workspace with molecular graphics.",
            "both smiling in awe at a colorful 3D folded protein ribbon model with teal and coral alpha-helices.",
            "both smiling brightly together looking forward to careers in data science and teaching.",
        ),
        "ep06-quantum-cryptography-math-informatics": _koma.__func__(
            "a high school girl stepping into an optics and quantum information laboratory.",
            "a smiling female researcher adjusting optical mirrors and crystal prisms on an optical table.",
            "both smiling in wonder at a delicate cyan and magenta entangled laser beam splitting across crystals.",
            "both smiling joyfully side by side in the twilight laboratory holding optical lenses.",
        ),
        "ep07-exoplanet-jwst-science-teacher": _koma.__func__(
            "a high school girl climbing up the stairs of a university astronomical observatory dome.",
            "a female astronomy researcher pointing toward the opening slit of the dome under twilight.",
            "both smiling in delight beside a gleaming golden hexagonal segmented telescope mirror model.",
            "both looking up with gentle joyful smiles at the vast starry sky filled with shining exoplanets.",
        ),
        "ep08-network-science-math-modeling": _koma.__func__(
            "a high school girl entering a bright applied mathematics lounge with curiosity.",
            "a smiling female mentor researcher showing natural graph patterns and complex systems.",
            "both smiling happily at an illuminated 3D geometric network sculpture of glowing golden nodes and connecting lines.",
            "both smiling warmly together by the sunny window inspired by the harmony of network mathematics.",
        ),
        "ep09-spider-silk-biomaterials": _koma.__func__(
            "a high school girl arriving at a high-tech polymer biomaterials laboratory.",
            "a smiling female researcher presenting natural silk cocoons and spinning micro-needles.",
            "both smiling with delight as they examine a shimmering golden artificial spider-silk spool glistening in the light.",
            "both smiling proudly together side by side, looking forward to sustainable future engineering.",
        ),
        "ep10-perovskite-solar-window": _koma.__func__(
            "a high school girl visiting a renewable energy and materials chemistry laboratory.",
            "a female researcher demonstrating thin film coating techniques on glass substrates.",
            "both smiling brightly as they hold up a thin flexible ruby-amber translucent perovskite solar film catching golden sunlight.",
            "both smiling warmly side by side with clean energy dreams shining in their eyes.",
        ),
        "ep11-sleep-glymphatic-memory-consolidation": _koma.__func__(
            "a high school girl with dark hair arriving at a quiet medical neuroscience and sleep laboratory at twilight with a thoughtful expression.",
            "a smiling female professor wearing glasses and white lab coat showing a luminous display illustrating clear water waves flowing through cellular spaces.",
            "both smiling in wonder examining an exquisite translucent crystal brain sculpture softly glowing with flowing sapphire-blue liquid streams and golden floating particles.",
            "both smiling brightly and warmly side by side by the dawn window, completely refreshed and inspired by brain science.",
        ),
        "ep12-environmental-dna-ocean-ecology": _koma.__func__(
            "a high school girl walking onto a marine biology research deck overlooking a sparkling blue bay.",
            "a smiling female marine ecologist demonstrating water sampling filters and DNA sequencing tubes.",
            "both smiling with joy as they hold a clear glass seawater sample bottle glittering in the ocean breeze.",
            "both smiling side by side gazing out at the vast ocean horizon under bright sunny skies.",
        ),
        "ep13-neural-symbolic-logic-math-teacher": _koma.__func__(
            "a high school girl entering a warm wooden math and AI seminar room.",
            "a smiling female researcher showing geometric logic puzzles and symbolic reasoning models.",
            "both smiling happily as they assemble translucent geometric polyhedron crystal models in golden sunlight.",
            "both smiling warmly with confidence in logic and mathematics by the afternoon window.",
        ),
        "ep14-statistical-mechanics-chaos-physics-teacher": _koma.__func__(
            "a high school girl visiting a classic physics and dynamics laboratory.",
            "a female physics researcher setting up a brass double pendulum and fluid dynamics apparatus.",
            "both smiling in fascination at swirling iridescent soap-film convection patterns and chaotic trajectories glowing in sunlight.",
            "both smiling joyfully side by side, discovering the hidden beauty within chaos physics.",
        ),
        "ep15-bionanotechnology-synthetic-genetics-materials": _koma.__func__(
            "a high school girl arriving at a synthetic genetics and bio-nanotechnology lab.",
            "a female researcher displaying natural nacre sea shells and biomolecular structure diagrams.",
            "both smiling in wonder beside an iridescent pearl-like artificial shell model and colorful DNA double-helix models.",
            "both smiling warmly together with enthusiasm for creative bioengineering careers.",
        ),
        "ep16-topological-data-analysis-persistent-homology": _koma.__func__(
            "a high school girl visiting an advanced data science and applied topology studio.",
            "a smiling female data scientist explaining geometric data shapes and persistent homology.",
            "both smiling happily examining a 3D simplicial complex crystal sculpture and torus models catching warm light.",
            "both smiling brightly side by side with newfound appreciation for abstract geometry.",
        ),
        "ep17-dna-origami-molecular-robotics": _koma.__func__(
            "a high school girl entering a molecular robotics laboratory with colorful paper cranes.",
            "a smiling female researcher demonstrating nanoscale self-folding DNA nanostructures.",
            "both smiling in delight as they hold folded origami paper beside a glowing nanoscale DNA box model.",
            "both smiling joyfully side by side inspired by the union of traditional origami and molecular robotics.",
        ),
        "ep18-gravitational-waves-laser-interferometer": _koma.__func__(
            "a high school girl visiting a precision laser optics and gravitational wave laboratory.",
            "a female astrophysics researcher demonstrating ultra-quiet vibration isolation pendulums.",
            "both smiling in awe beside a suspended sapphire mirror pendulum reflecting emerald laser beams.",
            "both smiling warmly side by side, listening to the cosmic ripples of the universe.",
        ),
        "ep19-mof-porous-coordination-polymers-carbon-capture": _koma.__func__(
            "a high school girl arriving at a coordination chemistry and molecular sponge laboratory.",
            "a smiling female chemist presenting porous crystals capable of trapping carbon dioxide.",
            "both smiling in wonder at a turquoise-blue porous crystal lattice MOF model catching bright afternoon sunlight.",
            "both smiling brightly together side by side, dreaming of a greener future for our planet.",
        ),
        "ep20-turing-pattern-reaction-diffusion-math-biology": _koma.__func__(
            "a high school girl entering a mathematical biology laboratory.",
            "a smiling female mentor researcher showing natural seashell patterns and differential equations.",
            "both smiling happily observing seashells with intricate stripe patterns beside a ripple wave petri dish.",
            "both smiling warmly side by side with deep admiration for the mathematical patterns of nature.",
        ),
        "ep21-compressed-sensing-black-hole-imaging-informatics": _koma.__func__(
            "a high school girl arriving at an astrophysics informatics lab at dusk.",
            "a female researcher demonstrating sparse modeling and radio telescope image reconstruction.",
            "both smiling in wonder beside a glowing golden ring model of a black hole shadow and miniature radio dish.",
            "both smiling joyfully together side by side under the darkening twilight sky.",
        ),
        "ep22-ips-organoid-regenerative-medicine-pharmacology": _koma.__func__(
            "a high school girl visiting a bright regenerative medicine and stem cell lab.",
            "a smiling female pharmacologist preparing culture dishes and stereo microscopes.",
            "both smiling in joy observing tiny organoid tissues softly glowing with warm ruby-pink light in a culture dish.",
            "both smiling warmly together side by side, inspired by the future of personalized medicine.",
        ),
        "ep23-topological-insulator-spintronics-physics": _koma.__func__(
            "a high school girl entering a quantum materials and solid-state physics lab.",
            "a smiling female physicist presenting crystal specimens and electronic surface band models.",
            "both smiling in amazement examining a metallic bismuth-telluride crystal and a glowing Dirac cone sculpture.",
            "both smiling brightly side by side with excitement for next-generation quantum technology.",
        ),
        "ep24-click-chemistry-bioorthogonal-reaction": _koma.__func__(
            "a high school girl visiting a chemical biology and click chemistry laboratory.",
            "a female researcher demonstrating snap-together bioorthogonal reaction mechanisms.",
            "both smiling with delight as they snap together interlocking colorful molecular ring models beside fluorescent flasks.",
            "both smiling warmly side by side, proud of the elegant power of molecular chemistry.",
        ),
        "ep25-fourier-transform-music-acoustics-math-teacher": _koma.__func__(
            "a high school girl holding a violin entering a sunlit acoustics and mathematics room.",
            "a smiling female researcher listening to violin tones and analyzing soundwave harmonics.",
            "both smiling happily beside golden harmonic wave sculptures resonating with musical pitch in afternoon light.",
            "both smiling joyfully side by side, celebrating the beautiful harmony of music and mathematics.",
        ),
        "ep26-optogenetics-channelrhodopsin-neuroscience": _koma.__func__(
            "a high school girl arriving at an optogenetics neurobiology laboratory.",
            "a female neuroscientist presenting green microalgae flasks and optical fiber switches.",
            "both smiling in wonder as a delicate sapphire-blue fiber-optic light beam activates channelrhodopsin models.",
            "both smiling brightly together side by side, fascinated by the light switches of the brain.",
        ),
        "ep27-autonomous-driving-slam-bayesian-informatics": _koma.__func__(
            "a high school girl visiting an autonomous robotics and artificial intelligence laboratory.",
            "a smiling female roboticist demonstrating mapping algorithms and Bayesian sensor estimation.",
            "both smiling with joy beside a compact wheeled autonomous rover robot with a spinning silver LiDAR sensor.",
            "both smiling warmly side by side with confidence in robotics and engineering.",
        ),
        "ep28-ice-core-paleoclimate-isotope-earth-science": _koma.__func__(
            "a high school girl in a winter jacket entering a paleoclimate ice-core laboratory.",
            "a smiling female geochemist preparing cold-storage Antarctic ice specimens.",
            "both smiling in awe as they examine a cylindrical Antarctic ice core sparkling with ancient atmospheric air bubbles.",
            "both smiling warmly side by side, reading eighty-thousand years of Earth history.",
        ),
        "ep29-artificial-photosynthesis-photocatalyst-chemistry": _koma.__func__(
            "a high school girl visiting a sunlit solar chemistry and artificial photosynthesis laboratory.",
            "a female researcher demonstrating titanium photocatalyst electrodes submerged in water.",
            "both smiling in delight watching sparkling hydrogen and oxygen bubbles rising from an emerald-titanium leaf plate in a glass reactor.",
            "both smiling joyfully side by side in the golden sunlight, inspired by the future of clean solar fuels.",
        ),
    }

    def generate_english_image_prompt(
        self,
        work: Dict[str, Any],
        story_body: str = "",
        episode_title: str = "",
    ) -> str:
        """
        Returns a scene-accurate English 4-panel comic strip prompt for FLUX.2 [klein] 9B.
        Uses curated 4-koma prompts when available, or queries the active LLM if online.
        """
        wid = work.get("id", "")
        if wid in self.CURATED_EPISODE_IMAGE_PROMPTS:
            curated = self.CURATED_EPISODE_IMAGE_PROMPTS[wid]
            logger.info(f"[Curated FLUX.2 4-Panel Prompt] Using 4-panel manga prompt for '{wid}': {curated[:110]}...")
            return curated

        # Fast check if any LLM host is online before attempting chat call
        conn = self.check_connection()
        if not conn.get("online"):
            logger.info(f"LLM servers are currently offline; using structured 4-panel prompt for '{wid}'.")
            return self._koma(
                f"a high school girl arriving at a university science department exploring {wid.replace('-', ' ')} with curiosity.",
                "the girl meets a warmly smiling female researcher in a modern laboratory.",
                f"both smiling in wonder as they examine the core scientific phenomenon of {wid.replace('-', ' ')} on the workbench.",
                "both characters smiling joyfully together side by side under the evening sky, looking toward the future.",
            )

        char_context = self._build_character_context(work)
        story_excerpt = story_body[:500] if story_body else work.get("summary", "")

        prompt = f"""You are an expert Japanese manga and light novel art director.
Based on the following Japanese science novel episode (structured into 4 scenes: 起承転結), write a single, vivid **English image generation prompt** for FLUX.2 to render a **vertical four-panel comic strip (Yonkoma manga layout: 4 vertically stacked rectangular panels with clean white borders separating the panels)** in full color anime art style.

[Episode Info]
- Title: {episode_title or work.get('title', '')}
- University Lab Setting: {work.get('faculty', '')}
- Science/Math/Informatics Theme: {work.get('theme', '')}
- Summary: {work.get('summary', '')}
- Characters:
{char_context}

[Story Excerpt]
{story_excerpt}

[Rules for Output]
1. Output ONLY the raw English prompt paragraph. Do NOT include markdown formatting, quotes, or Japanese text.
2. Structure the prompt into 4 vertically stacked panels corresponding to the story's 起承転結:
   - Start with: "Vertical four-panel comic strip, Japanese yonkoma manga layout, 4 rectangular panels stacked vertically from top to bottom with clean white borders separating the panels, full color Japanese anime art style."
   - Top panel 1 (Introduction / 起): The high school girl visiting the university campus or lab with curiosity.
   - Second panel 2 (Development / 承): The girl meets the female mentor researcher and engages in interactive experiment or demonstration.
   - Third panel 3 (Climax / 転): Both smiling in wonder at the breathtaking visual scientific or mathematical phenomenon.
   - Bottom panel 4 (Resolution / 結): Both characters smiling joyfully together looking toward their future under the evening sky.
3. NEVER mention speech bubbles, words, text, letters, book covers, titles, or dialogue.
4. End with: "Masterpiece anime comic strip, clean panel division, rich deep colors, high contrast, crisp lines, completely pure illustration, NO speech bubbles, NO text, NO words, NO letters, NO Japanese characters, NO sound effects."
"""
        try:
            logger.info(f"[Director: {self.director_model}] Generating English 4-panel manga prompt for FLUX.2...")
            raw_en = self.call_ollama_chat(
                model=self.director_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional prompt engineer for FLUX.2 vertical 4-panel manga comic strips. Output ONLY the English prompt text. Never include speech bubbles, text, letters, or writing.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                num_predict=220,
                num_ctx=8192,
                timeout=120,
                max_retries=1,
                keep_alive=0,
            )
            cleaned_en = self._clean_llm_output(raw_en).strip(" \"'`\n")
            cleaned_en = re.sub(r"^(?:Prompt|English Prompt)\s*[:：]\s*", "", cleaned_en, flags=re.IGNORECASE).strip()
            cleaned_en = " ".join(cleaned_en.splitlines()).strip()
            cleaned_en = re.sub(r"\b(?:speech bubble|dialogue bubble|text|words|letters|kanji)\b", "clean visual", cleaned_en, flags=re.IGNORECASE)
            if len(cleaned_en) >= 40 and "four-panel" in cleaned_en.lower():
                logger.info(f"  -> Generated English 4-panel prompt: {cleaned_en[:120]}...")
                return cleaned_en
        except Exception as e:
            logger.warning(f"Failed to generate English 4-panel prompt via LLM ({e}), using fallback.")

        return self._koma(
            f"a high school girl arriving at a university science department exploring {wid.replace('-', ' ')} with curiosity.",
            "the girl meets a warmly smiling female researcher in a modern laboratory.",
            f"both smiling in wonder as they examine the core scientific phenomenon of {wid.replace('-', ' ')} on the workbench.",
            "both characters smiling joyfully together side by side under the evening sky, looking toward the future.",
        )

    def generate_illustration(
        self,
        work: Dict[str, Any],
        output_image_path: Path,
        story_body: str = "",
        episode_title: str = "",
        custom_english_prompt: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[Optional[Path], str]:
        """
        Generates a vertical 512x1024 4-panel comic strip (Yonkoma manga layout for 起承転結)
        using Draw Things HTTP API (`http://kenomac-mini:7860/sdapi/v1/txt2img`, model `flux_2_klein_base_9b_i8x.ckpt`).
        Returns (saved_image_path_or_None, english_prompt_used).
        """
        dt_conn = self.check_draw_things_connection()
        if not dt_conn.get("online"):
            logger.warning(
                f"Draw Things HTTP API server ({self.draw_things_host}) is not reachable: {dt_conn.get('error')}. Skipping image generation."
            )
            return None, ""

        cached_en = getattr(self, "_cached_en_prompts", {}).get(work.get("id", ""), "")
        if custom_english_prompt and custom_english_prompt.strip():
            en_prompt = custom_english_prompt.strip()
        elif cached_en:
            en_prompt = cached_en
        else:
            if progress_callback:
                progress_callback(f"構成作家 ({self.director_model}) が小説本文から英語の4コマ漫画プロンプトを作成中...")
            en_prompt = self.generate_english_image_prompt(
                work=work,
                story_body=story_body,
                episode_title=episode_title,
            )

        dt_model = dt_conn.get("model", "flux_2_klein_base_9b_i8x.ckpt")
        if progress_callback:
            progress_callback(f"Draw Things ({self.draw_things_host}) で4コマ漫画風の縦長挿絵を生成中 ({dt_model})...")
        logger.info(f"[Draw Things: {self.draw_things_host} ({dt_model})] Generating 512x1024 4-panel manga illustration...")

        url = f"{self.draw_things_host}/sdapi/v1/txt2img"
        payload = {
            "prompt": en_prompt,
            "negative_prompt": (
                "speech bubble, dialogue bubble, speech balloon, text, words, letters, kanji, chinese characters, japanese text, english text, typography, title, "
                "font, calligraphy, signage, label, poster text, book text, fake letters, gibberish, runes, symbols, alphabet, numbers, subtitles, captions, "
                "book cover, watermark, signature, logo, caption, writing, chalk equations, "
                "blurry panels, merged frames, chaotic layout, irregular frame borders, "
                "sad, frowning, serious face, stern expression, solemn, expressionless, angry, worried, crying, gloomy face, "
                "overexposed, washed out, faded, blown-out highlights, whiteout, low contrast, dark, gloomy, hat, cap, helmet"
            ),
            "width": 512,
            "height": 1024,
            "steps": 16,
            "guidance_scale": 4.0,
            "sampler": "Euler A Trailing",
        }
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            start_t = time.time()
            with urllib.request.urlopen(req, timeout=900) as res:
                body = json.loads(res.read().decode("utf-8", errors="ignore"))
                images = body.get("images", [])
                if images and images[0]:
                    b64_str = re.sub(r"^data:image/[^;]+;base64,", "", images[0])
                    img_bytes = base64.b64decode(b64_str)
                    output_image_path.parent.mkdir(parents=True, exist_ok=True)
                    output_image_path.write_bytes(img_bytes)
                    elapsed = time.time() - start_t
                    logger.info(
                        f"[Draw Things Complete] Saved 4-panel manga illustration to {output_image_path} "
                        f"({len(img_bytes)} bytes in {elapsed:.1f}s)"
                    )
                    return output_image_path, en_prompt
                else:
                    logger.warning("Draw Things returned empty images list.")
        except Exception as e:
            logger.error(f"Draw Things image generation failed: {e}")

        return None, en_prompt

    def generate_new_catalog_themes(
        self,
        existing_catalog: List[Dict[str, Any]],
        count: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Uses `qwen3.5:9b` (Director) to automatically design new episode entries for `data/science_catalog.json`
        when all existing catalog themes have been stocked or published, featuring Mathematics, Informatics,
        Natural Sciences, Engineering, and the career path of becoming a school teacher.
        """
        next_ep_num = max([w.get("episode_num", 0) for w in existing_catalog], default=0) + 1
        existing_titles = "\n".join([f"- {w.get('id')}: {w.get('title')} ({w.get('theme')})" for w in existing_catalog[-15:]])

        prompt = f"""あなたは『放課後サイエンス・キャンパス』の構成作家（{self.director_model}）です。
既存のエピソードと重複しない、新しい魅力的な科学・数学・情報学・教職キャリアのライトノベル企画を **{count} 話分** 作成し、**純粋なJSON配列のみ** で出力してください。

【既存エピソード一覧（これらと重複しないこと）】
{existing_titles}

【必須条件】
1. 数学（代数学・幾何学・確率統計・数理モデル等）、情報学（AI・アルゴリズム・暗号・データサイエンス・量子計算等）、物理・化学・生物・地学・工学・薬学・農学、そして「教職課程を履修して数学・情報・理科の先生（高校・中学教員）になる道」をバランスよく取り入れること。
2. 各エピソードの `crossref_queries` には、Crossref APIで確実にヒットする超有名な実在の英語論文（ノーベル賞・フィールズ賞・チューリング賞・Nature・Science等の歴史的または最新の有名論文）の著者名・英語タイトルキーワード・雑誌名・年を3件指定すること。
3. 以下のJSONスキーマの配列（`[ ... ]`）のみを出力し、前後に説明文を入れないこと：

[
  {{
    "id": "ep{next_ep_num:02d}-english-slug-here",
    "episode_num": {next_ep_num},
    "title": "詩的で魅力的な日本語タイトル（第？話はつけない）",
    "faculty": "理学部・〇〇学科 ／ 教育学部・〇〇専攻（研究室名）",
    "protagonist": "姓 名（ふりがな・高校2年生・部活名）",
    "mentor": "姓 名（ふりがな・大学院生または助教・教員免許保持など）",
    "theme": "扱う学問テーマとキャリアテーマ",
    "modern_tech": "具体的な専門キーワード3つ",
    "summary": "女子高校生がキャンパスや研究室を訪れ、先輩や先生との対話・実験・数理体験を通じて学問の美しさと将来の道（研究者や先生になる夢）に目覚める200文字程度のあらすじ。",
    "crossref_queries": [
      {{
        "label": "日本語のトピック見出し1",
        "query": "Author1 Author2 Famous Paper Title Keyword Journal Year"
      }},
      {{
        "label": "日本語のトピック見出し2",
        "query": "Author1 Author2 Famous Paper Title Keyword Journal Year"
      }},
      {{
        "label": "日本語のトピック見出し3",
        "query": "Author1 Author2 Famous Paper Title Keyword Journal Year"
      }}
    ]
  }}
]"""
        try:
            logger.info(f"[Director: {self.director_model}] Designing {count} new catalog themes automatically...")
            raw_json = self.call_ollama_chat(
                model=self.director_model,
                messages=[
                    {"role": "system", "content": "You are a JSON generator. Output valid JSON array only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                num_predict=2800,
                num_ctx=8192,
            )
            cleaned = self._clean_llm_output(raw_json)
            m = re.search(r"\[\s*\{.*\}\s*\]", cleaned, flags=re.DOTALL)
            if m:
                cleaned = m.group(0)
            items = json.loads(cleaned)
            if isinstance(items, list):
                valid_items = []
                existing_ids = {w.get("id") for w in existing_catalog}
                for idx, item in enumerate(items):
                    if isinstance(item, dict) and item.get("title") and item.get("theme"):
                        ep_n = next_ep_num + idx
                        raw_id = str(item.get("id", f"ep{ep_n:02d}-auto-science")).strip()
                        if not raw_id.startswith(f"ep{ep_n:02d}-"):
                            slug = re.sub(r"[^a-z0-9-]+", "-", raw_id.lower()).strip("-")
                            raw_id = f"ep{ep_n:02d}-{slug or 'science-campus'}"
                        if raw_id in existing_ids:
                            raw_id = f"{raw_id}-{int(time.time()) % 1000}"
                        item["id"] = raw_id
                        item["episode_num"] = ep_n
                        if not item.get("crossref_queries"):
                            item["crossref_queries"] = [
                                {
                                    "label": item["theme"],
                                    "query": "Jumper Hassabis Highly accurate protein structure prediction with AlphaFold Nature 2021",
                                }
                            ]
                        valid_items.append(item)
                if valid_items:
                    logger.info(f"Successfully generated {len(valid_items)} new catalog episode theme(s)!")
                    return valid_items
        except Exception as e:
            logger.warning(f"Failed to auto-generate new catalog themes via LLM: {e}")
        return []

    def generate_complete_episode(
        self,
        work: Dict[str, Any],
        custom_plot_override: Optional[str] = None,
        custom_instruction: str = "",
        progress_callback: Optional[Callable[[str], None]] = None,
        preferred_node: Optional[str] = None,
    ) -> Tuple[str, str, List[str], str]:
        """
        Runs the full Collaborative Dual-LLM Pipeline, alternating between Primary (`rtx5060lp:11434`)
        and Secondary (`sff7020:1234`) per episode with automatic failover:
        1) Pre-fetches 3 DOI-verified scientific papers via Crossref REST API.
        2) Creates the 4-scene plot blueprint (or uses custom_plot_override).
        3) Writes the Science Column & University/Teacher Career Guide + English illustration prompt.
        4) Writes the emotional, sensory-rich light novel prose.
        5) Assembles the publication-ready Markdown with YAML frontmatter and verified DOI links.
        Returns: (full_markdown, episode_title, short_refs, plot_blueprint)
        """
        self.select_alternating_host_for_work(work=work, preferred_node=preferred_node)

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

        if progress_callback:
            progress_callback(f"構成作家 ({self.director_model}) が最新科学コラム＆大学・教職ガイドを執筆中...")
        guide_body = self.generate_science_guide_with_director(
            work=work,
            episode_title=work.get("title", "放課後サイエンス・キャンパス"),
            verified_papers=verified_papers,
        )

        if not hasattr(self, "_cached_en_prompts"):
            self._cached_en_prompts = {}
        self._cached_en_prompts[work.get("id", "")] = self.generate_english_image_prompt(
            work=work,
            story_body=plot_blueprint,
            episode_title=work.get("title", "放課後サイエンス・キャンパス"),
        )

        story_body, episode_title = self.generate_prose_with_writer(
            work=work,
            plot_blueprint=plot_blueprint,
            verified_papers=verified_papers,
            progress_callback=progress_callback,
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

        active_node = self.last_used_node or self._node_name_for_host(self.ollama_host)
        logger.info(
            f"[Dual-LLM Complete] '{episode_title}' | Node: {active_node} ({self.ollama_host}) | "
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
tags: ["理系女子", "ライトノベル", "最新科学", "数学・情報・教職", "{faculty.split('・')[0]}"]
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
