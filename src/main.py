import argparse
import os
import re
import sys
import subprocess
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional

from src.config import get_config
from src.history_manager import HistoryManager
from src.dual_llm_generator import DualLLMStoryGenerator
from src.post_formatter import format_post_content
from src.mail_sender import WordPressMailSender

JST = timezone(timedelta(hours=9))
logger = logging.getLogger("rikejo-novel")


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def print_stock_status(history_mgr: HistoryManager):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    posted_ids = history_mgr.get_posted_ids()
    posted_count = 0
    stocked_list = []
    unstocked_list = []

    for idx, w in enumerate(history_mgr.catalog, start=1):
        wid = w["id"]
        stock_file = history_mgr.find_stock_file_for_work(wid)
        if wid in posted_ids:
            posted_count += 1
        elif stock_file is not None:
            stocked_list.append((idx, w, stock_file))
        else:
            unstocked_list.append((idx, w))

    print("\n" + "=" * 76)
    print(" 【放課後サイエンス・キャンパス（Qwen2.5×Gemma2）ストック＆配信状況】")
    print("=" * 76)
    print(f"  ・全エピソード数         : {len(history_mgr.catalog)} 話")
    print(f"  ・WordPress配信済み      : {posted_count} 話")
    print(f"  ・書き溜め済み（配信待ち）: {len(stocked_list)} 話")
    print(f"  ・未生成（今後の執筆対象）: {len(unstocked_list)} 話")
    print("-" * 76)

    if stocked_list:
        print("\n[OK] 【書き溜め済み・WordPress配信待ちストック】")
        for idx, w, sf in stocked_list:
            print(f"  [第{w.get('episode_num', idx):02d}話] {w['title']}（{w['faculty']}） -> {sf}")
    else:
        print("\n[!] 現在、未配信の書き溜めストックは 0 話です。")

    if unstocked_list:
        print("\n[NEXT] 【未生成・次回のMac miniローカルLLM執筆対象（先頭5件）】")
        for idx, w in unstocked_list[:5]:
            print(f"  [第{w.get('episode_num', idx):02d}話] {w['id']} : {w['title']}（{w['faculty']}）")
    print("=" * 76 + "\n")


def git_sync_and_push(generated_files: List[Path]) -> bool:
    if not generated_files:
        return True
    try:
        logger.info("Syncing with remote GitHub repository (git pull --rebase origin main)...")
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=False)

        subprocess.run(["git", "add", "content/", "data/"], check=True)
        diff_res = subprocess.run(["git", "diff", "--staged", "--quiet"])
        if diff_res.returncode == 0:
            logger.info("No new changes in content/ or data/ to commit.")
            return True

        msg = f"feat(stock): Add {len(generated_files)} Rikejo science novel episode(s) via Qwen2.5xGemma2 [skip ci]"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        logger.info("Pushing to origin/main...")
        subprocess.run(["git", "push", "origin", "HEAD:main"], check=True)
        logger.info("Successfully pushed stocked episodes to GitHub!")
        return True
    except Exception as e:
        logger.error(f"Git push failed: {e}")
        return False


def extract_refs_from_markdown(md_text: str) -> List[str]:
    refs = []
    ref_sec = md_text.split("【引用・参考文献")[-1] if "【引用・参考文献" in md_text else md_text
    for m in re.finditer(r"^\d+\.\s+([^\n]+)\n\s*(\[https?://doi\.org/[^\]]+\]\([^\)]+\))", ref_sec, flags=re.MULTILINE):
        refs.append(f"{m.group(1).strip()} {m.group(2).strip()}")
    return refs


