# AIComing Skill

让你的 AI 编程助手（Claude Code 等）**直接用你的 AIComing key 干活**：生成图片、调用 127+ 大模型对话、提交视频任务、查余额、列可用模型——以及把你现有项目一键接入 AIComing。

> AIComing（[aicoming.top](https://aicoming.top)）是聚合 GPT、Claude、Gemini、DeepSeek 等 127+ 大模型的 OpenAI 兼容网关：一把 key、智能路由到最低价、秒级故障转移。

Give your AI coding assistant (Claude Code etc.) the ability to **act with your AIComing key**: generate images, chat with 127+ models, submit video tasks, check balance — and migrate existing projects to AIComing in one step.

## 装完能干什么

装好后直接对助手说人话：

- “用 aicoming 生成一张赛博朋克风格的猫，存到桌面”
- “用 gpt-5.5 和 claude 各回答一遍这个问题，对比给我看”
- “查一下我 aicoming 还剩多少钱”
- “aicoming 上现在有哪些图片模型？”
- “把这个项目的 OpenAI 调用全部切到 aicoming”
- “用 Claude Code 直连 aicoming 该怎么配？”

## 安装

### Claude Code（推荐）

```bash
git clone https://github.com/huatianwan/aicoming-skills.git
cp -r aicoming-skills/aicoming ~/.claude/skills/aicoming
```

或一行脚本（macOS / Linux / Git Bash）：

```bash
curl -fsSL https://raw.githubusercontent.com/huatianwan/aicoming-skills/main/install.sh | sh
```

Windows PowerShell：

```powershell
git clone https://github.com/huatianwan/aicoming-skills.git
Copy-Item -Recurse aicoming-skills/aicoming "$env:USERPROFILE\.claude\skills\aicoming"
```

### 其它助手

把 `aicoming/` 目录拷到对应工具的 skill/知识库位置即可（内容是纯 Markdown + 一个零依赖 Python 脚本）。

## 配置（一步）

到 [AIComing 控制台](https://aicoming.top/console) 创建 API Key（推荐“简单模式”：选模型，路由自动配好），然后：

```bash
export AICOMING_API_KEY="sk-..."
```

写进 `~/.bashrc` / `~/.zshrc` 持久化；或写到文件 `~/.aicoming/key`。

## 里面有什么

```
aicoming/
├── SKILL.md                 # 主指南:直接调用工作流 + 端点总览 + 错误处理
├── scripts/
│   └── aic.py               # 零依赖 CLI:models / chat / image / balance / video
└── references/
    ├── chat.md              # 对话/流式/多轮/Responses
    ├── media.md             # 生图(幂等重试/心跳容错)/图生图/视频/语音/MJ
    ├── protocols.md         # OpenAI / Anthropic / Gemini 三协议直连
    ├── account.md           # key 路由范围/白名单/余额/用量
    └── integrate.md         # 各 SDK 与工具接入速查表
```

设计原则：

- **能直接干活就不只给代码** —— 自带 `aic.py`，助手可直接生图/对话/查余额
- **模型名永不虚构** —— 强制从 `GET /v1/models` 实时获取
- **长任务不白花钱** —— 生图自动带 `Idempotency-Key`，断连重试直取结果不重复扣费
- **全部端点经源码核对** —— 与 aicoming.top 生产网关逐一对齐

## License

MIT
