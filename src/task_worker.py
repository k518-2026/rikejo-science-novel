import argparse
import json
import logging
import os
import re
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.dual_llm_generator import DualLLMStoryGenerator
from src.history_manager import HistoryManager
from src.site_builder import build_github_pages

JST = timezone(timedelta(hours=9))
logger = logging.getLogger("rikejo-task-worker")

TASKS_JSON_PATH = Path("data/tasks.json")
TASKS_MD_PATH = Path("data/TASKS.md")
PLOTS_DIR = Path("data/plots")

PROJECT_ID = "03e1e31e-29c5-4db4-b211-06e49e17b8bd"
PROJECT_NAME = "rikejo-science-novel"
PROJECT_TITLE = "放課後サイエンス・キャンパス"

DEFAULT_ROLES_CONFIG = {
    "rtx5060lp": {
        "node": "rtx5060lp",
        "role": "primary_writer",
        "host": "http://rtx5060lp:11434",
        "fallback_host": "http://192.168.128.62:11434",
        "local_host": "http://localhost:11434",
        "director_model": "qwen3.5:9b",
        "writer_model": "shosetsu",
        "daily_quota": 3,
        "description": "プライマリ小説執筆担当（偶数話メイン / 繊細で叙情的な青春科学ノベル調・単体起動時も自律実行＆セカンダリ停止時は自動代替）",
    },
    "sff7020": {
        "node": "sff7020",
        "role": "secondary_writer",
        "host": "http://sff7020:1234",
        "fallback_host": "http://192.168.128.16:1234",
        "local_host": "http://localhost:1234",
        "model": "google/gemma-4-26b-a4b-qat",
        "daily_quota": 3,
        "description": "セカンダリ小説執筆＆校閲担当（奇数話メイン / 知的スリルと煽りの効いたドラマチック調・単体起動時も自律実行＆プライマリ停止時は自動代替）",
    },
    "kenomac-mini": {
        "node": "kenomac-mini",
        "role": "illustrator",
        "host": "http://kenomac-mini:7860",
        "fallback_host": "http://192.168.128.59:7860",
        "local_host": "http://localhost:7860",
        "ollama_host": "http://kenomac-mini:11434",
        "fallback_ollama_host": "http://192.168.128.59:11434",
        "model": "flux_2_klein_base_4b_i8x.ckpt",
        "prompt_model": "gemma4:12b",
        "daily_quota": 5,
        "description": "FLUX.2 挿絵生成（content/*.png）＆ GitHub Pages（docs/）ビルド更新（単体起動時もGitHubから未挿絵原稿を取得して自律生成）",
    },
}


def setup_logging(verbose: bool = False):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def git_pull_latest() -> bool:
    try:
        logger.info("GitHubから最新のタスクキューと原稿を同期中 (git pull --rebase --autostash origin main)...")
        subprocess.run(["git", "pull", "--rebase", "--autostash", "origin", "main"], check=False)
        return True
    except Exception as e:
        logger.warning(f"git pull warning: {e}")
        return False


def git_commit_and_push(message: str, paths: Optional[List[str]] = None) -> bool:
    target_paths = paths or ["README.md", "content/", "data/", "docs/"]
    try:
        for p in target_paths:
            if Path(p).exists():
                subprocess.run(["git", "add", p], check=False)
        diff_res = subprocess.run(["git", "diff", "--staged", "--quiet"])
        if diff_res.returncode == 0:
            logger.info("コミット対象の変更はありません。")
            return True
        subprocess.run(["git", "commit", "-m", message], check=True)
        subprocess.run(["git", "pull", "--rebase", "--autostash", "origin", "main"], check=False)
        subprocess.run(["git", "push", "origin", "HEAD:main"], check=True)
        logger.info(f"GitHubへの自動プッシュ完了: {message}")
        return True
    except Exception as e:
        logger.error(f"Git push error: {e}")
        return False


def probe_http_json(url: str, timeout: int = 3) -> Optional[Dict[str, Any]]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AntigravityTaskWorker/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as res:
            if res.getcode() == 200:
                return json.loads(res.read().decode("utf-8", errors="ignore"))
    except Exception:
        return None
    return None


def resolve_reachable_url(candidates: List[str], probe_path: str, timeout: int = 3) -> Optional[str]:
    for base in candidates:
        if not base:
            continue
        clean_base = base.rstrip("/")
        if probe_http_json(f"{clean_base}{probe_path}", timeout=timeout) is not None:
            return clean_base
    return None


