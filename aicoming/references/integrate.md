# 把现有项目/工具接入 AIComing 速查

核心永远是两件事:**base url 换成 AIComing、key 换成 `$AICOMING_API_KEY`**。

## SDK / 框架

| 现有栈 | 改法 |
|---|---|
| OpenAI Python/Node SDK | `base_url="https://api.aicoming.top/v1"` |
| Anthropic SDK | `base_url="https://api.aicoming.top"` |
| Google GenAI SDK | REST endpoint 指 `https://api.aicoming.top`(v1beta 路径) |
| LangChain (ChatOpenAI) | `openai_api_base="https://api.aicoming.top/v1"` |
| LlamaIndex | `api_base="https://api.aicoming.top/v1"` |
| Vercel AI SDK | `createOpenAI({ baseURL: "https://api.aicoming.top/v1" })` |
| LiteLLM | `api_base` 同上,模型名前缀 `openai/<model>` |

## 常用工具

| 工具 | 配置 |
|---|---|
| **Claude Code** | `env ANTHROPIC_BASE_URL=https://api.aicoming.top` + `ANTHROPIC_AUTH_TOKEN=$AICOMING_API_KEY` |
| **Codex CLI** | provider base url `https://api.aicoming.top/v1`(走 /v1/responses) |
| **CC Switch** | 控制台 API Key 页有"一键导入"深链(含余额脚本) |
| **Cherry Studio** | OpenAI 兼容服务商,Base URL `https://api.aicoming.top/v1` |
| **Lobe Chat / One-API 类** | OpenAI 渠道,同上 |
| **Cline / Roo Code** | OpenAI Compatible,Base URL 同上 |

## 迁移检查单

1. 换 base url + key(上表)。
2. **模型名对一遍** `GET /v1/models`——AIComing 的模型名未必与原平台一致,不要沿用旧名。
3. 流式、工具调用、JSON mode、视觉输入均兼容,一般无需改业务代码。
4. 生图路径:客户端超时调到 ≥600s,带 `Idempotency-Key`(见 media.md)。
5. 验证:先 `GET /v1/balance` 确认 key 通,再发一条最便宜模型的测试消息。

## 环境变量约定

```bash
export AICOMING_API_KEY="sk-..."                      # 必需
export AICOMING_BASE_URL="https://api.aicoming.top"   # 可选,默认即此(自托管/分站才需要改)
```

写 `.env` 时同名即可;千万不要把 key 硬编码进代码或提交进 git。
