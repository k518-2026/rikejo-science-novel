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
    published_pages_list = []
    unstocked_list = []

    for idx, w in enumerate(history_mgr.catalog, start=1):
        wid = w["id"]
        stock_file = history_mgr.find_stock_file_for_work(wid)
        if stock_file is not None:
            published_pages_list.append((idx, w, stock_file))
        else:
            unstocked_list.append((idx, w))

    illustrated_count = sum(1 for _, _, sf in published_pages_list if sf.with_suffix(".png").exists())

    print("\n" + "=" * 78)
    print(" 【放課後サイエンス・キャンパス（Qwen3.5×Gemma4×FLUX.2）GitHub Pages 公開＆蓄積状況】")
    print("=" * 78)
    print("  ・Webサイト (GitHub Pages) : https://k518-2026.github.io/rikejo-science-novel/")
    print("  ・ブログメール自動投稿     : 休止中（GitHub Pages 蓄積・Web公開モード）")
    print(f"  ・カタログ総エピソード数   : {len(history_mgr.catalog)} 話")
    print(f"  ・GitHub Pages 公開済み    : {len(published_pages_list)} 話（うち挿絵付き {illustrated_count} 話）")
    print(f"  ・未生成（今後の執筆対象） : {len(unstocked_list)} 話")
    print("-" * 78)

    if published_pages_list:
        print("\n[OK] 【GitHub Pages 収録・公開済みエピソード一覧】")
        for idx, w, sf in published_pages_list:
            img_mark = "🎨[挿絵あり]" if sf.with_suffix(".png").exists() else "  [挿絵なし]"
            print(f"  [#{w.get('episode_num', idx):02d}] {img_mark} {w['title']}（{w['faculty']}） -> {sf}")
    else:
        print("\n[!] 現在、生成済みのエピソードは 0 話です。")

    if unstocked_list:
        print("\n[NEXT] 【未生成・次回のMac mini M4ローカルLLM執筆対象（先頭5件）】")
        for idx, w in unstocked_list[:5]:
            print(f"  [#{w.get('episode_num', idx):02d}] {w['id']} : {w['title']}（{w['faculty']}）")
    print("=" * 78 + "\n")