def default_assigned_writer_for_episode(ep_num: int) -> str:
    """
    Alternates episode writing assignment between Primary (rtx5060lp) and Secondary (sff7020):
    - Odd episodes (#29, #31, #33...): 'sff7020' (LM Studio Gemma 4 26B — dramatic & provocative hook style)
    - Even episodes (#30, #32, #34...): 'rtx5060lp' (Ollama Qwen3.5 9B x shosetsu — delicate literary style)
    """
    return "sff7020" if (ep_num % 2 == 1) else "rtx5060lp"


def sync_tasks_manifest(history_mgr: HistoryManager, default_queued_count: int = 5) -> Dict[str, Any]:
    existing_data: Dict[str, Any] = {}
    if TASKS_JSON_PATH.exists():
        try:
            existing_data = json.loads(TASKS_JSON_PATH.read_text(encoding="utf-8"))
        except Exception:
            existing_data = {}

    existing_tasks_map: Dict[str, Dict[str, Any]] = {
        t["id"]: t for t in existing_data.get("tasks", []) if isinstance(t, dict) and "id" in t
    }
    roles_cfg = DEFAULT_ROLES_CONFIG.copy()

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    synced_tasks: List[Dict[str, Any]] = []

    for idx, work in enumerate(history_mgr.catalog, start=1):
        wid = work["id"]
        ep_num = int(work.get("episode_num", idx))
        prev = existing_tasks_map.get(wid, {})
        stock_md = history_mgr.find_stock_file_for_work(wid)
        stock_png = stock_md.with_suffix(".png") if stock_md else None
        plot_path = PLOTS_DIR / f"{wid}.md"

        md_rel = str(stock_md).replace("\\", "/") if stock_md and stock_md.exists() else None
        png_rel = str(stock_png).replace("\\", "/") if stock_png and stock_png.exists() else None
        plot_rel = str(plot_path).replace("\\", "/") if plot_path.exists() else None

        prev_status = prev.get("status", "pending")
        if md_rel and png_rel:
            status = "completed"
        elif md_rel and not png_rel:
            status = "pending_illustration"
        elif prev_status == "queued":
            status = "queued"
        elif plot_rel:
            status = "plot_ready"
        else:
            status = "pending"

        inferred_date = None
        if stock_md and re.match(r"^\d{4}-\d{2}-\d{2}_", stock_md.name):
            inferred_date = stock_md.name[:10]

        assigned_writer = prev.get("assigned_writer") or default_assigned_writer_for_episode(ep_num)

        task_entry = {
            "id": wid,
            "episode_num": ep_num,
            "title": work.get("title", ""),
            "faculty": work.get("faculty", ""),
            "theme": work.get("theme", ""),
            "status": status,
            "assigned_writer": assigned_writer,
            "queued_at": prev.get("queued_at"),
            "plot_file": plot_rel,
            "plot_by": prev.get("plot_by") or ("sff7020" if plot_rel else None),
            "plot_at": prev.get("plot_at"),
            "md_file": md_rel,
            "written_by": prev.get("written_by") or ("rtx5060lp" if md_rel else None),
            "written_at": prev.get("written_at") or inferred_date,
            "reviewed_by": prev.get("reviewed_by"),
            "reviewed_at": prev.get("reviewed_at"),
            "png_file": png_rel,
            "illustrated_by": prev.get("illustrated_by") or ("kenomac-mini" if png_rel else None),
            "illustrated_at": prev.get("illustrated_at") or (inferred_date if png_rel else None),
        }
        synced_tasks.append(task_entry)

    # Self-replenish queue if all queued items have been consumed
    queued_now = [t for t in synced_tasks if t["status"] == "queued"]
    if not queued_now and default_queued_count > 0:
        now_iso = datetime.now(JST).isoformat()
        seeded = 0
        for t in synced_tasks:
            if t["status"] in ("plot_ready", "pending"):
                t["status"] = "queued"
                t["queued_at"] = t.get("queued_at") or now_iso
                seeded += 1
                if seeded >= default_queued_count:
                    break

    manifest = {
        "project_id": PROJECT_ID,
        "project_name": PROJECT_NAME,
        "project_title": PROJECT_TITLE,
        "updated_at": datetime.now(JST).isoformat(),
        "roles": roles_cfg,
        "tasks": synced_tasks,
    }

    TASKS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    TASKS_JSON_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_tasks_markdown(manifest)
    return manifest


