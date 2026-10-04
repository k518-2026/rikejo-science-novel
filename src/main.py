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
    print(" 【放課後サイエンス・キャンパス（Qwen3.5×Gemma4×FLUX.2）ストック＆配信状況】")
    print("=" * 76)
    print(f"  ・全エピソード数         : {len(history_mgr.catalog)} 話")
    print(f"  ・配信済み               : {posted_count} 話")
    print(f"  ・書き溜め済み（配信待ち）: {len(stocked_list)} 話")
    print(f"  ・未生成（今後の執筆対象）: {len(unstocked_list)} 話")
    print("-" * 76)

    if stocked_list:
        print("\n[OK] 【書き溜め済み・配信待ちストック】")
        for idx, w, sf in stocked_list:
            img_mark = "🎨[挿絵あり]" if sf.with_suffix(".png").exists() else "  [挿絵なし]"
            print(f"  [第{w.get('episode_num', idx):02d}話] {img_mark} {w['title']}（{w['faculty']}） -> {sf}")
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

        msg = f"feat(stock): Add {len(generated_files)} Rikejo science novel asset(s) via Qwen3.5xGemma4xFLUX2 [skip ci]"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        logger.info("Pushing to origin/main...")
        subprocess.run(["git", "push", "origin", "HEAD:main"], check=True)
        logger.info("Successfully pushed stocked episodes & illustrations to GitHub!")
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


def replenish_stock_if_needed(
    history_mgr: HistoryManager,
    generator: DualLLMStoryGenerator,
    min_stock: int = 1,
    target_stock: int = 6,
    push_to_git: bool = True,
) -> List[Path]:
    """
    Checks how many unposted stocked episodes remain in `content/`.
    If the remaining unposted stock is <= `min_stock` (e.g., 0 when stock runs out, or below threshold),
    automatically generates new episodes + Draw Things illustrations up to `target_stock` and pushes to GitHub.
    Also ensures any existing unposted stocked episodes that lack `.png` illustrations get their images generated.
    """
    try:
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=False)
        history_mgr.history = history_mgr._load_json(history_mgr.history_path)
        history_mgr.catalog = history_mgr._load_json(history_mgr.catalog_path)
    except Exception:
        pass

    conn = generator.check_connection()
    if not conn.get("online"):
        logger.info(f"Mac mini Ollama ({generator.ollama_host}) is not reachable on LAN; skipping auto-replenish.")
        return []

    generated_assets: List[Path] = []
    posted_ids = history_mgr.get_posted_ids()

    # 1. Ensure all currently unposted stocked episodes have their .png illustration
    dt_online = conn.get("draw_things_online", False)
    if dt_online:
        for w in history_mgr.catalog:
            if w["id"] in posted_ids:
                continue
            sf = history_mgr.find_stock_file_for_work(w["id"])
            if sf is not None:
                img_p = sf.with_suffix(".png")
                if not img_p.exists():
                    logger.info(f"[Auto-Replenish] Generating missing illustration for stocked episode '{w['id']}'...")
                    md_text = sf.read_text(encoding="utf-8", errors="ignore")
                    saved_img, _ = generator.generate_illustration(
                        work=w,
                        output_image_path=img_p,
                        story_body=md_text,
                        episode_title=w.get("title", ""),
                    )
                    if saved_img:
                        generated_assets.append(saved_img)

    # 2. Check remaining unposted stock count
    current_stock = history_mgr.count_unposted_stock()
    logger.info(f"[Auto-Replenish Check] Unposted stocked episodes: {current_stock} (trigger threshold <= {min_stock}, target = {target_stock})")

    if current_stock <= min_stock:
        needed = max(1, target_stock - current_stock)
        logger.info(
            f"[Auto-Replenish Triggered!] Unposted stock ({current_stock}) is <= {min_stock}. "
            f"Automatically generating {needed} new episode(s) and illustration(s)..."
        )
        targets = history_mgr.select_unstocked_works(count=needed)
        if len(targets) < needed:
            missing_themes = needed - len(targets)
            new_themes = generator.generate_new_catalog_themes(
                existing_catalog=history_mgr.catalog,
                count=max(3, missing_themes),
            )
            if new_themes:
                history_mgr.append_catalog_works(new_themes)
                targets = history_mgr.select_unstocked_works(count=needed)

        for idx, work in enumerate(targets, start=1):
            logger.info(f"\n=== [Auto-Replenish {idx}/{len(targets)}] Dual-LLM Generating: {work['title']} ===")
            full_md, ep_title, refs, _ = generator.generate_complete_episode(work=work)
            today_str = datetime.now(JST).strftime("%Y-%m-%d")
            safe_id = work["id"].replace("-", "_")
            out_path = Path(f"content/{today_str}_{safe_id}.md")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(full_md, encoding="utf-8")
            generated_assets.append(out_path)
            logger.info(f"Saved auto-replenished episode: {out_path} ('{ep_title}')")

            img_out_path = out_path.with_suffix(".png")
            saved_img, _ = generator.generate_illustration(
                work=work,
                output_image_path=img_out_path,
                story_body=full_md,
                episode_title=ep_title,
            )
            if saved_img:
                generated_assets.append(saved_img)

    if generated_assets and push_to_git:
        git_sync_and_push(generated_assets)

    return generated_assets


