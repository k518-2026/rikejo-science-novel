import os
import sys
import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

JST = timezone(timedelta(hours=9))

def main():
    repo_dir = Path(__file__).resolve().parent.parent
    os.chdir(repo_dir)

    print(f"[{datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')} JST] Checking daily publication status on GitHub...", flush=True)

    # 1. Fetch latest changes from GitHub
    try:
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=False, capture_output=True, timeout=30)
    except Exception as e:
        print(f"Warning: git pull failed: {e}", flush=True)

    # 2. Check if an episode was already published today (JST)
    history_file = repo_dir / "data" / "history.json"
    today_str = datetime.now(JST).strftime("%Y-%m-%d")
    already_posted = False

    if history_file.exists():
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
            for item in history:
                posted_at = item.get("posted_at", "")
                if posted_at[:10] == today_str:
                    already_posted = True
                    print(f"[OK] Today's episode is already published ({today_str} JST: {item.get('episode_title')}).", flush=True)
                    break
        except Exception as e:
            print(f"Error reading history.json: {e}", flush=True)

    if already_posted:
        print("[Status] No trigger needed. Exiting cleanly.", flush=True)
        return

    # 3. If NOT posted today, trigger publication on GitHub Actions
    print(f"[Trigger] Episode has NOT been published today ({today_str} JST). Sending command to GitHub...", flush=True)
    trigger_file = repo_dir / ".trigger_publish"
    trigger_content = f"trigger_publish_at={datetime.now(JST).isoformat()}\n"
    trigger_file.write_text(trigger_content, encoding="utf-8")

    try:
        subprocess.run(["git", "add", ".trigger_publish"], check=True, timeout=15)
        subprocess.run(["git", "commit", "-m", f"ci: startup trigger daily publish for {today_str}"], check=True, timeout=15)
        res = subprocess.run(["git", "push", "origin", "HEAD:main"], check=True, capture_output=True, text=True, timeout=30)
        print("[SUCCESS] Publication command sent to GitHub Actions! Workflow will publish today's episode.", flush=True)
    except Exception as e:
        print(f"Failed to push publication trigger to GitHub: {e}", flush=True)

if __name__ == "__main__":
    main()