def enqueue_tasks_on_github(
    manifest: Dict[str, Any],
    history_mgr: HistoryManager,
    enqueue_count: int = 5,
    push_to_git: bool = True,
) -> int:
    tasks = manifest.get("tasks", [])
    currently_queued = [t for t in tasks if t["status"] == "queued"]
    needed_to_queue = max(0, enqueue_count - len(currently_queued))
    if needed_to_queue == 0:
        logger.info(f"[Task Queue] 既に {len(currently_queued)} 件のタスクが GitHub キュー (`queued`) に蓄積されています。")
        return len(currently_queued)

    now_iso = datetime.now(JST).isoformat()
    added = 0
    for t in tasks:
        if t["status"] in ("plot_ready", "pending"):
            t["status"] = "queued"
            t["queued_at"] = now_iso
            t["assigned_writer"] = default_assigned_writer_for_episode(int(t.get("episode_num", 0)))
            added += 1
            if added >= needed_to_queue:
                break

    manifest["updated_at"] = now_iso
    TASKS_JSON_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_tasks_markdown(manifest)
    logger.info(f"[Task Queue] 新たに {added} 件のタスクを GitHub 実行待ちキュー (`queued`) に追加しました（合計 {len(currently_queued) + added} 件）。")
    if push_to_git and added > 0:
        git_commit_and_push(
            f"chore(queue): Enqueue {added} episode task(s) on GitHub for autonomous PC execution",
            paths=["data/tasks.json", "data/TASKS.md"],
        )
    return len(currently_queued) + added


