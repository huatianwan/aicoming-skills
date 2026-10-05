#!/bin/sh
set -eu
REPO_URL="${AICOMING_SKILL_REPO:-https://github.com/aicomingai/skills}"
TARGET="${AICOMING_SKILL_DIR:-$HOME/.claude/skills/aicoming}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT INT TERM
command -v git >/dev/null 2>&1 || { echo "需要先安装 git" >&2; exit 1; }
git clone --depth 1 "$REPO_URL" "$tmp/repo" >/dev/null 2>&1
mkdir -p "$TARGET"
cp -R "$tmp/repo/aicoming/." "$TARGET/"
printf 'AIComing skill 已安装到 %s\n' "$TARGET"
printf '下一步：python "%s/scripts/aic.py" login（隐藏输入，不要把 Key 写进命令行）\n' "$TARGET"