def main():
    parser = argparse.ArgumentParser(
        description="Rikejo Science Light Novel Dual-LLM Generator (Qwen 2.5 14B x Gemma 2 9B) & WordPress Mail Poster"
    )
    parser.add_argument("--file", "-f", default=None, help="Path to a specific markdown file to publish directly")
    parser.add_argument("--work-id", default=None, help="Specific episode ID from data/science_catalog.json")
    parser.add_argument("--stock-count", "-n", type=int, default=0, help="Batch-generate N episodes into content/ using Mac mini Dual-LLM")
    parser.add_argument("--push", action="store_true", help="Git commit & push after generating stock")
    parser.add_argument("--status-report", action="store_true", help="Show current stock & publication status")
    parser.add_argument("--send", action="store_true", help="Actually send the email to WordPress")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no email sent, history not updated)")
    parser.add_argument("--preview-html", action="store_true", help="Export rendered HTML to preview_output.html")
    parser.add_argument("--status", choices=["publish", "draft"], default=None, help="Override post status (publish or draft)")
    parser.add_argument("--force", action="store_true", help="Force regeneration even if stock or history exists")
    parser.add_argument("--web", action="store_true", help="Launch the interactive Web UI Studio in browser")
    parser.add_argument("--port", type=int, default=8505, help="Port for the Web UI Studio (default: 8505)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.web:
        from src.web_ui import run_web_server
        run_web_server(port=args.port)
        return

    config = get_config()
    history_mgr = HistoryManager()

    if args.status_report:
        print_stock_status(history_mgr)
        return

    generator = DualLLMStoryGenerator(
        ollama_host=config.ollama_host,
        director_model=config.director_model,
        writer_model=config.writer_model,
    )

    # Batch stock mode
    if args.stock_count > 0:
        conn = generator.check_connection()
        if not conn.get("online"):
            logger.error(f"Cannot reach Mac mini Ollama server at {config.ollama_host}: {conn.get('error')}")
            sys.exit(1)
        targets = history_mgr.select_unstocked_works(count=args.stock_count)
        if not targets:
            logger.info("All catalog episodes are already published or stocked!")
            print_stock_status(history_mgr)
            return

        generated_files: List[Path] = []
        for idx, work in enumerate(targets, start=1):
            logger.info(f"\n=== [{idx}/{len(targets)}] Dual-LLM Generating: {work['title']} ===")
            full_md, ep_title, refs, _ = generator.generate_complete_episode(work=work)
            today_str = datetime.now(JST).strftime("%Y-%m-%d")
            safe_id = work["id"].replace("-", "_")
            out_path = Path(f"content/{today_str}_{safe_id}.md")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(full_md, encoding="utf-8")
            generated_files.append(out_path)
            logger.info(f"Saved stocked episode: {out_path} ('{ep_title}')")

        if args.push:
            git_sync_and_push(generated_files)
        print_stock_status(history_mgr)
        return

    is_dry_run = True
    if args.send and not args.dry_run:
        is_dry_run = False

    target_file: Optional[Path] = None
    target_work = None
    target_refs: List[str] = []

    if args.file:
        target_file = Path(args.file)
        if not target_file.exists():
            logger.error(f"File not found: {target_file}")
            sys.exit(1)
        stem_norm = target_file.stem.replace("_", "-")
        for w in history_mgr.catalog:
            if w["id"] in stem_norm:
                target_work = w
                break
        target_refs = extract_refs_from_markdown(target_file.read_text(encoding="utf-8", errors="ignore"))
    else:
        target_work = history_mgr.select_next_work(work_id=args.work_id, force=args.force)
        if not target_work:
            logger.error("No unposted episodes found in catalog!")
            sys.exit(1)

        existing_file = history_mgr.find_stock_file_for_work(target_work["id"])
        conn = generator.check_connection() if (args.force or not existing_file) else {"online": False}
        if existing_file and (not args.force or not conn.get("online")):
            target_file = existing_file
            logger.info(f"Using pre-stocked episode file from content/: {target_file}")
            target_refs = extract_refs_from_markdown(target_file.read_text(encoding="utf-8", errors="ignore"))
        elif conn.get("online"):
            full_md, ep_title, target_refs, _ = generator.generate_complete_episode(work=target_work)
            today_str = datetime.now(JST).strftime("%Y-%m-%d")
            safe_id = target_work["id"].replace("-", "_")
            target_file = Path(f"content/{today_str}_{safe_id}.md")
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(full_md, encoding="utf-8")
            logger.info(f"Generated episode saved to: {target_file}")
        else:
            # Running on GitHub Actions cloud runner (cannot reach local Mac mini 192.168.128.59):
            # If user clicked Run workflow without specifying work_id, fall back to the latest stocked episode in content/
            stocked_candidates = []
            for w in history_mgr.catalog:
                sf = history_mgr.find_stock_file_for_work(w["id"])
                if sf is not None:
                    stocked_candidates.append((w, sf))
            if stocked_candidates:
                target_work, target_file = stocked_candidates[-1]
                logger.info(
                    f"Mac mini ({config.ollama_host}) is on local LAN; falling back to latest pre-stocked episode "
                    f"'{target_work['id']}' ({target_file}) for dispatch."
                )
                target_refs = extract_refs_from_markdown(target_file.read_text(encoding="utf-8", errors="ignore"))
            else:
                logger.error(
                    f"Mac mini Ollama ({config.ollama_host}) is not reachable and no pre-stocked file found in content/."
                )
                sys.exit(1)

    next_work = None
    if target_work:
        catalog = history_mgr.catalog
        for idx, w in enumerate(catalog):
            if w["id"] == target_work["id"]:
                next_work = catalog[(idx + 1) % len(catalog)]
                break

    formatted = format_post_content(
        str(target_file),
        status_override=args.status,
        include_jetpack_shortcodes=config.use_jetpack_shortcodes,
        next_work=next_work,
    )

    if args.preview_html or is_dry_run:
        preview_file = Path("preview_output.html")
        preview_file.write_text(formatted.content_html, encoding="utf-8")
        logger.info(f"Rendered HTML preview saved to: {preview_file.resolve()}")

    sender = WordPressMailSender(config)
    result = sender.send_post(formatted, dry_run=is_dry_run)
    if not result.get("success"):
        logger.error(f"Dispatch failed: {result.get('error')}")
        sys.exit(1)

    if not is_dry_run and target_work:
        history_mgr.record_post(
            work=target_work,
            episode_title=formatted.title,
            file_path=str(target_file),
            references=target_refs,
            status=formatted.status,
        )
        logger.info(f"Recorded '{formatted.title}' in data/history.json and data/POSTED_STORIES.md")


if __name__ == "__main__":
    main()