def write_tasks_markdown(manifest: Dict[str, Any]) -> None:
    tasks = manifest.get("tasks", [])
    completed = [t for t in tasks if t["status"] == "completed"]
    pending_ill = [t for t in tasks if t["status"] == "pending_illustration"]
    queued = [t for t in tasks if t["status"] == "queued"]
    plot_ready = [t for t in tasks if t["status"] == "plot_ready"]
    pending = [t for t in tasks if t["status"] == "pending"]

    lines = [
        f"# 📋 分散ローカルLLM 自動作業リスト (`{PROJECT_NAME}`)",
        "",
        f"- **会話ID**: `{PROJECT_ID}`",
        f"- **最終同期日時 (JST)**: `{manifest.get('updated_at', '')[:19]}`",
        f"- **進捗サマリー**: 全 **{len(tasks)}** 話 （完了: **{len(completed)}** / 挿絵待ち: **{len(pending_ill)}** / **PC起動時実行キュー(`queued`)**: **{len(queued)}** / プロット作成済: **{len(plot_ready)}** / 未着手待機: **{len(pending)}**）",
        "",
        "## 🖥️ 各ローカルLLMサーバーの役割分担（メインPC電源オフ時も各ノード単体で自律実行）",
        "",
        "| 優先順 / 担当 | サーバー名 (IP) | 使用モデル / API | 担当エピソード・単体自律動作 |",
        "|:---|:---|:---|:---|",
        "| **プライマリ執筆 (`rtx5060lp`)** | `http://rtx5060lp:11434` (`192.168.128.62`) | Ollama `qwen3.5:9b` × `shosetsu` (`think: false`) | **偶数話メイン**（繊細で叙情的な青春科学ノベル調・単体起動時にGitHubから偶数話または停止中ノード分を取得して執筆） |",
        "| **セカンダリ執筆 (`sff7020`)** | `http://sff7020:1234` (`192.168.128.16`) | LM Studio `google/gemma-4-26b-a4b-qat` (`reasoning_effort: none`) | **奇数話メイン**（知的スリルと煽りの効いたドラマチック展開・単体起動時にGitHubから奇数話または停止中ノード分を取得して執筆） |",
        "| **挿絵＆Web公開 (`kenomac-mini`)** | `http://kenomac-mini:7860` (`192.168.128.59`) | Draw Things `FLUX.2 [klein] 4B` + Ollama `gemma4:12b` | **全話の挿絵生成**（単体起動時にGitHub上の `pending_illustration` 原稿を検出して挿絵生成＆GitHub Pages更新） |",
        "",
        "## 🚀 GitHubから読み取って実行するタスクキュー (`queued` / 未完了タスク一覧)",
        "",
        "| 話数 | タスクID | タイトル | 学部・研究室 | 状態 (`status`) | 次回担当ライター (交互割当) |",
        "|:---:|:---|:---|:---|:---:|:---|",
    ]

    active_queue = pending_ill + queued + plot_ready + pending
    if not active_queue:
        lines.append("| - | - | （全エピソード完了済み・次回起動時に新規テーマ自動生成） | - | Completed | `sff7020` / `rtx5060lp` |")
    else:
        for t in active_queue[:15]:
            st = t["status"]
            writer_node = t.get("assigned_writer") or default_assigned_writer_for_episode(int(t.get("episode_num", 0)))
            if st == "pending_illustration":
                next_pc = "🎨 `kenomac-mini` (挿絵生成待ち)"
            elif writer_node == "sff7020":
                next_pc = "🔥 **セカンダリ `sff7020`** (`gemma-4-26b` ドラマチック調)"
            else:
                next_pc = "✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調)"
            lines.append(
                f"| #{t.get('episode_num', 0):02d} | `{t['id']}` | {t['title']} | {t.get('faculty', '')} | `{st}` | {next_pc} |"
            )

    lines.extend([
        "",
        "## ✅ 完了済みエピソード（最新10件）",
        "",
        "| 話数 | タスクID | タイトル | 執筆担当ノード | 執筆日 | 校閲 (`sff7020`) | 挿絵 (`kenomac-mini`) |",
        "|:---:|:---|:---|:---:|:---:|:---:|:---:|",
    ])
    for t in list(reversed(completed))[:10]:
        w_by = f"`{t.get('written_by') or 'rtx5060lp'}`"
        w_date = str(t.get("written_at") or "-")[:10]
        r_mark = f"✓ ({t.get('reviewed_by')})" if t.get("reviewed_by") else "未校閲"
        i_mark = f"🎨 ({t.get('illustrated_by')})" if t.get("png_file") else "-"
        lines.append(
            f"| #{t.get('episode_num', 0):02d} | `{t['id']}` | {t['title']} | {w_by} | {w_date} | {r_mark} | {i_mark} |"
        )

    TASKS_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_node_specific_writer(
    node_name: str,
    manifest: Dict[str, Any],
    history_mgr: HistoryManager,
    max_tasks: Optional[int] = None,
    push_to_git: bool = True,
) -> int:
    """
    Autonomous execution for an individual writer machine (`rtx5060lp` or `sff7020`)
    running on its own while the main PC (`MINISFORUM64GB`) is powered off:
    - Pulls latest `data/tasks.json` from GitHub before each episode to prevent conflicts.
    - Selects `queued` tasks assigned to `node_name` (`rtx5060lp` = even episodes, `sff7020` = odd episodes).
    - If the peer writer node is offline on LAN, also takes over the peer's queued tasks as failover.
    - If `kenomac-mini:7860` is online on LAN right now, generates `.png` illustration immediately;
      otherwise marks `status = "pending_illustration"` and pushes `.md` to GitHub so `kenomac-mini`
      will illustrate it when `kenomac-mini` boots up.
    """
    role_cfg = manifest["roles"].get(node_name, DEFAULT_ROLES_CONFIG[node_name])
    quota = max_tasks if (max_tasks is not None and max_tasks > 0) else int(role_cfg.get("daily_quota", 3))

    if node_name == "rtx5060lp":
        local_llm_url = resolve_reachable_url(
            ["http://localhost:11434", "http://127.0.0.1:11434", "http://rtx5060lp:11434", "http://192.168.128.62:11434"],
            "/api/tags",
        )
        peer_online = resolve_reachable_url(
            ["http://sff7020:1234", "http://192.168.128.16:1234"],
            "/v1/models",
        ) is not None
    else:
        local_llm_url = resolve_reachable_url(
            ["http://localhost:1234", "http://127.0.0.1:1234", "http://sff7020:1234", "http://192.168.128.16:1234"],
            "/v1/models",
        )
        peer_online = resolve_reachable_url(
            ["http://rtx5060lp:11434", "http://192.168.128.62:11434"],
            "/api/tags",
        ) is not None

    if not local_llm_url:
        logger.warning(f"[{node_name}] ローカルLLMサーバーが起動していないためスキップします。")
        return 0

    dt_host = resolve_reachable_url(
        ["http://kenomac-mini:7860", "http://192.168.128.59:7860", "http://localhost:7860"],
        "/sdapi/v1/options",
    )

    generator = DualLLMStoryGenerator(
        ollama_host=local_llm_url,
        director_model="qwen3.5:9b",
        writer_model="shosetsu",
        draw_things_host=dt_host or "http://kenomac-mini:7860",
        alternate_nodes=False,
    )

    # Filter queued tasks: prioritize tasks assigned to this node; if peer is offline, also take peer's tasks
    queued_tasks = [t for t in manifest.get("tasks", []) if t.get("status") == "queued"]
    own_tasks = [
        t for t in queued_tasks
        if (t.get("assigned_writer") or default_assigned_writer_for_episode(int(t.get("episode_num", 0)))) == node_name
    ]
    peer_tasks = [t for t in queued_tasks if t not in own_tasks]

    if peer_online:
        targets = own_tasks[:quota]
        logger.info(
            f"[{node_name} 自律実行] 相方ノードがオンラインのため、{node_name} 担当の {len(targets)} 話を執筆します。"
        )
    else:
        targets = (own_tasks + peer_tasks)[:quota]
        logger.info(
            f"[{node_name} 自律実行] 相方ノードがオフラインのため、フェイルオーバー込みで {len(targets)} 話を執筆します。"
        )

    if not targets:
        logger.info(f"[{node_name} 自律実行] 現在 {node_name} が実行すべき `queued` タスクはありません。")
        return 0

    catalog_map = {w["id"]: w for w in history_mgr.catalog}
    today_str = datetime.now(JST).strftime("%Y-%m-%d")
    written_count = 0

    for idx, task in enumerate(targets, start=1):
        # Pull latest from GitHub right before starting each episode to avoid duplicate work across nodes
        if push_to_git:
            git_pull_latest()
            history_mgr.catalog = history_mgr._load_json(history_mgr.catalog_path)
            manifest = sync_tasks_manifest(history_mgr)
            refreshed = next((t for t in manifest["tasks"] if t["id"] == task["id"]), None)
            if refreshed and refreshed.get("status") in ("completed", "pending_illustration"):
                logger.info(f"[{node_name}] {task['id']} は既に他ノードで執筆完了しているためスキップします。")
                continue

        work = catalog_map.get(task["id"])
        if not work:
            continue

        custom_plot = None
        if task.get("plot_file") and Path(task["plot_file"]).exists():
            custom_plot = Path(task["plot_file"]).read_text(encoding="utf-8", errors="ignore")

        logger.info(
            f"\n=== [{node_name} 自律執筆 {idx}/{len(targets)}] #{task.get('episode_num', 0):02d} "
            f"[{work['id']}] {work['title']} ==="
        )
        try:
            full_md, ep_title, _, _ = generator.generate_complete_episode(
                work=work,
                custom_plot_override=custom_plot,
                preferred_node=node_name,
            )
            safe_id = work["id"].replace("-", "_")
            out_path = Path(f"content/{today_str}_{safe_id}.md")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(full_md, encoding="utf-8")

            target_in_manifest = next((t for t in manifest["tasks"] if t["id"] == work["id"]), task)
            target_in_manifest["md_file"] = str(out_path).replace("\\", "/")
            target_in_manifest["written_by"] = node_name
            target_in_manifest["written_at"] = datetime.now(JST).isoformat()
            target_in_manifest["status"] = "pending_illustration"

            # If kenomac-mini:7860 is online on LAN right now, generate illustration immediately
            dt_now = resolve_reachable_url(
                ["http://kenomac-mini:7860", "http://192.168.128.59:7860", "http://localhost:7860"],
                "/sdapi/v1/options",
            )
            if dt_now:
                generator.draw_things_host = dt_now
                img_path = out_path.with_suffix(".png")
                saved_img, _ = generator.generate_illustration(
                    work=work,
                    output_image_path=img_path,
                    story_body=full_md,
                    episode_title=ep_title,
                )
                if saved_img:
                    target_in_manifest["png_file"] = str(saved_img).replace("\\", "/")
                    target_in_manifest["illustrated_by"] = "kenomac-mini"
                    target_in_manifest["illustrated_at"] = datetime.now(JST).isoformat()
                    target_in_manifest["status"] = "completed"
            else:
                logger.info(
                    f"[{node_name}] kenomac-mini:7860 がオフラインのため、小説原稿 ({out_path.name}) を "
                    f"`pending_illustration` として GitHub に保存します（kenomac-mini 起動時に挿絵自動生成）。"
                )

            written_count += 1
            manifest["updated_at"] = datetime.now(JST).isoformat()
            TASKS_JSON_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            write_tasks_markdown(manifest)
            build_github_pages(history_mgr)

            if push_to_git:
                git_commit_and_push(
                    f"feat({node_name}): Write queued episode '{work['id']}' autonomously on {node_name}"
                )
        except Exception as e:
            logger.error(f"[{node_name}] '{work['id']}' の自律執筆中にエラーが発生しました: {e}")
            continue

    return written_count