def git_sync_and_push(generated_files: List[Path]) -> bool:
    if not generated_files:
        return True
    try:
        subprocess.run(["git", "add", "README.md", "content/", "data/", "docs/"], check=True)
        diff_res = subprocess.run(["git", "diff", "--staged", "--quiet"])
        if diff_res.returncode == 0:
            logger.info("No new changes in README.md, content/, data/, or docs/ to commit.")
            return True

        msg = f"feat(pages): Add {len(generated_files)} Rikejo science novel asset(s) via Mac mini M4 & update GitHub Pages"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        logger.info("Syncing with remote GitHub repository (git pull --rebase origin main)...")
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=False)
        logger.info("Pushing to origin/main...")
        subprocess.run(["git", "push", "origin", "HEAD:main"], check=True)
        logger.info("Successfully pushed episodes, illustrations & GitHub Pages to GitHub!")
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
    min_stock: int = 5,
    target_stock: int = 6,
    push_to_git: bool = True,
) -> List[Path]:
    """
    Pulls accumulated tasks (`data/tasks.json`) from GitHub on PC startup or scheduled run,
    completes any missing illustrations via `kenomac-mini:7860`, and writes queued/due episodes
    by alternating between Primary (`http://rtx5060lp:11434`) and Secondary (`http://sff7020:1234`).
    """
    from src.site_builder import build_github_pages
    from src.task_worker import (
        TASKS_JSON_PATH,
        default_assigned_writer_for_episode,
        sync_tasks_manifest,
        write_tasks_markdown,
    )

    try:
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=False)
        history_mgr.history = history_mgr._load_json(history_mgr.history_path)
        history_mgr.catalog = history_mgr._load_json(history_mgr.catalog_path)
    except Exception:
        pass

    manifest = sync_tasks_manifest(history_mgr)

    conn = generator.check_connection()
    if not conn.get("online"):
        logger.info("Neither Primary (rtx5060lp:11434) nor Secondary (sff7020:1234) is reachable on LAN; skipping auto-replenish.")
        return []

    generated_assets: List[Path] = []

    # 1. Ensure ALL existing episodes in content/ have their .png illustration
    dt_online = conn.get("draw_things_online", False)
    if dt_online:
        for w in history_mgr.catalog:
            sf = history_mgr.find_stock_file_for_work(w["id"])
            if sf is not None:
                img_p = sf.with_suffix(".png")
                if not img_p.exists():
                    logger.info(f"[Auto-Replenish] Generating missing illustration for episode '{w['id']}'...")
                    md_text = sf.read_text(encoding="utf-8", errors="ignore")
                    saved_img, _ = generator.generate_illustration(
                        work=w,
                        output_image_path=img_p,
                        story_body=md_text,
                        episode_title=w.get("title", ""),
                    )
                    if saved_img:
                        generated_assets.append(saved_img)
                        manifest = sync_tasks_manifest(history_mgr)
                        build_github_pages(history_mgr)
                        if push_to_git:
                            git_sync_and_push([saved_img])

    # 2. Check GitHub task queue (`status == 'queued'`) first, then weekly quota
    queued_task_ids = [t["id"] for t in manifest.get("tasks", []) if t.get("status") == "queued"]
    blog_paused = os.environ.get("PAUSE_BLOG_AUTO_POST", "true").strip().lower() in ("1", "true", "yes")
    current_stock = history_mgr.count_unposted_stock()
    ungenerated = history_mgr.count_ungenerated_works()

    if queued_task_ids:
        needed = len(queued_task_ids) if min_stock <= 0 else min(len(queued_task_ids), max(1, min_stock))
        logger.info(
            f"[GitHub Task Queue Startup] Found {len(queued_task_ids)} queued task(s) on GitHub (`data/tasks.json`). "
            f"Executing {needed} episode(s) alternating between rtx5060lp and sff7020..."
        )
    elif blog_paused:
        weekly_quota = max(1, min_stock if min_stock > 0 else 5)
        generated_this_week = history_mgr.count_episodes_generated_this_week()
        needed = max(0, weekly_quota - generated_this_week)
        if needed == 0:
            logger.info(
                f"[GitHub Pages Weekly Accumulation] Weekly quota of {weekly_quota} episode(s) already met for this week "
                f"({generated_this_week}/{weekly_quota} generated)."
            )
            build_github_pages(history_mgr)
        else:
            logger.info(
                f"[GitHub Pages Weekly Accumulation] Generating {needed} new episode(s) alternating between rtx5060lp and sff7020 "
                f"({generated_this_week}/{weekly_quota} generated this week, {ungenerated} ungenerated in catalog)..."
            )
    else:
        logger.info(f"[Auto-Replenish Check] Unposted stocked episodes: {current_stock} (trigger threshold <= {min_stock}, target = {target_stock})")
        needed = max(1, target_stock - current_stock) if current_stock <= min_stock else 0

    if needed > 0:
        targets = history_mgr.select_unstocked_works(count=needed)
        if len(targets) < needed:
            missing_themes = needed - len(targets)
            new_themes = generator.generate_new_catalog_themes(
                existing_catalog=history_mgr.catalog,
                count=max(5, missing_themes),
            )
            if new_themes:
                history_mgr.append_catalog_works(new_themes)
                manifest = sync_tasks_manifest(history_mgr)
                targets = history_mgr.select_unstocked_works(count=needed)

        task_map = {t["id"]: t for t in manifest.get("tasks", [])}
        for idx, work in enumerate(targets, start=1):
            t_entry = task_map.get(work["id"], {})
            preferred_writer = t_entry.get("assigned_writer") or default_assigned_writer_for_episode(
                int(work.get("episode_num", idx))
            )
            logger.info(
                f"\n=== [Auto-Replenish {idx}/{len(targets)}] Alternating Dual-Node Generating: "
                f"{work['title']} (Assigned: {preferred_writer}) ==="
            )
            try:
                ep_assets: List[Path] = []
                full_md, ep_title, refs, _ = generator.generate_complete_episode(
                    work=work,
                    preferred_node=preferred_writer,
                )
                actual_writer = generator.last_used_node or preferred_writer
                today_str = datetime.now(JST).strftime("%Y-%m-%d")
                safe_id = work["id"].replace("-", "_")
                out_path = Path(f"content/{today_str}_{safe_id}.md")
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(full_md, encoding="utf-8")
                generated_assets.append(out_path)
                ep_assets.append(out_path)
                logger.info(f"Saved episode: {out_path} ('{ep_title}', written_by={actual_writer})")

                if work["id"] in task_map:
                    task_map[work["id"]]["written_by"] = actual_writer
                    task_map[work["id"]]["written_at"] = datetime.now(JST).isoformat()

                img_out_path = out_path.with_suffix(".png")
                saved_img, _ = generator.generate_illustration(
                    work=work,
                    output_image_path=img_out_path,
                    story_body=full_md,
                    episode_title=ep_title,
                )
                if saved_img:
                    generated_assets.append(saved_img)
                    ep_assets.append(saved_img)

                manifest["updated_at"] = datetime.now(JST).isoformat()
                TASKS_JSON_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                manifest = sync_tasks_manifest(history_mgr)
                write_tasks_markdown(manifest)
                build_github_pages(history_mgr)
                if push_to_git and ep_assets:
                    git_sync_and_push(ep_assets)
            except Exception as e:
                logger.error(f"Failed to generate episode '{work.get('id')}': {e}")
                continue

    return generated_assets


