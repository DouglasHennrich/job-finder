#!/bin/bash
set -euo pipefail

PLIST_NAME="com.douglashennrich.jobfinder"
PROJECT_DIR="/Users/douglashennrich/Documents/Projetos/job-finder"
PLIST_SRC="${PROJECT_DIR}/${PLIST_NAME}.plist"
PLIST_DEST="${HOME}/Library/LaunchAgents/${PLIST_NAME}.plist"

TOKEN=$(gh auth token 2>/dev/null || true)
if [ -z "$TOKEN" ]; then
    echo "ERROR: Could not fetch token via 'gh auth token'. Run 'gh auth login' first." >&2
    exit 1
fi

sed "s/REPLACE_WITH_GH_AUTH_TOKEN/${TOKEN}/" "${PLIST_SRC}" > "${PLIST_DEST}"
chmod 644 "${PLIST_DEST}"

launchctl load "${PLIST_DEST}"

echo "Installed and loaded ${PLIST_NAME}"
echo "Logs: ${PROJECT_DIR}/logs/job-finder.log"