def run_alternating_startup_queue(
    manifest: Dict[str, Any],
    history_mgr: HistoryManager,
    max_tasks: Optional[int] = None,
    push_to_git: bool = True,
) -> int:
    """
    Executes tasks accumulated on GitHub (`status == 'queued'` or `'pending_illustration'`):
    1. Completes any missing illustrations first via `kenomac-mini:7860`.
    2. Processes `queued` episodes from `data/tasks.json` by alternating between:
       - `sff7020` (`http://sff7020:1234`, LM Studio `google/gemma-4-26b-a4b-qat`) for odd episodes
       - `rtx5060lp` (`http://rtx5060lp:11434`, Ollama `qwen3.5:9b` x `shosetsu`) for even episodes
       with automatic failover to the other server if the assigned one is powered off.
    3. Generates the FLUX.2 illustration for each newly written episode and pushes to GitHub.
    """
    run_illustrator_role(manifest, history_mgr, quota_override=max_tasks or 5, push_to_git=push_to_git)
    manifest = sync_tasks_manifest(history_mgr)

    queued_tasks = [t for t in manifest["tasks"] if t["status"] == "queued"]
    if not queued_tasks:
        logger.info("[Startup Queue] GitHub 上の実行待ちタスク (`queued`) は現在 0 件です。")
        return 0

    limit = max_tasks if (max_tasks is not None and max_tasks > 0) else len(queued_tasks)
    targets = queued_tasks[:limit]

    dt_host = resolve_reachable_url(
        [
            os.getenv("DRAW_THINGS_HOST", ""),
            "http://kenomac-mini:7860",
            "http://192.168.128.59:7860",
            "http://localhost:7860",
        ],
        "/sdapi/v1/options",
    ) or "http://kenomac-mini:7860"

    generator = DualLLMStoryGenerator(
        ollama_host="http://rtx5060lp:11434",
        director_model="qwen3.5:9b",
        writer_model="shosetsu",
        draw_things_host=dt_host,
        alternate_nodes=True,
    )

    conn = generator.check_connection()
    if not conn.get("online"):
        logger.warning(
            "[Startup Queue] プライマリ (rtx5060lp:11434) もセカンダリ (sff7020:1234) もオフラインのため、"
            "GitHub キューの実行を次回起動時まで保留します。"
        )
        return 0

    catalog_map = {w["id"]: w for w in history_mgr.catalog}
    today_str = datetime.now(JST).strftime("%Y-%m-%d")
    completed_count = 0

    logger.info(
        f"[Startup Queue] GitHub から読み取った実行待ちタスク {len(targets)} 件を "
        f"rtx5060lp ⇄ sff7020 交互担当モードで実行開始します..."
    )

    for idx, task in enumerate(targets, start=1):
        if push_to_git:
            git_pull_latest()
            manifest = sync_tasks_manifest(history_mgr)
            refreshed = next((t for t in manifest["tasks"] if t["id"] == task["id"]), None)
            if refreshed and refreshed.get("status") in ("completed", "pending_illustration"):
                logger.info(f"[Startup Queue] {task['id']} は既に完了しているためスキップします。")
                continue

        work = catalog_map.get(task["id"])
        if not work:
            continue

        preferred_writer = task.get("assigned_writer") or default_assigned_writer_for_episode(
            int(task.get("episode_num", idx))
        )
        custom_plot = None
        if task.get("plot_file") and Path(task["plot_file"]).exists():
            custom_plot = Path(task["plot_file"]).read_text(encoding="utf-8", errors="ignore")

        logger.info(
            f"\n=== [GitHub Queue {idx}/{len(targets)}] #{task.get('episode_num', 0):02d} [{work['id']}] "
            f"{work['title']} (予定担当: {preferred_writer}) ==="
        )
        try:
            full_md, ep_title, _, _ = generator.generate_complete_episode(
                work=work,
                custom_plot_override=custom_plot,
                preferred_node=preferred_writer,
            )
            actual_writer = generator.last_used_node or preferred_writer
            safe_id = work["id"].replace("-", "_")
            out_path = Path(f"content/{today_str}_{safe_id}.md")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(full_md, encoding="utf-8")

            target_in_manifest = next((t for t in manifest["tasks"] if t["id"] == work["id"]), task)
            target_in_manifest["md_file"] = str(out_path).replace("\\", "/")
            target_in_manifest["written_by"] = actual_writer
            target_in_manifest["written_at"] = datetime.now(JST).isoformat()
            target_in_manifest["status"] = "pending_illustration"

            img_path = out_path.with_suffix(".png")
            saved_img, _ = generator.generate_illustration(
                work=work,
                output_image_path=img_path,
                story_body=full_md,
                episode_title=ep_title,
            )
            if saved_img:
                target_in_manifest["png_file"] = str(saved_img).replace("\\", "/")
                target_in_manifest["illustrated_by"] = "kenomac-mini"
                target_in_manifest["illustrated_at"] = datetime.now(JST).isoformat()
                target_in_manifest["status"] = "completed"

            completed_count += 1
            manifest["updated_at"] = datetime.now(JST).isoformat()
            TASKS_JSON_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            write_tasks_markdown(manifest)
            build_github_pages(history_mgr)

            if push_to_git:
                git_commit_and_push(
                    f"feat({actual_writer}): Complete queued episode '{work['id']}' via {actual_writer} & update GitHub Pages"
                )
        except Exception as e:
            logger.error(f"[Startup Queue] '{work['id']}' の生成中にエラーが発生しました: {e}")
            continue

    return completed_count


