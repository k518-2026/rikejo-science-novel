import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

HISTORY_FILE = Path("data/history.json")
CATALOG_FILE = Path("data/science_catalog.json")
TABLE_FILE = Path("data/POSTED_STORIES.md")

JST = timezone(timedelta(hours=9))


class HistoryManager:
    def __init__(self, history_path: Path = HISTORY_FILE, catalog_path: Path = CATALOG_FILE):
        self.history_path = history_path
        self.catalog_path = catalog_path
        self.history = self._load_json(self.history_path)
        self.catalog = self._load_json(self.catalog_path)

    def _load_json(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return []

    def get_posted_ids(self) -> set:
        return {item["work_id"] for item in self.history if "work_id" in item}

    def find_stock_file_for_work(self, work_id: str, content_dir: Path = Path("content")) -> Optional[Path]:
        if not work_id or not content_dir.exists():
            return None
        safe_id = work_id.replace("-", "_")
        for f in sorted(content_dir.glob("*.md"), reverse=True):
            if (
                f.name.endswith(f"_{safe_id}.md")
                or f.name == f"{safe_id}.md"
                or f.name.endswith(f"_{work_id}.md")
                or f.name == f"{work_id}.md"
            ):
                return f
        return None

    def count_unposted_stock(self, content_dir: Path = Path("content")) -> int:
        posted_ids = self.get_posted_ids()
        count = 0
        for w in self.catalog:
            wid = w["id"]
            if wid in posted_ids:
                continue
            if self.find_stock_file_for_work(wid, content_dir=content_dir) is not None:
                count += 1
        return count

    def count_ungenerated_works(self, content_dir: Path = Path("content")) -> int:
        count = 0
        for w in self.catalog:
            if self.find_stock_file_for_work(w["id"], content_dir=content_dir) is None:
                count += 1
        return count

    def append_catalog_works(self, new_works: List[Dict[str, Any]]):
        if not new_works:
            return
        existing_ids = {w["id"] for w in self.catalog}
        added = False
        for nw in new_works:
            if nw.get("id") and nw["id"] not in existing_ids:
                self.catalog.append(nw)
                existing_ids.add(nw["id"])
                added = True
        if added:
            self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.catalog_path, "w", encoding="utf-8") as f:
                json.dump(self.catalog, f, ensure_ascii=False, indent=2)

    def select_unstocked_works(self, count: int = 3, content_dir: Path = Path("content")) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        for w in self.catalog:
            wid = w["id"]
            if self.find_stock_file_for_work(wid, content_dir=content_dir) is not None:
                continue
            candidates.append(w)
            if len(candidates) >= count:
                break
        return candidates

    def select_next_work(self, work_id: Optional[str] = None, force: bool = False) -> Optional[Dict[str, Any]]:
        if not self.catalog:
            return None

        if work_id:
            for item in self.catalog:
                if item["id"] == work_id:
                    return item
            raise ValueError(f"Work ID '{work_id}' not found in catalog.")

        posted_ids = self.get_posted_ids()
        unposted = [w for w in self.catalog if w["id"] not in posted_ids]
        if unposted:
            for w in unposted:
                if self.find_stock_file_for_work(w["id"]) is not None:
                    return w
            return unposted[0]

        if force and self.catalog:
            return self.catalog[0]

        return None

    def remove_from_history(self, work_id: str):
        """Removes a specific work_id from history so it can be posted cleanly as an unposted episode."""
        self.history = [item for item in self.history if item.get("work_id") != work_id]
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
        self._update_markdown_table()

    def reset_history(self, work_ids: Optional[List[str]] = None):
        if work_ids is None:
            self.history = []
        else:
            self.history = [item for item in self.history if item.get("work_id") not in work_ids]

        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
        self._update_markdown_table()

    def record_post(
        self,
        work: Dict[str, Any],
        episode_title: str,
        file_path: str,
        references: List[str],
        status: str = "published",
    ):
        now_jst = datetime.now(JST).isoformat()
        self.history = [item for item in self.history if item.get("work_id") != work["id"]]

        record = {
            "work_id": work["id"],
            "episode_num": work.get("episode_num", 1),
            "faculty": work.get("faculty", ""),
            "theme": work.get("theme", ""),
            "episode_title": episode_title,
            "posted_at": now_jst,
            "file_path": file_path,
            "status": status,
            "references": references,
        }
        self.history.append(record)

        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
        self._update_markdown_table()

    def _update_markdown_table(self):
        lines = [
            "# 投稿済み『放課後サイエンス・キャンパス』作品一覧\n",
            "Mac mini M4 ローカルLLM（構成作家 `qwen3.5:9b` × 執筆作家 `gemma4:12b`）＋ Draw Things (`FLUX.2`) と Crossref 査読論文検証により執筆された作品一覧です。\n\n",
            "| No. | 投稿日 (JST) | 作品タイトル | 大学の学部・研究室 | 科学テーマ | 主な引用論文 (DOI) | 状態 |",
            "|:---:|:---:|:---|:---|:---|:---|:---:|",
        ]

        if not self.history:
            lines.append("| - | - | （初回配信待機中） | - | - | - | Ready |")
        else:
            for i, item in enumerate(self.history, start=1):
                date_str = item.get("posted_at", "")[:10]
                raw_t = item.get("episode_title", "")
                title = raw_t.replace("【第1話】", "").replace("【第2話】", "").strip()
                faculty = item.get("faculty", "")
                theme = item.get("theme", "")
                refs = item.get("references", [])
                ref_summary = ", ".join([r.split(".")[0] for r in refs[:2]]) if refs else "Nature/Science"
                status = item.get("status", "published").capitalize()
                lines.append(f"| {i} | {date_str} | {title} | {faculty} | {theme} | {ref_summary} | {status} |")

        TABLE_FILE.parent.mkdir(parents=True, exist_ok=True)
        TABLE_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