def main():
    parser = argparse.ArgumentParser(
        description="Rikejo Science Light Novel Dual-LLM Generator (Qwen 3.5 9B x Gemma 4 12B) + Draw Things (FLUX.2) & Mail Poster"
    )
    parser.add_argument("--file", "-f", default=None, help="Path to a specific markdown file to publish directly")
    parser.add_argument("--work-id", default=None, help="Specific episode ID from data/science_catalog.json")
    parser.add_argument("--stock-count", "-n", type=int, default=0, help="Batch-generate N episodes + illustrations into content/")
    parser.add_argument("--auto-replenish", action="store_true", help="Automatically generate new episodes + illustrations when unposted stock <= --min-stock")
    parser.add_argument("--min-stock", type=int, default=0, help="Stock threshold to trigger --auto-replenish (default: 0 = when stock runs out)")
    parser.add_argument("--target-stock", type=int, default=6, help="Target number of unposted episodes to maintain on --auto-replenish (default: 6)")
    parser.add_argument("--generate-images", action="store_true", help="Generate missing .png illustrations for existing stocked episodes via Draw Things")
    parser.add_argument("--push", action="store_true", help="Git commit & push after generating stock or illustrations")
    parser.add_argument("--status-report", action="store_true", help="Show current stock & publication status")
    parser.add_argument("--send", action="store_true", help="Actually send the email to Blogger / WordPress")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no email sent, history not updated)")
    parser.add_argument("--preview-html", action="store_true", help="Export rendered HTML to preview_output.html")
    parser.add_argument("--status", choices=["publish", "draft"], default=None, help="Override post status (publish or draft)")
    parser.add_argument("--force", action="store_true", help="Force regeneration even if stock or history exists")
    parser.add_argument("--web", action="store_true", help="Launch the interactive Web UI Studio in browser")
    parser.add_argument("--port", type=int, default=8505, help="Port for the Web UI Studio (default: 8505)")
    parser.add_argument("--repost", default=None, help="Re-post a specific episode number or ID (e.g., 1, 2, ep01-bioluminescence-plant, or reset_all)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.web:
        from src.web_ui import run_web_server
        run_web_server(port=args.port)
        return

    config = get_config()
    history_mgr = HistoryManager()

    if args.repost:
        rep_val = str(args.repost).strip()
        if rep_val == "reset_all":
            history_mgr.reset_history()
            logger.info("Reset all posting history.")
        else:
            matched_w = None
            for w in history_mgr.catalog:
                if w["id"] == rep_val or str(w.get("episode_num")) == rep_val:
                    matched_w = w
                    break
            if matched_w:
                history_mgr.remove_from_history(matched_w["id"])
                args.work_id = matched_w["id"]
                logger.info(f"Removed '{matched_w['id']}' from history so it can be cleanly posted.")

    if args.status_report:
        print_stock_status(history_mgr)
        return

    generator = DualLLMStoryGenerator(
        ollama_host=config.ollama_host,
        director_model=config.director_model,
        writer_model=config.writer_model,
        draw_things_host=config.draw_things_host,
    )

    # Auto-replenish mode (triggered by scheduled task or CLI when stock runs out)
    if args.auto_replenish:
        replenish_stock_if_needed(
            history_mgr=history_mgr,
            generator=generator,
            min_stock=args.min_stock,
            target_stock=args.target_stock,
            push_to_git=args.push,
        )
        print_stock_status(history_mgr)
        return

    # Generate missing illustrations for existing stocked episodes
    if args.generate_images:
        dt_conn = generator.check_draw_things_connection()
        if not dt_conn.get("online"):
            logger.error(f"Cannot reach Draw Things HTTP API at {config.draw_things_host}: {dt_conn.get('error')}")
            sys.exit(1)
        posted_ids = history_mgr.get_posted_ids()
        generated_imgs: List[Path] = []
        for w in history_mgr.catalog:
            if w["id"] in posted_ids and not args.force:
                continue
            sf = history_mgr.find_stock_file_for_work(w["id"])
            if sf is None:
                continue
            img_path = sf.with_suffix(".png")
            if img_path.exists() and not args.force:
                logger.info(f"Illustration already exists for {w['id']}: {img_path}")
                continue
            md_text = sf.read_text(encoding="utf-8", errors="ignore")
            saved_img, _ = generator.generate_illustration(
                work=w,
                output_image_path=img_path,
                story_body=md_text,
                episode_title=w["title"],
            )
            if saved_img:
                generated_imgs.append(saved_img)
        if args.push and generated_imgs:
            git_sync_and_push(generated_imgs)
        print_stock_status(history_mgr)
        return

    # Batch stock mode
    if args.stock_count > 0:
        conn = generator.check_connection()
        if not conn.get("online"):
            logger.error(f"Cannot reach Mac mini Ollama server at {config.ollama_host}: {conn.get('error')}")
            sys.exit(1)
        targets = history_mgr.select_unstocked_works(count=args.stock_count)
        if len(targets) < args.stock_count:
            new_themes = generator.generate_new_catalog_themes(
                existing_catalog=history_mgr.catalog,
                count=max(3, args.stock_count - len(targets)),
            )
            if new_themes:
                history_mgr.append_catalog_works(new_themes)
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

            img_out_path = out_path.with_suffix(".png")
            saved_img, _ = generator.generate_illustration(
                work=work,
                output_image_path=img_out_path,
                story_body=full_md,
                episode_title=ep_title,
            )
            if saved_img:
                generated_files.append(saved_img)

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
        # Prevent duplicate consecutive posts when manual dispatch and scheduled cron overlap
        if os.getenv("GITHUB_EVENT_NAME") == "schedule" and not args.force and history_mgr.history:
            last_entry = history_mgr.history[-1]
            last_posted_str = last_entry.get("posted_at", "")
            if last_posted_str:
                try:
                    last_dt = datetime.fromisoformat(last_posted_str)
                    elapsed_minutes = (datetime.now(JST) - last_dt).total_seconds() / 60.0
                    if 0 <= elapsed_minutes < 120:
                        logger.info(
                            f"An episode ('{last_entry.get('episode_title')}') was already published "
                            f"{elapsed_minutes:.1f} minutes ago. Skipping scheduled run to prevent duplicate posting."
                        )
                        return
                except Exception as e:
                    logger.warning(f"Could not parse last posted_at timestamp: {e}")

        target_work = history_mgr.select_next_work(work_id=args.work_id, force=args.force)
        if not target_work:
            # All existing catalog works have been published -> if Mac mini is online, auto-create new catalog works!
            conn_check = generator.check_connection()
            if conn_check.get("online"):
                new_themes = generator.generate_new_catalog_themes(existing_catalog=history_mgr.catalog, count=3)
                if new_themes:
                    history_mgr.append_catalog_works(new_themes)
                    target_work = history_mgr.select_next_work(work_id=args.work_id, force=args.force)
            if not target_work:
                logger.info("All catalog episodes have already been published! Skipping to prevent duplicate posts.")
                return

        posted_ids = history_mgr.get_posted_ids()
        if target_work["id"] in posted_ids and not args.force and not args.repost:
            logger.info(
                f"Episode '{target_work['id']}' ({target_work['title']}) is already recorded in data/history.json as published. "
                f"Skipping to strictly prevent duplicate posts. (Use --repost or --force if you intend to re-send.)"
            )
            return

        existing_file = history_mgr.find_stock_file_for_work(target_work["id"])
        conn = generator.check_connection() if (args.force or not existing_file) else {"online": False}
        if existing_file and (not args.force or not conn.get("online")):
            target_file = existing_file
            logger.info(f"Using pre-stocked episode file from content/: {target_file}")
            target_refs = extract_refs_from_markdown(target_file.read_text(encoding="utf-8", errors="ignore"))
        elif conn.get("online"):
            logger.info(f"Stock file not found for '{target_work['id']}'. Automatically generating article & illustration via Mac mini...")
            full_md, ep_title, target_refs, _ = generator.generate_complete_episode(work=target_work)
            today_str = datetime.now(JST).strftime("%Y-%m-%d")
            safe_id = target_work["id"].replace("-", "_")
            target_file = Path(f"content/{today_str}_{safe_id}.md")
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(full_md, encoding="utf-8")
            logger.info(f"Generated episode saved to: {target_file}")
            img_out_path = target_file.with_suffix(".png")
            generator.generate_illustration(
                work=target_work,
                output_image_path=img_out_path,
                story_body=full_md,
                episode_title=ep_title,
            )
        else:
            # Running on GitHub Actions cloud runner (cannot reach local Mac mini 192.168.128.59):
            # Look ONLY for an UNPOSTED stocked episode in content/ so we NEVER send a duplicate
            unposted_stocked = []
            for w in history_mgr.catalog:
                if w["id"] in posted_ids:
                    continue
                sf = history_mgr.find_stock_file_for_work(w["id"])
                if sf is not None:
                    unposted_stocked.append((w, sf))
            if unposted_stocked:
                target_work, target_file = unposted_stocked[0]
                logger.info(
                    f"Selected unposted pre-stocked episode '{target_work['id']}' ({target_file}) for dispatch."
                )
                target_refs = extract_refs_from_markdown(target_file.read_text(encoding="utf-8", errors="ignore"))
            else:
                logger.info(
                    "No unposted pre-stocked episodes remain in content/ and Mac mini is on local LAN. "
                    "Skipping dispatch to prevent duplicate posts."
                )
                return

    # Ensure sidecar illustration .png exists if Draw Things is reachable on LAN
    if target_file and target_work:
        sidecar_png = target_file.with_suffix(".png")
        if not sidecar_png.exists():
            dt_conn = generator.check_draw_things_connection()
            if dt_conn.get("online"):
                md_text = target_file.read_text(encoding="utf-8", errors="ignore")
                generator.generate_illustration(
                    work=target_work,
                    output_image_path=sidecar_png,
                    story_body=md_text,
                    episode_title=target_work.get("title", ""),
                )

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

        # After recording a post, if unposted stock has run out (0 remaining) and Mac mini is reachable on LAN,
        # automatically generate the next batch of articles & illustrations!
        remaining_stock = history_mgr.count_unposted_stock()
        if remaining_stock == 0:
            logger.info("Unposted stock has reached 0! Checking if Mac mini is online to auto-replenish...")
            replenish_stock_if_needed(
                history_mgr=history_mgr,
                generator=generator,
                min_stock=0,
                target_stock=6,
                push_to_git=args.push,
            )


if __name__ == "__main__":
    main()