def run_director_role(
    manifest: Dict[str, Any],
    history_mgr: HistoryManager,
    quota_override: Optional[int] = None,
    push_to_git: bool = True,
) -> int:
    role_cfg = manifest["roles"]["sff7020"]
    quota = quota_override if quota_override is not None else int(role_cfg.get("daily_quota", 3))
    lm_host = resolve_reachable_url(
        [
            os.getenv("LM_STUDIO_HOST", ""),
            "http://localhost:1234",
            role_cfg.get("host", "http://sff7020:1234"),
            role_cfg.get("fallback_host", "http://192.168.128.16:1234"),
        ],
        "/v1/models",
    )
    if not lm_host:
        logger.info("[sff7020 / director] LM Studio サーバーがオフラインのためスキップします。")
        return 0

    today_str = datetime.now(JST).strftime("%Y-%m-%d")
    now_iso = datetime.now(JST).isoformat()
    actions_done = 0

    unreviewed = [
        t for t in reversed(manifest["tasks"])
        if t.get("md_file") and not t.get("reviewed_by") and Path(t["md_file"]).exists()
    ]
    reviewed_today = sum(
        1 for t in manifest["tasks"]
        if str(t.get("reviewed_at") or "").startswith(today_str)
    )
    review_needed = max(0, quota - reviewed_today)

    for task in unreviewed[:review_needed]:
        md_path = Path(task["md_file"])
        raw_md = md_path.read_text(encoding="utf-8", errors="ignore")
        cleaned_md = DualLLMStoryGenerator._normalize_japanese_typos(raw_md)
        if cleaned_md != raw_md:
            md_path.write_text(cleaned_md, encoding="utf-8")
            logger.info(f"[sff7020 / director] 原稿の表記揺れ・簡体字を自動補正しました: {md_path.name}")
        task["reviewed_by"] = "sff7020"
        task["reviewed_at"] = now_iso
        actions_done += 1
        logger.info(f"[sff7020 / director] 校閲完了: [{task['id']}] {task['title']}")

    if actions_done > 0:
        manifest["updated_at"] = datetime.now(JST).isoformat()
        TASKS_JSON_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        write_tasks_markdown(manifest)
        build_github_pages(history_mgr)
        if push_to_git:
            git_commit_and_push(f"feat(sff7020): Review {actions_done} episode(s) via sff7020 LM Studio")

    return actions_done


