#!/usr/bin/env bash
# ==============================================================================
# One-command autonomous worker setup for macOS node (`kenomac-mini` / Mac mini M4)
# Runs automatically at macOS boot/login and every 60 minutes via launchd,
# pulling `pending_illustration` episodes from GitHub, generating FLUX.2 images
# via local Draw Things (`http://localhost:7860`), rebuilding GitHub Pages (`docs/`),
# and pushing to GitHub even when MINISFORUM64GB is powered off.
# ==============================================================================
set -e

REPO_URL="https://github.com/k518-2026/rikejo-science-novel.git"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "${SCRIPT_DIR}/src/task_worker.py" ]; then
  WORK_DIR="${SCRIPT_DIR}"
else
  WORK_DIR="${HOME}/rikejo-science-novel"
  if [ ! -d "${WORK_DIR}/.git" ]; then
    echo "[1/3] Cloning repository into ${WORK_DIR}..."
    git clone "${REPO_URL}" "${WORK_DIR}"
  else
    echo "[1/3] Updating repository in ${WORK_DIR}..."
    (cd "${WORK_DIR}" && git pull --rebase --autostash origin main)
  fi
fi

PYTHON_BIN="$(command -v python3 || which python3)"
PLIST_PATH="${HOME}/Library/LaunchAgents/com.rikejo.science.novel.worker.plist"
mkdir -p "${HOME}/Library/LaunchAgents"

cat > "${PLIST_PATH}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.rikejo.science.novel.worker</string>
    <key>WorkingDirectory</key>
    <string>${WORK_DIR}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_BIN}</string>
        <string>-m</string>
        <string>src.task_worker</string>
        <string>--role</string>
        <string>kenomac-mini</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>StandardOutPath</key>
    <string>${WORK_DIR}/worker_mac.log</string>
    <key>StandardErrorPath</key>
    <string>${WORK_DIR}/worker_mac.err.log</string>
</dict>
</plist>
EOF

launchctl unload "${PLIST_PATH}" 2>/dev/null || true
launchctl load "${PLIST_PATH}"

echo "[2/3] Installed and loaded macOS LaunchAgent: ${PLIST_PATH}"
echo "[3/3] Running initial autonomous illustrator check on $(hostname)..."
cd "${WORK_DIR}"
"${PYTHON_BIN}" -m src.task_worker --role kenomac-mini
