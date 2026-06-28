# AIComing Skills

Extend your AI coding assistant with deep knowledge of the [AIComing](https://aicoming.top) unified AI API gateway — generate integration code for OpenAI, Claude, Gemini, DeepSeek and more through one OpenAI-compatible endpoint with smart routing.

## What are Skills?

Skills are reusable knowledge packs that extend an AI coding assistant with domain knowledge, API references, and code templates. After installing the AIComing skill, your assistant understands the AIComing API deeply — it can write chat / image / embedding / rerank integration code in Python, Node.js, or cURL, in OpenAI, Anthropic, or Gemini format, on demand.

Supports Claude Code today, and adapts to other tools with a similar skill/knowledge system.

## What's Included

- Full API reference for all AIComing endpoints (relay + console)
- Code templates for Python, Node.js/TypeScript, and cURL
- OpenAI SDK / Anthropic SDK compatibility guides (just change `base_url`)
- Streaming (SSE) implementations
- Account / API-key / wallet / usage management
- A hard "never fabricate model IDs — always fetch `/api/v1/models`" rule

## Install

### Quick install (recommended)

```bash
npx skills add huatianwan/aicoming-skills
```

### Shell script

```bash
curl -fsSL https://raw.githubusercontent.com/huatianwan/aicoming-skills/main/install.sh | sh
```

### Manual

Copy the `aicoming/` directory to your skill location. For Claude Code: `~/.claude/skills/aicoming/`.

## Configure

Set your AIComing API key as an environment variable:

```bash
export AICOMING_API_KEY="sk-your-api-key"
```

To persist it across sessions, add the line to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.). Get your key in the [AIComing Console](https://aicoming.top/console).

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

MIT (or your preference)