def run_illustrator_role(
    manifest: Dict[str, Any],
    history_mgr: HistoryManager,
    quota_override: Optional[int] = None,
    push_to_git: bool = True,
) -> int:
    role_cfg = manifest["roles"]["kenomac-mini"]
    quota = quota_override if quota_override is not None else int(role_cfg.get("daily_quota", 5))
    dt_host = resolve_reachable_url(
        [
            os.getenv("DRAW_THINGS_HOST", ""),
            "http://localhost:7860",
            "http://127.0.0.1:7860",
            role_cfg.get("host", "http://kenomac-mini:7860"),
            role_cfg.get("fallback_host", "http://192.168.128.59:7860"),
        ],
        "/sdapi/v1/options",
    )
    if not dt_host:
        logger.info("[kenomac-mini / illustrator] Draw Things サーバー (kenomac-mini:7860) がオフラインのためスキップします。")
        return 0

    ollama_host = resolve_reachable_url(
        [
            "http://localhost:11434",
            "http://127.0.0.1:11434",
            role_cfg.get("ollama_host", "http://kenomac-mini:11434"),
            role_cfg.get("fallback_ollama_host", "http://192.168.128.59:11434"),
            "http://rtx5060lp:11434",
            "http://192.168.128.62:11434",
            "http://sff7020:1234",
            "http://192.168.128.16:1234",
        ],
        "/api/tags",
    ) or "http://rtx5060lp:11434"

    generator = DualLLMStoryGenerator(
        ollama_host=ollama_host,
        draw_things_host=dt_host,
    )

    pending_ill = [
        t for t in manifest["tasks"]
        if t.get("md_file") and Path(t["md_file"]).exists() and not Path(t["md_file"]).with_suffix(".png").exists()
    ]
    if not pending_ill:
        logger.info("[kenomac-mini / illustrator] 未挿絵のエピソードはありません。")
        return 0

    catalog_map = {w["id"]: w for w in history_mgr.catalog}
    illustrated_count = 0

    for task in pending_ill[:quota]:
        if push_to_git:
            git_pull_latest()
        work = catalog_map.get(task["id"])
        if not work:
            continue
        md_path = Path(task["md_file"])
        img_path = md_path.with_suffix(".png")
        if img_path.exists():
            continue
        md_text = md_path.read_text(encoding="utf-8", errors="ignore")
        logger.info(f"[kenomac-mini / illustrator] FLUX.2 挿絵生成中 ({illustrated_count + 1}/{min(quota, len(pending_ill))}): {img_path.name}")
        saved_img, _ = generator.generate_illustration(
            work=work,
            output_image_path=img_path,
            story_body=md_text,
            episode_title=work.get("title", ""),
        )
        if saved_img:
            task["png_file"] = str(saved_img).replace("\\", "/")
            task["illustrated_by"] = "kenomac-mini"
            task["illustrated_at"] = datetime.now(JST).isoformat()
            task["status"] = "completed"
            illustrated_count += 1

            manifest["updated_at"] = datetime.now(JST).isoformat()
            TASKS_JSON_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            write_tasks_markdown(manifest)
            build_github_pages(history_mgr)
            if push_to_git:
                git_commit_and_push(f"feat(kenomac-mini): Add FLUX.2 illustration for '{work['id']}' & rebuild GitHub Pages")

    return illustrated_count


