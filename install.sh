#!/bin/sh
# AIComing skill 安装脚本(Claude Code) — macOS / Linux / Git Bash
set -e

SKILL_DIR="$HOME/.claude/skills/aicoming"
REPO_URL="https://github.com/huatianwan/aicoming-skills"

command -v git >/dev/null 2>&1 || { echo "需要 git,请先安装。"; exit 1; }

echo "安装 AIComing skill 到 $SKILL_DIR ..."
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT
git clone --depth 1 "$REPO_URL" "$TMP_DIR" >/dev/null 2>&1

mkdir -p "$SKILL_DIR"
cp -r "$TMP_DIR/aicoming/." "$SKILL_DIR/"

echo "完成。"
echo
echo "下一步:"
echo "  1. 到 https://aicoming.top/console 创建 API Key(推荐\"简单模式\")"
echo "  2. export AICOMING_API_KEY=\"sk-...\"  (写入 ~/.bashrc 或 ~/.zshrc 持久化)"
echo "  3. 对助手说:\"用 aicoming 生成一张图\" 试试"
