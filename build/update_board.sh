#!/bin/bash
# Morning Market Cards — GitHub Pages publisher.
#
# Builds index.html from a dataset JSON and pushes to GitHub.
# Designed to run from within a cloned copy of this repo.
#
# Usage: update_board.sh <dataset.json> [repo-dir]
#
#   <dataset.json>  Path to the card dataset (see build_board.py for format).
#   [repo-dir]      Repo root (defaults to the parent of this script's dir).
#
# The script skips the push when the built HTML is unchanged.
# Requires: git, python3, and push access to the repo (e.g. via deploy key).

set -e

if [ $# -lt 1 ]; then
  echo "usage: $0 <dataset.json> [repo-dir]" >&2
  exit 1
fi

DATASET="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="${2:-$(dirname "$SCRIPT_DIR")}"

if [ ! -f "$DATASET" ]; then
  echo "ERROR: dataset not found: $DATASET" >&2
  exit 1
fi
if [ ! -d "$REPO_DIR/.git" ]; then
  echo "ERROR: not a git repo: $REPO_DIR" >&2
  exit 1
fi

cd "$REPO_DIR"

# Build the board using this repo's scripts
python3 "$SCRIPT_DIR/build_board.py" "$DATASET" index.html "$SCRIPT_DIR/board_template.html"

# Commit and push only when something changed
git add index.html
if git diff --cached --quiet; then
  echo "No changes — board is already current. Skipping push."
else
  DATE_LABEL=$(date +"%a %b %-d, %Y")
  SNAPSHOT=$(python3 -c "import json; print(json.load(open('$DATASET')).get('snapshot_id',''))" 2>/dev/null || echo "")
  MSG="Morning Market Cards — $DATE_LABEL"
  [ -n "$SNAPSHOT" ] && MSG="$MSG (snapshot #$SNAPSHOT)"
  git -c user.name="Muse" -c user.email="avkash1996@gmail.com" commit -m "$MSG" --quiet
  git push --quiet origin main
  echo "Pushed board update."
fi

# Verify the live site (Pages can take a minute to rebuild)
sleep 20
TITLE=$(curl -s "https://avkashc.github.io/morning-stocks-cards/" --max-time 20 \
  | grep -o "<title>[^<]*</title>" | head -1)
echo "Live site title: $TITLE"
echo "Done."
