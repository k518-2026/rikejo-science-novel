"""Regenerate (bright-toned) illustrations for stocked episodes.

Usage: python regenerate_images.py [from_ep=6]
"""
import re
import sys
from pathlib import Path

from src.config import get_config
from src.dual_llm_generator import DualLLMStoryGenerator
from src.history_manager import HistoryManager


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 6
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
            print(f"OK {png}", flush=True)
        else:
            print(f"FAILED {sf.name}", flush=True)


if __name__ == "__main__":
    main()