def detect_local_role() -> str:
    """
    Detects which PC this worker is running on by hostname so that each PC can operate
    autonomously even when the main PC (`MINISFORUM64GB`) is powered off:
    - `rtx5060lp` -> `"rtx5060lp"` (Primary Writer node)
    - `sff7020` -> `"sff7020"` (Secondary Writer + Director node)
    - `kenomac-mini` / `mac-mini` -> `"kenomac-mini"` (FLUX.2 Illustrator + GitHub Pages publisher node)
    - `MINISFORUM64GB` or others -> `"startup-queue"` (Orchestrator across online LAN servers)
    """
    hostname = socket.gethostname().lower()
    if "rtx5060lp" in hostname:
        return "rtx5060lp"
    if "sff7020" in hostname:
        return "sff7020"
    if "kenomac-mini" in hostname or "mac-mini" in hostname or "kenomac" in hostname:
        return "kenomac-mini"
    return "startup-queue"


def main():
    parser = argparse.ArgumentParser(
        description="GitHub-Synced Autonomous Multi-Node Local LLM Worker (rtx5060lp / sff7020 / kenomac-mini / MINISFORUM64GB)"
    )
    parser.add_argument(
        "--role",
        choices=[
            "auto",
            "startup-queue",
            "lan-dispatch",
            "writer",
            "rtx5060lp",
            "illustrator",
            "kenomac-mini",
            "director",
            "sff7020",
            "enqueue",
            "sync",
        ],
        default="auto",
        help="Worker role to run (default: auto-detect hostname and run autonomously)",
    )
    parser.add_argument("--enqueue", type=int, default=0, help="Enqueue N pending tasks into GitHub task queue (`status: queued`)")
    parser.add_argument("--quota", type=int, default=None, help="Maximum number of tasks to execute in this run")
    parser.add_argument("--no-push", action="store_true", help="Do not git commit/push changes")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    setup_logging(args.verbose)
    push_to_git = not args.no_push

    if push_to_git:
        git_pull_latest()

    history_mgr = HistoryManager()
    manifest = sync_tasks_manifest(history_mgr)

    if args.enqueue > 0 or args.role == "enqueue":
        count_to_queue = args.enqueue if args.enqueue > 0 else (args.quota or 5)
        enqueue_tasks_on_github(manifest, history_mgr, enqueue_count=count_to_queue, push_to_git=push_to_git)
        return

    role = args.role
    if role == "auto":
        role = detect_local_role()
        logger.info(f"ホスト名 '{socket.gethostname()}' から自動判定された自律実行モード: {role}")

    if role == "sync":
        if push_to_git:
            git_commit_and_push("chore(tasks): Sync distributed task queue manifest (data/tasks.json & data/TASKS.md)")
        return

    if role in ("rtx5060lp", "writer"):
        # Autonomous execution on rtx5060lp even when MINISFORUM64GB is powered off
        run_node_specific_writer("rtx5060lp", manifest, history_mgr, max_tasks=args.quota, push_to_git=push_to_git)
    elif role in ("sff7020", "director"):
        # Autonomous execution on sff7020 even when MINISFORUM64GB is powered off
        run_node_specific_writer("sff7020", manifest, history_mgr, max_tasks=args.quota, push_to_git=push_to_git)
        manifest = sync_tasks_manifest(history_mgr)
        run_director_role(manifest, history_mgr, quota_override=args.quota, push_to_git=push_to_git)
    elif role in ("kenomac-mini", "illustrator"):
        # Autonomous execution on kenomac-mini even when MINISFORUM64GB is powered off
        run_illustrator_role(manifest, history_mgr, quota_override=args.quota, push_to_git=push_to_git)
    elif role in ("startup-queue", "lan-dispatch"):
        run_alternating_startup_queue(manifest, history_mgr, max_tasks=args.quota, push_to_git=push_to_git)
        manifest = sync_tasks_manifest(history_mgr)
        run_director_role(manifest, history_mgr, quota_override=2, push_to_git=push_to_git)


if __name__ == "__main__":
    main()
