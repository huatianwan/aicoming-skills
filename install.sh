#!/bin/bash
set -e

SKILL_NAME="aicoming"
SKILL_DIR="$HOME/.claude/skills/$SKILL_NAME"
REPO_URL="https://github.com/huatianwan/aicoming-skills"

echo "Installing AIComing skill for Claude Code..."

mkdir -p "$SKILL_DIR"

if command -v git &> /dev/null; then
  TMP_DIR=$(mktemp -d)
  git clone --depth 1 "$REPO_URL" "$TMP_DIR" 2>/dev/null
  cp -r "$TMP_DIR/aicoming/"* "$SKILL_DIR/"
  rm -rf "$TMP_DIR"
else
  echo "Error: git is required to install this skill."
  exit 1
fi

echo "Done! AIComing skill installed to $SKILL_DIR"
echo "Next: export AICOMING_API_KEY=\"sk-...\"  (get one at https://aicoming.top/console)"
