"""Regenerate illustrations with 4-panel manga layout (512x1024) for stocked episodes.

Usage:
    python regenerate_images.py [start_ep] [end_ep] [--push]
Example:
    python regenerate_images.py 10 12 --push
"""
import re
import sys
from pathlib import Path

from src.config import get_config
from src.dual_llm_generator import DualLLMStoryGenerator
from src.history_manager import HistoryManager
from src.site_builder import build_github_pages
from src.main import git_sync_and_push, setup_logging


def main():
    setup_logging(True)
    non_flags = [a for a in sys.argv[1:] if not a.startswith("--")]
    push = "--push" in sys.argv[1:]

    start = int(non_flags[0]) if len(non_flags) >= 1 else 10
    end = int(non_flags[1]) if len(non_flags) >= 2 else start

    config = get_config()
    gen = DualLLMStoryGenerator(
        ollama_host=config.ollama_host,
        director_model=config.director_model,
        writer_model=config.writer_model,
        draw_things_host=config.draw_things_host,
    )
    hm = HistoryManager()

    print(f"=== Regenerating 4-panel manga illustrations: #{start:02d} to #{end:02d} ===", flush=True)

    generated_any = False
    for w in hm.catalog:
        sf = hm.find_stock_file_for_work(w["id"])
        if sf is None:
            continue
        m = re.search(r"_ep(\d+)_", sf.name)
        if not m:
            continue
        ep_n = int(m.group(1))
        if ep_n < start or ep_n > end:
            continue

        png = sf.with_suffix(".png")
        tmp = sf.with_suffix(".new.png")
        print(f"\n[#{ep_n:02d}] Generating 4-panel manga for '{w.get('title')}' ({w['id']})...", flush=True)

        saved = None
        for attempt in range(1, 4):
            try:
                saved, prompt_used = gen.generate_illustration(
                    work=w,
                    output_image_path=tmp,
                    story_body=sf.read_text(encoding="utf-8", errors="ignore"),
                    episode_title=w.get("title", ""),
                )
                if saved and tmp.exists():
                    break
            except Exception as ex:
                print(f"[#{ep_n:02d}] Attempt {attempt} failed: {ex}. Retrying...", flush=True)
            import time
            time.sleep(10)

        if saved and tmp.exists():
            tmp.replace(png)
            print(f"[#{ep_n:02d}] SUCCESS: Saved 512x1024 4-panel manga to {png}", flush=True)
            generated_any = True
        else:
            print(f"[#{ep_n:02d}] FAILED to generate illustration for {sf.name}", flush=True)

    if generated_any:
        print("\nRebuilding GitHub Pages (docs/)...", flush=True)
        build_github_pages(hm)
        if push:
            print("Committing and pushing to GitHub...", flush=True)
            msg = f"art(4koma): Regenerate 4-panel manga illustrations up to #{end:02d} & update GitHub Pages"
            import subprocess
            subprocess.run(["git", "add", "content/", "docs/", "README.md"], check=True)
            diff_res = subprocess.run(["git", "diff", "--staged", "--quiet"])
            if diff_res.returncode != 0:
                subprocess.run(["git", "commit", "-m", msg], check=True)
                subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=False)
                subprocess.run(["git", "push", "origin", "HEAD:main"], check=True)
                print("Successfully pushed to GitHub!", flush=True)
            else:
                print("No changes to commit.", flush=True)


if __name__ == "__main__":
    main()
