"""Regenerate illustrations with smiling characters and strong contrast for stocked episodes.

Usage: python regenerate_images.py [from_ep=15] [--push]
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
    setup_logging(False)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    push = "--push" in sys.argv[1:]
    start = int(args[0]) if args else 15
    config = get_config()
    gen = DualLLMStoryGenerator(
        ollama_host=config.ollama_host,
        director_model=config.director_model,
        writer_model=config.writer_model,
        draw_things_host=config.draw_things_host,
    )
    hm = HistoryManager()
    for w in hm.catalog:
        sf = hm.find_stock_file_for_work(w["id"])
        if sf is None:
            continue
        m = re.search(r"_ep(\d+)_", sf.name)
        if not m or int(m.group(1)) < start:
            continue
        png = sf.with_suffix(".png")
        tmp = sf.with_suffix(".new.png")
        saved, _ = gen.generate_illustration(
            work=w,
            output_image_path=tmp,
            story_body=sf.read_text(encoding="utf-8", errors="ignore"),
            episode_title=w.get("title", ""),
        )
        if saved and tmp.exists():
            tmp.replace(png)
            build_github_pages(hm)
            if push:
                git_sync_and_push([png])
            print(f"OK {png}", flush=True)
        else:
            print(f"FAILED {sf.name}", flush=True)


if __name__ == "__main__":
    main()


