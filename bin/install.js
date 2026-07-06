#!/usr/bin/env node
'use strict';

// AIComing skill 一行安装器(Claude Code / Codex)。
// 用法:  npx -y github:huatianwan/aicoming-skills
//
// 把随包的 aicoming/ 目录拷进已安装工具的 skills 目录:
//   Claude Code → ~/.claude/skills/aicoming
//   Codex       → ~/.codex/skills/aicoming
// 自动检测:哪个工具的主目录(~/.claude、~/.codex)存在就装到哪个;两个都没有则默认装
// Claude Code。零依赖、跨平台(Node 内置 fs.cpSync,Windows/macOS/Linux 均原生支持),
// 不再依赖 git / bash——旧 install.sh 需要 git,Windows 用户常缺。

const fs = require('fs');
const os = require('os');
const path = require('path');

function main() {
  const src = path.join(__dirname, '..', 'aicoming');

  if (!fs.existsSync(path.join(src, 'SKILL.md'))) {
    console.error('✗ 找不到 skill 源文件(aicoming/SKILL.md),安装包不完整。');
    process.exit(1);
  }
  if (typeof fs.cpSync !== 'function') {
    console.error('✗ 需要 Node.js 16.7 或更高版本(当前 ' + process.version + ')。请升级 Node 后重试。');
    process.exit(1);
  }

  const home = os.homedir();
  const candidates = [
    { name: 'Claude Code', home: path.join(home, '.claude'), root: path.join(home, '.claude', 'skills') },
    { name: 'Codex', home: path.join(home, '.codex'), root: path.join(home, '.codex', 'skills') },
  ];

  // 已安装的工具(主目录存在)才装;都没检测到则默认装 Claude Code。
  let targets = candidates.filter(function (c) { return fs.existsSync(c.home); });
  if (targets.length === 0) targets = [candidates[0]];

  const installed = [];
  for (const t of targets) {
    const dest = path.join(t.root, 'aicoming');
    try {
      fs.mkdirSync(t.root, { recursive: true });
      fs.cpSync(src, dest, { recursive: true });
      installed.push({ name: t.name, dest: dest });
    } catch (e) {
      console.error('✗ 安装到 ' + t.name + ' 失败:', (e && e.message) ? e.message : e);
    }
  }

  if (installed.length === 0) {
    process.exit(1);
  }

  console.log('');
  for (const it of installed) {
    console.log('  ✅ ' + it.name + ' skill 已安装 → ' + it.dest);
  }
  console.log('');
  console.log('  下一步:');
  console.log('    1. 到 https://aicoming.top/console 创建 API Key(推荐「简单模式」向导)');
  console.log('    2. export AICOMING_API_KEY="sk-..."   # 写入 ~/.zshrc 或 ~/.bashrc 持久化');
  console.log('       Windows PowerShell:  setx AICOMING_API_KEY "sk-..."');
  console.log('    3. 对助手说:「用 aicoming 生成一张图」试试');

  if (installed.some(function (it) { return it.name === 'Codex'; })) {
    console.log('');
    console.log('  ⚠ Codex 还需放行沙箱网络,在 ~/.codex/config.toml 顶层加:');
    console.log('      sandbox_mode = "workspace-write"');
    console.log('      [sandbox_workspace_write]');
    console.log('      network_access = true');
  }
  console.log('');
}

main();