def main():
    parser = argparse.ArgumentParser(
        description="Rikejo Science Light Novel Dual-LLM Generator (Qwen 3.5 9B x Gemma 4 12B) + Draw Things (FLUX.2) & GitHub Pages Publisher"
    )
    parser.add_argument("--file", "-f", default=None, help="Path to a specific markdown file")
    parser.add_argument("--work-id", default=None, help="Specific episode ID from data/science_catalog.json")
    parser.add_argument("--stock-count", "-n", type=int, default=0, help="Batch-generate N episodes + illustrations into content/ and docs/")
    parser.add_argument("--auto-replenish", action="store_true", help="Automatically generate new episodes + illustrations and update GitHub Pages")
    parser.add_argument("--min-stock", type=int, default=5, help="Batch count for weekly --auto-replenish (default: 5 episodes)")
    parser.add_argument("--target-stock", type=int, default=6, help="Target number of episodes to maintain on --auto-replenish (default: 6)")
    parser.add_argument("--generate-images", action="store_true", help="Generate missing .png illustrations for existing episodes in content/ via Draw Things")
    parser.add_argument("--build-pages", action="store_true", help="Rebuild GitHub Pages static site (docs/) and README.md from content/")
    parser.add_argument("--push", action="store_true", help="Git commit & push after generating stock, illustrations, or GitHub Pages")
    parser.add_argument("--status-report", action="store_true", help="Show current GitHub Pages & stock status")
    parser.add_argument("--send", action="store_true", help="(Paused by default) Send email to Blogger / WordPress only if PAUSE_BLOG_AUTO_POST=false")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode")
    parser.add_argument("--preview-html", action="store_true", help="Export rendered HTML to preview_output.html")
    parser.add_argument("--status", choices=["publish", "draft"], default=None, help="Override post status (publish or draft)")
    parser.add_argument("--force", action="store_true", help="Force regeneration even if stock or history exists")
    parser.add_argument("--web", action="store_true", help="Launch the interactive Web UI Studio in browser")
    parser.add_argument("--port", type=int, default=8505, help="Port for the Web UI Studio (default: 8505)")
    parser.add_argument("--repost", default=None, help="Re-post a specific episode number or ID")
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
                logger.info(f"Removed '{matched_w['id']}' from history.")

    if args.status_report:
        print_stock_status(history_mgr)
        return

    if args.build_pages:
        from src.site_builder import build_github_pages
        build_github_pages(history_mgr)
        if args.push:
            git_sync_and_push([Path("docs/index.html")])
        print_stock_status(history_mgr)
        return

    generator = DualLLMStoryGenerator(
        ollama_host=config.ollama_host,
        director_model=config.director_model,
        writer_model=config.writer_model,
        draw_things_host=config.draw_things_host,
    )

    # Auto-replenish mode (triggered by scheduled task or CLI)
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

    # Generate missing illustrations for ALL existing episodes in content/
    if args.generate_images:
        from src.site_builder import build_github_pages
        dt_conn = generator.check_draw_things_connection()
        if not dt_conn.get("online"):
            logger.error(f"Cannot reach Draw Things HTTP API at {config.draw_things_host}: {dt_conn.get('error')}")
            sys.exit(1)
        generated_imgs: List[Path] = []
        for w in history_mgr.catalog:
            if args.work_id and w["id"] != args.work_id:
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
                build_github_pages(history_mgr)
                if args.push:
                    git_sync_and_push([saved_img])
        print_stock_status(history_mgr)
        return

    # Batch stock mode
    if args.stock_count > 0:
        from src.site_builder import build_github_pages
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
            logger.info("All catalog episodes are already generated in content/!")
            build_github_pages(history_mgr)
            print_stock_status(history_mgr)
            return

        generated_files: List[Path] = []
        for idx, work in enumerate(targets, start=1):
            logger.info(f"\n=== [{idx}/{len(targets)}] Dual-LLM Generating: {work['title']} ===")
            ep_assets: List[Path] = []
            full_md, ep_title, refs, _ = generator.generate_complete_episode(work=work)
            today_str = datetime.now(JST).strftime("%Y-%m-%d")
            safe_id = work["id"].replace("-", "_")
            out_path = Path(f"content/{today_str}_{safe_id}.md")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(full_md, encoding="utf-8")
            generated_files.append(out_path)
            ep_assets.append(out_path)
            logger.info(f"Saved episode: {out_path} ('{ep_title}')")

            img_out_path = out_path.with_suffix(".png")
            saved_img, _ = generator.generate_illustration(
                work=work,
                output_image_path=img_out_path,
                story_body=full_md,
                episode_title=ep_title,
            )
            if saved_img:
                generated_files.append(saved_img)
                ep_assets.append(saved_img)

            build_github_pages(history_mgr)
            if args.push and ep_assets:
                git_sync_and_push(ep_assets)

        print_stock_status(history_mgr)
        return

    # Default mode: Blog auto-posting is paused; rebuild GitHub Pages (docs/) and README.md
    blog_paused = os.environ.get("PAUSE_BLOG_AUTO_POST", "true").strip().lower() in ("1", "true", "yes")
    if blog_paused:
        from src.site_builder import build_github_pages
        logger.info("Blog email auto-posting is paused (PAUSE_BLOG_AUTO_POST=true). Building GitHub Pages (docs/) and README.md...")
        build_github_pages(history_mgr)
        if args.push:
            git_sync_and_push([Path("docs/index.html")])
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
            logger.info("All catalog episodes have already been published!")
            return
        existing_file = history_mgr.find_stock_file_for_work(target_work["id"])
        if existing_file:
            target_file = existing_file
            target_refs = extract_refs_from_markdown(target_file.read_text(encoding="utf-8", errors="ignore"))
        else:
            return

    formatted = format_post_content(
        str(target_file),
        status_override=args.status,
        include_jetpack_shortcodes=config.use_jetpack_shortcodes,
        next_work=None,
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
        from src.site_builder import build_github_pages
        build_github_pages(history_mgr)


if __name__ == "__main__":
    main()
