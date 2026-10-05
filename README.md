# AIComing Skills

让编码 Agent 通过 AIComing 安全调用统一模型网关：默认 API 为 `https://api.gptcoming.cn`，控制台为 [AIComing](https://aicoming.top/console)。Skill 会先读取实时模型列表、检查权限，再按一次提交、可恢复、立即落盘的规则完成任务。

## What are Skills?

Skills are reusable knowledge packs that extend an AI coding assistant with domain knowledge, API references, and code templates. After installing the AIComing skill, your assistant understands the AIComing API deeply — it can write chat / image / embedding / rerank integration code in Python, Node.js, or cURL, in OpenAI, Anthropic, or Gemini format, on demand.

支持 Claude Code，也可复制到其他兼容 Skill 的工具。

## What's Included

- 零依赖 `aicoming/scripts/aic.py`：登录、模型预检、对话、生图、视频、任务找回、余额与用量
- Key 绑定主机、拒绝重定向、输出脱敏、私有权限存储
- 图片/视频任务先落盘；断线后继续查询，完成后自动下载且不覆盖文件
- 后端 manifest 生成的端点事实表与 CI 对账工具
- 手写的授权、计费、模型权限和禁止操作规则

## Install

### Claude Code / 通用安装

```bash
npx skills add aicomingai/skills
```

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/aicomingai/skills/main/install.sh | sh
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/aicomingai/skills/main/install.ps1 | iex
```

### Manual

Copy the `aicoming/` directory to your skill location. For Claude Code: `~/.claude/skills/aicoming/`.

## Configure

隐藏输入并保存到 `~/.aicoming/key`（Windows 会收紧 ACL，macOS/Linux 权限为 0600）：

```bash
python ~/.claude/skills/aicoming/scripts/aic.py login
```

服务端支持后也可使用设备码登录：`python .../aic.py login --device`。不要把 Key 放在命令参数、聊天记录或项目文件中。

## Usage Examples

Once installed, talk to your assistant in natural language:

- "Integrate AIComing chat completions into my Python app, with streaming"
- "Call Claude through AIComing using the Anthropic format"
- "Add an embeddings + rerank RAG step using AIComing"
- "What models are available on AIComing right now?"
- "Switch my OpenAI SDK code to use AIComing instead"

## Supported Features

| Feature | Endpoint | Format |
|---------|----------|--------|
| Chat completions | `POST /v1/chat/completions` | OpenAI (streaming + not) |
| Text completions | `POST /v1/completions` | OpenAI |
| Embeddings | `POST /v1/embeddings` | OpenAI |
| Text-to-image | `POST /v1/images/generations` | OpenAI |
| Rerank | `POST /v1/rerank` | Cohere/Jina-style |
| Audio (STT) | `POST /v1/audio/transcriptions` | OpenAI Whisper |
| Claude | `POST /v1/messages` | Anthropic |
| Gemini | `POST /v1beta/models/{model}:{action}` | Google |
| Midjourney | `POST /mj/submit/*`, `GET /mj/task/{id}/fetch` | midjourney-proxy |
| Model list | `GET /api/v1/models` | (no auth) |

## License

[MIT](./LICENSE) © AIComing
